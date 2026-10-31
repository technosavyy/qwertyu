"""Application service: answers each screen's questions from one verified snapshot (ADR-004).

Pure Python, no web framework. The API layer only translates HTTP to these calls and back.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from windfc.constants import LONDON
from windfc.data.loader import Snapshot
from windfc.domain.alignment import hourly_actuals
from windfc.domain.breakdown import by_delivery_day, by_london_hour
from windfc.domain.buffer import (
    Buffer,
    BufferBacktest,
    check_confidence,
    known_by,
    plan_for,
    shortfall_buffer,
)
from windfc.domain.cutoff import cutoff_instant
from windfc.domain.evaluation import Evaluation, evaluate
from windfc.domain.metrics import ErrorMetrics, summarise
from windfc.domain.selection import select_latest_forecasts
from windfc.errors import InvalidRequestError
from windfc.models import DeliveryWindow, ForecastPoint

_HOUR = timedelta(hours=1)
_EVALUATION_CACHE_SIZE = 64


@dataclass(frozen=True, slots=True)
class Meta:
    """What the screen needs before the first question: range, defaults and choices."""

    window: DeliveryWindow
    default_day: date
    default_cutoff: time
    confidence_options: tuple[int, ...]
    publish_run_times: tuple[time, ...]  # London wall-clock times of the regular forecast runs
    snapshot_generated_at: datetime


@dataclass(frozen=True, slots=True)
class HourView:
    """One hour of a delivery day. Any value is None when it is not known."""

    start_time: datetime
    forecast_mw: float | None
    publish_time: datetime | None
    actual_mw: float | None
    plan_for_mw: float | None

    @property
    def error_mw(self) -> float | None:
        if self.forecast_mw is None or self.actual_mw is None:
            return None
        return self.forecast_mw - self.actual_mw


@dataclass(frozen=True, slots=True)
class DayView:
    """Everything the decision strip and day chart show for one delivery day."""

    delivery_day: date
    cutoff_time: time
    cutoff_utc: datetime
    forecast_runs: tuple[datetime, ...]
    hours: tuple[HourView, ...]
    buffer: Buffer
    metrics: ErrorMetrics | None
    hours_without_forecast: tuple[datetime, ...]
    hours_without_actual: tuple[datetime, ...]


@dataclass(frozen=True, slots=True)
class AccuracyView:
    """Accuracy over the whole window at one cutoff, plus how well the buffer held up."""

    cutoff_time: time
    window: DeliveryWindow
    overall: ErrorMetrics
    by_hour: dict[int, ErrorMetrics]
    by_day: dict[date, ErrorMetrics]
    expected_hours: int
    hours_without_forecast: tuple[datetime, ...]
    hours_without_actual: tuple[datetime, ...]
    backtest: BufferBacktest


@dataclass(frozen=True, slots=True)
class Revision:
    publish_time: datetime
    generation_mw: float
    hours_ahead: float  # from publication to the start of the hour
    available_at_cutoff: bool


@dataclass(frozen=True, slots=True)
class RevisionsView:
    """Every forecast ever published for one hour, oldest first."""

    start_time: datetime
    cutoff_time: time
    cutoff_utc: datetime
    revisions: tuple[Revision, ...]
    selected_publish_time: datetime | None
    actual_mw: float | None


class ForecastService:
    """Read-only answers over one snapshot. Safe to share across requests."""

    def __init__(self, snapshot: Snapshot) -> None:
        self._snapshot = snapshot
        self._window = snapshot.manifest.window
        self._actual_by_hour = hourly_actuals(snapshot.actuals)
        forecasts_by_hour: defaultdict[datetime, list[ForecastPoint]] = defaultdict(list)
        for point in snapshot.forecasts:
            forecasts_by_hour[point.start_time].append(point)
        self._forecasts_by_hour = {
            hour: tuple(sorted(points, key=lambda point: point.publish_time))
            for hour, points in forecasts_by_hour.items()
        }
        self._evaluations: dict[time, Evaluation] = {}

    # Queries -------------------------------------------------------------------------------

    def meta(self, default_cutoff: time) -> Meta:
        return Meta(
            window=self._window,
            default_day=self._window.last_day,
            default_cutoff=default_cutoff,
            confidence_options=(90, 95),
            publish_run_times=self._regular_run_times(),
            snapshot_generated_at=self._snapshot.manifest.generated_at,
        )

    def day(self, delivery_day: date, cutoff_time: time, confidence: int) -> DayView:
        self._check_day(delivery_day)
        self._check_confidence(confidence)
        cutoff = cutoff_instant(delivery_day, cutoff_time)
        day_hours = list(DeliveryWindow(delivery_day, delivery_day).hours())
        selected = select_latest_forecasts(
            self._forecasts_for(day_hours), cutoff=cutoff, hours=day_hours
        )
        evaluation = self._evaluation(cutoff_time)
        buffer = shortfall_buffer(known_by(evaluation.errors, cutoff), confidence)

        hours = tuple(
            HourView(
                start_time=hour,
                forecast_mw=selected[hour].generation_mw if hour in selected else None,
                publish_time=selected[hour].publish_time if hour in selected else None,
                actual_mw=self._actual_by_hour.get(hour),
                plan_for_mw=plan_for(selected[hour].generation_mw, buffer)
                if hour in selected
                else None,
            )
            for hour in day_hours
        )
        day_errors = [item for item in evaluation.errors if item.start_time.date() == delivery_day]
        return DayView(
            delivery_day=delivery_day,
            cutoff_time=cutoff_time,
            cutoff_utc=cutoff,
            forecast_runs=tuple(sorted({point.publish_time for point in selected.values()})),
            hours=hours,
            buffer=buffer,
            metrics=summarise(day_errors) if day_errors else None,
            hours_without_forecast=tuple(hour for hour in day_hours if hour not in selected),
            hours_without_actual=tuple(
                hour for hour in day_hours if hour not in self._actual_by_hour
            ),
        )

    def accuracy(self, cutoff_time: time, confidence: int) -> AccuracyView:
        self._check_confidence(confidence)
        evaluation = self._evaluation(cutoff_time)
        if not evaluation.errors:
            raise InvalidRequestError("no hours could be measured at this cutoff")
        return AccuracyView(
            cutoff_time=cutoff_time,
            window=self._window,
            overall=summarise(evaluation.errors),
            by_hour=by_london_hour(evaluation.errors),
            by_day=by_delivery_day(evaluation.errors),
            expected_hours=evaluation.expected_hours,
            hours_without_forecast=evaluation.hours_without_forecast,
            hours_without_actual=evaluation.hours_without_actual,
            backtest=self._backtest(evaluation, cutoff_time, confidence),
        )

    def revisions(self, start_time: datetime, cutoff_time: time) -> RevisionsView:
        if start_time.utcoffset() is None:
            raise InvalidRequestError("start_time must include a timezone, for example ...Z")
        start_time = start_time.astimezone(UTC)
        if not self._window.contains(start_time) or start_time.minute or start_time.second:
            raise InvalidRequestError(
                f"start_time must be the start of an hour between "
                f"{self._window.first_day} and {self._window.last_day}"
            )
        cutoff = cutoff_instant(start_time.date(), cutoff_time)
        points = self._forecasts_by_hour.get(start_time, ())
        selected = select_latest_forecasts(points, cutoff=cutoff, hours=[start_time])
        chosen = selected.get(start_time)
        return RevisionsView(
            start_time=start_time,
            cutoff_time=cutoff_time,
            cutoff_utc=cutoff,
            revisions=tuple(
                Revision(
                    publish_time=point.publish_time,
                    generation_mw=point.generation_mw,
                    hours_ahead=(start_time - point.publish_time) / _HOUR,
                    available_at_cutoff=point.publish_time <= cutoff,
                )
                for point in points
            ),
            selected_publish_time=chosen.publish_time if chosen else None,
            actual_mw=self._actual_by_hour.get(start_time),
        )

    # Internals -----------------------------------------------------------------------------

    def _evaluation(self, cutoff_time: time) -> Evaluation:
        """Whole-window evaluation for a cutoff, computed once and kept (bounded)."""
        cached = self._evaluations.get(cutoff_time)
        if cached is not None:
            return cached
        result = evaluate(
            actuals=self._snapshot.actuals,
            forecasts=self._snapshot.forecasts,
            window=self._window,
            cutoff_time=cutoff_time,
        )
        if len(self._evaluations) >= _EVALUATION_CACHE_SIZE:
            self._evaluations.pop(next(iter(self._evaluations)))
        self._evaluations[cutoff_time] = result
        return result

    def _backtest(
        self, evaluation: Evaluation, cutoff_time: time, confidence: int
    ) -> BufferBacktest:
        """Replay each day: would yesterday-morning's buffer have covered today's shortfall?"""
        tested = covered = 0
        errors_by_day: defaultdict[date, list[float]] = defaultdict(list)
        for item in evaluation.errors:
            errors_by_day[item.start_time.date()].append(item.error_mw)
        for day, day_errors in errors_by_day.items():
            buffer = shortfall_buffer(
                known_by(evaluation.errors, cutoff_instant(day, cutoff_time)), confidence
            )
            if buffer.buffer_mw is None:
                continue
            tested += len(day_errors)
            covered += sum(error <= buffer.buffer_mw for error in day_errors)
        return BufferBacktest(confidence=confidence, hours_tested=tested, hours_covered=covered)

    def _forecasts_for(self, hours: list[datetime]) -> list[ForecastPoint]:
        return [point for hour in hours for point in self._forecasts_by_hour.get(hour, ())]

    def _regular_run_times(self) -> tuple[time, ...]:
        """London times at which forecasts are published on at least half of the days."""
        publish_times = {point.publish_time for point in self._snapshot.forecasts}
        days = len({moment.date() for moment in publish_times}) or 1
        counts = Counter(moment.astimezone(LONDON).time() for moment in publish_times)
        return tuple(sorted(run for run, count in counts.items() if count * 2 >= days))

    def _check_day(self, delivery_day: date) -> None:
        if not self._window.first_day <= delivery_day <= self._window.last_day:
            raise InvalidRequestError(
                f"date must be between {self._window.first_day} and {self._window.last_day}"
            )

    @staticmethod
    def _check_confidence(confidence: int) -> None:
        try:
            check_confidence(confidence)
        except ValueError as exc:
            raise InvalidRequestError(str(exc)) from exc

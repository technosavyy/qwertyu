"""Replay past decisions: what was forecast at each day's cutoff versus what happened."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, time, timedelta

from windfc.constants import DEFAULT_CUTOFF_TIME
from windfc.domain.alignment import hourly_actuals
from windfc.domain.cutoff import cutoff_instant
from windfc.domain.metrics import HourlyError
from windfc.domain.selection import select_latest_forecasts
from windfc.models import ActualPoint, DeliveryWindow, ForecastPoint


@dataclass(frozen=True, slots=True)
class Evaluation:
    """Hourly errors for a window, plus every hour that could not be measured and why."""

    errors: tuple[HourlyError, ...]
    expected_hours: int
    hours_without_forecast: tuple[datetime, ...]
    hours_without_actual: tuple[datetime, ...]


def evaluate(
    *,
    actuals: Sequence[ActualPoint],
    forecasts: Sequence[ForecastPoint],
    window: DeliveryWindow,
    cutoff_time: time = DEFAULT_CUTOFF_TIME,
) -> Evaluation:
    """Measure the forecast a buyer would have used for every hour in ``window``.

    Each delivery day uses its own cutoff: ``cutoff_time`` London time on the day before.
    An hour is measured only when it has both a forecast from before that cutoff and a
    complete actual. Hours missing either are listed, not guessed (ADR-009).
    """
    actual_by_hour = hourly_actuals(actuals)
    errors: list[HourlyError] = []
    no_forecast: list[datetime] = []
    no_actual: list[datetime] = []
    expected = 0

    for offset in range((window.last_day - window.first_day).days + 1):
        day = window.first_day + timedelta(days=offset)
        day_hours = list(DeliveryWindow(day, day).hours())
        expected += len(day_hours)
        selected = select_latest_forecasts(
            forecasts, cutoff=cutoff_instant(day, cutoff_time), hours=day_hours
        )
        for hour in day_hours:
            forecast = selected.get(hour)
            actual = actual_by_hour.get(hour)
            if forecast is None:
                no_forecast.append(hour)
            if actual is None:
                no_actual.append(hour)
            if forecast is not None and actual is not None:
                errors.append(
                    HourlyError(
                        start_time=hour,
                        publish_time=forecast.publish_time,
                        forecast_mw=forecast.generation_mw,
                        actual_mw=actual,
                    )
                )

    return Evaluation(
        errors=tuple(errors),
        expected_hours=expected,
        hours_without_forecast=tuple(no_forecast),
        hours_without_actual=tuple(no_actual),
    )

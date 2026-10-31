"""Immutable domain values. Names carry units; timestamps are always aware UTC."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta


def _require_utc(value: datetime, name: str) -> None:
    offset = value.utcoffset()
    if offset is None or offset != timedelta(0):
        raise ValueError(f"{name} must be a timezone-aware UTC datetime, got {value!r}")


@dataclass(frozen=True, slots=True)
class ActualPoint:
    """Metered wind generation, averaged over the half-hour starting at ``start_time``."""

    start_time: datetime
    generation_mw: float

    def __post_init__(self) -> None:
        _require_utc(self.start_time, "start_time")


@dataclass(frozen=True, slots=True)
class ForecastPoint:
    """One forecast of wind generation for the hour starting at ``start_time``.

    ``publish_time`` is when the forecast was created. Many forecasts exist for the same
    ``start_time``, one per publication (ADR-002).
    """

    publish_time: datetime
    start_time: datetime
    generation_mw: float

    def __post_init__(self) -> None:
        _require_utc(self.publish_time, "publish_time")
        _require_utc(self.start_time, "start_time")


@dataclass(frozen=True, slots=True)
class DeliveryWindow:
    """A run of whole UTC delivery days, both ends inclusive."""

    first_day: date
    last_day: date

    def __post_init__(self) -> None:
        if self.last_day < self.first_day:
            raise ValueError(f"last_day {self.last_day} is before first_day {self.first_day}")

    @property
    def start(self) -> datetime:
        """00:00 UTC on the first delivery day."""
        return datetime.combine(self.first_day, datetime.min.time(), tzinfo=UTC)

    @property
    def end_exclusive(self) -> datetime:
        """00:00 UTC on the day after the last delivery day."""
        return datetime.combine(self.last_day + timedelta(days=1), datetime.min.time(), tzinfo=UTC)

    def contains(self, moment: datetime) -> bool:
        """Whether ``moment`` falls inside the window."""
        return self.start <= moment < self.end_exclusive

    def half_hours(self) -> Iterator[datetime]:
        """Every half-hour start time in the window, in order."""
        yield from self._steps(timedelta(minutes=30))

    def hours(self) -> Iterator[datetime]:
        """Every hour start time in the window, in order."""
        yield from self._steps(timedelta(hours=1))

    def _steps(self, step: timedelta) -> Iterator[datetime]:
        moment = self.start
        while moment < self.end_exclusive:
            yield moment
            moment += step

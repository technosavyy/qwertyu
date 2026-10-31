"""Shared builders for tests: small, explicit raw rows and windows."""

from datetime import UTC, date, datetime, timedelta

from windfc.models import DeliveryWindow
from windfc.timeutil import format_utc, start_of_day_utc

TWO_DAYS = DeliveryWindow(date(2026, 1, 1), date(2026, 1, 2))


def utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """A UTC datetime, written short."""
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


def actual_row(start: datetime, generation: object, fuel_type: str = "WIND") -> dict[str, object]:
    """A raw FUELHH row."""
    return {
        "dataset": "FUELHH",
        "fuelType": fuel_type,
        "generation": generation,
        "startTime": format_utc(start),
    }


def forecast_row(publish: datetime, start: datetime, generation: object) -> dict[str, object]:
    """A raw WINDFOR row."""
    return {
        "dataset": "WINDFOR",
        "generation": generation,
        "publishTime": format_utc(publish),
        "startTime": format_utc(start),
    }


def complete_actual_rows(window: DeliveryWindow) -> list[dict[str, object]]:
    """One actual per half-hour. Generation is 1000 plus the half-hour's position."""
    return [actual_row(start, 1000 + index) for index, start in enumerate(window.half_hours())]


def complete_forecast_rows(window: DeliveryWindow) -> list[dict[str, object]]:
    """One forecast per hour, published an hour before its day starts.

    Generation is 2000 plus the hour's position.
    """
    return [
        forecast_row(start_of_day_utc(start) - timedelta(hours=1), start, 2000 + index)
        for index, start in enumerate(window.hours())
    ]

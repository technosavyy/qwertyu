"""Validate raw Elexon rows and turn them into domain values.

Anything unexpected raises ``SnapshotError``: bad data must stop the build, never reach
the buyer (ADR-003, CX2).
"""

from collections.abc import Iterable, Mapping
from datetime import datetime

from windfc.constants import ACTUALS_DATASET, FORECASTS_DATASET, FUEL_TYPE_WIND
from windfc.errors import SnapshotError
from windfc.models import ActualPoint, ForecastPoint
from windfc.timeutil import parse_utc

Row = Mapping[str, object]


def parse_actuals(rows: Iterable[Row]) -> list[ActualPoint]:
    """Parse FUELHH rows. Each must be wind, on a half-hour, with one row per start time."""
    points: dict[datetime, ActualPoint] = {}
    for index, row in enumerate(rows):
        where = f"{ACTUALS_DATASET} row {index}"
        fuel_type = _text(row, "fuelType", where)
        if fuel_type != FUEL_TYPE_WIND:
            raise SnapshotError(f"{where}: expected fuelType {FUEL_TYPE_WIND}, got {fuel_type!r}")
        start = _timestamp(row, "startTime", where)
        if start.minute not in (0, 30) or start.second or start.microsecond:
            raise SnapshotError(f"{where}: startTime {start.isoformat()} is not on a half-hour")
        if start in points:
            raise SnapshotError(f"{where}: duplicate startTime {start.isoformat()}")
        points[start] = ActualPoint(start, _generation(row, where))
    return [points[start] for start in sorted(points)]


def parse_forecasts(rows: Iterable[Row]) -> list[ForecastPoint]:
    """Parse WINDFOR rows. Start times must be on the hour (ADR-013); no repeated pairs."""
    points: dict[tuple[datetime, datetime], ForecastPoint] = {}
    for index, row in enumerate(rows):
        where = f"{FORECASTS_DATASET} row {index}"
        publish = _timestamp(row, "publishTime", where)
        start = _timestamp(row, "startTime", where)
        if start.minute or start.second or start.microsecond:
            raise SnapshotError(f"{where}: startTime {start.isoformat()} is not on the hour")
        key = (start, publish)
        if key in points:
            raise SnapshotError(
                f"{where}: duplicate forecast for startTime {start.isoformat()} "
                f"published {publish.isoformat()}"
            )
        points[key] = ForecastPoint(publish, start, _generation(row, where))
    return [points[key] for key in sorted(points)]


def _text(row: Row, key: str, where: str) -> str:
    value = row.get(key)
    if not isinstance(value, str):
        raise SnapshotError(f"{where}: field {key!r} is missing or not text")
    return value


def _timestamp(row: Row, key: str, where: str) -> datetime:
    try:
        return parse_utc(_text(row, key, where))
    except ValueError as exc:
        raise SnapshotError(f"{where}: field {key!r}: {exc}") from exc


def _generation(row: Row, where: str) -> float:
    value = row.get("generation")
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise SnapshotError(f"{where}: field 'generation' is missing or not a number")
    if value < 0:
        raise SnapshotError(f"{where}: generation {value} is negative")
    return float(value)

"""Put actuals on the same hourly footing as forecasts (ADR-013)."""

from collections.abc import Iterable
from datetime import datetime, timedelta

from windfc.models import ActualPoint

_HALF_HOUR = timedelta(minutes=30)


def hourly_actuals(actuals: Iterable[ActualPoint]) -> dict[datetime, float]:
    """Average each pair of half-hours into one value for the hour that starts at ``H:00``.

    The hour H is the mean of the half-hours starting at H:00 and H:30. If either is missing
    the hour has no actual and is left out, never filled in (ADR-009).
    """
    by_start = {point.start_time: point.generation_mw for point in actuals}
    return {
        start: (first + by_start[start + _HALF_HOUR]) / 2
        for start, first in by_start.items()
        if start.minute == 0 and start + _HALF_HOUR in by_start
    }

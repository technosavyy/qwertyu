"""Pick the forecast a buyer could actually see at decision time (ADR-002)."""

from collections.abc import Collection, Iterable
from datetime import datetime

from windfc.models import ForecastPoint


def select_latest_forecasts(
    forecasts: Iterable[ForecastPoint],
    *,
    cutoff: datetime,
    hours: Collection[datetime],
) -> dict[datetime, ForecastPoint]:
    """For each hour in ``hours``, the forecast with the newest ``publish_time`` <= ``cutoff``.

    A forecast published exactly at the cutoff counts as available. Forecasts published after
    the cutoff are ignored however good they look: the buyer did not have them. Hours with no
    qualifying forecast are absent from the result so callers can report them (ADR-009).
    """
    wanted = frozenset(hours)
    latest: dict[datetime, ForecastPoint] = {}
    for forecast in forecasts:
        if forecast.start_time not in wanted or forecast.publish_time > cutoff:
            continue
        current = latest.get(forecast.start_time)
        if current is None or forecast.publish_time > current.publish_time:
            latest[forecast.start_time] = forecast
    return latest

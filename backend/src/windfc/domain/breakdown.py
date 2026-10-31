"""Group hourly errors so buyers can see when and where the forecast misses (ADR-010)."""

from collections import defaultdict
from collections.abc import Iterable
from datetime import date

from windfc.constants import LONDON
from windfc.domain.metrics import ErrorMetrics, HourlyError, summarise


def by_london_hour(errors: Iterable[HourlyError]) -> dict[int, ErrorMetrics]:
    """Metrics for each hour of the day, 0 to 23, in London time (ADR-008)."""
    groups: defaultdict[int, list[HourlyError]] = defaultdict(list)
    for item in errors:
        groups[item.start_time.astimezone(LONDON).hour].append(item)
    return {hour: summarise(groups[hour]) for hour in sorted(groups)}


def by_delivery_day(errors: Iterable[HourlyError]) -> dict[date, ErrorMetrics]:
    """Metrics for each UTC delivery day, in date order."""
    groups: defaultdict[date, list[HourlyError]] = defaultdict(list)
    for item in errors:
        groups[item.start_time.date()].append(item)
    return {day: summarise(groups[day]) for day in sorted(groups)}

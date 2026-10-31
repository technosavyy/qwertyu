from datetime import datetime

from tests.support import utc
from windfc.domain.selection import select_latest_forecasts
from windfc.models import ForecastPoint

HOUR = utc(2026, 1, 2, 10)
CUTOFF = utc(2026, 1, 1, 9)


def forecast(publish: datetime, mw: float, start: datetime = HOUR) -> ForecastPoint:
    return ForecastPoint(publish, start, mw)


def pick(
    forecasts: list[ForecastPoint], hours: list[datetime] | None = None
) -> dict[datetime, float]:
    chosen = select_latest_forecasts(forecasts, cutoff=CUTOFF, hours=hours or [HOUR])
    return {start: point.generation_mw for start, point in chosen.items()}


def test_picks_the_newest_forecast_published_before_the_cutoff() -> None:
    rows = [forecast(utc(2026, 1, 1, 2, 30), 100), forecast(utc(2026, 1, 1, 7, 30), 200)]

    assert pick(rows) == {HOUR: 200}


def test_ignores_a_better_forecast_published_after_the_cutoff() -> None:
    rows = [forecast(utc(2026, 1, 1, 7, 30), 200), forecast(utc(2026, 1, 1, 9, 30), 999)]

    assert pick(rows) == {HOUR: 200}


def test_a_forecast_published_exactly_at_the_cutoff_counts() -> None:
    assert pick([forecast(CUTOFF, 300), forecast(utc(2026, 1, 1, 7, 30), 200)]) == {HOUR: 300}


def test_does_not_depend_on_input_order() -> None:
    rows = [forecast(utc(2026, 1, 1, 7, 30), 200), forecast(utc(2026, 1, 1, 2, 30), 100)]

    assert pick(rows) == pick(rows[::-1]) == {HOUR: 200}


def test_leaves_out_hours_with_no_forecast_before_the_cutoff() -> None:
    assert pick([forecast(utc(2026, 1, 1, 9, 30), 999)]) == {}


def test_only_returns_the_hours_asked_for() -> None:
    other = utc(2026, 1, 2, 11)
    rows = [forecast(utc(2026, 1, 1, 7, 30), 200), forecast(utc(2026, 1, 1, 7, 30), 50, other)]

    assert pick(rows) == {HOUR: 200}
    assert pick(rows, [HOUR, other]) == {HOUR: 200, other: 50}

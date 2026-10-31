from datetime import date, datetime, timedelta, timezone

import pytest

from tests.support import TWO_DAYS, utc
from windfc.models import ActualPoint, DeliveryWindow, ForecastPoint


def test_actual_point_rejects_naive_time() -> None:
    with pytest.raises(ValueError, match="start_time"):
        ActualPoint(datetime(2026, 1, 1), 100.0)


def test_forecast_point_rejects_non_utc_offset() -> None:
    plus_one = datetime(2026, 1, 1, 10, tzinfo=timezone(timedelta(hours=1)))

    with pytest.raises(ValueError, match="publish_time"):
        ForecastPoint(plus_one, utc(2026, 1, 2), 100.0)


def test_points_are_immutable() -> None:
    point = ActualPoint(utc(2026, 1, 1), 100.0)

    with pytest.raises(AttributeError):
        point.generation_mw = 5.0  # type: ignore[misc]


def test_window_rejects_reversed_days() -> None:
    with pytest.raises(ValueError, match="before first_day"):
        DeliveryWindow(date(2026, 1, 2), date(2026, 1, 1))


def test_two_day_window_has_expected_bounds_and_counts() -> None:
    assert TWO_DAYS.start == utc(2026, 1, 1)
    assert TWO_DAYS.end_exclusive == utc(2026, 1, 3)
    assert len(list(TWO_DAYS.half_hours())) == 96
    assert len(list(TWO_DAYS.hours())) == 48


def test_window_iteration_starts_and_ends_correctly() -> None:
    half_hours = list(TWO_DAYS.half_hours())

    assert half_hours[0] == utc(2026, 1, 1, 0, 0)
    assert half_hours[1] == utc(2026, 1, 1, 0, 30)
    assert half_hours[-1] == utc(2026, 1, 2, 23, 30)


def test_window_contains_is_inclusive_at_start_and_exclusive_at_end() -> None:
    assert TWO_DAYS.contains(utc(2026, 1, 1, 0, 0))
    assert TWO_DAYS.contains(utc(2026, 1, 2, 23, 59))
    assert not TWO_DAYS.contains(utc(2026, 1, 3, 0, 0))
    assert not TWO_DAYS.contains(utc(2025, 12, 31, 23, 59))

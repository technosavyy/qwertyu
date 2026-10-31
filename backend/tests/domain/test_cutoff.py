from datetime import UTC, date, datetime, time

import pytest

from windfc.domain.cutoff import cutoff_instant


def test_winter_cutoff_is_the_same_clock_time_in_utc_on_the_day_before() -> None:
    assert cutoff_instant(date(2026, 1, 15), time(9, 0)) == datetime(2026, 1, 14, 9, tzinfo=UTC)


def test_summer_cutoff_is_converted_with_the_london_offset() -> None:
    assert cutoff_instant(date(2026, 7, 2), time(9, 0)) == datetime(2026, 7, 1, 8, tzinfo=UTC)


def test_first_delivery_day_has_its_cutoff_in_the_previous_month_and_year() -> None:
    assert cutoff_instant(date(2026, 1, 1), time(9, 0)) == datetime(2025, 12, 31, 9, tzinfo=UTC)


def test_rejects_a_cutoff_time_that_carries_a_timezone() -> None:
    with pytest.raises(ValueError, match="must not carry a timezone"):
        cutoff_instant(date(2026, 1, 15), time(9, 0, tzinfo=UTC))

import pytest

from tests.support import utc
from windfc.domain.buffer import (
    MIN_HISTORY_HOURS,
    Buffer,
    BufferBacktest,
    check_confidence,
    known_by,
    plan_for,
    shortfall_buffer,
)
from windfc.domain.metrics import HourlyError

PUBLISHED = utc(2025, 12, 31, 7, 30)


def history(*signed: float) -> list[HourlyError]:
    return [
        HourlyError(
            utc(2026, 1, 1) + index * (utc(2026, 1, 1, 1) - utc(2026, 1, 1)),
            PUBLISHED,
            1000 + value,
            1000,
        )
        for index, value in enumerate(signed)
    ]


def test_no_buffer_until_there_are_three_days_of_history() -> None:
    result = shortfall_buffer(history(*[100.0] * (MIN_HISTORY_HOURS - 1)), 90)

    assert result == Buffer(confidence=90, buffer_mw=None, history_hours=71)
    assert not result.enough_history


def test_buffer_is_the_nearest_rank_percentile_of_signed_errors() -> None:
    # 80 hours: errors 0, 100, ..., 900 repeated 8 times. The 72nd of 80 sorted is 800.
    result = shortfall_buffer(history(*[100.0 * (i % 10) for i in range(80)]), 90)

    assert result.buffer_mw == 800
    assert result.history_hours == 80
    assert result.enough_history


def test_buffer_counts_under_forecasts_as_not_too_high_and_is_never_negative() -> None:
    assert shortfall_buffer(history(*[-500.0] * 80), 95).buffer_mw == 0


def test_only_offered_confidence_levels_are_accepted() -> None:
    check_confidence(90)
    check_confidence(95)
    with pytest.raises(ValueError, match="confidence must be one of"):
        shortfall_buffer(history(1.0), 80)


def test_known_by_includes_an_hour_that_ends_exactly_at_the_cutoff() -> None:
    items = history(1.0, 2.0, 3.0)  # hours starting 00:00, 01:00, 02:00

    assert [item.error_mw for item in known_by(items, utc(2026, 1, 1, 2))] == [1.0, 2.0]


def test_plan_for_subtracts_the_buffer_and_never_goes_below_zero() -> None:
    buffer = Buffer(confidence=90, buffer_mw=800, history_hours=80)

    assert plan_for(1600, buffer) == 800
    assert plan_for(500, buffer) == 0
    assert plan_for(1600, Buffer(confidence=90, buffer_mw=None, history_hours=0)) is None


def test_backtest_coverage() -> None:
    assert BufferBacktest(90, hours_tested=40, hours_covered=36).coverage_pct == 90
    assert BufferBacktest(90, hours_tested=0, hours_covered=0).coverage_pct is None

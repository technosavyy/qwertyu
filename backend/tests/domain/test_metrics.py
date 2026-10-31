import math

import pytest

from tests.support import utc
from windfc.domain.metrics import HourlyError, percentile, summarise
from windfc.errors import InsufficientDataError


def errors_of(*signed: float, actual: float = 1000) -> list[HourlyError]:
    """Hourly errors with the given signed errors, all against the same actual."""
    return [
        HourlyError(utc(2026, 1, 2, hour), utc(2026, 1, 1, 7, 30), actual + value, actual)
        for hour, value in enumerate(signed)
    ]


def test_error_is_forecast_minus_actual() -> None:
    assert errors_of(120)[0].error_mw == 120
    assert errors_of(-80)[0].error_mw == -80


def test_symmetric_misses_have_no_bias() -> None:
    result = summarise(errors_of(100, -100, 300, -300))

    assert result.hours == 4
    assert result.bias_mw == 0
    assert result.mae_mw == 200
    assert result.rmse_mw == pytest.approx(math.sqrt(50_000))


def test_all_over_forecasts_give_positive_bias_and_hand_calculated_metrics() -> None:
    result = summarise(errors_of(100, 200, 300, 400, 500, 600, 700, 800, 900, 1000))

    assert result.bias_mw == 550
    assert result.mae_mw == 550
    # Mean of squares: 100^2 * (1 + 4 + ... + 100) / 10 = 10_000 * 38.5.
    assert result.rmse_mw == pytest.approx(math.sqrt(385_000))
    # Nearest rank: P90 is the 9th of 10 sorted misses, P95 the 10th.
    assert result.p90_abs_error_mw == 900
    assert result.p95_abs_error_mw == 1000
    assert result.mean_actual_mw == 1000
    assert result.nmae_pct == pytest.approx(55)


def test_under_forecasts_give_negative_bias() -> None:
    assert summarise(errors_of(-50, -150)).bias_mw == -100


def test_nmae_is_undefined_when_there_is_no_wind_at_all() -> None:
    assert summarise(errors_of(10, -10, actual=0)).nmae_pct is None


def test_summarising_nothing_raises() -> None:
    with pytest.raises(InsufficientDataError):
        summarise([])


@pytest.mark.parametrize(
    ("q", "expected"),
    [(0, 10), (25, 10), (26, 20), (50, 20), (75, 30), (90, 40), (100, 40)],
)
def test_percentile_uses_the_nearest_rank(q: float, expected: float) -> None:
    assert percentile([10, 20, 30, 40], q) == expected


def test_percentile_never_reports_a_value_fewer_than_q_percent_stayed_under() -> None:
    values = sorted(float(v) for v in range(1, 745))

    result = percentile(values, 90)

    assert sum(v <= result for v in values) / len(values) >= 0.9


def test_percentile_of_one_value_is_that_value() -> None:
    assert percentile([7], 95) == 7


def test_percentile_rejects_bad_input() -> None:
    with pytest.raises(InsufficientDataError):
        percentile([], 50)
    with pytest.raises(ValueError, match="between 0 and 100"):
        percentile([1], 101)

"""Forecast error and the metric set shown to buyers (ADR-006).

Error is forecast minus actual, in MW. Positive means the forecast was too high, which is the
risky direction: the buyer would under-buy and face a shortfall.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from windfc.errors import InsufficientDataError


@dataclass(frozen=True, slots=True)
class HourlyError:
    """One hour's forecast next to what actually happened."""

    start_time: datetime
    publish_time: datetime
    forecast_mw: float
    actual_mw: float

    @property
    def error_mw(self) -> float:
        """Forecast minus actual. Positive means over-forecast."""
        return self.forecast_mw - self.actual_mw


@dataclass(frozen=True, slots=True)
class ErrorMetrics:
    """Plain-language accuracy numbers, all in MW unless stated."""

    hours: int
    mean_actual_mw: float
    bias_mw: float  # "Tends to over/under-forecast by"
    mae_mw: float  # "Typical miss"
    rmse_mw: float  # "Penalises big misses"
    p90_abs_error_mw: float  # "Misses stay below this 90% of the time"
    p95_abs_error_mw: float  # "Misses stay below this 95% of the time"
    nmae_pct: float | None  # MAE as % of mean actual; None when mean actual is zero


def percentile(sorted_values: Sequence[float], q: float) -> float:
    """The ``q``-th percentile (0 to 100) of already-sorted values, by the nearest-rank method.

    The result is the smallest observed value with at least ``q``% of values at or below it,
    so the buyer-facing wording "misses stay below this q% of the time" is literally true.
    Interpolating methods can return a value that fewer than ``q``% of hours stayed under
    (ADR-006). Equivalent to numpy's ``method="inverted_cdf"``.
    """
    if not sorted_values:
        raise InsufficientDataError("cannot take a percentile of no values")
    if not 0 <= q <= 100:
        raise ValueError(f"q must be between 0 and 100, got {q}")
    rank = max(1, math.ceil(q * len(sorted_values) / 100))
    return sorted_values[rank - 1]


def summarise(errors: Sequence[HourlyError]) -> ErrorMetrics:
    """Compute the metric set over ``errors``. Raises if there are none."""
    if not errors:
        raise InsufficientDataError("no hours with both a forecast and an actual to measure")
    count = len(errors)
    signed = [item.error_mw for item in errors]
    absolute = sorted(abs(value) for value in signed)
    mean_actual = math.fsum(item.actual_mw for item in errors) / count
    mae = math.fsum(absolute) / count
    return ErrorMetrics(
        hours=count,
        mean_actual_mw=mean_actual,
        bias_mw=math.fsum(signed) / count,
        mae_mw=mae,
        rmse_mw=math.sqrt(math.fsum(value * value for value in signed) / count),
        p90_abs_error_mw=percentile(absolute, 90),
        p95_abs_error_mw=percentile(absolute, 95),
        nmae_pct=None if mean_actual == 0 else mae / mean_actual * 100,
    )

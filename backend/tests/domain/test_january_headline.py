"""Pins the January 2026 headline numbers found in the data spike (ADR-001, ADR-007).

P90 and P95 use the nearest-rank method; the spike's first figures (4,248 and 5,294) used a
method that understated them (ADR-006). If this fails, a rule changed: decide deliberately
whether that is intended, then update the numbers and the ADRs together.
"""

from pathlib import Path

import pytest

from windfc.data.loader import load_snapshot
from windfc.domain.evaluation import evaluate
from windfc.domain.metrics import summarise

SNAPSHOT_DIR = Path(__file__).resolve().parents[3] / "data" / "snapshot"


def test_january_at_the_default_cutoff_matches_the_spike() -> None:
    snapshot = load_snapshot(SNAPSHOT_DIR)

    result = evaluate(
        actuals=snapshot.actuals,
        forecasts=snapshot.forecasts,
        window=snapshot.manifest.window,
    )
    metrics = summarise(result.errors)

    assert result.expected_hours == 744
    assert result.hours_without_forecast == ()
    assert result.hours_without_actual == ()
    assert metrics.hours == 744
    assert metrics.mean_actual_mw == pytest.approx(11_581, abs=1)
    assert metrics.bias_mw == pytest.approx(1_852, abs=1)
    assert metrics.mae_mw == pytest.approx(2_142, abs=1)
    assert metrics.rmse_mw == pytest.approx(2_612, abs=1)
    assert metrics.p90_abs_error_mw == pytest.approx(4_322.5, abs=0.1)
    assert metrics.p95_abs_error_mw == pytest.approx(5_309.5, abs=0.1)

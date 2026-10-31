import pytest

from tests.support import actual_row, forecast_row, utc
from windfc.errors import SnapshotError
from windfc.ingestion.parse import parse_actuals, parse_forecasts
from windfc.models import ActualPoint, ForecastPoint


def test_parse_actuals_returns_sorted_points() -> None:
    rows = [
        actual_row(utc(2026, 1, 1, 0, 30), 120),
        actual_row(utc(2026, 1, 1, 0, 0), 100.5),
    ]

    assert parse_actuals(rows) == [
        ActualPoint(utc(2026, 1, 1, 0, 0), 100.5),
        ActualPoint(utc(2026, 1, 1, 0, 30), 120.0),
    ]


def test_parse_actuals_rejects_other_fuel_types() -> None:
    with pytest.raises(SnapshotError, match="expected fuelType WIND"):
        parse_actuals([actual_row(utc(2026, 1, 1), 100, fuel_type="NUCLEAR")])


def test_parse_actuals_rejects_times_off_the_half_hour() -> None:
    with pytest.raises(SnapshotError, match="not on a half-hour"):
        parse_actuals([actual_row(utc(2026, 1, 1, 0, 15), 100)])


def test_parse_actuals_rejects_duplicate_start_times() -> None:
    rows = [actual_row(utc(2026, 1, 1), 100), actual_row(utc(2026, 1, 1), 101)]

    with pytest.raises(SnapshotError, match="duplicate startTime"):
        parse_actuals(rows)


def test_parse_actuals_rejects_missing_start_time() -> None:
    with pytest.raises(SnapshotError, match="startTime"):
        parse_actuals([{"fuelType": "WIND", "generation": 100}])


def test_parse_actuals_rejects_unparseable_timestamps() -> None:
    row = actual_row(utc(2026, 1, 1), 100) | {"startTime": "yesterday"}

    with pytest.raises(SnapshotError, match="startTime"):
        parse_actuals([row])


@pytest.mark.parametrize("generation", [None, "12", True, -1])
def test_parse_actuals_rejects_bad_generation(generation: object) -> None:
    with pytest.raises(SnapshotError, match="generation"):
        parse_actuals([actual_row(utc(2026, 1, 1), generation)])


def test_parse_forecasts_returns_points_sorted_by_start_then_publish() -> None:
    rows = [
        forecast_row(utc(2025, 12, 31, 9, 30), utc(2026, 1, 1, 1), 50),
        forecast_row(utc(2025, 12, 31, 7, 30), utc(2026, 1, 1, 1), 40),
        forecast_row(utc(2025, 12, 31, 7, 30), utc(2026, 1, 1, 0), 30),
    ]

    assert parse_forecasts(rows) == [
        ForecastPoint(utc(2025, 12, 31, 7, 30), utc(2026, 1, 1, 0), 30.0),
        ForecastPoint(utc(2025, 12, 31, 7, 30), utc(2026, 1, 1, 1), 40.0),
        ForecastPoint(utc(2025, 12, 31, 9, 30), utc(2026, 1, 1, 1), 50.0),
    ]


def test_parse_forecasts_rejects_times_off_the_hour() -> None:
    row = forecast_row(utc(2025, 12, 31, 7, 30), utc(2026, 1, 1, 0, 30), 30)

    with pytest.raises(SnapshotError, match="not on the hour"):
        parse_forecasts([row])


def test_parse_forecasts_rejects_repeated_publish_and_start_pairs() -> None:
    row = forecast_row(utc(2025, 12, 31, 7, 30), utc(2026, 1, 1, 0), 30)

    with pytest.raises(SnapshotError, match="duplicate forecast"):
        parse_forecasts([row, row])


def test_parse_forecasts_rejects_missing_generation() -> None:
    row = forecast_row(utc(2025, 12, 31, 7, 30), utc(2026, 1, 1, 0), 30)
    del row["generation"]

    with pytest.raises(SnapshotError, match="generation"):
        parse_forecasts([row])

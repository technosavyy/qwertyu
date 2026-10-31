from datetime import timedelta
from pathlib import Path

import pytest

from tests.support import (
    TWO_DAYS,
    actual_row,
    complete_actual_rows,
    complete_forecast_rows,
    forecast_row,
    utc,
)
from windfc.data.snapshot_format import ACTUALS_FILENAME, FORECASTS_FILENAME, MANIFEST_FILENAME
from windfc.errors import SnapshotError
from windfc.ingestion.build_snapshot import (
    build_snapshot,
    filter_actuals,
    filter_forecasts,
    verify_actuals_complete,
    verify_forecasts_cover_window,
)
from windfc.ingestion.parse import parse_actuals, parse_forecasts
from windfc.models import ActualPoint, ForecastPoint

GENERATED_AT = utc(2026, 10, 31, 12)


def forecast(
    publish: tuple[int, int, int, int, int], start: tuple[int, int, int, int]
) -> ForecastPoint:
    return ForecastPoint(utc(*publish), utc(*start), 1.0)


def test_filter_forecasts_keeps_only_forecasts_published_before_their_own_day() -> None:
    kept_late_night = forecast((2025, 12, 31, 23, 30), (2026, 1, 1, 10))
    kept_days_ahead = forecast((2025, 12, 30, 7, 30), (2026, 1, 2, 3))
    published_at_midnight = forecast((2026, 1, 1, 0, 0), (2026, 1, 1, 10))
    published_same_day = forecast((2026, 1, 1, 2, 30), (2026, 1, 1, 10))
    before_window = forecast((2025, 12, 30, 7, 30), (2025, 12, 31, 23))
    after_window = forecast((2026, 1, 2, 22, 30), (2026, 1, 3, 0))

    result = filter_forecasts(
        [
            kept_late_night,
            kept_days_ahead,
            published_at_midnight,
            published_same_day,
            before_window,
            after_window,
        ],
        TWO_DAYS,
    )

    assert result == [kept_late_night, kept_days_ahead]


def test_filter_actuals_keeps_only_the_window() -> None:
    inside = ActualPoint(utc(2026, 1, 2, 23, 30), 1.0)
    points = [
        ActualPoint(utc(2025, 12, 31, 23, 30), 1.0),
        inside,
        ActualPoint(utc(2026, 1, 3), 1.0),
    ]

    assert filter_actuals(points, TWO_DAYS) == [inside]


def test_verify_actuals_complete_accepts_a_full_window() -> None:
    verify_actuals_complete(parse_actuals(complete_actual_rows(TWO_DAYS)), TWO_DAYS)


def test_verify_actuals_complete_names_the_first_missing_half_hour() -> None:
    rows = [
        row for row in complete_actual_rows(TWO_DAYS) if row["startTime"] != "2026-01-01T05:30:00Z"
    ]

    with pytest.raises(SnapshotError, match=r"missing 1 half-hours.*2026-01-01T05:30:00Z"):
        verify_actuals_complete(parse_actuals(rows), TWO_DAYS)


def test_verify_forecasts_cover_window_accepts_full_coverage() -> None:
    verify_forecasts_cover_window(parse_forecasts(complete_forecast_rows(TWO_DAYS)), TWO_DAYS)


def test_verify_forecasts_cover_window_names_the_first_uncovered_hour() -> None:
    rows = [
        row
        for row in complete_forecast_rows(TWO_DAYS)
        if row["startTime"] != "2026-01-02T07:00:00Z"
    ]

    with pytest.raises(SnapshotError, match=r"missing for 1 hours.*2026-01-02T07:00:00Z"):
        verify_forecasts_cover_window(parse_forecasts(rows), TWO_DAYS)


def test_build_snapshot_writes_the_expected_files(tmp_path: Path) -> None:
    extra_forecasts = [
        forecast_row(utc(2026, 1, 1, 2, 30), utc(2026, 1, 1, 10), 9999),
        forecast_row(utc(2025, 12, 30), utc(2026, 1, 3), 9999),
        forecast_row(utc(2025, 12, 30), utc(2025, 12, 31, 23), 9999),
    ]

    manifest = build_snapshot(
        raw_actuals=complete_actual_rows(TWO_DAYS),
        raw_forecasts=[*complete_forecast_rows(TWO_DAYS), *extra_forecasts],
        window=TWO_DAYS,
        out_dir=tmp_path,
        generated_at=GENERATED_AT,
    )

    assert manifest.actuals.rows == 96
    assert manifest.forecasts.rows == 48
    actual_lines = (tmp_path / ACTUALS_FILENAME).read_text().splitlines()
    assert actual_lines[:2] == ["start_time,generation_mw", "2026-01-01T00:00:00Z,1000"]
    assert actual_lines[-1] == "2026-01-02T23:30:00Z,1095"
    forecast_lines = (tmp_path / FORECASTS_FILENAME).read_text().splitlines()
    assert forecast_lines[:2] == [
        "publish_time,start_time,generation_mw",
        "2025-12-31T23:00:00Z,2026-01-01T00:00:00Z,2000",
    ]
    assert forecast_lines[25] == "2026-01-01T23:00:00Z,2026-01-02T00:00:00Z,2024"
    assert (tmp_path / MANIFEST_FILENAME).is_file()


def test_build_snapshot_is_deterministic(tmp_path: Path) -> None:
    for name in ("one", "two"):
        build_snapshot(
            raw_actuals=complete_actual_rows(TWO_DAYS),
            raw_forecasts=complete_forecast_rows(TWO_DAYS),
            window=TWO_DAYS,
            out_dir=tmp_path / name,
            generated_at=GENERATED_AT,
        )

    for filename in (ACTUALS_FILENAME, FORECASTS_FILENAME, MANIFEST_FILENAME):
        assert (tmp_path / "one" / filename).read_bytes() == (
            tmp_path / "two" / filename
        ).read_bytes()


def test_build_snapshot_writes_nothing_when_actuals_are_incomplete(tmp_path: Path) -> None:
    rows = complete_actual_rows(TWO_DAYS)[:-1]
    out_dir = tmp_path / "snapshot"

    with pytest.raises(SnapshotError, match="actuals are missing 1 half-hours"):
        build_snapshot(
            raw_actuals=rows,
            raw_forecasts=complete_forecast_rows(TWO_DAYS),
            window=TWO_DAYS,
            out_dir=out_dir,
            generated_at=GENERATED_AT,
        )

    assert not out_dir.exists()


def test_build_snapshot_rejects_invalid_raw_rows(tmp_path: Path) -> None:
    rows = [
        *complete_actual_rows(TWO_DAYS),
        actual_row(utc(2026, 1, 1, 0, 0) + timedelta(minutes=5), 1),
    ]

    with pytest.raises(SnapshotError, match="not on a half-hour"):
        build_snapshot(
            raw_actuals=rows,
            raw_forecasts=complete_forecast_rows(TWO_DAYS),
            window=TWO_DAYS,
            out_dir=tmp_path,
            generated_at=GENERATED_AT,
        )

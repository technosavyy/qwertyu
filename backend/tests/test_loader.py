import dataclasses
from pathlib import Path

import pytest

from tests.support import TWO_DAYS, complete_actual_rows, complete_forecast_rows, utc
from windfc.data.loader import load_snapshot
from windfc.data.snapshot_format import (
    ACTUALS_FILENAME,
    FORECASTS_FILENAME,
    MANIFEST_FILENAME,
    SnapshotManifest,
    format_mw,
    sha256_of,
)
from windfc.errors import SnapshotError
from windfc.ingestion.build_snapshot import build_snapshot
from windfc.models import ActualPoint, ForecastPoint


@pytest.fixture
def snapshot_dir(tmp_path: Path) -> Path:
    build_snapshot(
        raw_actuals=complete_actual_rows(TWO_DAYS),
        raw_forecasts=complete_forecast_rows(TWO_DAYS),
        window=TWO_DAYS,
        out_dir=tmp_path,
        generated_at=utc(2026, 10, 31, 12),
    )
    return tmp_path


def rewrite_csv(directory: Path, filename: str, text: str) -> None:
    """Replace a data file and make the manifest agree with it, so only the content is wrong."""
    path = directory / filename
    path.write_text(text, encoding="utf-8")
    manifest = SnapshotManifest.from_json((directory / MANIFEST_FILENAME).read_text())
    section = "actuals" if filename == ACTUALS_FILENAME else "forecasts"
    updated = dataclasses.replace(getattr(manifest, section), sha256=sha256_of(path))
    (directory / MANIFEST_FILENAME).write_text(
        dataclasses.replace(manifest, **{section: updated}).to_json()
    )


def test_loads_exactly_what_was_written(snapshot_dir: Path) -> None:
    snapshot = load_snapshot(snapshot_dir)

    assert len(snapshot.actuals) == 96
    assert snapshot.actuals[0] == ActualPoint(utc(2026, 1, 1, 0, 0), 1000.0)
    assert snapshot.actuals[-1] == ActualPoint(utc(2026, 1, 2, 23, 30), 1095.0)
    assert len(snapshot.forecasts) == 48
    assert snapshot.forecasts[0] == ForecastPoint(utc(2025, 12, 31, 23), utc(2026, 1, 1, 0), 2000.0)
    assert snapshot.manifest.window == TWO_DAYS
    assert snapshot.manifest.generated_at == utc(2026, 10, 31, 12)


def test_manifest_survives_a_json_round_trip(snapshot_dir: Path) -> None:
    manifest = load_snapshot(snapshot_dir).manifest

    assert SnapshotManifest.from_json(manifest.to_json()) == manifest


def test_rejects_a_missing_manifest(tmp_path: Path) -> None:
    with pytest.raises(SnapshotError, match="manifest not found"):
        load_snapshot(tmp_path)


def test_rejects_a_missing_data_file(snapshot_dir: Path) -> None:
    (snapshot_dir / FORECASTS_FILENAME).rename(snapshot_dir / "elsewhere.csv")

    with pytest.raises(SnapshotError, match="file not found"):
        load_snapshot(snapshot_dir)


def test_rejects_a_file_changed_after_the_manifest_was_written(snapshot_dir: Path) -> None:
    with (snapshot_dir / ACTUALS_FILENAME).open("a") as handle:
        handle.write("2026-01-03T00:00:00Z,1\n")

    with pytest.raises(SnapshotError, match="checksum does not match"):
        load_snapshot(snapshot_dir)


def test_rejects_a_row_count_that_disagrees_with_the_manifest(snapshot_dir: Path) -> None:
    text = (snapshot_dir / ACTUALS_FILENAME).read_text().splitlines()
    rewrite_csv(snapshot_dir, ACTUALS_FILENAME, "\n".join(text[:-1]) + "\n")

    with pytest.raises(SnapshotError, match="has 95 rows, manifest says 96"):
        load_snapshot(snapshot_dir)


def test_rejects_unexpected_columns(snapshot_dir: Path) -> None:
    rewrite_csv(snapshot_dir, ACTUALS_FILENAME, "time,mw\n2026-01-01T00:00:00Z,1\n")

    with pytest.raises(SnapshotError, match="expected columns"):
        load_snapshot(snapshot_dir)


def test_rejects_unreadable_values(snapshot_dir: Path) -> None:
    rewrite_csv(
        snapshot_dir, ACTUALS_FILENAME, "start_time,generation_mw\n2026-01-01T00:00:00Z,lots\n"
    )

    with pytest.raises(SnapshotError, match="bad row"):
        load_snapshot(snapshot_dir)


def test_rejects_a_manifest_that_is_not_json(snapshot_dir: Path) -> None:
    (snapshot_dir / MANIFEST_FILENAME).write_text("not json")

    with pytest.raises(SnapshotError, match="manifest is malformed"):
        load_snapshot(snapshot_dir)


def test_rejects_an_unknown_schema_version(snapshot_dir: Path) -> None:
    path = snapshot_dir / MANIFEST_FILENAME
    path.write_text(path.read_text().replace('"schema_version": 1', '"schema_version": 99'))

    with pytest.raises(SnapshotError, match="unsupported snapshot schema_version"):
        load_snapshot(snapshot_dir)


def test_rejects_a_manifest_with_a_non_integer_row_count(snapshot_dir: Path) -> None:
    path = snapshot_dir / MANIFEST_FILENAME
    path.write_text(path.read_text().replace('"rows": 96', '"rows": "96"'))

    with pytest.raises(SnapshotError, match="manifest is malformed"):
        load_snapshot(snapshot_dir)


def test_format_mw_drops_trailing_zero_only_for_whole_numbers() -> None:
    assert format_mw(15538.0) == "15538"
    assert format_mw(12.5) == "12.5"

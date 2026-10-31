"""Load a snapshot from disk, verifying it against its manifest (ADR-003, ADR-009)."""

import csv
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from windfc.data.snapshot_format import (
    ACTUALS_HEADER,
    FORECASTS_HEADER,
    MANIFEST_FILENAME,
    FileInfo,
    SnapshotManifest,
    sha256_of,
)
from windfc.errors import SnapshotError
from windfc.models import ActualPoint, ForecastPoint
from windfc.timeutil import parse_utc

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Everything the application serves from, loaded and verified."""

    manifest: SnapshotManifest
    actuals: tuple[ActualPoint, ...]
    forecasts: tuple[ForecastPoint, ...]


def load_snapshot(directory: Path) -> Snapshot:
    """Read ``directory`` and return its contents, or raise ``SnapshotError``."""
    manifest_path = directory / MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise SnapshotError(f"snapshot manifest not found: {manifest_path}")
    manifest = SnapshotManifest.from_json(manifest_path.read_text(encoding="utf-8"))
    actuals = _read_rows(directory, manifest.actuals, ACTUALS_HEADER, _actual_from_row)
    forecasts = _read_rows(directory, manifest.forecasts, FORECASTS_HEADER, _forecast_from_row)
    return Snapshot(manifest=manifest, actuals=tuple(actuals), forecasts=tuple(forecasts))


def _read_rows(
    directory: Path,
    info: FileInfo,
    header: Sequence[str],
    build: Callable[[dict[str, str]], T],
) -> list[T]:
    path = directory / info.file
    if not path.is_file():
        raise SnapshotError(f"snapshot file not found: {path}")
    if sha256_of(path) != info.sha256:
        raise SnapshotError(f"{info.file}: checksum does not match the manifest")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != tuple(header):
            raise SnapshotError(f"{info.file}: expected columns {list(header)}")
        try:
            items = [build(row) for row in reader]
        except (KeyError, ValueError) as exc:
            raise SnapshotError(f"{info.file}: bad row: {exc!r}") from exc
    if len(items) != info.rows:
        raise SnapshotError(f"{info.file}: has {len(items)} rows, manifest says {info.rows}")
    return items


def _actual_from_row(row: dict[str, str]) -> ActualPoint:
    return ActualPoint(parse_utc(row["start_time"]), float(row["generation_mw"]))


def _forecast_from_row(row: dict[str, str]) -> ForecastPoint:
    return ForecastPoint(
        parse_utc(row["publish_time"]), parse_utc(row["start_time"]), float(row["generation_mw"])
    )

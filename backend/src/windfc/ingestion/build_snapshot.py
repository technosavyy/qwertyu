"""Turn raw Elexon rows into a verified snapshot directory (ADR-003).

The snapshot keeps only what the product can use:

* actuals for the delivery window, which must be complete;
* forecasts for target hours in the window that were published before the start of their
  own delivery day, the latest moment any day-ahead cutoff can fall (ADR-001).

The day boundary is taken in UTC. London is on GMT in January, so the two agree for the
pilot; extending beyond winter would need the London day boundary (ADR-008).
"""

import csv
import logging
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from windfc.constants import ELEXON_BASE_URL
from windfc.data.snapshot_format import (
    ACTUALS_FILENAME,
    ACTUALS_HEADER,
    FORECASTS_FILENAME,
    FORECASTS_HEADER,
    MANIFEST_FILENAME,
    FileInfo,
    SnapshotManifest,
    format_mw,
    sha256_of,
)
from windfc.errors import SnapshotError
from windfc.ingestion.parse import Row, parse_actuals, parse_forecasts
from windfc.models import ActualPoint, DeliveryWindow, ForecastPoint
from windfc.timeutil import format_utc, start_of_day_utc

logger = logging.getLogger(__name__)


def filter_actuals(points: Iterable[ActualPoint], window: DeliveryWindow) -> list[ActualPoint]:
    """Keep actuals whose half-hour falls inside the delivery window."""
    return [point for point in points if window.contains(point.start_time)]


def filter_forecasts(
    points: Iterable[ForecastPoint], window: DeliveryWindow
) -> list[ForecastPoint]:
    """Keep forecasts for hours in the window published before their own delivery day starts."""
    return [
        point
        for point in points
        if window.contains(point.start_time)
        and point.publish_time < start_of_day_utc(point.start_time)
    ]


def verify_actuals_complete(actuals: Iterable[ActualPoint], window: DeliveryWindow) -> None:
    """Raise unless every half-hour in the window has an actual."""
    present = {point.start_time for point in actuals}
    missing = [moment for moment in window.half_hours() if moment not in present]
    if missing:
        raise SnapshotError(
            f"actuals are missing {len(missing)} half-hours; "
            f"first missing: {format_utc(missing[0])}"
        )


def verify_forecasts_cover_window(
    forecasts: Iterable[ForecastPoint], window: DeliveryWindow
) -> None:
    """Raise unless every hour in the window has at least one usable forecast."""
    present = {point.start_time for point in forecasts}
    missing = [moment for moment in window.hours() if moment not in present]
    if missing:
        raise SnapshotError(
            f"forecasts are missing for {len(missing)} hours; "
            f"first missing: {format_utc(missing[0])}"
        )


def build_snapshot(
    *,
    raw_actuals: Iterable[Row],
    raw_forecasts: Iterable[Row],
    window: DeliveryWindow,
    out_dir: Path,
    generated_at: datetime,
) -> SnapshotManifest:
    """Validate raw rows, filter them, and write the snapshot into ``out_dir``."""
    actuals = filter_actuals(parse_actuals(raw_actuals), window)
    forecasts = filter_forecasts(parse_forecasts(raw_forecasts), window)
    verify_actuals_complete(actuals, window)
    verify_forecasts_cover_window(forecasts, window)

    out_dir.mkdir(parents=True, exist_ok=True)
    actuals_info = _write_csv(
        out_dir / ACTUALS_FILENAME,
        ACTUALS_HEADER,
        ([format_utc(p.start_time), format_mw(p.generation_mw)] for p in actuals),
    )
    forecasts_info = _write_csv(
        out_dir / FORECASTS_FILENAME,
        FORECASTS_HEADER,
        (
            [format_utc(p.publish_time), format_utc(p.start_time), format_mw(p.generation_mw)]
            for p in forecasts
        ),
    )
    manifest = SnapshotManifest(
        generated_at=generated_at,
        source_base_url=ELEXON_BASE_URL,
        window=window,
        actuals=actuals_info,
        forecasts=forecasts_info,
    )
    (out_dir / MANIFEST_FILENAME).write_text(manifest.to_json(), encoding="utf-8")
    logger.info(
        "snapshot written to %s: %d actuals, %d forecasts",
        out_dir,
        actuals_info.rows,
        forecasts_info.rows,
    )
    return manifest


def _write_csv(path: Path, header: tuple[str, ...], rows: Iterable[list[str]]) -> FileInfo:
    count = 0
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)
            count += 1
    return FileInfo(file=path.name, rows=count, sha256=sha256_of(path))

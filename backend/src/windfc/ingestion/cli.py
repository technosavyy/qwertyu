"""Command line for the ingestion step. The only place errors become exit codes.

    python -m windfc.ingestion fetch   # download raw Elexon data (needs internet)
    python -m windfc.ingestion build   # raw data -> verified snapshot (offline)

Run both from the repository root.
"""

import argparse
import json
import logging
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path

from windfc.constants import FORECAST_LOOKBACK, PILOT_FIRST_DAY, PILOT_LAST_DAY
from windfc.errors import SnapshotError, WindfcError
from windfc.ingestion.build_snapshot import build_snapshot
from windfc.ingestion.client import ElexonClient
from windfc.models import DeliveryWindow

logger = logging.getLogger(__name__)

RAW_ACTUALS_FILENAME = "fuelhh_wind_2026-01.json"
RAW_FORECASTS_FILENAME = "windfor_raw.json"


def main(argv: Sequence[str] | None = None, *, client: ElexonClient | None = None) -> int:
    """Run the command and return the process exit code (0 ok, 1 failure, 2 bad usage)."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        window = DeliveryWindow(args.first_day, args.last_day)
    except ValueError as exc:
        parser.error(str(exc))
    try:
        if args.command == "fetch":
            _fetch(client or ElexonClient(), window, args.raw_dir)
        else:
            _build(window, args.raw_dir, args.out_dir)
    except WindfcError as exc:
        logger.error("%s", exc)
        return 1
    return 0


def _fetch(client: ElexonClient, window: DeliveryWindow, raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    actuals = client.fetch_actual_rows(window.first_day, window.last_day)
    # A forecast published after the last delivery day starts cannot inform any decision.
    last_day_start = datetime.combine(window.last_day, datetime.min.time(), tzinfo=UTC)
    forecasts = client.fetch_forecast_rows(window.start - FORECAST_LOOKBACK, last_day_start)
    _write_json(raw_dir / RAW_ACTUALS_FILENAME, actuals)
    _write_json(raw_dir / RAW_FORECASTS_FILENAME, forecasts)
    logger.info("raw data saved to %s", raw_dir)


def _build(window: DeliveryWindow, raw_dir: Path, out_dir: Path) -> None:
    build_snapshot(
        raw_actuals=_read_json_rows(raw_dir / RAW_ACTUALS_FILENAME),
        raw_forecasts=_read_json_rows(raw_dir / RAW_FORECASTS_FILENAME),
        window=window,
        out_dir=out_dir,
        generated_at=datetime.now(UTC).replace(microsecond=0),
    )


def _write_json(path: Path, rows: object) -> None:
    path.write_text(json.dumps(rows), encoding="utf-8")


def _read_json_rows(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        raise SnapshotError(f"raw file not found: {path} (run the fetch command first)")
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(rows, list):
        raise SnapshotError(f"{path} should contain a JSON list")
    return rows


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m windfc.ingestion", description=__doc__)
    parser.add_argument("command", choices=["fetch", "build"])
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--out-dir", type=Path, default=Path("data/snapshot"))
    parser.add_argument("--first-day", type=date.fromisoformat, default=PILOT_FIRST_DAY)
    parser.add_argument("--last-day", type=date.fromisoformat, default=PILOT_LAST_DAY)
    return parser

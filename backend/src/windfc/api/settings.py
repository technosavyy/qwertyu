"""Runtime configuration, read from the environment with safe defaults (ADR-011)."""

import os
from pathlib import Path

SNAPSHOT_DIR_ENV = "WINDFC_SNAPSHOT_DIR"
# backend/src/windfc/api/settings.py -> repository root -> data/snapshot
DEFAULT_SNAPSHOT_DIR = Path(__file__).resolve().parents[4] / "data" / "snapshot"


def snapshot_dir() -> Path:
    """Where the snapshot lives. Docker sets ``WINDFC_SNAPSHOT_DIR``; local runs use the repo."""
    return Path(os.environ.get(SNAPSHOT_DIR_ENV, str(DEFAULT_SNAPSHOT_DIR)))

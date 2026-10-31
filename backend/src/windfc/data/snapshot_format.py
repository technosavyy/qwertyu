"""The on-disk snapshot format, shared by the builder and the loader (ADR-003).

A snapshot is a directory holding two CSV files and a manifest that records row counts and
SHA-256 checksums, so a damaged or hand-edited snapshot is detected on load.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from windfc.errors import SnapshotError
from windfc.models import DeliveryWindow
from windfc.timeutil import format_utc, parse_utc

SCHEMA_VERSION = 1
ACTUALS_FILENAME = "actuals.csv"
FORECASTS_FILENAME = "forecasts.csv"
MANIFEST_FILENAME = "manifest.json"
ACTUALS_HEADER = ("start_time", "generation_mw")
FORECASTS_HEADER = ("publish_time", "start_time", "generation_mw")


@dataclass(frozen=True, slots=True)
class FileInfo:
    """What the manifest records about one data file."""

    file: str
    rows: int
    sha256: str


@dataclass(frozen=True, slots=True)
class SnapshotManifest:
    """Describes a snapshot: where it came from, what it covers and how to verify it."""

    generated_at: datetime
    source_base_url: str
    window: DeliveryWindow
    actuals: FileInfo
    forecasts: FileInfo

    def to_json(self) -> str:
        """Serialise to stable, human-readable JSON."""
        document = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": format_utc(self.generated_at),
            "source": {"base_url": self.source_base_url},
            "delivery_window": {
                "first_day": self.window.first_day.isoformat(),
                "last_day": self.window.last_day.isoformat(),
            },
            "actuals": _file_info_to_dict(self.actuals),
            "forecasts": _file_info_to_dict(self.forecasts),
        }
        return json.dumps(document, indent=2) + "\n"

    @classmethod
    def from_json(cls, text: str) -> "SnapshotManifest":
        """Parse a manifest, raising ``SnapshotError`` if it is malformed."""
        try:
            data = json.loads(text)
            if data["schema_version"] != SCHEMA_VERSION:
                raise SnapshotError(
                    f"unsupported snapshot schema_version {data['schema_version']!r}; "
                    f"expected {SCHEMA_VERSION}"
                )
            window = DeliveryWindow(
                date.fromisoformat(data["delivery_window"]["first_day"]),
                date.fromisoformat(data["delivery_window"]["last_day"]),
            )
            return cls(
                generated_at=parse_utc(data["generated_at"]),
                source_base_url=str(data["source"]["base_url"]),
                window=window,
                actuals=_file_info_from_dict(data["actuals"]),
                forecasts=_file_info_from_dict(data["forecasts"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SnapshotError(f"manifest is malformed: {exc!r}") from exc


def sha256_of(path: Path) -> str:
    """SHA-256 of a file's bytes, as lowercase hex."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def format_mw(value: float) -> str:
    """Write whole megawatts without a trailing ``.0`` so the CSV is compact and stable."""
    return str(int(value)) if value.is_integer() else repr(value)


def _file_info_to_dict(info: FileInfo) -> dict[str, object]:
    return {"file": info.file, "rows": info.rows, "sha256": info.sha256}


def _file_info_from_dict(data: dict[str, object]) -> FileInfo:
    rows = data["rows"]
    if isinstance(rows, bool) or not isinstance(rows, int):
        raise ValueError(f"rows must be an integer, got {rows!r}")
    return FileInfo(file=str(data["file"]), rows=rows, sha256=str(data["sha256"]))

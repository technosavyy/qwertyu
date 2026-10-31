"""A six-day synthetic snapshot whose every number can be worked out by hand.

- Actual wind is 1000 MW in every half-hour, except one missing half-hour on 6 Jan (03:30),
  so the hour 03:00 on 6 Jan has no actual.
- Hour number h (0 = 1 Jan 00:00) is forecast as 1000 + 100 * (h % 10) MW, published at 07:30
  on the day before. The error is therefore 100 * (h % 10) MW.
- Each hour also has a late revision of 99,999 MW published at 09:30 on the day before, after
  the default 09:00 cutoff. It must never appear at 09:00.
"""

from datetime import date, timedelta

from tests.support import utc
from windfc.data.loader import Snapshot
from windfc.data.snapshot_format import FileInfo, SnapshotManifest
from windfc.models import ActualPoint, DeliveryWindow, ForecastPoint

WINDOW = DeliveryWindow(date(2026, 1, 1), date(2026, 1, 6))
MISSING_HALF_HOUR = utc(2026, 1, 6, 3, 30)
HOUR_WITHOUT_ACTUAL = utc(2026, 1, 6, 3)
LATE_MW = 99_999.0


def synthetic_snapshot() -> Snapshot:
    actuals = tuple(
        ActualPoint(start, 1000.0) for start in WINDOW.half_hours() if start != MISSING_HALF_HOUR
    )
    forecasts: list[ForecastPoint] = []
    for index, start in enumerate(WINDOW.hours()):
        before = start.date() - timedelta(days=1)
        early = utc(before.year, before.month, before.day, 7, 30)
        late = utc(before.year, before.month, before.day, 9, 30)
        forecasts.append(ForecastPoint(early, start, 1000.0 + 100 * (index % 10)))
        forecasts.append(ForecastPoint(late, start, LATE_MW))
    manifest = SnapshotManifest(
        generated_at=utc(2026, 2, 1, 12),
        source_base_url="https://example.invalid",
        window=WINDOW,
        actuals=FileInfo("actuals.csv", len(actuals), "0" * 64),
        forecasts=FileInfo("forecasts.csv", len(forecasts), "0" * 64),
    )
    return Snapshot(manifest=manifest, actuals=actuals, forecasts=tuple(forecasts))

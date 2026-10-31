"""Guards the snapshot that is committed to the repository and shipped with the app."""

from pathlib import Path

from tests.support import utc
from windfc.constants import PILOT_FIRST_DAY, PILOT_LAST_DAY
from windfc.data.loader import load_snapshot
from windfc.timeutil import start_of_day_utc

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshot"


def test_the_committed_snapshot_is_intact_and_covers_january_2026() -> None:
    snapshot = load_snapshot(SNAPSHOT_DIR)

    assert snapshot.manifest.window.first_day == PILOT_FIRST_DAY
    assert snapshot.manifest.window.last_day == PILOT_LAST_DAY
    assert len(snapshot.actuals) == 31 * 48
    assert snapshot.actuals[0].start_time == utc(2026, 1, 1, 0, 0)
    assert snapshot.actuals[-1].start_time == utc(2026, 1, 31, 23, 30)


def test_every_committed_forecast_was_published_before_its_own_delivery_day() -> None:
    snapshot = load_snapshot(SNAPSHOT_DIR)

    assert snapshot.forecasts
    for point in snapshot.forecasts:
        assert point.publish_time < start_of_day_utc(point.start_time)
        assert point.start_time.minute == 0


def test_every_hour_of_january_has_a_forecast() -> None:
    snapshot = load_snapshot(SNAPSHOT_DIR)

    covered = {point.start_time for point in snapshot.forecasts}

    assert set(snapshot.manifest.window.hours()) == covered

from datetime import UTC, datetime, timedelta, timezone

import pytest

from tests.support import utc
from windfc.timeutil import format_utc, parse_utc, start_of_day_utc


def test_parse_utc_reads_z_suffix() -> None:
    assert parse_utc("2026-01-01T09:30:00Z") == utc(2026, 1, 1, 9, 30)


def test_parse_utc_converts_offsets_to_utc() -> None:
    parsed = parse_utc("2026-01-01T10:30:00+01:00")

    assert parsed == utc(2026, 1, 1, 9, 30)
    assert parsed.utcoffset() == timedelta(0)


def test_parse_utc_rejects_missing_timezone() -> None:
    with pytest.raises(ValueError, match="no timezone"):
        parse_utc("2026-01-01T09:30:00")


def test_parse_utc_rejects_garbage() -> None:
    with pytest.raises(ValueError, match="not an ISO 8601"):
        parse_utc("yesterday")


def test_format_utc_round_trips() -> None:
    assert format_utc(parse_utc("2026-01-01T09:30:00Z")) == "2026-01-01T09:30:00Z"


def test_format_utc_converts_other_zones() -> None:
    plus_one = datetime(2026, 1, 1, 10, 30, tzinfo=timezone(timedelta(hours=1)))

    assert format_utc(plus_one) == "2026-01-01T09:30:00Z"


def test_format_utc_rejects_naive_datetimes() -> None:
    with pytest.raises(ValueError, match="without a timezone"):
        format_utc(datetime(2026, 1, 1, 9, 30))


def test_start_of_day_utc_truncates_to_midnight() -> None:
    assert start_of_day_utc(datetime(2026, 1, 5, 23, 59, 59, 5, tzinfo=UTC)) == utc(2026, 1, 5)

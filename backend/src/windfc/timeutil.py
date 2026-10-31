"""Timestamp helpers. Everything stored or transmitted is timezone-aware UTC (ADR-008)."""

from datetime import UTC, datetime


def parse_utc(value: str) -> datetime:
    """Parse an ISO 8601 timestamp that carries a timezone, returning it in UTC."""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"not an ISO 8601 timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp has no timezone: {value!r}")
    return parsed.astimezone(UTC)


def format_utc(value: datetime) -> str:
    """Format an aware datetime as ISO 8601 UTC with a trailing Z, to the second."""
    if value.tzinfo is None:
        raise ValueError("cannot format a datetime without a timezone")
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def start_of_day_utc(value: datetime) -> datetime:
    """Return 00:00 UTC on the UTC day that contains ``value``."""
    return value.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

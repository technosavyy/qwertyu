"""When a buyer must decide: the cutoff instant for a delivery day (ADR-001, ADR-008)."""

from datetime import UTC, date, datetime, time, timedelta

from windfc.constants import LONDON


def cutoff_instant(delivery_day: date, cutoff_time: time) -> datetime:
    """The moment, in UTC, that ``cutoff_time`` London time occurs on the day before delivery.

    ``cutoff_time`` is a plain wall-clock time with no timezone. During the hour that
    clocks change the wall-clock time may not exist or may occur twice; the first
    occurrence is used. The January pilot is unaffected.
    """
    if cutoff_time.tzinfo is not None:
        raise ValueError("cutoff_time is a London wall-clock time and must not carry a timezone")
    decision_day = delivery_day - timedelta(days=1)
    return datetime.combine(decision_day, cutoff_time, tzinfo=LONDON).astimezone(UTC)

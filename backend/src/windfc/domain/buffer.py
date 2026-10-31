"""How much lower than forecast a buyer should plan for wind to be (ADR-007).

The buffer answers: "In 9 of 10 past hours, the forecast was no more than X MW too high."
It is a percentile of past signed errors (forecast minus actual), so hours where the forecast
was too low count as hours where it was "not too high". It is never negative.

No look-ahead: history only contains hours that had finished by the decision cutoff, so the
buffer is a number the buyer could really have computed at that moment.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from windfc.domain.metrics import HourlyError, percentile

SUPPORTED_CONFIDENCE = (90, 95)
# Three days of hourly history before a buffer is shown; earlier it says "not enough history".
MIN_HISTORY_HOURS = 72
_HOUR = timedelta(hours=1)


@dataclass(frozen=True, slots=True)
class Buffer:
    """A shortfall buffer, or the reason there is none (``buffer_mw`` is None)."""

    confidence: int
    buffer_mw: float | None
    history_hours: int

    @property
    def enough_history(self) -> bool:
        return self.buffer_mw is not None


@dataclass(frozen=True, slots=True)
class BufferBacktest:
    """How often the buffer would have been enough, replayed day by day."""

    confidence: int
    hours_tested: int
    hours_covered: int

    @property
    def coverage_pct(self) -> float | None:
        """Share of tested hours where actual wind was at least forecast minus buffer."""
        return None if self.hours_tested == 0 else self.hours_covered / self.hours_tested * 100


def check_confidence(confidence: int) -> None:
    """Raise ``ValueError`` unless ``confidence`` is one the product offers."""
    if confidence not in SUPPORTED_CONFIDENCE:
        raise ValueError(f"confidence must be one of {SUPPORTED_CONFIDENCE}, got {confidence}")


def known_by(errors: Iterable[HourlyError], cutoff: datetime) -> list[HourlyError]:
    """The errors whose hour had fully finished at ``cutoff``."""
    return [item for item in errors if item.start_time + _HOUR <= cutoff]


def shortfall_buffer(history: Sequence[HourlyError], confidence: int) -> Buffer:
    """The ``confidence`` percentile of past signed errors, floored at zero."""
    check_confidence(confidence)
    if len(history) < MIN_HISTORY_HOURS:
        return Buffer(confidence=confidence, buffer_mw=None, history_hours=len(history))
    signed = sorted(item.error_mw for item in history)
    return Buffer(
        confidence=confidence,
        buffer_mw=max(0.0, percentile(signed, confidence)),
        history_hours=len(history),
    )


def plan_for(forecast_mw: float, buffer: Buffer) -> float | None:
    """The wind level to plan for: forecast minus buffer, never below zero."""
    if buffer.buffer_mw is None:
        return None
    return max(0.0, forecast_mw - buffer.buffer_mw)

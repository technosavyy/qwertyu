# ADR-002: "Latest forecast" means newest publishTime at or before the cutoff

- **Status:** Proposed
- **Date:** 2026-10-31
- **CX principles:** CX2 Trustworthy numbers

## Context

WINDFOR contains many rows for the same `startTime`, one per `publishTime`. Requirement 1 says the buyer must understand "the latest forecasts available when they need to make decisions". This is the core of the product. Picking the wrong row (for example the newest ever published) would show information the buyer did not have at decision time, which flatters the forecast and misleads them.

## Options considered

1. **Newest publishTime overall.** Easy, but uses future information. Rejected: makes accuracy look better than it was.
2. **Oldest publishTime.** Ignores useful updates. Rejected.
3. **Newest publishTime where `publishTime <= cutoff`.** Matches what was knowable at decision time.

## Decision

Option 3. For each target hour `startTime` on delivery day D, select the row with the greatest `publishTime` that is less than or equal to the cutoff on D-1. If no forecast exists before the cutoff, the slot is marked "no forecast available" (see ADR-009).

The rule is displayed in plain English in the UI and in the README.

## CX impact

- Numbers match what a buyer would actually have seen that morning.
- Accuracy statistics are honest because they use only information that existed at decision time.
- A revisions view (same slot, different publish times) lets the buyer see how much the forecast moved.

## Consequences

- Forecasts for early January days are published in late December. Ingestion must fetch publish times before 1 January (ADR-003).
- The selection logic is the most important code in the system and gets the strongest tests (ADR-012).

## Revisit when

The client needs a different notion of availability, for example per-slot lead-time limits.

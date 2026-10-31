# ADR-008: UTC in the API, London time in the UI

- **Status:** Proposed
- **Date:** 2026-10-31
- **CX principles:** CX2 Trustworthy numbers

## Context

Elexon timestamps are UTC. The buyer works in London time. In January, London is on GMT so the two are identical, but the product must not rely on that coincidence. Cutoff times (ADR-001) are defined in London time.

## Options considered

1. **Everything in local time.** Ambiguous around clock changes.
2. **Everything in UTC, including the UI.** Correct but confusing if a buyer thinks in London time.
3. **UTC for storage and API, Europe/London for display and for the cutoff input.**

## Decision

Option 3. All stored and transmitted timestamps are ISO 8601 UTC. The cutoff is entered as a London local time and converted explicitly with the `Europe/London` zone. The UI labels the zone ("09:00 London time (GMT)").

## CX impact

- No off-by-an-hour surprises, which would silently change which forecast is chosen.
- If the product is later extended beyond January, daylight saving is already handled.

## Consequences

- A small conversion layer on the backend and a formatting helper on the frontend.
- Tests include a date that crosses a clock change, even though January does not.

## Revisit when

Never expected; this is a standing rule.

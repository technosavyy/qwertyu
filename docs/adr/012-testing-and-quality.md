# ADR-012: Test the rules the buyer relies on

- **Status:** Proposed
- **Date:** 2026-10-31
- **CX principles:** CX2 Trustworthy numbers

## Context

Time is limited to 16 hours. We cannot test everything equally. The failure that would hurt a buyer most is a wrong number shown confidently, and that failure lives in a few places: forecast selection, metric calculation, the buffer method, and timezone conversion.

## Options considered

1. **Even coverage target (for example 80% everywhere).** Spends time on trivial code.
2. **Risk-based testing:** deep tests on business rules, light tests elsewhere.

## Decision

Option 2.

- **Backend (pytest):** hand-built fixtures with known answers for ADR-002 (selection at, before and after the cutoff, ties, no forecast), ADR-006 (metrics on small known arrays), ADR-007 (no look-ahead, minimum history), ADR-008 (conversion), ADR-009 (gaps).
- **API contract tests:** each endpoint returns the documented shape and rejects dates outside January 2026 with a clear message.
- **Frontend (Vitest + Testing Library):** formatting helpers, and rendering of loading, empty, gap and error states.
- **CI (GitHub Actions):** lint, type-check and tests on every push.
- **Data validation:** ingestion fails loudly on unexpected row counts or fields (ADR-003).

## CX impact

- The numbers on screen are verified against hand-calculated answers.
- Error and empty states are tested, so the buyer never sees a blank page or raw stack trace.

## Consequences

- Some UI code, such as pure styling, is deliberately not unit tested.
- Test fixtures double as worked examples for the tech-lead walkthrough.

## Revisit when

The product grows beyond the pilot, then add end-to-end browser tests.

# ADR-010: Answer-first dashboard layout

- **Status:** Proposed
- **Date:** 2026-10-31
- **CX principles:** CX1 Answer first, CX3 Plain language

## Context

The persona is under time pressure on D-1 morning. Dashboards often start with filters and tables, forcing the user to assemble the answer. Our buyer's question is simple: "What wind can I count on tomorrow, and how much should I allow for error?"

## Options considered

1. **Analyst layout:** filters at top, many equal-weight charts.
2. **Tabs per feature (Forecast, Accuracy, Revisions).** Hides the connection between them.
3. **Single page, ordered by the decision.** Answer first, evidence next, deep-dive last.

## Decision

Option 3. One page, top to bottom:

1. **Decision strip:** delivery day, active cutoff, forecast total or peak, and the buffered "plan for as low as" figure.
2. **Forecast vs actual chart** for the day (24 hourly points, see ADR-013) with an error band.
3. **Accuracy cards:** typical miss, bias, P90/P95, number of slots used.
4. **Error by hour of day** to show when the forecast is least reliable.
5. **Forecast revisions** for a chosen slot (how the number changed over time).
6. **How this is calculated:** collapsible plain-English method and assumptions.

Controls (day and cutoff) sit in the header and update everything at once. The page opens on a sensible default day, never an empty state.

## CX impact

- The most important number is visible without scrolling.
- Detail is available but never in the way.
- Accessibility: keyboard-operable controls, labelled charts, colour not used alone to carry meaning.

## Consequences

- Fewer separate screens, so a longer page. Mitigated with a clear visual hierarchy.
- Chart and cards share one data fetch per selection, simplifying state.

## Revisit when

Usability feedback from real buyers contradicts this ordering.

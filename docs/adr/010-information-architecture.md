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

## Amendment (2026-11-01): the screen as built

The page leads with three things, top to bottom:

1. **Decision clock.** The decision day as a timeline of the eight forecast runs, with the decision time marked. It states which run the decision uses and which it just misses ("The next, at 09:30, arrives 30 minutes too late"). Picking a run sets the decision time to that moment, so the cutoff control is the timeline itself.
2. **Answer panel.** "Plan for this much wind": the plan-for level averaged over the day's hours, the sentence explaining the margin, the tightest hour, the January back-test hit rate next to the target, and how many past hours the margin rests on. Without enough history it shows the forecast and says why there is no margin; with nothing published before the cutoff it says to pick a later run.
3. **Hour by hour.** Each hour as a column: solid up to the plan-for level, hatched orange from there to the forecast (the margin), a level mark for what actually came. Hover, click or arrow keys read out one hour in words, including whether actual wind stayed above the plan.

Below them:

4. **How good is the forecast?** January accuracy at the chosen decision time in four plain figures (typical miss, how far it runs high or low, the misses 9 in 10 and 19 in 20 stay under), the typical miss by hour of day with the worst hour named, and the daily bias, which explains why the back-tested margin falls a little short.
5. **How the forecast changed** for the hour selected on the chart: every forecast published before the day, which were available at the decision time, the one used, the last one, and what came.
6. **How this is calculated**: the rules, assumptions and limits, collapsed by default.

Every chart also gives its values as a table for screen readers.

Day and safety level sit in the top bar. The current view is mirrored in the address bar so it can be shared. Colour is never the only carrier of meaning: every value is also stated in text.

## Revisit when

Usability feedback from real buyers contradicts this ordering.

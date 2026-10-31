# ADR-009: Show gaps, never impute

- **Status:** Proposed
- **Date:** 2026-10-31
- **CX principles:** CX5 Honest about limits, CX2 Trustworthy numbers

## Context

Real data has holes: a half-hour may lack an actual, or a forecast may not exist before the cutoff. Actuals for the final days of January may be incomplete. Filling holes silently (interpolation, zeros) would make the charts look complete while the statistics become fiction.

## Options considered

1. **Interpolate or forward-fill.** Looks smooth, but invents data.
2. **Drop silently.** Statistics are computed on less data without telling the buyer.
3. **Exclude from calculations, show the gap on the chart, and report counts.**

## Decision

Option 3. Missing points render as gaps in the line. Every metric card shows how many slots it is based on ("Based on 22 of 24 hours"). A banner appears when a selected day has incomplete data. Slots with no forecast before cutoff are listed explicitly.

## CX impact

- The buyer always knows how much data sits behind a number.
- Builds trust: the product admits what it does not know.

## Consequences

- API responses carry `null` values and counts, and the frontend must handle them everywhere.
- A little extra UI for banners and counts, which is worth it.

## Revisit when

The client supplies an agreed gap-filling policy.

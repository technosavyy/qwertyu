# ADR-013: Compare forecasts and actuals at hourly resolution

- **Status:** Proposed
- **Date:** 2026-10-31
- **CX principles:** CX2 Trustworthy numbers, CX5 Honest about limits

## Context

The brief describes both datasets as if they share a 30-minute resolution. The data spike (2026-10-31) showed otherwise:

- **FUELHH actuals** are half-hourly: 48 rows per day, MW averaged over 30 minutes.
- **WINDFOR forecasts** have `startTime` values on the hour (for example 21:00Z). One publication carried 73 hourly values.

Joining on exact `startTime` would match only the `:00` half-hours and silently drop the `:30` actuals.

## Options considered

1. **Join on exact `startTime`.** Throws away half the actuals and treats a half-hour as a whole hour.
2. **Spread each hourly forecast over two half-hours (or interpolate).** Invents 30-minute detail the forecast does not contain.
3. **Aggregate actuals to hourly means and compare hour by hour.**

## Decision

Option 3. The actual for hour H is the mean of the half-hours starting at H:00 and H:30. If either half-hour is missing, that hour has no actual (a gap, per ADR-009). All error metrics (ADR-006) and the buffer (ADR-007) are computed on hourly pairs. The day chart shows 24 hourly points.

Alignment: a value stamped H:00 is compared with the hour H:00 to H+1:00, following the meaning of `startTime` in both datasets. The test on the full data is recorded below.

## CX impact

- Like-for-like comparison, so the accuracy numbers can be trusted.
- No hidden data loss and no invented detail.
- Hourly is also a natural unit for day-ahead purchasing.

## Consequences

- The chart has 24 points per day, not 48.
- The alignment assumption must be stated in the README and demo.

## Revisit when

The client needs half-hourly comparison, or the alignment check contradicts the assumption.

## Validation result (2026-10-31)

Three alignments were tested on all January target hours, split into eight forecast lead-time ranges. The hour ending at the stamp had the lowest error in every range, then the hour centred on the stamp, then the hour starting at the stamp (our choice). The gap is small: 30 to 130 MW of mean absolute error, about 2% to 5%. This is weak evidence, so we keep the documented meaning of `startTime`.

The alignment is a single constant in the backend. The README and demo disclose that switching to hour-ending changes accuracy figures by at most about 5%.

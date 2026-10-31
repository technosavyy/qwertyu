# ADR-007: Safety buffer from past errors only (no look-ahead)

- **Status:** Proposed
- **Date:** 2026-10-31
- **CX principles:** CX2 Trustworthy numbers, CX3 Plain language

## Context

The real value of the product is the sentence: "Forecast says 6.0 GW, but plan for as little as 5.1 GW." Computing that honestly is subtle. If the buffer for 10 January uses errors from the whole of January, it uses information the buyer did not have on 9 January. That would overstate how well the buffer works.

## Options considered

1. **Use the whole month's errors for every day.** Simple, but leaks the future.
2. **Fixed percentage of forecast (for example 15%).** Easy, but not grounded in the data.
3. **Use only errors from days before the delivery day (expanding window), taking a percentile of over-forecast error.**

## Decision

Option 3. For delivery day D, build the error distribution from slots on days before D, using the same cutoff rule (ADR-002). The shortfall buffer is the P90 (selectable P95) of positive (over-forecast) errors. The UI presents:

> "Forecast: 6,000 MW. In 9 of 10 past slots the forecast was no more than X MW too high. Plan for wind as low as 6,000 − X MW."

Early days with too little history (fewer than 3 prior days) show "Not enough history yet" instead of a number.

## CX impact

- The buffer is something the buyer could really have computed on the day, so it can be trusted.
- Confidence level (P90 or P95) is a visible choice, not a hidden constant.
- Wording avoids statistical jargon.

## Consequences

- Early January shows fewer buffer values. This is honest, and the UI says so.
- A month-level summary view (all days) is still available but is labelled "retrospective".
- The backtest could also report how often actual wind fell below the buffered level, which validates the method.

## Revisit when

The client wants a day-type or time-of-day specific buffer (for example per hour), once more history exists.

## Spike finding (2026-10-31)

On the full January data the forecast runs high on average. At the 09:00 cutoff, over all 744 hours, retrospectively: mean actual wind 11,581 MW, forecast too high by 1,852 MW on average, typical miss (MAE) 2,142 MW, and a miss no larger than 4,323 MW nine times in ten (5,310 MW nineteen times in twenty; nearest-rank percentiles, see ADR-006). Even forecasts published 0 to 3 hours ahead run about 1,550 MW high, so much of this looks systematic rather than lack of forecast skill. We have not established the cause; one possibility is that the two datasets do not count exactly the same wind.

Because the error is skewed, the buffer must be built from signed errors (forecast minus actual), not absolute ones, and the UI shows the average bias as its own line ("Forecast tends to run 1,850 MW high"). The bias also varies by week (about 1,100 to 2,700 MW), so the expanding-window method here will move from day to day, and this must be explained in the UI. These whole-month figures are retrospective; the no-look-ahead numbers shown to the buyer will differ.

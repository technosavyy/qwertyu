# ADR-006: Error definition and metric set

- **Status:** Proposed
- **Date:** 2026-10-31
- **CX principles:** CX2 Trustworthy numbers, CX3 Plain language

## Context

Requirement 2 asks for quantitative accuracy evaluation "so that they can make their decisions considering the quantified error". We must pick one error definition and a small, meaningful metric set. Too many metrics overwhelm; the wrong ones mislead (for example percentage error explodes when wind is near zero).

## Options considered

Error sign:
1. `actual - forecast`: positive means under-forecast.
2. `forecast - actual`: positive means over-forecast.

Metrics:
- MAPE: unstable near zero generation. Rejected as a headline number.
- RMSE only: hard for buyers to interpret.
- A small set in megawatts plus one relative measure.

## Decision

**Error = forecast − actual**, in MW. Positive means the forecast was too high. This is the risky direction for a buyer, because they would under-buy and face a shortfall.

Metric set, all in MW unless stated:

| Metric | Plain-language label |
|--------|----------------------|
| MAE | Typical miss |
| Bias (mean signed error) | Tends to over/under-forecast by |
| RMSE | Penalises big misses |
| P90 and P95 of absolute error | Misses stay below this 90% / 95% of the time |
| nMAE (MAE ÷ mean actual, %) | Typical miss as % of average wind |

MAPE is not shown.

## CX impact

- Everything is in MW, the unit the buyer already thinks in.
- One consistent sign convention, explained once in the UI.
- Percentile wording directly supports the buffer decision (ADR-007).

## Consequences

- Metrics are computed on the joined forecast/actual set, so missing actuals are excluded and counted (ADR-009).
- Definitions live in one backend module and are quoted verbatim in the UI help text.

## Revisit when

The client defines their own tolerance or cost-of-error asymmetry. Then add a cost-weighted metric.

# ADR-001: Decision cutoff time is configurable, default 09:00 London

- **Status:** Proposed
- **Date:** 2026-10-31
- **CX principles:** CX2 Trustworthy numbers, CX5 Honest about limits

## Context

The brief says purchase decisions are made "one day before the delivery day" but gives no clock time. The whole product depends on this: a forecast published at 08:00 on D-1 is usable, one published at 14:00 is not. Choosing the wrong cutoff silently changes every number the buyer sees.

## Options considered

1. **Midnight (00:00) on D-1.** Simple, but too early. Ignores forecasts the buyer really could have used that morning.
2. **Fixed 09:00 London on D-1.** Close to how GB day-ahead auctions run (morning gate closure), but hard-coded.
3. **Configurable cutoff, default 09:00 London on D-1.** Buyer can change it to match their own desk process.

## Decision

Option 3. The cutoff is an input to every forecast and accuracy API call. Default is 09:00 Europe/London on the day before delivery. The UI shows the active cutoff next to every forecast, and the buyer can change it.

## CX impact

- A buyer whose desk decides at 10:30 sees correct numbers for their process, not ours.
- The cutoff is never hidden: it appears in the page header ("Forecasts as known at 09:00, 14 Jan").
- Avoids the worst failure: confident numbers built on a wrong assumption.

## Consequences

- Every endpoint takes a `cutoff` parameter. More API surface, but it is one parameter used consistently.
- Accuracy numbers change when the cutoff changes. This is correct and must be explained in the UI.
- The 09:00 default is an assumption, to be stated in the README and video.

## Revisit when

The client tells us their real gate-closure time. Replace the default, keep the parameter.

## Spike finding (2026-10-31)

Forecasts are published 8 times a day at 02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30 and 22:30 UTC. The cutoff therefore only matters at these moments. With the 09:00 default, the 07:30 run is used and the 09:30 run is missed by 30 minutes; a 10:00 cutoff would use the 09:30 run. The UI shows which run a cutoff selects ("Using the 07:30 forecast run") and offers the eight run times as quick choices. A cutoff before 02:30 on D-1 leaves hours with no forecast (ADR-009).

# ADR-003: Pre-fetch Elexon data into a versioned snapshot

- **Status:** Proposed
- **Date:** 2026-10-31
- **CX principles:** CX4 Fast and always available, CX2 Trustworthy numbers

## Context

Data comes from two Elexon BMRS stream endpoints (FUELHH for actuals, WINDFOR for forecasts). The scope is a closed period: decisions for January 2026. The data for that period is historical and will not change in ways that matter to this pilot. Stream endpoints may limit the date range per call, and calling a public API at page-load time would make the product slow and fragile.

## Options considered

1. **Call Elexon live on every request.** Always fresh, but slow, rate-limit-prone, and the demo breaks if Elexon is down.
2. **Live call plus cache.** More moving parts, still fails on a cold cache.
3. **Offline ingestion script producing a snapshot file committed or baked into the image.** Fast and deterministic.

## Decision

Option 3. The `windfc.ingestion` package fetches (`python -m windfc.ingestion fetch`, then `build` to create the snapshot offline):

- FUELHH for 1 to 31 January 2026, filtered to `fuelType == "WIND"`.
- WINDFOR for publish times covering late December 2025 through January 2026, so that early-January target slots have forecasts.

It writes a compact snapshot (CSV, so the backend needs no extra dependency) plus a `manifest.json` recording fetch time, row counts, date ranges and source URLs. The deployed app reads only the snapshot.

## CX impact

- Pages load fast and work even if Elexon is offline.
- The manifest lets the UI show "Data as of <date>, source: Elexon BMRS", so the buyer knows where numbers come from.
- Ingestion validates row counts and flags gaps, so bad data is caught before the buyer sees it.

## Consequences

- No live updates. Acceptable: the scope is a closed historical month. A production version would schedule this script.
- Snapshot must be small enough to ship in the image (expected well under a few MB for one month of national wind).
- Spike needed first to confirm the date-range limit per call, exact field names and the publish-time window. Findings update this ADR.

## Revisit when

The client wants live or rolling data. Then add a scheduled ingestion job and a small store.

## Spike findings (2026-10-31)

- **FUELHH:** the server-side `fuelType=WIND` filter works. One row per `startTime`, 48 per day. All of January fits in one call (1,488 rows). Fields: `dataset, fuelType, generation, publishTime, settlementDate, settlementPeriod, startTime`.
- **WINDFOR:** `publishDateTimeFrom` and `publishDateTimeTo` work. Fields: `dataset, generation, publishTime, startTime`. `startTime` is hourly (see ADR-013). One publish day returned 584 rows: 8 publish times with 73 hourly values each. In that sample the gap from publish to target ranged from -25.5h to +66.5h; rows before the publish time are excluded automatically by the selection rule (ADR-002).
- **Size:** about 600 rows per publish day, so roughly 27,000 forecast rows for the whole window. A few MB raw, small enough to ship in the image.
- **Rate limits:** the API documents HTTP 429. The ingestion script retries with backoff.
- **Full download confirmed (2026-10-31):** 1,488 actual rows (no gaps, no nulls) and 26,864 forecast rows from 368 publications. Forecasts are published 8 times a day at 02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30 and 22:30 UTC (one extra off-schedule run at 12:25 on one day). Every publication has 73 hourly values. No duplicate (publishTime, startTime) pairs.
- **Horizon:** at most 66.5 hours ahead. The earliest publication that can matter for a 1 January target is therefore about 29 December 05:30, and ingestion can start at 29 December instead of 17 December.
- **Snapshot filter:** keep only target hours in January 2026 whose publishTime is before the start of their own day (the latest possible D-1 cutoff). This leaves 11,408 of 26,864 forecast rows.

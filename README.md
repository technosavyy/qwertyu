# Wind forecast decision support (pilot)

Helps a UK day-ahead power buyer see the wind forecast available at decision time and how far off such forecasts usually are. Scope: national GB wind, Elexon data (FUELHH actuals, WINDFOR forecasts), decisions for January 2026.

## Status

Design phase. Architecture decisions are in [docs/adr](docs/adr/README.md).

## Files and directories

| Path | Purpose |
|------|---------|
| `docs/adr/` | Architecture decision records, one per decision |
| `backend/` | Python API (FastAPI + pandas) |
| `frontend/` | React + TypeScript dashboard |
| `data/` | Ingestion output: Elexon snapshot and manifest |

## How to start the application

To be completed once the app is built.

## Live app

To be added after deployment.

## AI tools disclosure

This project was built with AI assistance (Claude). Design decisions are recorded in `docs/adr/`.

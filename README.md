# Wind forecast decision support (pilot)

Helps a UK day-ahead power buyer see the wind forecast available at decision time and how far off such forecasts usually are. Scope: national GB wind, Elexon data (FUELHH actuals, WINDFOR forecasts), decisions for January 2026.

## Status

| Area | State |
|------|-------|
| Architecture decisions | Written, see [docs/adr](docs/adr/README.md) |
| Data ingestion and snapshot | Done: verified CSV snapshot in `data/snapshot/` |
| Core rules (selection, metrics, buffer) | Next |
| API, frontend, Docker, deployment | Planned |

## Files and directories

| Path | Purpose |
|------|---------|
| `docs/adr/` | Architecture decision records, one per decision |
| `backend/src/windfc/` | Python package (domain models, ingestion, snapshot loader) |
| `backend/tests/` | Tests, one module per source module |
| `backend/pyproject.toml`, `backend/Makefile` | Dependencies, tool settings, quality gate |
| `frontend/` | React + TypeScript dashboard (not started) |
| `data/snapshot/` | Committed Elexon snapshot the app serves from: `actuals.csv`, `forecasts.csv`, `manifest.json` |
| `data/raw/` | Raw Elexon downloads (git-ignored) |
| `backend/scripts/` | Throwaway data-probing script, removed once ingestion landed |

## Backend: run the quality gate

Needs Python 3.11 or newer.

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
make install
make check        # ruff, mypy --strict, pytest with coverage
```

## Data: rebuild the snapshot

The snapshot is already committed. To rebuild it (from the repository root, with the virtual environment active):

```bash
python -m windfc.ingestion fetch   # downloads raw Elexon data, needs internet
python -m windfc.ingestion build   # raw data -> verified snapshot, works offline
```

The snapshot's manifest records row counts and SHA-256 checksums; the loader refuses a snapshot that does not match.

## How to start the application

To be completed once the API and frontend are built.

## Live app

To be added after deployment.

## AI tools disclosure

This project was built with AI assistance (Claude). Design decisions are recorded in `docs/adr/`.

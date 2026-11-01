# Wind forecast decision support (pilot)

Helps a UK day-ahead power buyer see the wind forecast available at decision time and how far off such forecasts usually are. Scope: national GB wind, Elexon data (FUELHH actuals, WINDFOR forecasts), decisions for January 2026.

## Status

| Area | State |
|------|-------|
| Architecture decisions | Written, see [docs/adr](docs/adr/README.md) |
| Data ingestion and snapshot | Done: verified CSV snapshot in `data/snapshot/` |
| Core rules (selection, alignment, metrics) | Done: `backend/src/windfc/domain/` |
| Safety buffer and API | Done: `backend/src/windfc/services/`, `backend/src/windfc/api/` |
| Frontend: decision strip and controls | Done: `frontend/` |
| Frontend: charts, accuracy, revisions, method | Next |
| Docker, deployment | Planned |

## Files and directories

| Path | Purpose |
|------|---------|
| `docs/adr/` | Architecture decision records, one per decision |
| `backend/src/windfc/` | Python package: `domain/` (pure rules), `services/` (answers per screen), `api/` (HTTP only), `ingestion/`, `data/` |
| `backend/tests/` | Tests, one module per source module |
| `backend/pyproject.toml`, `backend/Makefile` | Dependencies, tool settings, quality gate |
| `frontend/` | React + TypeScript + Vite dashboard: `src/api/` (contract and calls), `src/lib/` (pure logic), `src/components/`, `src/styles/` (design tokens) |
| `data/snapshot/` | Committed Elexon snapshot the app serves from: `actuals.csv`, `forecasts.csv`, `manifest.json` |
| `data/raw/` | Raw Elexon downloads (git-ignored) |

## Backend: run the quality gate

Needs Python 3.11 or newer.

```bash
cd backend
python3 -m venv ~/.venvs/windfc && source ~/.venvs/windfc/bin/activate
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

API (from `backend/`, with the virtual environment active):

```bash
uvicorn windfc.api.main:app --reload
```

Then open http://127.0.0.1:8000/api/docs for interactive API docs.

| Endpoint | Answers |
|----------|---------|
| `GET /api/meta` | Date range, default day and cutoff, buffer levels, forecast run times |
| `GET /api/day?date=2026-01-31&cutoff=09:00&confidence=90` | The forecast available at the cutoff, hour by hour, with actuals and the "plan for" level |
| `GET /api/accuracy?cutoff=09:00&confidence=90` | Accuracy over the month, by hour of day and by day, and how often the buffer would have been enough |
| `GET /api/revisions?start_time=2026-01-31T17:00:00Z` | Every forecast published for one hour, and which one was usable |
| `GET /api/health` | Liveness and snapshot date |

Frontend (needs Node 20 or newer), in a second terminal while the API runs:

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, forwards /api to the API on port 8000
npm run check      # typecheck, lint, tests, production build
```

The address bar holds the current view (`?date=2026-01-31&cutoff=09:00&confidence=90`), so a view can be bookmarked or shared.

## Live app

To be added after deployment.

## AI tools disclosure

This project was built with AI assistance (Claude). Design decisions are recorded in `docs/adr/`.

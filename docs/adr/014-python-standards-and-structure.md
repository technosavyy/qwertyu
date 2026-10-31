# ADR-014: Python code standards and backend structure

- **Status:** Proposed
- **Date:** 2026-10-31
- **CX principles:** CX2 Trustworthy numbers, CX4 Fast and always available

## Context

The buyer's trust rests on a few rules being exactly right: forecast selection, hourly alignment, error metrics and the buffer. Those rules must be easy to read, easy to test and impossible to break by accident. The reviewer will also read the code, so consistency matters. The budget is 16 hours, so quality has to come from cheap automation, not ceremony.

## Options considered

1. **Plain scripts.** Fast to write, hard to test and review. This is what the spike script is.
2. **Heavy enterprise layering** (repositories, dependency-injection containers, ORM). Far more structure than a 27,000-row read-only dataset needs.
3. **Lean layered package, strict typing, automated gates.**

## Decision

Option 3.

### Structure

```
backend/
  pyproject.toml            dependencies and tool config (ruff, mypy, pytest)
  src/windfc/
    config.py               typed, environment-driven settings
    domain/                 pure business rules, no I/O, no web framework
      models.py             frozen dataclasses: ForecastPoint, ActualPoint, ErrorStats, Buffer
      selection.py          latest forecast at or before the cutoff (ADR-002)
      alignment.py          half-hourly actuals to hourly (ADR-013)
      metrics.py            error metrics (ADR-006)
      buffer.py             expanding-window safety buffer (ADR-007)
    data/loader.py          read the snapshot CSV into domain models
    ingestion/
      client.py             Elexon HTTP client: retries, typed errors
      build_snapshot.py     raw files to snapshot CSV plus manifest
    api/                    FastAPI app, routes, response schemas
  tests/                    one test module per source module, no network access
```

Dependencies point one way: `api` and `ingestion` use `domain`; `domain` imports nothing from them.

### Rules

- Python 3.11 or newer (the Docker image pins 3.12), full type hints, `mypy --strict` clean.
- `ruff` for linting and formatting (one tool).
- Domain values are immutable dataclasses; pydantic is used only at the API boundary.
- Domain code uses plain Python and the standard library. Pandas is not needed for this data volume and would enlarge the deployment bundle. Percentile and mean definitions are implemented explicitly and documented, so the buyer-facing numbers have exactly one meaning.
- Timestamps are always timezone-aware UTC (ADR-008). Names carry units (`generation_mw`).
- No `print` in application code; use `logging`. Library code raises typed exceptions (for example `ElexonError`, `SnapshotError`); only command-line entry points turn them into exit codes.
- Small functions with one job, small modules. Docstrings state the business rule in words and cite the ADR.
- Tests use pytest, hand-calculated fixtures and no network (the Elexon client is tested against a fake transport). Domain coverage target 90% or higher.
- Quality gates run locally via pre-commit and in CI on every PR: `ruff check`, `ruff format --check`, `mypy`, `pytest` with a coverage floor. One command runs all of them: `make -C backend check`. A PR cannot merge while a gate fails.
- Dependencies are pinned for a reproducible install.

## CX impact

- The numbers a buyer sees are produced by small pure functions that are tested against hand-checked answers.
- Fewer dependencies means a smaller bundle and faster cold starts on the deployed site.

## Consequences

- PR 2 includes the tooling setup, roughly an hour of upfront work.
- `backend/scripts/spike_elexon.py` is a throwaway and is replaced by `ingestion/` in PR 2, then deleted.
- ADR-004 is amended: pandas is not part of v1.

## Revisit when

Data volume grows beyond what plain Python handles comfortably (roughly a million rows), then introduce a columnar library.

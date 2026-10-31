# ADR-004: Backend: FastAPI + pandas, stateless

- **Status:** Proposed
- **Date:** 2026-10-31
- **CX principles:** CX4 Fast and always available

## Context

The brief requires Python. The workload is small: roughly 1,500 actual rows and a few tens of thousands of forecast rows for one month. The work is selecting rows, joining, and computing statistics.

## Options considered

1. **Flask.** Familiar, but no built-in validation or auto docs.
2. **Django.** Far heavier than needed.
3. **FastAPI + pandas.** Typed request and response models, automatic OpenAPI docs, async-ready, and pandas fits the join and statistics work directly.

## Decision

FastAPI with Pydantic models and pandas. The snapshot is loaded once at startup into memory. No database. The service is stateless, so it scales horizontally and restarts cleanly.

Layering: `api/` (HTTP only) → `services/` (business rules: selection, metrics, buffer) → `data/` (snapshot loading). Business rules never import FastAPI.

## CX impact

- In-memory data means responses in milliseconds, so charts update instantly when the buyer changes the date or cutoff.
- Strict input validation returns clear messages ("Date must be in January 2026") instead of server errors.
- Auto-generated OpenAPI docs make tech-lead review faster.

## Consequences

- Memory use grows with data size. Fine at this scale; documented limit.
- No persistence means no user accounts or saved settings in v1.
- Pure-Python service layer is easy to unit test.

## Revisit when

Data grows beyond memory or multiple regions and fuel types are added. Move to a columnar store.

## Update 2026-10-31

Amended by [ADR-014](014-python-standards-and-structure.md): pandas is not used in v1. The domain rules are plain Python, which keeps the deployment bundle small and each metric explicitly defined. FastAPI and Pydantic are unchanged.

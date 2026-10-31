# Architecture Decision Records

## North Star

**Best customer experience.** Every decision in this folder must show how it serves this goal, or it is rejected.

For this product, "best customer experience" is made concrete as five measurable principles. ADRs cite these by ID.

| ID | Principle | What it means for the buyer |
|----|-----------|-----------------------------|
| CX1 | Answer first | The decision view loads showing tomorrow's forecast and risk. No setup, no digging. |
| CX2 | Trustworthy numbers | Every number can be traced to a rule the buyer can read in plain English. Wrong-but-confident is the worst outcome. |
| CX3 | Plain language | Buyers are energy traders, not statisticians. "Could be 800 MW short" beats "P95 signed error". |
| CX4 | Fast and always available | Page loads in under 2 seconds. No dependence on a third-party API at the moment of use. |
| CX5 | Honest about limits | Missing data, partial days and assumptions are shown, never hidden or silently filled. |

## Persona

**Day-ahead power buyer** at a UK utility. Under time pressure each morning on day D-1. Needs to decide how much extra power to buy for day D. Not a developer, not a data scientist.

## Scope (from the brief)

- National-level GB wind only. Elexon data only (FUELHH actuals, WINDFOR forecasts).
- Purchase decisions made in **January 2026** only (delivery days 1 to 31 January 2026).
- React frontend, Python backend, Docker, deployed on Vercel or Heroku.
- Time budget: 16 hours.

## Decision log

| ADR | Title | Status | Main CX principle |
|-----|-------|--------|-------------------|
| [001](001-decision-cutoff-time.md) | Decision cutoff time is configurable, default 09:00 London | Proposed | CX2, CX5 |
| [002](002-forecast-selection-rule.md) | "Latest forecast" means newest publishTime at or before cutoff | Proposed | CX2 |
| [003](003-data-ingestion-and-snapshot.md) | Pre-fetch Elexon data into a versioned snapshot | Proposed | CX4 |
| [004](004-backend-stack.md) | Backend: FastAPI + pandas, stateless | Proposed | CX4 |
| [005](005-frontend-stack.md) | Frontend: React + TypeScript + Vite + Recharts | Proposed | CX1, CX4 |
| [006](006-error-metrics.md) | Error definition and metric set | Proposed | CX2, CX3 |
| [007](007-risk-buffer-method.md) | Safety buffer from past errors only (no look-ahead) | Proposed | CX2, CX3 |
| [008](008-time-and-timezone.md) | UTC in the API, London time in the UI | Proposed | CX2 |
| [009](009-missing-data-handling.md) | Show gaps, never impute | Proposed | CX5 |
| [010](010-information-architecture.md) | Answer-first dashboard layout | Proposed | CX1, CX3 |
| [011](011-containerisation-and-deployment.md) | One Docker image, deployed to a single public URL | Proposed | CX4 |
| [012](012-testing-and-quality.md) | Test the rules the buyer relies on | Proposed | CX2 |
| [013](013-hourly-comparison-resolution.md) | Compare forecasts and actuals at hourly resolution | Proposed | CX2, CX5 |
| [014](014-python-standards-and-structure.md) | Python code standards and backend structure | Proposed | CX2, CX4 |

## Status meanings

- **Proposed**: written, awaiting review.
- **Accepted**: reviewed and agreed. Code may depend on it.
- **Superseded**: replaced by a later ADR (linked).

## Template

Every ADR uses: Status, Date, Context, Options considered, Decision, CX impact, Consequences, Revisit when.

## Open assumptions needing validation

These are the places where the brief is silent and we chose a default. Each is flagged in its ADR and must be stated in the README and demo video.

1. Cutoff time on D-1 (ADR-001).
2. Which spike findings confirm Elexon API date-range limits and field names (ADR-003).
3. Whether the chosen host can run the backend within size limits (ADR-011).
4. Hourly alignment of forecasts and actuals (ADR-013). Tested: the data mildly favours hour-ending, effect on error at most about 5%. We keep the `startTime` meaning and disclose it.

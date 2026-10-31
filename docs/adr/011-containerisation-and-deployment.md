# ADR-011: One Docker image, deployed to a single public URL

- **Status:** Proposed (needs deployment spike)
- **Date:** 2026-10-31
- **CX principles:** CX4 Fast and always available

## Context

The brief requires Docker and a deployment on Vercel or Heroku. Evaluators open the link cold, possibly in incognito mode. A deployment that sleeps for 30 seconds, or a frontend that cannot reach its backend because of CORS or a wrong URL, would fail the first impression.

## Options considered

1. **Two hosts:** frontend on Vercel, backend elsewhere. Adds CORS, two URLs, and two failure points.
2. **Vercel for both:** static frontend plus Python function reading the bundled snapshot. One URL, no sleeping server. Needs to fit function size limits.
3. **Single container on Heroku:** backend serves the built frontend. One URL, but Heroku container hosting is paid and dynos may sleep on low tiers.

## Decision

Build **one multi-stage Docker image** (Node builds the frontend, Python image serves API and static files) for local and review use via `docker compose up`. For the public deployment, prefer **Option 2 (Vercel)** after a short spike confirming the Python function with pandas fits size limits and cold start is acceptable. If it does not, fall back to Option 3.

Same-origin API (`/api/...`) is used everywhere, so there is no CORS configuration.

## CX impact

- One link, loads immediately, no sleeping server.
- Reviewers can reproduce locally with one command.

## Consequences

- The deployment path is the least certain decision here, so it is validated early rather than at the end.
- Docker image and Vercel deployment must stay equivalent; the same API code runs in both.

## Revisit when

The spike shows size or cold-start problems, or the client requires a specific hosting platform.

## Update 2026-10-31 (data spike)

The snapshot is small (about 27,000 forecast rows plus 1,488 actual rows), so data size is no longer a deployment concern. The remaining risk is the size and cold start of the Python function with pandas. Given the small data, pandas could be dropped if the bundle is too large (see ADR-004).

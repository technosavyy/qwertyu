# ADR-005: Frontend: React + TypeScript + Vite + Recharts

- **Status:** Proposed
- **Date:** 2026-10-31
- **CX principles:** CX1 Answer first, CX4 Fast and always available

## Context

The brief requires React. The UI is a dashboard: date and cutoff controls, a forecast-versus-actual chart, metric cards and an error-by-hour view. It must be fast, readable and accessible.

## Options considered

Build tool:
1. **Create React App.** Deprecated.
2. **Next.js.** Powerful, but server rendering is unnecessary for a single dashboard.
3. **Vite.** Fast builds, small output, simple config.

Charts:
1. **Plotly.** Rich, but a large bundle slows first load.
2. **Chart.js wrapper.** Canvas-based, weaker accessibility and React integration.
3. **Recharts.** Composable React components, SVG output, supports lines, areas (error band) and bars in a small bundle.

## Decision

React + TypeScript + Vite + Recharts. TypeScript types for API responses are kept in one module so frontend and backend contracts stay aligned. Plain CSS with design tokens, no heavy UI framework.

## CX impact

- Small bundle gives a fast first paint.
- SVG charts scale cleanly and can carry accessible labels.
- TypeScript catches contract mistakes before the buyer ever sees a broken chart.

## Consequences

- Recharts has less built-in interactivity than Plotly (no box-zoom). Acceptable for this scope.
- Custom styling is our responsibility, which gives us control over plain-language labels and colour-blind-safe palettes.

## Amendment (2026-11-01): charts are hand-drawn SVG, no Recharts

The one chart the decision needs (hourly columns split into plan-for and margin, with an actual-level mark) is drawn directly in SVG in `HourlyChart.tsx`. It is about 150 lines, adds no dependency, keeps the bundle small (CX4), and gives full control over the hatch pattern, keyboard reading and screen-reader text (CX2, CX3). Recharts can be added later if charts multiply.

## Revisit when

Users need advanced analytical interaction. Then evaluate Plotly or ECharts for specific views.

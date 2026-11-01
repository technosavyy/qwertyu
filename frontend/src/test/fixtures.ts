import type { AccuracyView, DayView, Hour, Meta, Metrics } from "../api/types";

export const meta: Meta = {
  window: { first_day: "2026-01-01", last_day: "2026-01-31" },
  default_day: "2026-01-31",
  default_cutoff: "09:00",
  confidence_options: [90, 95],
  publish_run_times: ["02:30", "04:30", "07:30", "09:30", "11:30", "15:30", "18:30", "22:30"],
  snapshot_generated_at: "2026-10-31T15:55:37Z",
};

const metrics: Metrics = {
  hours: 24,
  mean_actual_mw: 9000,
  bias_mw: 1800,
  mae_mw: 2100,
  rmse_mw: 2600,
  p90_abs_error_mw: 4300,
  p95_abs_error_mw: 5300,
  nmae_pct: 23.3,
};

function hour(index: number, forecast: number | null, planFor: number | null): Hour {
  return {
    start_time: `2026-01-31T${String(index).padStart(2, "0")}:00:00Z`,
    forecast_mw: forecast,
    publish_time: forecast === null ? null : "2026-01-30T07:30:00Z",
    actual_mw: 9000,
    error_mw: forecast === null ? null : forecast - 9000,
    plan_for_mw: planFor,
  };
}

/** 24 hours: forecast 11,000 MW and plan-for 7,000 MW, except 17:00 which plans for 5,000. */
export function dayWithMargin(): DayView {
  return {
    delivery_day: "2026-01-31",
    cutoff: "09:00",
    cutoff_utc: "2026-01-30T09:00:00Z",
    forecast_runs: ["2026-01-30T07:30:00Z"],
    hours: Array.from({ length: 24 }, (_, index) =>
      index === 17 ? hour(index, 9000, 5000) : hour(index, 11000, 7000),
    ),
    buffer: { confidence: 90, buffer_mw: 4000, history_hours: 705, enough_history: true },
    metrics,
    hours_without_forecast: [],
    hours_without_actual: [],
  };
}

export function dayWithoutHistory(): DayView {
  const day = dayWithMargin();
  return {
    ...day,
    delivery_day: "2026-01-04",
    cutoff_utc: "2026-01-03T09:00:00Z",
    forecast_runs: ["2026-01-03T07:30:00Z"],
    hours: day.hours.map((item) => ({ ...item, plan_for_mw: null })),
    buffer: { confidence: 90, buffer_mw: null, history_hours: 57, enough_history: false },
  };
}

export function dayWithoutForecast(): DayView {
  const day = dayWithoutHistory();
  return {
    ...day,
    cutoff: "00:00",
    cutoff_utc: "2026-01-03T00:00:00Z",
    forecast_runs: [],
    hours: day.hours.map((item) => ({
      ...item,
      forecast_mw: null,
      publish_time: null,
      error_mw: null,
    })),
    metrics: null,
    hours_without_forecast: day.hours.map((item) => item.start_time),
  };
}

export const accuracy: AccuracyView = {
  cutoff: "09:00",
  window: meta.window,
  overall: metrics,
  by_hour: [],
  by_day: [],
  expected_hours: 744,
  hours_without_forecast: [],
  hours_without_actual: [],
  backtest: { confidence: 90, hours_tested: 648, hours_covered: 575, coverage_pct: 88.73 },
};

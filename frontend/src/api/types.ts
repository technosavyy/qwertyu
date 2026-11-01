/**
 * The API contract, mirroring backend/src/windfc/api/schemas.py. Change both together.
 *
 * Timestamps are ISO 8601 UTC strings ending in "Z". Dates are "YYYY-MM-DD". Cutoff times are
 * London wall-clock "HH:MM". A null value always means "not known", never zero.
 */

export type IsoUtc = string;
export type IsoDate = string;
export type HhMm = string;
export type Confidence = 90 | 95;

export interface Window {
  first_day: IsoDate;
  last_day: IsoDate;
}

export interface Metrics {
  hours: number;
  mean_actual_mw: number;
  bias_mw: number;
  mae_mw: number;
  rmse_mw: number;
  p90_abs_error_mw: number;
  p95_abs_error_mw: number;
  nmae_pct: number | null;
}

export interface Buffer {
  confidence: number;
  buffer_mw: number | null;
  history_hours: number;
  enough_history: boolean;
}

export interface Backtest {
  confidence: number;
  hours_tested: number;
  hours_covered: number;
  coverage_pct: number | null;
}

export interface Meta {
  window: Window;
  default_day: IsoDate;
  default_cutoff: HhMm;
  confidence_options: number[];
  publish_run_times: HhMm[];
  snapshot_generated_at: IsoUtc;
}

export interface Hour {
  start_time: IsoUtc;
  forecast_mw: number | null;
  publish_time: IsoUtc | null;
  actual_mw: number | null;
  error_mw: number | null;
  plan_for_mw: number | null;
}

export interface DayView {
  delivery_day: IsoDate;
  cutoff: HhMm;
  cutoff_utc: IsoUtc;
  forecast_runs: IsoUtc[];
  hours: Hour[];
  buffer: Buffer;
  metrics: Metrics | null;
  hours_without_forecast: IsoUtc[];
  hours_without_actual: IsoUtc[];
}

export interface AccuracyView {
  cutoff: HhMm;
  window: Window;
  overall: Metrics;
  by_hour: { hour: number; metrics: Metrics }[];
  by_day: { day: IsoDate; metrics: Metrics }[];
  expected_hours: number;
  hours_without_forecast: IsoUtc[];
  hours_without_actual: IsoUtc[];
  backtest: Backtest;
}

export interface Revision {
  publish_time: IsoUtc;
  generation_mw: number;
  hours_ahead: number;
  available_at_cutoff: boolean;
}

export interface RevisionsView {
  start_time: IsoUtc;
  cutoff: HhMm;
  cutoff_utc: IsoUtc;
  revisions: Revision[];
  selected_publish_time: IsoUtc | null;
  actual_mw: number | null;
}

import type { DayView, IsoUtc } from "../api/types";

/** What the decision strip says about a day, worked out from its hours. */
export interface DaySummary {
  hoursWithForecast: number;
  meanForecastMw: number | null;
  meanPlanForMw: number | null;
  tightestHour: { startTime: IsoUtc; planForMw: number } | null;
}

function mean(values: number[]): number | null {
  if (values.length === 0) return null;
  return values.reduce((total, value) => total + value, 0) / values.length;
}

export function summariseDay(day: DayView): DaySummary {
  const forecasts: number[] = [];
  const planFor: number[] = [];
  let tightest: DaySummary["tightestHour"] = null;

  for (const hour of day.hours) {
    if (hour.forecast_mw !== null) forecasts.push(hour.forecast_mw);
    if (hour.plan_for_mw !== null) {
      planFor.push(hour.plan_for_mw);
      if (tightest === null || hour.plan_for_mw < tightest.planForMw) {
        tightest = { startTime: hour.start_time, planForMw: hour.plan_for_mw };
      }
    }
  }

  return {
    hoursWithForecast: forecasts.length,
    meanForecastMw: mean(forecasts),
    meanPlanForMw: mean(planFor),
    tightestHour: tightest,
  };
}

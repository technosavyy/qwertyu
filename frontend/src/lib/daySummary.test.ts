import { describe, expect, it } from "vitest";

import { dayWithMargin, dayWithoutForecast, dayWithoutHistory } from "../test/fixtures";
import { summariseDay } from "./daySummary";

describe("summariseDay", () => {
  it("averages forecast and plan-for, and finds the tightest hour", () => {
    const summary = summariseDay(dayWithMargin());

    expect(summary.hoursWithForecast).toBe(24);
    expect(summary.meanForecastMw).toBeCloseTo((23 * 11000 + 9000) / 24);
    expect(summary.meanPlanForMw).toBeCloseTo((23 * 7000 + 5000) / 24);
    expect(summary.tightestHour).toEqual({ startTime: "2026-01-31T17:00:00Z", planForMw: 5000 });
  });

  it("has no plan-for without a margin", () => {
    const summary = summariseDay(dayWithoutHistory());

    expect(summary.meanForecastMw).toBeCloseTo(11000 - 2000 / 24);
    expect(summary.meanPlanForMw).toBeNull();
    expect(summary.tightestHour).toBeNull();
  });

  it("has nothing to average without forecasts", () => {
    expect(summariseDay(dayWithoutForecast()).meanForecastMw).toBeNull();
  });
});

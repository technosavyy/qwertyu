import { describe, expect, it } from "vitest";

import { formatDuration, minutesOf, runTiming } from "./runs";

const RUNS = ["02:30", "04:30", "07:30", "09:30", "11:30", "15:30", "18:30", "22:30"];

describe("runTiming", () => {
  it("finds the run in use and the one just missed", () => {
    expect(runTiming(RUNS, "09:00")).toEqual({
      used: "07:30",
      next: { run: "09:30", minutesLate: 30 },
    });
  });

  it("counts a run published exactly at the decision time as in use", () => {
    expect(runTiming(RUNS, "11:30").used).toBe("11:30");
  });

  it("handles a decision before the first run and after the last", () => {
    expect(runTiming(RUNS, "01:00")).toEqual({ used: null, next: { run: "02:30", minutesLate: 90 } });
    expect(runTiming(RUNS, "23:00")).toEqual({ used: "22:30", next: null });
  });
});

describe("formatting durations and times", () => {
  it("reads minutes after midnight", () => {
    expect(minutesOf("09:30")).toBe(570);
  });

  it("says durations in words", () => {
    expect(formatDuration(1)).toBe("1 minute");
    expect(formatDuration(30)).toBe("30 minutes");
    expect(formatDuration(90)).toBe("1 hour 30 minutes");
    expect(formatDuration(240)).toBe("4 hours");
  });
});

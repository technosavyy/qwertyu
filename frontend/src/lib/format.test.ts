import { describe, expect, it } from "vitest";

import {
  confidenceInWords,
  formatDeliveryDay,
  formatHourRange,
  formatLondonShortDay,
  formatLondonTime,
  formatMw,
  formatPct,
} from "./format";

describe("format", () => {
  it("rounds megawatts to whole numbers with thousands separators", () => {
    expect(formatMw(11404.4)).toBe("11,404");
    expect(formatMw(11404.5)).toBe("11,405");
  });

  it("shows percentages to one decimal place", () => {
    expect(formatPct(88.734)).toBe("88.7%");
  });

  it("shows times in London time, including summer time", () => {
    expect(formatLondonTime("2026-01-30T07:30:00Z")).toBe("07:30");
    expect(formatLondonTime("2026-07-30T07:30:00Z")).toBe("08:30");
  });

  it("formats days without browser-specific punctuation", () => {
    expect(formatLondonShortDay("2026-01-30T07:30:00Z")).toBe("Fri 30 Jan");
    expect(formatDeliveryDay("2026-01-31")).toBe("Saturday 31 January 2026");
  });

  it("formats an hour as a range that can cross midnight", () => {
    expect(formatHourRange("2026-01-31T23:00:00Z")).toBe("23:00–00:00");
  });

  it("puts the confidence level into words", () => {
    expect(confidenceInWords(90)).toBe("9 out of 10");
    expect(confidenceInWords(95)).toBe("19 out of 20");
  });
});

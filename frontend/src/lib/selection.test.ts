import { describe, expect, it } from "vitest";

import { meta } from "../test/fixtures";
import { cutoffOptions, selectionFromQuery, selectionToQuery } from "./selection";

describe("selection", () => {
  it("reads a valid selection from the address bar", () => {
    expect(selectionFromQuery("?date=2026-01-15&cutoff=10:30&confidence=95", meta)).toEqual({
      date: "2026-01-15",
      cutoff: "10:30",
      confidence: 95,
    });
  });

  it("falls back to defaults for anything invalid or out of range", () => {
    expect(selectionFromQuery("?date=2026-02-01&cutoff=25:00&confidence=7", meta)).toEqual({
      date: "2026-01-31",
      cutoff: "09:00",
      confidence: 90,
    });
  });

  it("round-trips through the query string", () => {
    const selection = { date: "2026-01-15", cutoff: "09:30", confidence: 95 } as const;

    expect(selectionFromQuery(selectionToQuery(selection), meta)).toEqual(selection);
  });

  it("offers the default, the current choice and every forecast run, in time order", () => {
    const options = cutoffOptions(meta, "10:15");

    expect(options[0]).toBe("02:30");
    expect(options).toContain("09:00");
    expect(options).toContain("10:15");
    expect(new Set(options).size).toBe(options.length);
    expect([...options].sort()).toEqual(options);
  });
});

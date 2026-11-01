import { describe, expect, it } from "vitest";

import { niceAxis } from "./scale";

describe("niceAxis", () => {
  it("rounds the maximum up to a whole step", () => {
    expect(niceAxis(18_338)).toEqual({ max: 20_000, step: 5_000 });
    expect(niceAxis(13_200)).toEqual({ max: 15_000, step: 5_000 });
    expect(niceAxis(7_900)).toEqual({ max: 8_000, step: 2_000 });
  });

  it("still draws an axis when there is nothing to show", () => {
    expect(niceAxis(0)).toEqual({ max: 1_000, step: 250 });
  });
});

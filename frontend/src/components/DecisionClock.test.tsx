import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { meta } from "../test/fixtures";
import { DecisionClock } from "./DecisionClock";

function renderClock(cutoff: string, onChange = vi.fn()) {
  render(
    <DecisionClock
      runs={meta.publish_run_times}
      cutoff={cutoff}
      defaultCutoff="09:00"
      cutoffUtc="2026-01-30T09:00:00Z"
      onChange={onChange}
    />,
  );
  return onChange;
}

describe("DecisionClock", () => {
  it("says which run the decision time catches and which it misses", () => {
    renderClock("09:00");

    expect(screen.getByRole("heading", { name: "Decide at 09:00 on Fri 30 Jan" })).toBeInTheDocument();
    expect(
      screen.getByText("Uses the 07:30 forecast. The next, at 09:30, arrives 30 minutes too late."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /07:30 run \(in use\)/ })).toBeInTheDocument();
  });

  it("sets the decision time to the run the buyer picks", async () => {
    const onChange = renderClock("09:00");

    await userEvent.setup().click(screen.getByRole("button", { name: /after the 11:30 run/ }));

    expect(onChange).toHaveBeenCalledWith("11:30");
  });

  it("offers a way back to the default only when it has been changed", () => {
    renderClock("09:00");

    expect(screen.queryByRole("button", { name: "Back to 09:00" })).not.toBeInTheDocument();
  });

  it("returns to the default time", async () => {
    const onChange = renderClock("11:30");

    await userEvent.setup().click(screen.getByRole("button", { name: "Back to 09:00" }));

    expect(onChange).toHaveBeenCalledWith("09:00");
  });
});

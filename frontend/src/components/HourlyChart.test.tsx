import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { dayWithMargin, dayWithoutHistory } from "../test/fixtures";
import { HourlyChart } from "./HourlyChart";

describe("HourlyChart", () => {
  it("opens on the tightest hour and reads it out", () => {
    render(<HourlyChart hours={dayWithMargin().hours} />);

    expect(screen.getByText("17:00–18:00")).toBeInTheDocument();
    expect(screen.getByText("5,000 MW")).toBeInTheDocument();
    expect(screen.getByText("Actual wind stayed above the plan.")).toBeInTheDocument();
  });

  it("steps through hours with the arrow keys", async () => {
    const user = userEvent.setup();
    render(<HourlyChart hours={dayWithMargin().hours} />);

    await user.click(screen.getByRole("group", { name: /Hourly forecast chart/ }));
    await user.keyboard("{ArrowRight}");

    expect(screen.getByText("18:00–19:00")).toBeInTheDocument();
  });

  it("explains that there is no plan-for level without a margin", () => {
    render(<HourlyChart hours={dayWithoutHistory().hours} />);

    expect(screen.getByText("00:00–01:00")).toBeInTheDocument();
    expect(screen.getByText("No margin yet")).toBeInTheDocument();
  });
});

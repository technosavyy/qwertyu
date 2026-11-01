import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { accuracy, dayWithMargin, dayWithoutForecast, dayWithoutHistory } from "../test/fixtures";
import { DecisionStrip } from "./DecisionStrip";

describe("DecisionStrip", () => {
  it("answers first: what to plan for, and why", () => {
    render(<DecisionStrip day={dayWithMargin()} backtest={accuracy.backtest} />);

    expect(
      screen.getByRole("heading", { name: "Plan for this much wind on Saturday 31 January 2026" }),
    ).toBeInTheDocument();
    expect(screen.getByText("6,917")).toBeInTheDocument(); // (23 x 7,000 + 5,000) / 24
    expect(
      screen.getByText(/In 9 out of 10 past hours it was no more than 4,000 MW too high/),
    ).toBeInTheDocument();
    expect(screen.getByText("17:00–18:00, plan for 5,000 MW")).toBeInTheDocument();
    expect(screen.getByText("88.7% of hours (575 of 648), aiming for 90%")).toBeInTheDocument();
    expect(screen.getByText("705 hours")).toBeInTheDocument();
  });

  it("says plainly when there is not enough history for a margin", () => {
    render(<DecisionStrip day={dayWithoutHistory()} backtest={undefined} />);

    expect(screen.getByRole("heading", { name: /^Forecast wind on/ })).toBeInTheDocument();
    expect(screen.getByText(/No safety margin yet/)).toHaveTextContent("only 57 were known");
    expect(screen.queryByText(/Margin held/)).not.toBeInTheDocument();
  });

  it("tells the buyer what to do when nothing had been published", () => {
    render(<DecisionStrip day={dayWithoutForecast()} backtest={undefined} />);

    expect(
      screen.getByText("No forecast had been published by 00:00. Choose a later run on the timeline."),
    ).toBeInTheDocument();
  });

  it("lists hours that had no forecast by the decision time", () => {
    const day = dayWithMargin();
    day.hours_without_forecast = ["2026-01-31T03:00:00Z"];

    render(<DecisionStrip day={day} backtest={undefined} />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "1 of 24 hours had no forecast by the decision time: 03:00–04:00.",
    );
  });
});

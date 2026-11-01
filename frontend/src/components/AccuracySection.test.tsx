import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { accuracy } from "../test/fixtures";
import { AccuracySection } from "./AccuracySection";

describe("AccuracySection", () => {
  it("states the month's accuracy in plain words", () => {
    render(<AccuracySection accuracy={accuracy} />);

    expect(screen.getByText(/Based on 24 of 744 hours/)).toBeInTheDocument();
    expect(screen.getByText("2,100")).toBeInTheDocument();
    expect(screen.getByText("23.3% of the average wind")).toBeInTheDocument();
    expect(screen.getByText("Runs high by")).toBeInTheDocument();
    expect(screen.getByText("1,800")).toBeInTheDocument();
    expect(screen.getByText("4,300")).toBeInTheDocument();
    expect(screen.getByText("5,300")).toBeInTheDocument();
  });

  it("names the worst hour and the range of daily bias", () => {
    render(<AccuracySection accuracy={accuracy} />);

    expect(screen.getByText("Worst between 05:00 and the next hour: 2,535 MW.")).toBeInTheDocument();
    expect(
      screen.getByText(/^730 MW too low on its best day, 5,375 MW too high on its worst\./),
    ).toBeInTheDocument();
  });

  it("gives each chart's values as a table for screen readers", () => {
    render(<AccuracySection accuracy={accuracy} />);

    const table = screen.getByRole("table", { name: "Average over-forecast by delivery day of January" });
    expect(table).toHaveTextContent("-730");
  });

  it("says when the forecast ran low instead of high", () => {
    render(
      <AccuracySection accuracy={{ ...accuracy, overall: { ...accuracy.overall, bias_mw: -400 } }} />,
    );

    expect(screen.getByText("Runs low by")).toBeInTheDocument();
    expect(screen.getByText("400")).toBeInTheDocument();
  });
});

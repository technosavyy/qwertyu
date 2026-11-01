import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { revisions } from "../test/fixtures";
import { RevisionsPanel } from "./RevisionsPanel";

function stubFetch(body: unknown, status = 200) {
  const fetchMock = vi.fn<typeof fetch>(async () =>
    new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("RevisionsPanel", () => {
  it("tells the story of one hour's forecast", async () => {
    stubFetch(revisions);

    render(<RevisionsPanel startTime="2026-01-31T17:00:00Z" cutoff="09:00" />);

    expect(
      screen.getByRole("heading", { name: "How the forecast for 17:00–18:00 on Sat 31 Jan changed" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByText(
        "Published 3 times before the day began. At the decision time it said 11,404 MW (the 07:30 run). The last update before the day said 10,800 MW, and 8,750 MW actually came.",
      ),
    ).toBeInTheDocument();
  });

  it("says when nothing had been published by the decision time", async () => {
    stubFetch({ ...revisions, selected_publish_time: null, actual_mw: null });

    render(<RevisionsPanel startTime="2026-01-31T17:00:00Z" cutoff="00:00" />);

    expect(await screen.findByText(/Nothing had been published by the decision time\./)).toBeInTheDocument();
  });

  it("shows a problem it cannot recover from on its own", async () => {
    stubFetch({ detail: "start_time must be the start of an hour" }, 422);

    render(<RevisionsPanel startTime="2026-01-31T17:00:00Z" cutoff="09:00" />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Start_time must be the start of an hour.");
  });
});

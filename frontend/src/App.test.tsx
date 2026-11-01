import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { accuracy, dayWithMargin, meta, revisions } from "./test/fixtures";

function respond(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  window.history.replaceState(null, "", "/");
  fetchMock.mockImplementation(async (input) => {
    const url = String(input);
    if (url.startsWith("/api/meta")) return respond(meta);
    if (url.startsWith("/api/day")) return respond(dayWithMargin());
    if (url.startsWith("/api/accuracy")) return respond(accuracy);
    if (url.startsWith("/api/revisions")) return respond(revisions);
    return respond({ detail: "not found" }, 404);
  });
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  fetchMock.mockReset();
});

describe("App", () => {
  it("opens on the default day with the answer showing", async () => {
    render(<App />);

    expect(await screen.findByText("6,917")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/day?date=2026-01-31&cutoff=09%3A00&confidence=90",
      expect.anything(),
    );
    expect(window.location.search).toBe("?date=2026-01-31&cutoff=09%3A00&confidence=90");
  });

  it("asks again when the buyer changes the safety level", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("6,917");

    const group = screen.getByRole("group", { name: "Margin covers" });
    await user.click(within(group).getByLabelText("19 in 20 hours"));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/day?date=2026-01-31&cutoff=09%3A00&confidence=95",
      expect.anything(),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/accuracy?cutoff=09%3A00&confidence=95",
      expect.anything(),
    );
  });

  it("moves the decision time when the buyer picks a forecast run", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("6,917");

    await user.click(screen.getByRole("button", { name: /after the 11:30 run/ }));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/day?date=2026-01-31&cutoff=11%3A30&confidence=90",
      expect.anything(),
    );
  });

  it("steps to the previous day", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("6,917");

    await user.click(screen.getByRole("button", { name: "Previous day" }));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/day?date=2026-01-30&cutoff=09%3A00&confidence=90",
      expect.anything(),
    );
  });

  it("shows accuracy, the selected hour's history and the method", async () => {
    render(<App />);

    expect(await screen.findByRole("heading", { name: "How good is the forecast?" })).toBeInTheDocument();
    expect(await screen.findByText(/^Published 3 times before the day began/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "How this is calculated" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/revisions?start_time=2026-01-31T17%3A00%3A00Z&cutoff=09%3A00",
      expect.anything(),
    );
  });

  it("explains a failure and recovers on retry", async () => {
    fetchMock.mockImplementationOnce(async () => respond({ detail: "snapshot unavailable" }, 503));
    const user = userEvent.setup();
    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Snapshot unavailable.");
    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByText("6,917")).toBeInTheDocument();
  });
});

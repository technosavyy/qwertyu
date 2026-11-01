import type {
  AccuracyView,
  Confidence,
  DayView,
  HhMm,
  IsoDate,
  IsoUtc,
  Meta,
  RevisionsView,
} from "./types";

/** An API call failed. ``message`` is safe to show to the buyer. */
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type Params = Record<string, string | number>;

async function getJson<T>(path: string, params: Params, signal: AbortSignal): Promise<T> {
  const query = new URLSearchParams(
    Object.entries(params).map(([key, value]) => [key, String(value)]),
  ).toString();
  let response: Response;
  try {
    response = await fetch(query ? `${path}?${query}` : path, {
      signal,
      headers: { Accept: "application/json" },
    });
  } catch (error) {
    if (signal.aborted) throw error;
    throw new ApiError("Could not reach the forecast service. Check your connection and try again.", 0);
  }
  if (!response.ok) {
    throw new ApiError(await failureMessage(response), response.status);
  }
  return (await response.json()) as T;
}

async function failureMessage(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null && "detail" in body) {
      const { detail } = body as { detail: unknown };
      if (typeof detail === "string") return capitalise(detail);
    }
  } catch {
    // Not JSON: fall through to a generic message.
  }
  return `The forecast service returned an error (${response.status}). Try again in a moment.`;
}

function capitalise(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1) + (text.endsWith(".") ? "" : ".");
}

export interface DayQuery {
  date: IsoDate;
  cutoff: HhMm;
  confidence: Confidence;
}

export const api = {
  meta: (signal: AbortSignal) => getJson<Meta>("/api/meta", {}, signal),
  day: (query: DayQuery, signal: AbortSignal) =>
    getJson<DayView>("/api/day", { ...query }, signal),
  accuracy: (query: Omit<DayQuery, "date">, signal: AbortSignal) =>
    getJson<AccuracyView>("/api/accuracy", { ...query }, signal),
  revisions: (query: { start_time: IsoUtc; cutoff: HhMm }, signal: AbortSignal) =>
    getJson<RevisionsView>("/api/revisions", { ...query }, signal),
};

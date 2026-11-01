import type { Confidence, HhMm, IsoDate, Meta } from "../api/types";

/** What the buyer is looking at. Mirrored in the address bar so a view can be shared. */
export interface Selection {
  date: IsoDate;
  cutoff: HhMm;
  confidence: Confidence;
}

const DATE = /^\d{4}-\d{2}-\d{2}$/;
const HHMM = /^([01]\d|2[0-3]):[0-5]\d$/;

/** Read a selection from a query string, falling back to the API defaults for anything invalid. */
export function selectionFromQuery(query: string, meta: Meta): Selection {
  const params = new URLSearchParams(query);
  const date = params.get("date");
  const cutoff = params.get("cutoff");
  const confidence = Number(params.get("confidence"));
  const inWindow =
    date !== null && DATE.test(date) && date >= meta.window.first_day && date <= meta.window.last_day;
  return {
    date: inWindow ? date : meta.default_day,
    cutoff: cutoff !== null && HHMM.test(cutoff) ? cutoff : meta.default_cutoff,
    confidence: confidence === 95 ? 95 : 90,
  };
}

export function selectionToQuery(selection: Selection): string {
  return new URLSearchParams({
    date: selection.date,
    cutoff: selection.cutoff,
    confidence: String(selection.confidence),
  }).toString();
}

/** Decision times to offer: the default, the current choice, and each regular forecast run. */
export function cutoffOptions(meta: Meta, current: HhMm): HhMm[] {
  return [...new Set([meta.default_cutoff, current, ...meta.publish_run_times])].sort();
}

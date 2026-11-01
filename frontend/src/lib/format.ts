/** Formatting for buyers: British English, London time, whole megawatts (ADR-008). */

const LONDON = "Europe/London";

const mwFormat = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 });
const pctFormat = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 1 });
const londonTime = new Intl.DateTimeFormat("en-GB", {
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
  timeZone: LONDON,
});
const londonShortDay = new Intl.DateTimeFormat("en-GB", {
  weekday: "short",
  day: "numeric",
  month: "short",
  timeZone: LONDON,
});
const longDay = new Intl.DateTimeFormat("en-GB", {
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

/** 11404.4 -> "11,404". */
export function formatMw(value: number): string {
  return mwFormat.format(Math.round(value));
}

/** 88.73 -> "88.7%". */
export function formatPct(value: number): string {
  return `${pctFormat.format(value)}%`;
}

/** "2026-01-30T07:30:00Z" -> "07:30" in London time. */
export function formatLondonTime(iso: string): string {
  return londonTime.format(new Date(iso));
}

/** "2026-01-30T07:30:00Z" -> "Fri 30 Jan" in London time. */
export function formatLondonShortDay(iso: string): string {
  return londonShortDay.format(new Date(iso));
}

/** "2026-01-31" -> "Saturday 31 January 2026", the same in every browser. */
export function formatDeliveryDay(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const parts = longDay.formatToParts(new Date(Date.UTC(year ?? 0, (month ?? 1) - 1, day ?? 1)));
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((item) => item.type === type)?.value ?? "";
  return `${part("weekday")} ${part("day")} ${part("month")} ${part("year")}`;
}

/** An hour starting at ``iso``, as "03:00–04:00" London time. */
export function formatHourRange(iso: string): string {
  const start = new Date(iso);
  const end = new Date(start.getTime() + 60 * 60 * 1000);
  return `${londonTime.format(start)}–${londonTime.format(end)}`;
}

/** 90 -> "9 out of 10", 95 -> "19 out of 20". */
export function confidenceInWords(confidence: number): string {
  return confidence === 95 ? "19 out of 20" : "9 out of 10";
}

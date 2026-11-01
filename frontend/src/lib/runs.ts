import type { HhMm } from "../api/types";

/** Minutes after midnight for "HH:MM". */
export function minutesOf(time: HhMm): number {
  const [hours, minutes] = time.split(":").map(Number);
  return (hours ?? 0) * 60 + (minutes ?? 0);
}

export interface RunTiming {
  /** The newest regular run at or before the cutoff, if any. */
  used: HhMm | null;
  /** The first regular run after the cutoff, and how many minutes after it, if any. */
  next: { run: HhMm; minutesLate: number } | null;
}

/** Which forecast run a decision time catches, and which one it just misses. */
export function runTiming(runs: HhMm[], cutoff: HhMm): RunTiming {
  const at = minutesOf(cutoff);
  const sorted = [...runs].sort((a, b) => minutesOf(a) - minutesOf(b));
  const before = sorted.filter((run) => minutesOf(run) <= at);
  const after = sorted.find((run) => minutesOf(run) > at);
  return {
    used: before.at(-1) ?? null,
    next: after ? { run: after, minutesLate: minutesOf(after) - at } : null,
  };
}

/** 30 -> "30 minutes", 90 -> "1 hour 30 minutes", 120 -> "2 hours". */
export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  const parts = [];
  if (hours > 0) parts.push(`${hours} hour${hours === 1 ? "" : "s"}`);
  if (rest > 0 || hours === 0) parts.push(`${rest} minute${rest === 1 ? "" : "s"}`);
  return parts.join(" ");
}

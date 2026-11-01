/** A "nice" axis maximum and step for megawatt values, e.g. 13,200 -> max 14,000 step 2,000. */
export function niceAxis(maxValue: number, ticks = 4): { max: number; step: number } {
  if (!(maxValue > 0)) return { max: 1000, step: 250 };
  const rough = maxValue / ticks;
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= rough) ?? rough;
  return { max: Math.ceil(maxValue / step) * step, step };
}

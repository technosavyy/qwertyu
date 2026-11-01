import { type KeyboardEvent, useEffect, useRef, useState } from "react";

import type { Hour } from "../api/types";
import { formatHourRange, formatLondonTime, formatMw } from "../lib/format";
import { niceAxis } from "../lib/scale";

interface Props {
  hours: Hour[];
}

const HEIGHT = 340;
const PAD = { top: 12, right: 8, bottom: 28, left: 52 };
const FALLBACK_WIDTH = 720;

function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(FALLBACK_WIDTH);
  useEffect(() => {
    const element = ref.current;
    if (!element || typeof ResizeObserver === "undefined") return undefined;
    const observer = new ResizeObserver(([entry]) => {
      const measured = entry?.contentRect.width ?? 0;
      if (measured > 0) setWidth(measured);
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  return [ref, width] as const;
}

function describe(hour: Hour): string {
  if (hour.actual_mw === null || hour.plan_for_mw === null) return "";
  const gap = hour.actual_mw - hour.plan_for_mw;
  return gap >= 0
    ? "Actual wind stayed above the plan."
    : `Actual wind fell ${formatMw(-gap)} MW below the plan.`;
}

/**
 * Each hour as a column: solid up to the plan-for level (wind to count on), hatched from there
 * to the forecast (the margin held back), with a level mark for what actually came.
 */
export function HourlyChart({ hours }: Props) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [selected, setSelected] = useState(() => {
    const tightest = hours.reduce(
      (best, hour, index) =>
        hour.plan_for_mw !== null &&
        (best < 0 || hour.plan_for_mw < (hours[best]?.plan_for_mw ?? Infinity))
          ? index
          : best,
      -1,
    );
    return tightest < 0 ? 0 : tightest;
  });

  const values = hours.flatMap((hour) => [hour.forecast_mw ?? 0, hour.actual_mw ?? 0]);
  const axis = niceAxis(Math.max(0, ...values));
  const plotWidth = Math.max(1, width - PAD.left - PAD.right);
  const plotHeight = HEIGHT - PAD.top - PAD.bottom;
  const step = plotWidth / Math.max(1, hours.length);
  const column = Math.max(2, step * 0.68);
  const y = (mw: number) => PAD.top + plotHeight * (1 - mw / axis.max);
  const ticks = Array.from({ length: Math.round(axis.max / axis.step) + 1 }, (_, i) => i * axis.step);
  const current = hours[selected];
  const labelEvery = width < 480 ? 6 : 3;

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "ArrowRight") setSelected((index) => Math.min(hours.length - 1, index + 1));
    else if (event.key === "ArrowLeft") setSelected((index) => Math.max(0, index - 1));
    else return;
    event.preventDefault();
  }

  return (
    <section className="chart" aria-labelledby="chart-heading">
      <div className="chart__head">
        <h2 id="chart-heading" className="chart__title">
          Hour by hour
        </h2>
        <ul className="chart__legend">
          <li>
            <span className="swatch swatch--plan" aria-hidden="true" />
            Plan for
          </li>
          <li>
            <span className="swatch swatch--margin" aria-hidden="true" />
            Margin, up to the forecast
          </li>
          <li>
            <span className="swatch swatch--actual" aria-hidden="true" />
            What actually came
          </li>
        </ul>
      </div>

      <div
        ref={ref}
        className="chart__plot"
        tabIndex={0}
        role="group"
        aria-label="Hourly forecast chart. Use the left and right arrow keys to read each hour."
        onKeyDown={onKeyDown}
      >
        <svg width={width} height={HEIGHT} aria-hidden="true">
          <defs>
            <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <rect width="6" height="6" className="chart__hatch-ground" />
              <rect width="2.5" height="6" className="chart__hatch-line" />
            </pattern>
          </defs>
          {ticks.map((tick) => (
            <g key={tick}>
              <line className="chart__grid" x1={PAD.left} x2={width - PAD.right} y1={y(tick)} y2={y(tick)} />
              <text className="chart__axis" x={PAD.left - 8} y={y(tick)} dy="0.32em" textAnchor="end">
                {formatMw(tick)}
              </text>
            </g>
          ))}
          {hours.map((hour, index) => {
            const x = PAD.left + index * step + (step - column) / 2;
            const isSelected = index === selected;
            return (
              <g key={hour.start_time} className={isSelected ? "chart__hour is-selected" : "chart__hour"}>
                <rect
                  className="chart__hit"
                  x={PAD.left + index * step}
                  y={PAD.top}
                  width={step}
                  height={plotHeight}
                  onMouseEnter={() => setSelected(index)}
                  onClick={() => setSelected(index)}
                />
                {hour.forecast_mw !== null && hour.plan_for_mw !== null ? (
                  <>
                    <rect className="chart__plan" x={x} width={column} y={y(hour.plan_for_mw)} height={y(0) - y(hour.plan_for_mw)} />
                    <rect
                      className="chart__margin"
                      x={x}
                      width={column}
                      y={y(hour.forecast_mw)}
                      height={Math.max(0, y(hour.plan_for_mw) - y(hour.forecast_mw))}
                    />
                  </>
                ) : hour.forecast_mw !== null ? (
                  <rect className="chart__forecast" x={x} width={column} y={y(hour.forecast_mw)} height={y(0) - y(hour.forecast_mw)} />
                ) : null}
                {hour.actual_mw !== null ? (
                  <rect className="chart__actual" x={x - 2} width={column + 4} y={y(hour.actual_mw) - 1.5} height={3} />
                ) : null}
                {index % labelEvery === 0 ? (
                  <text className="chart__axis" x={PAD.left + index * step + step / 2} y={HEIGHT - 8} textAnchor="middle">
                    {formatLondonTime(hour.start_time)}
                  </text>
                ) : null}
              </g>
            );
          })}
        </svg>
      </div>

      {current ? (
        <div className="readout" aria-live="polite">
          <p className="readout__hour">{formatHourRange(current.start_time)}</p>
          <dl className="readout__values">
            <div>
              <dt>Forecast</dt>
              <dd>{current.forecast_mw === null ? "None yet" : `${formatMw(current.forecast_mw)} MW`}</dd>
            </div>
            <div>
              <dt>Plan for</dt>
              <dd>{current.plan_for_mw === null ? "No margin yet" : `${formatMw(current.plan_for_mw)} MW`}</dd>
            </div>
            <div>
              <dt>Actual</dt>
              <dd>{current.actual_mw === null ? "Not known yet" : `${formatMw(current.actual_mw)} MW`}</dd>
            </div>
          </dl>
          <p className="readout__verdict">{describe(current)}</p>
        </div>
      ) : null}
    </section>
  );
}

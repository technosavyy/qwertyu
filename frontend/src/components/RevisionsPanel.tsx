import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { HhMm, IsoUtc, RevisionsView } from "../api/types";
import { useApi } from "../api/useApi";
import { formatHourRange, formatLondonShortDay, formatLondonTime, formatMw } from "../lib/format";
import { niceAxis } from "../lib/scale";
import { useWidth } from "../lib/useWidth";
import { StatusMessage } from "./StatusMessage";

interface Props {
  startTime: IsoUtc;
  cutoff: HhMm;
}

/** Every forecast ever published for one hour, and which one the buyer could use. */
/** ``value``, but only once it has stopped changing for ``delay`` ms (so hovering is quiet). */
function useSettled<T>(value: T, delay: number): T {
  const [settled, setSettled] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setSettled(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return settled;
}

export function RevisionsPanel({ startTime: liveStartTime, cutoff }: Props) {
  const startTime = useSettled(liveStartTime, 200);
  const revisions = useApi(`revisions?${startTime}&${cutoff}`, (signal) =>
    api.revisions({ start_time: startTime, cutoff }, signal),
  );
  const hour = `${formatHourRange(startTime)} on ${formatLondonShortDay(startTime)}`;

  return (
    <section className="revisions" aria-labelledby="revisions-heading" aria-busy={revisions.loading}>
      <h2 id="revisions-heading" className="section-title">
        How the forecast for {hour} changed
      </h2>
      {revisions.error ? (
        <StatusMessage message={revisions.error} onRetry={revisions.retry} />
      ) : revisions.data ? (
        <RevisionsBody view={revisions.data} />
      ) : (
        <p className="loading">Loading the forecast history…</p>
      )}
    </section>
  );
}

const HEIGHT = 220;
const PAD = { top: 12, right: 12, bottom: 28, left: 52 };

function RevisionsBody({ view }: { view: RevisionsView }) {
  const [ref, width] = useWidth<HTMLElement>(640);
  const points = view.revisions;
  const used = points.find((point) => point.publish_time === view.selected_publish_time);
  const last = points.at(-1);
  if (points.length === 0 || !last) return <p>No forecast was ever published for this hour.</p>;

  const values = [...points.map((point) => point.generation_mw), view.actual_mw ?? 0];
  const axis = niceAxis(Math.max(...values));
  const earliest = Math.ceil(Math.max(...points.map((point) => point.hours_ahead)) / 12) * 12;
  const plotWidth = width - PAD.left - PAD.right;
  const plotHeight = HEIGHT - PAD.top - PAD.bottom;
  const x = (hoursAhead: number) => PAD.left + plotWidth * (1 - hoursAhead / earliest);
  const y = (mw: number) => PAD.top + plotHeight * (1 - mw / axis.max);
  const cutoffAhead = (Date.parse(view.start_time) - Date.parse(view.cutoff_utc)) / 3_600_000;
  const path = points
    .map((point, index) => {
      const next = points[index + 1];
      const end = next ? x(next.hours_ahead) : x(0);
      return `${index === 0 ? "M" : "L"}${x(point.hours_ahead)},${y(point.generation_mw)}H${end}`;
    })
    .join("");
  const tickEvery = width < 480 ? 24 : 12;
  const xTicks = Array.from(
    { length: Math.floor(earliest / tickEvery) + 1 },
    (_, index) => index * tickEvery,
  );

  return (
    <div className="revisions__body">
      <p className="revisions__story">
        Published {points.length} times before the day began.{" "}
        {used
          ? `At the decision time it said ${formatMw(used.generation_mw)} MW (the ${formatLondonTime(used.publish_time)} run).`
          : "Nothing had been published by the decision time."}{" "}
        The last update before the day said {formatMw(last.generation_mw)} MW
        {view.actual_mw === null ? "." : `, and ${formatMw(view.actual_mw)} MW actually came.`}
      </p>
      <figure className="revisions__figure" ref={ref}>
        <svg width={width} height={HEIGHT} role="img" aria-label="Forecast for this hour by hours before it began">
          {[0, axis.max / 2, axis.max].map((tick) => (
            <g key={tick}>
              <line className="column-chart__grid" x1={PAD.left} x2={width - PAD.right} y1={y(tick)} y2={y(tick)} />
              <text className="column-chart__axis" x={PAD.left - 6} y={y(tick)} dy="0.32em" textAnchor="end">
                {formatMw(tick)}
              </text>
            </g>
          ))}
          {xTicks.map((tick) => (
            <text key={tick} className="column-chart__axis" x={x(tick)} y={HEIGHT - 8} textAnchor="middle">
              {tick === 0 ? "start" : `${tick} h before`}
            </text>
          ))}
          {cutoffAhead >= 0 && cutoffAhead <= earliest ? (
            <g>
              <line className="revisions__cutoff" x1={x(cutoffAhead)} x2={x(cutoffAhead)} y1={PAD.top} y2={HEIGHT - PAD.bottom} />
              <text className="revisions__cutoff-label" x={x(cutoffAhead) + 6} y={PAD.top + 10}>
                decision {view.cutoff}
              </text>
            </g>
          ) : null}
          {view.actual_mw !== null ? (
            <line className="revisions__actual" x1={PAD.left} x2={width - PAD.right} y1={y(view.actual_mw)} y2={y(view.actual_mw)} />
          ) : null}
          <path className="revisions__line" d={path} />
          {points.map((point) => (
            <circle
              key={point.publish_time}
              className={`revisions__point${point.available_at_cutoff ? " is-available" : ""}${point === used ? " is-used" : ""}`}
              cx={x(point.hours_ahead)}
              cy={y(point.generation_mw)}
              r={point === used ? 6 : 3.5}
            />
          ))}
        </svg>
        <figcaption className="revisions__key">
          <span>
            <span className="swatch swatch--plan" aria-hidden="true" /> Published before the decision
          </span>
          <span>
            <span className="swatch swatch--late" aria-hidden="true" /> Published after
          </span>
          <span>
            <span className="swatch swatch--actual" aria-hidden="true" /> What actually came
          </span>
        </figcaption>
      </figure>
    </div>
  );
}

import type { AccuracyView } from "../api/types";
import { formatMw, formatPct } from "../lib/format";
import { ColumnChart } from "./ColumnChart";

interface Props {
  accuracy: AccuracyView;
}

function shortDay(isoDate: string): string {
  return String(Number(isoDate.slice(8, 10)));
}

/** 5375 -> "5,375 MW too high", -730 -> "730 MW too low". */
function describeBias(mw: number): string {
  return `${formatMw(Math.abs(mw))} MW too ${mw >= 0 ? "high" : "low"}`;
}

/** How good the forecast was over the whole month, at the chosen decision time (ADR-006). */
export function AccuracySection({ accuracy }: Props) {
  const { overall } = accuracy;
  const byHour = accuracy.by_hour.map((item) => ({
    label: `${String(item.hour).padStart(2, "0")}:00`,
    value: item.metrics.mae_mw,
  }));
  const worstHour = byHour.reduce(
    (worst, item, index) => (item.value > (byHour[worst]?.value ?? -Infinity) ? index : worst),
    0,
  );
  const byDay = accuracy.by_day.map((item) => ({ label: shortDay(item.day), value: item.metrics.bias_mw }));
  const biases = byDay.map((item) => item.value);
  const runsHigh = overall.bias_mw >= 0;

  return (
    <section className="accuracy" aria-labelledby="accuracy-heading">
      <div className="accuracy__intro">
        <h2 id="accuracy-heading" className="section-title">
          How good is the forecast?
        </h2>
        <p>
          Every hour of January, using the forecast available at {accuracy.cutoff} the day before,
          compared with the wind that came. Based on {overall.hours} of {accuracy.expected_hours}{" "}
          hours.
        </p>
      </div>

      <dl className="metrics">
        <div>
          <dt>Typical miss</dt>
          <dd>
            {formatMw(overall.mae_mw)} <span>MW</span>
          </dd>
          <p>
            {overall.nmae_pct === null ? "" : `${formatPct(overall.nmae_pct)} of the average wind`}
          </p>
        </div>
        <div>
          <dt>{runsHigh ? "Runs high by" : "Runs low by"}</dt>
          <dd className={runsHigh ? "is-risk" : undefined}>
            {formatMw(Math.abs(overall.bias_mw))} <span>MW</span>
          </dd>
          <p>{runsHigh ? "on average, so it tends to promise too much" : "on average"}</p>
        </div>
        <div>
          <dt>9 in 10 misses are under</dt>
          <dd>
            {formatMw(overall.p90_abs_error_mw)} <span>MW</span>
          </dd>
          <p>in either direction</p>
        </div>
        <div>
          <dt>19 in 20 misses are under</dt>
          <dd>
            {formatMw(overall.p95_abs_error_mw)} <span>MW</span>
          </dd>
          <p>in either direction</p>
        </div>
      </dl>

      <div className="accuracy__charts">
        <div>
          <h3 className="chart-title">Typical miss by hour of day</h3>
          <p className="chart-note">
            Worst between {byHour[worstHour]?.label} and the next hour:{" "}
            {formatMw(byHour[worstHour]?.value ?? 0)} MW.
          </p>
          <ColumnChart
            columns={byHour}
            title="Typical miss by hour of day, London time"
            valueLabel="Typical miss (MW)"
            format={formatMw}
            tone="size"
            labelEvery={6}
            highlight={worstHour}
          />
        </div>
        <div>
          <h3 className="chart-title">How far off it ran, day by day</h3>
          <p className="chart-note">
            {biases.length > 0
              ? `${describeBias(Math.min(...biases))} on its best day, ${describeBias(Math.max(...biases))} on its worst. Because this drifts, a margin from past days can fall a little short.`
              : "No days to show."}
          </p>
          <ColumnChart
            columns={byDay}
            title="Average over-forecast by delivery day of January"
            valueLabel="Runs high by (MW)"
            format={formatMw}
            tone="signed"
            labelEvery={5}
          />
        </div>
      </div>
    </section>
  );
}

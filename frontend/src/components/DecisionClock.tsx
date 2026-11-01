import type { HhMm, IsoUtc } from "../api/types";
import { formatLondonShortDay } from "../lib/format";
import { formatDuration, minutesOf, runTiming } from "../lib/runs";

interface Props {
  runs: HhMm[];
  cutoff: HhMm;
  defaultCutoff: HhMm;
  cutoffUtc: IsoUtc;
  onChange: (cutoff: HhMm) => void;
}

const DAY_MINUTES = 24 * 60;
const DAY_EDGES = [0, 24];

function position(time: HhMm): string {
  return `${(minutesOf(time) / DAY_MINUTES) * 100}%`;
}

/**
 * The decision day as a timeline: the eight forecast runs, and where the decision time falls
 * among them. Choosing a run sets the decision time to the moment it is published.
 */
export function DecisionClock({ runs, cutoff, defaultCutoff, cutoffUtc, onChange }: Props) {
  const timing = runTiming(runs, cutoff);
  const decisionDay = formatLondonShortDay(cutoffUtc);

  return (
    <section className="clock" aria-labelledby="clock-heading">
      <div className="clock__text">
        <h2 id="clock-heading" className="clock__title">
          Decide at {cutoff} on {decisionDay}
        </h2>
        <p className="clock__note">
          {timing.used
            ? `Uses the ${timing.used} forecast.`
            : "No forecast run has been published yet that day."}{" "}
          {timing.next
            ? `The next, at ${timing.next.run}, arrives ${formatDuration(timing.next.minutesLate)} too late.`
            : "It is the last run of the day."}
        </p>
      </div>

      <div className="clock__track" role="group" aria-label="Forecast runs on the decision day, London time">
        <div className="clock__rail" aria-hidden="true">
          <div className="clock__known" style={{ width: position(cutoff) }} />
        </div>
        {DAY_EDGES.map((hour) => (
          <span
            key={hour}
            className="clock__hour"
            style={{ left: `${(hour / 24) * 100}%` }}
            aria-hidden="true"
          >
            {String(hour).padStart(2, "0")}:00
          </span>
        ))}
        <span className="clock__cutoff" style={{ left: position(cutoff) }} aria-hidden="true">
          <span className="clock__cutoff-label">{cutoff}</span>
        </span>
        {runs.map((run) => {
          const available = minutesOf(run) <= minutesOf(cutoff);
          const used = run === timing.used;
          const next = run === timing.next?.run;
          return (
            <button
              key={run}
              type="button"
              className={`clock__run${available ? " is-available" : ""}${used ? " is-used" : ""}${next ? " is-next" : ""}`}
              style={{ left: position(run) }}
              aria-pressed={cutoff === run}
              aria-label={`Decide right after the ${run} run${used ? " (in use)" : ""}`}
              onClick={() => onChange(run)}
            >
              <span className="clock__run-dot" aria-hidden="true" />
              <span className="clock__run-label" aria-hidden="true">
                {run}
              </span>
            </button>
          );
        })}
      </div>

      {cutoff !== defaultCutoff ? (
        <button type="button" className="text-button" onClick={() => onChange(defaultCutoff)}>
          Back to {defaultCutoff}
        </button>
      ) : null}
    </section>
  );
}

import type { Backtest, DayView } from "../api/types";
import { summariseDay } from "../lib/daySummary";
import {
  confidenceInWords,
  formatDeliveryDay,
  formatHourRange,
  formatMw,
  formatPct,
} from "../lib/format";

interface Props {
  day: DayView;
  backtest: Backtest | undefined;
}

/** The answer first (ADR-010): how much wind to plan for, and why that much. */
export function DecisionStrip({ day, backtest }: Props) {
  const summary = summariseDay(day);
  const deliveryDay = formatDeliveryDay(day.delivery_day);

  if (summary.meanForecastMw === null) {
    return (
      <section className="answer" aria-labelledby="answer-heading">
        <h2 id="answer-heading" className="answer__lede">
          {deliveryDay}
        </h2>
        <p className="answer__empty">
          No forecast had been published by {day.cutoff}. Choose a later run on the timeline.
        </p>
      </section>
    );
  }

  const buffer = day.buffer.buffer_mw;
  const missing = day.hours_without_forecast;
  const hasMargin = buffer !== null && summary.meanPlanForMw !== null;

  return (
    <section className="answer" aria-labelledby="answer-heading">
      <h2 id="answer-heading" className="answer__lede">
        {hasMargin ? `Plan for this much wind on ${deliveryDay}` : `Forecast wind on ${deliveryDay}`}
      </h2>
      <p className="answer__figure">
        <span className="answer__number">
          {formatMw(hasMargin ? (summary.meanPlanForMw ?? 0) : summary.meanForecastMw)}
        </span>
        <span className="answer__unit">MW</span>
      </p>
      <p className="answer__qualifier">average over the day’s 24 hours</p>

      {hasMargin ? (
        <p className="answer__reason">
          The forecast says {formatMw(summary.meanForecastMw)} MW. In{" "}
          {confidenceInWords(day.buffer.confidence)} past hours it was no more than{" "}
          {formatMw(buffer ?? 0)} MW too high, so that much is held back.
        </p>
      ) : (
        <p className="answer__reason answer__reason--warning">
          No safety margin yet. It needs 72 hours of past results and only{" "}
          {day.buffer.history_hours} were known by the decision time. Treat this forecast with
          extra care.
        </p>
      )}

      {missing.length > 0 ? (
        <p className="answer__notice" role="status">
          {missing.length} of {day.hours.length} hours had no forecast by the decision time:{" "}
          {missing.map(formatHourRange).join(", ")}.
        </p>
      ) : null}

      <dl className="answer__facts">
        {summary.tightestHour ? (
          <div>
            <dt>Tightest hour</dt>
            <dd>
              {formatHourRange(summary.tightestHour.startTime)}, plan for{" "}
              {formatMw(summary.tightestHour.planForMw)} MW
            </dd>
          </div>
        ) : null}
        {backtest && backtest.coverage_pct !== null ? (
          <div>
            <dt>Margin held in January</dt>
            <dd>
              {formatPct(backtest.coverage_pct)} of hours ({backtest.hours_covered} of{" "}
              {backtest.hours_tested}), aiming for {backtest.confidence}%
            </dd>
          </div>
        ) : null}
        <div>
          <dt>Past results behind the margin</dt>
          <dd>{day.buffer.history_hours} hours</dd>
        </div>
      </dl>
    </section>
  );
}

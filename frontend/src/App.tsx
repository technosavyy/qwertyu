import { type ReactNode, useEffect, useState } from "react";

import { api } from "./api/client";
import type { Meta } from "./api/types";
import { useApi } from "./api/useApi";
import { AccuracySection } from "./components/AccuracySection";
import { DayPicker } from "./components/DayPicker";
import { DecisionClock } from "./components/DecisionClock";
import { DecisionStrip } from "./components/DecisionStrip";
import { HourlyChart } from "./components/HourlyChart";
import { MethodPanel } from "./components/MethodPanel";
import { RevisionsPanel } from "./components/RevisionsPanel";
import { SafetyLevel } from "./components/SafetyLevel";
import { StatusMessage } from "./components/StatusMessage";
import { formatLondonShortDay } from "./lib/format";
import { selectionFromQuery, selectionToQuery, type Selection } from "./lib/selection";

export function App() {
  const meta = useApi("meta", api.meta);

  if (meta.data) return <Dashboard meta={meta.data} />;
  return (
    <Page>
      {meta.error ? (
        <StatusMessage message={meta.error} onRetry={meta.retry} />
      ) : (
        <p className="loading">Loading forecast data…</p>
      )}
    </Page>
  );
}

function Dashboard({ meta }: { meta: Meta }) {
  const [selection, setSelection] = useState<Selection>(() =>
    selectionFromQuery(window.location.search, meta),
  );
  const query = selectionToQuery(selection);
  const [selectedHour, setSelectedHour] = useState<string>();
  const update = (change: Partial<Selection>) => setSelection((current) => ({ ...current, ...change }));

  useEffect(() => {
    window.history.replaceState(null, "", `?${query}`);
  }, [query]);

  const day = useApi(`day?${query}`, (signal) => api.day(selection, signal));
  const accuracy = useApi(`accuracy?${selection.cutoff}&${selection.confidence}`, (signal) =>
    api.accuracy({ cutoff: selection.cutoff, confidence: selection.confidence }, signal),
  );

  const toolbar = (
    <div className="toolbar" role="group" aria-label="What to show">
      <DayPicker window={meta.window} value={selection.date} onChange={(date) => update({ date })} />
      <SafetyLevel value={selection.confidence} onChange={(confidence) => update({ confidence })} />
    </div>
  );

  return (
    <Page toolbar={toolbar} meta={meta}>
      {day.error ? (
        <StatusMessage message={day.error} onRetry={day.retry} />
      ) : day.data ? (
        <div className={day.loading ? "board is-refreshing" : "board"} aria-busy={day.loading}>
          <DecisionClock
            runs={meta.publish_run_times}
            cutoff={selection.cutoff}
            defaultCutoff={meta.default_cutoff}
            cutoffUtc={day.data.cutoff_utc}
            onChange={(cutoff) => update({ cutoff })}
          />
          <div className="board__main">
            <DecisionStrip day={day.data} backtest={accuracy.data?.backtest} />
            <HourlyChart key={query} hours={day.data.hours} onSelect={setSelectedHour} />
          </div>
          {accuracy.data ? <AccuracySection accuracy={accuracy.data} /> : null}
          {selectedHour ? <RevisionsPanel startTime={selectedHour} cutoff={selection.cutoff} /> : null}
          <MethodPanel />
        </div>
      ) : (
        <p className="loading">Loading the forecast for this day…</p>
      )}
    </Page>
  );
}

interface PageProps {
  children: ReactNode;
  toolbar?: ReactNode;
  meta?: Meta;
}

function Page({ children, toolbar, meta }: PageProps) {
  return (
    <div className="page">
      <header className="topbar">
        <div className="topbar__brand">
          <h1 className="topbar__title">Day-ahead wind</h1>
          <p className="topbar__subtitle">GB wind forecast at the moment you buy, and how far to trust it</p>
        </div>
        {toolbar}
      </header>
      <main className="content">{children}</main>
      <footer className="footer">
        <p>
          Source: Elexon BMRS wind outturn (FUELHH) and day-ahead wind forecast (WINDFOR).
          {meta ? ` Snapshot taken ${formatLondonShortDay(meta.snapshot_generated_at)}.` : ""} All
          times are London time.
        </p>
      </footer>
    </div>
  );
}

import type { IsoDate, Window } from "../api/types";

interface Props {
  window: Window;
  value: IsoDate;
  onChange: (value: IsoDate) => void;
}

function shift(day: IsoDate, days: number): IsoDate {
  const date = new Date(`${day}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

/** The delivery day, with previous and next buttons for stepping through the month. */
export function DayPicker({ window, value, onChange }: Props) {
  const previous = shift(value, -1);
  const next = shift(value, 1);
  return (
    <div className="day-picker">
      <button
        type="button"
        className="icon-button"
        aria-label="Previous day"
        disabled={previous < window.first_day}
        onClick={() => onChange(previous)}
      >
        <svg viewBox="0 0 16 16" aria-hidden="true">
          <path d="M10 3 5 8l5 5" />
        </svg>
      </button>
      <label className="day-picker__field">
        <span className="visually-hidden">Delivery day</span>
        <input
          type="date"
          min={window.first_day}
          max={window.last_day}
          value={value}
          onChange={(event) => {
            const picked = event.target.value;
            if (picked >= window.first_day && picked <= window.last_day) onChange(picked);
          }}
        />
      </label>
      <button
        type="button"
        className="icon-button"
        aria-label="Next day"
        disabled={next > window.last_day}
        onClick={() => onChange(next)}
      >
        <svg viewBox="0 0 16 16" aria-hidden="true">
          <path d="m6 3 5 5-5 5" />
        </svg>
      </button>
    </div>
  );
}

import type { Confidence } from "../api/types";

interface Props {
  value: Confidence;
  onChange: (value: Confidence) => void;
}

const LEVELS: { value: Confidence; label: string }[] = [
  { value: 90, label: "9 in 10 hours" },
  { value: 95, label: "19 in 20 hours" },
];

/** How many past hours the safety margin must have covered. */
export function SafetyLevel({ value, onChange }: Props) {
  return (
    <fieldset className="segmented">
      <legend className="segmented__legend">Margin covers</legend>
      {LEVELS.map((level) => (
        <label key={level.value} className="segmented__option">
          <input
            type="radio"
            name="confidence"
            value={level.value}
            checked={value === level.value}
            onChange={() => onChange(level.value)}
          />
          <span>{level.label}</span>
        </label>
      ))}
    </fieldset>
  );
}

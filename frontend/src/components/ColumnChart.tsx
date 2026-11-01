import { niceAxis } from "../lib/scale";
import { useWidth } from "../lib/useWidth";

export interface Column {
  label: string;
  value: number;
}

interface Props {
  columns: Column[];
  /** Accessible name; the values are also given as a hidden table. */
  title: string;
  valueLabel: string;
  format: (value: number) => string;
  /** "size" draws every column in one tone; "signed" colours over-forecast (positive) as risk. */
  tone: "size" | "signed";
  labelEvery: number;
  highlight?: number;
}

const HEIGHT = 200;
const PAD = { top: 10, right: 4, bottom: 24, left: 48 };

/** A small column chart drawn to the page's rules: one tone, a zero line, no decoration. */
export function ColumnChart({ columns, title, valueLabel, format, tone, labelEvery, highlight }: Props) {
  const [ref, width] = useWidth<HTMLElement>(560);
  const every = width < 360 ? labelEvery * 2 : labelEvery;
  const values = columns.map((column) => column.value);
  const top = niceAxis(Math.max(0, ...values));
  const bottom = Math.min(0, ...values) < 0 ? niceAxis(-Math.min(...values)).max : 0;
  const span = top.max + bottom || 1;
  const plotWidth = width - PAD.left - PAD.right;
  const plotHeight = HEIGHT - PAD.top - PAD.bottom;
  const y = (value: number) => PAD.top + plotHeight * ((top.max - value) / span);
  const step = plotWidth / Math.max(1, columns.length);
  const barWidth = Math.max(2, step * 0.66);

  return (
    <figure className="column-chart" ref={ref}>
      <svg width={width} height={HEIGHT} role="img" aria-label={title}>
        {[top.max, 0, ...(bottom ? [-bottom] : [])].map((tick) => (
          <g key={tick}>
            <line
              className={tick === 0 ? "column-chart__zero" : "column-chart__grid"}
              x1={PAD.left}
              x2={width - PAD.right}
              y1={y(tick)}
              y2={y(tick)}
            />
            <text className="column-chart__axis" x={PAD.left - 6} y={y(tick)} dy="0.32em" textAnchor="end">
              {format(tick)}
            </text>
          </g>
        ))}
        {columns.map((column, index) => {
          const kind =
            tone === "signed" ? (column.value >= 0 ? "is-high" : "is-low") : "is-size";
          return (
            <g key={column.label}>
              <rect
                className={`column-chart__bar ${kind}${index === highlight ? " is-highlight" : ""}`}
                x={PAD.left + index * step + (step - barWidth) / 2}
                width={barWidth}
                y={Math.min(y(column.value), y(0))}
                height={Math.abs(y(column.value) - y(0))}
              />
              {index % every === 0 ? (
                <text
                  className="column-chart__axis"
                  x={PAD.left + index * step + step / 2}
                  y={HEIGHT - 6}
                  textAnchor="middle"
                >
                  {column.label}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>
      <div className="visually-hidden">
        <table>
        <caption>{title}</caption>
        <thead>
          <tr>
            <th scope="col">Period</th>
            <th scope="col">{valueLabel}</th>
          </tr>
        </thead>
        <tbody>
          {columns.map((column) => (
            <tr key={column.label}>
              <th scope="row">{column.label}</th>
              <td>{format(column.value)}</td>
            </tr>
          ))}
        </tbody>
        </table>
      </div>
    </figure>
  );
}

import { formatWeekDate } from "../../copy";
import { usd } from "../../api";

export interface ForecastWeek {
  readonly week_start?: string;
  readonly week_end?: string;
  readonly beginning_cash?: number;
  readonly ending_cash?: number;
  readonly ar_collections?: number;
  readonly ap_payments?: number;
  readonly payroll?: number;
  readonly other_inflows?: number;
  readonly other_outflows?: number;
  readonly line_ids?: readonly string[];
}

export interface ForecastLineProps {
  readonly weeks: readonly ForecastWeek[];
  readonly selectedWeekStart?: string;
  readonly onSelectWeek?: (week: ForecastWeek) => void;
  readonly missId?: string;
  readonly opening?: number;
  readonly ending?: number;
}

interface Point {
  readonly week: ForecastWeek;
  readonly x: number;
  readonly y: number;
  readonly cash: number;
  readonly miss: boolean;
}

const VIEW_W = 960;
const VIEW_H = 380;
const PAD_L = 78;
const PAD_R = 36;
const PAD_T = 36;
const PAD_B = 52;

function cx(...parts: Array<string | false | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

export function asNumber(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return undefined;
}

export function isForecastWeek(value: unknown): value is ForecastWeek {
  if (value == null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const rec = value as Record<string, unknown>;
  return (
    rec.week_start != null || rec.week_end != null || rec.ending_cash != null || rec.beginning_cash != null
  );
}

export function weeksFromUnknown(value: unknown): ForecastWeek[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter(isForecastWeek);
}

function weekMentions(week: ForecastWeek, missId: string): boolean {
  const ids = week.line_ids ?? [];
  if (ids.some((id) => id.includes(missId))) {
    return true;
  }
  return JSON.stringify(week).includes(missId);
}

function compactUsd(value: number): string {
  if (Math.abs(value) >= 1000) {
    const thousands = value / 1000;
    const digits = Math.abs(thousands) >= 100 ? 0 : 1;
    return `$${thousands.toFixed(digits)}k`;
  }
  return usd(value);
}

function endingCash(week: ForecastWeek): number {
  return asNumber(week.ending_cash) ?? 0;
}

export function ForecastLine(props: ForecastLineProps): JSX.Element {
  const { weeks, selectedWeekStart, onSelectWeek, missId, opening, ending } = props;
  const innerW = VIEW_W - PAD_L - PAD_R;
  const innerH = VIEW_H - PAD_T - PAD_B;
  const cashes = weeks.map(endingCash);
  const minVal = cashes.length ? Math.min(...cashes) : 0;
  const maxVal = cashes.length ? Math.max(...cashes) : 1;
  const span = maxVal - minVal || Math.max(Math.abs(maxVal), 1);
  const lo = minVal === maxVal ? minVal - span * 0.08 : minVal;
  const hi = minVal === maxVal ? maxVal + span * 0.08 : maxVal;
  const range = hi - lo || 1;

  function xAt(index: number): number {
    if (weeks.length <= 1) {
      return PAD_L + innerW / 2;
    }
    return PAD_L + (index / (weeks.length - 1)) * innerW;
  }

  function yAt(value: number): number {
    return PAD_T + (1 - (value - lo) / range) * innerH;
  }

  const points: Point[] = weeks.map((week, index) => {
    const cash = endingCash(week);
    return {
      week,
      x: xAt(index),
      y: yAt(cash),
      cash,
      miss: Boolean(missId && weekMentions(week, missId)),
    };
  });

  const poly = points.map((point) => `${point.x},${point.y}`).join(" ");
  const area =
    points.length > 0
      ? `${points.map((point) => `${point.x},${point.y}`).join(" ")} ${points[points.length - 1].x},${PAD_T + innerH} ${points[0].x},${PAD_T + innerH}`
      : "";
  const first = points[0];
  const last = points[points.length - 1];
  const openLabel = opening ?? (first ? asNumber(first.week.beginning_cash) ?? first.cash : undefined);
  const endLabel = ending ?? last?.cash;
  const ticks = [hi, (hi + lo) / 2, lo];

  return (
    <div className="month-line">
      <svg
        className="month-line-svg"
        data-testid="forecast-line"
        viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
        role="img"
        aria-label="Thirteen-week ending cash"
      >
        <text className="month-line-axis-title" x={16} y={VIEW_H / 2} transform={`rotate(-90 16 ${VIEW_H / 2})`}>
          Ending cash (USD)
        </text>
        <text className="month-line-axis-title" x={VIEW_W / 2} y={VIEW_H - 8}>
          Week
        </text>
        <line className="month-line-axis" x1={PAD_L} y1={PAD_T} x2={PAD_L} y2={PAD_T + innerH} />
        <line className="month-line-axis" x1={PAD_L} y1={PAD_T + innerH} x2={PAD_L + innerW} y2={PAD_T + innerH} />
        {ticks.map((tick) => (
          <g key={`tick-${tick}`}>
            <line
              className="month-line-grid"
              x1={PAD_L}
              y1={yAt(tick)}
              x2={PAD_L + innerW}
              y2={yAt(tick)}
            />
            <text className="month-line-tick" x={PAD_L - 8} y={yAt(tick) + 4} textAnchor="end">
              {compactUsd(tick)}
            </text>
          </g>
        ))}
        {points.length > 0 ? <polygon className="month-line-area" points={area} /> : null}
        {points.length > 1 ? <polyline className="month-line-poly" points={poly} /> : null}
        {points.length === 0 ? (
          <text className="month-line-empty" x={VIEW_W / 2} y={VIEW_H / 2} textAnchor="middle">
            Run forecast
          </text>
        ) : null}
        {points.map((point, index) => {
          const selected = selectedWeekStart === point.week.week_start;
          const label = formatWeekDate(point.week.week_end || point.week.week_start);
          return (
            <g
              key={point.week.week_start || `pt-${index}`}
              className={cx("month-line-hit", selected && "active", point.miss && "miss")}
              role="button"
              tabIndex={0}
              aria-label={label}
              aria-pressed={selected}
              data-week-start={point.week.week_start}
              onClick={() => onSelectWeek?.(point.week)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectWeek?.(point.week);
                }
              }}
            >
              <circle
                className={cx("month-line-point", selected && "active", point.miss && "miss")}
                cx={point.x}
                cy={point.y}
                r={selected ? 6 : 4.5}
              />
              <text
                className="month-line-x"
                x={point.x}
                y={PAD_T + innerH + 16}
                textAnchor="end"
                transform={`rotate(-36 ${point.x} ${PAD_T + innerH + 16})`}
              >
                {label}
              </text>
              {point.miss && missId ? (
                <text className="month-line-miss-label" x={point.x} y={point.y - 12} textAnchor="middle">
                  {missId}
                </text>
              ) : null}
            </g>
          );
        })}
        {first && openLabel != null ? (
          <text className="month-line-anno" x={first.x} y={first.y - 14} textAnchor={points.length === 1 ? "middle" : "start"}>
            open {usd(openLabel)}
          </text>
        ) : null}
        {last && endLabel != null && points.length > 1 ? (
          <text className="month-line-anno" x={last.x} y={last.y - 14} textAnchor="end">
            end {usd(endLabel)}
          </text>
        ) : null}
      </svg>
    </div>
  );
}

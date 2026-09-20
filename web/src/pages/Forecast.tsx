import { useEffect, useState } from "react";
import { get, usd } from "../api";
import { useWorkflow } from "../hooks";
import { ErrorBox, RunBar } from "../layout/Shell";
import { BeforeAfterDiff, ProcessPanel, SourceArtifactViewer } from "../components/Demo";
import { FlowPlay, type FlowEdge, type FlowNode, type FlowStep, type LiveStage } from "../components/FlowPlay";
import { ForecastLine, asNumber, weeksFromUnknown, type ForecastWeek } from "../components/boards/ForecastLine";
import { formatWeekDate } from "../copy";
import { TraceIds } from "../components/Explain";

const FORECAST_STAKE = "The same books, projected forward.";

const FORECAST_NODES: readonly FlowNode[] = [
  { id: "pay", label: "pay", kind: "operator", room: "pay", column: 0, row: 0 },
  { id: "apply", label: "apply", kind: "operator", room: "cash", column: 0, row: 1 },
  { id: "story", label: "story", kind: "operator", room: "books-close", column: 1, row: 0 },
];

const FORECAST_EDGES: readonly FlowEdge[] = [
  { id: "pay-story", from: "pay", to: "story", label: "cash out" },
  { id: "apply-story", from: "apply", to: "story", label: "cash in" },
];

const FORECAST_STEPS: readonly FlowStep[] = [
  { id: "s-pay", title: "pay sends vendor cash out", nodeId: "pay", manipulations: ["vendor payments"] },
  { id: "s-apply", title: "apply brings customer cash in", nodeId: "apply", manipulations: ["collections"] },
  { id: "s-story", title: "story projects ending cash", nodeId: "story", manipulations: ["13-week line"] },
];

interface GrossMargin {
  readonly august?: number;
  readonly september?: number;
  readonly drivers?: readonly unknown[];
}

interface ForecastData {
  readonly weeks?: readonly ForecastWeek[];
  readonly opening_cash?: number;
  readonly projected_ending_cash?: number;
  readonly miss?: {
    readonly late_collection?: string;
    readonly unexpected_or_early?: readonly string[];
    readonly gross_margin?: GrossMargin;
  };
  readonly inputs?: {
    readonly original_forecast?: unknown;
    readonly new_events?: readonly unknown[];
    readonly gross_margin?: GrossMargin;
    readonly weeks?: unknown;
  };
}

interface WorkflowInner {
  readonly stages?: readonly Record<string, unknown>[];
  readonly handoffs?: unknown[];
  readonly summary?: string;
  readonly snapshot?: { readonly weeks?: unknown };
  readonly io?: {
    readonly outputs?: Record<string, unknown>;
    readonly before?: Record<string, unknown>;
    readonly after?: Record<string, unknown>;
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === "object" && !Array.isArray(value);
}

function workflowInner(result: unknown): WorkflowInner | undefined {
  if (!isRecord(result)) {
    return undefined;
  }
  if (isRecord(result.result)) {
    return result.result as WorkflowInner;
  }
  if (result.snapshot || result.stages || result.io) {
    return result as WorkflowInner;
  }
  return undefined;
}

function readStages(result: unknown): LiveStage[] {
  if (!isRecord(result)) {
    return [];
  }
  const nested = isRecord(result.result) ? result.result.stages : undefined;
  const raw = Array.isArray(nested) ? nested : Array.isArray(result.stages) ? result.stages : [];
  return raw.filter(isRecord).map((row) => ({
    id: typeof row.id === "string" ? row.id : undefined,
    bot: typeof row.bot === "string" ? row.bot : undefined,
    slug: typeof row.slug === "string" ? row.slug : undefined,
    label: typeof row.label === "string" ? row.label : undefined,
    status: typeof row.status === "string" ? row.status : undefined,
    detail: row.detail != null ? String(row.detail) : undefined,
  }));
}

function mentionsMiss(payload: unknown, token: string): boolean {
  if (payload == null) {
    return false;
  }
  try {
    return JSON.stringify(payload).includes(token);
  } catch {
    return false;
  }
}

function missIdFrom(data: ForecastData | null, result: unknown): string | undefined {
  const late = data?.miss?.late_collection;
  if (typeof late === "string" && late.length > 0) {
    return late;
  }
  if (mentionsMiss(data, "INV-AR-014") || mentionsMiss(result, "INV-AR-014")) {
    return "INV-AR-014";
  }
  return undefined;
}

function cashByWeek(weeks: readonly ForecastWeek[]): Record<string, unknown> {
  return Object.fromEntries(weeks.map((week) => [String(week.week_start || week.week_end || ""), week.ending_cash]));
}

function gmPercent(value: number | undefined): string | undefined {
  if (value == null || Number.isNaN(value)) {
    return undefined;
  }
  return `${Math.round(value * 1000) / 10}%`;
}

export default function Forecast(): JSX.Element {
  const [data, setData] = useState<ForecastData | null>(null);
  const [week, setWeek] = useState<ForecastWeek | null>(null);
  const [showNumbers, setShowNumbers] = useState(false);
  const { running, result, error, run } = useWorkflow();

  useEffect(() => {
    get<ForecastData>("/api/forecast")
      .then(setData)
      .catch(() => undefined);
  }, [result]);

  const inner = workflowInner(result);
  const resultWeeks = weeksFromUnknown(inner?.snapshot?.weeks);
  const weeks = resultWeeks.length > 0 ? resultWeeks : weeksFromUnknown(data?.weeks);
  const beforeWeeks = weeksFromUnknown(inner?.io?.before?.weeks || data?.inputs?.weeks || data?.weeks);
  const missId = missIdFrom(data, result);
  const opening =
    asNumber(weeks[0]?.beginning_cash) ?? asNumber(data?.opening_cash);
  const ending =
    asNumber(inner?.io?.outputs?.ending_cash) ??
    asNumber(data?.projected_ending_cash) ??
    asNumber(weeks[weeks.length - 1]?.ending_cash);
  const gm = data?.inputs?.gross_margin || data?.miss?.gross_margin;
  const ran = result != null;
  const augustGm = gmPercent(gm?.august);
  const septemberGm = gmPercent(gm?.september);

  return (
    <div className="month-desk">
      <h1>13-week cash</h1>
      <p className="month-stake">{FORECAST_STAKE}</p>
      <p className="month-caption">
        Source <span className="mono">/api/forecast</span>
      </p>
      {!data && !ran ? <p className="month-loading">Loading cash forecast…</p> : null}
      <ForecastLine
        weeks={weeks}
        selectedWeekStart={week?.week_start}
        onSelectWeek={setWeek}
        missId={missId}
        opening={opening}
        ending={ending}
      />
      <div className="month-line-toolbar">
        <RunBar
          label="Run forecast"
          running={running}
          onRun={() => {
            void run("/api/workflows/forecast");
          }}
        />
        <button
          type="button"
          className="btn"
          aria-pressed={showNumbers}
          onClick={() => setShowNumbers((open) => !open)}
        >
          Numbers
        </button>
      </div>
      <ErrorBox error={error} />
      {showNumbers ? (
        <div className="month-numbers">
          <div className="table-scroll">
            <table className="data">
              <thead>
                <tr>
                  <th>Week ending</th>
                  <th className="right">Start</th>
                  <th className="right">From customers</th>
                  <th className="right">To vendors</th>
                  <th className="right">End</th>
                </tr>
              </thead>
              <tbody>
                {weeks.map((item) => (
                  <tr
                    key={item.week_start}
                    className={week?.week_start === item.week_start ? "selected" : ""}
                    onClick={() => setWeek(item)}
                  >
                    <td>{formatWeekDate(item.week_end || item.week_start)}</td>
                    <td className="num right">{usd(item.beginning_cash)}</td>
                    <td className="num right">{usd(item.ar_collections)}</td>
                    <td className="num right">{usd(item.ap_payments)}</td>
                    <td className="num right">{usd(item.ending_cash)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {week ? <TraceIds ids={[week.week_start]} label="Selected week" /> : null}
        </div>
      ) : null}
      <FlowPlay
        nodes={FORECAST_NODES}
        edges={FORECAST_EDGES}
        steps={FORECAST_STEPS}
        mode="live"
        liveStages={readStages(result)}
      />
      {ran ? (
        <ProcessPanel
          stages={inner?.stages ? [...inner.stages] : undefined}
          handoffs={inner?.handoffs ? [...inner.handoffs] : undefined}
          summary={inner?.summary}
        />
      ) : null}
      <details className="month-evidence">
        <summary>Evidence</summary>
        <BeforeAfterDiff
          before={cashByWeek(beforeWeeks)}
          after={cashByWeek(weeks)}
          onlyChanged
          unchangedMessage="The refreshed forecast did not change any weekly ending-cash values."
          labelFor={formatWeekDate}
        />
        <SourceArtifactViewer artifact={data?.inputs?.original_forecast} />
        {(data?.inputs?.new_events || []).map((item, index) => (
          <SourceArtifactViewer key={`event-${index}`} artifact={item} />
        ))}
        {augustGm || septemberGm ? (
          <p className="muted">
            Gross margin {augustGm ?? "—"} → {septemberGm ?? "—"}.
          </p>
        ) : null}
        {(gm?.drivers || []).map((item, index) => (
          <SourceArtifactViewer key={`gm-${index}`} artifact={item} compact />
        ))}
      </details>
    </div>
  );
}

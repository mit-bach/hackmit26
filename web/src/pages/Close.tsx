import { useEffect, useState } from "react";
import { get, usd } from "../api";
import { useWorkflow } from "../hooks";
import { ErrorBox, RunBar } from "../layout/Shell";
import { BeforeAfterDiff, ProcessPanel, SourceArtifactViewer } from "../components/Demo";
import { FlowPlay, type FlowEdge, type FlowNode, type FlowStep, type LiveStage } from "../components/FlowPlay";
import { CloseGate, leftoverTasks, PLANTED_GAP, type CloseTask } from "../components/boards/CloseGate";
import { formatAccountingSentence, formatStatus, formatTask } from "../copy";
import { TraceIds } from "../components/Explain";

const CLOSE_STAKE = "Unexplained cash keeps the period lock from seating.";

const CLOSE_NODES: readonly FlowNode[] = [
  { id: "close", label: "close", kind: "operator", room: "books-close", column: 0, row: 0 },
  { id: "ctl-books", label: "ctl-books", kind: "verifier", room: "books-close", column: 1, row: 0, status: "blocked" },
  { id: "story", label: "story", kind: "operator", room: "books-close", column: 2, row: 0 },
  { id: "audit", label: "audit", kind: "assurance", room: "books-close", column: 3, row: 0 },
];

const CLOSE_EDGES: readonly FlowEdge[] = [
  { id: "close-lock", from: "close", to: "ctl-books", label: "lock" },
  { id: "close-story", from: "close", to: "story", label: "books" },
  { id: "lock-audit", from: "ctl-books", to: "audit", label: "sample" },
];

const CLOSE_STEPS: readonly FlowStep[] = [
  { id: "s-close", title: "close coordinates the month", nodeId: "close", manipulations: ["accrue", "prepaid", "assets"] },
  { id: "s-lock", title: "ctl-books refuses the lock", nodeId: "ctl-books", manipulations: ["TXN-2026-09-015", PLANTED_GAP], status: "blocked" },
  { id: "s-story", title: "story reads the same books", nodeId: "story", manipulations: ["forecast"] },
  { id: "s-audit", title: "audit samples independently", nodeId: "audit", manipulations: ["re-perform"] },
];

interface CloseJournal {
  readonly entry_id?: string;
  readonly memo?: string;
  readonly vendor?: string;
  readonly debit_account?: string;
  readonly credit_account?: string;
  readonly amount_minor?: number;
}

interface HarborInput {
  readonly history_table?: { readonly rows?: unknown; readonly record?: unknown };
  readonly contract?: unknown;
  readonly current_evidence?: readonly unknown[];
  readonly prior_memory?: readonly unknown[];
  readonly seeded_journal?: { readonly record?: { readonly amount_minor?: number } };
  readonly invoice_exists_for_september?: boolean;
}

interface CloseData {
  readonly status?: string;
  readonly tasks?: readonly CloseTask[];
  readonly journals?: readonly CloseJournal[];
  readonly before_close?: readonly CloseTask[];
  readonly harbor?: {
    readonly accrual_id?: string;
    readonly journal_id?: string;
    readonly input?: HarborInput;
  };
}

interface WorkflowInner {
  readonly stages?: readonly Record<string, unknown>[];
  readonly handoffs?: unknown[];
  readonly summary?: string;
  readonly io?: {
    readonly outputs?: Record<string, unknown>;
    readonly before?: Record<string, unknown>;
    readonly after?: Record<string, unknown>;
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === "object" && !Array.isArray(value);
}

function asNumber(value: unknown): number | undefined {
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

function workflowInner(result: unknown): WorkflowInner | undefined {
  if (!isRecord(result)) {
    return undefined;
  }
  if (isRecord(result.result)) {
    return result.result as WorkflowInner;
  }
  if (result.stages || result.io) {
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
    status:
      row.bot === "ctl-books" || row.id === "lock" || row.id === "ctl-books"
        ? "blocked"
        : typeof row.status === "string"
          ? row.status
          : undefined,
    detail: row.detail != null ? String(row.detail) : undefined,
  }));
}

function asTaskList(value: unknown): CloseTask[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter(isRecord).map((row) => ({
    task_id: typeof row.task_id === "string" ? row.task_id : undefined,
    status: typeof row.status === "string" ? row.status : undefined,
    category: typeof row.category === "string" ? row.category : undefined,
    blocker_reason: typeof row.blocker_reason === "string" ? row.blocker_reason : undefined,
    blocking_items: Array.isArray(row.blocking_items) ? row.blocking_items.map(String) : undefined,
    evidence_refs: Array.isArray(row.evidence_refs) ? row.evidence_refs.map(String) : undefined,
  }));
}

function taskStatusMap(tasks: readonly CloseTask[]): Record<string, unknown> {
  return Object.fromEntries(tasks.map((task) => [task.task_id || "", task.status]));
}

function harborAmounts(input: HarborInput | undefined): number[] {
  const table = input?.history_table;
  const rows = Array.isArray(table?.rows) ? table.rows : Array.isArray(table?.record) ? table.record : [];
  return rows
    .map((row) => {
      if (!isRecord(row)) {
        return undefined;
      }
      return asNumber(row.expense) ?? asNumber(row.amount);
    })
    .filter((value): value is number => value != null);
}

function harborAmount(data: CloseData | null, result: unknown): number | undefined {
  const inner = workflowInner(result);
  const outputs = inner?.io?.outputs;
  if (isRecord(result) && result.workflow === "accrual" && outputs) {
    const posted = asNumber(outputs.amount);
    if (posted != null) {
      return posted;
    }
    if (isRecord(outputs.journal_entry)) {
      const minor = asNumber(outputs.journal_entry.amount_minor);
      if (minor != null) {
        return minor / 100;
      }
    }
  }
  const seeded = data?.harbor?.input?.seeded_journal?.record?.amount_minor;
  if (typeof seeded === "number") {
    return seeded / 100;
  }
  return undefined;
}

function accrualMethod(result: unknown): string | undefined {
  if (!isRecord(result) || result.workflow !== "accrual") {
    return undefined;
  }
  const outputs = workflowInner(result)?.io?.outputs;
  if (!outputs) {
    return undefined;
  }
  const method = outputs.selected_method ?? outputs.method;
  return typeof method === "string" ? method : undefined;
}

function HarborSpark(props: { amounts: readonly number[] }): JSX.Element | null {
  const { amounts } = props;
  if (amounts.length < 2) {
    return amounts.length === 1 ? <span className="month-chip">{usd(amounts[0])}</span> : null;
  }
  const width = 132;
  const height = 28;
  const minVal = Math.min(...amounts);
  const maxVal = Math.max(...amounts);
  const span = maxVal - minVal || 1;
  const coords = amounts.map((value, index) => {
    const x = (index / (amounts.length - 1)) * (width - 4) + 2;
    const y = height - 3 - ((value - minVal) / span) * (height - 6);
    return `${x},${y}`;
  });
  return (
    <svg className="month-spark" width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <polyline className="month-spark-line" points={coords.join(" ")} />
    </svg>
  );
}

function HarborStrip(props: {
  input: HarborInput | undefined;
  amount: number | undefined;
  method: string | undefined;
}): JSX.Element {
  const { input, amount, method } = props;
  const amounts = harborAmounts(input);
  const chips = amounts.slice(-3);
  const memory = input?.prior_memory || [];
  const evidence = input?.current_evidence || [];
  return (
    <div className="month-harbor">
      <div className="month-harbor-main">
        <div>
          <div className="month-harbor-kicker">Harbor Electric</div>
          <div className="month-harbor-est">{amount != null ? usd(amount) : "Estimate after run"}</div>
          {method ? <p className="month-harbor-method">{formatAccountingSentence(method)}</p> : null}
        </div>
        <HarborSpark amounts={amounts} />
        <div className="month-harbor-chips">
          {chips.map((value, index) => (
            <span className="month-chip" key={`${value}-${index}`}>
              {usd(value)}
            </span>
          ))}
        </div>
      </div>
      <details className="month-harbor-docs">
        <summary>Contract and August memory</summary>
        {input?.contract ? <SourceArtifactViewer artifact={input.contract} compact /> : null}
        {evidence.map((item, index) => (
          <SourceArtifactViewer key={`ev-${index}`} artifact={item} compact />
        ))}
        {memory.map((item, index) => (
          <SourceArtifactViewer key={`mem-${index}`} artifact={item} />
        ))}
      </details>
    </div>
  );
}

export default function Close(): JSX.Element {
  const [data, setData] = useState<CloseData | null>(null);
  const { running, result, error, run } = useWorkflow();

  useEffect(() => {
    get<CloseData>("/api/close")
      .then(setData)
      .catch(() => undefined);
  }, [result]);

  const inner = workflowInner(result);
  const tasks = asTaskList(inner?.io?.after && Array.isArray(inner.io.after.tasks) ? inner.io.after.tasks : data?.tasks);
  const leftover = leftoverTasks(tasks);
  const amount = harborAmount(data, result);
  const method = accrualMethod(result);
  const stages = readStages(result);
  const beforeTasks = asTaskList(
    inner?.io?.before && Array.isArray(inner.io.before.tasks) ? inner.io.before.tasks : data?.before_close
  );
  const journals = data?.journals || [];
  const ran = result != null;

  return (
    <div className="month-desk">
      <h1>September is not closed</h1>
      <p className="month-stake">{CLOSE_STAKE}</p>
      <CloseGate tasks={tasks} status={data?.status || "BLOCKED"} />
      <HarborStrip input={data?.harbor?.input} amount={amount} method={method} />
      <RunBar
        label="Run month-end close"
        running={running}
        onRun={() => {
          void run("/api/workflows/close");
        }}
        extra={
          <button
            className="btn"
            type="button"
            disabled={running}
            onClick={() => {
              void run("/api/workflows/accrual", { vendor: "Harbor Electric" });
            }}
          >
            Estimate Harbor Electric
          </button>
        }
      />
      <ErrorBox error={error} />
      <FlowPlay
        nodes={CLOSE_NODES}
        edges={CLOSE_EDGES}
        steps={CLOSE_STEPS}
        mode="live"
        liveStages={stages}
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
        {leftover.length > 0 ? (
          <div className="month-leftover">
            <h2>Other close tasks</h2>
            <ul>
              {leftover.map((task) => (
                <li key={task.task_id}>
                  {formatTask(task.task_id)} · {formatStatus(task.status)}
                  {task.task_id === "TASK-CASH" ? ` · ${PLANTED_GAP}` : ""}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        <BeforeAfterDiff
          before={taskStatusMap(beforeTasks)}
          after={taskStatusMap(tasks)}
          onlyChanged
          unchangedMessage="Close-task statuses did not change in this run."
          labelFor={formatTask}
        />
        <TraceIds ids={[data?.harbor?.accrual_id, data?.harbor?.journal_id]} />
        <details>
          <summary>Journals</summary>
          <div className="table-scroll">
            <table className="data">
              <thead>
                <tr>
                  <th>What it recorded</th>
                  <th>Expense / asset</th>
                  <th>Offset</th>
                  <th className="right">Amount</th>
                </tr>
              </thead>
              <tbody>
                {journals.slice(0, 12).map((item) => (
                  <tr key={item.entry_id}>
                    <td>
                      <div>{item.memo || item.vendor || "Journal entry"}</div>
                      <TraceIds ids={[item.entry_id]} />
                    </td>
                    <td>{item.debit_account}</td>
                    <td>{item.credit_account}</td>
                    <td className="num right">{usd((item.amount_minor || 0) / 100)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
        {data?.harbor?.input?.seeded_journal ? (
          <SourceArtifactViewer artifact={data.harbor.input.seeded_journal} compact />
        ) : null}
      </details>
    </div>
  );
}

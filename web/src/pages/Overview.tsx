import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get, usd, statusTone } from "../api";
import { useWorkflow } from "../hooks";
import { ErrorBox, Pill } from "../layout/Shell";
import { BeforeAfterDiff, ProcessPanel } from "../components/Demo";
import { MetricCard, TraceIds } from "../components/Explain";
import { EventBoard } from "../components/EventBoard";
import { AGENTS } from "../data/agents";
import { formatFieldKey, formatStatus, explainMetric } from "../copy";

interface OverviewMetrics {
  cash?: number;
  ap_outstanding?: number;
  ar_outstanding?: number;
  projected_13w_ending_cash?: number;
  unreconciled_items?: number;
  close_status?: string;
  open_audit_findings?: number | string;
}

interface BriefingItem {
  title: string;
  href: string;
  detail: string;
  record_ids?: string[];
}

interface OperationItem {
  id: string;
  href: string;
  label: string;
  status: string;
}

interface OverviewResponse {
  metrics?: OverviewMetrics;
  briefing?: BriefingItem[];
  operations?: OperationItem[];
}

interface CompanySnapshot {
  cash?: number;
  ap_outstanding?: number;
  ar_outstanding?: number;
  unreconciled_item?: string;
  close_status?: string;
  exception_count?: number;
  projected_ending_cash?: number;
  journal_count?: number;
  decision_memory_count?: number;
}

interface WorkflowInner {
  io?: { before?: CompanySnapshot; after?: CompanySnapshot };
  stages?: Array<Record<string, unknown>>;
  handoffs?: unknown[];
  summary?: string;
}

function workflowInner(result: unknown): WorkflowInner | undefined {
  if (!result || typeof result !== "object") {
    return undefined;
  }
  const rec = result as { result?: unknown; io?: unknown; stages?: unknown };
  if (rec.result && typeof rec.result === "object") {
    return rec.result as WorkflowInner;
  }
  if (rec.stages || rec.io) {
    return rec as WorkflowInner;
  }
  return undefined;
}

export default function Overview(): JSX.Element {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [start, setStart] = useState<CompanySnapshot | null>(null);
  const { running, result, error: runError, run } = useWorkflow();

  useEffect(() => {
    get<OverviewResponse>("/api/demo/overview")
      .then(setData)
      .catch((err: unknown) => setError(String(err)));
    get<CompanySnapshot>("/api/demo/company-state")
      .then(setStart)
      .catch(() => setStart(null));
  }, [result]);

  const m = data?.metrics || {};
  const inner = workflowInner(result);
  const io = inner?.io;
  const before = io?.before || start;
  const after = io?.after;

  return (
    <div className="home">
      <section className="hero flow-hero">
        <div className="eyebrow">HackMIT · Agentic Systems for the Office of the CFO</div>
        <h1>An AI finance office that finishes the work.</h1>
        <p className="hero-sub">Maximor Demo Corp · September 2026</p>
        <EventBoard />
        <div className="btn-row">
          <Link className="btn primary" to="/workflow">
            Follow three invoices
          </Link>
          <Link className="btn" to="/architecture">
            Office graph
          </Link>
          <Link className="btn" to="/coverage">
            What it can do
          </Link>
        </div>
        <p className="muted home-sim-link">
          <Link to="/simulations">Run simulations</Link>
        </p>
      </section>

      <hr className="home-rule" />

      <section className="showcase-section" id="live-books">
        <div className="eyebrow">Live books</div>
        <h2 className="section-title">Maximor Demo Corp, September 2026</h2>
        <p className="lede">Starting company state, the work the agents perform, and the ending state stay visible.</p>
        {error ? <div className="error">{error}</div> : null}
        {!data && !error ? <div className="muted">Loading Maximor books…</div> : null}
        <div className="toolbar">
          <div className="btn-row">
            <button className="btn primary" disabled={running} onClick={() => run("/api/workflows/cfo-cycle")}>
              {running ? "Running…" : "Run the connected CFO cycle"}
            </button>
            <Link className="btn" to="/simulations/cfo-cycle">
              About this simulation
            </Link>
          </div>
        </div>
        <ErrorBox error={runError} />
        <div className="io-flow">
          <div className="io-col">
            <div className="io-label">Starting company state</div>
            <StateCard state={before} />
          </div>
          <div className="io-arrow">→</div>
          <div className="io-col">
            <div className="io-label">What the agents did</div>
            <ProcessPanel stages={inner?.stages} handoffs={inner?.handoffs} summary={inner?.summary} />
          </div>
          <div className="io-arrow">→</div>
          <div className="io-col">
            <div className="io-label">Ending company state</div>
            {after ? (
              <div className="stack">
                <StateCard state={after} />
                <div className="card">
                  <h2>What changed</h2>
                  <BeforeAfterDiff
                    before={pickState(before)}
                    after={pickState(after)}
                    fields={["cash", "ap_outstanding", "ar_outstanding", "close_status", "exception_count", "journal_count", "decision_memory_count", "projected_ending_cash"]}
                    onlyChanged
                    unchangedMessage="The CFO cycle ran, but these headline company totals did not move."
                    labelFor={formatFieldKey}
                  />
                </div>
              </div>
            ) : (
              <div className="card">
                <p className="muted">Run the cycle to persist ending cash, unpaid bills, close status, journals, memory, and the cash forecast from the live agents.</p>
              </div>
            )}
          </div>
        </div>
        {data ? (
          <>
            <div className="metrics">
              <MetricCard
                label="Cash in bank"
                value={usd(m.cash)}
                interpretation={explainMetric("cash", m.cash).interpretation}
              />
              <MetricCard
                label="Unpaid vendor bills"
                value={usd(m.ap_outstanding)}
                interpretation={explainMetric("ap_outstanding", m.ap_outstanding).interpretation}
              />
              <MetricCard
                label="Unpaid customer invoices"
                value={usd(m.ar_outstanding)}
                interpretation={explainMetric("ar_outstanding", m.ar_outstanding).interpretation}
              />
              <MetricCard
                label="13-week ending cash"
                value={usd(m.projected_13w_ending_cash)}
                interpretation={explainMetric("projected_13w_ending_cash", m.projected_13w_ending_cash).interpretation}
                driver="The largest expected cash outflows are payroll and vendor payments."
              />
              <MetricCard
                label="Unresolved bank difference"
                value={usd(m.unreconciled_items)}
                interpretation={explainMetric("unreconciled_items", m.unreconciled_items).interpretation}
                driver="The Northstar deposit is $12.40 above the invoice."
              />
              <MetricCard
                label="Month-end status"
                value={formatStatus(m.close_status)}
                interpretation={explainMetric("close_status", m.close_status).interpretation}
              />
              <MetricCard
                label="Audit findings"
                value={m.open_audit_findings ?? "Not run yet"}
                interpretation="Independent audit findings appear after the audit is run. The Audit Agent samples the books after operations have recorded them."
              />
              <MetricCard
                label="Finance team"
                value={`${AGENTS.length} agents`}
                interpretation="Standing office workers sharing one set of books, saved decisions, and evidence."
              />
            </div>
            <div className="grid-2">
              <div className="card">
                <h2>What needs attention</h2>
                {(data.briefing || []).map((item) => (
                  <Link key={item.title} to={item.href} className="tl-item" style={{ marginBottom: 10 }}>
                    <div />
                    <div className="tl-body">
                      <div className="tl-title">{item.title}</div>
                      <div className="tl-meta">{item.detail}</div>
                      <TraceIds ids={item.record_ids} />
                    </div>
                  </Link>
                ))}
              </div>
              <div className="card">
                <h2>Finance operations</h2>
                {(data.operations || []).map((item) => (
                  <Link key={item.id} to={item.href} className="split" style={{ marginBottom: 8 }}>
                    <strong>{item.label}</strong>
                    <Pill tone={statusTone(item.status)}>{formatStatus(item.status)}</Pill>
                  </Link>
                ))}
              </div>
            </div>
          </>
        ) : null}
      </section>
    </div>
  );
}

function pickState(state: CompanySnapshot | null | undefined): Record<string, unknown> {
  if (!state) {
    return {};
  }
  return {
    cash: state.cash,
    ap_outstanding: state.ap_outstanding,
    ar_outstanding: state.ar_outstanding,
    close_status: state.close_status,
    exception_count: state.exception_count,
    journal_count: state.journal_count,
    decision_memory_count: state.decision_memory_count,
    projected_ending_cash: state.projected_ending_cash,
  };
}

function StateCard({ state }: { state: CompanySnapshot | null | undefined }): JSX.Element {
  if (!state) {
    return (
      <div className="card">
        <p className="muted">Loading company state…</p>
      </div>
    );
  }
  return (
    <div className="card">
      <dl className="kv">
        <dt>Cash in bank</dt>
        <dd>{usd(state.cash)}</dd>
        <dt>Unpaid vendor bills</dt>
        <dd>{usd(state.ap_outstanding)}</dd>
        <dt>Unpaid customer invoices</dt>
        <dd>{usd(state.ar_outstanding)}</dd>
        <dt>Unresolved bank item</dt>
        <dd>{state.unreconciled_item === "TXN-2026-09-015" ? "Northstar $12.40 difference" : formatStatus(state.unreconciled_item)}</dd>
        <dt>Month-end</dt>
        <dd>{formatStatus(state.close_status)}</dd>
        <dt>Open exceptions</dt>
        <dd>
          {state.exception_count}
          <div className="muted">
            {Number(state.exception_count) === 0
              ? "No bills or bank items are currently waiting on extra investigation."
              : `${state.exception_count} item${Number(state.exception_count) === 1 ? "" : "s"} still need investigation before they can be treated as settled.`}
          </div>
        </dd>
        <dt>Forecast ending cash</dt>
        <dd>{usd(state.projected_ending_cash)}</dd>
      </dl>
      <TraceIds ids={[state.unreconciled_item]} label="Bank reference" />
    </div>
  );
}

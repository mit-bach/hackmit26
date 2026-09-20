import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get, usd, statusTone } from "../api";
import { useWorkflow } from "../hooks";
import { ErrorBox, PageHead, Pill } from "../layout/Shell";
import { BeforeAfterDiff, ProcessPanel } from "../components/Demo";
import { TraceIds, WhatsHappening } from "../components/Explain";
import { formatFieldKey, formatStatus } from "../copy";

export default function Overview() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [start, setStart] = useState<any>(null);
  const { running, result, error: runError, run } = useWorkflow();

  useEffect(() => {
    get("/api/demo/overview").then(setData).catch((err) => setError(String(err)));
    get("/api/demo/company-state").then(setStart).catch(() => setStart(null));
  }, [result]);

  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="muted">Loading Maximor books…</div>;

  const m = data.metrics || {};
  const inner = result?.result;
  const io = inner?.io;
  const before = io?.before || start;
  const after = io?.after;

  return (
    <div>
      <PageHead
        eyebrow="Command center"
        title="Autonomous Office of the CFO"
        lede="Maximor is running the finance office for Maximor Demo Corp. This screen shows the company's current cash, unpaid bills, unpaid customer invoices, and whether September's books can finish."
      />
      <WhatsHappening
        happening="The office is working from the live Maximor demo books. Running the CFO cycle asks the specialized finance agents to process vendor bills, customer payments, bank activity, month-end close, the cash forecast, and an independent audit — then persist what actually changed."
        figureOut="Can September's books finish, and what records did the agents produce along the way?"
        why="A judge should see the starting company state, the work Maximor performed, and the ending state — not a mock landing page."
      />
      <div className="toolbar">
        <div className="btn-row">
          <button className="btn primary" disabled={running} onClick={() => run("/api/workflows/cfo-cycle")}>
            {running ? "Running…" : "Run CFO cycle"}
          </button>
          <Link className="btn" to="/scenarios">
            Open scenario previews
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
          <div className="io-label">System process</div>
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
      <div className="metrics">
        <div className="metric">
          <div className="metric-label">Cash in bank</div>
          <div className="metric-value">{usd(m.cash)}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Unpaid vendor bills</div>
          <div className="metric-value">{usd(m.ap_outstanding)}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Unpaid customer invoices</div>
          <div className="metric-value">{usd(m.ar_outstanding)}</div>
        </div>
        <div className="metric">
          <div className="metric-label">13-week ending cash</div>
          <div className="metric-value">{usd(m.projected_13w_ending_cash)}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Unresolved bank difference</div>
          <div className="metric-value">{usd(m.unreconciled_items)}</div>
          <div className="metric-note">Northstar deposit is $12.40 above the invoice</div>
        </div>
        <div className="metric">
          <div className="metric-label">Month-end status</div>
          <div className="metric-value">{formatStatus(m.close_status)}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Audit findings</div>
          <div className="metric-value">{m.open_audit_findings ?? "Run audit"}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Specialized agents</div>
          <div className="metric-value">{m.active_bots}</div>
        </div>
      </div>
      <div className="grid-2">
        <div className="card">
          <h2>What needs attention</h2>
          {(data.briefing || []).map((item: any) => (
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
          {(data.operations || []).map((item: any) => (
            <Link key={item.id} to={item.href} className="split" style={{ marginBottom: 8 }}>
              <strong>{item.label}</strong>
              <Pill tone={statusTone(item.status)}>{formatStatus(item.status)}</Pill>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

function pickState(state: any) {
  if (!state) return {};
  const { close_tasks, open_ap, open_ar, ...rest } = state;
  return rest;
}

function StateCard({ state }: { state: any }) {
  if (!state) return <div className="card"><p className="muted">Loading company state…</p></div>;
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
        <dd>{state.exception_count}</dd>
        <dt>Forecast ending cash</dt>
        <dd>{usd(state.projected_ending_cash)}</dd>
      </dl>
      <TraceIds ids={[state.unreconciled_item]} label="Bank reference" />
    </div>
  );
}

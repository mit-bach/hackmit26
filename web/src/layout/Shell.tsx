import { NavLink, useLocation } from "react-router-dom";
import { ReactNode, useEffect, useState } from "react";
import { get, post, statusTone } from "../api";
import { formatAgent } from "../copy";

const PRIMARY = [
  ["/", "Overview"],
  ["/inbox", "Inbox"],
  ["/ap", "Accounts Payable"],
  ["/ar", "Accounts Receivable"],
  ["/cash", "Cash"],
  ["/stripe", "Stripe Reconciliation"],
  ["/close", "Close"],
  ["/forecast", "Forecast"],
  ["/audit", "Audit & Controls"],
  ["/memory", "Memory"],
  ["/agents", "Agent Activity"],
  ["/evaluations", "Evaluation Lab"],
];

const SECONDARY = [
  ["/scenarios", "Demo Scenarios"],
  ["/architecture", "System Architecture"],
];

export function Shell({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<any>(null);
  const [resetting, setResetting] = useState(false);
  const location = useLocation();

  useEffect(() => {
    get("/api/demo/status").then(setStatus).catch(() => setStatus(null));
  }, [location.pathname]);

  async function resetDemo() {
    setResetting(true);
    try {
      await post("/api/demo/reset");
      window.location.reload();
    } finally {
      setResetting(false);
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">
            Maxi<span>mor</span>
          </div>
          <div className="brand-sub">Office of the CFO</div>
        </div>
        <div className="top-meta">
          <span>
            Company <strong>{typeof status?.company === "string" ? status.company : status?.company?.legal_name || status?.company?.company?.legal_name || "Maximor Demo Corp"}</strong>
          </span>
          <span>
            Period <strong>{status?.period || "2026-09"}</strong>
          </span>
          <span className={`pill ${statusTone(status?.system_status)}`}>{status?.system_status || "loading"}</span>
          <span className={`pill ${status?.autonomy?.live_llm ? "warn" : "ok"}`}>
            {status?.autonomy?.execution || "kernel-deterministic"}
          </span>
          <span className={`pill ${status?.stripe?.mode === "live" ? "warn" : "info"}`}>
            Stripe {status?.stripe?.mode || "simulated"}
          </span>
        </div>
      </header>
      <aside className="sidebar">
        <div>
          <div className="nav-label">Operations</div>
          {PRIMARY.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
              {label}
            </NavLink>
          ))}
        </div>
        <div>
          <div className="nav-label">Demo</div>
          {SECONDARY.map(([to, label]) => (
            <NavLink key={to} to={to} className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
              {label}
            </NavLink>
          ))}
          <button className="nav-link" style={{ width: "100%", background: "transparent", border: 0, textAlign: "left" }} onClick={resetDemo} disabled={resetting}>
            {resetting ? "Resetting…" : "Reset Demo"}
          </button>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}

export function PageHead({ eyebrow, title, lede }: { eyebrow: string; title: string; lede?: string }) {
  return (
    <div className="page-head">
      <div className="eyebrow">{eyebrow}</div>
      <h1>{title}</h1>
      {lede ? <p className="lede">{lede}</p> : null}
    </div>
  );
}

export function Pill({ children, tone }: { children: ReactNode; tone?: string }) {
  return <span className={`pill ${tone || "neutral"}`}>{children}</span>;
}

export function RunBar({
  label,
  running,
  onRun,
  extra,
}: {
  label: string;
  running: boolean;
  onRun: () => void;
  extra?: ReactNode;
}) {
  return (
    <div className="toolbar">
      <div className="btn-row">
        <button className="btn primary" onClick={onRun} disabled={running}>
          {running ? "Running…" : label}
        </button>
        {extra}
      </div>
      {running ? <Pill tone="warn">queued → running</Pill> : null}
    </div>
  );
}

export function Stages({ stages }: { stages?: any[] }) {
  if (!stages?.length) return null;
  return (
    <div className="stages">
      {stages.map((stage) => (
        <div className="stage" key={stage.id || stage.label}>
          <div className={`stage-dot ${stage.status || "completed"}`} />
          <div className="stage-copy">
            <div>
              {stage.label} {stage.bot ? <Pill>{formatAgent(stage.bot)}</Pill> : null}
            </div>
            {stage.detail ? <div className="muted">{stage.detail}</div> : null}
          </div>
        </div>
      ))}
    </div>
  );
}

export function ErrorBox({ error }: { error: string | null }) {
  if (!error) return null;
  return <div className="error">{error}</div>;
}

export function JsonBlock({ value }: { value: unknown }) {
  if (value === null || value === undefined) return <div className="muted">None</div>;
  return (
    <pre className="mono" style={{ whiteSpace: "pre-wrap", color: "var(--muted)", fontSize: 12 }}>
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

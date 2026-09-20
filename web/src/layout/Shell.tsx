import { NavLink, useLocation } from "react-router-dom";
import { ReactNode, useEffect, useState } from "react";
import { get, post, statusTone } from "../api";
import { formatAgent, formatExecution, formatPeriod, formatStatus, formatSummary } from "../copy";

interface NavItem {
  readonly to: string;
  readonly label: string;
}

const PITCH: readonly NavItem[] = [
  { to: "/", label: "Home" },
  { to: "/architecture", label: "Office graph" },
  { to: "/workflow", label: "Three stories" },
  { to: "/coverage", label: "Capabilities" },
  { to: "/evaluations", label: "Evidence" },
];

const LIVE_OFFICE: readonly NavItem[] = [
  { to: "/inbox", label: "Inbox" },
  { to: "/ap", label: "Payables" },
  { to: "/ar", label: "Receivables" },
  { to: "/cash", label: "Cash" },
  { to: "/stripe", label: "Stripe" },
  { to: "/close", label: "Close" },
  { to: "/forecast", label: "Forecast" },
  { to: "/audit", label: "Audit" },
  { to: "/memory", label: "Memory" },
  { to: "/agents", label: "Team activity" },
];

const MORE: readonly NavItem[] = [
  { to: "/simulations", label: "Simulations" },
  { to: "/videos", label: "Videos" },
];

export function Shell({ children }: { children: ReactNode }): JSX.Element {
  const [status, setStatus] = useState<any>(null);
  const [resetting, setResetting] = useState(false);
  const location = useLocation();

  useEffect(() => {
    get("/api/demo/status").then(setStatus).catch(() => setStatus(null));
  }, [location.pathname]);

  async function resetBooks(): Promise<void> {
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
            Period <strong>{formatPeriod(status?.period || "2026-09")}</strong>
          </span>
          <span className={`pill ${statusTone(status?.system_status)}`}>{formatStatus(status?.system_status || "operational")}</span>
          <span className={`pill ${status?.autonomy?.live_llm ? "warn" : "ok"}`}>
            {formatExecution(status?.autonomy?.execution || "kernel-deterministic")}
          </span>
          <span className={`pill ${status?.stripe?.mode === "live" ? "warn" : "info"}`}>
            Stripe {formatStatus(status?.stripe?.mode || "simulated")}
          </span>
        </div>
      </header>
      <aside className="sidebar">
        <div>
          <div className="nav-label">Pitch</div>
          {PITCH.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
        </div>
        <div>
          <div className="nav-label">Live office</div>
          {LIVE_OFFICE.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
              {item.label}
            </NavLink>
          ))}
        </div>
        <div>
          <div className="nav-label">More</div>
          {MORE.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
              {item.label}
            </NavLink>
          ))}
          <button
            className="nav-link"
            style={{ width: "100%", background: "transparent", border: 0, textAlign: "left" }}
            onClick={resetBooks}
            disabled={resetting}
          >
            {resetting ? "Resetting…" : "Reset books"}
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
      {running ? <Pill tone="warn">Checking the work…</Pill> : null}
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
            {formatSummary(stage.label)} {stage.bot ? <Pill>{formatAgent(stage.bot)}</Pill> : null}
          </div>
          {stage.detail ? <div className="muted">{formatSummary(stage.detail)}</div> : null}
          </div>
        </div>
      ))}
    </div>
  );
}

export function ErrorBox({ error }: { error: string | null }) {
  if (!error) return null;
  const text =
    error === "Not Found" || /^not found$/i.test(error)
      ? "That request did not match a route on the running demo API. Restart the Maximor API and try again."
      : error === "Internal Server Error" || error === "Failed to fetch" || /failed to fetch/i.test(error)
        ? "The demo API did not respond. If it was restarting, run this again."
        : error;
  return <div className="error error-top">{text}</div>;
}

export function JsonBlock({ value }: { value: unknown }) {
  if (value === null || value === undefined) return <div className="muted">None</div>;
  return (
    <pre className="mono" style={{ whiteSpace: "pre-wrap", color: "var(--muted)", fontSize: 12 }}>
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

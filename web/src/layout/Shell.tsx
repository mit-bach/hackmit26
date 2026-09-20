import { NavLink, useLocation } from "react-router-dom";
import { Fragment, type ReactNode, useEffect, useState } from "react";
import { statusTone } from "../api";
import { demoApi } from "../demoClient";
import { useHealth } from "../hooks";
import { formatAgent, formatExecution, formatFieldKey, formatPeriod, formatStatus, formatSummary } from "../copy";

interface NavItem {
  readonly to: string;
  readonly label: string;
}

const SHOWCASE: readonly NavItem[] = [
  { to: "/", label: "Home" },
  { to: "/architecture", label: "How they work" },
  { to: "/workflow", label: "One invoice" },
  { to: "/memory", label: "Saved decisions" },
  { to: "/simulations", label: "Simulations" },
  { to: "/videos", label: "Videos" },
  { to: "/coverage", label: "What it covers" },
  { to: "/evaluations", label: "Evaluation" },
];

const LIVE_OFFICE: readonly NavItem[] = [
  { to: "/inbox", label: "Inbox" },
  { to: "/ap", label: "Bills to pay" },
  { to: "/ar", label: "Customer invoices" },
  { to: "/cash", label: "Bank vs books" },
  { to: "/stripe", label: "Stripe" },
  { to: "/close", label: "Finish the month" },
  { to: "/forecast", label: "Cash outlook" },
  { to: "/audit", label: "Control tests" },
  { to: "/agents", label: "The team" },
];

interface StatusPayload {
  readonly company?: string | { legal_name?: string; company?: { legal_name?: string } };
  readonly period?: string;
  readonly system_status?: string;
  readonly autonomy?: { live_llm?: boolean; execution?: string };
  readonly stripe?: { mode?: string };
}

function companyName(status: StatusPayload | null): string {
  const company = status?.company;
  if (typeof company === "string") {
    return company;
  }
  return company?.legal_name || company?.company?.legal_name || "Maximor Demo Corp";
}

export function Shell({ children }: { children: ReactNode }): JSX.Element {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [resetting, setResetting] = useState(false);
  const live = useHealth();
  const location = useLocation();

  useEffect(() => {
    demoApi.loadStatus().then((payload) => setStatus(payload as StatusPayload)).catch(() => setStatus(null));
  }, [location.pathname]);

  async function resetBooks(): Promise<void> {
    setResetting(true);
    try {
      await demoApi.resetBooks();
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
            Company <strong>{companyName(status)}</strong>
          </span>
          <span>
            Accounting month <strong>{formatPeriod(status?.period || "2026-09")}</strong>
          </span>
          <span className={`pill ${statusTone(status?.system_status)}`}>{formatStatus(status?.system_status || "operational")}</span>
          <span className={`pill ${status?.autonomy?.live_llm ? "warn" : "ok"}`}>
            {formatExecution(status?.autonomy?.execution || "kernel-deterministic")}
          </span>
          <span className={`pill ${status?.stripe?.mode === "live" ? "warn" : "info"}`}>
            Stripe {formatStatus(status?.stripe?.mode || "simulated")}
          </span>
          <span className={`pill ${live ? "ok" : "warn"}`}>{live ? "Live office" : "Saved demo"}</span>
        </div>
      </header>
      <aside className="sidebar">
        <div>
          <div className="nav-label">Showcase</div>
          {SHOWCASE.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === "/"} className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
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
          <button className="nav-link" style={{ width: "100%", background: "transparent", border: 0, textAlign: "left" }} onClick={() => void resetBooks()} disabled={resetting}>
            {resetting ? "Resetting…" : "Reset books"}
          </button>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}

export function PageHead({ eyebrow, title, lede }: { eyebrow: string; title: string; lede?: string }): JSX.Element {
  return (
    <div className="page-head">
      <div className="eyebrow">{eyebrow}</div>
      <h1>{title}</h1>
      {lede ? <p className="lede">{lede}</p> : null}
    </div>
  );
}

export function Pill({ children, tone }: { children: ReactNode; tone?: string }): JSX.Element {
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
}): JSX.Element {
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

export function Stages({ stages }: { stages?: Array<{ id?: string; label?: string; bot?: string; status?: string; detail?: string }> }): JSX.Element | null {
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

export function ErrorBox({ error }: { error: string | null }): JSX.Element | null {
  if (!error) return null;
  const unavailable =
    /not found/i.test(error) ||
    /unknown api route/i.test(error) ||
    /did not match a route/i.test(error) ||
    /method not allowed/i.test(error) ||
    /failed to fetch/i.test(error) ||
    /demo api unavailable/i.test(error) ||
    /internal server error/i.test(error) ||
    /timed out/i.test(error) ||
    /timeout/i.test(error) ||
    /aborted/i.test(error);
  return (
    <div className="notice notice-top">
      {unavailable ? "Live agent run unavailable. Showing the saved demonstration result if one is available." : error}
    </div>
  );
}

export function SourceBadge({ source }: { source?: "live" | "saved" | null }): JSX.Element | null {
  if (!source) return null;
  return <span className={`source-badge ${source}`}>{source === "live" ? "Live run" : "Saved demo result"}</span>;
}

export function JsonBlock({ value }: { value: unknown }): JSX.Element {
  if (value === null || value === undefined) return <div className="muted">None</div>;
  if (typeof value !== "object") return <div>{String(value)}</div>;
  const entries = Object.entries(value as Record<string, unknown>).slice(0, 12);
  if (!entries.length) return <div className="muted">None</div>;
  return (
    <dl className="kv">
      {entries.map(([key, item]) => (
        <Fragment key={key}>
          <dt>{formatFieldKey(key)}</dt>
          <dd>{typeof item === "object" ? "See explanation above" : formatStatus(item)}</dd>
        </Fragment>
      ))}
    </dl>
  );
}

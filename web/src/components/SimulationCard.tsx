import { Link } from "react-router-dom";
import { AGENTS_BY_SLUG } from "../data/agents";
import type { Simulation } from "../data/simulations";

export function SimulationCard({
  item,
  status,
}: {
  item: Simulation;
  status?: { label: string; tone?: string };
}) {
  return (
    <div className="card sim-card">
      <div className="split">
        <h2 style={{ margin: 0, textTransform: "none", letterSpacing: 0, color: "var(--text)", fontSize: 18 }}>{item.title}</h2>
        {status ? <span className={`pill ${status.tone || "neutral"}`}>{status.label}</span> : <span className="pill">Runnable</span>}
      </div>
      <p>
        <strong>Business scenario. </strong>
        {item.scenario}
      </p>
      <p>
        <strong>What makes it difficult. </strong>
        {item.difficulty}
      </p>
      <p className="muted">
        Agents: {item.agents.map((slug) => AGENTS_BY_SLUG[slug]?.name.replace(/ Agent$/, "")).join(" · ")}
      </p>
      <div className="btn-row" style={{ marginTop: 12 }}>
        <Link className="btn primary" to={`/simulations/${item.id}`}>
          Open simulation
        </Link>
        <Link className="btn" to={item.href}>
          Live runner
        </Link>
      </div>
    </div>
  );
}

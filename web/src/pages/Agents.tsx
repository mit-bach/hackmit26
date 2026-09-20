import { useEffect, useState } from "react";
import { get, statusTone } from "../api";
import { PageHead, Pill } from "../layout/Shell";
import { AgentDirectory, AgentPanel } from "../components/AgentPanel";
import { AGENTS, AGENTS_BY_SLUG } from "../data/agents";
import { formatHandoff, formatStatus, formatSummary, formatWorkflow } from "../copy";

export default function Agents() {
  const [data, setData] = useState<any>(null);
  const [open, setOpen] = useState<string>("ap");

  useEffect(() => {
    get("/api/agents").then(setData);
  }, []);

  const agent = AGENTS_BY_SLUG[open as keyof typeof AGENTS_BY_SLUG] || AGENTS[0];
  const live = (data?.bots || []).find((item: any) => item.slug === open);

  return (
    <div>
      <PageHead
        eyebrow="Office of the CFO"
        title="The finance team"
        lede="A coordinated set of finance agents sharing context, memory, evidence, and decisions. Each agent can take several related jobs. Control agents recheck uncertain work instead of asking a person to intervene."
      />
      <div className="grid-2">
        <div className="card">
          <h2>The team</h2>
          <AgentDirectory selected={open} onSelect={setOpen} />
        </div>
        <div className="stack">
          <div className="card">
            <AgentPanel agent={agent} live={live} />
          </div>
          <div className="card">
            <h2>What the agents just did</h2>
            {(data?.activity || []).length === 0 ? (
              <p className="muted">Run a simulation to append real agent activity. Events are not fabricated.</p>
            ) : (
              (data.activity || []).map((row: any, idx: number) => (
                <div key={idx} style={{ marginBottom: 12 }}>
                  <div className="split">
                    <strong>{formatWorkflow(row.workflow)}</strong>
                    <Pill tone={statusTone(row.status)}>{formatStatus(row.status)}</Pill>
                  </div>
                  <p>{formatHandoff(row.bots, row.workflow)}</p>
                  {row.summary ? <p className="muted">{formatSummary(row.summary)}</p> : null}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

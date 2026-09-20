import { useEffect, useState } from "react";
import { demoApi } from "../demoClient";
import { PageHead } from "../layout/Shell";
import { ArchitectureDiagram } from "../components/ArchitectureDiagram";
import { AgentDirectory, AgentPanel } from "../components/AgentPanel";
import { AGENTS, AGENTS_BY_SLUG, ROUTINES, type AgentSlug } from "../data/agents";
import { WORLD_INSPECTOR, WORLD_NODE_ID, isGrainId } from "../data/officeGraph";
import { formatAgent, formatCadence, humanizeToken } from "../copy";

interface LiveBot {
  readonly slug?: string;
  readonly skills?: readonly string[];
}

interface RoutineRow {
  readonly id?: string;
  readonly name?: string;
  readonly title?: string;
  readonly cadence?: string;
  readonly bot?: string;
}

interface ArchitecturePayload {
  readonly bots?: readonly LiveBot[];
  readonly routines?: readonly RoutineRow[];
}

export default function Architecture(): JSX.Element {
  const [data, setData] = useState<ArchitecturePayload | null>(null);
  const [open, setOpen] = useState<string>("ap");

  useEffect(() => {
    demoApi
      .loadArchitecture()
      .then((payload) => setData(payload as ArchitecturePayload))
      .catch(() => setData(null));
  }, []);

  const grainAgent = isGrainId(open) ? AGENTS_BY_SLUG[open as AgentSlug] : undefined;
  const agent = grainAgent || AGENTS[0];
  const live = (data?.bots || []).find((bot) => bot.slug === agent.slug);
  const routines: readonly RoutineRow[] = data?.routines?.length ? data.routines : ROUTINES;

  return (
    <div>
      <PageHead
        eyebrow="How the team works"
        title="How the finance team is actually organized"
        lede="Standing agents share one company picture. Related jobs live as profiles on those agents. Control agents recheck uncertain work. Audit samples after the fact. This page is drawn from the live office roster, not from an older, larger agent list."
      />
      <h2 className="section-title">The office</h2>
      <p className="muted">Fifteen standing agents, the handles between them, and World not attached.</p>
      <ArchitectureDiagram selected={open} onSelect={setOpen} />
      <div className="grid-2" style={{ marginTop: 18 }}>
        <div className="card">
          <h2>The team</h2>
          <AgentDirectory selected={open} onSelect={setOpen} />
        </div>
        <div className="card office-inspector">
          {open === WORLD_NODE_ID ? (
            <div>
              <div className="eyebrow">{WORLD_INSPECTOR.room}</div>
              <h2 className="office-inspector-name">{WORLD_INSPECTOR.name}</h2>
              <p className="muted">{WORLD_INSPECTOR.title}</p>
              <p>{WORLD_INSPECTOR.body}</p>
            </div>
          ) : (
            <AgentPanel agent={agent} live={live} />
          )}
        </div>
      </div>
      <div className="card" style={{ marginTop: 14 }}>
        <h2>Scheduled office routines</h2>
        <p className="muted">These are recurring jobs on the calendar. They are not extra agents.</p>
        {routines.map((row) => (
          <div className="split" key={row.id || row.name} style={{ marginBottom: 8 }}>
            <div>
              <div>{row.title || humanizeToken(row.id) || row.name}</div>
              <div className="muted">
                {formatCadence(row.cadence)} · {formatAgent(row.bot)}
              </div>
            </div>
          </div>
        ))}
      </div>
      <p className="muted">Older, narrower finance roles still exist as jobs inside these agents. They are not separate standing agents.</p>
    </div>
  );
}

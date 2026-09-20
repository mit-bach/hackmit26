import { useEffect, useState } from "react";
import { statusTone } from "../api";
import { demoApi } from "../demoClient";
import { PageHead, Pill, SourceBadge } from "../layout/Shell";
import { ArchitectureDiagram } from "../components/ArchitectureDiagram";
import { AgentDirectory, AgentPanel } from "../components/AgentPanel";
import { AgentIcon } from "../components/AgentIcon";
import { AGENTS, AGENTS_BY_SLUG, ROUTINES, type AgentSlug } from "../data/agents";
import { WORLD_INSPECTOR, WORLD_NODE_ID, isGrainId } from "../data/officeGraph";
import { formatAgent, formatCadence, formatHandoff, formatStatus, formatSummary, formatWorkflow, humanizeToken } from "../copy";
import { savedGet } from "../data/savedDemo";

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

interface AgentActivityRow {
  readonly workflow?: string;
  readonly status?: string;
  readonly bots?: readonly string[];
  readonly summary?: string;
}

interface AgentsPayload {
  readonly activity?: readonly AgentActivityRow[];
}

export default function Architecture(): JSX.Element {
  const [data, setData] = useState<ArchitecturePayload | null>(null);
  const [activityPayload, setActivityPayload] = useState<AgentsPayload | null>(
    () => savedGet("/api/agents") as AgentsPayload
  );
  const [open, setOpen] = useState<string>("ap");

  useEffect(() => {
    demoApi
      .loadArchitecture()
      .then((payload) => setData(payload as ArchitecturePayload))
      .catch(() => setData(null));
    demoApi
      .loadAgents()
      .then((payload) => setActivityPayload(payload as AgentsPayload))
      .catch(() => setActivityPayload(savedGet("/api/agents") as AgentsPayload));
  }, []);

  const grainAgent = isGrainId(open) ? AGENTS_BY_SLUG[open as AgentSlug] : undefined;
  const agent = grainAgent || AGENTS[0];
  const live = (data?.bots || []).find((bot) => bot.slug === agent.slug);
  const routines: readonly RoutineRow[] = data?.routines?.length ? data.routines : ROUTINES;
  const savedActivity = (savedGet("/api/agents") as AgentsPayload | undefined)?.activity || [];
  const liveActivity = activityPayload?.activity || [];
  const activity = liveActivity.length ? liveActivity : savedActivity;
  const activitySource = liveActivity.length ? "live" : "saved";

  return (
    <div>
      <PageHead
        eyebrow="How the team works"
        title="How the finance team is actually organized"
        lede="Standing agents share one company picture. Related jobs live as profiles on those agents. Control agents recheck uncertain work. Audit samples after the fact. This page is drawn from the live office roster, not from an older, larger agent list."
      />
      <h2 className="section-title">How work moves through the office</h2>
      <p className="muted">
        Fifteen standing agents sit in four rooms. Each icon is one agent. Lines are Handles — records one agent hands to the next. World sits beside incoming records and is not on the live roster.
      </p>
      <ArchitectureDiagram selected={open} onSelect={setOpen} />
      <div className="grid-2" style={{ marginTop: 18 }}>
        <div className="card">
          <h2>Standing agents</h2>
          <AgentDirectory selected={open} onSelect={setOpen} />
        </div>
        <div className="card office-inspector">
          {open === WORLD_NODE_ID ? (
            <div>
              <div className="eyebrow">{WORLD_INSPECTOR.room}</div>
              <div className="agent-heading">
                <span className="sys-node-icon agent-heading-icon">
                  <AgentIcon slug="world" size={28} />
                </span>
                <h2 className="office-inspector-name">{WORLD_INSPECTOR.name}</h2>
              </div>
              <p className="muted">{WORLD_INSPECTOR.title}</p>
              <p>{WORLD_INSPECTOR.body}</p>
            </div>
          ) : (
            <AgentPanel agent={agent} live={live} />
          )}
        </div>
      </div>
      <div className="grid-2" style={{ marginTop: 14 }}>
        <div className="card">
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
          <p className="muted">Older, narrower finance roles still exist as jobs inside these agents. They are not separate standing agents.</p>
        </div>
        <div className="card">
          <h2>What the agents just did</h2>
          {activitySource === "saved" ? <SourceBadge source="saved" /> : null}
          {activity.length === 0 ? (
            <p className="muted">No recent agent activity is available yet. Run a finance workflow to see who handed work to whom.</p>
          ) : (
            activity.map((row, idx) => (
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
  );
}

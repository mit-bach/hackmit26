import { useEffect, useState } from "react";
import { get } from "../api";
import { AgentPanel } from "../components/AgentPanel";
import { ArchitectureDiagram } from "../components/ArchitectureDiagram";
import { AGENTS_BY_SLUG, ROOMS, ROUTINES, type AgentSlug } from "../data/agents";
import {
  WORLD_INSPECTOR,
  WORLD_NODE_ID,
  isGrainId,
  outboundHandles,
} from "../data/officeGraph";
import { formatAgent } from "../copy";

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

function liveBotFor(bots: readonly LiveBot[] | undefined, slug: string): LiveBot | undefined {
  return (bots ?? []).find((bot) => bot.slug === slug);
}

export default function Architecture(): JSX.Element {
  const [data, setData] = useState<ArchitecturePayload | null>(null);
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    get<ArchitecturePayload>("/api/architecture")
      .then(setData)
      .catch(() => setData(null));
  }, []);

  function handleSelect(slug: string): void {
    setOpen((current) => (current === slug ? null : slug));
  }

  const grainAgent = open && isGrainId(open) ? AGENTS_BY_SLUG[open as AgentSlug] : undefined;
  const live = grainAgent ? liveBotFor(data?.bots, grainAgent.slug) : undefined;
  const outbound = open ? outboundHandles(open).slice(0, 5) : [];
  const routines: readonly RoutineRow[] = data?.routines ?? ROUTINES;

  return (
    <div className="office-page">
      <h1>The office</h1>
      <p className="office-lede">Fifteen standing Bots, Handles between them, World not attached.</p>
      <div className={`office-stage${open ? " is-open" : ""}`}>
        <ArchitectureDiagram selected={open} onSelect={handleSelect} />
        {open ? (
          <aside className="office-inspector" aria-live="polite">
            <button type="button" className="office-inspector-close" onClick={() => setOpen(null)}>
              Close
            </button>
            {open === WORLD_NODE_ID ? (
              <div>
                <div className="eyebrow">{WORLD_INSPECTOR.room}</div>
                <h2 className="office-inspector-name">{WORLD_INSPECTOR.name}</h2>
                <p className="muted">{WORLD_INSPECTOR.title}</p>
                <p>{WORLD_INSPECTOR.body}</p>
              </div>
            ) : grainAgent ? (
              <div>
                <div className="eyebrow">{ROOMS.find((room) => room.id === grainAgent.room)?.title}</div>
                <h2 className="office-inspector-name">{grainAgent.name}</h2>
              </div>
            ) : (
              <p className="muted">No Bot selected.</p>
            )}
            {outbound.length ? (
              <div>
                <h2>Outbound Handles</h2>
                <ul className="plain-list">
                  {outbound.map((edge) => (
                    <li key={edge.id}>
                      <span className="mono">{edge.when}</span>
                      {" → "}
                      {formatAgent(edge.to)}
                      {edge.attached ? "" : " — not attached"}
                      <div className="muted">{edge.why}</div>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="muted">This Bot does not start a Handle of its own.</p>
            )}
            {grainAgent ? (
              <details>
                <summary>Skills, profiles, and responsibilities</summary>
                <AgentPanel agent={grainAgent} live={live} />
              </details>
            ) : null}
          </aside>
        ) : null}
      </div>
      <section className="office-routines">
        <h2>Scheduled office routines</h2>
        <p className="muted">These are not extra Bots. They are calendar jobs on the standing roster.</p>
        {routines.map((row) => (
          <div className="split" key={row.id || row.name}>
            <div>
              <div>{row.title || row.id || row.name}</div>
              <div className="muted">
                {row.cadence} · {formatAgent(row.bot)}
              </div>
            </div>
          </div>
        ))}
      </section>
      <p className="muted">Older finance roles still exist as jobs inside these Bots.</p>
    </div>
  );
}

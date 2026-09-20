import { useEffect, useState } from "react";
import { get, statusTone } from "../api";
import { PageHead, Pill } from "../layout/Shell";
import { TraceIds } from "../components/Explain";
import { AGENT_COPY, GRAIN_SLUGS, formatAgent, formatHandoff, formatStatus, formatWorkflow } from "../copy";

export default function Agents() {
  const [data, setData] = useState<any>(null);
  const [open, setOpen] = useState<string>("ap");

  useEffect(() => {
    get("/api/agents").then(setData);
  }, []);

  const bots = data?.bots || GRAIN_SLUGS.map((slug) => ({ slug, name: AGENT_COPY[slug]?.name }));
  const selected = bots.find((item: any) => item.slug === open) || bots[0];
  const story = AGENT_COPY[selected?.slug] || AGENT_COPY[open];

  return (
    <div>
      <PageHead
        eyebrow="Office of the CFO"
        title="15 specialized finance agents"
        lede="One autonomous finance team, divided into specialized responsibilities. Each agent owns a distinct part of the finance workflow, and agents pass structured work to one another."
      />
      <div className="grid-2">
        <div className="card">
          <h2>The team</h2>
          {bots.map((bot: any) => (
            <div key={bot.slug} className="card clickable" onClick={() => setOpen(bot.slug)} style={{ marginBottom: 8 }}>
              <div className="split">
                <strong>{formatAgent(bot.slug)}</strong>
              </div>
              <div className="muted">{(AGENT_COPY[bot.slug] || story)?.role?.slice(0, 140)}</div>
            </div>
          ))}
        </div>
        <div className="stack">
          <div className="card">
            <h2>{story?.name || formatAgent(open)}</h2>
            {story ? (
              <>
                <p>{story.role}</p>
                <h2>Example of what it does</h2>
                <p>{story.example}</p>
                <h2>Inputs it works with</h2>
                <p>{story.inputs}</p>
                <h2>Outputs it produces</h2>
                <p>{story.outputs}</p>
                <h2>Who it passes work to</h2>
                <p>{story.passesTo}</p>
                {selected?.profiles?.length ? (
                  <>
                    <h2>Specialized jobs inside this agent</h2>
                    {(selected.profiles || []).map((profile: any) => (
                      <div key={profile.profile} style={{ marginBottom: 10 }}>
                        <div>
                          {profile.display_name || formatAgent(selected.slug)}
                        </div>
                        <TraceIds ids={[profile.profile]} label="Internal profile" />
                      </div>
                    ))}
                  </>
                ) : null}
              </>
            ) : (
              <p className="muted">Select an agent.</p>
            )}
          </div>
          <div className="card">
            <h2>What the agents just did</h2>
            {(data?.activity || []).length === 0 ? (
              <p className="muted">Launch a demo scenario to append real agent activity. Events are not fabricated.</p>
            ) : (
              (data.activity || []).map((row: any, idx: number) => (
                <div key={idx} style={{ marginBottom: 12 }}>
                  <div className="split">
                    <strong>{formatWorkflow(row.workflow)}</strong>
                    <Pill tone={statusTone(row.status)}>{formatStatus(row.status)}</Pill>
                  </div>
                  <p className="muted">{formatHandoff(row.bots, row.workflow)}</p>
                  <TraceIds ids={row.bots} label="Agents involved" />
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

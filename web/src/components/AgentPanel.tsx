import { AGENTS, AGENTS_BY_SLUG, ROOMS, skillLabel, type AgentDef } from "../data/agents";
import { HANDOFFS, handoffsFor } from "../data/handoffs";
import { AgentIcon } from "./AgentIcon";

interface LiveAgentHint {
  readonly skills?: readonly string[];
}

export function AgentPanel({ agent, live }: { agent: AgentDef; live?: LiveAgentHint }): JSX.Element {
  const edges = handoffsFor(agent.slug);
  const skills: readonly string[] = live?.skills?.length ? live.skills : agent.skills;
  const profiles = agent.profiles;

  return (
    <div className="stack">
      <div>
        <div className="eyebrow">{ROOMS.find((room) => room.id === agent.room)?.title}</div>
        <div className="agent-heading">
          <span className="sys-node-icon agent-heading-icon">
            <AgentIcon slug={agent.slug} size={28} />
          </span>
          <h2 className="office-inspector-name">{agent.name}</h2>
        </div>
        <p>{agent.role}</p>
      </div>
      <div>
        <h2>What it is responsible for</h2>
        <ul className="plain-list">
          {agent.responsibilities.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
      <div>
        <h2>Finance work it handles</h2>
        <p>{agent.workflows.join(" · ")}</p>
      </div>
      {skills.length ? (
        <div>
          <h2>What it knows how to do</h2>
          <ul className="plain-list">
            {skills.map((skill) => (
              <li key={skill}>{skillLabel(skill)}</li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="muted">This agent works from the records handed to it.</p>
      )}
      <div>
        <h2>Jobs inside this agent</h2>
        <ul className="plain-list">
          {profiles.map((profile) => (
            <li key={profile.id}>{profile.name}</li>
          ))}
        </ul>
      </div>
      <div>
        <h2>Information it receives</h2>
        <p>{agent.inputs}</p>
        <h2>Decisions and records it produces</h2>
        <p>{agent.outputs}</p>
      </div>
      <div>
        <h2>Who it works with</h2>
        <p>{agent.passesTo}</p>
        {edges.outbound.length ? (
          <ul className="plain-list">
            {edges.outbound.map((edge) => (
              <li key={`${edge.when}-${edge.to}`}>
                Hands work to {AGENTS_BY_SLUG[edge.to].name}. {edge.why}
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">This agent receives work and returns a decision. It does not start work for another agent on its own.</p>
        )}
        {edges.inbound.length ? (
          <>
            <h2>Work it receives</h2>
            <ul className="plain-list">
              {edges.inbound.map((edge) => (
                <li key={`${edge.from}-${edge.when}`}>
                  From {AGENTS_BY_SLUG[edge.from].name}: {edge.why}
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </div>
      <div>
        <h2>Example of this agent's work</h2>
        <p className="muted">{agent.example}</p>
      </div>
    </div>
  );
}

export function AgentDirectory({
  selected,
  onSelect,
}: {
  selected: string;
  onSelect: (slug: string) => void;
}): JSX.Element {
  return (
    <div className="agent-directory">
      {ROOMS.map((room) => (
        <div key={room.id} className="agent-room">
          <div className="nav-label">{room.title}</div>
          {AGENTS.filter((agent) => agent.room === room.id).map((agent) => (
            <button
              key={agent.slug}
              type="button"
              className={`nav-link agent-pick${selected === agent.slug ? " active" : ""}`}
              onClick={() => onSelect(agent.slug)}
            >
              <span className="sys-node-icon">
                <AgentIcon slug={agent.slug} size={18} />
              </span>
              <span>{agent.name}</span>
            </button>
          ))}
        </div>
      ))}
    </div>
  );
}

export function HandoffList({ slug }: { slug?: string }): JSX.Element {
  const rows = slug ? [...handoffsFor(slug).inbound, ...handoffsFor(slug).outbound] : HANDOFFS;
  const unique = slug ? rows : HANDOFFS;
  return (
    <ul className="plain-list handoff-list">
      {unique.map((edge) => (
        <li key={`${edge.from}-${edge.when}-${edge.to}`}>
          <strong>{AGENTS_BY_SLUG[edge.from].name}</strong>
          {" sent work to "}
          <strong>{AGENTS_BY_SLUG[edge.to].name}</strong>
          <div className="muted">{edge.why}</div>
        </li>
      ))}
    </ul>
  );
}

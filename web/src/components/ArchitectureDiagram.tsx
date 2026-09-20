import { AGENTS, ROOMS, type AgentSlug } from "../data/agents";
import { HANDOFFS, PRINCIPAL_FLOWS } from "../data/handoffs";

export function ArchitectureDiagram({
  selected,
  onSelect,
}: {
  selected: string | null;
  onSelect: (slug: string) => void;
}) {
  const related = new Set<string>();
  if (selected) {
    related.add(selected);
    for (const edge of HANDOFFS) {
      if (edge.from === selected) related.add(edge.to);
      if (edge.to === selected) related.add(edge.from);
    }
  }

  const selectedEdges = selected ? HANDOFFS.filter((edge) => edge.from === selected || edge.to === selected) : [];

  return (
    <div className="arch-diagram">
      <div className="arch-shared card">
        <div className="eyebrow">Shared company context</div>
        <h3>One picture of the company</h3>
        <p>
          Open vendor bills, unpaid customer invoices, bank activity, the ledger, period lock, and saved decisions from earlier months. Agents do not keep private copies of the books.
        </p>
      </div>
      <div className="arch-rooms">
        {ROOMS.map((room) => (
          <div className="arch-room" key={room.id}>
            <h3>{room.title}</h3>
            <p className="muted">{room.plain}</p>
            <div className="arch-nodes">
              {AGENTS.filter((agent) => agent.room === room.id).map((agent) => {
                const on = !selected || related.has(agent.slug);
                return (
                  <button
                    type="button"
                    key={agent.slug}
                    className={`arch-node${selected === agent.slug ? " selected" : ""}${selected && !on ? " dim" : ""}`}
                    onClick={() => onSelect(agent.slug)}
                  >
                    {agent.name.replace(/ Agent$/, "")}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
      <div className="arch-flows">
        {PRINCIPAL_FLOWS.map((flow) => (
          <div className="chip" key={flow.label}>
            {flow.label}
          </div>
        ))}
      </div>
      {selected ? (
        <div className="card">
          <h2>Why this agent talks to others</h2>
          {selectedEdges.length ? (
            selectedEdges.map((edge) => (
              <p key={`${edge.from}-${edge.when}-${edge.to}`}>
                The {name(edge.from)} handed this to the {name(edge.to)}. {edge.why}
              </p>
            ))
          ) : (
            <p className="muted">This agent works from shared records rather than starting work for another agent.</p>
          )}
        </div>
      ) : (
        <p className="muted">Select an agent to see who it talks to and why. The default view is grouped by job so the picture stays readable.</p>
      )}
    </div>
  );
}

function name(slug: AgentSlug) {
  return AGENTS.find((agent) => agent.slug === slug)?.name || slug;
}

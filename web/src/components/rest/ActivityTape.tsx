import { statusTone } from "../../api";
import { formatHandoff, formatStatus, formatSummary, formatWorkflow } from "../../copy";
import { AGENTS, type AgentSlug } from "../../data/agents";
import { Pill } from "../../layout/Shell";
import { asRecord, readString } from "./kernel";

export interface ActivityRow {
  readonly key: string;
  readonly workflow?: string;
  readonly status?: string;
  readonly summary?: string;
  readonly bots: unknown;
  readonly slugs: readonly string[];
}

export function activityFromUnknown(value: unknown, index: number): ActivityRow | null {
  const rec = asRecord(value);
  if (!rec) {
    return null;
  }
  const bots = rec.bots ?? rec.bot;
  const slugs: string[] = [];
  const pushSlug = (raw: string): void => {
    const slug = raw.trim().replace(/_/g, "-").replace(/^bot-/, "");
    if (slug) {
      slugs.push(slug);
    }
  };
  if (typeof bots === "string") {
    pushSlug(bots);
  } else if (Array.isArray(bots)) {
    for (const entry of bots) {
      if (typeof entry === "string") {
        pushSlug(entry);
        continue;
      }
      const row = asRecord(entry);
      const slug = readString(row, "slug") || readString(row, "bot") || readString(row, "display_name");
      if (slug) {
        pushSlug(slug);
      }
    }
  }
  return {
    key: readString(rec, "trace_id") || `activity-${index}`,
    workflow: readString(rec, "workflow"),
    status: readString(rec, "status"),
    summary: readString(rec, "summary"),
    bots,
    slugs: Array.from(new Set(slugs)),
  };
}

interface ActivityTapeProps {
  readonly rows: readonly ActivityRow[];
  readonly filter: string | null;
}

export function ActivityTape(props: ActivityTapeProps): JSX.Element {
  const selected = props.filter;
  const filtered = selected ? props.rows.filter((row) => row.slugs.includes(selected)) : props.rows;
  if (!filtered.length) {
    return (
      <div className="rest-tape is-empty" aria-label="Activity tape">
        <p className="muted">Run a simulation to append real agent activity. Events are not fabricated.</p>
      </div>
    );
  }
  return (
    <ol className="rest-tape" aria-label="Activity tape">
      {filtered.map((row) => (
        <li key={row.key} className="rest-tape-row">
          <div className="split">
            <strong>{formatWorkflow(row.workflow)}</strong>
            <Pill tone={statusTone(row.status)}>{formatStatus(row.status)}</Pill>
          </div>
          <p>{formatHandoff(row.bots, row.workflow)}</p>
          {row.summary ? <p className="muted">{formatSummary(row.summary)}</p> : null}
        </li>
      ))}
    </ol>
  );
}

interface SlugFilterProps {
  readonly selected: AgentSlug | null;
  readonly onSelect: (slug: AgentSlug | null) => void;
}

function oneLineRole(role: string): string {
  const first = role.split(/(?<=\.)\s/)[0] || role;
  return first;
}

export function SlugFilter(props: SlugFilterProps): JSX.Element {
  return (
    <div className="rest-slug-dir" aria-label="Bot filter">
      <button
        type="button"
        className={`rest-chip${!props.selected ? " is-on" : ""}`}
        aria-pressed={!props.selected}
        onClick={() => props.onSelect(null)}
      >
        all
      </button>
      {AGENTS.map((agent) => (
        <button
          type="button"
          key={agent.slug}
          className={`rest-chip rest-chip-slug${props.selected === agent.slug ? " is-on" : ""}`}
          aria-pressed={props.selected === agent.slug}
          title={oneLineRole(agent.role)}
          onClick={() => props.onSelect(props.selected === agent.slug ? null : agent.slug)}
        >
          <span className="mono">{agent.slug}</span>
          <span className="rest-dir-role">{oneLineRole(agent.role)}</span>
        </button>
      ))}
    </div>
  );
}

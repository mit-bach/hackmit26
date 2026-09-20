import { useState } from "react";
import { Link } from "react-router-dom";
import {
  CAPABILITY_PIPES,
  CAPABILITY_STATUSES,
  capabilityById,
  compactPipeCounts,
  filterCapabilities,
  rowsInPipe,
  type CapabilityFilter,
  type CapabilityRow,
  type CapabilityStatus,
} from "../data/capabilityMatrix";

export interface CoverageGridProps {
  compact?: boolean;
  intro?: boolean;
}

const FILTERS: readonly { id: CapabilityFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "office-live", label: "Office-live" },
  { id: "partial", label: "Partial" },
  { id: "not-built", label: "Not built" },
];

const STATUS_PILL: Record<CapabilityStatus, string> = {
  "kernel-live": "info",
  "office-live": "ok",
  partial: "warn",
  "not-built": "",
};

function statusClass(status: CapabilityStatus): string {
  return `cap-cell cap-cell--${status}`;
}

function CompactWall(): JSX.Element {
  const counts = compactPipeCounts();
  return (
    <section className="cap-compact">
      <div className="cap-compact-pipes">
        {counts.map((item) => (
          <div className="cap-compact-pipe" key={item.pipe}>
            <span className="cap-compact-label">{item.label}</span>
            <span className="cap-compact-count">
              {item.live} live / {item.notBuilt} not-built
            </span>
          </div>
        ))}
      </div>
      <p className="cap-compact-link">
        <Link to="/coverage">Open the capability wall</Link>
      </p>
    </section>
  );
}

interface CapabilityDrawerProps {
  readonly row: CapabilityRow;
}

function CapabilityDrawer({ row }: CapabilityDrawerProps): JSX.Element {
  const pillTone = STATUS_PILL[row.status];
  return (
    <aside className="cap-drawer" aria-live="polite">
      <div className="mono cap-drawer-id">{row.id}</div>
      <p className="cap-drawer-sentence">{row.sentence}</p>
      <div className="cap-drawer-pills">
        <span className={`pill${pillTone ? ` ${pillTone}` : ""}`}>{row.status}</span>
        {row.caption ? <span className="pill info">{row.caption}</span> : null}
      </div>
      {row.agents.length > 0 ? (
        <div className="cap-grains">
          {row.agents.map((slug) => (
            <span className="mono pill" key={slug}>
              {slug}
            </span>
          ))}
        </div>
      ) : null}
      {row.links.length > 0 ? (
        <div className="cap-links">
          {row.links.map((link) => (
            <Link className="cap-open" key={link.href} to={link.href}>
              {link.label}
            </Link>
          ))}
        </div>
      ) : null}
      {row.notice ? <p className="muted cap-notice">{row.notice}</p> : null}
    </aside>
  );
}

function CapabilityWall(): JSX.Element {
  const [filter, setFilter] = useState<CapabilityFilter>("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const visible = filterCapabilities(filter);
  const selected = selectedId ? capabilityById(selectedId) : undefined;
  const selectedVisible =
    selected !== undefined && visible.some((row) => row.id === selected.id);

  function onFilter(next: CapabilityFilter): void {
    setFilter(next);
    if (selectedId === null) {
      return;
    }
    const row = capabilityById(selectedId);
    if (row && next !== "all" && row.status !== next) {
      setSelectedId(null);
    }
  }

  function onSelect(id: string): void {
    setSelectedId((current) => (current === id ? null : id));
  }

  return (
    <section className="cap-wall">
      <h1>What it can do</h1>
      <p className="cap-lede">
        Kernel-live is the engine; Office-live is a standing Bot; not-built is not-built
      </p>
      <div className="cap-legend">
        {CAPABILITY_STATUSES.map((status) => (
          <span className={`cap-swatch cap-swatch--${status}`} key={status}>
            <i aria-hidden="true" />
            {status}
          </span>
        ))}
      </div>
      <div className="cap-filters" role="toolbar" aria-label="Capability status">
        {FILTERS.map((item) => (
          <button
            className={`btn${filter === item.id ? " primary" : ""}`}
            key={item.id}
            type="button"
            aria-pressed={filter === item.id}
            onClick={() => {
              onFilter(item.id);
            }}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="cap-groups">
        {CAPABILITY_PIPES.map((band) => {
          const cells = rowsInPipe(band.id, visible);
          if (cells.length === 0) {
            return null;
          }
          return (
            <div className="cap-band" key={band.id}>
              <h2 className="cap-band-label">{band.label}</h2>
              <div className="cap-band-cells">
                {cells.map((row) => {
                  const open = selectedId === row.id;
                  return (
                    <button
                      className={`${statusClass(row.status)}${open ? " is-selected" : ""}`}
                      key={row.id}
                      type="button"
                      data-capability={row.id}
                      data-status={row.status}
                      aria-pressed={open}
                      onClick={() => {
                        onSelect(row.id);
                      }}
                    >
                      <span className="mono">{row.id}</span>
                      <span className="cap-cell-title">{row.title}</span>
                      <span className="cap-cell-status">{row.status}</span>
                      {row.caption ? <span className="cap-cell-caption">{row.caption}</span> : null}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
      {selectedVisible && selected ? <CapabilityDrawer row={selected} /> : null}
    </section>
  );
}

export function CoverageGrid({ compact = false, intro = true }: CoverageGridProps): JSX.Element {
  if (compact) {
    return <CompactWall />;
  }
  void intro;
  return <CapabilityWall />;
}

import { useId, useMemo, useState } from "react";
import { AgentIcon } from "./AgentIcon";
import {
  OFFICE_GRAPH_EDGES,
  OFFICE_GRAPH_NODES,
  OFFICE_ROOM_BANDS,
  WORLD_NODE_ID,
  edgeWeight,
  isIncidentHandle,
  isPrincipalHandle,
  type OfficeGraphEdge,
} from "../data/officeGraph";
import {
  FLOW_COL_GAP,
  FLOW_NODE_W,
  FLOW_PAD_X,
  labelWidth,
  layoutOfficeNodes,
  nudgeLabels,
  routeOfficeEdges,
  type LabelAnchor,
} from "../data/flowchartRoute";

export interface SystemFlowchartProps {
  readonly selected: string | null;
  readonly onSelect: (slug: string) => void;
}

const BAND_CAPTION: Record<string, string> = {
  world: "World",
  intake: "Incoming records",
  pay: "Company owes",
  cash: "Bank and cash",
  "books-close": "Finishing the books",
};

function cx(...parts: Array<string | false | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

function nodeAriaLabel(label: string, notAttached: boolean): string {
  if (notAttached) {
    return `${label} (not attached)`;
  }
  return label;
}

function displayName(id: string, label: string): string {
  if (id === WORLD_NODE_ID) {
    return "World";
  }
  return label;
}

function showEdgeLabel(edge: OfficeGraphEdge, selected: string | null, showAll: boolean): boolean {
  if (selected) {
    return isIncidentHandle(edge, selected);
  }
  if (showAll) {
    return false;
  }
  return isPrincipalHandle(edge) || edge.attached === false;
}

function visualOpacity(edge: OfficeGraphEdge, selected: string | null, showAll: boolean): number {
  const weight = edgeWeight(edge, selected, showAll);
  if (weight >= 1) {
    return 1;
  }
  if (edge.attached === false) {
    return selected && !isIncidentHandle(edge, selected) ? 0.18 : 0.72;
  }
  if (isPrincipalHandle(edge) && !showAll) {
    return selected ? 0.28 : 1;
  }
  return weight;
}

export function SystemFlowchart({ selected, onSelect }: SystemFlowchartProps): JSX.Element {
  const markerId = useId().replace(/:/g, "");
  const [showAll, setShowAll] = useState(false);
  const layout = useMemo(() => layoutOfficeNodes(OFFICE_GRAPH_NODES), []);
  const routed = useMemo(() => routeOfficeEdges(OFFICE_GRAPH_EDGES, layout), [layout]);
  const boxes = useMemo(() => [...layout.boxes.values()], [layout]);
  const edgeById = useMemo(() => new Map(OFFICE_GRAPH_EDGES.map((edge) => [edge.id, edge])), []);

  const labels = useMemo(() => {
    const anchors: LabelAnchor[] = [];
    for (const route of routed) {
      const edge = edgeById.get(route.id);
      if (!edge || !showEdgeLabel(edge, selected, showAll)) {
        continue;
      }
      anchors.push({
        id: route.id,
        text: edge.when,
        x: route.labelX,
        y: route.labelY,
      });
    }
    return nudgeLabels(anchors, boxes);
  }, [boxes, edgeById, routed, selected, showAll]);

  const labelById = useMemo(() => new Map(labels.map((label) => [label.id, label])), [labels]);
  const attachedMarker = `flow-arrow-${markerId}`;
  const detachedMarker = `flow-arrow-dash-${markerId}`;

  return (
    <div className="office-graph system-flow">
      <div className="system-flow-toolbar">
        <label className="office-graph-all">
          <input
            type="checkbox"
            checked={showAll}
            onChange={(event) => setShowAll(event.target.checked)}
          />
          Show all Handles
        </label>
        <p className="system-flow-legend">
          Solid lines are live Handles. Dashed lines go through World, which is not on the live roster.
          Select an agent to read only the Handles that touch it.
        </p>
      </div>
      <div className="system-flow-scroll">
        <div className="system-flow-rooms" style={{ width: layout.width }} aria-hidden="true">
          {OFFICE_ROOM_BANDS.map((band, index) => (
            <span
              key={band.id}
              style={{
                left: FLOW_PAD_X + index * (FLOW_NODE_W + FLOW_COL_GAP),
                width: FLOW_NODE_W,
              }}
            >
              {BAND_CAPTION[band.id] ?? band.label}
            </span>
          ))}
        </div>
        <div className="system-flow-canvas" style={{ width: layout.width, height: layout.height }}>
          <svg
            className="flow-edges"
            width={layout.width}
            height={layout.height}
            viewBox={`0 0 ${layout.width} ${layout.height}`}
            aria-hidden="false"
          >
            <defs>
              <marker
                id={attachedMarker}
                markerWidth="7"
                markerHeight="7"
                refX="6"
                refY="3.5"
                orient="auto"
              >
                <path d="M0 0 7 3.5 0 7Z" fill="var(--line-strong)" />
              </marker>
              <marker
                id={detachedMarker}
                markerWidth="7"
                markerHeight="7"
                refX="6"
                refY="3.5"
                orient="auto"
              >
                <path d="M0 0 7 3.5 0 7Z" fill="var(--faint)" />
              </marker>
            </defs>
            {routed.map((route) => {
              const edge = edgeById.get(route.id);
              if (!edge) {
                return null;
              }
              const detached = edge.attached === false;
              const opacity = visualOpacity(edge, selected, showAll);
              const title = detached ? `${edge.when}: not attached` : `${edge.when} — ${edge.why}`;
              return (
                <path
                  key={route.id}
                  className={cx("flow-edge", detached && "not-attached")}
                  d={route.d}
                  opacity={opacity}
                  markerEnd={`url(#${detached ? detachedMarker : attachedMarker})`}
                  aria-label={detached ? `${edge.when} not attached` : edge.when}
                >
                  <title>{title}</title>
                </path>
              );
            })}
            {routed.map((route) => {
              const label = labelById.get(route.id);
              const edge = edgeById.get(route.id);
              if (!label || !edge) {
                return null;
              }
              const width = labelWidth(label.text);
              return (
                <g key={`${route.id}-label`} className="flow-edge-label-group" pointerEvents="none">
                  <rect
                    className="flow-edge-label-bg"
                    x={label.x - width / 2}
                    y={label.y - 8}
                    width={width}
                    height={16}
                    rx={3}
                  />
                  <text className="flow-edge-label" x={label.x} y={label.y} textAnchor="middle" dominantBaseline="middle">
                    {label.text}
                  </text>
                </g>
              );
            })}
          </svg>
          {OFFICE_GRAPH_NODES.map((node) => {
            const box = layout.boxes.get(node.id);
            if (!box) {
              return null;
            }
            const notAttached = node.status === "not-attached";
            const name = displayName(node.id, node.label);
            return (
              <button
                key={node.id}
                type="button"
                className={cx(
                  "flow-node",
                  "sys-node",
                  node.kind,
                  notAttached && "not-attached",
                  selected === node.id && "is-selected"
                )}
                style={{ left: box.x, top: box.y, width: box.w, height: box.h }}
                data-node-id={node.id}
                aria-label={nodeAriaLabel(node.label, notAttached)}
                aria-pressed={selected === node.id}
                onClick={() => onSelect(node.id)}
              >
                <span className="sys-node-icon">
                  <AgentIcon slug={node.id} size={22} />
                </span>
                <span className="sys-node-copy">
                  <span className="sys-node-name">{name}</span>
                  {notAttached ? <span className="sys-node-note">not on live roster</span> : null}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

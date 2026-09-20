import { useEffect, useRef, useState, type MouseEvent } from "react";
import { FlowPlay, type FlowEdge, type FlowNode, type FlowStep } from "./FlowPlay";
import {
  OFFICE_GRAPH_EDGES,
  OFFICE_GRAPH_NODES,
  OFFICE_ROOM_BANDS,
  edgeWeight,
  type OfficeGraphEdge,
  type OfficeGraphNode,
} from "../data/officeGraph";

export interface OfficeGraphProps {
  readonly selected: string | null;
  readonly onSelect: (slug: string) => void;
}

const EMPTY_STEPS: readonly FlowStep[] = [];

function toFlowNode(node: OfficeGraphNode): FlowNode {
  return {
    id: node.id,
    label: node.label,
    kind: node.kind,
    room: node.room,
    column: node.column,
    row: node.row,
    status: node.status,
  };
}

function toFlowEdge(edge: OfficeGraphEdge): FlowEdge {
  return {
    id: edge.id,
    from: edge.from,
    to: edge.to,
    label: edge.when,
    attached: edge.attached,
  };
}

const FLOW_NODES: readonly FlowNode[] = OFFICE_GRAPH_NODES.map(toFlowNode);
const FLOW_EDGES: readonly FlowEdge[] = OFFICE_GRAPH_EDGES.map(toFlowEdge);

function applyGraphChrome(
  root: HTMLElement,
  selected: string | null,
  showAll: boolean
): void {
  const paths = root.querySelectorAll<SVGPathElement>("path.flow-edge");
  const labels = root.querySelectorAll<SVGTextElement>("text.flow-edge-label");
  paths.forEach((path, index) => {
    const edge = OFFICE_GRAPH_EDGES[index];
    if (!edge) {
      return;
    }
    const weight = String(edgeWeight(edge, selected, showAll));
    path.style.opacity = weight;
    const label = labels[index];
    if (label) {
      label.style.opacity = weight;
    }
  });
  root.querySelectorAll<HTMLElement>("[data-node-id]").forEach((node) => {
    node.classList.toggle("is-selected", node.dataset.nodeId === selected);
  });
}

export function OfficeGraph({ selected, onSelect }: OfficeGraphProps): JSX.Element {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    const root = wrapRef.current;
    if (!root) {
      return undefined;
    }
    const apply = (): void => {
      applyGraphChrome(root, selected, showAll);
    };
    apply();
    if (typeof MutationObserver === "undefined") {
      return undefined;
    }
    const observer = new MutationObserver(apply);
    observer.observe(root, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, [selected, showAll]);

  function handleGraphClick(event: MouseEvent<HTMLDivElement>): void {
    const target = event.target;
    if (!(target instanceof Element)) {
      return;
    }
    const button = target.closest("[data-node-id]");
    if (!(button instanceof HTMLElement)) {
      return;
    }
    const id = button.dataset.nodeId;
    if (!id) {
      return;
    }
    onSelect(id);
  }

  return (
    <div className="office-graph" ref={wrapRef}>
      <label className="office-graph-all">
        <input
          type="checkbox"
          checked={showAll}
          onChange={(event) => setShowAll(event.target.checked)}
        />
        Show all Handles
      </label>
      <div className="office-graph-rooms" aria-hidden="true">
        {OFFICE_ROOM_BANDS.map((band) => (
          <span key={band.id}>{band.label}</span>
        ))}
      </div>
      <div className="office-graph-canvas" onClick={handleGraphClick}>
        <FlowPlay nodes={FLOW_NODES} edges={FLOW_EDGES} steps={EMPTY_STEPS} mode="story" />
      </div>
    </div>
  );
}

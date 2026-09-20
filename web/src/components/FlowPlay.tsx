import { useEffect, useMemo, useRef, useState } from "react";
import { formatStage } from "../copy";
import { AgentIcon } from "./AgentIcon";

export type FlowMode = "story" | "live";
export type FlowNodeKind = "event" | "source" | "operator" | "verifier" | "assurance";
export type FlowNodeStatus = "idle" | "active" | "done" | "blocked" | "not-attached";

export interface FlowNode {
  readonly id: string;
  readonly label: string;
  readonly kind: FlowNodeKind;
  readonly room?: "intake" | "pay" | "cash" | "books-close";
  readonly column?: number;
  readonly row?: number;
  readonly status?: FlowNodeStatus;
}

export interface FlowEdge {
  readonly id: string;
  readonly from: string;
  readonly to: string;
  readonly label: string;
  readonly attached?: boolean;
}

export interface FlowStep {
  readonly id: string;
  readonly title: string;
  readonly nodeId: string;
  readonly body?: string;
  readonly manipulations: readonly string[];
  readonly handoff?: { readonly to: string; readonly why: string };
  readonly artifactIds?: readonly string[];
  readonly status?: FlowNodeStatus;
}

export interface LiveStage {
  readonly id?: string;
  readonly bot?: string;
  readonly slug?: string;
  readonly label?: string;
  readonly status?: string;
  readonly detail?: string;
}

export interface FlowPlayProps {
  readonly nodes: readonly FlowNode[];
  readonly edges: readonly FlowEdge[];
  readonly steps: readonly FlowStep[];
  readonly activeStepId?: string;
  readonly mode?: FlowMode;
  readonly liveStages?: readonly LiveStage[] | Readonly<{
    result?: { stages?: readonly LiveStage[] };
    stages?: readonly LiveStage[];
  }>;
  readonly onStepChange?: (stepId: string) => void;
  readonly autoplay?: boolean;
}

const NODE_W = 148;
const NODE_H = 56;
const V_GAP = 28;
const MIN_H_GAP = 64;
const PAD_X = 16;
const PAD_Y = 18;
const BAND_GAP = 36;
const STEP_MS = 1100;
const WRAP_NODE_COUNT = 16;
const WRAP_COL_COUNT = 12;
const COLS_PER_BAND = 6;

interface NodeBox {
  readonly id: string;
  readonly x: number;
  readonly y: number;
  readonly w: number;
  readonly h: number;
}

interface FlowLayout {
  readonly width: number;
  readonly height: number;
  readonly boxes: Map<string, NodeBox>;
}

function cx(...parts: Array<string | false | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

export function resolveBotId(raw: string): string {
  return raw.trim().replace(/_/g, "-").replace(/^bot-/, "");
}

export function normalizeLiveStages(value: unknown): LiveStage[] {
  if (value == null) {
    return [];
  }
  if (Array.isArray(value)) {
    if (value.length === 1 && isStageWrapper(value[0])) {
      return normalizeLiveStages(value[0]);
    }
    return value as LiveStage[];
  }
  if (typeof value === "object") {
    const rec = value as { result?: { stages?: unknown }; stages?: unknown };
    if (Array.isArray(rec.result?.stages)) {
      return rec.result.stages as LiveStage[];
    }
    if (Array.isArray(rec.stages)) {
      return rec.stages as LiveStage[];
    }
  }
  return [];
}

function isStageWrapper(value: unknown): boolean {
  if (!value || typeof value !== "object") {
    return false;
  }
  const rec = value as { bot?: unknown; slug?: unknown; stages?: unknown; result?: unknown };
  if (rec.bot || rec.slug) {
    return false;
  }
  return Boolean(rec.stages || rec.result);
}

function computeColumns(nodes: readonly FlowNode[], edges: readonly FlowEdge[]): Map<string, number> {
  const incoming = new Map<string, string[]>();
  for (const node of nodes) {
    incoming.set(node.id, []);
  }
  for (const edge of edges) {
    incoming.get(edge.to)?.push(edge.from);
  }
  const col = new Map<string, number>();
  for (const node of nodes) {
    if (typeof node.column === "number") {
      col.set(node.id, node.column);
    } else if (node.kind === "event") {
      col.set(node.id, 0);
    }
  }
  let changed = true;
  let guard = 0;
  while (changed && guard < nodes.length + 2) {
    changed = false;
    guard += 1;
    for (const node of nodes) {
      if (typeof node.column === "number") {
        continue;
      }
      const ins = incoming.get(node.id) ?? [];
      if (ins.length === 0) {
        if (!col.has(node.id)) {
          col.set(node.id, 0);
          changed = true;
        }
        continue;
      }
      const preds = ins.map((id) => col.get(id)).filter((value): value is number => value !== undefined);
      if (preds.length === 0) {
        continue;
      }
      const next = Math.max(...preds) + 1;
      if (col.get(node.id) !== next) {
        col.set(node.id, next);
        changed = true;
      }
    }
  }
  for (const node of nodes) {
    if (!col.has(node.id)) {
      col.set(node.id, 0);
    }
  }
  return col;
}

function layoutFlow(nodes: readonly FlowNode[], edges: readonly FlowEdge[], containerWidth: number): FlowLayout {
  const columns = computeColumns(nodes, edges);
  let maxCol = 0;
  for (const value of columns.values()) {
    maxCol = Math.max(maxCol, value);
  }
  const colCount = Math.max(1, maxCol + 1);
  const wrap = nodes.length > WRAP_NODE_COUNT || colCount > WRAP_COL_COUNT;
  const slotCols = wrap ? COLS_PER_BAND : colCount;
  const byCol = new Map<number, FlowNode[]>();
  const order = new Map(nodes.map((node, idx) => [node.id, idx]));
  for (const node of nodes) {
    const column = columns.get(node.id) ?? 0;
    const list = byCol.get(column) ?? [];
    byCol.set(column, [...list, node]);
  }
  for (const [column, list] of byCol) {
    byCol.set(
      column,
      [...list].sort((left, right) => {
        const rowDelta = (left.row ?? 0) - (right.row ?? 0);
        if (rowDelta !== 0) {
          return rowDelta;
        }
        return (order.get(left.id) ?? 0) - (order.get(right.id) ?? 0);
      })
    );
  }
  const bandOf = (column: number): number => (wrap ? Math.floor(column / COLS_PER_BAND) : 0);
  const colInBand = (column: number): number => (wrap ? column % COLS_PER_BAND : column);
  const bandStack = new Map<number, number>();
  for (let column = 0; column <= maxCol; column += 1) {
    const list = byCol.get(column) ?? [];
    const stack = Math.max(list.length, 1, ...list.map((node) => (node.row ?? 0) + 1));
    const band = bandOf(column);
    bandStack.set(band, Math.max(bandStack.get(band) ?? 0, stack));
  }
  const bandCount = wrap ? Math.floor(maxCol / COLS_PER_BAND) + 1 : 1;
  const minWidth = PAD_X * 2 + slotCols * NODE_W + Math.max(0, slotCols - 1) * MIN_H_GAP;
  const width = Math.max(containerWidth, minWidth);
  const colPitch = NODE_W + MIN_H_GAP;
  const bandTop = new Map<number, number>();
  let yCursor = PAD_Y;
  for (let band = 0; band < bandCount; band += 1) {
    bandTop.set(band, yCursor);
    const stack = Math.max(1, bandStack.get(band) ?? 1);
    yCursor += stack * NODE_H + Math.max(0, stack - 1) * V_GAP + BAND_GAP;
  }
  const height = Math.max(220, yCursor - BAND_GAP + PAD_Y);
  const boxes = new Map<string, NodeBox>();
  for (const node of nodes) {
    const column = columns.get(node.id) ?? 0;
    const band = bandOf(column);
    const siblings = byCol.get(column) ?? [node];
    const idx = Math.max(0, siblings.findIndex((item) => item.id === node.id));
    const stackIndex = node.row ?? idx;
    boxes.set(node.id, {
      id: node.id,
      x: PAD_X + colInBand(column) * colPitch,
      y: (bandTop.get(band) ?? PAD_Y) + stackIndex * (NODE_H + V_GAP),
      w: NODE_W,
      h: NODE_H,
    });
  }
  return { width, height, boxes };
}

function orthogonalPath(from: NodeBox, to: NodeBox, lane: number): string {
  const x1 = from.x + from.w;
  const y1 = from.y + from.h / 2;
  const x2 = to.x;
  const y2 = to.y + to.h / 2;
  const yOffset = lane * 8;
  if (x2 >= x1 && Math.abs(y1 - y2) < 3) {
    const y = y1 + yOffset;
    return `M ${x1} ${y} H ${x2}`;
  }
  if (x2 >= x1) {
    const midX = x1 + Math.max(28, (x2 - x1) * 0.42) + lane * 12;
    return `M ${x1} ${y1} H ${midX} V ${y2} H ${x2}`;
  }
  const stub = Math.max(20, 24 + lane * 10);
  return `M ${x1} ${y1} H ${x1 + stub} V ${y2 + yOffset} H ${x2}`;
}

function labelPoint(from: NodeBox, to: NodeBox, lane: number): { x: number; y: number } {
  const x1 = from.x + from.w;
  const y1 = from.y + from.h / 2;
  const x2 = to.x;
  const y2 = to.y + to.h / 2;
  if (x2 >= x1 && Math.abs(y1 - y2) < 3) {
    return { x: (x1 + x2) / 2, y: y1 + lane * 8 - 14 };
  }
  if (x2 >= x1) {
    const midX = x1 + Math.max(28, (x2 - x1) * 0.42) + lane * 12;
    return { x: midX, y: (y1 + y2) / 2 - 4 };
  }
  return { x: (x1 + x2) / 2, y: Math.min(y1, y2) - 14 };
}

function estimateLabelWidth(text: string): number {
  return Math.max(28, text.length * 6.3 + 10);
}

function assignFlowLanes(edges: readonly FlowEdge[]): Map<string, number> {
  const groups = new Map<string, string[]>();
  for (const edge of edges) {
    const key = `${edge.from}->${edge.to}`;
    const list = groups.get(key) ?? [];
    groups.set(key, [...list, edge.id]);
  }
  const lanes = new Map<string, number>();
  for (const ids of groups.values()) {
    ids.forEach((id, index) => {
      lanes.set(id, index);
    });
  }
  return lanes;
}

function findActiveEdgeId(
  edges: readonly FlowEdge[],
  fromId: string | undefined,
  toId: string
): string | undefined {
  if (fromId) {
    const direct = edges.find((edge) => edge.from === fromId && edge.to === toId && edge.attached !== false);
    if (direct) {
      return direct.id;
    }
  }
  return edges.find((edge) => edge.to === toId && edge.attached !== false)?.id;
}

function resolveStageNodeId(stage: LiveStage, nodeIds: ReadonlySet<string>): string | undefined {
  const raw = String(stage.bot || stage.slug || stage.id || "");
  if (!raw) {
    return undefined;
  }
  const id = resolveBotId(raw);
  return nodeIds.has(id) ? id : undefined;
}

function liveStatusHint(status: string | undefined): FlowNodeStatus | undefined {
  const value = (status || "").toLowerCase();
  if (value.includes("block") || value.includes("fail")) {
    return "blocked";
  }
  if (value.includes("not-attached") || value.includes("not_attached")) {
    return "not-attached";
  }
  return undefined;
}

function storyNodeStatus(node: FlowNode, steps: readonly FlowStep[], index: number): FlowNodeStatus {
  if (node.status === "not-attached") {
    return "not-attached";
  }
  const current = steps[index];
  if (!current) {
    return node.status ?? "idle";
  }
  if (current.nodeId === node.id) {
    return current.status ?? node.status ?? "active";
  }
  const seen = steps.slice(0, index).some((step) => step.nodeId === node.id);
  if (seen && node.status !== "blocked") {
    return "done";
  }
  return node.status ?? "idle";
}

function liveNodeStatus(node: FlowNode, resolved: readonly string[], stages: readonly LiveStage[]): FlowNodeStatus {
  if (node.status === "not-attached") {
    return "not-attached";
  }
  if (resolved.length === 0) {
    return node.status ?? "idle";
  }
  const currentId = resolved[resolved.length - 1];
  if (node.id === currentId) {
    const last = stages[stages.length - 1];
    return liveStatusHint(last?.status) ?? "active";
  }
  if (resolved.includes(node.id)) {
    return "done";
  }
  return node.status ?? "idle";
}

function nodeAriaLabel(node: FlowNode, status: FlowNodeStatus): string {
  if (status === "not-attached") {
    return `${node.label} (not attached)`;
  }
  if (status === "blocked") {
    return `${node.label} (blocked)`;
  }
  return node.label;
}

export function FlowPlay(props: FlowPlayProps): JSX.Element {
  const { nodes, edges, steps, activeStepId, mode, liveStages, onStepChange, autoplay = false } = props;
  const stages = useMemo(() => normalizeLiveStages(liveStages), [liveStages]);
  const isLive = mode === "live" || stages.length > 0;
  const nodeIds = useMemo(() => new Set(nodes.map((node) => node.id)), [nodes]);
  const resolvedLive = useMemo(() => {
    const ids: string[] = [];
    for (const stage of stages) {
      const id = resolveStageNodeId(stage, nodeIds);
      if (id) {
        ids.push(id);
      }
    }
    return ids;
  }, [stages, nodeIds]);

  const wrapRef = useRef<HTMLDivElement>(null);
  const onStepChangeRef = useRef(onStepChange);
  onStepChangeRef.current = onStepChange;
  const [width, setWidth] = useState(960);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(() => Boolean(autoplay) && !isLive && steps.length > 1);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) {
      return undefined;
    }
    const apply = (): void => {
      const next = el.clientWidth || 960;
      setWidth((prev) => (Math.abs(prev - next) < 2 ? prev : next));
    };
    apply();
    if (typeof ResizeObserver === "undefined") {
      return undefined;
    }
    const observer = new ResizeObserver(apply);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (activeStepId == null) {
      return;
    }
    const next = steps.findIndex((step) => step.id === activeStepId);
    if (next >= 0) {
      setIndex(next);
    }
  }, [activeStepId, steps]);

  useEffect(() => {
    if (!playing || isLive) {
      return undefined;
    }
    const timer = window.setInterval(() => {
      setIndex((current) => {
        if (current >= steps.length - 1) {
          return current;
        }
        const next = current + 1;
        const step = steps[next];
        if (step) {
          onStepChangeRef.current?.(step.id);
        }
        return next;
      });
    }, STEP_MS);
    return () => window.clearInterval(timer);
  }, [playing, isLive, steps]);

  useEffect(() => {
    if (playing && (isLive || index >= steps.length - 1)) {
      setPlaying(false);
    }
  }, [playing, isLive, index, steps.length]);

  const layout = useMemo(() => layoutFlow(nodes, edges, width), [nodes, edges, width]);
  const lanes = useMemo(() => assignFlowLanes(edges), [edges]);
  const currentStep = steps[index];
  const liveStage = stages[stages.length - 1];
  const currentNodeId = isLive ? resolvedLive[resolvedLive.length - 1] : currentStep?.nodeId;
  const priorNodeId = isLive
    ? resolvedLive.length > 1
      ? resolvedLive[resolvedLive.length - 2]
      : undefined
    : index > 0
      ? steps[index - 1]?.nodeId
      : undefined;
  const activeEdgeId = currentNodeId ? findActiveEdgeId(edges, priorNodeId, currentNodeId) : undefined;

  function goTo(next: number): void {
    setPlaying(false);
    if (isLive || next < 0 || next >= steps.length) {
      return;
    }
    setIndex(next);
    const step = steps[next];
    if (step) {
      onStepChangeRef.current?.(step.id);
    }
  }

  function stepForward(): void {
    if (index >= steps.length - 1) {
      setPlaying(false);
      return;
    }
    goTo(index + 1);
  }

  function restart(): void {
    setPlaying(false);
    goTo(0);
  }

  function play(): void {
    if (isLive || steps.length < 2 || index >= steps.length - 1) {
      return;
    }
    setPlaying(true);
  }

  const liveCopy = liveStage ? formatStage(liveStage) : undefined;
  const railTitle = isLive ? liveCopy?.label || currentStep?.title : currentStep?.title;
  const railBody = isLive ? liveCopy?.detail || currentStep?.body : currentStep?.body;
  const railStep = isLive ? undefined : currentStep;

  return (
    <div className="flow-play">
      <div className="flow-toolbar" role="toolbar" aria-label="Flow playback">
        <button type="button" className="btn" disabled={isLive} aria-pressed={playing} onClick={play}>
          Play
        </button>
        <button type="button" className="btn" disabled={isLive || !playing} onClick={() => setPlaying(false)}>
          Pause
        </button>
        <button type="button" className="btn" disabled={isLive} onClick={stepForward}>
          Step
        </button>
        <button type="button" className="btn" disabled={isLive} onClick={restart}>
          Restart
        </button>
      </div>
      <div className="flow-canvas" ref={wrapRef}>
        <div className="flow-canvas-inner" style={{ width: layout.width, height: layout.height }}>
          <svg
            className="flow-edges"
            width={layout.width}
            height={layout.height}
            viewBox={`0 0 ${layout.width} ${layout.height}`}
            aria-hidden="false"
          >
            {edges.map((edge) => {
              const from = layout.boxes.get(edge.from);
              const to = layout.boxes.get(edge.to);
              if (!from || !to) {
                return null;
              }
              const detached = edge.attached === false;
              const active = !detached && edge.id === activeEdgeId;
              const title = detached ? `${edge.label || "edge"}: not attached` : edge.label;
              const lane = lanes.get(edge.id) ?? 0;
              const mid = labelPoint(from, to, lane);
              const labelW = estimateLabelWidth(edge.label || "");
              return (
                <g key={edge.id}>
                  <path
                    className={cx("flow-edge", detached && "not-attached", active && "active")}
                    d={orthogonalPath(from, to, lane)}
                    aria-label={detached ? `${edge.label || "edge"} not attached` : edge.label || undefined}
                  >
                    {title ? <title>{title}</title> : null}
                  </path>
                  {edge.label ? (
                    <g className="flow-edge-label-group" pointerEvents="none">
                      <rect
                        className="flow-edge-label-bg"
                        x={mid.x - labelW / 2}
                        y={mid.y - 8}
                        width={labelW}
                        height={16}
                        rx={3}
                      />
                      <text className="flow-edge-label" x={mid.x} y={mid.y} textAnchor="middle" dominantBaseline="middle">
                        {edge.label}
                      </text>
                    </g>
                  ) : null}
                </g>
              );
            })}
          </svg>
          {nodes.map((node) => {
            const box = layout.boxes.get(node.id);
            if (!box) {
              return null;
            }
            const status = isLive
              ? liveNodeStatus(node, resolvedLive, stages)
              : storyNodeStatus(node, steps, index);
            return (
              <button
                key={node.id}
                type="button"
                className={cx(
                  "flow-node",
                  "sys-node",
                  node.kind,
                  status === "active" && "active",
                  status === "done" && "done",
                  status === "blocked" && "blocked",
                  status === "not-attached" && "not-attached"
                )}
                style={{ left: box.x, top: box.y, width: box.w, height: box.h }}
                data-node-id={node.id}
                aria-label={nodeAriaLabel(node, status)}
                aria-current={status === "active" ? "step" : undefined}
                onClick={() => {
                  const next = steps.findIndex((step) => step.nodeId === node.id);
                  if (next >= 0) {
                    setPlaying(false);
                    goTo(next);
                  }
                }}
              >
                <span className="sys-node-icon">
                  <AgentIcon slug={node.id} size={18} />
                </span>
                <span className="sys-node-copy">
                  <span className="sys-node-name">{node.label}</span>
                </span>
              </button>
            );
          })}
        </div>
      </div>
      <div className="flow-rail" aria-live="polite">
        {railTitle ? <h3>{railTitle}</h3> : <h3 className="muted">Select a step</h3>}
        {railBody ? <p className="flow-rail-body">{railBody}</p> : null}
        {railStep?.manipulations?.length ? (
          <div className="flow-chips">
            {railStep.manipulations.map((item) => (
              <span className="flow-chip" key={item}>
                {item}
              </span>
            ))}
          </div>
        ) : null}
        {railStep?.handoff ? (
          <p className="flow-handoff">
            Handle to {railStep.handoff.to}: {railStep.handoff.why}
          </p>
        ) : null}
        {railStep?.artifactIds?.length ? (
          <div className="flow-artifacts">
            {railStep.artifactIds.map((id) => (
              <span className="mono" key={id}>
                {id}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

import { OFFICE_GRAPH_NODES, type OfficeGraphEdge, type OfficeGraphNode } from "./officeGraph";

export const FLOW_NODE_W = 172;
export const FLOW_NODE_H = 62;
export const FLOW_COL_GAP = 96;
export const FLOW_ROW_GAP = 44;
export const FLOW_PAD_X = 18;
export const FLOW_PAD_TOP = 34;
export const FLOW_PAD_BOTTOM = 48;
export const FLOW_PAD_RIGHT = 52;

export interface FlowBox {
  readonly id: string;
  readonly column: number;
  readonly row: number;
  readonly x: number;
  readonly y: number;
  readonly w: number;
  readonly h: number;
}

export interface OfficeLayout {
  readonly width: number;
  readonly height: number;
  readonly maxRow: number;
  readonly boxes: ReadonlyMap<string, FlowBox>;
}

export interface RoutedEdge {
  readonly id: string;
  readonly d: string;
  readonly labelX: number;
  readonly labelY: number;
  readonly attached: boolean;
}

export interface LabelAnchor {
  readonly id: string;
  readonly text: string;
  readonly x: number;
  readonly y: number;
}

interface RouteSketch {
  readonly d: string;
  readonly labelX: number;
  readonly labelY: number;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

export function layoutOfficeNodes(nodes: readonly OfficeGraphNode[] = OFFICE_GRAPH_NODES): OfficeLayout {
  let maxCol = 0;
  let maxRow = 0;
  for (const node of nodes) {
    maxCol = Math.max(maxCol, node.column);
    maxRow = Math.max(maxRow, node.row);
  }
  const width =
    FLOW_PAD_X + (maxCol + 1) * FLOW_NODE_W + maxCol * FLOW_COL_GAP + FLOW_PAD_RIGHT;
  const height =
    FLOW_PAD_TOP + (maxRow + 1) * FLOW_NODE_H + maxRow * FLOW_ROW_GAP + FLOW_PAD_BOTTOM;
  const boxes = new Map<string, FlowBox>();
  for (const node of nodes) {
    boxes.set(node.id, {
      id: node.id,
      column: node.column,
      row: node.row,
      x: FLOW_PAD_X + node.column * (FLOW_NODE_W + FLOW_COL_GAP),
      y: FLOW_PAD_TOP + node.row * (FLOW_NODE_H + FLOW_ROW_GAP),
      w: FLOW_NODE_W,
      h: FLOW_NODE_H,
    });
  }
  return { width, height, maxRow, boxes };
}

export function gutterY(gutter: number, maxRow: number): number {
  if (gutter <= 0) {
    return round(FLOW_PAD_TOP * 0.42);
  }
  if (gutter > maxRow) {
    const lastBottom = FLOW_PAD_TOP + (maxRow + 1) * FLOW_NODE_H + maxRow * FLOW_ROW_GAP;
    return round(lastBottom + FLOW_PAD_BOTTOM * 0.42);
  }
  return round(FLOW_PAD_TOP + gutter * FLOW_NODE_H + (gutter - 1) * FLOW_ROW_GAP + FLOW_ROW_GAP / 2);
}

function preferredGutter(from: FlowBox, to: FlowBox): number {
  if (from.row === to.row) {
    return from.row + 1;
  }
  if (from.row < to.row) {
    return from.row + 1;
  }
  return from.row;
}

function routeKey(from: FlowBox, to: FlowBox): string {
  const colDelta = to.column - from.column;
  if (colDelta === 0) {
    return `col-${from.column}`;
  }
  if (colDelta === 1 && from.row === to.row) {
    return `fwd-row-${from.column}-${from.row}`;
  }
  if (colDelta === 1) {
    return `fwd-adj-${from.column}`;
  }
  if (colDelta === -1 && from.row === to.row) {
    return `back-row-${to.column}-${from.row}`;
  }
  if (colDelta === -1) {
    return `back-adj-${to.column}`;
  }
  if (colDelta > 1) {
    return `skip-${from.column}-${to.column}-g${preferredGutter(from, to)}`;
  }
  return `far-back-${to.column}`;
}

export function assignLanes(
  edges: readonly OfficeGraphEdge[],
  boxes: ReadonlyMap<string, FlowBox>
): ReadonlyMap<string, number> {
  const groups = new Map<string, string[]>();
  for (const edge of edges) {
    const from = boxes.get(edge.from);
    const to = boxes.get(edge.to);
    if (!from || !to) {
      continue;
    }
    const key = routeKey(from, to);
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

function onNodeY(box: FlowBox, raw: number): number {
  return round(clamp(raw, box.y + 14, box.y + box.h - 14));
}

function sketchRoute(from: FlowBox, to: FlowBox, lane: number, maxRow: number, height: number): RouteSketch {
  const colDelta = to.column - from.column;
  const fromRight = from.x + from.w;
  const fromLeft = from.x;
  const fromCy = from.y + from.h / 2;
  const fromCx = from.x + from.w / 2;
  const fromBottom = from.y + from.h;
  const toLeft = to.x;
  const toRight = to.x + to.w;
  const toCy = to.y + to.h / 2;
  const toCx = to.x + to.w / 2;
  const toBottom = to.y + to.h;

  if (colDelta === 0) {
    const stubX = round(fromRight + 16 + lane * 14);
    const d = `M ${round(fromRight)} ${round(fromCy)} H ${stubX} V ${round(toCy)} H ${round(toRight)}`;
    return { d, labelX: stubX + 8, labelY: round((fromCy + toCy) / 2) };
  }

  if (colDelta === 1 && from.row === to.row) {
    const y = onNodeY(from, fromCy + lane * 9);
    const midX = round((fromRight + toLeft) / 2);
    const d = `M ${round(fromRight)} ${y} H ${round(toLeft)}`;
    return { d, labelX: midX, labelY: y - 12 };
  }

  if (colDelta === 1) {
    const channelX = round(fromRight + 20 + lane * 16);
    const d = `M ${round(fromRight)} ${round(fromCy)} H ${channelX} V ${round(toCy)} H ${round(toLeft)}`;
    return { d, labelX: channelX + 10, labelY: round((fromCy + toCy) / 2) };
  }

  if (colDelta === -1 && from.row === to.row) {
    const y = onNodeY(from, fromCy + 11 + lane * 8);
    const midX = round((fromLeft + toRight) / 2);
    const d = `M ${round(fromLeft)} ${y} H ${round(toRight)}`;
    return { d, labelX: midX, labelY: y - 12 };
  }

  if (colDelta === -1) {
    const channelX = round(toRight + 20 + lane * 16);
    const d = `M ${round(fromLeft)} ${round(fromCy)} H ${channelX} V ${round(toCy)} H ${round(toRight)}`;
    return { d, labelX: channelX + 10, labelY: round((fromCy + toCy) / 2) };
  }

  if (colDelta > 1) {
    const gutter = (preferredGutter(from, to) + lane) % (maxRow + 2);
    const gy = round(gutterY(gutter, maxRow));
    const outX = round(fromRight + 12 + lane * 6);
    const inX = round(toLeft - 12 - lane * 6);
    const d = `M ${round(fromRight)} ${round(fromCy)} H ${outX} V ${gy} H ${inX} V ${round(toCy)} H ${round(toLeft)}`;
    const labelY = gy < FLOW_PAD_TOP ? gy + 11 : gy - 12;
    return { d, labelX: round(outX + 30 + lane * 10), labelY };
  }

  const hwy = round(height - 16 - lane * 12);
  const d = `M ${round(fromCx)} ${round(fromBottom)} V ${hwy} H ${round(toCx)} V ${round(toBottom)}`;
  return { d, labelX: round((fromCx + toCx) / 2), labelY: hwy - 12 };
}

export function routeOfficeEdges(
  edges: readonly OfficeGraphEdge[],
  layout: OfficeLayout
): readonly RoutedEdge[] {
  const lanes = assignLanes(edges, layout.boxes);
  return edges.flatMap((edge) => {
    const from = layout.boxes.get(edge.from);
    const to = layout.boxes.get(edge.to);
    if (!from || !to) {
      return [];
    }
    const sketch = sketchRoute(from, to, lanes.get(edge.id) ?? 0, layout.maxRow, layout.height);
    return [
      {
        id: edge.id,
        d: sketch.d,
        labelX: sketch.labelX,
        labelY: sketch.labelY,
        attached: edge.attached,
      },
    ];
  });
}

export function labelWidth(text: string): number {
  return Math.max(28, text.length * 6.35 + 12);
}

export function labelsOverlap(
  left: Pick<LabelAnchor, "x" | "y" | "text">,
  right: Pick<LabelAnchor, "x" | "y" | "text">
): boolean {
  const leftW = labelWidth(left.text);
  const rightW = labelWidth(right.text);
  const dx = Math.abs(left.x - right.x);
  const dy = Math.abs(left.y - right.y);
  return dx < (leftW + rightW) / 2 - 4 && dy < 13;
}

function overlapsNode(x: number, y: number, text: string, nodes: readonly FlowBox[]): boolean {
  const width = labelWidth(text);
  const left = x - width / 2;
  const right = x + width / 2;
  const top = y - 11;
  const bottom = y + 3;
  return nodes.some((box) => left < box.x + box.w && right > box.x && top < box.y + box.h && bottom > box.y);
}

export function nudgeLabels(labels: readonly LabelAnchor[], nodes: readonly FlowBox[]): LabelAnchor[] {
  const placed: LabelAnchor[] = [];
  for (const label of labels) {
    let x = label.x;
    let y = label.y;
    let guard = 0;
    let step = -14;
    while (
      guard < 12 &&
      (placed.some((item) => labelsOverlap({ ...label, x, y }, item)) || overlapsNode(x, y, label.text, nodes))
    ) {
      y += step;
    if (y < 12) {
        step = 14;
        y = Math.max(label.y, FLOW_PAD_TOP - 8) + 14;
        x = label.x + (guard % 2 === 0 ? 18 : -18);
      }
      guard += 1;
    }
    placed.push({ ...label, x: round(x), y: round(y) });
  }
  return placed;
}

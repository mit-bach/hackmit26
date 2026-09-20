import { AGENTS_BY_SLUG, GRAIN_SLUGS, ROOMS, type AgentSlug, type RoomId } from "./agents";
import { HANDOFFS, PRINCIPAL_FLOWS } from "./handoffs";

export const WORLD_NODE_ID = "world";

export const WORLD_GRAPH_LABEL = "World (not on live roster)";

export interface WorldInspectorCopy {
  readonly name: string;
  readonly title: string;
  readonly room: string;
  readonly body: string;
}

export const WORLD_INSPECTOR: WorldInspectorCopy = {
  name: "World",
  title: "not on live roster",
  room: "Beside incoming records",
  body: "Simulated mailbox, not bound to the live Computer roster. send_office_outbound is not on the live catalog.",
};

export type OfficeNodeKind = "source" | "operator" | "verifier" | "assurance";

export interface OfficeGraphNode {
  readonly id: string;
  readonly label: string;
  readonly kind: OfficeNodeKind;
  readonly room?: RoomId;
  readonly column: number;
  readonly row: number;
  readonly status?: "not-attached";
}

export interface OfficeGraphEdge {
  readonly id: string;
  readonly from: string;
  readonly to: string;
  readonly when: string;
  readonly why: string;
  readonly attached: boolean;
}

export interface OfficeRoomBand {
  readonly id: string;
  readonly label: string;
}

const ROOM_COLUMN: Record<RoomId, number> = {
  intake: 1,
  pay: 2,
  cash: 3,
  "books-close": 4,
};

export const OFFICE_ROOM_BANDS: readonly OfficeRoomBand[] = [
  { id: WORLD_NODE_ID, label: "World" },
  ...ROOMS.map((room) => ({ id: room.id, label: room.title })),
];

function kindForSlug(slug: AgentSlug): OfficeNodeKind {
  if (slug.startsWith("ctl-")) {
    return "verifier";
  }
  if (slug === "audit") {
    return "assurance";
  }
  if (slug === "email" || slug === "stripe" || slug === "bank" || slug === "books") {
    return "source";
  }
  return "operator";
}

function graphLabel(name: string): string {
  return name.replace(/ Agent$/, "");
}

function buildGrainNodes(): OfficeGraphNode[] {
  const rowAt: Record<RoomId, number> = {
    intake: 0,
    pay: 0,
    cash: 0,
    "books-close": 0,
  };
  return GRAIN_SLUGS.map((slug) => {
    const agent = AGENTS_BY_SLUG[slug];
    const row = rowAt[agent.room];
    rowAt[agent.room] = row + 1;
    return {
      id: slug,
      label: graphLabel(agent.name),
      kind: kindForSlug(slug),
      room: agent.room,
      column: ROOM_COLUMN[agent.room],
      row,
    };
  });
}

const WORLD_NODE: OfficeGraphNode = {
  id: WORLD_NODE_ID,
  label: WORLD_GRAPH_LABEL,
  kind: "source",
  column: 0,
  row: 0,
  status: "not-attached",
};

const WORLD_EDGES: readonly OfficeGraphEdge[] = [
  {
    id: "collect-dun-world",
    from: "collect",
    to: WORLD_NODE_ID,
    when: "dun",
    why: "Collections would send a follow-up into the outside mailbox. That hop is not attached on the live roster.",
    attached: false,
  },
  {
    id: "email-missing-info-world",
    from: "email",
    to: WORLD_NODE_ID,
    when: "missing-info",
    why: "Missing-info outbound would leave through World. send_office_outbound is not on the live catalog.",
    attached: false,
  },
  {
    id: "world-inbound-email",
    from: WORLD_NODE_ID,
    to: "email",
    when: "inbound",
    why: "Delivered inbound mail is simulated. World is not bound as a live Bot.",
    attached: false,
  },
];

const HANDOFF_EDGES: readonly OfficeGraphEdge[] = HANDOFFS.map((edge) => ({
  id: `${edge.from}-${edge.when}-${edge.to}`,
  from: edge.from,
  to: edge.to,
  when: edge.when,
  why: edge.why,
  attached: true,
}));

export const OFFICE_GRAPH_NODES: readonly OfficeGraphNode[] = [WORLD_NODE, ...buildGrainNodes()];

export const OFFICE_GRAPH_EDGES: readonly OfficeGraphEdge[] = [...HANDOFF_EDGES, ...WORLD_EDGES];

export function isGrainId(id: string): boolean {
  return (GRAIN_SLUGS as readonly string[]).includes(id);
}

export function roomOf(id: string): RoomId | undefined {
  if (id === WORLD_NODE_ID) {
    return undefined;
  }
  return AGENTS_BY_SLUG[id as AgentSlug]?.room;
}

export function isPrincipalHandle(edge: Pick<OfficeGraphEdge, "from" | "to">): boolean {
  const fromRoom = roomOf(edge.from);
  const toRoom = roomOf(edge.to);
  if (!fromRoom || !toRoom) {
    return false;
  }
  return PRINCIPAL_FLOWS.some((flow) => flow.from === fromRoom && flow.to === toRoom);
}

export function isIncidentHandle(edge: Pick<OfficeGraphEdge, "from" | "to">, selected: string | null): boolean {
  if (!selected) {
    return false;
  }
  return edge.from === selected || edge.to === selected;
}

export function outboundHandles(id: string): OfficeGraphEdge[] {
  return OFFICE_GRAPH_EDGES.filter((edge) => edge.from === id);
}

export function edgeWeight(edge: OfficeGraphEdge, selected: string | null, showAll: boolean): number {
  if (selected) {
    return isIncidentHandle(edge, selected) ? 1 : 0.12;
  }
  if (showAll || isPrincipalHandle(edge)) {
    return 1;
  }
  return 0.22;
}

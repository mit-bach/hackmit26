export interface ProtocolEvent {
  readonly t: string;
  readonly seq: number;
  readonly type: string;
  readonly from?: string;
  readonly to?: string;
  readonly handleId?: string;
  readonly slug?: string;
  readonly text?: string;
  readonly status?: string;
}

export interface TranscriptEntry {
  readonly seq: number;
  readonly t: string;
  readonly kind: string;
  readonly text: string;
  readonly handleId?: string;
  readonly from?: string;
  readonly to?: string;
}

export const DEMO_COLORS = [
  "teal",
  "blue",
  "purple",
  "pink",
  "orange",
  "cyan",
  "green",
  "coral",
  "yellow",
  "red",
] as const;

export type DemoColor = (typeof DEMO_COLORS)[number];

export type DemoPaneStatus = "queued" | "running";

export type DemoSource = "live" | "recording";

export interface MosaicCell {
  readonly index: number;
  readonly left: number;
  readonly top: number;
  readonly width: number;
  readonly height: number;
}

export interface DemoBotWire {
  readonly id: string;
  readonly slug: string;
  readonly name: string;
  readonly purpose: string;
  readonly color: DemoColor;
}

export interface DemoActivity {
  readonly t: string;
  readonly type: string;
  readonly title: string;
}

export interface DemoOpenTurn {
  readonly botId: string;
  readonly slug: string;
  readonly name: string;
  readonly purpose: string;
  readonly color: DemoColor;
  readonly status: DemoPaneStatus;
  readonly handleId?: string;
  readonly prompt?: string;
  readonly startedSeq: number;
}

export interface DemoAwakeBot extends DemoOpenTurn {
  readonly activity: string;
  readonly messages: readonly TranscriptEntry[];
  readonly held: boolean;
}

export interface DemoFrame {
  readonly seq: number;
  readonly t: string;
  readonly type: string;
  readonly text: string;
  readonly from?: string;
  readonly to?: string;
  readonly slug?: string;
  readonly awake: readonly DemoAwakeBot[];
  readonly layout: readonly MosaicCell[];
  readonly overflow: number;
  readonly overflowSlugs: readonly string[];
}

export interface DemoDirector {
  readonly maxPanes: number;
  readonly featured: readonly string[];
  readonly seqFrom: number;
  readonly seqTo: number;
}

export interface DemoScene {
  readonly id: string;
  readonly title: string;
  readonly seqFrom: number;
  readonly seqTo: number;
  readonly featured: readonly string[];
  readonly maxPanes: number;
}

export interface DemoBundle {
  readonly source: DemoSource;
  readonly recordedAt?: string;
  readonly lastSeq: number;
  readonly bots: readonly DemoBotWire[];
  readonly events: readonly ProtocolEvent[];
  readonly transcripts: Readonly<Record<string, readonly TranscriptEntry[]>>;
  readonly activities: Readonly<Record<string, readonly DemoActivity[]>>;
  readonly scenes?: readonly DemoScene[];
}

const MIN_PLAY_MS = 80;
const MAX_PLAY_MS = 900;
export const MOSAIC_MESSAGE_CAP = 8;
export const HERO_MESSAGE_CAP = 40;
export const PANE_CAPS = [1, 2, 4, 6, 9, 16] as const;

export const DEFAULT_DEMO_DIRECTOR: DemoDirector = {
  maxPanes: 16,
  featured: [],
  seqFrom: 0,
  seqTo: 0,
};

export const CAMERA_DEMO_DIRECTOR: DemoDirector = {
  maxPanes: 6,
  featured: [],
  seqFrom: 0,
  seqTo: 0,
};

function cell(index: number, left: number, top: number, width: number, height: number): MosaicCell {
  return { index, left, top, width, height };
}

function grid(count: number, cols: number): MosaicCell[] {
  const rows = Math.max(1, Math.ceil(count / cols));
  const width = 100 / cols;
  const height = 100 / rows;
  const cells: MosaicCell[] = [];
  for (let i = 0; i < count; i += 1) {
    const col = i % cols;
    const row = Math.floor(i / cols);
    cells.push(cell(i, col * width, row * height, width, height));
  }
  return cells;
}

export function mosaicLayout(count: number): readonly MosaicCell[] {
  if (count <= 0) {
    return [];
  }
  if (count === 1) {
    return [cell(0, 0, 0, 100, 100)];
  }
  if (count === 2) {
    return [cell(0, 0, 0, 50, 100), cell(1, 50, 0, 50, 100)];
  }
  if (count === 3) {
    return [cell(0, 0, 0, 50, 100), cell(1, 50, 0, 50, 50), cell(2, 50, 50, 50, 50)];
  }
  if (count === 4) {
    return [
      cell(0, 0, 0, 50, 50),
      cell(1, 50, 0, 50, 50),
      cell(2, 0, 50, 50, 50),
      cell(3, 50, 50, 50, 50),
    ];
  }
  if (count === 5) {
    const third = 100 / 3;
    return [
      cell(0, 0, 0, 50, 50),
      cell(1, 50, 0, 50, 50),
      cell(2, 0, 50, third, 50),
      cell(3, third, 50, third, 50),
      cell(4, third * 2, 50, third, 50),
    ];
  }
  if (count === 6) {
    return grid(6, 3);
  }
  if (count === 8) {
    return grid(8, 4);
  }
  if (count === 9) {
    return grid(9, 3);
  }
  if (count === 10) {
    return grid(10, 4);
  }
  if (count === 12) {
    return grid(12, 4);
  }
  if (count === 16) {
    return grid(16, 4);
  }
  return grid(count, Math.ceil(Math.sqrt(count)));
}

function finiteNumber(value: number, fallback: number): number {
  return Number.isFinite(value) ? value : fallback;
}

function clampNumber(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export function clampDirector(raw: Partial<DemoDirector> | undefined): DemoDirector {
  const base = DEFAULT_DEMO_DIRECTOR;
  if (!raw) {
    return base;
  }
  const featured = (raw.featured ?? [])
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
  return {
    maxPanes: clampNumber(Math.round(finiteNumber(raw.maxPanes ?? base.maxPanes, base.maxPanes)), 1, 16),
    featured,
    seqFrom: Math.max(0, Math.trunc(finiteNumber(raw.seqFrom ?? 0, 0))),
    seqTo: Math.max(0, Math.trunc(finiteNumber(raw.seqTo ?? 0, 0))),
  };
}

function turnFeatured(turn: DemoOpenTurn, featuredKeys: ReadonlySet<string>): boolean {
  return (
    featuredKeys.has(turn.slug.toLowerCase()) ||
    featuredKeys.has(turn.botId.toLowerCase()) ||
    featuredKeys.has(turn.name.toLowerCase())
  );
}

export function selectCast(
  turns: readonly DemoOpenTurn[],
  director: Pick<DemoDirector, "maxPanes" | "featured">,
): { visible: readonly DemoOpenTurn[]; overflow: readonly DemoOpenTurn[] } {
  const cap = clampNumber(Math.trunc(director.maxPanes), 1, 16);
  if (turns.length <= cap) {
    return { visible: turns, overflow: [] };
  }
  const featuredKeys = new Set(
    director.featured.map((item) => item.trim().toLowerCase()).filter((item) => item.length > 0),
  );
  const featured: DemoOpenTurn[] = [];
  const rest: DemoOpenTurn[] = [];
  for (const turn of turns) {
    if (turnFeatured(turn, featuredKeys)) {
      featured.push(turn);
    } else {
      rest.push(turn);
    }
  }
  const combined = [...featured, ...rest];
  return { visible: combined.slice(0, cap), overflow: combined.slice(cap) };
}

export function capPaneMessages(rows: readonly TranscriptEntry[], cap: number): readonly TranscriptEntry[] {
  if (cap <= 0 || rows.length <= cap) {
    return rows;
  }
  return rows.slice(rows.length - cap);
}

function resolveBot(bots: readonly DemoBotWire[], event: ProtocolEvent): DemoBotWire | undefined {
  if (event.to) {
    const byId = bots.find((bot) => bot.id === event.to);
    if (byId) {
      return byId;
    }
    const bySlug = bots.find((bot) => bot.slug === event.to);
    if (bySlug) {
      return bySlug;
    }
  }
  if (event.slug) {
    return bots.find((bot) => bot.slug === event.slug);
  }
  return undefined;
}

function snapshotOpen(open: Map<string, DemoOpenTurn>): DemoOpenTurn[] {
  return [...open.values()].sort((left, right) => right.startedSeq - left.startedSeq);
}

function applyAwakeEvent(open: Map<string, DemoOpenTurn>, bots: readonly DemoBotWire[], event: ProtocolEvent): void {
  const bot = resolveBot(bots, event);
  if (!bot) {
    return;
  }
  if (event.type === "send.accepted") {
    open.set(bot.id, {
      botId: bot.id,
      slug: bot.slug,
      name: bot.name,
      purpose: bot.purpose,
      color: bot.color,
      status: "queued",
      handleId: event.handleId,
      prompt: event.text,
      startedSeq: event.seq,
    });
    return;
  }
  if (event.type === "turn.start") {
    const previous = open.get(bot.id);
    open.set(bot.id, {
      botId: bot.id,
      slug: bot.slug,
      name: bot.name,
      purpose: bot.purpose,
      color: bot.color,
      status: "running",
      handleId: event.handleId ?? previous?.handleId,
      prompt: event.text ?? previous?.prompt,
      startedSeq: event.seq,
    });
    return;
  }
  if (event.type === "turn.end") {
    const previous = open.get(bot.id);
    if (!previous) {
      return;
    }
    if (!event.handleId || !previous.handleId || event.handleId === previous.handleId) {
      open.delete(bot.id);
    }
  }
}

export function foldAwake(bots: readonly DemoBotWire[], events: readonly ProtocolEvent[]): DemoOpenTurn[] {
  const open = new Map<string, DemoOpenTurn>();
  for (const event of events) {
    applyAwakeEvent(open, bots, event);
  }
  return snapshotOpen(open);
}

export function firstAwakeSeq(events: readonly ProtocolEvent[]): number {
  for (const event of events) {
    if (event.type === "send.accepted" || event.type === "turn.start") {
      return event.seq;
    }
  }
  return 0;
}

export interface DemoStageFold {
  readonly live: readonly DemoOpenTurn[];
  readonly held: readonly DemoOpenTurn[];
  readonly stage: readonly DemoOpenTurn[];
  readonly holding: boolean;
}

export function foldAwakeStage(bots: readonly DemoBotWire[], events: readonly ProtocolEvent[]): DemoStageFold {
  const open = new Map<string, DemoOpenTurn>();
  let held: DemoOpenTurn[] = [];
  for (const event of events) {
    applyAwakeEvent(open, bots, event);
    const live = snapshotOpen(open);
    if (live.length > 0) {
      held = live;
    }
  }
  const live = snapshotOpen(open);
  const holding = live.length === 0 && held.length > 0;
  return { live, held, stage: holding ? held : live, holding };
}

export function activityAt(rows: readonly DemoActivity[], iso: string): DemoActivity | undefined {
  if (rows.length === 0) {
    return undefined;
  }
  const cursor = Date.parse(iso);
  if (!Number.isFinite(cursor)) {
    return rows[rows.length - 1];
  }
  let last: DemoActivity | undefined;
  for (const row of rows) {
    const at = Date.parse(row.t);
    if (!Number.isFinite(at) || at <= cursor) {
      last = row;
    }
  }
  return last;
}

export function activityLabel(status: DemoPaneStatus, activity?: DemoActivity): string {
  if (activity?.title && /memory_/.test(activity.title)) {
    return activity.title;
  }
  if (activity?.type === "item.started" && activity.title.length > 0) {
    return activity.title;
  }
  if (activity?.type === "turn.started") {
    return "Running";
  }
  if (status === "queued") {
    return "Queued";
  }
  return "Running";
}

function paintFrame(
  bundle: DemoBundle,
  seq: number,
  turns: readonly DemoOpenTurn[],
  holding: boolean,
  director: DemoDirector,
): DemoFrame {
  const visibleEvents = bundle.events.filter((event) => event.seq <= seq);
  const current = visibleEvents[visibleEvents.length - 1];
  const cast = selectCast(turns, director);
  const layout = mosaicLayout(cast.visible.length);
  const messageCap = cast.visible.length <= 1 ? HERO_MESSAGE_CAP : MOSAIC_MESSAGE_CAP;
  const awake: DemoAwakeBot[] = cast.visible.map((turn) => {
    const messages = capPaneMessages(
      (bundle.transcripts[turn.botId] ?? []).filter((row) => row.seq <= seq),
      messageCap,
    );
    const lastActivity = activityAt(bundle.activities[turn.botId] ?? [], current?.t ?? "");
    return {
      ...turn,
      status: holding ? "queued" : turn.status,
      activity: holding ? "Idle" : activityLabel(turn.status, lastActivity),
      messages,
      held: holding,
    };
  });
  return {
    seq,
    t: current?.t ?? "",
    type: current?.type ?? "wipe",
    text: current?.text ?? "",
    from: current?.from,
    to: current?.to,
    slug: current?.slug,
    awake,
    layout,
    overflow: cast.overflow.length,
    overflowSlugs: cast.overflow.map((turn) => turn.slug),
  };
}

export function projectFrame(
  bundle: DemoBundle,
  cursorSeq: number,
  director: DemoDirector = DEFAULT_DEMO_DIRECTOR,
): DemoFrame {
  const lastSeq = bundle.lastSeq;
  const seq = Math.max(0, Math.min(cursorSeq, lastSeq));
  const visible = bundle.events.filter((event) => event.seq <= seq);
  const open = foldAwake(bundle.bots, visible);
  return paintFrame(bundle, seq, open, false, clampDirector(director));
}

export function projectStageFrame(
  bundle: DemoBundle,
  cursorSeq: number,
  director: DemoDirector = DEFAULT_DEMO_DIRECTOR,
): DemoFrame {
  const origin = firstAwakeSeq(bundle.events);
  const camera = clampDirector(director);
  if (origin <= 0 || bundle.lastSeq <= 0) {
    return projectFrame(bundle, cursorSeq, camera);
  }
  const seq = Math.max(origin, Math.min(cursorSeq, bundle.lastSeq));
  const visible = bundle.events.filter((event) => event.seq <= seq);
  const folded = foldAwakeStage(bundle.bots, visible);
  return paintFrame(bundle, seq, folded.stage, folded.holding, camera);
}

export function playDelayMs(
  previous: ProtocolEvent | undefined,
  next: ProtocolEvent,
  speed: number,
): number {
  const scale = speed > 0 ? speed : 1;
  if (!previous) {
    return Math.round(200 / scale);
  }
  const dt = Date.parse(next.t) - Date.parse(previous.t);
  const clamped = Number.isFinite(dt) ? Math.min(MAX_PLAY_MS, Math.max(MIN_PLAY_MS, dt)) : 200;
  return Math.max(16, Math.round(clamped / scale));
}

export function nextEventSeq(events: readonly ProtocolEvent[], seq: number): number | undefined {
  return events.find((event) => event.seq > seq)?.seq;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function asNumber(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function parseEvent(value: unknown): ProtocolEvent | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const seq = asNumber(value.seq);
  const type = asString(value.type);
  const t = asString(value.t);
  if (seq === undefined || type === undefined || t === undefined) {
    return undefined;
  }
  return {
    t,
    seq,
    type,
    from: asString(value.from),
    to: asString(value.to),
    handleId: asString(value.handleId),
    slug: asString(value.slug),
    text: asString(value.text),
    status: asString(value.status),
  };
}

function parseTranscript(value: unknown): TranscriptEntry | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const seq = asNumber(value.seq);
  const t = asString(value.t);
  const kind = asString(value.kind);
  if (seq === undefined || t === undefined || kind === undefined) {
    return undefined;
  }
  return {
    seq,
    t,
    kind,
    text: asString(value.text) ?? "",
    handleId: asString(value.handleId),
    from: asString(value.from),
    to: asString(value.to),
  };
}

function parseActivityRow(value: unknown): DemoActivity | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const t = asString(value.t);
  const type = asString(value.type);
  const title = asString(value.title);
  if (!t || !type || title === undefined) {
    return undefined;
  }
  return { t, type, title };
}

function parseBot(value: unknown): DemoBotWire | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const id = asString(value.id);
  const slug = asString(value.slug);
  const name = asString(value.name);
  const purpose = asString(value.purpose);
  const colorRaw = asString(value.color);
  if (!id || !slug || !name || purpose === undefined) {
    return undefined;
  }
  const color: DemoColor = DEMO_COLORS.includes(colorRaw as DemoColor)
    ? (colorRaw as DemoColor)
    : "teal";
  return { id, slug, name, purpose, color };
}

function parseKeyed<T>(value: unknown, parse: (row: unknown) => T | undefined): Record<string, T[]> {
  if (!isRecord(value)) {
    return {};
  }
  const out: Record<string, T[]> = {};
  for (const [key, rows] of Object.entries(value)) {
    if (!Array.isArray(rows)) {
      continue;
    }
    out[key] = rows.map(parse).filter((row): row is T => row !== undefined);
  }
  return out;
}

function parseScene(raw: unknown): DemoScene | undefined {
  if (!isRecord(raw)) {
    return undefined;
  }
  const id = asString(raw.id);
  const title = asString(raw.title);
  if (!id || !title) {
    return undefined;
  }
  const director = clampDirector({
    maxPanes: asNumber(raw.maxPanes) ?? CAMERA_DEMO_DIRECTOR.maxPanes,
    featured: Array.isArray(raw.featured) ? raw.featured.filter((item): item is string => typeof item === "string") : [],
    seqFrom: asNumber(raw.seqFrom) ?? 0,
    seqTo: asNumber(raw.seqTo) ?? 0,
  });
  return {
    id,
    title,
    seqFrom: director.seqFrom,
    seqTo: director.seqTo,
    featured: director.featured,
    maxPanes: director.maxPanes,
  };
}

export function parseDemoScenes(value: unknown): DemoScene[] {
  if (Array.isArray(value)) {
    return value.map(parseScene).filter((row): row is DemoScene => row !== undefined);
  }
  if (isRecord(value) && Array.isArray(value.scenes)) {
    return value.scenes.map(parseScene).filter((row): row is DemoScene => row !== undefined);
  }
  return [];
}

export function parseDemoBundle(value: unknown): DemoBundle | undefined {
  if (!isRecord(value) || !Array.isArray(value.events) || !Array.isArray(value.bots)) {
    return undefined;
  }
  const source = value.source === "recording" ? "recording" : "live";
  const lastSeq = asNumber(value.lastSeq) ?? 0;
  const bots = value.bots.map(parseBot).filter((bot): bot is DemoBotWire => bot !== undefined);
  const events = value.events.map(parseEvent).filter((row): row is ProtocolEvent => row !== undefined);
  return {
    source,
    recordedAt: asString(value.recordedAt),
    lastSeq,
    bots,
    events,
    transcripts: parseKeyed(value.transcripts, parseTranscript),
    activities: parseKeyed(value.activities, parseActivityRow),
    scenes: parseDemoScenes(value.scenes),
  };
}

export interface DemoMetaWire {
  readonly source: DemoSource;
  readonly recordedAt?: string;
  readonly lastSeq: number;
  readonly eventCount: number;
  readonly bots: number;
  readonly hasRecording: boolean;
  readonly hasLive: boolean;
}

export function parseDemoMeta(value: unknown): DemoMetaWire | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const lastSeq = asNumber(value.lastSeq);
  const eventCount = asNumber(value.eventCount);
  const bots = asNumber(value.bots);
  if (lastSeq === undefined || eventCount === undefined || bots === undefined) {
    return undefined;
  }
  return {
    source: value.source === "recording" ? "recording" : "live",
    recordedAt: asString(value.recordedAt),
    lastSeq,
    eventCount,
    bots,
    hasRecording: value.hasRecording === true,
    hasLive: value.hasLive === true,
  };
}

const DIRECTOR_STORAGE_KEY = "harness-demo-director-v1";

export function loadDirectorSettings(): DemoDirector {
  if (typeof localStorage === "undefined") {
    return CAMERA_DEMO_DIRECTOR;
  }
  const raw = localStorage.getItem(DIRECTOR_STORAGE_KEY);
  if (!raw) {
    return CAMERA_DEMO_DIRECTOR;
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return CAMERA_DEMO_DIRECTOR;
    }
    return clampDirector({ ...CAMERA_DEMO_DIRECTOR, ...(parsed as Partial<DemoDirector>) });
  } catch (cause) {
    if (cause instanceof SyntaxError) {
      return CAMERA_DEMO_DIRECTOR;
    }
    throw cause;
  }
}

export function saveDirectorSettings(director: DemoDirector): void {
  if (typeof localStorage === "undefined") {
    return;
  }
  localStorage.setItem(DIRECTOR_STORAGE_KEY, JSON.stringify(clampDirector(director)));
}

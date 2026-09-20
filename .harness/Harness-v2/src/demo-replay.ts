import { copyFileSync, existsSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

import { ensureDir, readJsonIfExists, readJsonl, writeJsonAtomic } from "./fs.ts";
import { nowIso } from "./ids.ts";
import {
  demoLatestDir,
  piRuntimePath,
  protocolLogPath,
  transcriptPath,
} from "./paths.ts";
import { parseProtocolEvent } from "./protocol-log.ts";
import { loadRoster } from "./roster.ts";
import { parseTranscriptEntry } from "./transcript.ts";
import type { ProtocolEvent, TranscriptEntry } from "./types.ts";

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

export type DemoSourceQuery = DemoSource | "auto";

export function parseDemoSourceQuery(value: string | null): DemoSourceQuery {
  if (value === "live" || value === "recording" || value === "auto") {
    return value;
  }
  return "auto";
}

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
}

export interface DemoBundle {
  readonly source: DemoSource;
  readonly recordedAt?: string;
  readonly lastSeq: number;
  readonly bots: readonly DemoBotWire[];
  readonly events: readonly ProtocolEvent[];
  readonly transcripts: Readonly<Record<string, readonly TranscriptEntry[]>>;
  readonly activities: Readonly<Record<string, readonly DemoActivity[]>>;
}

export interface DemoMeta {
  readonly source: DemoSource;
  readonly recordedAt?: string;
  readonly lastSeq: number;
  readonly eventCount: number;
  readonly bots: number;
  readonly hasRecording: boolean;
  readonly hasLive: boolean;
}

export interface DemoRecordReport {
  readonly recordedAt: string;
  readonly lastSeq: number;
  readonly eventCount: number;
  readonly bots: number;
  readonly path: string;
}

const KEEP_ACTIVITY = new Set(["turn.started", "turn.completed", "item.started", "item.completed"]);
const MIN_PLAY_MS = 80;
const MAX_PLAY_MS = 900;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

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

/**
 * Absolute mosaic for awake Bots. 1 = full chat. 2 = 50/50. 3 = half + two
 * stacked. 4 = quad. 5 = two then three. Else ceil(sqrt(n)) columns.
 */
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
  return grid(count, Math.ceil(Math.sqrt(count)));
}

export function colorForIndex(index: number): DemoColor {
  return DEMO_COLORS[index % DEMO_COLORS.length] ?? "teal";
}

export function botsFromRoster(computerRoot: string): DemoBotWire[] {
  const roster = loadRoster(computerRoot);
  return roster.bots.map((bot, index) => ({
    id: bot.id,
    slug: bot.slug,
    name: bot.name,
    purpose: bot.purpose,
    color: colorForIndex(index),
  }));
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
): DemoFrame {
  const visible = bundle.events.filter((event) => event.seq <= seq);
  const current = visible[visible.length - 1];
  const layout = mosaicLayout(turns.length);
  const awake: DemoAwakeBot[] = turns.map((turn) => {
    const messages = (bundle.transcripts[turn.botId] ?? []).filter((row) => row.seq <= seq);
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
  };
}

export function projectFrame(bundle: DemoBundle, cursorSeq: number): DemoFrame {
  const lastSeq = bundle.lastSeq;
  const seq = Math.max(0, Math.min(cursorSeq, lastSeq));
  const visible = bundle.events.filter((event) => event.seq <= seq);
  const open = foldAwake(bundle.bots, visible);
  return paintFrame(bundle, seq, open, false);
}

export function projectStageFrame(bundle: DemoBundle, cursorSeq: number): DemoFrame {
  const origin = firstAwakeSeq(bundle.events);
  if (origin <= 0 || bundle.lastSeq <= 0) {
    return projectFrame(bundle, cursorSeq);
  }
  const seq = Math.max(origin, Math.min(cursorSeq, bundle.lastSeq));
  const visible = bundle.events.filter((event) => event.seq <= seq);
  const folded = foldAwakeStage(bundle.bots, visible);
  return paintFrame(bundle, seq, folded.stage, folded.holding);
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

function readProtocolFile(file: string): ProtocolEvent[] {
  if (!existsSync(file)) {
    return [];
  }
  const events: ProtocolEvent[] = [];
  for (const row of readJsonl(file)) {
    const parsed = parseProtocolEvent(row);
    if (parsed) {
      events.push(parsed);
    }
  }
  return events;
}

function readTranscriptFile(file: string): TranscriptEntry[] {
  if (!existsSync(file)) {
    return [];
  }
  const rows: TranscriptEntry[] = [];
  for (const raw of readJsonl(file)) {
    const parsed = parseTranscriptEntry(raw);
    if (parsed) {
      rows.push(parsed);
    }
  }
  return rows;
}

function parseActivity(raw: unknown): DemoActivity | undefined {
  if (!isRecord(raw)) {
    return undefined;
  }
  const type = asString(raw.type);
  const t = asString(raw.createdAt) ?? asString(raw.t);
  if (!type || !t || !KEEP_ACTIVITY.has(type)) {
    return undefined;
  }
  const title = asString(raw.title) ?? asString(raw.itemType) ?? type;
  return { t, type, title };
}

function compactActivities(file: string): DemoActivity[] {
  if (!existsSync(file)) {
    return [];
  }
  const rows: DemoActivity[] = [];
  for (const raw of readJsonl(file)) {
    const parsed = parseActivity(raw);
    if (parsed) {
      rows.push(parsed);
    }
  }
  return rows;
}

function writeJsonl(file: string, rows: readonly unknown[]): void {
  ensureDir(dirname(file));
  const body = rows.map((row) => JSON.stringify(row)).join("\n");
  writeFileSync(file, body.length > 0 ? `${body}\n` : "", "utf8");
}

function lastSeqOf(events: readonly ProtocolEvent[]): number {
  let last = 0;
  for (const event of events) {
    if (event.seq > last) {
      last = event.seq;
    }
  }
  return last;
}

function loadLiveBundle(computerRoot: string): DemoBundle {
  const bots = botsFromRoster(computerRoot);
  const events = readProtocolFile(protocolLogPath(computerRoot));
  const transcripts: Record<string, TranscriptEntry[]> = {};
  const activities: Record<string, DemoActivity[]> = {};
  for (const bot of bots) {
    transcripts[bot.id] = readTranscriptFile(transcriptPath(computerRoot, bot.id));
    activities[bot.id] = compactActivities(piRuntimePath(computerRoot, bot.id));
  }
  return {
    source: "live",
    lastSeq: lastSeqOf(events),
    bots,
    events,
    transcripts,
    activities,
  };
}

function parseMeta(raw: unknown): { recordedAt?: string; lastSeq?: number } {
  if (!isRecord(raw)) {
    return {};
  }
  return {
    recordedAt: asString(raw.recordedAt),
    lastSeq: typeof raw.lastSeq === "number" && Number.isFinite(raw.lastSeq) ? raw.lastSeq : undefined,
  };
}

function loadRecordingBundle(computerRoot: string): DemoBundle | undefined {
  const dir = demoLatestDir(computerRoot);
  const protocolFile = join(dir, "protocol.jsonl");
  if (!existsSync(protocolFile)) {
    return undefined;
  }
  const bots = botsFromRoster(computerRoot);
  const events = readProtocolFile(protocolFile);
  const transcripts: Record<string, TranscriptEntry[]> = {};
  const activities: Record<string, DemoActivity[]> = {};
  for (const bot of bots) {
    transcripts[bot.id] = readTranscriptFile(join(dir, "transcripts", `${bot.id}.jsonl`));
    activities[bot.id] = compactActivities(join(dir, "activities", `${bot.id}.jsonl`));
  }
  const meta = parseMeta(readJsonIfExists(join(dir, "meta.json")));
  return {
    source: "recording",
    recordedAt: meta.recordedAt,
    lastSeq: meta.lastSeq ?? lastSeqOf(events),
    bots,
    events,
    transcripts,
    activities,
  };
}

export function hasDemoRecording(computerRoot: string): boolean {
  return existsSync(join(demoLatestDir(computerRoot), "protocol.jsonl"));
}

export function demoMeta(computerRoot: string, source: DemoSourceQuery = "auto"): DemoMeta {
  const recording = loadRecordingBundle(computerRoot);
  const live = loadLiveBundle(computerRoot);
  const hasRecording = recording !== undefined;
  const picked = pickBundle(live, recording, source);
  return {
    source: picked.source,
    recordedAt: picked.recordedAt,
    lastSeq: picked.lastSeq,
    eventCount: picked.events.length,
    bots: picked.bots.length,
    hasRecording,
    hasLive: live.events.length > 0,
  };
}

function pickBundle(live: DemoBundle, recording: DemoBundle | undefined, source: DemoSourceQuery): DemoBundle {
  if (source === "live") {
    return live;
  }
  if (source === "recording") {
    if (!recording) {
      throw new DemoRecordingMissingError();
    }
    return recording;
  }
  return recording ?? live;
}

export class DemoRecordingMissingError extends Error {
  constructor() {
    super("no demo recording on this Computer (POST /api/demo/record)");
    this.name = "DemoRecordingMissingError";
  }
}

export function loadDemoBundle(computerRoot: string, source: DemoSourceQuery = "auto"): DemoBundle {
  const live = loadLiveBundle(computerRoot);
  const recording = loadRecordingBundle(computerRoot);
  return pickBundle(live, recording, source);
}

export function recordDemoSession(computerRoot: string): DemoRecordReport {
  const live = loadLiveBundle(computerRoot);
  const dir = demoLatestDir(computerRoot);
  if (existsSync(dir)) {
    rmSync(dir, { recursive: true, force: true });
  }
  ensureDir(dir);
  ensureDir(join(dir, "transcripts"));
  ensureDir(join(dir, "activities"));
  const protocolFile = protocolLogPath(computerRoot);
  if (existsSync(protocolFile)) {
    copyFileSync(protocolFile, join(dir, "protocol.jsonl"));
  } else {
    writeFileSync(join(dir, "protocol.jsonl"), "", "utf8");
  }
  for (const bot of live.bots) {
    const transcriptFile = transcriptPath(computerRoot, bot.id);
    if (existsSync(transcriptFile)) {
      copyFileSync(transcriptFile, join(dir, "transcripts", `${bot.id}.jsonl`));
    }
    writeJsonl(join(dir, "activities", `${bot.id}.jsonl`), live.activities[bot.id] ?? []);
  }
  const recordedAt = nowIso();
  writeJsonAtomic(join(dir, "meta.json"), {
    recordedAt,
    lastSeq: live.lastSeq,
    eventCount: live.events.length,
    bots: live.bots.map((bot) => bot.id),
  });
  return {
    recordedAt,
    lastSeq: live.lastSeq,
    eventCount: live.events.length,
    bots: live.bots.length,
    path: dir,
  };
}

export function removeDemoRecording(computerRoot: string): boolean {
  const dir = demoLatestDir(computerRoot);
  if (!existsSync(dir)) {
    return false;
  }
  rmSync(dir, { recursive: true, force: true });
  const root = join(dir, "..");
  if (existsSync(root) && readdirSync(root).length === 0) {
    rmSync(root, { recursive: true, force: true });
  }
  return true;
}

import {
  projectStageFrame,
  type DemoAwakeBot,
  type DemoBundle,
  type DemoFrame,
  type TranscriptEntry,
} from "./demo-replay";

export type DemoTimingMode = "beat" | "wall";

export interface DemoPlaybackSettings {
  readonly timing: DemoTimingMode;
  readonly wallSpeed: number;
  readonly wallMaxGapMs: number;
  readonly beatMs: number;
  readonly beatSpeed: number;
  readonly stream: boolean;
  readonly streamHold: number;
  readonly streamCharsPerSec: number;
  readonly showTimestamps: boolean;
  readonly lingerMs: number;
  readonly leadMs: number;
}

export const DEFAULT_DEMO_PLAYBACK: DemoPlaybackSettings = {
  timing: "beat",
  wallSpeed: 2,
  wallMaxGapMs: 2000,
  beatMs: 1600,
  beatSpeed: 1,
  stream: true,
  streamHold: 0.24,
  streamCharsPerSec: 72,
  showTimestamps: false,
  lingerMs: 280,
  leadMs: 0,
};

export interface DemoBeat {
  readonly index: number;
  readonly seq: number;
  readonly wallMs: number;
  readonly botId: string;
  readonly kind: string;
  readonly text: string;
}

export interface DemoMessageReveal {
  readonly revealed: string;
  readonly streaming: boolean;
  readonly complete: boolean;
}

export interface DemoPlayhead {
  readonly showMs: number;
  readonly totalMs: number;
  readonly progress: number;
  readonly seq: number;
  readonly wallMs: number;
  readonly beatIndex: number;
  readonly frame: DemoFrame;
  readonly reveals: Readonly<Record<string, DemoMessageReveal>>;
}

export interface DemoCursor {
  readonly seq: number;
  readonly wallMs: number;
  readonly beatIndex: number;
  readonly revealFrac: number;
  readonly spanMs: number;
  readonly elapsedInBeat: number;
}

const PLAYBACK_STORAGE_KEY = "harness-demo-playback-v2";

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function finite(value: number, fallback: number): number {
  return Number.isFinite(value) ? value : fallback;
}

export function clampPlaybackSettings(raw: Partial<DemoPlaybackSettings> | undefined): DemoPlaybackSettings {
  const base = DEFAULT_DEMO_PLAYBACK;
  if (!raw) {
    return base;
  }
  return {
    timing: raw.timing === "wall" ? "wall" : "beat",
    wallSpeed: clamp(finite(raw.wallSpeed ?? base.wallSpeed, base.wallSpeed), 0.25, 8),
    wallMaxGapMs: clamp(finite(raw.wallMaxGapMs ?? base.wallMaxGapMs, base.wallMaxGapMs), 0, 30_000),
    beatMs: clamp(finite(raw.beatMs ?? base.beatMs, base.beatMs), 200, 6000),
    beatSpeed: clamp(finite(raw.beatSpeed ?? base.beatSpeed, base.beatSpeed), 0.25, 8),
    stream: raw.stream !== false,
    streamHold: clamp(finite(raw.streamHold ?? base.streamHold, base.streamHold), 0, 0.45),
    streamCharsPerSec: clamp(finite(raw.streamCharsPerSec ?? base.streamCharsPerSec, base.streamCharsPerSec), 12, 240),
    showTimestamps: raw.showTimestamps === true,
    lingerMs: clamp(finite(raw.lingerMs ?? base.lingerMs, base.lingerMs), 0, 2000),
    leadMs: clamp(finite(raw.leadMs ?? base.leadMs, base.leadMs), 0, 2000),
  };
}

export function loadPlaybackSettings(): DemoPlaybackSettings {
  if (typeof localStorage === "undefined") {
    return DEFAULT_DEMO_PLAYBACK;
  }
  const raw = localStorage.getItem(PLAYBACK_STORAGE_KEY);
  if (!raw) {
    return DEFAULT_DEMO_PLAYBACK;
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return DEFAULT_DEMO_PLAYBACK;
    }
    return clampPlaybackSettings(parsed as Partial<DemoPlaybackSettings>);
  } catch (cause) {
    if (cause instanceof SyntaxError) {
      return DEFAULT_DEMO_PLAYBACK;
    }
    throw cause;
  }
}

export function savePlaybackSettings(settings: DemoPlaybackSettings): void {
  if (typeof localStorage === "undefined") {
    return;
  }
  localStorage.setItem(PLAYBACK_STORAGE_KEY, JSON.stringify(settings));
}

export function revealText(text: string, fraction: number): string {
  if (fraction >= 1) {
    return text;
  }
  if (fraction <= 0 || text.length === 0) {
    return "";
  }
  const chars = [...text];
  const count = Math.max(1, Math.ceil(chars.length * fraction));
  return chars.slice(0, Math.min(chars.length, count)).join("");
}

export function revealKey(botId: string, row: Pick<TranscriptEntry, "seq" | "kind">): string {
  return `${botId}:${row.seq}:${row.kind}`;
}

export function collectBeats(bundle: DemoBundle): DemoBeat[] {
  const rows: Array<Omit<DemoBeat, "index">> = [];
  for (const bot of bundle.bots) {
    for (const entry of bundle.transcripts[bot.id] ?? []) {
      const parsed = Date.parse(entry.t);
      rows.push({
        seq: entry.seq,
        wallMs: Number.isFinite(parsed) ? parsed : 0,
        botId: bot.id,
        kind: entry.kind,
        text: entry.text,
      });
    }
  }
  rows.sort((left, right) => left.seq - right.seq || left.wallMs - right.wallMs);
  return rows.map((row, index) => ({ ...row, index }));
}

export function beatSlotMs(settings: DemoPlaybackSettings): number {
  const speed = settings.beatSpeed > 0 ? settings.beatSpeed : 1;
  return Math.max(80, settings.beatMs / speed);
}

interface WallMark {
  readonly showMs: number;
  readonly wallMs: number;
  readonly seq: number;
  readonly beatIndex: number;
}

function openingCursor(beats: readonly DemoBeat[], settings: DemoPlaybackSettings): DemoCursor {
  const first = beats[0];
  if (!first) {
    return { seq: 0, wallMs: 0, beatIndex: -1, revealFrac: 0, spanMs: beatSlotMs(settings), elapsedInBeat: 0 };
  }
  return {
    seq: first.seq,
    wallMs: first.wallMs,
    beatIndex: 0,
    revealFrac: 0,
    spanMs: beatSlotMs(settings),
    elapsedInBeat: 0,
  };
}

export function buildWallMarks(beats: readonly DemoBeat[], settings: DemoPlaybackSettings): WallMark[] {
  if (beats.length === 0) {
    return [{ showMs: 0, wallMs: 0, seq: 0, beatIndex: -1 }];
  }
  const speed = settings.wallSpeed > 0 ? settings.wallSpeed : 1;
  const maxGap = Math.max(0, settings.wallMaxGapMs);
  const first = beats[0]!;
  const marks: WallMark[] = [];
  let show = 0;
  if (settings.leadMs > 0) {
    marks.push({ showMs: 0, wallMs: first.wallMs, seq: first.seq, beatIndex: 0 });
    show = settings.leadMs;
  }
  let prevWall = first.wallMs;
  for (let i = 0; i < beats.length; i += 1) {
    const beat = beats[i]!;
    if (i === 0) {
      marks.push({ showMs: show, wallMs: beat.wallMs, seq: beat.seq, beatIndex: 0 });
      continue;
    }
    const raw = Math.max(0, beat.wallMs - prevWall);
    const compressed = maxGap > 0 ? Math.min(raw, maxGap) : raw;
    show += Math.max(60, compressed / speed);
    marks.push({ showMs: show, wallMs: beat.wallMs, seq: beat.seq, beatIndex: i });
    prevWall = beat.wallMs;
  }
  const last = beats[beats.length - 1]!;
  const tail = Math.max(360, (last.text.length / Math.max(12, settings.streamCharsPerSec)) * 400);
  show += tail;
  marks.push({ showMs: show, wallMs: last.wallMs, seq: last.seq, beatIndex: beats.length - 1 });
  return marks;
}

function wallCursor(beats: readonly DemoBeat[], showMs: number, settings: DemoPlaybackSettings): DemoCursor {
  const marks = buildWallMarks(beats, settings);
  if (marks.length === 0 || beats.length === 0) {
    return openingCursor(beats, settings);
  }
  let index = 0;
  for (let i = 0; i < marks.length; i += 1) {
    const mark = marks[i];
    if (mark && mark.showMs <= showMs) {
      index = i;
    }
  }
  const mark = marks[index] ?? marks[0]!;
  const next = marks[index + 1];
  const spanMs = Math.max(1, (next?.showMs ?? mark.showMs + 400) - mark.showMs);
  const elapsed = Math.max(0, showMs - mark.showMs);
  const beat = mark.beatIndex >= 0 ? beats[mark.beatIndex] : undefined;
  const frac = revealFraction(elapsed, spanMs, beat ? [...beat.text].length : 0, settings);
  return {
    seq: mark.seq,
    wallMs: mark.wallMs,
    beatIndex: mark.beatIndex,
    revealFrac: frac,
    spanMs,
    elapsedInBeat: elapsed,
  };
}

function beatCursor(beats: readonly DemoBeat[], showMs: number, settings: DemoPlaybackSettings): DemoCursor {
  if (beats.length === 0) {
    return openingCursor(beats, settings);
  }
  const lead = Math.max(0, settings.leadMs);
  const first = beats[0]!;
  if (lead > 0 && showMs < lead) {
    return {
      seq: first.seq,
      wallMs: first.wallMs,
      beatIndex: 0,
      revealFrac: 0,
      spanMs: lead,
      elapsedInBeat: showMs,
    };
  }
  const slot = beatSlotMs(settings);
  const into = Math.max(0, showMs - lead);
  const index = Math.min(beats.length - 1, Math.floor(into / slot));
  const elapsed = into - index * slot;
  const beat = beats[index]!;
  return {
    seq: beat.seq,
    wallMs: beat.wallMs,
    beatIndex: index,
    revealFrac: revealFraction(elapsed, slot, [...beat.text].length, settings),
    spanMs: slot,
    elapsedInBeat: elapsed,
  };
}

export function revealFraction(
  elapsedMs: number,
  spanMs: number,
  textLen: number,
  settings: DemoPlaybackSettings,
): number {
  if (!settings.stream) {
    return 1;
  }
  if (elapsedMs <= 0) {
    return 0;
  }
  const span = Math.max(1, spanMs);
  const hold = clamp(settings.streamHold, 0, 0.45);
  const natural = (Math.max(1, textLen) / Math.max(8, settings.streamCharsPerSec)) * 1000;
  const window = Math.min(natural, Math.max(80, span * (1 - hold)));
  return clamp(elapsedMs / window, 0, 1);
}

export function timelineTotalMs(beats: readonly DemoBeat[], settings: DemoPlaybackSettings): number {
  if (beats.length === 0) {
    return 0;
  }
  if (settings.timing === "beat") {
    return settings.leadMs + beats.length * beatSlotMs(settings);
  }
  const marks = buildWallMarks(beats, settings);
  return marks[marks.length - 1]?.showMs ?? 0;
}

export function cursorAt(beats: readonly DemoBeat[], showMs: number, settings: DemoPlaybackSettings): DemoCursor {
  const total = timelineTotalMs(beats, settings);
  const clamped = clamp(showMs, 0, Math.max(0, total));
  return settings.timing === "wall" ? wallCursor(beats, clamped, settings) : beatCursor(beats, clamped, settings);
}

function applyReveals(
  frame: DemoFrame,
  beats: readonly DemoBeat[],
  cursor: DemoCursor,
  settings: DemoPlaybackSettings,
): { frame: DemoFrame; reveals: Record<string, DemoMessageReveal> } {
  const byKey = new Map<string, DemoBeat>();
  for (const beat of beats) {
    byKey.set(`${beat.botId}:${beat.seq}:${beat.kind}`, beat);
  }
  const reveals: Record<string, DemoMessageReveal> = {};
  const current = cursor.beatIndex >= 0 ? beats[cursor.beatIndex] : undefined;
  const awake: DemoAwakeBot[] = frame.awake.map((pane) => {
    const messages = pane.messages.map((row) => {
      const key = revealKey(pane.botId, row);
      const beat = byKey.get(key);
      const isCurrent = current !== undefined && beat?.index === current.index;
      const complete = beat === undefined || (current !== undefined && beat.index < current.index) || (isCurrent && cursor.revealFrac >= 1);
      const fraction = complete ? 1 : isCurrent ? cursor.revealFrac : 0;
      const revealed = revealText(row.text, fraction);
      const streaming = Boolean(settings.stream && isCurrent && cursor.revealFrac < 1 && revealed.length > 0);
      reveals[key] = { revealed, streaming, complete: fraction >= 1 };
      return row;
    }).filter((row) => {
      const key = revealKey(pane.botId, row);
      return (reveals[key]?.revealed.length ?? 0) > 0 || reveals[key]?.complete === true;
    });
    return { ...pane, messages };
  });
  return { frame: { ...frame, awake }, reveals };
}

export function projectPlayhead(
  bundle: DemoBundle,
  showMs: number,
  settings: DemoPlaybackSettings,
): DemoPlayhead {
  const beats = collectBeats(bundle);
  const totalMs = timelineTotalMs(beats, settings);
  const clamped = clamp(showMs, 0, Math.max(0, totalMs));
  const cursor = cursorAt(beats, clamped, settings);
  const frame = projectStageFrame(bundle, cursor.seq);
  const painted = applyReveals(frame, beats, cursor, settings);
  return {
    showMs: clamped,
    totalMs,
    progress: totalMs > 0 ? clamped / totalMs : 0,
    seq: cursor.seq,
    wallMs: cursor.wallMs,
    beatIndex: cursor.beatIndex,
    frame: painted.frame,
    reveals: painted.reveals,
  };
}

export function formatShowClock(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export function stepBeat(beats: readonly DemoBeat[], beatIndex: number, delta: number): number {
  if (beats.length === 0) {
    return 0;
  }
  return clamp(beatIndex + delta, 0, beats.length - 1);
}

export function showMsForBeat(beats: readonly DemoBeat[], beatIndex: number, settings: DemoPlaybackSettings): number {
  if (beatIndex < 0) {
    return 0;
  }
  if (settings.timing === "beat") {
    return settings.leadMs + beatIndex * beatSlotMs(settings) + 1;
  }
  const marks = buildWallMarks(beats, settings);
  const mark = marks.find((item) => item.beatIndex === beatIndex);
  return mark?.showMs ?? 0;
}

/**
 * Durable Bot↔Bot thread: one JSON file per pair, prompt then reply.
 * Only communication-protocol tool posts. Assistant text stays off this file.
 */
import { existsSync, readdirSync } from "node:fs";
import { join } from "node:path";

import { readJsonIfExists, withFileLock, writeJsonAtomic } from "../fs.ts";
import { threadFilePath, threadsDir } from "../paths.ts";
import { findBot, loadRoster } from "../roster.ts";
import type { ProtocolEvent, Roster } from "../types.ts";
import { pairChannelId, parsePairChannelId } from "./pair-id.ts";

const MAUS_COLORS = [
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

type MausColor = (typeof MAUS_COLORS)[number];

export interface ThreadSpeaker {
  readonly botId: string;
  readonly name: string;
  readonly color: MausColor;
}

export interface ThreadPost {
  readonly id: string;
  readonly handleId: string;
  readonly role: "bot";
  readonly kind: "text";
  readonly text: string;
  readonly at: number;
  readonly from: ThreadSpeaker;
}

export interface ThreadFile {
  readonly id: string;
  readonly threadId: string;
  readonly name: string;
  readonly memberIds: readonly string[];
  readonly createdAt: number;
  readonly dm: true;
  readonly messages: readonly ThreadPost[];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function colorFor(index: number): MausColor {
  return MAUS_COLORS[index % MAUS_COLORS.length] ?? "teal";
}

function epoch(iso: string | number): number {
  if (typeof iso === "number") {
    return iso;
  }
  const parsed = Date.parse(iso);
  return Number.isFinite(parsed) ? parsed : Date.now();
}

function speakerOf(roster: Roster, botId: string): ThreadSpeaker | undefined {
  const bot = findBot(roster, botId);
  if (!bot) {
    return undefined;
  }
  const index = roster.bots.findIndex((row) => row.id === bot.id);
  return { botId: bot.id, name: bot.name, color: colorFor(index) };
}

function emptyThread(roster: Roster, pairId: string): ThreadFile | undefined {
  const parsed = parsePairChannelId(pairId);
  if (!parsed) {
    return undefined;
  }
  const left = findBot(roster, parsed.a);
  const right = findBot(roster, parsed.b);
  if (!left || !right) {
    return undefined;
  }
  return {
    id: pairId,
    threadId: pairId,
    name: `${left.name} ↔ ${right.name}`,
    memberIds: [left.id, right.id],
    createdAt: Date.now(),
    dm: true,
    messages: [],
  };
}

function parseThreadFile(raw: unknown): ThreadFile | undefined {
  if (!isRecord(raw) || asString(raw.id).length === 0) {
    return undefined;
  }
  const messages: ThreadPost[] = [];
  if (Array.isArray(raw.messages)) {
    for (const row of raw.messages) {
      if (!isRecord(row) || asString(row.text).length === 0) {
        continue;
      }
      if (!isRecord(row.from) || asString(row.from.botId).length === 0) {
        continue;
      }
      const color = asString(row.from.color);
      messages.push({
        id: asString(row.id),
        handleId: asString(row.handleId) || asString(row.id),
        role: "bot",
        kind: "text",
        text: asString(row.text),
        at: typeof row.at === "number" ? row.at : epoch(asString(row.at)),
        from: {
          botId: asString(row.from.botId),
          name: asString(row.from.name) || asString(row.from.botId),
          color: (MAUS_COLORS as readonly string[]).includes(color) ? (color as MausColor) : "teal",
        },
      });
    }
  }
  const memberIds = Array.isArray(raw.memberIds)
    ? raw.memberIds.filter((row): row is string => typeof row === "string")
    : [];
  return {
    id: asString(raw.id),
    threadId: asString(raw.threadId) || asString(raw.id),
    name: asString(raw.name) || asString(raw.id),
    memberIds,
    createdAt: typeof raw.createdAt === "number" ? raw.createdAt : messages[0]?.at ?? Date.now(),
    dm: true,
    messages,
  };
}

function readThreadUnlocked(computerRoot: string, pairId: string): ThreadFile | undefined {
  const raw = readJsonIfExists(threadFilePath(computerRoot, pairId));
  return parseThreadFile(raw);
}

function writeThreadUnlocked(computerRoot: string, file: ThreadFile): void {
  writeJsonAtomic(threadFilePath(computerRoot, pairIdOf(file)), file);
}

function pairIdOf(file: ThreadFile): string {
  return file.id;
}

function appendUnlocked(
  computerRoot: string,
  roster: Roster,
  pairId: string,
  post: ThreadPost,
): ThreadFile | undefined {
  const existing = readThreadUnlocked(computerRoot, pairId) ?? emptyThread(roster, pairId);
  if (!existing) {
    return undefined;
  }
  if (existing.messages.some((row) => row.id === post.id)) {
    return existing;
  }
  const messages = [...existing.messages, post];
  const next: ThreadFile = {
    ...existing,
    createdAt: existing.messages.length === 0 ? post.at : existing.createdAt,
    messages,
  };
  writeThreadUnlocked(computerRoot, next);
  return next;
}

/** Sender prompt into the pair thread. Id is the Handle so a later reply can chain. */
export function appendThreadAsk(
  computerRoot: string,
  fromId: string,
  toId: string,
  handleId: string,
  text: string,
  at: string | number,
): ThreadFile | undefined {
  const trimmed = text.trim();
  if (trimmed.length === 0 || handleId.length === 0) {
    return undefined;
  }
  const roster = loadRoster(computerRoot);
  const from = speakerOf(roster, fromId);
  if (!from || !findBot(roster, toId)) {
    return undefined;
  }
  const pairId = pairChannelId(fromId, toId);
  return withFileLock(threadFilePath(computerRoot, pairId), () =>
    appendUnlocked(computerRoot, roster, pairId, {
      id: handleId,
      handleId,
      role: "bot",
      kind: "text",
      text: trimmed,
      at: epoch(at),
      from,
    }),
  );
}

/** Receiver ask_bot text into the pair thread. Separate from either Operator DM. */
export function appendThreadReply(
  computerRoot: string,
  fromId: string,
  toId: string,
  handleId: string,
  text: string,
  at: string | number,
): ThreadFile | undefined {
  const trimmed = text.trim();
  if (trimmed.length === 0 || handleId.length === 0) {
    return undefined;
  }
  const roster = loadRoster(computerRoot);
  const from = speakerOf(roster, fromId);
  if (!from || !findBot(roster, toId)) {
    return undefined;
  }
  const pairId = pairChannelId(fromId, toId);
  return withFileLock(threadFilePath(computerRoot, pairId), () =>
    appendUnlocked(computerRoot, roster, pairId, {
      id: `pair-result-${handleId}`,
      handleId,
      role: "bot",
      kind: "text",
      text: trimmed,
      at: epoch(at),
      from,
    }),
  );
}

export function readThread(computerRoot: string, pairId: string): ThreadFile | undefined {
  return readThreadUnlocked(computerRoot, pairId);
}

export function listThreadFiles(computerRoot: string): ThreadFile[] {
  const dir = threadsDir(computerRoot);
  if (!existsSync(dir)) {
    return [];
  }
  const out: ThreadFile[] = [];
  for (const name of readdirSync(dir)) {
    if (!name.endsWith(".json")) {
      continue;
    }
    const parsed = parseThreadFile(readJsonIfExists(join(dir, name)));
    if (parsed) {
      out.push(parsed);
    }
  }
  return out.sort((left, right) => left.createdAt - right.createdAt);
}

/** Fill thread JSON from protocol send/turn events when a file is missing (upgrade path). */
export function seedThreadsFromProtocol(
  computerRoot: string,
  events: readonly ProtocolEvent[],
  roster?: Roster,
): void {
  const live = roster ?? loadRoster(computerRoot);
  for (const event of events) {
    const from = event.from;
    const to = event.to;
    if (!from || !to || from === "operator" || from === "harness" || to === "operator") {
      continue;
    }
    if (!findBot(live, from) || !findBot(live, to)) {
      continue;
    }
    const handleId = event.handleId;
    if (!handleId) {
      continue;
    }
    if (event.type === "send.accepted") {
      appendThreadAsk(computerRoot, from, to, handleId, event.text ?? "", event.t);
      continue;
    }
    if (event.type === "thread.reply") {
      appendThreadReply(computerRoot, from, to, handleId, event.text ?? "", event.t);
    }
  }
}

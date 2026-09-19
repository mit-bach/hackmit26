import { existsSync, readdirSync } from "node:fs";
import { join } from "node:path";

import { readJsonIfExists, readJsonUnknown, writeJsonAtomic } from "./fs.ts";
import { nowIso } from "./ids.ts";
import { botsRoot, handleDir, handlePath } from "./paths.ts";
import type { ConversationKind, HandleRecord, HandleStatus, MessageKind } from "./types.ts";

const TRANSITIONS: Readonly<Record<HandleStatus, readonly HandleStatus[]>> = {
  accepted: ["queued", "running", "cancelled"],
  queued: ["running", "cancelled"],
  running: ["completed", "failed", "cancelled", "blocked", "queued"],
  blocked: ["running", "cancelled"],
  completed: [],
  failed: [],
  cancelled: [],
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
}

function isConversationKind(value: unknown): value is ConversationKind {
  return value === "operator_dm" || value === "peer_dm" || value === "room";
}

function isMessageKind(value: unknown): value is MessageKind {
  return (
    value === "user_dm" ||
    value === "user_stop" ||
    value === "a2a_handoff" ||
    value === "group_post" ||
    value === "group_mention" ||
    value === "result" ||
    value === "routine"
  );
}

function isHandleStatus(value: unknown): value is HandleStatus {
  return (
    value === "accepted" ||
    value === "queued" ||
    value === "running" ||
    value === "blocked" ||
    value === "completed" ||
    value === "failed" ||
    value === "cancelled"
  );
}

export function parseHandle(value: unknown): HandleRecord | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const id = asString(value.id);
  const from = asString(value.from);
  const to = asString(value.to);
  const toSlug = asString(value.toSlug);
  const prompt = asString(value.prompt);
  const status = value.status;
  const createdAt = asString(value.createdAt);
  const updatedAt = asString(value.updatedAt);
  const kind = asString(value.kind);
  if (
    !id ||
    !from ||
    !to ||
    !toSlug ||
    prompt === undefined ||
    !isHandleStatus(status) ||
    !createdAt ||
    !updatedAt ||
    !kind
  ) {
    return undefined;
  }
  const conversationRaw = value.conversation;
  if (!isRecord(conversationRaw) || !isConversationKind(conversationRaw.kind) || !isMessageKind(kind)) {
    return undefined;
  }
  return {
    id,
    from,
    to,
    toSlug,
    prompt,
    paths: asStringArray(value.paths),
    conversation: {
      kind: conversationRaw.kind,
      botId: asString(conversationRaw.botId),
      fromId: asString(conversationRaw.fromId),
      toId: asString(conversationRaw.toId),
      roomId: asString(conversationRaw.roomId),
    },
    kind,
    status,
    createdAt,
    updatedAt,
    result: asString(value.result),
    resultPaths: Array.isArray(value.resultPaths) ? asStringArray(value.resultPaths) : undefined,
    seq: typeof value.seq === "number" ? value.seq : undefined,
    error: asString(value.error),
    blockedReason: asString(value.blockedReason),
  };
}

export function writeHandle(computerRoot: string, botId: string, handle: HandleRecord): void {
  writeJsonAtomic(handlePath(computerRoot, botId, handle.id), handle);
}

export function readHandle(computerRoot: string, botId: string, handleId: string): HandleRecord | undefined {
  const raw = readJsonIfExists(handlePath(computerRoot, botId, handleId));
  if (raw === undefined) {
    return undefined;
  }
  return parseHandle(raw);
}

export function findHandle(computerRoot: string, handleId: string): HandleRecord | undefined {
  const owner = findHandleOwner(computerRoot, handleId);
  if (!owner) {
    return undefined;
  }
  return readHandle(computerRoot, owner, handleId);
}

export function findHandleOwner(computerRoot: string, handleId: string): string | undefined {
  const root = botsRoot(computerRoot);
  if (!existsSync(root)) {
    return undefined;
  }
  for (const ent of readdirSync(root, { withFileTypes: true })) {
    if (!ent.isDirectory()) {
      continue;
    }
    if (existsSync(handlePath(computerRoot, ent.name, handleId))) {
      return ent.name;
    }
  }
  return undefined;
}

export function listHandles(computerRoot: string, botId: string): HandleRecord[] {
  const dir = handleDir(computerRoot, botId);
  if (!existsSync(dir)) {
    return [];
  }
  const out: HandleRecord[] = [];
  for (const name of readdirSync(dir)) {
    if (!name.endsWith(".json")) {
      continue;
    }
    const parsed = parseHandle(readJsonUnknown(join(dir, name)));
    if (parsed) {
      out.push(parsed);
    }
  }
  return out.sort((a, b) => a.createdAt.localeCompare(b.createdAt));
}

export function canTransition(from: HandleStatus, to: HandleStatus): boolean {
  if (from === to) {
    return true;
  }
  return TRANSITIONS[from].includes(to);
}

export function transitionHandle(
  computerRoot: string,
  botId: string,
  handleId: string,
  next: HandleStatus,
  patch: Partial<Omit<HandleRecord, "id" | "status" | "createdAt">> = {},
): HandleRecord {
  const current = readHandle(computerRoot, botId, handleId);
  if (!current) {
    throw new Error(`unknown handle ${handleId}`);
  }
  if (!canTransition(current.status, next)) {
    throw new Error(`illegal handle transition ${current.status} -> ${next}`);
  }
  const updated: HandleRecord = {
    ...current,
    ...patch,
    status: next,
    updatedAt: nowIso(),
  };
  writeHandle(computerRoot, botId, updated);
  return updated;
}

export function isTerminalStatus(status: HandleStatus): boolean {
  return status === "completed" || status === "failed" || status === "cancelled";
}

export function patchHandle(
  computerRoot: string,
  botId: string,
  handleId: string,
  patch: Partial<Omit<HandleRecord, "id" | "status" | "createdAt">>,
): HandleRecord {
  const current = readHandle(computerRoot, botId, handleId);
  if (!current) {
    throw new Error(`unknown handle ${handleId}`);
  }
  const updated: HandleRecord = {
    ...current,
    ...patch,
    id: current.id,
    status: current.status,
    createdAt: current.createdAt,
    updatedAt: nowIso(),
  };
  writeHandle(computerRoot, botId, updated);
  return updated;
}

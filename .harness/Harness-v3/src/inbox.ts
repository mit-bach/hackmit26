import { existsSync } from "node:fs";

import { isProcessAlive, readJsonl, rewriteJsonlAtomic, withFileLock } from "./fs.ts";
import { nowIso } from "./ids.ts";
import { inboxPath } from "./paths.ts";
import type { InboxItem, InboxItemStatus, MessageKind } from "./types.ts";

const PRIORITY: Readonly<Record<MessageKind, number>> = {
  user_stop: 0,
  user_dm: 1,
  a2a_handoff: 2,
  group_mention: 2,
  group_post: 2,
  routine: 3,
  result: 4,
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

function isKind(value: unknown): value is MessageKind {
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

function isStatus(value: unknown): value is InboxItemStatus {
  return value === "pending" || value === "claimed" || value === "done";
}

export function parseInboxItem(value: unknown): InboxItem | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const id = asString(value.id);
  const handleId = asString(value.handleId);
  const from = asString(value.from);
  const to = asString(value.to);
  const prompt = asString(value.prompt);
  const createdAt = asString(value.createdAt);
  if (!id || !handleId || !from || !to || prompt === undefined || !createdAt) {
    return undefined;
  }
  if (!isKind(value.kind) || !isStatus(value.status)) {
    return undefined;
  }
  const conversationRaw = value.conversation;
  if (!isRecord(conversationRaw) || typeof conversationRaw.kind !== "string") {
    return undefined;
  }
  return {
    id,
    handleId,
    kind: value.kind,
    from,
    to,
    conversation: {
      kind: conversationRaw.kind as InboxItem["conversation"]["kind"],
      botId: asString(conversationRaw.botId),
      fromId: asString(conversationRaw.fromId),
      toId: asString(conversationRaw.toId),
      roomId: asString(conversationRaw.roomId),
    },
    prompt,
    paths: asStringArray(value.paths),
    mentions: asStringArray(value.mentions),
    createdAt,
    status: value.status,
    claimedByPid: typeof value.claimedByPid === "number" ? value.claimedByPid : undefined,
    claimedAt: asString(value.claimedAt),
  };
}

function loadItems(computerRoot: string, botId: string): InboxItem[] {
  const file = inboxPath(computerRoot, botId);
  if (!existsSync(file)) {
    return [];
  }
  const items: InboxItem[] = [];
  for (const row of readJsonl(file)) {
    const parsed = parseInboxItem(row);
    if (parsed) {
      items.push(parsed);
    }
  }
  return items;
}

function saveItems(computerRoot: string, botId: string, items: readonly InboxItem[]): void {
  rewriteJsonlAtomic(inboxPath(computerRoot, botId), items);
}

export function appendInbox(computerRoot: string, botId: string, item: InboxItem): void {
  const file = inboxPath(computerRoot, botId);
  withFileLock(file, () => {
    const items = loadItems(computerRoot, botId);
    items.push(item);
    saveItems(computerRoot, botId, items);
  });
}

export function listInbox(computerRoot: string, botId: string): InboxItem[] {
  return loadItems(computerRoot, botId);
}

export function pendingCount(computerRoot: string, botId: string): number {
  return loadItems(computerRoot, botId).filter((item) => effectiveStatus(item) === "pending").length;
}

function effectiveStatus(item: InboxItem): InboxItemStatus {
  if (item.status === "claimed" && item.claimedByPid !== undefined && !isProcessAlive(item.claimedByPid)) {
    return "pending";
  }
  return item.status;
}

export function claimNextInbox(
  computerRoot: string,
  botId: string,
  pid: number,
): InboxItem | undefined {
  const file = inboxPath(computerRoot, botId);
  return withFileLock(file, () => {
    const items = loadItems(computerRoot, botId).map((item) => {
      if (item.status === "claimed" && item.claimedByPid !== undefined && !isProcessAlive(item.claimedByPid)) {
        const recovered: InboxItem = { ...item, status: "pending" };
        return recovered;
      }
      return item;
    });
    const pending = items
      .filter((item) => item.status === "pending")
      .sort((a, b) => {
        const pa = PRIORITY[a.kind] ?? 9;
        const pb = PRIORITY[b.kind] ?? 9;
        if (pa !== pb) {
          return pa - pb;
        }
        return a.createdAt.localeCompare(b.createdAt);
      });
    const next = pending[0];
    if (!next) {
      saveItems(computerRoot, botId, items);
      return undefined;
    }
    const claimed: InboxItem = {
      ...next,
      status: "claimed",
      claimedByPid: pid,
      claimedAt: nowIso(),
    };
    const rewritten = items.map((item) => (item.id === claimed.id ? claimed : item));
    saveItems(computerRoot, botId, rewritten);
    return claimed;
  });
}

export function markInboxDone(computerRoot: string, botId: string, inboxId: string): void {
  const file = inboxPath(computerRoot, botId);
  withFileLock(file, () => {
    const items = loadItems(computerRoot, botId).map((item) => {
      if (item.id !== inboxId) {
        return item;
      }
      const done: InboxItem = { ...item, status: "done" };
      return done;
    });
    saveItems(computerRoot, botId, items);
  });
}

export function findInboxByHandle(
  computerRoot: string,
  botId: string,
  handleId: string,
): InboxItem | undefined {
  return loadItems(computerRoot, botId).find((item) => item.handleId === handleId);
}

export function requeueInbox(computerRoot: string, botId: string, inboxId: string): void {
  const file = inboxPath(computerRoot, botId);
  withFileLock(file, () => {
    const items = loadItems(computerRoot, botId).map((item) => {
      if (item.id !== inboxId) {
        return item;
      }
      const pending: InboxItem = {
        ...item,
        status: "pending",
        claimedByPid: undefined,
        claimedAt: undefined,
      };
      return pending;
    });
    saveItems(computerRoot, botId, items);
  });
}

export function claimInboxById(
  computerRoot: string,
  botId: string,
  inboxId: string,
  pid: number,
): InboxItem | undefined {
  const file = inboxPath(computerRoot, botId);
  return withFileLock(file, () => {
    const items = loadItems(computerRoot, botId);
    const current = items.find((item) => item.id === inboxId);
    if (!current || current.status === "done") {
      return undefined;
    }
    const claimed: InboxItem = {
      ...current,
      status: "claimed",
      claimedByPid: pid,
      claimedAt: nowIso(),
    };
    saveItems(
      computerRoot,
      botId,
      items.map((item) => (item.id === inboxId ? claimed : item)),
    );
    return claimed;
  });
}

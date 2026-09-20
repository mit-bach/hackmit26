import {
  claimInboxById,
  claimNextInbox,
  findInboxByHandle,
  listInbox,
  markInboxDone,
  requeueInbox,
} from "./inbox.ts";
import {
  isTerminalStatus,
  listHandles,
  readHandle,
  transitionHandle,
} from "./handle.ts";
import { isProcessAlive } from "./fs.ts";
import { readLane, touchLane } from "./lane-state.ts";
import { appendDailyLog } from "./memory.ts";
import { appendProtocol } from "./protocol-log.ts";
import { settleReceiptsForHandle } from "./routines.ts";
import { appendTranscript } from "./transcript.ts";
import { parseAskPeer } from "./ask-peer.ts";
import { appendThreadReply } from "./server/thread-log.ts";
import type { BotRecord, HandleRecord, InboxItem, Roster, TurnResult } from "./types.ts";

export interface BoundLane {
  readonly computerRoot: string;
  readonly bot: BotRecord;
  currentInbox: InboxItem | undefined;
  drainLock: boolean;
}

export function bindLane(computerRoot: string, bot: BotRecord): BoundLane {
  const lane: BoundLane = {
    computerRoot,
    bot,
    currentInbox: undefined,
    drainLock: false,
  };
  recoverStaleWork(lane);
  if (!lane.currentInbox) {
    touchLane(computerRoot, bot.id, bot.slug, "idle");
  }
  return lane;
}

export function recoverStaleWork(lane: BoundLane): void {
  const previous = readLane(lane.computerRoot, lane.bot.id);
  const dead = !previous || !isProcessAlive(previous.pid) || previous.pid !== process.pid;
  if (!dead) {
    return;
  }
  for (const item of listInbox(lane.computerRoot, lane.bot.id)) {
    if (
      item.status === "claimed" &&
      (item.claimedByPid === undefined || !isProcessAlive(item.claimedByPid))
    ) {
      requeueInbox(lane.computerRoot, lane.bot.id, item.id);
    }
  }
  let parked: InboxItem | undefined;
  for (const handle of listHandles(lane.computerRoot, lane.bot.id)) {
    if (handle.status === "running") {
      transitionHandle(lane.computerRoot, lane.bot.id, handle.id, "queued");
      const item = findInboxByHandle(lane.computerRoot, lane.bot.id, handle.id);
      if (item) {
        requeueInbox(lane.computerRoot, lane.bot.id, item.id);
      }
    }
    if (handle.status === "blocked") {
      const item = findInboxByHandle(lane.computerRoot, lane.bot.id, handle.id);
      if (item && item.status !== "done") {
        parked = claimInboxById(lane.computerRoot, lane.bot.id, item.id, process.pid) ?? item;
      }
    }
  }
  if (parked) {
    lane.currentInbox = parked;
    touchLane(lane.computerRoot, lane.bot.id, lane.bot.slug, "blocked", parked.handleId);
  }
}

export function noteBusyQueue(lane: BoundLane): void {
  if (!lane.currentInbox) {
    return;
  }
  for (const item of listInbox(lane.computerRoot, lane.bot.id)) {
    if (item.status !== "pending") {
      continue;
    }
    const handle = readHandle(lane.computerRoot, lane.bot.id, item.handleId);
    if (handle?.status === "accepted") {
      transitionHandle(lane.computerRoot, lane.bot.id, item.handleId, "queued");
    }
  }
}

export function startNextTurn(lane: BoundLane): InboxItem | undefined {
  interruptIfStop(lane);
  const parked = listHandles(lane.computerRoot, lane.bot.id).find((handle) => handle.status === "blocked");
  if (parked) {
    const parkedItem = findInboxByHandle(lane.computerRoot, lane.bot.id, parked.id);
    if (parkedItem && parkedItem.status !== "done") {
      lane.currentInbox = parkedItem.status === "claimed" ? parkedItem : claimInboxById(
        lane.computerRoot,
        lane.bot.id,
        parkedItem.id,
        process.pid,
      );
      touchLane(lane.computerRoot, lane.bot.id, lane.bot.slug, "blocked", parked.id);
      return undefined;
    }
  }
  if (lane.currentInbox) {
    return undefined;
  }
  const item = claimNextInbox(lane.computerRoot, lane.bot.id, process.pid);
  if (!item) {
    touchLane(lane.computerRoot, lane.bot.id, lane.bot.slug, "idle");
    return undefined;
  }
  const handle = readHandle(lane.computerRoot, lane.bot.id, item.handleId);
  if (!handle || isTerminalStatus(handle.status)) {
    markInboxDone(lane.computerRoot, lane.bot.id, item.id);
    return startNextTurn(lane);
  }
  if (handle.status === "blocked") {
    requeueInbox(lane.computerRoot, lane.bot.id, item.id);
    touchLane(lane.computerRoot, lane.bot.id, lane.bot.slug, "blocked", handle.id);
    return undefined;
  }
  if (handle.status === "accepted" || handle.status === "queued") {
    transitionHandle(lane.computerRoot, lane.bot.id, item.handleId, "running");
  }
  lane.currentInbox = item;
  touchLane(lane.computerRoot, lane.bot.id, lane.bot.slug, "running", item.handleId);
  const event = appendProtocol(lane.computerRoot, {
    type: "turn.start",
    from: item.from,
    to: item.to,
    handleId: item.handleId,
    slug: lane.bot.slug,
    status: "running",
    text: item.prompt,
  });
  appendTranscript(lane.computerRoot, lane.bot.id, {
    seq: event.seq,
    t: event.t,
    kind: "turn.start",
    text: `wake from ${item.from}: ${item.prompt}`.slice(0, 500),
    handleId: item.handleId,
    from: item.from,
    to: item.to,
  });
  noteBusyQueue(lane);
  return item;
}

export function blockTurn(lane: BoundLane, reason: string): void {
  const item = lane.currentInbox;
  if (!item) {
    return;
  }
  const handle = readHandle(lane.computerRoot, lane.bot.id, item.handleId);
  if (handle && handle.status === "running") {
    transitionHandle(lane.computerRoot, lane.bot.id, item.handleId, "blocked", {
      blockedReason: reason,
    });
  }
  touchLane(lane.computerRoot, lane.bot.id, lane.bot.slug, "blocked", item.handleId);
  appendProtocol(lane.computerRoot, {
    type: "turn.blocked",
    from: item.from,
    to: item.to,
    handleId: item.handleId,
    slug: lane.bot.slug,
    status: "blocked",
    text: reason,
  });
}

export function resumeTurn(lane: BoundLane): void {
  const item = lane.currentInbox;
  if (!item) {
    return;
  }
  const handle = readHandle(lane.computerRoot, lane.bot.id, item.handleId);
  if (handle?.status === "blocked") {
    transitionHandle(lane.computerRoot, lane.bot.id, item.handleId, "running");
  }
  touchLane(lane.computerRoot, lane.bot.id, lane.bot.slug, "running", item.handleId);
}

export function preemptPeerForUser(lane: BoundLane): InboxItem | undefined {
  const item = lane.currentInbox;
  if (!item) {
    return undefined;
  }
  if (item.kind === "user_dm" || item.kind === "user_stop") {
    return undefined;
  }
  const handle = readHandle(lane.computerRoot, lane.bot.id, item.handleId);
  if (handle?.status === "blocked") {
    return undefined;
  }
  if (handle?.status === "running") {
    transitionHandle(lane.computerRoot, lane.bot.id, item.handleId, "queued");
  }
  requeueInbox(lane.computerRoot, lane.bot.id, item.id);
  lane.currentInbox = undefined;
  return item;
}

export function cancelTurn(lane: BoundLane, reason: string): void {
  const item = lane.currentInbox;
  if (!item) {
    return;
  }
  const handle = readHandle(lane.computerRoot, lane.bot.id, item.handleId);
  const event = appendProtocol(lane.computerRoot, {
    type: "turn.end",
    from: item.from,
    to: item.to,
    handleId: item.handleId,
    slug: lane.bot.slug,
    status: "cancelled",
    text: reason,
  });
  if (handle && !isTerminalStatus(handle.status) && canCancel(handle.status)) {
    transitionHandle(lane.computerRoot, lane.bot.id, item.handleId, "cancelled", {
      result: reason,
      error: reason,
      seq: event.seq,
    });
  }
  settleReceiptsForHandle(lane.computerRoot, item.handleId, "cancelled", reason);
  markInboxDone(lane.computerRoot, lane.bot.id, item.id);
  appendTranscript(lane.computerRoot, lane.bot.id, {
    seq: event.seq,
    t: event.t,
    kind: "handoff.done",
    text: `${lane.bot.slug} cancelled handle ${item.handleId}: ${reason}`.slice(0, 500),
    handleId: item.handleId,
    from: item.from,
    to: item.to,
  });
  if (item.from !== "operator" && item.from !== "harness" && item.from !== lane.bot.id) {
    appendTranscript(lane.computerRoot, item.from, {
      seq: event.seq,
      t: event.t,
      kind: "handoff.done",
      text: `${lane.bot.slug} cancelled handle ${item.handleId}: ${reason}`.slice(0, 500),
      handleId: item.handleId,
      from: item.from,
      to: item.to,
    });
  }
  lane.currentInbox = undefined;
  touchLane(lane.computerRoot, lane.bot.id, lane.bot.slug, "idle");
}

function canCancel(status: HandleRecord["status"]): boolean {
  return (
    status === "accepted" ||
    status === "queued" ||
    status === "running" ||
    status === "blocked"
  );
}

export function interruptIfStop(lane: BoundLane): boolean {
  const waiting = listInbox(lane.computerRoot, lane.bot.id).some((item) => {
    if (item.kind !== "user_stop") {
      return false;
    }
    return item.status === "pending" || (item.status === "claimed" && item.id !== lane.currentInbox?.id);
  });
  if (!waiting) {
    return false;
  }
  if (lane.currentInbox && lane.currentInbox.kind !== "user_stop") {
    cancelTurn(lane, "operator stop");
    return true;
  }
  return false;
}

export function completeTurn(lane: BoundLane, result: TurnResult): void {
  const item = lane.currentInbox;
  if (!item) {
    return;
  }
  const handle = readHandle(lane.computerRoot, lane.bot.id, item.handleId);
  if (handle?.status === "blocked") {
    return;
  }
  if (!handle || isTerminalStatus(handle.status)) {
    markInboxDone(lane.computerRoot, lane.bot.id, item.id);
    if (handle) {
      settleReceiptsForHandle(lane.computerRoot, item.handleId, handle.status, handle.result);
    }
    lane.currentInbox = undefined;
    touchLane(lane.computerRoot, lane.bot.id, lane.bot.slug, "idle");
    return;
  }
  const nextStatus = result.error ? "failed" : "completed";
  const event = appendProtocol(lane.computerRoot, {
    type: "turn.end",
    from: item.from,
    to: item.to,
    handleId: item.handleId,
    slug: lane.bot.slug,
    status: nextStatus,
    text: result.text,
    paths: result.paths,
  });
  transitionHandle(lane.computerRoot, lane.bot.id, item.handleId, nextStatus, {
    result: result.text,
    resultPaths: result.paths,
    error: result.error,
    seq: event.seq,
  });
  settleReceiptsForHandle(lane.computerRoot, item.handleId, nextStatus, result.text);
  markInboxDone(lane.computerRoot, lane.bot.id, item.id);
  const line = {
    seq: event.seq,
    t: event.t,
    kind: "handoff.done",
    text: `${lane.bot.slug} finished handle ${item.handleId}: ${result.text}`.slice(0, 500),
    handleId: item.handleId,
    from: item.from,
    to: item.to,
  };
  appendTranscript(lane.computerRoot, lane.bot.id, line);
  if (item.from !== "operator" && item.from !== "harness" && item.from !== lane.bot.id) {
    appendTranscript(lane.computerRoot, item.from, line);
    if (item.kind === "a2a_handoff") {
      appendThreadReply(lane.computerRoot, lane.bot.id, item.from, item.handleId, result.text, event.t);
    }
  }
  appendDailyLog(lane.computerRoot, lane.bot.id, `${item.kind} from ${item.from} → ${nextStatus}`);
  lane.currentInbox = undefined;
  touchLane(lane.computerRoot, lane.bot.id, lane.bot.slug, "idle");
}

export function failTurn(lane: BoundLane, error: string): void {
  completeTurn(lane, { text: "", paths: [], error });
}

export function formatWake(item: InboxItem, roster?: Roster, selfSlug?: string): string {
  const pathLine = item.paths.length > 0 ? `paths: ${item.paths.join(", ")}` : "";
  const lines = [
    "[harness wake]",
    `kind: ${item.kind}`,
    `from: ${item.from}`,
    `handle: ${item.handleId}`,
    `conversation: ${item.conversation.kind}${item.conversation.roomId ? ` ${item.conversation.roomId}` : ""}`,
    pathLine,
    "",
    item.prompt,
  ];
  if (roster && selfSlug && item.kind === "user_dm") {
    const parsed = parseAskPeer(item.prompt, roster, selfSlug);
    if (parsed) {
      lines.push(
        "",
        `Required tool: call bot_ask (same as ask_bot) with bot_id=${parsed.slug} and prompt=${JSON.stringify(parsed.question)}. Then report the peer result. These tools are registered. Never say they are missing.`,
      );
    }
  }
  if (item.kind === "a2a_handoff") {
    lines.push(
      "",
      "---",
      "Harness note: Your assistant text is the reply in the pair thread with the sender. It also appears in this Bot's operator chat. Do not call ask_bot just to answer the sender. Messaging the Operator is a separate turn.",
    );
  }
  return lines.filter((line) => line.length > 0).join("\n");
}

export async function drainOnce(
  lane: BoundLane,
  execute: (item: InboxItem) => Promise<TurnResult>,
): Promise<boolean> {
  if (lane.drainLock) {
    return false;
  }
  lane.drainLock = true;
  try {
    const item = startNextTurn(lane);
    if (!item) {
      return false;
    }
    try {
      const result = await execute(item);
      const handle = readHandle(lane.computerRoot, lane.bot.id, item.handleId);
      if (handle?.status === "blocked") {
        return true;
      }
      completeTurn(lane, result);
    } catch (error) {
      const handle = readHandle(lane.computerRoot, lane.bot.id, item.handleId);
      if (handle?.status === "blocked") {
        return true;
      }
      const message = error instanceof Error ? error.message : String(error);
      failTurn(lane, message);
    }
    return true;
  } finally {
    lane.drainLock = false;
  }
}

export async function drainAll(
  lane: BoundLane,
  execute: (item: InboxItem) => Promise<TurnResult>,
): Promise<number> {
  let n = 0;
  while (await drainOnce(lane, execute)) {
    const handleId = lane.currentInbox?.handleId;
    if (handleId) {
      const handle = readHandle(lane.computerRoot, lane.bot.id, handleId);
      if (handle?.status === "blocked") {
        break;
      }
    }
    n += 1;
  }
  return n;
}

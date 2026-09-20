import { existsSync, readdirSync, statSync, watch, type FSWatcher } from "node:fs";
import { dirname, join } from "node:path";

import { listApprovals } from "../approvals.ts";
import { pendingCount } from "../inbox.ts";
import { liveStatus } from "../lane-state.ts";
import { piSessionDir, protocolLogPath } from "../paths.ts";
import { readProtocol } from "../protocol-log.ts";
import { findBot, loadRoster } from "../roster.ts";
import { listReceipts } from "../routines.ts";
import { sleep } from "../sleep.ts";
import type { EventBus } from "./bus.ts";
import { wireRun } from "./desk.ts";
import type { ProtocolEvent, Roster } from "../types.ts";
import { ombAdoptLeaf, ombChainParent, peerCommPayload, wireBotFrame } from "./omb-compat.ts";
import { getPairChannel, isPeerHandoff, pairChannelId } from "./pair-channels.ts";

function publishPeerChip(
  bus: EventBus,
  roster: Roster,
  event: ProtocolEvent,
  viewerId: string,
  messageId: string,
  atMs: number,
): void {
  const fields = peerCommPayload(roster, event.from ?? "", event.to ?? "", event.handleId, viewerId);
  if (!fields) {
    return;
  }
  const parentId = ombChainParent(viewerId);
  ombAdoptLeaf(viewerId, messageId);
  bus.publish({
    kind: "message",
    threadId: viewerId,
    message: {
      id: messageId,
      role: "bot",
      kind: "activity",
      text: fields.tool.name,
      at: atMs,
      parentId,
      ...fields,
    },
  });
}

function publishBotDesk(bus: EventBus, computerRoot: string, botId: string): void {
  const frame = wireBotFrame(computerRoot, botId);
  if (!frame) {
    return;
  }
  bus.publish({ kind: "bot", bot: frame });
}

function publishPair(bus: EventBus, computerRoot: string, roster: Roster, fromId: string, toId: string): void {
  const pairId = pairChannelId(fromId, toId);
  const pairGroup = getPairChannel(computerRoot, pairId, roster);
  if (pairGroup) {
    bus.publish({ kind: "group", group: pairGroup });
  }
}

function sessionStamp(computerRoot: string, botId: string): number {
  const dir = piSessionDir(computerRoot, botId);
  if (!existsSync(dir)) {
    return 0;
  }
  let max = 0;
  for (const name of readdirSync(dir)) {
    if (!name.endsWith(".jsonl")) {
      continue;
    }
    try {
      const mtime = statSync(join(dir, name)).mtimeMs;
      if (mtime > max) {
        max = mtime;
      }
    } catch {
      continue;
    }
  }
  return max;
}

export function startPumps(
  computerRoot: string,
  bus: EventBus,
): { stop: () => void } {
  let lastSeq = 0;
  for (const event of readProtocol(computerRoot, 0)) {
    lastSeq = event.seq;
  }
  const lastStatus = new Map<string, string>();
  const lastPending = new Map<string, number>();
  const lastSession = new Map<string, number>();
  let lastApprovalSig = listApprovals(computerRoot)
    .map((row) => `${row.id}:${row.status}`)
    .sort()
    .join("|");
  const lastReceiptStatus = new Map<string, string>();
  let watcher: FSWatcher | undefined;
  try {
    watcher = watch(dirname(protocolLogPath(computerRoot)), () => {
      flushProtocol();
    });
  } catch {
    watcher = undefined;
  }

  const flushProtocol = (): void => {
    const events = readProtocol(computerRoot, lastSeq);
    for (const event of events) {
      lastSeq = event.seq;
      bus.publish({ kind: "protocol", event });
      const roster = loadRoster(computerRoot);
      if (event.type === "send.accepted" && event.from && event.from !== "operator" && event.from !== "harness" && event.to) {
        const sender = findBot(roster, event.from);
        const receiver = findBot(roster, event.to);
        const at = Date.parse(event.t);
        const atMs = Number.isFinite(at) ? at : Date.now();
        const handleKey = event.handleId ?? String(event.seq);
        if (sender) {
          publishPeerChip(bus, roster, event, sender.id, `comm-${handleKey}`, atMs);
        }
        if (receiver) {
          publishPeerChip(bus, roster, event, receiver.id, `comm-recv-${handleKey}`, atMs);
        }
        publishPair(bus, computerRoot, roster, event.from, event.to);
      }
      if (
        (event.type === "turn.end" || event.type === "handoff.done" || event.type === "send.completed") &&
        event.from &&
        event.to
      ) {
        if (isPeerHandoff(roster, event.from, event.to)) {
          publishPair(bus, computerRoot, roster, event.from, event.to);
          publishBotDesk(bus, computerRoot, event.to);
          publishBotDesk(bus, computerRoot, event.from);
          continue;
        }
        const threadId = event.to;
        publishBotDesk(bus, computerRoot, threadId);
      }
    }
  };

  const flushBots = (): void => {
    const roster = loadRoster(computerRoot);
    for (const bot of roster.bots) {
      const status = liveStatus(computerRoot, bot.id);
      const pending = pendingCount(computerRoot, bot.id);
      const stamp = sessionStamp(computerRoot, bot.id);
      const prev = lastStatus.get(bot.id);
      const prevPending = lastPending.get(bot.id);
      const prevStamp = lastSession.get(bot.id);
      const sessionChanged = prevStamp !== stamp;
      if (sessionChanged) {
        lastSession.set(bot.id, stamp);
        lastStatus.set(bot.id, status);
        lastPending.set(bot.id, pending);
        publishBotDesk(bus, computerRoot, bot.id);
        continue;
      }
      if (prev !== status || prevPending !== pending) {
        lastStatus.set(bot.id, status);
        lastPending.set(bot.id, pending);
        const activity =
          status === "running"
            ? "working"
            : status === "blocked"
              ? "waiting-on-you"
              : pending > 0
                ? "working"
                : status === "offline"
                  ? "no-signal"
                  : "idle";
        const busy = activity === "working" || activity === "waiting-on-you";
        bus.publish({
          kind: "bot",
          bot: {
            id: bot.id,
            name: bot.name,
            status,
            pending,
            busy,
            activity,
            computer: "off",
          },
        });
      }
    }
    const approvals = listApprovals(computerRoot);
    const approvalSig = approvals
      .map((row) => `${row.id}:${row.status}`)
      .sort()
      .join("|");
    if (approvalSig !== lastApprovalSig) {
      lastApprovalSig = approvalSig;
      bus.publish({ kind: "approvals", approvals });
    }
    const receipts = listReceipts(computerRoot);
    for (const receipt of receipts) {
      const prev = lastReceiptStatus.get(receipt.id);
      if (prev !== receipt.status) {
        lastReceiptStatus.set(receipt.id, receipt.status);
        bus.publish({ kind: "routine.run", run: wireRun(roster, receipt) });
      }
    }
  };

  let running = true;
  const loop = async (): Promise<void> => {
    while (running) {
      try {
        flushProtocol();
        flushBots();
      } catch {
        // keep the host up
      }
      await sleep(400);
    }
  };
  void loop();

  return {
    stop: (): void => {
      running = false;
      watcher?.close();
    },
  };
}

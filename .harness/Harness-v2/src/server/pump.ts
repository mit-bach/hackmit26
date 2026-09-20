import { watch, type FSWatcher } from "node:fs";
import { dirname } from "node:path";

import { listApprovals } from "../approvals.ts";
import { pendingCount } from "../inbox.ts";
import { liveStatus } from "../lane-state.ts";
import { protocolLogPath } from "../paths.ts";
import { readProtocol } from "../protocol-log.ts";
import { loadRoster } from "../roster.ts";
import { listReceipts } from "../routines.ts";
import { sleep } from "../sleep.ts";
import type { EventBus } from "./bus.ts";
import { wireRun } from "./desk.ts";
import { ombAdoptLeaf, ombChainParent, ombLatestMessage, ombUserLeaf } from "./omb-compat.ts";

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
      const threadId = event.to ?? event.from;
      if (!threadId) {
        continue;
      }
      if (event.type === "turn.end" || event.type === "handoff.done" || event.type === "send.completed") {
        const latest = ombLatestMessage(computerRoot, threadId);
        const parentId = ombChainParent(threadId) ?? ombUserLeaf(threadId) ?? latest?.parentId ?? null;
        if (latest && latest.role === "bot" && latest.kind === "text" && (latest.text ?? "").trim().length > 0) {
          ombAdoptLeaf(threadId, latest.id);
          bus.publish({
            kind: "message",
            threadId,
            message: {
              ...latest,
              parentId,
            },
          });
        } else {
          const raw = event.text ?? "";
          const text = raw
            .replace(/^[^\n]*finished handle \S+:\s*/i, "")
            .replace(/^[^\n]*cancelled handle \S+:\s*/i, "");
          if (text.trim().length === 0) {
            continue;
          }
          const at = Date.parse(event.t);
          const messageId = `seq-${event.seq}`;
          ombAdoptLeaf(threadId, messageId);
          bus.publish({
            kind: "message",
            threadId,
            message: {
              id: messageId,
              role: "bot",
              kind: "text",
              text,
              at: Number.isFinite(at) ? at : Date.now(),
              parentId,
            },
          });
        }
      }
    }
  };

  const flushBots = (): void => {
    const roster = loadRoster(computerRoot);
    for (const bot of roster.bots) {
      const status = liveStatus(computerRoot, bot.id);
      const pending = pendingCount(computerRoot, bot.id);
      const prev = lastStatus.get(bot.id);
      const prevPending = lastPending.get(bot.id);
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

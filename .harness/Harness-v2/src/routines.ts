import { existsSync, readdirSync } from "node:fs";

import { awaitTurn } from "./await.ts";
import { readJsonIfExists, writeJsonAtomic } from "./fs.ts";
import { newReceiptId, nowIso } from "./ids.ts";
import { receiptDir, receiptPath } from "./paths.ts";
import { findBot, findRoutine, loadRoster } from "./roster.ts";
import { sendPrompt } from "./send.ts";
import type { HandleStatus, ReceiptRecord } from "./types.ts";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

export function parseReceipt(value: unknown): ReceiptRecord | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const id = asString(value.id);
  const name = asString(value.name);
  const bot = asString(value.bot);
  const at = asString(value.at);
  const updatedAt = asString(value.updatedAt);
  const status = value.status;
  if (!id || !name || !bot || !at || !updatedAt) {
    return undefined;
  }
  if (
    status !== "queued" &&
    status !== "running" &&
    status !== "completed" &&
    status !== "failed" &&
    status !== "missed"
  ) {
    return undefined;
  }
  return {
    id,
    name,
    bot,
    handleId: asString(value.handleId),
    status,
    at,
    updatedAt,
    result: asString(value.result),
  };
}

export function fireRoutine(computerRoot: string, name: string): ReceiptRecord {
  const roster = loadRoster(computerRoot);
  const routine = findRoutine(roster, name);
  if (!routine) {
    throw new Error(`unknown routine ${name}`);
  }
  const owner = findBot(roster, routine.bot);
  if (!owner) {
    throw new Error(`routine ${routine.name} owner ${routine.bot} is not a Bot`);
  }
  const at = nowIso();
  const receipt: ReceiptRecord = {
    id: newReceiptId(),
    name: routine.name,
    bot: owner.slug,
    status: "queued",
    at,
    updatedAt: at,
  };
  writeJsonAtomic(receiptPath(computerRoot, receipt.id), receipt);
  const sent = sendPrompt({
    computerRoot,
    from: "harness",
    to: owner.id,
    prompt: routine.prompt,
    kind: "routine",
    conversation:
      routine.conversation.startsWith("room:")
        ? { kind: "room", roomId: routine.conversation.slice("room:".length) }
        : { kind: "operator_dm", botId: owner.id },
  });
  if (!sent.accepted || !sent.handleId) {
    const failed: ReceiptRecord = {
      ...receipt,
      status: "failed",
      updatedAt: nowIso(),
      result: sent.reason ?? "not accepted",
    };
    writeJsonAtomic(receiptPath(computerRoot, receipt.id), failed);
    return failed;
  }
  const queued: ReceiptRecord = {
    ...receipt,
    handleId: sent.handleId,
    status: "queued",
    updatedAt: nowIso(),
  };
  writeJsonAtomic(receiptPath(computerRoot, receipt.id), queued);
  return queued;
}

export async function settleReceipt(
  computerRoot: string,
  receipt: ReceiptRecord,
  timeoutMs = 300_000,
): Promise<ReceiptRecord> {
  if (!receipt.handleId) {
    return receipt;
  }
  const outcome = await awaitTurn(computerRoot, receipt.handleId, { timeoutMs, waitOnBlocked: true });
  let status: ReceiptRecord["status"] = "queued";
  if (outcome.status === "completed") {
    status = "completed";
  } else if (outcome.status === "failed" || outcome.status === "cancelled") {
    status = "failed";
  } else if (outcome.status === "running") {
    status = "running";
  }
  const updated: ReceiptRecord = {
    ...receipt,
    status,
    result: outcome.result,
    updatedAt: nowIso(),
  };
  writeJsonAtomic(receiptPath(computerRoot, receipt.id), updated);
  return updated;
}

export function listReceipts(computerRoot: string): ReceiptRecord[] {
  const dir = receiptDir(computerRoot);
  if (!existsSync(dir)) {
    return [];
  }
  const out: ReceiptRecord[] = [];
  for (const name of readdirSync(dir)) {
    if (!name.endsWith(".json")) {
      continue;
    }
    const parsed = parseReceipt(readJsonIfExists(`${dir}/${name}`));
    if (parsed) {
      out.push(parsed);
    }
  }
  return out;
}

export function settleReceiptsForHandle(
  computerRoot: string,
  handleId: string,
  handleStatus: HandleStatus,
  result?: string,
): void {
  for (const receipt of listReceipts(computerRoot)) {
    if (receipt.handleId !== handleId) {
      continue;
    }
    let status: ReceiptRecord["status"] = receipt.status;
    if (handleStatus === "completed") {
      status = "completed";
    } else if (handleStatus === "failed" || handleStatus === "cancelled") {
      status = "failed";
    } else if (handleStatus === "running") {
      status = "running";
    } else {
      continue;
    }
    const updated: ReceiptRecord = {
      ...receipt,
      status,
      result,
      updatedAt: nowIso(),
    };
    writeJsonAtomic(receiptPath(computerRoot, receipt.id), updated);
  }
}

export function cadenceToMs(cadence: string): number | undefined {
  const trimmed = cadence.trim().toLowerCase();
  if (trimmed === "hourly") {
    return 60 * 60 * 1000;
  }
  if (trimmed === "daily") {
    return 24 * 60 * 60 * 1000;
  }
  const every = /^every\s+(\d+)\s*(s|m|h|ms)$/.exec(trimmed);
  if (!every) {
    return undefined;
  }
  const n = Number(every[1]);
  const unit = every[2];
  if (unit === "ms") {
    return n;
  }
  if (unit === "s") {
    return n * 1000;
  }
  if (unit === "m") {
    return n * 60 * 1000;
  }
  if (unit === "h") {
    return n * 60 * 60 * 1000;
  }
  return undefined;
}

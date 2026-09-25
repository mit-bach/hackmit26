import { existsSync, readdirSync } from "node:fs";
import { join } from "node:path";

import { readJsonIfExists, writeJsonAtomic } from "./fs.ts";
import { newApprovalId, nowIso } from "./ids.ts";
import { approvalDir, approvalPath } from "./paths.ts";
import { sleep } from "./sleep.ts";
import type { ApprovalLevel, ApprovalRecord } from "./types.ts";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

export function parseApproval(value: unknown): ApprovalRecord | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const id = asString(value.id);
  const botId = asString(value.botId);
  const toolName = asString(value.toolName);
  const detail = asString(value.detail);
  const createdAt = asString(value.createdAt);
  const status = value.status;
  if (!id || !botId || !toolName || detail === undefined || !createdAt) {
    return undefined;
  }
  if (status !== "pending" && status !== "allowed" && status !== "denied") {
    return undefined;
  }
  return {
    id,
    botId,
    handleId: asString(value.handleId),
    toolName,
    detail,
    status,
    createdAt,
    resolvedAt: asString(value.resolvedAt),
  };
}

const DELETE_TREE = /\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-rf|--recursive)\b/;
const SIDE_EFFECT =
  /\b(sudo|mkfs|shutdown|reboot|git\s+push|deploy|kubectl\s+apply)\b|\b(curl|wget)\b.*\|\s*(sh|bash)\b|\b(send-as-user|wire|ach\s+pay|publish)\b/i;

function commandOf(input: unknown): string {
  if (!isRecord(input)) {
    return "";
  }
  if (typeof input.command === "string") {
    return input.command;
  }
  if (typeof input.path === "string") {
    return input.path;
  }
  return JSON.stringify(input);
}

export function isConsequential(
  toolName: string,
  input: unknown,
  level: ApprovalLevel,
): boolean {
  const text = commandOf(input);
  if (DELETE_TREE.test(text) || /\brm\s+-rf\b/.test(text)) {
    return true;
  }
  if (level === "never") {
    return DELETE_TREE.test(text);
  }
  if (level === "always") {
    return toolName === "bash" || toolName === "write" || toolName === "edit";
  }
  if (toolName === "bash" && SIDE_EFFECT.test(text)) {
    return true;
  }
  return false;
}

export function createApproval(
  computerRoot: string,
  record: Omit<ApprovalRecord, "id" | "status" | "createdAt"> & { readonly id?: string },
): ApprovalRecord {
  const created: ApprovalRecord = {
    id: record.id ?? newApprovalId(),
    botId: record.botId,
    handleId: record.handleId,
    toolName: record.toolName,
    detail: record.detail,
    status: "pending",
    createdAt: nowIso(),
  };
  writeJsonAtomic(approvalPath(computerRoot, created.id), created);
  return created;
}

export function readApproval(computerRoot: string, approvalId: string): ApprovalRecord | undefined {
  const raw = readJsonIfExists(approvalPath(computerRoot, approvalId));
  if (raw === undefined) {
    return undefined;
  }
  return parseApproval(raw);
}

export function listApprovals(computerRoot: string): ApprovalRecord[] {
  const dir = approvalDir(computerRoot);
  if (!existsSync(dir)) {
    return [];
  }
  const out: ApprovalRecord[] = [];
  for (const name of readdirSync(dir)) {
    if (!name.endsWith(".json")) {
      continue;
    }
    const parsed = parseApproval(readJsonIfExists(join(dir, name)));
    if (parsed) {
      out.push(parsed);
    }
  }
  return out.sort((a, b) => a.createdAt.localeCompare(b.createdAt));
}

export function resolveApproval(
  computerRoot: string,
  approvalId: string,
  allowed: boolean,
): ApprovalRecord {
  const current = readApproval(computerRoot, approvalId);
  if (!current) {
    throw new Error(`unknown approval ${approvalId}`);
  }
  const updated: ApprovalRecord = {
    ...current,
    status: allowed ? "allowed" : "denied",
    resolvedAt: nowIso(),
  };
  writeJsonAtomic(approvalPath(computerRoot, approvalId), updated);
  return updated;
}

export async function waitForApproval(
  computerRoot: string,
  approvalId: string,
  timeoutMs = 300_000,
): Promise<ApprovalRecord> {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const current = readApproval(computerRoot, approvalId);
    if (current && current.status !== "pending") {
      return current;
    }
    await sleep(50);
  }
  const last = readApproval(computerRoot, approvalId);
  if (!last) {
    throw new Error(`approval ${approvalId} missing`);
  }
  if (last.status !== "pending") {
    return last;
  }
  return resolveApproval(computerRoot, approvalId, false);
}

/**
 * Client intercept for consequential Kernel ops.
 * Harness Operator approval is not the queue. Verifier Bots are.
 * Unlock reads the same Handle file completeTurn writes.
 */

import {existsSync, mkdirSync, readdirSync, readFileSync, renameSync, writeFileSync} from "node:fs";
import {basename, dirname, join} from "node:path";

import {isRecord} from "./load.ts";
import {botIdForSlug} from "./profile.ts";
import type {BoundProfile, CatalogOp, VerifierRoute} from "./types.ts";
import {isConsequentialKernelOp, routeVerifier} from "./verifier.ts";

export const VERIFIER_SLUGS: ReadonlySet<string> = new Set(["ctl-pay", "ctl-cash", "ctl-books"]);

export type ConsequentialGate =
  | {readonly kind: "proceed"}
  | {readonly kind: "forbidden"}
  | {readonly kind: "intercept"; readonly route: VerifierRoute};

export type HandleConcurrence = "CONCUR" | "REFUSE" | "none";

function writeJsonAtomic(path: string, value: unknown): void {
  mkdirSync(dirname(path), {recursive: true});
  const tmp = `${path}.tmp.${process.pid}`;
  writeFileSync(tmp, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  renameSync(tmp, path);
}

/** Same path as Harness `handlePath` / completeTurn. */
export function harnessHandlePath(computerRoot: string, botId: string, handleId: string): string {
  return join(computerRoot, "harness", "bots", botId, "handles", `${handleId}.json`);
}

export function pendingIndexPath(computerRoot: string, handleId: string): string {
  return join(computerRoot, "workspace", "verifier", "pending", `${handleId}.json`);
}

/** Legacy Client-only CONCUR store. Not the unlock source of truth. */
export function clientConcurPath(computerRoot: string, handleId: string): string {
  return join(computerRoot, "workspace", "verifier", "handles", `${handleId}.json`);
}

export function findHarnessHandlePath(computerRoot: string, handleId: string): string | undefined {
  const root = join(computerRoot, "harness", "bots");
  if (!existsSync(root)) {
    return undefined;
  }
  for (const ent of readdirSync(root, {withFileTypes: true})) {
    if (!ent.isDirectory()) {
      continue;
    }
    const path = harnessHandlePath(computerRoot, ent.name, handleId);
    if (existsSync(path)) {
      return path;
    }
  }
  return undefined;
}

function asDecision(value: unknown): HandleConcurrence {
  return value === "CONCUR" || value === "REFUSE" ? value : "none";
}

/**
 * Structured decisions only: a first line exactly `CONCUR` or `REFUSE`, or a
 * JSON object with `decision`. Prose such as "I do not concur" is "none".
 */
export function handleConcurrence(result: string): HandleConcurrence {
  const trimmed = result.trim();
  if (trimmed.length === 0) {
    return "none";
  }
  if (trimmed.startsWith("{")) {
    try {
      const raw: unknown = JSON.parse(trimmed);
      return isRecord(raw) ? asDecision(raw.decision) : "none";
    } catch {
      return "none";
    }
  }
  return asDecision(trimmed.split("\n", 1)[0]?.trim());
}

function pendingOpMatches(computerRoot: string, handleId: string, opId: string): boolean {
  const path = pendingIndexPath(computerRoot, handleId);
  if (!existsSync(path)) {
    return true;
  }
  try {
    const raw: unknown = JSON.parse(readFileSync(path, "utf8"));
    if (!isRecord(raw) || typeof raw.op !== "string") {
      return true;
    }
    return raw.op === opId;
  } catch {
    return true;
  }
}

export function completedHandleAllowsOp(
  computerRoot: string,
  handleId: string | null,
  op: CatalogOp,
): boolean {
  if (!handleId) {
    return false;
  }
  const path = findHarnessHandlePath(computerRoot, handleId);
  if (!path) {
    return false;
  }
  try {
    const raw: unknown = JSON.parse(readFileSync(path, "utf8"));
    if (!isRecord(raw) || raw.status !== "completed") {
      return false;
    }
    const result = typeof raw.result === "string" ? raw.result : "";
    if (handleConcurrence(result) !== "CONCUR") {
      return false;
    }
    if (typeof raw.op === "string" && raw.op !== op.id) {
      return false;
    }
    return pendingOpMatches(computerRoot, handleId, op.id);
  } catch {
    return false;
  }
}

export function gateConsequentialCall(
  bind: BoundProfile,
  op: CatalogOp,
  handleId: string | null,
): ConsequentialGate {
  if (!isConsequentialKernelOp(op)) {
    return {kind: "proceed"};
  }
  if (VERIFIER_SLUGS.has(bind.slug)) {
    return {kind: "forbidden"};
  }
  if (completedHandleAllowsOp(bind.computerRoot, handleId, op)) {
    return {kind: "proceed"};
  }
  const route = routeVerifier(op);
  if (!route) {
    return {kind: "forbidden"};
  }
  return {kind: "intercept", route};
}

function pendingKeyOf(raw: Record<string, unknown>): string | undefined {
  if (typeof raw.idempotencyKey === "string" || raw.idempotencyKey === null) {
    return raw.idempotencyKey ?? undefined;
  }
  // Index rows written before idempotencyKey was recorded name the packet `<key>.json`.
  return typeof raw.packetPath === "string" ? basename(raw.packetPath, ".json") : undefined;
}

/**
 * Pending Verifier Handle ids this Bot opened for one op and idempotency key,
 * newest first.
 */
export function pendingHandleIdsForKey(
  computerRoot: string,
  query: {readonly fromSlug: string; readonly op: string; readonly idempotencyKey: string},
): string[] {
  const dir = join(computerRoot, "workspace", "verifier", "pending");
  if (!existsSync(dir)) {
    return [];
  }
  const rows: {readonly id: string; readonly createdAt: string}[] = [];
  for (const ent of readdirSync(dir, {withFileTypes: true})) {
    if (!ent.isFile() || !ent.name.endsWith(".json")) {
      continue;
    }
    try {
      const raw: unknown = JSON.parse(readFileSync(join(dir, ent.name), "utf8"));
      if (
        !isRecord(raw) ||
        typeof raw.id !== "string" ||
        raw.fromSlug !== query.fromSlug ||
        raw.op !== query.op ||
        pendingKeyOf(raw) !== query.idempotencyKey
      ) {
        continue;
      }
      rows.push({id: raw.id, createdAt: typeof raw.createdAt === "string" ? raw.createdAt : ""});
    } catch {
      continue;
    }
  }
  rows.sort((a, b) => (a.createdAt < b.createdAt ? 1 : a.createdAt > b.createdAt ? -1 : 0));
  return rows.map((row) => row.id);
}

/**
 * The Verifier Handle to present for a retried call: the newest pending Handle
 * that already allows the op, else the newest pending Handle, else null.
 */
export function resolvePendingHandleId(
  bind: BoundProfile,
  op: CatalogOp,
  idempotencyKey: string | undefined,
): string | null {
  if (!idempotencyKey) {
    return null;
  }
  const ids = pendingHandleIdsForKey(bind.computerRoot, {
    fromSlug: bind.slug,
    op: op.id,
    idempotencyKey,
  });
  return ids.find((id) => completedHandleAllowsOp(bind.computerRoot, id, op)) ?? ids[0] ?? null;
}

export function persistPendingHandle(input: {
  readonly computerRoot: string;
  readonly handleId: string;
  readonly op: string;
  readonly route: VerifierRoute;
  readonly fromSlug: string;
  readonly packetPath: string;
  readonly idempotencyKey: string | null;
  readonly createdAt: string;
}): void {
  const botId = botIdForSlug(input.route.slug);
  writeJsonAtomic(pendingIndexPath(input.computerRoot, input.handleId), {
    id: input.handleId,
    status: "accepted",
    done: false,
    op: input.op,
    toSlug: input.route.slug,
    profile: input.route.profile,
    fromSlug: input.fromSlug,
    packetPath: input.packetPath,
    idempotencyKey: input.idempotencyKey,
    handleStore: "harness",
    handlePath: harnessHandlePath(input.computerRoot, botId, input.handleId),
    humanQueue: false,
    createdAt: input.createdAt,
  });
}

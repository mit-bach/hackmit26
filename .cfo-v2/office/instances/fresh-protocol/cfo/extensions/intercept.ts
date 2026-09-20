/**
 * Client intercept for consequential Kernel ops.
 * Harness Operator approval is not the queue. Verifier Bots are.
 */

import {existsSync, mkdirSync, readFileSync, renameSync, writeFileSync} from "node:fs";
import {dirname, join} from "node:path";

import {isRecord} from "./load.ts";
import type {BoundProfile, CatalogOp, VerifierRoute} from "./types.ts";
import {isConsequentialKernelOp, routeVerifier} from "./verifier.ts";

export const VERIFIER_SLUGS: ReadonlySet<string> = new Set(["ctl-pay", "ctl-cash", "ctl-books"]);

export type ConsequentialGate =
  | {readonly kind: "proceed"}
  | {readonly kind: "forbidden"}
  | {readonly kind: "intercept"; readonly route: VerifierRoute};

function writeJsonAtomic(path: string, value: unknown): void {
  mkdirSync(dirname(path), {recursive: true});
  const tmp = `${path}.tmp.${process.pid}`;
  writeFileSync(tmp, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  renameSync(tmp, path);
}

export function handleFilePath(computerRoot: string, handleId: string): string {
  return join(computerRoot, "workspace", "verifier", "handles", `${handleId}.json`);
}

export function completedHandleAllowsOp(
  computerRoot: string,
  handleId: string | null,
  op: CatalogOp,
): boolean {
  if (!handleId) {
    return false;
  }
  const path = handleFilePath(computerRoot, handleId);
  if (!existsSync(path)) {
    return false;
  }
  try {
    const raw: unknown = JSON.parse(readFileSync(path, "utf8"));
    if (!isRecord(raw)) {
      return false;
    }
    return raw.status === "completed" && raw.decision === "CONCUR" && raw.op === op.id;
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

export function persistPendingHandle(input: {
  readonly computerRoot: string;
  readonly handleId: string;
  readonly op: string;
  readonly route: VerifierRoute;
  readonly fromSlug: string;
  readonly packetPath: string;
  readonly createdAt: string;
}): void {
  writeJsonAtomic(handleFilePath(input.computerRoot, input.handleId), {
    id: input.handleId,
    status: "accepted",
    done: false,
    op: input.op,
    toSlug: input.route.slug,
    profile: input.route.profile,
    fromSlug: input.fromSlug,
    packetPath: input.packetPath,
    humanQueue: false,
    createdAt: input.createdAt,
  });
}

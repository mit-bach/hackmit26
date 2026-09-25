import {mkdirSync, renameSync, writeFileSync} from "node:fs";
import {dirname, join} from "node:path";

import {
  argsHash,
  gateConsequentialCall,
  persistPendingHandle,
} from "./intercept.ts";
import {buildKernelRequest, callSidecar} from "./kernel.ts";
import {prefixesForSlug, writePathAllowed, writePathFromArgs} from "./paths.ts";
import {grantAllows, resolveOp} from "./search.ts";
import type {
  BoundProfile,
  CallRequest,
  CallResult,
  CatalogFile,
  CatalogOp,
  PathLeaseFile,
} from "./types.ts";
import {routeVerifier, verifierInstruction, type VerifierIntercept} from "./verifier.ts";

const FORBIDDEN: CallResult = {
  ok: false,
  error: "forbidden",
  result: null,
  traceId: null,
};

export type SendHandleFn = (input: {
  readonly to: string;
  readonly prompt: string;
  readonly paths: readonly string[];
}) => Promise<string | null>;

function writeJsonAtomic(path: string, value: unknown): void {
  mkdirSync(dirname(path), {recursive: true});
  const tmp = `${path}.tmp.${process.pid}`;
  writeFileSync(tmp, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  renameSync(tmp, path);
}

function fail(error: string, result: unknown = null): CallResult {
  return {ok: false, error, result, traceId: null};
}

export function refuseConnectedTool(
  bind: BoundProfile,
  catalog: CatalogFile,
  request: CallRequest,
  leases: PathLeaseFile | undefined,
): CallResult | undefined {
  const op = resolveOp(catalog, request.name);
  if (op === undefined || !grantAllows(bind, op)) {
    return FORBIDDEN;
  }
  const writePath = writePathFromArgs(request.args);
  if (writePath === undefined) {
    return undefined;
  }
  const listed = leases === undefined ? [] : prefixesForSlug(leases, bind.slug);
  const memory = `harness/bots/bot_${bind.slug.replaceAll("-", "_")}/memory/`;
  const prefixes = listed.length > 0 ? listed : [`workspace/${bind.slug}/`, memory];
  if (!writePathAllowed(writePath, prefixes)) {
    return FORBIDDEN;
  }
  return undefined;
}

async function interceptVerifier(
  bind: BoundProfile,
  op: CatalogOp,
  request: CallRequest,
  sendHandle: SendHandleFn | undefined,
  nowIso: string,
): Promise<CallResult> {
  const route = routeVerifier(op);
  if (!route) {
    return fail("verifier_unmapped");
  }
  const key = request.idempotencyKey ?? `pending-${nowIso.replace(/[:.]/g, "")}`;
  const hash = argsHash(request.args);
  // One packet per key and args: a later call with other args must not rewrite
  // the packet a Verifier is still reading for an earlier Handle.
  const packetPath = join(bind.computerRoot, "workspace", "verifier", route.slug, `${key}.${hash.slice(0, 16)}.json`);
  writeJsonAtomic(packetPath, {
    op: op.id,
    args: request.args,
    argsHash: hash,
    fromSlug: bind.slug,
    fromProfile: bind.profile,
    verifier: route.slug,
    verifierProfile: route.profile,
    idempotencyKey: request.idempotencyKey ?? null,
    createdAt: nowIso,
    humanQueue: false,
  });
  let handleId: string | null = null;
  if (sendHandle) {
    handleId = await sendHandle({
      to: route.slug,
      prompt: verifierInstruction(route, packetPath),
      paths: [packetPath],
    });
  }
  const pendingId = handleId ?? key;
  persistPendingHandle({
    computerRoot: bind.computerRoot,
    handleId: pendingId,
    op: op.id,
    route,
    fromSlug: bind.slug,
    packetPath,
    idempotencyKey: request.idempotencyKey ?? null,
    argsHash: hash,
    createdAt: nowIso,
  });
  const intercept: VerifierIntercept = {
    error: "verifier_required",
    verifier: route.slug,
    verifierProfile: route.profile,
    reason: route.reason,
    packetPath,
    handleId: pendingId,
    instruction: `bot_send_prompt to ${route.slug} with profile ${route.profile}; await the Handle. After CONCUR, call again with the same idempotency_key and the same args. Never ask_user.`,
  };
  return {ok: false, error: "verifier_required", result: intercept, traceId: null};
}

export async function callConnectedTool(
  bind: BoundProfile,
  catalog: CatalogFile,
  request: CallRequest,
  leases: PathLeaseFile | undefined,
  handleId: string | null,
  sendHandle?: SendHandleFn,
): Promise<CallResult> {
  const refused = refuseConnectedTool(bind, catalog, request, leases);
  if (refused !== undefined) {
    return refused;
  }
  const op = resolveOp(catalog, request.name);
  if (op === undefined) {
    return FORBIDDEN;
  }
  if (op.mutability !== "read" && (request.idempotencyKey === undefined || request.idempotencyKey.length === 0)) {
    return fail("idempotency_required");
  }
  const gate = gateConsequentialCall(bind, op, handleId, request.args);
  if (gate.kind === "forbidden") {
    return FORBIDDEN;
  }
  if (gate.kind === "intercept") {
    return interceptVerifier(bind, op, request, sendHandle, new Date().toISOString());
  }
  return callSidecar(bind.computerRoot, buildKernelRequest(bind, op, request, handleId));
}

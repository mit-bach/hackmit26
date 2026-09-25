import {existsSync, readFileSync} from "node:fs";
import {join} from "node:path";

import {isRecord} from "./load.ts";
import type {BoundProfile, CallRequest, CatalogOp} from "./types.ts";

export interface KernelRequest {
  readonly op: string;
  readonly args: Readonly<Record<string, unknown>>;
  readonly botId: string;
  readonly slug: string;
  readonly profile: string;
  readonly handleId: string | null;
  readonly idempotencyKey: string | null;
}

export interface KernelResponse {
  readonly ok: boolean;
  readonly result: unknown;
  readonly error: string | null;
  readonly traceId: string | null;
}

export function readKernelPort(computerRoot: string): number | undefined {
  const path = join(computerRoot, "cfo", "kernel.port");
  if (!existsSync(path)) {
    return undefined;
  }
  const raw = readFileSync(path, "utf8").trim();
  const asNumber = Number(raw);
  if (Number.isFinite(asNumber) && asNumber > 0) {
    return asNumber;
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    if (isRecord(parsed) && typeof parsed.port === "number" && parsed.port > 0) {
      return parsed.port;
    }
  } catch {
    return undefined;
  }
  return undefined;
}

export function sidecarErrorCode(payload: Record<string, unknown>): string | null {
  if (payload.ok === true) {
    return null;
  }
  const err = payload.error;
  if (typeof err === "string" && err.length > 0) {
    return err;
  }
  if (isRecord(err) && typeof err.code === "string") {
    return err.code;
  }
  return "sidecar_error";
}

export function buildKernelRequest(
  bind: BoundProfile,
  op: CatalogOp,
  request: CallRequest,
  handleId: string | null,
): KernelRequest {
  return {
    op: op.id,
    args: request.args,
    botId: bind.botId,
    slug: bind.slug,
    profile: bind.profile,
    handleId,
    idempotencyKey: request.idempotencyKey ?? null,
  };
}

export async function callSidecar(
  computerRoot: string,
  body: KernelRequest,
): Promise<KernelResponse> {
  const port = readKernelPort(computerRoot);
  if (port === undefined) {
    return {
      ok: false,
      result: null,
      error: "sidecar_unavailable",
      traceId: null,
    };
  }
  try {
    const response = await fetch(`http://127.0.0.1:${port}/rpc`, {
      method: "POST",
      headers: {"content-type": "application/json"},
      body: JSON.stringify(body),
    });
    const payload: unknown = await response.json();
    if (!isRecord(payload)) {
      return {ok: false, result: null, error: "sidecar_bad_response", traceId: null};
    }
    return {
      ok: payload.ok === true,
      result: payload.result ?? null,
      error: sidecarErrorCode(payload),
      traceId: typeof payload.traceId === "string" ? payload.traceId : null,
    };
  } catch {
    return {ok: false, result: null, error: "sidecar_unavailable", traceId: null};
  }
}

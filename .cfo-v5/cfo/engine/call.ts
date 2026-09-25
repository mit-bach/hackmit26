import { isController, isWrite, loadCatalog, loadStepGrants, opsForStep, readOpsForBot, shortName, type CatalogOp } from "./grants.ts";
import { kernelRpc } from "./kernel.ts";
import { readItem, writeItem } from "./ledger.ts";
import type { Item, PendingWrite } from "./types.ts";
import { enqueueItem } from "./wake.ts";

const VERIFIER: Record<string, { readonly owner: string; readonly step: string }> = {
  "accrual.tools.create_accrual": { owner: "ctl-books", step: "review-treatment" },
  "accrual.tools.reconcile_accrual_with_invoice": { owner: "ctl-books", step: "review-treatment" },
  "inbox.tools.reply_in_thread": { owner: "ctl-pay", step: "review-pay" },
  "inbox.tools.send_inbox_message": { owner: "ctl-pay", step: "review-pay" },
  "inbox.tools.send_office_outbound": { owner: "ctl-pay", step: "review-pay" },
};

function stable(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  const record = value as Record<string, unknown>;
  return `{${Object.keys(record)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${stable(record[key])}`)
    .join(",")}}`;
}

function sameArgs(left: Record<string, unknown>, right: Record<string, unknown>): boolean {
  return stable(left) === stable(right);
}

function concurred(item: Item, verifier: string, step: string): boolean {
  return item.history.some(
    (entry) => entry.by === verifier && entry.step === step && entry.result.decision === "CONCUR",
  );
}

function refused(item: Item): boolean {
  return item.history.some((entry) => entry.result.decision === "REFUSE");
}

function kernelCall(
  computerRoot: string,
  slug: string,
  profile: string,
  op: string,
  args: Record<string, unknown>,
  idempotencyKey: string | undefined,
): { ok: boolean; result: unknown; error: string | null } {
  return kernelRpc(computerRoot, {
    op,
    args,
    botId: `bot_${slug.replaceAll("-", "_")}`,
    slug,
    profile,
    handleId: "engine",
    idempotencyKey: idempotencyKey ?? null,
  });
}

function profileFor(slug: string, step: string): string {
  if (slug === "ap" && step === "match") return "prepare";
  if (slug === "close" && step === "accrue") return "accrue";
  return step;
}

export interface CallOutcome {
  readonly ok: boolean;
  readonly error?: string;
  readonly result?: unknown;
  readonly pending?: boolean;
  readonly enqueued?: { readonly owner: string; readonly handleId: string };
}

export function callConnectedTool(input: {
  readonly computerRoot: string;
  readonly caller: string;
  readonly op: string;
  readonly args?: Record<string, unknown>;
  readonly idempotencyKey?: string;
  readonly item?: string;
}): CallOutcome {
  const catalog = loadCatalog(input.computerRoot);
  const meta = catalog.get(input.op);
  if (!meta) return { ok: false, error: `unknown op ${input.op}` };
  const grants = loadStepGrants(input.computerRoot);
  const args = input.args ?? {};
  if (!input.item) {
    if (isWrite(meta) || isController(input.caller)) {
      return { ok: false, error: `write ${shortName(meta)} is not available without an item` };
    }
    const reads = readOpsForBot(grants, input.caller, catalog);
    if (!reads.includes(meta.id)) {
      return { ok: false, error: `${shortName(meta)} is not available without an item` };
    }
    return kernelCall(input.computerRoot, input.caller, profileFor(input.caller, ""), meta.id, args, input.idempotencyKey);
  }
  let item: Item;
  try {
    item = readItem(input.computerRoot, input.item);
  } catch {
    return { ok: false, error: `unknown item ${input.item}` };
  }
  if (input.caller !== item.owner) {
    return { ok: false, error: `caller ${input.caller} is not the owner ${item.owner} of ${item.id}` };
  }
  const allowed = opsForStep(grants, item.owner, item.step);
  if (isWrite(meta)) {
    return writeOp(input.computerRoot, item, meta, args, input.idempotencyKey, allowed);
  }
  if (!allowed.includes(meta.id)) {
    return { ok: false, error: `${shortName(meta)} is not available at step ${item.step} of ${item.id}` };
  }
  const ran = kernelCall(input.computerRoot, item.owner, profileFor(item.owner, item.step), meta.id, args, input.idempotencyKey);
  return ran.ok ? { ok: true, result: ran.result } : { ok: false, error: ran.error ?? "kernel refused" };
}

function writeOp(
  computerRoot: string,
  item: Item,
  meta: CatalogOp,
  args: Record<string, unknown>,
  idempotencyKey: string | undefined,
  allowed: readonly string[],
): CallOutcome {
  if (isController(item.owner)) {
    return { ok: false, error: `${item.owner} cannot call a write op` };
  }
  if (!allowed.includes(meta.id)) {
    return { ok: false, error: `${shortName(meta)} is not available at step ${item.step} of ${item.id}` };
  }
  const key = idempotencyKey ?? "";
  if (key.length === 0) return { ok: false, error: "idempotency_required" };
  const route = VERIFIER[meta.id];
  if (!route) return { ok: false, error: `no verifier for ${meta.id}` };
  const pending = item.pendingWrite;
  if (pending && pending.idempotencyKey === key) {
    const handle = pending.verifierHandle;
    if (handle.length === 0) return { ok: false, error: "verifier handle missing" };
    if (pending.op !== meta.id || !sameArgs(pending.args, args)) {
      return { ok: false, error: `idempotency locked by verifier handle ${handle}` };
    }
  }
  const agreed = concurred(item, route.owner, route.step);
  if (refused(item) && !agreed) {
    return { ok: false, error: `write refused; ledger decision is REFUSE on ${item.id}` };
  }
  if (pending && pending.op === meta.id && pending.idempotencyKey === key && sameArgs(pending.args, args) && !agreed) {
    return { ok: false, error: "verifier_required", pending: true };
  }
  if (!agreed) {
    const enqueued = enqueueItem(computerRoot, item.id, route.step, route.owner);
    const stored: PendingWrite = {
      op: meta.id,
      args,
      idempotencyKey: key,
      verifierHandle: enqueued.handleId,
    };
    item.facts = {
      ...item.facts,
      resumeStep: item.step,
      resumeOwner: item.owner,
    };
    item.pendingWrite = stored;
    item.step = route.step;
    item.owner = route.owner;
    writeItem(computerRoot, item);
    return { ok: false, error: "verifier_required", pending: true, enqueued };
  }
  const ran = kernelCall(computerRoot, item.owner, profileFor(item.owner, item.step), meta.id, args, key);
  if (!ran.ok) return { ok: false, error: ran.error ?? "kernel gate refused" };
  item.pendingWrite = null;
  writeItem(computerRoot, item);
  return { ok: true, result: ran.result };
}

import { readItem, seedItem, writeItem } from "./ledger.ts";
import type { CompleteResult, HistoryEntry, Item, StepResult } from "./types.ts";
import { enqueueItem } from "./wake.ts";
import { advance, allowedDecisions } from "./workflows.ts";

function now(): string {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function pathAllowed(owner: string, raw: string): boolean {
  const rel = raw.replaceAll("\\", "/").replace(/^\.\//, "");
  if (rel.split("/").includes("..")) return false;
  return rel === `sandboxes/${owner}` || rel.startsWith(`sandboxes/${owner}/`);
}

function asResult(value: unknown, allowed: readonly string[]): { ok: true; result: StepResult } | { ok: false; error: string } {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return { ok: false, error: "schema: result must be an object with a decision" };
  }
  const record = value as Record<string, unknown>;
  const decision = record.decision;
  if (typeof decision !== "string" || !allowed.includes(decision)) {
    return {
      ok: false,
      error: `schema: decision ${JSON.stringify(decision)} is not one of ${allowed.join(", ")}`,
    };
  }
  return { ok: true, result: record as StepResult };
}

export function completeStep(input: {
  readonly computerRoot: string;
  readonly caller: string;
  readonly item: string;
  readonly wakeStep: string;
  readonly result: unknown;
  readonly paths?: readonly string[];
}): CompleteResult {
  let item: Item;
  try {
    item = readItem(input.computerRoot, input.item);
  } catch {
    return { ok: false, error: `unknown item ${input.item}` };
  }
  if (input.caller !== item.owner) {
    return { ok: false, error: `caller ${input.caller} is not the owner ${item.owner} of ${item.id}` };
  }
  if (input.wakeStep !== item.step) {
    return { ok: false, error: `wake step ${input.wakeStep} does not match ledger step ${item.step} of ${item.id}` };
  }
  const allowed = allowedDecisions(item.workflow, item.step);
  const parsed = asResult(input.result, allowed);
  if (!parsed.ok) return parsed;
  for (const path of input.paths ?? []) {
    if (!pathAllowed(item.owner, path)) {
      return { ok: false, error: `path ${path} is outside sandboxes/${item.owner}/` };
    }
  }
  const entry: HistoryEntry = {
    step: item.step,
    by: input.caller,
    result: parsed.result,
    t: now(),
  };
  item.history = [...item.history, entry];
  if (item.pendingWrite && (parsed.result.decision === "CONCUR" || parsed.result.decision === "REFUSE")) {
    const resumeStep = item.facts.resumeStep;
    const resumeOwner = item.facts.resumeOwner;
    if (
      typeof resumeStep === "string" &&
      typeof resumeOwner === "string" &&
      (resumeStep !== item.step || resumeOwner !== item.owner)
    ) {
      item.step = resumeStep;
      item.owner = resumeOwner;
      delete item.facts.resumeStep;
      delete item.facts.resumeOwner;
      writeItem(input.computerRoot, item);
      return { ok: true, next: { step: resumeStep, owner: resumeOwner }, item };
    }
  }
  const moved = advance(input.computerRoot, item, parsed.result);
  if (moved.kind === "terminal") {
    item.terminal = moved.terminal;
    writeItem(input.computerRoot, item);
    return { ok: true, terminal: moved.terminal, item };
  }
  if (moved.kind === "emit") {
    const child = seedItem(input.computerRoot, {
      id: moved.emit.id,
      workflow: moved.emit.workflow,
      step: moved.emit.step,
      owner: moved.emit.owner,
      facts: moved.emit.facts ?? {},
      pendingWrite: null,
      history: [],
    });
    item.terminal = moved.terminal ?? "emitted";
    writeItem(input.computerRoot, item);
    if (child.owner === input.caller) {
      return { ok: true, next: { step: child.step, owner: child.owner }, item };
    }
    const enqueued = enqueueItem(input.computerRoot, child.id, child.step, child.owner);
    return { ok: true, enqueued, item };
  }
  item.step = moved.step;
  item.owner = moved.owner;
  writeItem(input.computerRoot, item);
  if (moved.owner === input.caller) {
    return { ok: true, next: { step: moved.step, owner: moved.owner }, item };
  }
  const enqueued = enqueueItem(input.computerRoot, item.id, moved.step, moved.owner);
  return { ok: true, enqueued, item };
}

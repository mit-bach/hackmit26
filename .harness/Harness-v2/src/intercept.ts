import { findBot, loadRoster } from "./roster.ts";
import { readJsonIfExists, writeJsonAtomic } from "./fs.ts";
import { interceptPath } from "./paths.ts";
import { sendPrompt } from "./send.ts";
import type { ApprovalRecord } from "./types.ts";

export type InterceptTarget = { readonly kind: "operator" } | { readonly kind: "bot"; readonly bot: string };

export interface InterceptMap {
  readonly default: InterceptTarget;
  readonly bots: Readonly<Record<string, InterceptTarget>>;
}

const EMPTY: InterceptMap = { default: { kind: "operator" }, bots: {} };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseTarget(value: unknown): InterceptTarget | undefined {
  if (value === "operator" || value === "operator_dm") {
    return { kind: "operator" };
  }
  if (!isRecord(value)) {
    return undefined;
  }
  if (value.kind === "operator") {
    return { kind: "operator" };
  }
  if (value.kind === "bot" && typeof value.bot === "string" && value.bot.length > 0) {
    return { kind: "bot", bot: value.bot };
  }
  return undefined;
}

export function parseIntercept(value: unknown): InterceptMap {
  if (!isRecord(value)) {
    return EMPTY;
  }
  const fallback = parseTarget(value.default) ?? EMPTY.default;
  const bots: Record<string, InterceptTarget> = {};
  if (isRecord(value.bots)) {
    for (const [slug, raw] of Object.entries(value.bots)) {
      const parsed = parseTarget(raw);
      if (parsed) {
        bots[slug] = parsed;
      }
    }
  }
  return { default: fallback, bots };
}

export function loadIntercept(computerRoot: string): InterceptMap {
  return parseIntercept(readJsonIfExists(interceptPath(computerRoot)));
}

export function saveIntercept(computerRoot: string, next: InterceptMap): void {
  writeJsonAtomic(interceptPath(computerRoot), next);
}

const VERIFIER_OWNERS: Readonly<Record<string, string>> = {
  ap: "ctl-pay",
  pay: "ctl-pay",
  apply: "ctl-cash",
  collect: "ctl-cash",
  cash: "ctl-cash",
  close: "ctl-books",
  books: "ctl-books",
  story: "ctl-books",
};

/**
 * If intercept.json still has an empty map and the Roster has verifier Bots,
 * park those drafters on the matching ctl-* Bot instead of the Operator.
 */
export function seedVerifierIntercept(computerRoot: string): InterceptMap {
  const existing = loadIntercept(computerRoot);
  if (Object.keys(existing.bots).length > 0) {
    return existing;
  }
  const roster = loadRoster(computerRoot);
  const slugs = new Set(roster.bots.map((bot) => bot.slug));
  const bots: Record<string, InterceptTarget> = {};
  for (const [from, to] of Object.entries(VERIFIER_OWNERS)) {
    if (slugs.has(from) && slugs.has(to)) {
      bots[from] = { kind: "bot", bot: to };
    }
  }
  if (Object.keys(bots).length === 0) {
    return existing;
  }
  const next: InterceptMap = { default: existing.default, bots };
  saveIntercept(computerRoot, next);
  return next;
}

export function resolveIntercept(map: InterceptMap, botKey: string): InterceptTarget {
  return map.bots[botKey] ?? map.default;
}

export function notifyIntercept(computerRoot: string, approval: ApprovalRecord): void {
  const roster = loadRoster(computerRoot);
  const owner = findBot(roster, approval.botId);
  if (!owner) {
    return;
  }
  const target = resolveIntercept(loadIntercept(computerRoot), owner.slug);
  if (target.kind !== "bot") {
    return;
  }
  const verifier = findBot(roster, target.bot);
  if (!verifier || verifier.id === owner.id) {
    return;
  }
  sendPrompt({
    computerRoot,
    from: "harness",
    to: verifier.id,
    prompt: [
      `Approval ${approval.id} is parked for ${owner.slug}.`,
      `Tool: ${approval.toolName}`,
      `Detail: ${approval.detail}`,
      `Resolve with bot_resolve_approval approval_id=${approval.id} allowed=true|false.`,
    ].join("\n"),
    kind: "a2a_handoff",
    mode: "fire_and_forget",
  });
}

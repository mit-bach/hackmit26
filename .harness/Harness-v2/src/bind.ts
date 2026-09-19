import { resolve } from "node:path";

import { initComputer } from "./computer.ts";
import { findBot, loadRoster } from "./roster.ts";
import type { BotRecord, Roster } from "./types.ts";

export function resolveComputerRoot(cwd = process.cwd()): string {
  return resolve(process.env.HARNESS_COMPUTER ?? cwd);
}

export interface BindResult {
  readonly ok: true;
  readonly computerRoot: string;
  readonly roster: Roster;
  readonly bot: BotRecord;
}

export interface BindFailure {
  readonly ok: false;
  readonly reason: "unbound" | "unknown";
  readonly slug?: string;
  readonly computerRoot: string;
}

export function resolveBind(cwd = process.cwd()): BindResult | BindFailure {
  const computerRoot = resolveComputerRoot(cwd);
  const slug = process.env.HARNESS_BOT?.trim();
  if (!slug) {
    return { ok: false, reason: "unbound", computerRoot };
  }
  const roster = loadRoster(computerRoot);
  initComputer(computerRoot, roster);
  const bot = findBot(roster, slug);
  if (!bot) {
    return { ok: false, reason: "unknown", slug, computerRoot };
  }
  return { ok: true, computerRoot, roster, bot };
}

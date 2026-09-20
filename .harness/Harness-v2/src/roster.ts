import { existsSync } from "node:fs";
import { isAbsolute, join, resolve } from "node:path";

import { readJsonUnknown, writeJsonAtomic } from "./fs.ts";
import { rosterPath } from "./paths.ts";
import type { ApprovalLevel, BotRecord, RoomRecord, Roster, RoutineRecord } from "./types.ts";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
}

function asApprovalLevel(value: unknown): ApprovalLevel {
  if (value === "ask" || value === "always" || value === "never") {
    return value;
  }
  return "ask";
}

function parseBot(value: unknown): BotRecord | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const id = asString(value.id);
  const slug = asString(value.slug);
  const name = asString(value.name);
  if (id.length === 0 || slug.length === 0 || name.length === 0) {
    return undefined;
  }
  return {
    id,
    name,
    slug,
    purpose: asString(value.purpose),
    instructions: asString(value.instructions),
    skills: asStringArray(value.skills),
    connectors: asStringArray(value.connectors),
    approvalLevel: asApprovalLevel(value.approvalLevel),
  };
}

function parseRoom(value: unknown): RoomRecord | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const id = asString(value.id);
  const members = asStringArray(value.members);
  if (id.length === 0 || members.length < 2 || members.length > 6) {
    return undefined;
  }
  return {
    id,
    title: asString(value.title, id),
    members,
  };
}

function parseRoutine(value: unknown): RoutineRecord | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const name = asString(value.name);
  const bot = asString(value.bot);
  if (name.length === 0 || bot.length === 0) {
    return undefined;
  }
  return {
    name,
    bot,
    cadence: asString(value.cadence, "daily"),
    prompt: asString(value.prompt),
    conversation: asString(value.conversation, "operator_dm"),
  };
}

export function parseRoster(value: unknown): Roster {
  if (!isRecord(value)) {
    throw new Error("roster is not an object");
  }
  const bots = Array.isArray(value.bots)
    ? value.bots.map(parseBot).filter((bot): bot is BotRecord => bot !== undefined)
    : [];
  if (bots.length === 0) {
    throw new Error("roster has no bots");
  }
  const rooms = Array.isArray(value.rooms)
    ? value.rooms.map(parseRoom).filter((room): room is RoomRecord => room !== undefined)
    : [];
  const routines = Array.isArray(value.routines)
    ? value.routines.map(parseRoutine).filter((row): row is RoutineRecord => row !== undefined)
    : [];
  return {
    system: asString(value.system, "unnamed"),
    version: asString(value.version, "1"),
    description: asString(value.description),
    computer: asString(value.computer, "."),
    bots,
    rooms,
    routines,
  };
}

export function resolveRosterFile(computerRoot: string): string {
  const envPath = process.env.HARNESS_ROSTER;
  if (envPath && envPath.length > 0) {
    return isAbsolute(envPath) ? envPath : resolve(computerRoot, envPath);
  }
  const primary = rosterPath(computerRoot);
  if (existsSync(primary)) {
    return primary;
  }
  const alt = join(computerRoot, "roster.json");
  if (existsSync(alt)) {
    return alt;
  }
  throw new Error(`no roster.json under ${computerRoot}`);
}

function waitBriefly(): void {
  try {
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 20);
  } catch {
    const end = Date.now() + 20;
    while (Date.now() < end) {
      // spin
    }
  }
}

export function loadRoster(computerRoot: string): Roster {
  const path = resolveRosterFile(computerRoot);
  let last: unknown;
  for (let attempt = 0; attempt < 8; attempt += 1) {
    try {
      return parseRoster(readJsonUnknown(path));
    } catch (error) {
      last = error;
      waitBriefly();
    }
  }
  if (last instanceof Error) {
    throw last;
  }
  throw new Error(String(last));
}

export function saveRoster(computerRoot: string, roster: Roster): void {
  writeJsonAtomic(resolveRosterFile(computerRoot), roster);
}

export function findBot(roster: Roster, key: string): BotRecord | undefined {
  const needle = key.trim().toLowerCase();
  return roster.bots.find(
    (bot) =>
      bot.id.toLowerCase() === needle ||
      bot.slug.toLowerCase() === needle ||
      bot.name.toLowerCase() === needle,
  );
}

export function requireBot(roster: Roster, key: string): BotRecord {
  const bot = findBot(roster, key);
  if (!bot) {
    throw new Error(`unknown bot ${key}`);
  }
  return bot;
}

export function findRoom(roster: Roster, roomId: string): RoomRecord | undefined {
  return roster.rooms.find((room) => room.id === roomId);
}

export function findRoutine(roster: Roster, name: string): RoutineRecord | undefined {
  const needle = name.trim().toLowerCase();
  return roster.routines.find(
    (row) => row.name.toLowerCase() === needle || row.bot.toLowerCase() === needle,
  );
}

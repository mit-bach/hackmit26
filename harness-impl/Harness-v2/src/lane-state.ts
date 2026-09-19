import { readJsonIfExists, writeJsonAtomic } from "./fs.ts";
import { isProcessAlive } from "./fs.ts";
import { nowIso } from "./ids.ts";
import { lanePath } from "./paths.ts";
import type { BotStatus, LaneState } from "./types.ts";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function isBotStatus(value: unknown): value is BotStatus {
  return value === "offline" || value === "idle" || value === "running" || value === "blocked";
}

export function parseLane(value: unknown): LaneState | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const botId = asString(value.botId);
  const slug = asString(value.slug);
  const updatedAt = asString(value.updatedAt);
  if (!botId || !slug || !updatedAt || !isBotStatus(value.status) || typeof value.pid !== "number") {
    return undefined;
  }
  return {
    botId,
    slug,
    status: value.status,
    pid: value.pid,
    handleId: asString(value.handleId),
    updatedAt,
  };
}

export function writeLane(computerRoot: string, state: LaneState): void {
  writeJsonAtomic(lanePath(computerRoot, state.botId), state);
}

export function readLane(computerRoot: string, botId: string): LaneState | undefined {
  const raw = readJsonIfExists(lanePath(computerRoot, botId));
  if (raw === undefined) {
    return undefined;
  }
  return parseLane(raw);
}

const HEARTBEAT_STALE_MS = 8000;

export function liveStatus(computerRoot: string, botId: string): BotStatus {
  const lane = readLane(computerRoot, botId);
  if (!lane) {
    return "offline";
  }
  const age = Date.now() - Date.parse(lane.updatedAt);
  if (!isProcessAlive(lane.pid) || !Number.isFinite(age) || age > HEARTBEAT_STALE_MS) {
    return "offline";
  }
  return lane.status;
}

export function touchLane(
  computerRoot: string,
  botId: string,
  slug: string,
  status: BotStatus,
  handleId?: string,
): LaneState {
  const state: LaneState = {
    botId,
    slug,
    status,
    pid: process.pid,
    handleId,
    updatedAt: nowIso(),
  };
  writeLane(computerRoot, state);
  return state;
}

export function isLaneBusy(computerRoot: string, botId: string): boolean {
  const status = liveStatus(computerRoot, botId);
  return status === "running" || status === "blocked";
}

import { existsSync } from "node:fs";

import { appendJsonlAtomic, readJsonl } from "./fs.ts";
import { nowIso } from "./ids.ts";
import { protocolLogPath } from "./paths.ts";
import { nextSeq } from "./seq.ts";
import type { ProtocolEvent } from "./types.ts";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function asNumber(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function asStringArray(value: unknown): string[] | undefined {
  if (!Array.isArray(value)) {
    return undefined;
  }
  return value.filter((item): item is string => typeof item === "string");
}

export function parseProtocolEvent(value: unknown): ProtocolEvent | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const seq = asNumber(value.seq);
  const type = asString(value.type);
  const t = asString(value.t);
  if (seq === undefined || type === undefined || t === undefined) {
    return undefined;
  }
  return {
    t,
    seq,
    type,
    from: asString(value.from),
    to: asString(value.to),
    handleId: asString(value.handleId),
    roomId: asString(value.roomId),
    slug: asString(value.slug),
    text: asString(value.text),
    status: asString(value.status),
    paths: asStringArray(value.paths),
  };
}

export function appendProtocol(
  computerRoot: string,
  event: Omit<ProtocolEvent, "seq" | "t"> & { readonly t?: string },
): ProtocolEvent {
  const row: ProtocolEvent = {
    ...event,
    t: event.t ?? nowIso(),
    seq: nextSeq(computerRoot),
  };
  appendJsonlAtomic(protocolLogPath(computerRoot), row);
  return row;
}

export function readProtocol(computerRoot: string, afterSeq = 0): ProtocolEvent[] {
  const file = protocolLogPath(computerRoot);
  if (!existsSync(file)) {
    return [];
  }
  const events: ProtocolEvent[] = [];
  for (const row of readJsonl(file)) {
    const parsed = parseProtocolEvent(row);
    if (parsed && parsed.seq > afterSeq) {
      events.push(parsed);
    }
  }
  return events;
}

export function searchProtocol(
  computerRoot: string,
  query: string,
  botId?: string,
): ProtocolEvent[] {
  const needle = query.trim().toLowerCase();
  return readProtocol(computerRoot).filter((event) => {
    if (botId && event.from !== botId && event.to !== botId && event.slug !== botId) {
      return false;
    }
    if (needle.length === 0) {
      return true;
    }
    const hay = `${event.type} ${event.from ?? ""} ${event.to ?? ""} ${event.handleId ?? ""} ${event.text ?? ""} ${event.slug ?? ""}`.toLowerCase();
    return hay.includes(needle);
  });
}

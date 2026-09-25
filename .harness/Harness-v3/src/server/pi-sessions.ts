/**
 * Pi conversation files live on the Computer under
 * harness/bots/<botId>/pi-session/*.jsonl — not the Harness package .pi folder.
 */
import { existsSync, readdirSync, statSync } from "node:fs";
import { basename, join } from "node:path";

import { readJsonl } from "../fs.ts";
import { piSessionDir } from "../paths.ts";
import type { PiHydratedTool, PiHydratedTurn } from "./pi-runtime.ts";

export interface PiSessionSummary {
  readonly name: string;
  readonly id: string;
  readonly path: string;
  readonly startedAt: string;
  readonly messageCount: number;
}

export interface PiSessionTurn {
  readonly id: string;
  readonly role: "user" | "assistant" | "tool";
  readonly text: string;
  readonly at: string;
  readonly toolName?: string;
}

export interface PiSessionBody {
  readonly name: string;
  readonly path: string;
  readonly turns: readonly PiSessionTurn[];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function stringifyUnknown(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  if (value === undefined || value === null) {
    return "";
  }
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

/** Basename only; rejects path escape. */
export function isPiSessionFileName(name: string): boolean {
  const base = basename(name);
  return base === name && /^[\w.-]+\.jsonl$/.test(base);
}

function contentText(message: Record<string, unknown>): string {
  if (!Array.isArray(message.content)) {
    return asString(message.text);
  }
  const parts: string[] = [];
  for (const part of message.content) {
    if (!isRecord(part)) {
      continue;
    }
    if (asString(part.type) === "text" && asString(part.text).length > 0) {
      parts.push(asString(part.text));
    }
  }
  return parts.join("\n").trim();
}

function connectedName(rawName: string, args: unknown): string {
  if (rawName === "call_connected_tool" && isRecord(args) && asString(args.name).length > 0) {
    return asString(args.name);
  }
  return rawName.length > 0 ? rawName : "tool";
}

function toolResultText(inner: Record<string, unknown>): string {
  const fromContent = contentText(inner);
  if (fromContent.length > 0) {
    return fromContent;
  }
  if (inner.details !== undefined) {
    return stringifyUnknown(inner.details);
  }
  return stringifyUnknown(inner.content);
}

/** List Pi session jsonl files for one Bot, newest first. */
export function listPiSessions(computerRoot: string, botId: string): PiSessionSummary[] {
  const dir = piSessionDir(computerRoot, botId);
  if (!existsSync(dir)) {
    return [];
  }
  const out: PiSessionSummary[] = [];
  for (const name of readdirSync(dir)) {
    if (!isPiSessionFileName(name)) {
      continue;
    }
    const abs = join(dir, name);
    let startedAt = "";
    let id = name.replace(/\.jsonl$/, "");
    let messageCount = 0;
    try {
      startedAt = statSync(abs).mtime.toISOString();
    } catch {
      continue;
    }
    for (const row of readJsonl(abs)) {
      if (!isRecord(row)) {
        continue;
      }
      const type = asString(row.type);
      if (type === "session") {
        startedAt = asString(row.timestamp) || startedAt;
        id = asString(row.id) || id;
      }
      if (type === "message") {
        messageCount += 1;
      }
    }
    out.push({
      name,
      id,
      path: `harness/bots/${botId}/pi-session/${name}`,
      startedAt,
      messageCount,
    });
  }
  return out.sort((left, right) => right.startedAt.localeCompare(left.startedAt));
}

/** Read one Pi session as a clickable chat log (user / assistant / Kernel tool). */
export function readPiSession(
  computerRoot: string,
  botId: string,
  name: string,
): PiSessionBody | undefined {
  if (!isPiSessionFileName(name)) {
    return undefined;
  }
  const abs = join(piSessionDir(computerRoot, botId), name);
  if (!existsSync(abs)) {
    return undefined;
  }
  const turns: PiSessionTurn[] = [];
  const pendingNames = new Map<string, string>();
  for (const row of readJsonl(abs)) {
    if (!isRecord(row) || asString(row.type) !== "message") {
      continue;
    }
    const at = asString(row.timestamp) || new Date().toISOString();
    const id = asString(row.id) || `msg-${turns.length}`;
    const inner = isRecord(row.message) ? row.message : row;
    const role = asString(inner.role) || asString(row.role);
    if (role === "user") {
      const text = contentText(inner);
      if (text.length === 0) {
        continue;
      }
      turns.push({ id, role: "user", text, at });
      continue;
    }
    if (role === "assistant") {
      const text = contentText(inner);
      if (text.length > 0) {
        turns.push({ id, role: "assistant", text, at });
      }
      if (Array.isArray(inner.content)) {
        for (const part of inner.content) {
          if (!isRecord(part) || asString(part.type) !== "toolCall") {
            continue;
          }
          const callId = asString(part.id);
          const name = connectedName(asString(part.name), part.arguments);
          if (callId.length > 0) {
            pendingNames.set(callId, name);
          }
        }
      }
      continue;
    }
    if (role === "toolResult" || role === "tool") {
      const callId = asString(inner.toolCallId) || asString(row.toolCallId);
      const toolName =
        (callId.length > 0 ? pendingNames.get(callId) : undefined) ??
        connectedName(asString(inner.toolName) || asString(row.toolName), inner.arguments);
      const text = toolResultText(inner);
      turns.push({
        id,
        role: "tool",
        text,
        at,
        toolName,
      });
    }
  }
  return {
    name,
    path: `harness/bots/${botId}/pi-session/${name}`,
    turns,
  };
}

function thinkingText(message: Record<string, unknown>): string {
  if (!Array.isArray(message.content)) {
    return "";
  }
  const parts: string[] = [];
  for (const part of message.content) {
    if (!isRecord(part)) {
      continue;
    }
    if (asString(part.type) !== "thinking") {
      continue;
    }
    const chunk = asString(part.thinking) || asString(part.text);
    if (chunk.length > 0) {
      parts.push(chunk);
    }
  }
  return parts.join("\n").trim();
}

function wakeConversation(text: string): PiHydratedTurn["conversation"] {
  if (/\bkind:\s*a2a_handoff\b/i.test(text) || /\bconversation:\s*peer_dm\b/i.test(text)) {
    return "peer_dm";
  }
  if (/\bkind:\s*group_/i.test(text) || /\bconversation:\s*room\b/i.test(text)) {
    return "room";
  }
  return "operator_dm";
}

function wakeField(text: string, name: string): string | undefined {
  const match = new RegExp(`\\b${name}:\\s+(\\S+)`, "i").exec(text);
  const value = match?.[1];
  return value && value.length > 0 ? value : undefined;
}

/**
 * Fold Pi session jsonl (the files under pi-session/) into the same turn
 * shape as the RPC hydrate, including thinking blocks.
 */
export function hydrateSessionTurns(computerRoot: string, botId: string): PiHydratedTurn[] {
  const turns: PiHydratedTurn[] = [];
  for (const file of [...listPiSessions(computerRoot, botId)].reverse()) {
    const abs = join(piSessionDir(computerRoot, botId), file.name);
    let reasoning = "";
    let text = "";
    let tools: PiHydratedTool[] = [];
    let conversation: PiHydratedTurn["conversation"] = "operator_dm";
    let handleId: string | undefined;
    let fromId: string | undefined;
    const pending = new Map<string, number>();
    const finishAssistant = (): void => {
      if (reasoning.length === 0 && text.length === 0 && tools.length === 0) {
        return;
      }
      turns.push({
        reasoning,
        text,
        tools,
        conversation,
        ...(handleId ? { handleId } : {}),
        ...(fromId ? { fromId } : {}),
      });
      reasoning = "";
      text = "";
      tools = [];
      pending.clear();
    };
    for (const row of readJsonl(abs)) {
      if (!isRecord(row) || asString(row.type) !== "message") {
        continue;
      }
      const inner = isRecord(row.message) ? row.message : row;
      const role = asString(inner.role) || asString(row.role);
      if (role === "user") {
        finishAssistant();
        const wake = contentText(inner);
        conversation = wakeConversation(wake);
        handleId = wakeField(wake, "handle");
        fromId = wakeField(wake, "from");
        continue;
      }
      if (role === "assistant") {
        finishAssistant();
        const nextThinking = thinkingText(inner);
        if (nextThinking.length > 0) {
          reasoning = nextThinking;
        }
        const nextText = contentText(inner);
        if (nextText.length > 0) {
          text = nextText;
        }
        if (Array.isArray(inner.content)) {
          for (const part of inner.content) {
            if (!isRecord(part) || asString(part.type) !== "toolCall") {
              continue;
            }
            const callId = asString(part.id);
            const name = connectedName(asString(part.name), part.arguments);
            const input = stringifyUnknown(part.arguments);
            tools.push({
              id: callId.length > 0 ? callId : `tool-${tools.length}`,
              name,
              ok: true,
              ...(input.length > 0 ? { summary: clip(input, 8000), input: clip(input, 8000) } : {}),
            });
            if (callId.length > 0) {
              pending.set(callId, tools.length - 1);
            }
          }
        }
        continue;
      }
      if (role === "toolResult" || role === "tool") {
        const callId = asString(inner.toolCallId) || asString(row.toolCallId);
        const index = callId.length > 0 ? pending.get(callId) : undefined;
        const output = clip(toolResultText(inner), 8000);
        const ok = inner.isError !== true;
        if (index !== undefined) {
          const existing = tools[index];
          if (existing) {
            tools[index] = {
              ...existing,
              ok,
              ...(output.length > 0 ? { output } : {}),
            };
          }
        }
      }
    }
    finishAssistant();
  }
  return turns;
}

function clip(value: string, max: number): string {
  const trimmed = value.trim();
  if (trimmed.length <= max) {
    return trimmed;
  }
  return `${trimmed.slice(0, max - 1)}…`;
}

/**
 * Project a Bot's Pi session jsonl into the operator desk, message by message.
 * One assistant row stays one desk event — two Pi reasonings stay two events.
 */
import { join } from "node:path";

import { readJsonl } from "../fs.ts";
import { piSessionDir } from "../paths.ts";
import { findBot } from "../roster.ts";
import type { Roster } from "../types.ts";
import { pairChannelId } from "./pair-id.ts";
import { listPiSessions } from "./pi-sessions.ts";
import { listThreadFiles } from "./thread-log.ts";

const MAUS_COLORS = [
  "teal",
  "blue",
  "purple",
  "pink",
  "orange",
  "cyan",
  "green",
  "coral",
  "yellow",
  "red",
] as const;

type MausColor = (typeof MAUS_COLORS)[number];

const ASK_TOOLS = new Set(["ask_bot", "bot_ask", "bot_send_prompt"]);
const OPERATOR_TOOLS = new Set(["message_operator"]);

export interface DeskMessage {
  readonly id: string;
  readonly role: "bot" | "user";
  readonly kind: "text" | "activity";
  readonly text?: string;
  readonly reasoning?: string;
  readonly at: number;
  readonly peerAsk?: { readonly botId: string; readonly name: string };
  readonly comm?: {
    readonly groupId: string;
    readonly threadId?: string;
    readonly withBotId: string;
    readonly withName: string;
    readonly withColor: MausColor;
  };
  readonly tool?: {
    readonly name: string;
    readonly ok?: boolean;
    readonly spoken?: string;
    readonly summary?: string;
    readonly input?: string;
    readonly output?: string;
  };
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

function clip(value: string, max: number): string {
  const trimmed = value.trim();
  if (trimmed.length <= max) {
    return trimmed;
  }
  return `${trimmed.slice(0, max - 1)}…`;
}

function epoch(iso: string): number {
  const parsed = Date.parse(iso);
  return Number.isFinite(parsed) ? parsed : Date.now();
}

function colorFor(index: number): MausColor {
  return MAUS_COLORS[index % MAUS_COLORS.length] ?? "teal";
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

function wakeField(text: string, name: string): string | undefined {
  const match = new RegExp(`\\b${name}:\\s+(\\S+)`, "i").exec(text);
  const value = match?.[1];
  return value && value.length > 0 ? value : undefined;
}

function wakeKind(text: string): "operator_dm" | "peer_dm" | "room" {
  if (/\bkind:\s*a2a_handoff\b/i.test(text) || /\bconversation:\s*peer_dm\b/i.test(text)) {
    return "peer_dm";
  }
  if (/\bkind:\s*group_/i.test(text) || /\bconversation:\s*room\b/i.test(text)) {
    return "room";
  }
  return "operator_dm";
}

/** Strip the Harness wake header so the desk shows the prompt the Bot actually got. */
export function displayWake(text: string): string {
  const lines = text.replace(/^\uFEFF/, "").split(/\r?\n/);
  const body: string[] = [];
  let inHeader = lines[0]?.trim() === "[harness wake]";
  for (const line of lines) {
    const trimmed = line.trim();
    if (inHeader) {
      if (trimmed === "[harness wake]") {
        continue;
      }
      if (/^(kind|from|handle|conversation|paths):/i.test(trimmed)) {
        continue;
      }
      inHeader = false;
    }
    if (/^Required tool:/i.test(trimmed)) {
      continue;
    }
    if (trimmed === "---" || /^Harness note:/i.test(trimmed) || /^Tools:/i.test(trimmed)) {
      break;
    }
    if (/^Your assistant text is the reply/i.test(trimmed)) {
      break;
    }
    body.push(line);
  }
  const shown = body.join("\n").trim();
  return shown.length > 0 ? shown : text.trim();
}

function connectedName(rawName: string, args: unknown): string {
  if (rawName === "call_connected_tool" && isRecord(args) && asString(args.name).length > 0) {
    return asString(args.name);
  }
  return rawName.length > 0 ? rawName : "tool";
}

function handleFromResult(inner: Record<string, unknown>): string | undefined {
  if (isRecord(inner.details) && asString(inner.details.handleId).length > 0) {
    return asString(inner.details.handleId);
  }
  const raw = contentText(inner);
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (isRecord(parsed) && asString(parsed.handleId).length > 0) {
      return asString(parsed.handleId);
    }
  } catch {
    return undefined;
  }
  return undefined;
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

function commChip(
  roster: Roster,
  fromId: string,
  toId: string,
  handleId: string | undefined,
  recv: boolean,
): DeskMessage["comm"] | undefined {
  const from = findBot(roster, fromId);
  const peer = findBot(roster, toId);
  if (!from || !peer) {
    return undefined;
  }
  const shown = recv ? from : peer;
  const index = roster.bots.findIndex((bot) => bot.id === shown.id);
  return {
    groupId: pairChannelId(from.id, peer.id),
    ...(handleId ? { threadId: handleId } : {}),
    withBotId: shown.id,
    withName: shown.name,
    withColor: colorFor(index),
  };
}

function toolArgText(args: unknown): string {
  if (!isRecord(args)) {
    return "";
  }
  return asString(args.text) || asString(args.message);
}

function commChipsFromThreads(
  computerRoot: string,
  botId: string,
  roster: Roster,
): DeskMessage[] {
  const out: DeskMessage[] = [];
  for (const file of listThreadFiles(computerRoot)) {
    if (!file.memberIds.includes(botId)) {
      continue;
    }
    const otherId = file.memberIds.find((id) => id !== botId);
    if (!otherId) {
      continue;
    }
    for (const post of file.messages) {
      const outbound = post.from.botId === botId;
      const peer = findBot(roster, outbound ? otherId : post.from.botId);
      if (!peer) {
        continue;
      }
      const recv = !outbound;
      const comm = commChip(
        roster,
        outbound ? botId : post.from.botId,
        outbound ? otherId : botId,
        post.handleId,
        recv,
      );
      if (!comm) {
        continue;
      }
      out.push({
        id: outbound ? `comm-${post.id}` : `comm-recv-${post.id}`,
        role: "bot",
        kind: "activity",
        text: outbound ? `Messaged @${peer.name}` : `Message from @${peer.name}`,
        at: post.at,
        comm,
        tool: {
          name: outbound ? `Messaged @${peer.name}` : `Message from @${peer.name}`,
          ok: true,
        },
      });
    }
  }
  return out;
}

function mergeDesk(session: readonly DeskMessage[], chips: readonly DeskMessage[]): DeskMessage[] {
  const seen = new Set(session.map((row) => row.id));
  const extra = chips.filter((row) => !seen.has(row.id));
  return [...session, ...extra].sort((left, right) => {
    if (left.at !== right.at) {
      return left.at - right.at;
    }
    return left.id.localeCompare(right.id);
  });
}

/**
 * Operator DM from this Bot's session files plus pair-thread comm chips.
 * Peer wake bodies stay in the messages tab, not on this desk.
 */
export function projectSessionDesk(
  computerRoot: string,
  botId: string,
  roster: Roster,
): DeskMessage[] {
  const self = findBot(roster, botId);
  if (!self) {
    return [];
  }
  const files = [...listPiSessions(computerRoot, botId)].reverse();
  const out: DeskMessage[] = [];
  for (const file of files) {
    const abs = join(piSessionDir(computerRoot, botId), file.name);
    let wakeHandle: string | undefined;
    let wakeKindNow: "operator_dm" | "peer_dm" | "room" = "operator_dm";
    const pending = new Map<string, number>();
    for (const row of readJsonl(abs)) {
      if (!isRecord(row) || asString(row.type) !== "message") {
        continue;
      }
      const inner = isRecord(row.message) ? row.message : row;
      const role = asString(inner.role) || asString(row.role);
      const at = epoch(asString(row.timestamp));
      const rowId = asString(row.id) || `row-${out.length}`;
      if (role === "user") {
        const wake = contentText(inner);
        wakeKindNow = wakeKind(wake);
        wakeHandle = wakeField(wake, "handle");
        if (wakeKindNow === "peer_dm") {
          continue;
        }
        const text = displayWake(wake);
        if (text.length === 0) {
          continue;
        }
        out.push({
          id: wakeHandle && wakeKindNow === "operator_dm" ? wakeHandle : `sess-${rowId}`,
          role: "user",
          kind: "text",
          text,
          at,
        });
        continue;
      }
      if (role === "assistant") {
        const peerTurn = wakeKindNow === "peer_dm";
        if (!peerTurn) {
          const reasoning = thinkingText(inner);
          const text = contentText(inner);
          if (reasoning.length > 0 || text.length > 0) {
            out.push({
              id: `sess-${rowId}`,
              role: "bot",
              kind: "text",
              text,
              at,
              ...(reasoning.length > 0 ? { reasoning } : {}),
            });
          }
        }
        if (!Array.isArray(inner.content)) {
          continue;
        }
        for (const part of inner.content) {
          if (!isRecord(part) || asString(part.type) !== "toolCall") {
            continue;
          }
          const name = connectedName(asString(part.name), part.arguments);
          if (peerTurn && OPERATOR_TOOLS.has(name)) {
            const spoken = toolArgText(part.arguments);
            if (spoken.length > 0) {
              out.push({
                id: `sess-op-${rowId}`,
                role: "bot",
                kind: "text",
                text: spoken,
                at,
              });
            }
            continue;
          }
          if (peerTurn) {
            continue;
          }
          const callId = asString(part.id);
          const input = stringifyUnknown(part.arguments);
          const chipId = callId.length > 0 ? `tool-${callId}` : `tool-${rowId}-${out.length}`;
          out.push({
            id: chipId,
            role: "bot",
            kind: "activity",
            text: `Finished ${name}`,
            at,
            tool: {
              name,
              ok: true,
              spoken: `Finished ${name}`,
              ...(input.length > 0 ? { summary: clip(input, 8000), input: clip(input, 8000) } : {}),
            },
          });
          if (callId.length > 0) {
            pending.set(callId, out.length - 1);
          }
        }
        continue;
      }
      if (role === "toolResult" || role === "tool") {
        if (wakeKindNow === "peer_dm") {
          continue;
        }
        const callId = asString(inner.toolCallId) || asString(row.toolCallId);
        const index = callId.length > 0 ? pending.get(callId) : undefined;
        const output = clip(toolResultText(inner), 8000);
        const ok = inner.isError !== true;
        if (index !== undefined) {
          const existing = out[index];
          if (existing?.tool) {
            out[index] = {
              ...existing,
              text: ok ? `Finished ${existing.tool.name}` : `Failed ${existing.tool.name}`,
              tool: {
                ...existing.tool,
                ok,
                spoken: ok ? `Finished ${existing.tool.name}` : `Failed ${existing.tool.name}`,
                ...(output.length > 0 ? { output } : {}),
              },
            };
          }
        }
        const toolName = existingToolName(out, index) || asString(inner.toolName);
        if (ASK_TOOLS.has(toolName)) {
          const argsPeer = peerFromChip(out, index, roster);
          const handleId = handleFromResult(inner) ?? wakeHandle;
          if (argsPeer && handleId) {
            const comm = commChip(roster, botId, argsPeer.id, handleId, false);
            if (comm) {
              out.push({
                id: `comm-${handleId}`,
                role: "bot",
                kind: "activity",
                text: `Messaged @${argsPeer.name}`,
                at,
                comm,
                tool: { name: `Messaged @${argsPeer.name}`, ok: true },
              });
            }
          }
        }
      }
    }
  }
  return mergeDesk(out, commChipsFromThreads(computerRoot, botId, roster));
}

function existingToolName(out: readonly DeskMessage[], index: number | undefined): string {
  if (index === undefined) {
    return "";
  }
  return out[index]?.tool?.name ?? "";
}

function peerFromChip(
  out: readonly DeskMessage[],
  index: number | undefined,
  roster: Roster,
): { readonly id: string; readonly name: string } | undefined {
  if (index === undefined) {
    return undefined;
  }
  const input = out[index]?.tool?.input ?? out[index]?.tool?.summary ?? "";
  let parsed: unknown;
  try {
    parsed = JSON.parse(input) as unknown;
  } catch {
    parsed = undefined;
  }
  const key = isRecord(parsed) ? asString(parsed.bot_id) || asString(parsed.botId) : "";
  if (key.length === 0) {
    return undefined;
  }
  const bot = findBot(roster, key);
  return bot ? { id: bot.id, name: bot.name } : undefined;
}

/** Fold Pi RPC JSONL into Operator RuntimeEvent shapes the desk already renders. */

export type PiStreamKind = "assistant_text" | "reasoning_text";

export interface PiRuntimeEvent {
  readonly eventId: string;
  readonly provider: "pi";
  readonly threadId: string;
  readonly createdAt: string;
  readonly type: string;
  readonly streamKind?: PiStreamKind;
  readonly delta?: string;
  readonly itemType?: "tool" | "reasoning" | "assistant_text";
  readonly title?: string;
  readonly summary?: string;
  readonly ok?: boolean;
  readonly output?: string;
  readonly text?: string;
  readonly sessionId?: string | null;
  readonly model?: string | null;
  readonly stopReason?: string | null;
  readonly message?: string;
  readonly input?: number;
  readonly cachedInput?: number;
  readonly attempt?: number;
  readonly delayMs?: number;
  readonly reason?: string;
  readonly raw?: { readonly source: string; readonly payload: unknown };
  readonly usage?: {
    readonly input?: number;
    readonly output?: number;
    readonly cachedInput?: number;
  };
}

export interface PiActivityChip {
  readonly id: string;
  readonly name: string;
  readonly spoken: string;
  readonly ok?: boolean;
  readonly summary?: string;
  readonly input?: string;
  readonly output?: string;
}

export interface PiHydratedTool {
  readonly id: string;
  readonly name: string;
  readonly ok: boolean;
  readonly summary?: string;
  readonly input?: string;
  readonly output?: string;
}

export interface PiHydratedTurn {
  readonly reasoning: string;
  readonly text: string;
  readonly tools: readonly PiHydratedTool[];
  readonly conversation: "operator_dm" | "peer_dm" | "room";
  readonly handleId?: string;
  readonly fromId?: string;
}

export interface FoldedPiChunk {
  readonly events: readonly PiRuntimeEvent[];
  readonly activity?: PiActivityChip;
}

export interface FoldPiContext {
  readonly botId: string;
  readonly slug: string;
  readonly now: () => string;
  readonly nextId: () => string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

const TOOL_OUTPUT_CHARS = 8000;

function clip(value: string, max = 400): string {
  const trimmed = value.trim();
  if (trimmed.length <= max) {
    return trimmed;
  }
  return `${trimmed.slice(0, max - 1)}…`;
}

function usageFields(raw: unknown): {
  readonly input?: number;
  readonly output?: number;
  readonly cachedInput?: number;
} {
  if (!isRecord(raw)) {
    return {};
  }
  const input = typeof raw.input === "number" ? raw.input : undefined;
  const output = typeof raw.output === "number" ? raw.output : undefined;
  const cachedInput = typeof raw.cacheRead === "number" ? raw.cacheRead : undefined;
  return {
    ...(input !== undefined ? { input } : {}),
    ...(output !== undefined ? { output } : {}),
    ...(cachedInput !== undefined ? { cachedInput } : {}),
  };
}

function baseEvent(
  ctx: FoldPiContext,
  type: string,
  raw: unknown,
  extra: Partial<PiRuntimeEvent> = {},
): PiRuntimeEvent {
  return {
    eventId: ctx.nextId(),
    provider: "pi",
    threadId: ctx.botId,
    createdAt: ctx.now(),
    type,
    raw: { source: "pi-rpc", payload: raw },
    ...extra,
  };
}

function assistantEvent(raw: Record<string, unknown>): Record<string, unknown> | undefined {
  if (isRecord(raw.assistantMessageEvent)) {
    return raw.assistantMessageEvent;
  }
  if (isRecord(raw.event) && isRecord(raw.event.assistantMessageEvent)) {
    return raw.event.assistantMessageEvent;
  }
  return undefined;
}

function argsRecord(
  raw: Record<string, unknown>,
  nested?: Record<string, unknown>,
): Record<string, unknown> | undefined {
  if (nested && isRecord(nested.arguments)) {
    return nested.arguments;
  }
  if (nested && isRecord(nested.args)) {
    return nested.args;
  }
  if (isRecord(raw.args)) {
    return raw.args;
  }
  if (isRecord(raw.arguments)) {
    return raw.arguments;
  }
  return undefined;
}

function toolNameOf(raw: Record<string, unknown>, nested?: Record<string, unknown>): string {
  const fromNested = nested ? asString(nested.toolName) || asString(nested.name) : "";
  const named = fromNested.length > 0 ? fromNested : asString(raw.toolName) || asString(raw.name);
  const args = argsRecord(raw, nested);
  const inner = args ? asString(args.name) : "";
  if (named === "call_connected_tool" && inner.length > 0) {
    return inner;
  }
  if (named.length > 0) {
    return named;
  }
  return inner.length > 0 ? inner : "tool";
}

function toolIdOf(raw: Record<string, unknown>, nested?: Record<string, unknown>, fallback = ""): string {
  const fromNested = nested ? asString(nested.toolCallId) || asString(nested.id) : "";
  if (fromNested.length > 0) {
    return fromNested;
  }
  const fromRaw = asString(raw.toolCallId) || asString(raw.id);
  if (fromRaw.length > 0) {
    return fromRaw;
  }
  return fallback;
}

function stringifyUnknown(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  if (value === undefined || value === null) {
    return "";
  }
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function contentParts(message: unknown): readonly Record<string, unknown>[] {
  if (!isRecord(message) || !Array.isArray(message.content)) {
    return [];
  }
  return message.content.filter((part): part is Record<string, unknown> => isRecord(part));
}

function assistantTextFromMessage(message: unknown): string {
  let text = "";
  for (const part of contentParts(message)) {
    if (asString(part.type) === "text" && asString(part.text).length > 0) {
      text = asString(part.text);
    }
  }
  return text;
}

function assistantThinkingFromMessage(message: unknown): string {
  let thinking = "";
  for (const part of contentParts(message)) {
    if (asString(part.type) === "thinking" && asString(part.thinking).length > 0) {
      thinking = asString(part.thinking);
    }
  }
  return thinking;
}

/**
 * Map one Pi RPC JSON object to desk RuntimeEvents. Unknown lines still
 * become a typed `runtime.error` only when Pi itself reports failure.
 */
export function foldPiRpc(raw: unknown, ctx: FoldPiContext): FoldedPiChunk {
  if (!isRecord(raw)) {
    return { events: [] };
  }
  const type = asString(raw.type);
  const events: PiRuntimeEvent[] = [];

  if (type === "agent_start" || type === "turn_start") {
    events.push(baseEvent(ctx, "turn.started", raw));
    return { events };
  }

  if (type === "agent_settled") {
    events.push(
      baseEvent(ctx, "turn.completed", raw, {
        ok: true,
        stopReason: type,
        usage: usageFields(raw.usage),
      }),
    );
    return { events };
  }

  if (type === "turn_end") {
    const text = assistantTextFromMessage(raw.message);
    events.push(
      baseEvent(ctx, "item.completed", raw, {
        itemType: "assistant_text",
        ...(text.length > 0 ? { text } : {}),
        stopReason: "turn_end",
      }),
    );
    return { events };
  }

  if (type === "agent_end") {
    const willRetry = raw.willRetry === true;
    events.push(
      baseEvent(ctx, willRetry ? "turn.retrying" : "turn.completed", raw, {
        ok: !willRetry,
        stopReason: willRetry ? "retry" : "agent_end",
        ...(willRetry ? { attempt: 1, delayMs: 0, reason: "willRetry" } : {}),
        usage: usageFields(raw.usage),
      }),
    );
    return { events };
  }

  if (type === "message_update") {
    const inner = assistantEvent(raw);
    const innerType = inner ? asString(inner.type) : "";
    const delta = inner ? asString(inner.delta) : "";
    if (innerType === "text_delta" && delta.length > 0) {
      events.push(
        baseEvent(ctx, "content.delta", raw, {
          streamKind: "assistant_text",
          delta,
          usage: usageFields(raw.usage),
        }),
      );
    } else if (innerType === "thinking_delta" && delta.length > 0) {
      events.push(
        baseEvent(ctx, "content.delta", raw, {
          streamKind: "reasoning_text",
          delta,
          usage: usageFields(raw.usage),
        }),
      );
    } else if (innerType === "thinking_start") {
      events.push(baseEvent(ctx, "item.started", raw, { itemType: "reasoning", title: "reasoning" }));
    } else if (innerType === "thinking_end" && asString(inner?.content).length > 0) {
      events.push(
        baseEvent(ctx, "item.completed", raw, {
          itemType: "reasoning",
          text: asString(inner?.content),
        }),
      );
    } else if (innerType === "toolcall_start") {
      const name = toolNameOf(raw, inner);
      const id = toolIdOf(raw, inner);
      events.push(baseEvent(ctx, "item.started", raw, { itemType: "tool", title: name, summary: name }));
      if (id.length === 0) {
        return { events };
      }
      return {
        events,
        activity: { id, name, spoken: `Calling ${name}` },
      };
    } else if (innerType === "text_end" && asString(inner?.content).length > 0) {
      events.push(
        baseEvent(ctx, "item.completed", raw, {
          itemType: "assistant_text",
          text: asString(inner?.content),
        }),
      );
    }
    return { events };
  }

  if (type === "tool_execution_start") {
    const name = toolNameOf(raw);
    const id = toolIdOf(raw);
    const summary = clip(stringifyUnknown(raw.args), 200);
    const input = clip(stringifyUnknown(raw.args), TOOL_OUTPUT_CHARS);
    events.push(baseEvent(ctx, "item.started", raw, { itemType: "tool", title: name, summary }));
    if (id.length === 0) {
      return { events };
    }
    return {
      events,
      activity: { id, name, spoken: `Running ${name}`, summary, input },
    };
  }

  if (type === "tool_execution_end") {
    const name = toolNameOf(raw);
    const id = toolIdOf(raw);
    const ok = raw.isError !== true;
    const output = clip(stringifyUnknown(raw.result), TOOL_OUTPUT_CHARS);
    events.push(baseEvent(ctx, "item.completed", raw, { itemType: "tool", ok, output, title: name }));
    if (id.length === 0) {
      return { events };
    }
    return {
      events,
      activity: { id, name, spoken: ok ? `Finished ${name}` : `Failed ${name}`, ok, output },
    };
  }

  if (type === "extension_error" || type === "error") {
    const message = asString(raw.message) || clip(stringifyUnknown(raw), 240);
    events.push(baseEvent(ctx, "runtime.error", raw, { message }));
    return { events };
  }

  return { events };
}

interface MutableHydratedTurn {
  reasoning: string;
  text: string;
  tools: PiHydratedTool[];
  conversation: "operator_dm" | "peer_dm" | "room";
  handleId?: string;
  fromId?: string;
}

function wakeConversation(text: string): "operator_dm" | "peer_dm" | "room" {
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

function applyWake(turn: MutableHydratedTurn, text: string): void {
  turn.conversation = wakeConversation(text);
  const handleId = wakeField(text, "handle");
  const fromId = wakeField(text, "from");
  if (handleId) {
    turn.handleId = handleId;
  }
  if (fromId) {
    turn.fromId = fromId;
  }
}

function absorbAssistantMessage(turn: MutableHydratedTurn, message: unknown): void {
  const thinking = assistantThinkingFromMessage(message);
  if (thinking.length > turn.reasoning.length) {
    turn.reasoning = thinking;
  }
  const text = assistantTextFromMessage(message);
  if (text.length > 0) {
    turn.text = text;
  }
}

/**
 * Rebuild one desk turn (reasoning, Kernel tools, assistant text) from the
 * Pi RPC log so a reload still shows the debug transcript.
 */
export function hydratePiTurns(rows: readonly unknown[]): PiHydratedTurn[] {
  const turns: PiHydratedTurn[] = [];
  let current: MutableHydratedTurn | undefined;

  const start = (): MutableHydratedTurn => {
    current = { reasoning: "", text: "", tools: [], conversation: "operator_dm" };
    return current;
  };
  const finish = (): void => {
    if (!current) {
      return;
    }
    if (current.reasoning.length > 0 || current.text.length > 0 || current.tools.length > 0) {
      turns.push({
        reasoning: current.reasoning,
        text: current.text,
        tools: current.tools,
        conversation: current.conversation,
        ...(current.handleId ? { handleId: current.handleId } : {}),
        ...(current.fromId ? { fromId: current.fromId } : {}),
      });
    }
    current = undefined;
  };

  for (const raw of rows) {
    if (!isRecord(raw)) {
      continue;
    }
    const type = asString(raw.type);
    if (type === "agent_start") {
      finish();
      start();
      continue;
    }
    if (type === "message_start" || type === "message_end") {
      const message = raw.message;
      if (isRecord(message) && asString(message.role) === "user") {
        const turn = current ?? start();
        applyWake(turn, assistantTextFromMessage(message));
      }
      continue;
    }
    const turn = current ?? start();
    if (type === "message_update") {
      const inner = assistantEvent(raw);
      const innerType = inner ? asString(inner.type) : "";
      if (innerType === "thinking_delta") {
        turn.reasoning += asString(inner?.delta);
      } else if (innerType === "thinking_end" && asString(inner?.content).length > 0) {
        turn.reasoning = asString(inner?.content);
      } else if (innerType === "text_delta") {
        turn.text += asString(inner?.delta);
      } else if (innerType === "text_end" && asString(inner?.content).length > 0) {
        turn.text = asString(inner?.content);
      }
    } else if (type === "tool_execution_start") {
      const id = toolIdOf(raw);
      const name = toolNameOf(raw);
      const input = clip(stringifyUnknown(raw.args), TOOL_OUTPUT_CHARS);
      turn.tools.push({
        id: id.length > 0 ? id : `tool-${turn.tools.length}`,
        name,
        ok: true,
        ...(input.length > 0 ? { summary: input, input } : {}),
      });
    } else if (type === "tool_execution_end") {
      const id = toolIdOf(raw);
      const name = toolNameOf(raw);
      const ok = raw.isError !== true;
      const output = clip(stringifyUnknown(raw.result), TOOL_OUTPUT_CHARS);
      const existing = [...turn.tools].reverse().find((tool) => tool.id === id || tool.name === name);
      if (existing) {
        const index = turn.tools.lastIndexOf(existing);
        turn.tools[index] = {
          ...existing,
          ok,
          ...(output.length > 0 ? { output } : {}),
        };
      } else {
        turn.tools.push({
          id: id.length > 0 ? id : `tool-${turn.tools.length}`,
          name,
          ok,
          ...(output.length > 0 ? { output } : {}),
        });
      }
    } else if (type === "turn_end") {
      absorbAssistantMessage(turn, raw.message);
    } else if (type === "agent_end") {
      if (Array.isArray(raw.messages)) {
        for (const message of raw.messages) {
          if (isRecord(message) && asString(message.role) === "user") {
            applyWake(turn, assistantTextFromMessage(message));
          } else if (isRecord(message) && asString(message.role) === "assistant") {
            absorbAssistantMessage(turn, message);
          }
        }
      }
      finish();
    } else if (type === "agent_settled") {
      finish();
    }
  }
  finish();
  return turns;
}

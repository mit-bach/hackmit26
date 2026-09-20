import assert from "node:assert/strict";
import { test } from "node:test";

import { piModelArg } from "../src/server/supervisor.ts";
import { foldPiRpc, hydratePiTurns, type FoldPiContext } from "../src/server/pi-runtime.ts";

function ctx(): FoldPiContext {
  let n = 0;
  return {
    botId: "bot_email",
    slug: "email",
    now: (): string => "2026-09-20T00:00:00.000Z",
    nextId: (): string => `e${++n}`,
  };
}

test("foldPiRpc maps text and thinking deltas onto content.delta with a threadId", () => {
  const text = foldPiRpc(
    {
      type: "message_update",
      assistantMessageEvent: { type: "text_delta", delta: "office-ok" },
    },
    ctx(),
  );
  assert.equal(text.events.length, 1);
  assert.equal(text.events[0]?.type, "content.delta");
  assert.equal(text.events[0]?.streamKind, "assistant_text");
  assert.equal(text.events[0]?.delta, "office-ok");
  assert.equal(text.events[0]?.threadId, "bot_email");

  const thought = foldPiRpc(
    {
      type: "message_update",
      assistantMessageEvent: { type: "thinking_delta", delta: "The user wants a reply." },
    },
    ctx(),
  );
  assert.equal(thought.events[0]?.streamKind, "reasoning_text");
  assert.equal(thought.events[0]?.delta, "The user wants a reply.");
});

test("foldPiRpc turns Kernel tool execution into live activity chips", () => {
  const start = foldPiRpc(
    { type: "tool_execution_start", toolCallId: "call_1", toolName: "call_connected_tool", args: { name: "list_email_candidates" } },
    ctx(),
  );
  assert.equal(start.events[0]?.type, "item.started");
  assert.equal(start.activity?.name, "list_email_candidates");
  assert.equal(start.activity?.id, "call_1");

  const end = foldPiRpc(
    { type: "tool_execution_end", toolCallId: "call_1", toolName: "call_connected_tool", result: { ok: true }, isError: false },
    ctx(),
  );
  assert.equal(end.events[0]?.type, "item.completed");
  assert.equal(end.activity?.ok, true);
  assert.equal(end.activity?.id, "call_1");
});

test("foldPiRpc toolcall_start and execution share one toolCallId", () => {
  const begin = foldPiRpc(
    {
      type: "message_update",
      assistantMessageEvent: {
        type: "toolcall_start",
        id: "call_1",
        name: "call_connected_tool",
        arguments: { name: "list_email_candidates" },
      },
    },
    ctx(),
  );
  assert.equal(begin.activity?.id, "call_1");
  assert.equal(begin.activity?.name, "list_email_candidates");
  const start = foldPiRpc(
    { type: "tool_execution_start", toolCallId: "call_1", toolName: "call_connected_tool", args: { name: "list_email_candidates" } },
    ctx(),
  );
  assert.equal(start.activity?.id, begin.activity?.id);
});

test("foldPiRpc ignores noise and maps agent_settled to turn.completed", () => {
  assert.deepEqual(foldPiRpc({ type: "queue_update" }, ctx()).events, []);
  const settled = foldPiRpc({ type: "agent_settled" }, ctx());
  assert.equal(settled.events[0]?.type, "turn.completed");
  assert.equal(settled.events[0]?.ok, true);
  const step = foldPiRpc(
    { type: "turn_end", message: { role: "assistant", content: [{ type: "text", text: "office-ok" }] } },
    ctx(),
  );
  assert.equal(step.events[0]?.type, "item.completed");
  assert.notEqual(step.events[0]?.type, "turn.completed");
});

test("hydratePiTurns keeps reasoning, Kernel tools, and assistant text together", () => {
  const turns = hydratePiTurns([
    { type: "agent_start" },
    { type: "message_update", assistantMessageEvent: { type: "thinking_end", content: "Need the catalog." } },
    { type: "tool_execution_start", toolCallId: "call_1", toolName: "search_connected_tools", args: { query: "email" } },
    { type: "tool_execution_end", toolCallId: "call_1", toolName: "search_connected_tools", result: { ok: true }, isError: false },
    {
      type: "agent_end",
      messages: [
        { role: "assistant", content: [{ type: "thinking", thinking: "Need the catalog." }, { type: "text", text: "Found tools." }] },
      ],
    },
  ]);
  assert.equal(turns.length, 1);
  assert.equal(turns[0]?.reasoning, "Need the catalog.");
  assert.equal(turns[0]?.text, "Found tools.");
  assert.equal(turns[0]?.tools[0]?.name, "search_connected_tools");
  assert.equal(turns[0]?.tools[0]?.ok, true);
  assert.equal(turns[0]?.conversation, "operator_dm");
});

test("hydratePiTurns marks a2a wakes as peer_dm", () => {
  const turns = hydratePiTurns([
    { type: "agent_start" },
    {
      type: "message_start",
      message: {
        role: "user",
        content: [{ type: "text", text: "[harness wake]\nkind: a2a_handoff\nfrom: bot_email\nconversation: peer_dm\nWhat color is the sky?" }],
      },
    },
    {
      type: "agent_end",
      messages: [{ role: "assistant", content: [{ type: "text", text: "Blue." }] }],
    },
  ]);
  assert.equal(turns.length, 1);
  assert.equal(turns[0]?.conversation, "peer_dm");
  assert.equal(turns[0]?.text, "Blue.");
});

test("piModelArg appends thinking only when the model has no suffix", () => {
  assert.equal(piModelArg("grok-4.5", "low"), "grok-4.5:low");
  assert.equal(piModelArg("grok-4.5:medium", "low"), "grok-4.5:medium");
  assert.equal(piModelArg(undefined, "low"), undefined);
});

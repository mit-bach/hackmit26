import assert from "node:assert/strict";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

import { piSessionDir } from "../src/paths.ts";
import { listPiSessions, readPiSession, hydrateSessionTurns } from "../src/server/pi-sessions.ts";
import { makeComputer } from "./helpers.ts";

test("listPiSessions and readPiSession parse a Computer pi-session jsonl", () => {
  const computer = makeComputer();
  const botId = "bot_alpha";
  const dir = piSessionDir(computer, botId);
  mkdirSync(dir, { recursive: true });
  const name = "2026-09-20T03-28-17-373Z_sess.jsonl";
  writeFileSync(
    join(dir, name),
    [
      JSON.stringify({
        type: "session",
        version: 3,
        id: "sess-1",
        timestamp: "2026-09-20T03:28:17.373Z",
      }),
      JSON.stringify({
        type: "message",
        id: "u1",
        timestamp: "2026-09-20T03:28:17.739Z",
        message: { role: "user", content: [{ type: "text", text: "list the invoices" }] },
      }),
      JSON.stringify({
        type: "message",
        id: "a1",
        timestamp: "2026-09-20T03:28:19.400Z",
        message: {
          role: "assistant",
          content: [
            { type: "text", text: "Calling list_email_candidates." },
            {
              type: "toolCall",
              id: "call_1",
              name: "call_connected_tool",
              arguments: { name: "list_email_candidates" },
            },
          ],
        },
      }),
      JSON.stringify({
        type: "message",
        id: "t1",
        timestamp: "2026-09-20T03:28:19.433Z",
        message: {
          role: "toolResult",
          toolCallId: "call_1",
          toolName: "call_connected_tool",
          content: [{ type: "text", text: "{\"ok\":true}" }],
        },
      }),
      "",
    ].join("\n"),
  );

  const listed = listPiSessions(computer, botId);
  assert.equal(listed.length, 1);
  assert.equal(listed[0]?.id, "sess-1");
  assert.equal(listed[0]?.messageCount, 3);
  assert.ok(listed[0]?.path.includes("pi-session"));

  const body = readPiSession(computer, botId, name);
  assert.ok(body);
  assert.equal(body?.turns.length, 3);
  assert.equal(body?.turns[0]?.role, "user");
  assert.equal(body?.turns[1]?.role, "assistant");
  assert.equal(body?.turns[2]?.role, "tool");
  assert.equal(body?.turns[2]?.toolName, "list_email_candidates");
  assert.equal(readPiSession(computer, botId, "../escape.jsonl"), undefined);
});

test("hydrateSessionTurns keeps thinking and peer_dm handle fields", () => {
  const computer = makeComputer();
  const botId = "bot_alpha";
  const dir = piSessionDir(computer, botId);
  mkdirSync(dir, { recursive: true });
  writeFileSync(
    join(dir, "peer.jsonl"),
    [
      JSON.stringify({ type: "session", id: "sess-peer", timestamp: "2026-09-20T00:00:00.000Z" }),
      JSON.stringify({
        type: "message",
        message: {
          role: "user",
          content: [
            {
              type: "text",
              text: "[harness wake]\nkind: a2a_handoff\nfrom: bot_email\nhandle: h_sky\nconversation: peer_dm\n\nWhat color is the sky?",
            },
          ],
        },
      }),
      JSON.stringify({
        type: "message",
        message: {
          role: "assistant",
          content: [
            { type: "thinking", thinking: "Clear daylight is blue." },
            { type: "text", text: "Blue." },
          ],
        },
      }),
      "",
    ].join("\n"),
  );
  const turns = hydrateSessionTurns(computer, botId);
  assert.equal(turns.length, 1);
  assert.equal(turns[0]?.conversation, "peer_dm");
  assert.equal(turns[0]?.handleId, "h_sky");
  assert.equal(turns[0]?.fromId, "bot_email");
  assert.equal(turns[0]?.reasoning, "Clear daylight is blue.");
  assert.equal(turns[0]?.text, "Blue.");
});

test("hydrateSessionTurns keeps two assistant messages as two turns", () => {
  const computer = makeComputer();
  const botId = "bot_alpha";
  const dir = piSessionDir(computer, botId);
  mkdirSync(dir, { recursive: true });
  writeFileSync(
    join(dir, "two.jsonl"),
    [
      JSON.stringify({ type: "session", id: "sess-two", timestamp: "2026-09-20T00:00:00.000Z" }),
      JSON.stringify({
        type: "message",
        message: { role: "user", content: [{ type: "text", text: "ask beta" }] },
      }),
      JSON.stringify({
        type: "message",
        message: {
          role: "assistant",
          content: [
            { type: "thinking", thinking: "first thought" },
            { type: "text", text: "asking" },
            { type: "toolCall", id: "c1", name: "ask_bot", arguments: { bot_id: "beta" } },
          ],
        },
      }),
      JSON.stringify({
        type: "message",
        message: {
          role: "assistant",
          content: [
            { type: "thinking", thinking: "second thought" },
            { type: "text", text: "they said blue" },
          ],
        },
      }),
      "",
    ].join("\n"),
  );
  const turns = hydrateSessionTurns(computer, botId);
  assert.equal(turns.length, 2);
  assert.equal(turns[0]?.reasoning, "first thought");
  assert.equal(turns[0]?.text, "asking");
  assert.equal(turns[1]?.reasoning, "second thought");
  assert.equal(turns[1]?.text, "they said blue");
});

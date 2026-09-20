import assert from "node:assert/strict";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

import { piSessionDir } from "../src/paths.ts";
import { loadRoster } from "../src/roster.ts";
import { displayWake, projectSessionDesk } from "../src/server/session-desk.ts";
import { makeComputer } from "./helpers.ts";

test("displayWake strips the harness header and pair-thread note", () => {
  const shown = displayWake(
    [
      "[harness wake]",
      "kind: a2a_handoff",
      "from: bot_email",
      "handle: h_sky",
      "conversation: peer_dm",
      "What color is the sky?",
      "---",
      "Harness note: Your assistant text is the reply in the pair thread.",
    ].join("\n"),
  );
  assert.equal(shown, "What color is the sky?");
});

test("projectSessionDesk keeps both Pi reasonings in session order plus the thread chip", () => {
  const computer = makeComputer();
  const botId = "bot_alpha";
  const dir = piSessionDir(computer, botId);
  mkdirSync(dir, { recursive: true });
  writeFileSync(
    join(dir, "2026-09-20T10-38-42-926Z_sess.jsonl"),
    [
      JSON.stringify({ type: "session", id: "sess-email", timestamp: "2026-09-20T10:38:42.926Z" }),
      JSON.stringify({
        type: "message",
        id: "u1",
        timestamp: "2026-09-20T10:38:43.252Z",
        message: {
          role: "user",
          content: [
            {
              type: "text",
              text: "[harness wake]\nkind: user_dm\nfrom: operator\nhandle: h_op\nconversation: operator_dm\nI want you to ask the AP agent what color the sky is.",
            },
          ],
        },
      }),
      JSON.stringify({
        type: "message",
        id: "a1",
        timestamp: "2026-09-20T10:38:45.123Z",
        message: {
          role: "assistant",
          content: [
            { type: "thinking", thinking: "The operator wants me to ask the AP agent." },
            { type: "text", text: "Asking AP what color the sky is." },
            {
              type: "toolCall",
              id: "call-ask",
              name: "ask_bot",
              arguments: { bot_id: "beta", prompt: "What color is the sky?" },
            },
          ],
        },
      }),
      JSON.stringify({
        type: "message",
        id: "t1",
        timestamp: "2026-09-20T10:38:49.354Z",
        message: {
          role: "toolResult",
          toolCallId: "call-ask",
          toolName: "ask_bot",
          content: [
            {
              type: "text",
              text: JSON.stringify({ accepted: true, handleId: "h_peer", done: true, result: "Blue." }),
            },
          ],
          details: { accepted: true, handleId: "h_peer", done: true, result: "Blue." },
          isError: false,
        },
      }),
      JSON.stringify({
        type: "message",
        id: "a2",
        timestamp: "2026-09-20T10:38:50.873Z",
        message: {
          role: "assistant",
          content: [
            { type: "thinking", thinking: "I got the answer from AP." },
            { type: "text", text: "AP’s answer: **Blue**." },
          ],
        },
      }),
      "",
    ].join("\n"),
  );

  const rows = projectSessionDesk(computer, botId, loadRoster(computer));
  const kinds = rows.map((row) => `${row.role}:${row.kind}:${row.tool?.name ?? row.text?.slice(0, 24) ?? ""}`);
  assert.equal(rows[0]?.role, "user");
  assert.match(rows[0]?.text ?? "", /ask the AP agent/i);
  assert.match(rows[1]?.reasoning ?? "", /operator wants me to ask/);
  assert.match(rows[1]?.text ?? "", /Asking AP/);
  assert.equal(rows[2]?.tool?.name, "ask_bot");
  assert.equal(rows[3]?.comm?.withBotId, "bot_beta");
  assert.match(rows[3]?.text ?? "", /Messaged @Beta/);
  assert.match(rows[4]?.reasoning ?? "", /I got the answer from AP/);
  assert.match(rows[4]?.text ?? "", /Blue/);
  assert.equal(rows.filter((row) => (row.reasoning ?? "").length > 0).length, 2);
  assert.ok(kinds.length >= 5);
});

test("projectSessionDesk shows a peer wake and the Bot's reply on the operator desk", () => {
  const computer = makeComputer();
  const botId = "bot_beta";
  const dir = piSessionDir(computer, botId);
  mkdirSync(dir, { recursive: true });
  writeFileSync(
    join(dir, "peer.jsonl"),
    [
      JSON.stringify({ type: "session", id: "sess-ap", timestamp: "2026-09-20T10:38:47.000Z" }),
      JSON.stringify({
        type: "message",
        id: "u1",
        timestamp: "2026-09-20T10:38:47.166Z",
        message: {
          role: "user",
          content: [
            {
              type: "text",
              text: "[harness wake]\nkind: a2a_handoff\nfrom: bot_alpha\nhandle: h_sky\nconversation: peer_dm\nWhat color is the sky?",
            },
          ],
        },
      }),
      JSON.stringify({
        type: "message",
        id: "a1",
        timestamp: "2026-09-20T10:38:49.205Z",
        message: {
          role: "assistant",
          content: [
            { type: "thinking", thinking: "Answer directly." },
            { type: "text", text: "Blue (in clear daylight)." },
          ],
        },
      }),
      "",
    ].join("\n"),
  );
  const rows = projectSessionDesk(computer, botId, loadRoster(computer));
  assert.ok(rows.some((row) => row.role === "user" && /sky/.test(row.text ?? "")));
  assert.ok(rows.some((row) => row.peerAsk?.botId === "bot_alpha"));
  assert.ok(rows.some((row) => row.comm && /Message from @Alpha/.test(row.text ?? "")));
  assert.ok(rows.some((row) => /Blue/.test(row.text ?? "") && /Answer directly/.test(row.reasoning ?? "")));
});

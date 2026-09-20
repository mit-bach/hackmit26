import assert from "node:assert/strict";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

import { askPeer } from "../src/ask-peer.ts";
import { piSessionDir } from "../src/paths.ts";
import { readProtocol } from "../src/protocol-log.ts";
import { loadRoster } from "../src/roster.ts";
import {
  getPairChannel,
  isPairChannelId,
  isPeerHandoff,
  listPairChannels,
  pairChannelId,
} from "../src/server/pair-channels.ts";
import { startFakeWorkers } from "../src/worker.ts";
import { makeComputer } from "./helpers.ts";

test("pairChannelId is order-independent", () => {
  assert.equal(pairChannelId("bot_email", "bot_ap"), pairChannelId("bot_ap", "bot_email"));
  assert.equal(isPairChannelId("pair:bot_ap:bot_email"), true);
  assert.equal(isPairChannelId("bot_ap"), false);
});

test("listPairChannels projects Alpha→Beta handoff as a read-only dm group", async () => {
  const computer = makeComputer();
  const workers = startFakeWorkers(computer, ["beta"], async (slug, item) => ({
    text: `${slug} says blue for: ${item.prompt}`,
    paths: [],
  }));
  const answered = await askPeer({
    computerRoot: computer,
    from: "alpha",
    to: "beta",
    prompt: "what color is the sky",
    timeoutMs: 4000,
  });
  workers.stop();
  assert.equal(answered.done, true);

  const roster = loadRoster(computer);
  assert.equal(isPeerHandoff(roster, "bot_alpha", "bot_beta"), true);
  assert.equal(isPeerHandoff(roster, "operator", "bot_beta"), false);
  const channels = listPairChannels(computer, roster);
  assert.equal(channels.length, 1);
  const channel = channels[0];
  assert.ok(channel);
  assert.equal(channel.dm, true);
  assert.equal(channel.id, pairChannelId("bot_alpha", "bot_beta"));
  assert.equal(channel.name, "Alpha ↔ Beta");
  assert.deepEqual([...channel.memberIds].sort(), ["bot_alpha", "bot_beta"]);
  assert.ok(channel.messages.some((row) => row.from.botId === "bot_alpha" && /sky/.test(row.text)));
  assert.ok(channel.messages.some((row) => row.from.botId === "bot_beta" && /blue/.test(row.text)));
  assert.equal(getPairChannel(computer, channel.id, roster)?.id, channel.id);
  assert.equal(channel.messages[0]?.parentId, null);
});

test("listPairChannels is the thread JSON of ask prompt and peer reply, not session thinking", async () => {
  const computer = makeComputer();
  const workers = startFakeWorkers(computer, ["beta"], async (slug, item) => ({
    text: `${slug} says blue for: ${item.prompt}`,
    paths: [],
  }));
  const answered = await askPeer({
    computerRoot: computer,
    from: "alpha",
    to: "beta",
    prompt: "what color is the sky",
    timeoutMs: 4000,
  });
  workers.stop();
  assert.equal(answered.done, true);
  const handleId = readProtocol(computer).find((event) => event.type === "send.accepted")?.handleId;
  assert.ok(handleId);
  const dir = piSessionDir(computer, "bot_beta");
  mkdirSync(dir, { recursive: true });
  writeFileSync(
    join(dir, "2026-09-20T00-00-00-000Z_sess.jsonl"),
    [
      JSON.stringify({ type: "session", id: "sess-pair", timestamp: "2026-09-20T00:00:00.000Z" }),
      JSON.stringify({
        type: "message",
        id: "u1",
        timestamp: "2026-09-20T00:00:01.000Z",
        message: {
          role: "user",
          content: [
            {
              type: "text",
              text: `[harness wake]\nkind: a2a_handoff\nfrom: bot_alpha\nhandle: ${handleId}\nconversation: peer_dm\n\nwhat color is the sky`,
            },
          ],
        },
      }),
      JSON.stringify({
        type: "message",
        id: "a1",
        timestamp: "2026-09-20T00:00:02.000Z",
        message: {
          role: "assistant",
          content: [
            { type: "thinking", thinking: "AP is considering daylight and Rayleigh scattering." },
            { type: "text", text: "beta says blue for: what color is the sky" },
          ],
        },
      }),
      "",
    ].join("\n"),
  );
  const roster = loadRoster(computer);
  const channel = listPairChannels(computer, roster)[0];
  assert.ok(channel);
  assert.equal(channel.messages.length, 2);
  assert.ok(channel.messages.some((row) => row.from.botId === "bot_alpha" && /sky/.test(row.text)));
  assert.ok(channel.messages.some((row) => row.from.botId === "bot_beta" && /blue/.test(row.text)));
  assert.equal(
    channel.messages.some((row) => /Rayleigh/.test(row.reasoning ?? "") || /Rayleigh/.test(row.text)),
    false,
  );
  assert.equal(
    channel.messages.some((row) => row.kind === "activity"),
    false,
  );
});

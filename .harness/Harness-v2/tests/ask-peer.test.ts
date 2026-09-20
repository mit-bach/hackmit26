import assert from "node:assert/strict";
import { test } from "node:test";

import { awaitTurn } from "../src/await.ts";
import { findHandle } from "../src/handle.ts";
import { bindLane, completeTurn, formatWake, startNextTurn } from "../src/lane.ts";
import { askPeer, executeFakeTurn, parseAskPeer, sendBotMessage, tryOperatorAskHandoff } from "../src/ask-peer.ts";
import { readProtocol } from "../src/protocol-log.ts";
import { findBot, loadRoster } from "../src/roster.ts";
import { roomPost } from "../src/rooms.ts";
import { sendPrompt } from "../src/send.ts";
import { listPairChannels } from "../src/server/pair-channels.ts";
import { startFakeWorkers } from "../src/worker.ts";
import { makeCfoComputer, makeComputer } from "./helpers.ts";

test("parseAskPeer reads named, unnamed, mention, and typo peers", () => {
  const computer = makeCfoComputer();
  const roster = loadRoster(computer);
  const named = parseAskPeer("Ask the Payables agent what color the sky is.", roster, "ingest");
  assert.equal(named?.slug, "ap");
  assert.match(named?.question ?? "", /color the sky/i);

  const typo = parseAskPeer("Ask the Paybles agent what color the sky is", roster, "ingest");
  assert.equal(typo?.slug, "ap");

  const unnamed = parseAskPeer("Ask one of your agents what color the sky is", roster, "ingest");
  assert.equal(unnamed?.slug, "ap");
  assert.equal(unnamed?.question, "what color the sky is");

  const mention = parseAskPeer("@Payables what color is the sky?", roster, "ingest");
  assert.equal(mention?.slug, "ap");
  assert.match(mention?.question ?? "", /what color is the sky/i);

  const self = parseAskPeer("Ask Ingest what color the sky is", roster, "ingest");
  assert.equal(self, undefined);
});

test("formatWake tells a bound Bot to call bot_ask for a natural ask", () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const wake = formatWake(
    {
      id: "in_1",
      handleId: "h_1",
      kind: "user_dm",
      from: "operator",
      to: "bot_alpha",
      conversation: { kind: "operator_dm", botId: "bot_alpha" },
      prompt: "Ask the Beta agent what color the sky is",
      paths: [],
      mentions: [],
      createdAt: new Date().toISOString(),
      status: "claimed",
    },
    roster,
    "alpha",
  );
  assert.match(wake, /bot_ask/);
  assert.match(wake, /bot_id=beta/);
});

test("formatWake requires ask_bot back on a peer wake", () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const wake = formatWake(
    {
      id: "in_2",
      handleId: "h_2",
      kind: "a2a_handoff",
      from: "bot_alpha",
      to: "bot_beta",
      conversation: { kind: "peer_dm", fromId: "bot_alpha", toId: "bot_beta" },
      prompt: "What color is the sky?",
      paths: [],
      mentions: [],
      createdAt: new Date().toISOString(),
      status: "claimed",
    },
    roster,
    "beta",
  );
  assert.match(wake, /Required tool: call ask_bot/);
  assert.match(wake, /bot_id=alpha/);
  assert.match(wake, /message_operator/);
});

test("lane kickWake sequence completes an operator ask without Pi", async () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const alpha = findBot(roster, "alpha");
  assert.ok(alpha);
  const workers = startFakeWorkers(computer, ["beta"], (slug, item) =>
    executeFakeTurn(computer, slug, item, 4000),
  );
  const lane = bindLane(computer, alpha);
  const sent = sendPrompt({
    computerRoot: computer,
    from: "operator",
    to: "alpha",
    prompt: "Ask one of your agents what color the sky is",
  });
  assert.ok(sent.handleId);
  const item = startNextTurn(lane);
  assert.ok(item);
  const handed = await tryOperatorAskHandoff(computer, alpha.id, item, 4000);
  assert.ok(handed);
  completeTurn(lane, handed);
  workers.stop();
  const done = await awaitTurn(computer, sent.handleId, { timeoutMs: 1000 });
  assert.equal(done.done, true);
  assert.match(done.result ?? "", /beta/);
});

test("natural-language ask routes to a peer and returns their result", async () => {
  const computer = makeComputer();
  const workers = startFakeWorkers(computer, ["alpha", "beta"], (slug, item) =>
    executeFakeTurn(computer, slug, item, 4000),
  );
  const sent = sendPrompt({
    computerRoot: computer,
    from: "operator",
    to: "alpha",
    prompt: "Ask the Beta agent what color the sky is",
  });
  assert.equal(sent.accepted, true);
  assert.ok(sent.handleId);
  const done = await awaitTurn(computer, sent.handleId, { timeoutMs: 4000 });
  workers.stop();
  assert.equal(done.done, true);
  assert.match(done.result ?? "", /\[beta\]/i);
  const protocol = readProtocol(computer);
  assert.ok(
    protocol.some(
      (row) => row.type === "send.accepted" && row.from === "bot_alpha" && row.to === "bot_beta",
    ),
  );
});

test("askPeer send-and-wait returns the peer Handle result", async () => {
  const computer = makeComputer();
  const workers = startFakeWorkers(computer, ["beta"], (slug, item) =>
    executeFakeTurn(computer, slug, item, 4000),
  );
  const answered = await askPeer({
    computerRoot: computer,
    from: "alpha",
    to: "beta",
    prompt: "what color is the sky",
    timeoutMs: 4000,
  });
  workers.stop();
  assert.equal(answered.accepted, true);
  assert.equal(answered.done, true);
  assert.match(answered.result ?? "", /\[beta\]/);
});

test("sendBotMessage reply is two-way and is the only thread post from the receiver", async () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const alpha = findBot(roster, "alpha");
  const beta = findBot(roster, "beta");
  assert.ok(alpha && beta);
  const workers = startFakeWorkers(computer, ["beta"], async (_slug, item) => {
    const replied = sendBotMessage({
      computerRoot: computer,
      from: beta.id,
      to: alpha.id,
      prompt: "Blue, typically.",
      inbound: item,
      timeoutMs: 1000,
    });
    return { text: (await replied).result ?? "", paths: [] };
  });
  const asked = await askPeer({
    computerRoot: computer,
    from: alpha.id,
    to: beta.id,
    prompt: "What color is the sky?",
    timeoutMs: 4000,
  });
  workers.stop();
  assert.equal(asked.done, true);
  assert.match(asked.result ?? "", /Blue/);
  const channel = listPairChannels(computer, roster)[0];
  assert.ok(channel);
  assert.equal(channel.messages.length, 2);
  assert.equal(channel.messages[0]?.from.botId, alpha.id);
  assert.equal(channel.messages[1]?.from.botId, beta.id);
  assert.match(channel.messages[1]?.text ?? "", /Blue/);
});

test("@Payables in a Room wakes Payables by name, not only slug", async () => {
  const computer = makeCfoComputer();
  const roster = loadRoster(computer);
  const ingest = findBot(roster, "ingest");
  const ap = findBot(roster, "ap");
  const cash = findBot(roster, "cash");
  assert.ok(ingest && ap && cash);
  const workers = startFakeWorkers(computer, ["ingest", "ap", "cash"], async (slug, item) => ({
    text: `${slug} heard ${item.kind}`,
    paths: [],
  }));
  await roomPost({
    computerRoot: computer,
    roomId: "pay",
    from: "operator",
    text: "@Payables ping the sky",
    waitCapMs: 250,
    awaitTimeoutMs: 4000,
  });
  workers.stop();
  const protocol = readProtocol(computer);
  assert.ok(protocol.some((row) => row.type === "send.accepted" && row.to === ap.id));
  assert.equal(
    protocol.some((row) => row.type === "send.accepted" && row.to === cash.id),
    false,
  );
});

test("assistant text on a peer wake does not enter the pair thread", () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const beta = findBot(roster, "beta");
  assert.ok(beta);
  const lane = bindLane(computer, beta);
  const sent = sendPrompt({
    computerRoot: computer,
    from: "alpha",
    to: "beta",
    prompt: "What color is the sky?",
  });
  assert.ok(sent.handleId);
  const item = startNextTurn(lane);
  assert.ok(item);
  completeTurn(lane, { text: "Blue from assistant text only", paths: [] });
  assert.equal(findHandle(computer, sent.handleId)?.status, "failed");
  const channel = listPairChannels(computer, roster)[0];
  assert.ok(channel);
  assert.equal(channel.messages.length, 1);
  assert.equal(channel.messages[0]?.from.botId, "bot_alpha");
  assert.equal(
    channel.messages.some((row) => /assistant text/.test(row.text)),
    false,
  );
});

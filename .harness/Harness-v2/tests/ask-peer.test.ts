import assert from "node:assert/strict";
import { test } from "node:test";

import { bindLane, completeTurn, formatWake, startNextTurn } from "../src/lane.ts";
import { askPeer, executeFakeTurn, parseAskPeer, tryOperatorAskHandoff } from "../src/ask-peer.ts";
import { awaitTurn } from "../src/await.ts";
import { readProtocol } from "../src/protocol-log.ts";
import { findBot, loadRoster } from "../src/roster.ts";
import { roomPost } from "../src/rooms.ts";
import { sendPrompt } from "../src/send.ts";
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

test("lane kickWake sequence completes an operator ask without Pi", async () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const alpha = findBot(roster, "alpha");
  assert.ok(alpha);
  const workers = startFakeWorkers(computer, ["beta"], async (slug, item) => ({
    text: `${slug} says blue`,
    paths: [],
  }));
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
  assert.match(done.result ?? "", /blue/);
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
  assert.equal(answered.accepted, true);
  assert.equal(answered.done, true);
  assert.match(answered.result ?? "", /blue/);
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

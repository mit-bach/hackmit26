import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

import { awaitTurn } from "../src/await.ts";
import { findHandle } from "../src/handle.ts";
import { bindLane, drainAll, noteBusyQueue, preemptPeerForUser, startNextTurn } from "../src/lane.ts";
import { pendingCount } from "../src/inbox.ts";
import { liveStatus } from "../src/lane-state.ts";
import { readProtocol } from "../src/protocol-log.ts";
import { findBot, loadRoster } from "../src/roster.ts";
import { searchAgents } from "../src/search.ts";
import { sendPrompt } from "../src/send.ts";
import { readTranscript } from "../src/transcript.ts";
import { startFakeWorkers } from "../src/worker.ts";
import { makeComputer } from "./helpers.ts";

test("unknown Bot is refused at accept time", () => {
  const computer = makeComputer();
  const result = sendPrompt({
    computerRoot: computer,
    from: "bot_alpha",
    to: "does-not-exist",
    prompt: "nope",
  });
  assert.equal(result.accepted, false);
  assert.equal(result.reason, "unknown");
});

test("blocking mode is refused", () => {
  const computer = makeComputer();
  const result = sendPrompt({
    computerRoot: computer,
    from: "bot_alpha",
    to: "bot_beta",
    prompt: "nope",
    mode: "blocking",
  });
  assert.equal(result.accepted, false);
  assert.equal(result.reason, "blocking forbidden");
});

test("accept happens before the receiver runs, await completes after the turn ends", async () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const alpha = findBot(roster, "alpha");
  const beta = findBot(roster, "beta");
  assert.ok(alpha);
  assert.ok(beta);
  bindLane(computer, alpha);
  const betaLane = bindLane(computer, beta);
  assert.equal(liveStatus(computer, alpha.id), "idle");
  assert.equal(liveStatus(computer, beta.id), "idle");

  const sent = sendPrompt({
    computerRoot: computer,
    from: alpha.id,
    to: beta.id,
    prompt: "read workspace/note.md and return PONG",
    paths: ["workspace/note.md"],
  });
  assert.equal(sent.accepted, true);
  assert.ok(sent.handleId);
  const before = findHandle(computer, sent.handleId);
  assert.ok(before);
  assert.equal(before.status, "accepted");
  assert.equal(before.result, undefined);

  const protocolAfterAccept = readProtocol(computer);
  assert.ok(protocolAfterAccept.some((row) => row.type === "send.accepted" && row.handleId === sent.handleId));

  const n = await drainAll(betaLane, async (item) => ({
    text: `PONG ${item.prompt}`,
    paths: item.paths,
  }));
  assert.equal(n, 1);

  const afterHandle = findHandle(computer, sent.handleId);
  assert.ok(afterHandle);
  assert.equal(afterHandle.status, "completed");
  assert.ok(afterHandle.result?.includes("PONG"));

  const awaited = await awaitTurn(computer, sent.handleId, { timeoutMs: 1000 });
  assert.equal(awaited.done, true);
  assert.equal(awaited.status, "completed");

  const handleId = sent.handleId;
  const senderLines = readTranscript(computer, alpha.id, 50);
  const receiverLines = readTranscript(computer, beta.id, 50);
  assert.ok(senderLines.some((row) => row.text.includes(handleId)));
  assert.ok(receiverLines.some((row) => row.text.includes(handleId)));

  const log = readFileSync(join(computer, "harness", "protocol.jsonl"), "utf8");
  assert.match(log, /send\.accepted/);
  assert.match(log, /turn\.end/);
});

test("roster search returns Bots with live status, never child ids", () => {
  const computer = makeComputer();
  const hits = searchAgents(computer, "handoff");
  assert.ok(hits.some((hit) => hit.slug === "alpha"));
  assert.ok(hits.every((hit) => !hit.id.includes("agent-") && !hit.slug.includes("pid")));
});

test("peer work queues while a turn is running; operator preempt requeues it", () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const alpha = findBot(roster, "alpha");
  const beta = findBot(roster, "beta");
  assert.ok(alpha);
  assert.ok(beta);
  const lane = bindLane(computer, beta);
  const first = sendPrompt({
    computerRoot: computer,
    from: alpha.id,
    to: beta.id,
    prompt: "long job",
  });
  assert.ok(first.handleId);
  const item = startNextTurn(lane);
  assert.ok(item);
  assert.equal(findHandle(computer, first.handleId)?.status, "running");

  const second = sendPrompt({
    computerRoot: computer,
    from: alpha.id,
    to: beta.id,
    prompt: "queued job",
  });
  assert.ok(second.handleId);
  noteBusyQueue(lane);
  assert.equal(findHandle(computer, second.handleId)?.status, "queued");
  assert.ok(pendingCount(computer, beta.id) >= 1);

  const preempted = preemptPeerForUser(lane);
  assert.ok(preempted);
  assert.equal(findHandle(computer, first.handleId)?.status, "queued");
});

test("fake workers complete a handle without a model", async () => {
  const computer = makeComputer();
  const workers = startFakeWorkers(computer, ["beta"], async (slug, item) => ({
    text: `${slug}-ok:${item.handleId}`,
    paths: [],
  }));
  const sent = sendPrompt({
    computerRoot: computer,
    from: "operator",
    to: "beta",
    prompt: "ping",
    kind: "user_dm",
  });
  assert.ok(sent.handleId);
  const outcome = await awaitTurn(computer, sent.handleId, { timeoutMs: 5000 });
  workers.stop();
  assert.equal(outcome.done, true);
  assert.equal(outcome.status, "completed");
});

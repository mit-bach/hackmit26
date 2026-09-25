import assert from "node:assert/strict";
import { test } from "node:test";

import { findHandle, writeHandle } from "../src/handle.ts";
import { appendInbox, listInbox } from "../src/inbox.ts";
import { nowIso } from "../src/ids.ts";
import { bindLane } from "../src/lane.ts";
import { writeLane } from "../src/lane-state.ts";
import { findBot, loadRoster } from "../src/roster.ts";
import { makeComputer } from "./helpers.ts";

const DEAD_PID = 2147483647;

test("claimed inbox plus dead pid becomes pending; running Handle becomes queued", () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const beta = findBot(roster, "beta");
  assert.ok(beta);
  const createdAt = nowIso();
  writeHandle(computer, beta.id, {
    id: "h_crash",
    from: "bot_alpha",
    to: beta.id,
    toSlug: "beta",
    prompt: "was running",
    paths: [],
    conversation: { kind: "peer_dm", fromId: "bot_alpha", toId: beta.id },
    kind: "a2a_handoff",
    status: "running",
    createdAt,
    updatedAt: createdAt,
  });
  appendInbox(computer, beta.id, {
    id: "in_crash",
    handleId: "h_crash",
    kind: "a2a_handoff",
    from: "bot_alpha",
    to: beta.id,
    conversation: { kind: "peer_dm", fromId: "bot_alpha", toId: beta.id },
    prompt: "was running",
    paths: [],
    mentions: [],
    createdAt,
    status: "claimed",
    claimedByPid: DEAD_PID,
    claimedAt: createdAt,
  });
  writeLane(computer, {
    botId: beta.id,
    slug: "beta",
    status: "running",
    pid: DEAD_PID,
    handleId: "h_crash",
    updatedAt: createdAt,
  });

  bindLane(computer, beta);
  assert.equal(findHandle(computer, "h_crash")?.status, "queued");
  assert.ok(listInbox(computer, beta.id).some((item) => item.id === "in_crash" && item.status === "pending"));
});

test("blocked Handle occupies the lane after a dead process bind", () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const beta = findBot(roster, "beta");
  assert.ok(beta);
  const createdAt = nowIso();
  writeHandle(computer, beta.id, {
    id: "h_block",
    from: "operator",
    to: beta.id,
    toSlug: "beta",
    prompt: "needs operator",
    paths: [],
    conversation: { kind: "operator_dm", botId: beta.id },
    kind: "user_dm",
    status: "blocked",
    createdAt,
    updatedAt: createdAt,
    blockedReason: "approval",
  });
  appendInbox(computer, beta.id, {
    id: "in_block",
    handleId: "h_block",
    kind: "user_dm",
    from: "operator",
    to: beta.id,
    conversation: { kind: "operator_dm", botId: beta.id },
    prompt: "needs operator",
    paths: [],
    mentions: [],
    createdAt,
    status: "claimed",
    claimedByPid: DEAD_PID,
    claimedAt: createdAt,
  });
  writeLane(computer, {
    botId: beta.id,
    slug: "beta",
    status: "blocked",
    pid: DEAD_PID,
    handleId: "h_block",
    updatedAt: createdAt,
  });

  const lane = bindLane(computer, beta);
  assert.equal(findHandle(computer, "h_block")?.status, "blocked");
  assert.equal(lane.currentInbox?.handleId, "h_block");
});

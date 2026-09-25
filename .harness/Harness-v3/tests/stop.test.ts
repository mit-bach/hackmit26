import assert from "node:assert/strict";
import { test } from "node:test";

import { findHandle } from "../src/handle.ts";
import { bindLane, interruptIfStop, startNextTurn } from "../src/lane.ts";
import { pendingCount } from "../src/inbox.ts";
import { findBot, loadRoster } from "../src/roster.ts";
import { sendPrompt } from "../src/send.ts";
import { makeComputer } from "./helpers.ts";

test("fire_and_forget accepts without returning a Handle", () => {
  const computer = makeComputer();
  const result = sendPrompt({
    computerRoot: computer,
    from: "bot_alpha",
    to: "bot_beta",
    prompt: "no handle please",
    mode: "fire_and_forget",
  });
  assert.equal(result.accepted, true);
  assert.equal(result.handleId, undefined);
  assert.ok(pendingCount(computer, "bot_beta") >= 1);
});

test("operator stop cancels the running peer Handle", () => {
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

  const stop = sendPrompt({
    computerRoot: computer,
    from: "operator",
    to: beta.id,
    prompt: "Stop now",
    kind: "user_stop",
    onBusy: "supersede",
  });
  assert.equal(stop.accepted, true);
  const interrupted = interruptIfStop(lane);
  assert.equal(interrupted, true);
  assert.equal(findHandle(computer, first.handleId)?.status, "cancelled");
});

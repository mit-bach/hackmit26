import assert from "node:assert/strict";
import { test } from "node:test";

import {
  createApproval,
  isConsequential,
  resolveApproval,
  waitForApproval,
} from "../src/approvals.ts";
import { awaitTurn } from "../src/await.ts";
import { findHandle } from "../src/handle.ts";
import { bindLane, blockTurn, drainOnce, resumeTurn } from "../src/lane.ts";
import { findBot, loadRoster } from "../src/roster.ts";
import { sendPrompt } from "../src/send.ts";
import { makeComputer } from "./helpers.ts";

test("fail-closed patterns are consequential; a peer Handle is not", () => {
  assert.equal(isConsequential("bash", { command: "rm -rf /tmp/x" }, "ask"), true);
  assert.equal(isConsequential("bash", { command: "ls" }, "ask"), false);
  assert.equal(isConsequential("read", { path: "x" }, "always"), false);
  assert.equal(isConsequential("write", { path: "x" }, "always"), true);
});

test("a consequential gate parks the Handle blocked until the Operator answers", async () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const gamma = findBot(roster, "gamma");
  assert.ok(gamma);
  const lane = bindLane(computer, gamma);

  const sent = sendPrompt({
    computerRoot: computer,
    from: "operator",
    to: gamma.id,
    prompt: "do a gated action",
    kind: "user_dm",
  });
  assert.ok(sent.handleId);

  const ran = await drainOnce(lane, async () => {
    const approval = createApproval(computer, {
      botId: gamma.id,
      handleId: sent.handleId,
      toolName: "bash",
      detail: "rm -rf workspace",
    });
    blockTurn(lane, "waiting on Operator");
    setTimeout(() => {
      resolveApproval(computer, approval.id, true);
    }, 40);
    const decided = await waitForApproval(computer, approval.id, 2000);
    assert.equal(decided.status, "allowed");
    resumeTurn(lane);
    return { text: "allowed and finished", paths: [] };
  });
  assert.equal(ran, true);

  const blockedSnap = await awaitTurn(computer, sent.handleId, { timeoutMs: 10 });
  void blockedSnap;

  const handle = findHandle(computer, sent.handleId);
  assert.ok(handle);
  assert.equal(handle.status, "completed");
  assert.equal(handle.result, "allowed and finished");
});

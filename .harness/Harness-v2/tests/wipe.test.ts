import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

import { initComputer } from "../src/computer.ts";
import { listInbox } from "../src/inbox.ts";
import { listHandles } from "../src/handle.ts";
import { inboxPath, protocolLogPath, seqPath } from "../src/paths.ts";
import { findBot, loadRoster } from "../src/roster.ts";
import { fireRoutine } from "../src/routines.ts";
import { sendPrompt } from "../src/send.ts";
import { wipeRuntime } from "../src/wipe.ts";
import { makeComputer } from "./helpers.ts";

test("wipeRuntime clears session files and keeps the roster", () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const beta = findBot(roster, "beta");
  assert.ok(beta);
  const sent = sendPrompt({
    computerRoot: computer,
    from: "operator",
    to: beta.id,
    prompt: "leave a handle",
    kind: "user_dm",
  });
  assert.ok(sent.handleId);
  fireRoutine(computer, "morning-brief");
  assert.ok(listInbox(computer, beta.id).length > 0);
  assert.ok(listHandles(computer, beta.id).length > 0);

  const report = wipeRuntime(computer);
  assert.equal(report.bots, 3);
  initComputer(computer);
  const after = loadRoster(computer);
  assert.equal(after.bots.length, 3);
  assert.equal(after.system, "protocol-floor");
  assert.equal(listInbox(computer, beta.id).length, 0);
  assert.equal(listHandles(computer, beta.id).length, 0);
  assert.equal(readFileSync(inboxPath(computer, beta.id), "utf8").trim(), "");
  assert.equal(readFileSync(protocolLogPath(computer), "utf8").trim(), "");
  assert.equal(readFileSync(seqPath(computer), "utf8").trim(), "0");
  assert.equal(existsSync(join(computer, "harness", "roster.json")), true);
});

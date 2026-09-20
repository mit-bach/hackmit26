import assert from "node:assert/strict";
import { test } from "node:test";

import { writeJsonAtomic } from "../src/fs.ts";
import { writeHandle } from "../src/handle.ts";
import { listInbox } from "../src/inbox.ts";
import { receiptPath } from "../src/paths.ts";
import { findBot, loadRoster } from "../src/roster.ts";
import { fireRoutine, listReceipts } from "../src/routines.ts";
import { startFakeWorkers } from "../src/worker.ts";
import { awaitTurn } from "../src/await.ts";
import { makeComputer } from "./helpers.ts";

test("a Routine enqueue lands on the owning Bot inbox, not the Operator pane", async () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const beta = findBot(roster, "beta");
  const alpha = findBot(roster, "alpha");
  assert.ok(beta);
  assert.ok(alpha);

  const workers = startFakeWorkers(computer, ["beta"], async (slug, item) => ({
    text: `${slug} routine ${item.kind}`,
    paths: [],
  }));

  const receipt = fireRoutine(computer, "morning-brief");
  assert.equal(receipt.bot, "beta");
  assert.equal(receipt.status, "queued");
  assert.ok(receipt.handleId);

  const inbox = listInbox(computer, beta.id);
  assert.ok(inbox.some((row) => row.handleId === receipt.handleId && row.kind === "routine"));
  const alphaInbox = listInbox(computer, alpha.id);
  assert.equal(
    alphaInbox.some((row) => row.handleId === receipt.handleId),
    false,
  );

  const outcome = await awaitTurn(computer, receipt.handleId, { timeoutMs: 4000 });
  workers.stop();
  assert.equal(outcome.done, true);
  const settled = listReceipts(computer).find((row) => row.id === receipt.id);
  assert.equal(settled?.status, "completed");
});

test("listReceipts heals a queued receipt whose Handle already completed", () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const beta = findBot(roster, "beta");
  assert.ok(beta);
  const at = new Date().toISOString();
  const handleId = "h_orphan_receipt";
  writeHandle(computer, beta.id, {
    id: handleId,
    from: "operator",
    to: beta.id,
    toSlug: beta.slug,
    prompt: "stale routine",
    paths: [],
    conversation: { kind: "operator_dm", botId: beta.id },
    kind: "routine",
    status: "completed",
    createdAt: at,
    updatedAt: at,
    result: "done while receipt stayed queued",
  });
  writeJsonAtomic(receiptPath(computer, "rc_orphan"), {
    id: "rc_orphan",
    name: "morning-brief",
    bot: "beta",
    handleId,
    status: "queued",
    at,
    updatedAt: at,
  });
  const healed = listReceipts(computer).find((row) => row.id === "rc_orphan");
  assert.equal(healed?.status, "completed");
  assert.equal(healed?.result, "done while receipt stayed queued");
});

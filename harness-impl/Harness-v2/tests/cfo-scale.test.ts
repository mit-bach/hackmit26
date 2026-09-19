import assert from "node:assert/strict";
import { test } from "node:test";

import { awaitTurn } from "../src/await.ts";
import { findHandle } from "../src/handle.ts";
import { writeMemoryFile, readMemoryFile } from "../src/memory.ts";
import { readProtocol } from "../src/protocol-log.ts";
import { fireRoutine } from "../src/routines.ts";
import { readRoomLog, roomPost } from "../src/rooms.ts";
import { findBot, loadRoster } from "../src/roster.ts";
import { searchAgents } from "../src/search.ts";
import { sendPrompt } from "../src/send.ts";
import { startFakeWorkers } from "../src/worker.ts";
import { makeCfoComputer } from "./helpers.ts";

test("cfo-floor: a six-Bot pay cycle completes on disk without a model", async () => {
  const computer = makeCfoComputer();
  const roster = loadRoster(computer);
  const slugs = roster.bots.map((bot) => bot.slug);
  const workers = startFakeWorkers(computer, slugs, async (slug, item) => ({
    text: `${slug} handled ${item.handleId}`,
    paths: item.paths,
  }));

  const ingest = findBot(roster, "ingest");
  const ap = findBot(roster, "ap");
  const cash = findBot(roster, "cash");
  const close = findBot(roster, "close");
  assert.ok(ingest && ap && cash && close);

  const toAp = sendPrompt({
    computerRoot: computer,
    from: ingest.id,
    to: ap.id,
    prompt: "check workspace/inbox/INV-1001.md",
    paths: ["workspace/inbox/INV-1001.md"],
  });
  assert.equal(toAp.accepted, true);
  assert.ok(toAp.handleId);
  const apDone = await awaitTurn(computer, toAp.handleId, { timeoutMs: 5000 });
  assert.equal(apDone.done, true);

  const toCash = sendPrompt({
    computerRoot: computer,
    from: ap.id,
    to: cash.id,
    prompt: "cash note for INV-1001",
    paths: ["workspace/inbox/INV-1001.md"],
  });
  assert.ok(toCash.handleId);
  assert.equal((await awaitTurn(computer, toCash.handleId, { timeoutMs: 5000 })).done, true);

  const toClose = sendPrompt({
    computerRoot: computer,
    from: cash.id,
    to: close.id,
    prompt: "close checklist for INV-1001",
    paths: ["workspace/inbox/INV-1001.md"],
  });
  assert.ok(toClose.handleId);
  assert.equal((await awaitTurn(computer, toClose.handleId, { timeoutMs: 5000 })).done, true);

  const log = readProtocol(computer);
  assert.ok(log.some((row) => row.type === "send.accepted" && row.handleId === toAp.handleId));
  assert.ok(log.some((row) => row.type === "turn.end" && row.handleId === toClose.handleId));
  assert.equal(findHandle(computer, toAp.handleId)?.status, "completed");

  const hits = searchAgents(computer, "payables");
  assert.ok(hits.some((hit) => hit.slug === "ap"));
  assert.ok(hits.every((hit) => !hit.id.startsWith("agent-")));

  workers.stop();
});

test("cfo-floor: twenty mixed handoffs all reach a terminal Handle", async () => {
  const computer = makeCfoComputer();
  const roster = loadRoster(computer);
  const slugs = roster.bots.map((bot) => bot.slug);
  const workers = startFakeWorkers(computer, slugs, async (slug, item) => ({
    text: `${slug}:${item.kind}`,
    paths: [],
  }));
  const handles: string[] = [];
  for (let i = 0; i < 20; i += 1) {
    const to = slugs[i % slugs.length] ?? "ap";
    const sent = sendPrompt({
      computerRoot: computer,
      from: "operator",
      to,
      prompt: `job ${i}`,
      kind: "user_dm",
    });
    assert.ok(sent.handleId);
    handles.push(sent.handleId);
  }
  for (const handleId of handles) {
    const outcome = await awaitTurn(computer, handleId, { timeoutMs: 8000 });
    assert.equal(outcome.done, true, handleId);
  }
  workers.stop();
});

test("cfo-floor: pay Room Host and close Routine stay on owning Bots", async () => {
  const computer = makeCfoComputer();
  const roster = loadRoster(computer);
  const workers = startFakeWorkers(
    computer,
    roster.bots.map((bot) => bot.slug),
    async (slug, item) => ({
      text: `${slug} room-or-routine`,
      paths: [],
    }),
  );
  const posted = await roomPost({
    computerRoot: computer,
    roomId: "pay",
    from: "operator",
    text: "status in two lines",
    waitCapMs: 400,
    awaitTimeoutMs: 4000,
  });
  assert.ok(posted.handles.length >= 1);
  const roomLog = readRoomLog(computer, "pay");
  assert.ok(roomLog.some((row) => row.kind === "post"));

  const receipt = fireRoutine(computer, "morning-brief");
  assert.equal(receipt.bot, "close");
  assert.ok(receipt.handleId);
  assert.equal((await awaitTurn(computer, receipt.handleId, { timeoutMs: 5000 })).done, true);

  writeMemoryFile(computer, "bot_ap", "MEMORY.md", "ap only");
  writeMemoryFile(computer, "bot_audit", "MEMORY.md", "audit only");
  assert.doesNotMatch(readMemoryFile(computer, "bot_audit", "MEMORY.md"), /ap only/);
  workers.stop();
});

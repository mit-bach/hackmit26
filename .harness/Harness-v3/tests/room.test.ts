import assert from "node:assert/strict";
import { test } from "node:test";

import { touchLane } from "../src/lane-state.ts";
import { findBot, loadRoster } from "../src/roster.ts";
import { readRoomLog, roomPost } from "../src/rooms.ts";
import { startFakeWorkers } from "../src/worker.ts";
import { makeComputer } from "./helpers.ts";

test("Room Host wakes members in roster order and chips a busy member instead of skipping silently", async () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const gamma = findBot(roster, "gamma");
  assert.ok(gamma);

  const workers = startFakeWorkers(computer, ["alpha", "beta"], async (slug, item) => ({
    text: `${slug} round: ${item.prompt.slice(0, 40)}`,
    paths: [],
  }));

  touchLane(computer, gamma.id, "gamma", "running");

  const result = await roomPost({
    computerRoot: computer,
    roomId: "floor",
    from: "operator",
    text: "each of you: status in two lines",
    waitCapMs: 250,
    awaitTimeoutMs: 4000,
  });
  workers.stop();

  assert.ok(result.handles.length >= 1);
  const log = readRoomLog(computer, "floor");
  assert.ok(log.some((row) => row.kind === "post"));
  assert.ok(log.some((row) => row.kind === "chip" && row.text.includes("gamma")));
});

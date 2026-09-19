import assert from "node:assert/strict";
import { test } from "node:test";

import { startServer } from "../src/server/http.ts";
import { makeComputer } from "./helpers.ts";

interface RosterBody {
  readonly bots: readonly unknown[];
}

interface SendBody {
  readonly accepted: boolean;
  readonly handleId?: string;
}

interface HandleBody {
  readonly status: string;
}

test("headless HTTP speaks the same protocol without a UI", async () => {
  const computer = makeComputer();
  const started = await startServer({ computerRoot: computer, port: 0, workers: false });
  try {
    const health = await fetch(`${started.url}/v1/health`);
    assert.equal(health.ok, true);
    const roster = (await (await fetch(`${started.url}/v1/roster`)).json()) as RosterBody;
    assert.ok(Array.isArray(roster.bots));
    const sent = (await (
      await fetch(`${started.url}/v1/bots/beta/prompt`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: "operator ping" }),
      })
    ).json()) as SendBody;
    assert.equal(sent.accepted, true);
    assert.ok(sent.handleId);
    const handle = (await (await fetch(`${started.url}/v1/handles/${sent.handleId}`)).json()) as HandleBody;
    assert.equal(handle.status, "accepted");
    const bots = (await (await fetch(`${started.url}/v1/bots?query=beta`)).json()) as Array<{ slug: string }>;
    assert.ok(Array.isArray(bots));
    assert.ok(bots.some((row) => row.slug === "beta"));
    const inbox = await fetch(`${started.url}/v1/bots/beta/inbox`);
    assert.equal(inbox.ok, true);
  } finally {
    await started.stop();
  }
});

test("fake HTTP workers complete a Handle without a model", async () => {
  const computer = makeComputer();
  const started = await startServer({
    computerRoot: computer,
    port: 0,
    workers: false,
    fakeWorkers: true,
  });
  try {
    const sent = (await (
      await fetch(`${started.url}/v1/bots/beta/prompt`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: "http fake ping" }),
      })
    ).json()) as SendBody;
    assert.ok(sent.handleId);
    const awaited = (await (
      await fetch(`${started.url}/v1/handles/${sent.handleId}/await?timeoutMs=4000`, {
        method: "POST",
      })
    ).json()) as { done: boolean; status: string };
    assert.equal(awaited.done, true);
    assert.equal(awaited.status, "completed");
  } finally {
    await started.stop();
  }
});

import assert from "node:assert/strict";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

import { startServer } from "../src/server/http.ts";
import { listComputerTree } from "../src/server/computer-tree.ts";
import { makeCfoComputer, makeComputer } from "./helpers.ts";

interface SnapshotBody {
  readonly system: string;
  readonly bots: readonly { readonly slug: string; readonly threadId: string }[];
  readonly rooms: readonly { readonly id: string }[];
}

interface SendBody {
  readonly accepted: boolean;
  readonly handleId?: string;
}

test("GET /api/bots returns the OpenMausBot snapshot object", async () => {
  const computer = makeCfoComputer();
  const started = await startServer({ computerRoot: computer, port: 0, workers: false });
  try {
    const body = (await (await fetch(`${started.url}/api/bots`)).json()) as {
      bots: readonly { id: string; messages: unknown[] }[];
      groups: readonly { id: string }[];
    };
    assert.ok(Array.isArray(body.bots));
    assert.equal(body.bots.length, 6);
    assert.ok(body.bots.some((bot) => bot.id === "bot_ap" && Array.isArray(bot.messages)));
    assert.ok(body.groups.some((group) => group.id === "pay"));
    const session = (await (await fetch(`${started.url}/api/auth/session`)).json()) as { kind: string };
    assert.equal(session.kind, "loopback");
    const instances = (await (await fetch(`${started.url}/api/instances`)).json()) as {
      instances: readonly { snapshot: { state: string } }[];
    };
    assert.equal(instances.instances[0]?.snapshot.state, "available");
  } finally {
    await started.stop();
  }
});

test("GET /api/snapshot returns Operator bots and rooms", async () => {
  const computer = makeCfoComputer();
  const started = await startServer({ computerRoot: computer, port: 0, workers: false });
  try {
    const snap = (await (await fetch(`${started.url}/api/snapshot`)).json()) as SnapshotBody;
    assert.equal(snap.system, "cfo-floor");
    assert.equal(snap.bots.length, 6);
    assert.ok(snap.bots.some((bot) => bot.slug === "ap" && bot.threadId === "bot_ap"));
    assert.ok(snap.rooms.some((room) => room.id === "pay"));
  } finally {
    await started.stop();
  }
});

test("POST /api/bots/:slug/messages accepts a Handle and fake workers complete it", async () => {
  const computer = makeComputer();
  const started = await startServer({
    computerRoot: computer,
    port: 0,
    workers: false,
    fakeWorkers: true,
  });
  try {
    const sent = (await (
      await fetch(`${started.url}/api/bots/beta/messages`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: "operator ping from shell" }),
      })
    ).json()) as SendBody;
    assert.equal(sent.accepted, true);
    assert.ok(sent.handleId);
    const awaited = (await (
      await fetch(`${started.url}/api/handles/${sent.handleId}/await?timeoutMs=4000`, {
        method: "POST",
      })
    ).json()) as { done: boolean; status: string };
    assert.equal(awaited.done, true);
    assert.equal(awaited.status, "completed");
    const messages = (await (await fetch(`${started.url}/api/bots/beta/messages`)).json()) as unknown[];
    assert.ok(Array.isArray(messages));
    assert.ok(messages.length > 0);
  } finally {
    await started.stop();
  }
});

test("SSE /api/events sends a hello snapshot", async () => {
  const computer = makeComputer();
  const started = await startServer({ computerRoot: computer, port: 0, workers: false });
  try {
    const res = await fetch(`${started.url}/api/events`);
    assert.equal(res.ok, true);
    assert.ok(res.headers.get("content-type")?.includes("text/event-stream"));
    const reader = res.body?.getReader();
    assert.ok(reader);
    const { value } = await reader.read();
    const text = new TextDecoder().decode(value);
    assert.ok(text.includes("hello"));
    assert.ok(text.includes("protocol-floor"));
    await reader.cancel();
  } finally {
    await started.stop();
  }
});

test("computer tree lists workspace files and refuses path escape", async () => {
  const computer = makeComputer();
  mkdirSync(join(computer, "workspace", "nested"), { recursive: true });
  writeFileSync(join(computer, "workspace", "nested", "note.md"), "ok\n");
  const tree = listComputerTree(computer, "workspace");
  assert.ok(tree.some((row) => row.path.includes("note.md")));
  const started = await startServer({ computerRoot: computer, port: 0, workers: false });
  try {
    const file = await fetch(`${started.url}/api/computer/file?path=workspace/nested/note.md`);
    assert.equal(file.ok, true);
    const escaped = await fetch(`${started.url}/api/computer/file?path=../etc/passwd`);
    assert.equal(escaped.status, 400);
    const written = await fetch(`${started.url}/api/computer/file`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ path: "workspace/nested/operator.md", content: "demo note\n" }),
    });
    assert.equal(written.ok, true);
    const reread = (await (
      await fetch(`${started.url}/api/computer/file?path=workspace/nested/operator.md`)
    ).json()) as { content: string };
    assert.equal(reread.content, "demo note\n");
  } finally {
    await started.stop();
  }
});

test("POST /api/rooms/:id/messages and PATCH /api/bots/:slug update the Computer", async () => {
  const computer = makeComputer();
  const started = await startServer({
    computerRoot: computer,
    port: 0,
    workers: false,
    fakeWorkers: true,
  });
  try {
    const posted = await fetch(`${started.url}/api/rooms/floor/messages`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text: "stand-up from operator" }),
    });
    assert.equal(posted.ok, true);
    const room = (await (await fetch(`${started.url}/api/rooms/floor`)).json()) as {
      log: readonly { text: string }[];
    };
    assert.ok(room.log.some((row) => row.text.includes("stand-up")));
    const patched = await fetch(`${started.url}/api/bots/beta`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ purpose: "receives demo handoffs" }),
    });
    assert.equal(patched.ok, true);
    const snap = (await (await fetch(`${started.url}/api/snapshot`)).json()) as {
      protocol: readonly unknown[];
      bots: readonly { slug: string; purpose: string }[];
    };
    assert.ok(Array.isArray(snap.protocol));
    const beta = snap.bots.find((bot) => bot.slug === "beta");
    assert.equal(beta?.purpose, "receives demo handoffs");
  } finally {
    await started.stop();
  }
});

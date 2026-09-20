import assert from "node:assert/strict";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

import { startServer } from "../src/server/http.ts";
import { listComputerTree } from "../src/server/computer-tree.ts";
import { messagesForBot } from "../src/server/api.ts";
import { appendTranscript } from "../src/transcript.ts";
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
    const ingest = body.bots.find((row) => row.id === "bot_ingest") as
      | {
          id: string;
          activeLeafId?: string | null;
          messages: readonly { id: string; parentId?: string | null }[];
        }
      | undefined;
    assert.ok(ingest);
    if (ingest.messages.length > 0) {
      assert.equal(ingest.messages[0]?.parentId ?? null, null);
      for (let i = 1; i < ingest.messages.length; i += 1) {
        assert.equal(ingest.messages[i]?.parentId, ingest.messages[i - 1]?.id);
      }
      assert.equal(ingest.activeLeafId, ingest.messages.at(-1)?.id);
    }
    const taskPatch = await fetch(`${started.url}/api/bots/bot_ap/tasks/${encodeURIComponent("bot_ap")}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ modelSelection: { instanceId: "pi", model: "default" } }),
    });
    assert.equal(taskPatch.status, 200);
    const taskBody = (await taskPatch.json()) as { bot?: { id: string } };
    assert.equal(taskBody.bot?.id, "bot_ap");
    const config = (await (await fetch(`${started.url}/api/config`)).json()) as {
      onboarding: { hintsSeen: string[] };
    };
    assert.ok(config.onboarding.hintsSeen.includes("tour.composer"));
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
    const sendId = "send-ui-1";
    const uiSent = (await (
      await fetch(`${started.url}/api/bots/beta/messages`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: "visible operator line", sendId }),
      })
    ).json()) as {
      accepted: boolean;
      threadId: string;
      message: { id: string; sendId?: string; parentId?: string | null; role: string };
    };
    assert.equal(uiSent.accepted, true);
    assert.equal(uiSent.threadId, "bot_beta");
    assert.equal(uiSent.message.role, "user");
    assert.equal(uiSent.message.sendId, sendId);
    assert.equal(uiSent.message.id, `optimistic-${sendId}`);
  } finally {
    await started.stop();
  }
});

test("POST /api/bots/:slug/messages asking another Bot returns the peer text", async () => {
  const computer = makeComputer();
  const started = await startServer({
    computerRoot: computer,
    port: 0,
    workers: false,
    fakeWorkers: true,
  });
  try {
    const sent = (await (
      await fetch(`${started.url}/api/bots/alpha/messages`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: "Ask the Beta agent what color the sky is" }),
      })
    ).json()) as SendBody;
    assert.equal(sent.accepted, true);
    assert.ok(sent.handleId);
    const awaited = (await (
      await fetch(`${started.url}/api/handles/${sent.handleId}/await?timeoutMs=8000`, {
        method: "POST",
      })
    ).json()) as { done: boolean; status: string; result?: string };
    assert.equal(awaited.done, true);
    assert.equal(awaited.status, "completed");
    assert.match(awaited.result ?? "", /\[beta\]/i);
    const snap = (await (await fetch(`${started.url}/api/bots`)).json()) as {
      bots: readonly {
        id: string;
        messages: readonly { kind?: string; comm?: { groupId: string }; tool?: { name: string } }[];
      }[];
      groups: readonly { id: string; dm?: boolean }[];
    };
    const alpha = snap.bots.find((bot) => bot.id === "bot_alpha");
    const beta = snap.bots.find((bot) => bot.id === "bot_beta");
    assert.ok(alpha?.messages.some((row) => row.comm && /Messaged @Beta/.test(row.tool?.name ?? "")));
    assert.ok(beta?.messages.some((row) => row.comm && /Message from @Alpha/.test(row.tool?.name ?? "")));
    assert.ok(
      snap.groups.some(
        (group) => group.dm === true && group.id.includes("bot_alpha") && group.id.includes("bot_beta"),
      ),
    );
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

test("messagesForBot keeps operator wakes and peer handoff chips, not the pair log", () => {
  const computer = makeComputer();
  appendTranscript(computer, "bot_alpha", {
    seq: 1,
    t: "2026-09-20T00:00:00.000Z",
    kind: "turn.start",
    text: "wake from operator: list invoices",
    handleId: "h_1",
    from: "operator",
    to: "bot_alpha",
  });
  appendTranscript(computer, "bot_alpha", {
    seq: 2,
    t: "2026-09-20T00:00:01.000Z",
    kind: "handoff.sent",
    text: "handed to beta, handle h_2",
    handleId: "h_2",
    from: "bot_alpha",
    to: "bot_beta",
  });
  appendTranscript(computer, "bot_alpha", {
    seq: 3,
    t: "2026-09-20T00:00:02.000Z",
    kind: "turn.start",
    text: "wake from bot_beta: what color is the sky",
    handleId: "h_3",
    from: "bot_beta",
    to: "bot_alpha",
  });
  appendTranscript(computer, "bot_alpha", {
    seq: 4,
    t: "2026-09-20T00:00:03.000Z",
    kind: "handoff.done",
    text: "alpha finished handle h_3: blue",
    handleId: "h_3",
    from: "bot_beta",
    to: "bot_alpha",
  });
  const rows = messagesForBot(computer, "bot_alpha");
  assert.ok(rows.some((row) => row.role === "user" && row.text === "list invoices"));
  assert.ok(rows.some((row) => row.kind === "activity" && row.to === "bot_beta" && row.handleId === "h_2"));
  assert.equal(rows.some((row) => /sky/.test(row.text ?? "")), false);
  assert.equal(rows.some((row) => /blue/i.test(row.text ?? "")), false);

  appendTranscript(computer, "bot_beta", {
    seq: 2,
    t: "2026-09-20T00:00:01.000Z",
    kind: "handoff.received",
    text: "message from alpha, handle h_2",
    handleId: "h_2",
    from: "bot_alpha",
    to: "bot_beta",
  });
  const betaRows = messagesForBot(computer, "bot_beta");
  assert.ok(betaRows.some((row) => row.kind === "activity" && row.from === "bot_alpha" && row.handleId === "h_2"));
  assert.equal(betaRows.some((row) => /sky/.test(row.text ?? "")), false);
});

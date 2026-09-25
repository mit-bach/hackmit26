import assert from "node:assert/strict";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

import {
  CAMERA_DEMO_DIRECTOR,
  DemoRecordingMissingError,
  botsFromRoster,
  demoMeta,
  foldAwake,
  firstAwakeSeq,
  hasDemoRecording,
  loadDemoBundle,
  loadDemoScenes,
  mosaicLayout,
  playDelayMs,
  projectFrame,
  projectStageFrame,
  recordDemoSession,
  removeDemoRecording,
  saveDemoScenes,
  selectCast,
} from "../src/demo-replay.ts";
import { harnessPackageRoot } from "../src/pkg.ts";
import { protocolLogPath, seqPath, transcriptPath, piRuntimePath } from "../src/paths.ts";
import { startServer } from "../src/server/http.ts";
import { parseProtocolEvent } from "../src/protocol-log.ts";
import { appendTranscript } from "../src/transcript.ts";
import type { ProtocolEvent } from "../src/types.ts";
import { wipeRuntime } from "../src/wipe.ts";
import { makeComputer } from "./helpers.ts";

function ev(
  seq: number,
  type: string,
  to: string,
  slug: string,
  extra: Partial<ProtocolEvent> = {},
): ProtocolEvent {
  return {
    t: `2026-09-20T04:00:${String(seq).padStart(2, "0")}.000Z`,
    seq,
    type,
    from: extra.from ?? "operator",
    to,
    slug,
    handleId: extra.handleId ?? `h_${slug}_${seq}`,
    text: extra.text ?? `${type} ${slug}`,
    status: extra.status,
  };
}

function writeProtocol(computer: string, events: readonly ProtocolEvent[]): void {
  writeFileSync(
    protocolLogPath(computer),
    `${events.map((row) => JSON.stringify(row)).join("\n")}\n`,
    "utf8",
  );
  writeFileSync(seqPath(computer), `${events[events.length - 1]?.seq ?? 0}\n`, "utf8");
}

function sampleBots(): ReturnType<typeof botsFromRoster> {
  return [
    { id: "bot_email", slug: "email", name: "Email", purpose: "inbox", color: "teal" },
    { id: "bot_ap", slug: "ap", name: "AP", purpose: "bills", color: "blue" },
    { id: "bot_pay", slug: "pay", name: "Pay", purpose: "run", color: "purple" },
    { id: "bot_cash", slug: "cash", name: "Cash", purpose: "bank", color: "pink" },
  ];
}

test("mosaicLayout paints 1 full, 3 half-plus-stack, 4 quad", () => {
  assert.deepEqual(mosaicLayout(0), []);
  assert.deepEqual(mosaicLayout(1), [{ index: 0, left: 0, top: 0, width: 100, height: 100 }]);
  const two = mosaicLayout(2);
  assert.equal(two.length, 2);
  assert.equal(two[0]?.width, 50);
  assert.equal(two[1]?.left, 50);
  const three = mosaicLayout(3);
  assert.equal(three.length, 3);
  assert.deepEqual(three[0], { index: 0, left: 0, top: 0, width: 50, height: 100 });
  assert.deepEqual(three[1], { index: 1, left: 50, top: 0, width: 50, height: 50 });
  assert.deepEqual(three[2], { index: 2, left: 50, top: 50, width: 50, height: 50 });
  const four = mosaicLayout(4);
  assert.equal(four.length, 4);
  assert.equal(four[0]?.width, 50);
  assert.equal(four[0]?.height, 50);
  assert.equal(four[3]?.left, 50);
  assert.equal(four[3]?.top, 50);
  const five = mosaicLayout(5);
  assert.equal(five.length, 5);
  assert.equal(five[2]?.top, 50);
  assert.equal(mosaicLayout(6).length, 6);
  assert.equal(mosaicLayout(9).length, 9);
  assert.equal(mosaicLayout(10).length, 10);
  assert.equal(mosaicLayout(15).length, 15);
  assert.equal(mosaicLayout(16).length, 16);
  for (const cell of mosaicLayout(10)) {
    assert.ok(cell.width > 0);
    assert.ok(cell.height > 0);
  }
  const ten = mosaicLayout(10);
  assert.equal(ten[0]?.width, 25);
  assert.equal(mosaicLayout(16)[15]?.left, 75);
});

test("foldAwake wakes on turn.start and sleeps on turn.end", () => {
  const bots = sampleBots();
  const events: ProtocolEvent[] = [
    ev(1, "send.accepted", "bot_email", "email", { status: "accepted" }),
    ev(2, "turn.start", "bot_email", "email", { status: "running", handleId: "h_email_1" }),
    ev(3, "turn.end", "bot_email", "email", { status: "completed", handleId: "h_email_1" }),
    ev(4, "send.accepted", "bot_email", "email", { status: "accepted", handleId: "h_email_4" }),
    ev(5, "turn.start", "bot_email", "email", { status: "running", handleId: "h_email_4" }),
    ev(6, "send.accepted", "bot_ap", "ap", { from: "bot_email", status: "accepted", handleId: "h_ap_6" }),
    ev(7, "turn.start", "bot_ap", "ap", { from: "bot_email", status: "running", handleId: "h_ap_6" }),
    ev(8, "turn.end", "bot_ap", "ap", { from: "bot_email", status: "completed", handleId: "h_ap_6" }),
    ev(9, "turn.end", "bot_email", "email", { status: "completed", handleId: "h_email_4" }),
  ];
  assert.equal(foldAwake(bots, events.filter((row) => row.seq <= 1))[0]?.status, "queued");
  assert.deepEqual(
    foldAwake(bots, events.filter((row) => row.seq <= 2)).map((row) => row.slug),
    ["email"],
  );
  assert.equal(foldAwake(bots, events.filter((row) => row.seq <= 3)).length, 0);
  const two = foldAwake(bots, events.filter((row) => row.seq <= 7));
  assert.deepEqual(
    two.map((row) => row.slug),
    ["ap", "email"],
  );
  assert.equal(two[0]?.status, "running");
  assert.deepEqual(
    foldAwake(bots, events.filter((row) => row.seq <= 8)).map((row) => row.slug),
    ["email"],
  );
  assert.equal(foldAwake(bots, events).length, 0);
});

test("three and four overlapping turns layout as half-stack then quad", () => {
  const bots = sampleBots();
  const events: ProtocolEvent[] = [
    ev(1, "turn.start", "bot_email", "email"),
    ev(2, "turn.start", "bot_ap", "ap"),
    ev(3, "turn.start", "bot_pay", "pay"),
    ev(4, "turn.start", "bot_cash", "cash"),
  ];
  const three = foldAwake(bots, events.filter((row) => row.seq <= 3));
  assert.deepEqual(
    three.map((row) => row.slug),
    ["pay", "ap", "email"],
  );
  const threeLayout = mosaicLayout(three.length);
  assert.equal(threeLayout[0]?.width, 50);
  assert.equal(threeLayout[0]?.height, 100);
  const four = foldAwake(bots, events);
  assert.equal(four.length, 4);
  assert.equal(mosaicLayout(four.length)[0]?.height, 50);
});

test("projectFrame seq 0 is the wipe look", () => {
  const bots = sampleBots();
  const events = [ev(1, "turn.start", "bot_email", "email")];
  const frame = projectFrame(
    {
      source: "live",
      lastSeq: 1,
      bots,
      events,
      transcripts: { bot_email: [{ seq: 1, t: events[0]!.t, kind: "turn.start", text: "wake" }] },
      activities: {},
    },
    0,
  );
  assert.equal(frame.type, "wipe");
  assert.equal(frame.awake.length, 0);
  assert.equal(frame.layout.length, 0);
  const started = projectFrame(
    {
      source: "live",
      lastSeq: 1,
      bots,
      events,
      transcripts: { bot_email: [{ seq: 1, t: events[0]!.t, kind: "turn.start", text: "wake" }] },
      activities: {},
    },
    1,
  );
  assert.equal(started.awake.length, 1);
  assert.equal(started.awake[0]?.messages.length, 1);
});

test("projectStageFrame starts on the first send and holds the last Bot", () => {
  const bots = sampleBots();
  const events = [
    ev(1, "send.accepted", "bot_email", "email", { handleId: "h_email", text: "hello" }),
    ev(2, "turn.start", "bot_email", "email", { handleId: "h_email" }),
    ev(3, "turn.end", "bot_email", "email", { handleId: "h_email" }),
    ev(4, "send.accepted", "bot_ap", "ap", { handleId: "h_ap", text: "pay" }),
    ev(5, "turn.start", "bot_ap", "ap", { handleId: "h_ap" }),
    ev(6, "turn.end", "bot_ap", "ap", { handleId: "h_ap" }),
  ];
  const bundle = {
    source: "live" as const,
    lastSeq: 6,
    bots,
    events,
    transcripts: {},
    activities: {},
  };
  assert.equal(firstAwakeSeq(events), 1);
  const start = projectStageFrame(bundle, 0);
  assert.equal(start.seq, 1);
  assert.equal(start.awake.length, 1);
  assert.equal(start.awake[0]?.slug, "email");
  assert.equal(start.awake[0]?.held, false);
  const gap = projectStageFrame(bundle, 3);
  assert.equal(foldAwake(bots, events.filter((row) => row.seq <= 3)).length, 0);
  assert.equal(gap.awake.length, 1);
  assert.equal(gap.awake[0]?.slug, "email");
  assert.equal(gap.awake[0]?.held, true);
  const ap = projectStageFrame(bundle, 5);
  assert.equal(ap.awake.length, 1);
  assert.equal(ap.awake[0]?.slug, "ap");
  assert.equal(ap.awake[0]?.held, false);
  const end = projectStageFrame(bundle, 6);
  assert.equal(end.awake.length, 1);
  assert.equal(end.awake[0]?.slug, "ap");
  assert.equal(end.awake[0]?.held, true);
});

test("playDelayMs clamps wall-clock gaps", () => {
  const a = ev(1, "turn.start", "bot_email", "email");
  const b = ev(2, "turn.end", "bot_email", "email");
  assert.ok(playDelayMs(undefined, a, 1) > 0);
  const slow = playDelayMs(a, { ...b, t: "2026-09-20T04:10:00.000Z" }, 1);
  assert.equal(slow, 900);
  const fast = playDelayMs(a, b, 4);
  assert.ok(fast <= 225);
});

test("record survives wipe; live after wipe is empty", () => {
  const computer = makeComputer();
  const events = [
    ev(1, "send.accepted", "bot_alpha", "alpha", { handleId: "h_a", text: "hello alpha" }),
    ev(2, "turn.start", "bot_alpha", "alpha", { handleId: "h_a", text: "hello alpha" }),
    ev(3, "turn.end", "bot_alpha", "alpha", { handleId: "h_a", text: "ok" }),
  ];
  writeProtocol(computer, events);
  appendTranscript(computer, "bot_alpha", {
    seq: 2,
    t: events[1]!.t,
    kind: "turn.start",
    text: "wake from operator: hello alpha",
    handleId: "h_a",
    from: "operator",
    to: "bot_alpha",
  });
  const recorded = recordDemoSession(computer);
  assert.equal(recorded.lastSeq, 3);
  assert.equal(hasDemoRecording(computer), true);
  wipeRuntime(computer);
  assert.equal(hasDemoRecording(computer), true);
  const live = loadDemoBundle(computer, "live");
  assert.equal(live.lastSeq, 0);
  assert.equal(live.events.length, 0);
  const replay = loadDemoBundle(computer, "recording");
  assert.equal(replay.lastSeq, 3);
  assert.equal(replay.events.length, 3);
  const frame = projectFrame(replay, 2);
  assert.equal(frame.awake[0]?.slug, "alpha");
  assert.equal(existsSync(transcriptPath(computer, "bot_alpha")), true);
  removeDemoRecording(computer);
  assert.equal(hasDemoRecording(computer), false);
  assert.throws(() => loadDemoBundle(computer, "recording"), DemoRecordingMissingError);
});

test("GET /api/demo and POST /api/demo/record serve the protocol cursor", async () => {
  const computer = makeComputer();
  writeProtocol(computer, [
    ev(1, "turn.start", "bot_alpha", "alpha"),
    ev(2, "turn.start", "bot_beta", "beta"),
    ev(3, "turn.end", "bot_alpha", "alpha", { handleId: "h_alpha_1" }),
  ]);
  const started = await startServer({ computerRoot: computer, port: 0, workers: false });
  try {
    const bundle = (await (await fetch(`${started.url}/api/demo`)).json()) as {
      source: string;
      lastSeq: number;
      events: readonly { seq: number }[];
    };
    assert.equal(bundle.source, "live");
    assert.equal(bundle.lastSeq, 3);
    const frame = (await (await fetch(`${started.url}/api/demo/frame?seq=2`)).json()) as {
      seq: number;
      awake: readonly { slug: string }[];
      layout: readonly { width: number }[];
    };
    assert.equal(frame.seq, 2);
    assert.equal(frame.awake.length, 2);
    assert.equal(frame.layout[0]?.width, 50);
    const recorded = await fetch(`${started.url}/api/demo/record`, { method: "POST" });
    assert.equal(recorded.status, 200);
    wipeRuntime(computer);
    const afterWipe = (await (await fetch(`${started.url}/api/demo?source=recording`)).json()) as {
      source: string;
      lastSeq: number;
    };
    assert.equal(afterWipe.source, "recording");
    assert.equal(afterWipe.lastSeq, 3);
    const live = (await (await fetch(`${started.url}/api/demo?source=live`)).json()) as { lastSeq: number };
    assert.equal(live.lastSeq, 0);
    const meta = (await (await fetch(`${started.url}/api/demo/meta`)).json()) as {
      hasRecording: boolean;
      source: string;
    };
    assert.equal(meta.hasRecording, true);
    assert.equal(meta.source, "recording");
    const scenesPut = await fetch(`${started.url}/api/demo/scenes`, {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        scenes: [{ id: "two", title: "Two panes", seqFrom: 1, seqTo: 2, featured: ["alpha"], maxPanes: 2 }],
      }),
    });
    assert.equal(scenesPut.status, 200);
    const scenesGet = (await (await fetch(`${started.url}/api/demo/scenes`)).json()) as {
      scenes: readonly { id: string }[];
    };
    assert.equal(scenesGet.scenes[0]?.id, "two");
    const camera = (await (await fetch(`${started.url}/api/demo/frame?seq=2&maxPanes=1&featured=beta`)).json()) as {
      awake: readonly { slug: string }[];
      overflow: number;
    };
    assert.equal(camera.awake.length, 1);
    assert.equal(camera.awake[0]?.slug, "beta");
    assert.equal(camera.overflow, 1);
  } finally {
    await started.stop();
  }
});

test("CFO V2 office protocol folds Email then Email+AP", () => {
  const computer = join(harnessPackageRoot(), "..", "..", ".cfo-v2", "office", "computer");
  const protocolFile = protocolLogPath(computer);
  if (!existsSync(protocolFile)) {
    return;
  }
  const events: ProtocolEvent[] = [];
  for (const line of readFileSync(protocolFile, "utf8").split("\n")) {
    if (line.trim().length === 0) {
      continue;
    }
    const parsed = parseProtocolEvent(JSON.parse(line) as unknown);
    if (parsed) {
      events.push(parsed);
    }
  }
  if (events.length === 0) {
    return;
  }
  const bots = botsFromRoster(computer);
  assert.ok(bots.some((bot) => bot.slug === "email"));
  assert.ok(bots.some((bot) => bot.slug === "ap"));
  const atTwo = foldAwake(bots, events.filter((row) => row.seq <= 2));
  if (events.some((row) => row.seq === 2 && row.type === "turn.start" && row.slug === "email")) {
    assert.deepEqual(
      atTwo.map((row) => row.slug),
      ["email"],
    );
  }
  const overlap = events.filter((row) => row.seq <= 17);
  const atSeventeen = foldAwake(bots, overlap);
  if (
    overlap.some((row) => row.seq === 15 && row.type === "turn.start") &&
    overlap.some((row) => row.seq === 17 && row.type === "turn.start")
  ) {
    assert.ok(atSeventeen.some((row) => row.slug === "email"));
    assert.ok(atSeventeen.some((row) => row.slug === "ap"));
    assert.equal(mosaicLayout(atSeventeen.length)[0]?.width, 50);
  }
  const origin = firstAwakeSeq(events);
  const last = events[events.length - 1]?.seq ?? 0;
  const tape = {
    source: "live" as const,
    lastSeq: last,
    bots,
    events,
    transcripts: {},
    activities: {},
  };
  for (let seq = origin; seq <= last; seq += 1) {
    assert.ok(projectStageFrame(tape, seq).awake.length >= 1, `stage empty at seq ${seq}`);
  }
  const meta = demoMeta(computer, "live");
  assert.ok(meta.lastSeq >= (events[events.length - 1]?.seq ?? 0));
});

test("selectCast keeps featured Bots and reports overflow", () => {
  const bots = [
    ...sampleBots(),
    { id: "bot_close", slug: "close", name: "Close", purpose: "lock", color: "green" as const },
    { id: "bot_story", slug: "story", name: "Story", purpose: "gm", color: "coral" as const },
    { id: "bot_audit", slug: "audit", name: "Audit", purpose: "sample", color: "yellow" as const },
    { id: "bot_ctl_pay", slug: "ctl-pay", name: "ctl-pay", purpose: "review", color: "red" as const },
    { id: "bot_books", slug: "books", name: "Books", purpose: "erp", color: "teal" as const },
    { id: "bot_apply", slug: "apply", name: "Apply", purpose: "cash", color: "blue" as const },
  ];
  const events = bots.map((bot, index) => ev(index + 1, "turn.start", bot.id, bot.slug));
  const awake = foldAwake(bots, events);
  assert.equal(awake.length, 10);
  const cast = selectCast(awake, { maxPanes: 6, featured: ["ctl-pay", "audit"] });
  assert.equal(cast.visible.length, 6);
  assert.equal(cast.overflow.length, 4);
  assert.equal(cast.visible[0]?.slug, "ctl-pay");
  assert.ok(cast.visible.some((row) => row.slug === "audit"));
  const frame = projectFrame(
    {
      source: "live",
      lastSeq: 10,
      bots,
      events,
      transcripts: {},
      activities: {},
    },
    10,
    { ...CAMERA_DEMO_DIRECTOR, maxPanes: 6, featured: ["ctl-pay"] },
  );
  assert.equal(frame.awake.length, 6);
  assert.equal(frame.overflow, 4);
  assert.equal(frame.layout.length, 6);
  assert.equal(frame.awake[0]?.slug, "ctl-pay");
});

test("recordDemoSession does not scan pi-runtime.jsonl", () => {
  const computer = makeComputer();
  writeProtocol(computer, [
    ev(1, "send.accepted", "bot_alpha", "alpha", { handleId: "h_a", text: "hello alpha" }),
    ev(2, "turn.start", "bot_alpha", "alpha", { handleId: "h_a", text: "hello alpha" }),
    ev(3, "turn.end", "bot_alpha", "alpha", { handleId: "h_a", text: "ok" }),
  ]);
  appendTranscript(computer, "bot_alpha", {
    seq: 2,
    t: "2026-09-20T04:00:02.000Z",
    kind: "turn.start",
    text: "wake from operator: hello alpha",
    handleId: "h_a",
    from: "operator",
    to: "bot_alpha",
  });
  writeFileSync(piRuntimePath(computer, "bot_alpha"), `${"{\"type\":\"noise\"}\n".repeat(80_000)}`);
  const started = Date.now();
  const recorded = recordDemoSession(computer);
  assert.ok(Date.now() - started < 3_000, "record scanned pi-runtime");
  assert.equal(recorded.lastSeq, 3);
  const live = loadDemoBundle(computer, "live");
  assert.equal(live.activities.bot_alpha?.[0]?.type, "turn.started");
  const scenes = saveDemoScenes(computer, [
    {
      id: "alpha",
      title: "Alpha wake",
      seqFrom: 1,
      seqTo: 3,
      featured: ["alpha"],
      maxPanes: 1,
    },
  ]);
  assert.equal(loadDemoScenes(computer)[0]?.id, "alpha");
  assert.equal(scenes[0]?.maxPanes, 1);
});

test("live demo maps memory_read transcript rows onto activity chips", () => {
  const computer = makeComputer();
  writeProtocol(computer, [
    ev(1, "send.accepted", "bot_alpha", "alpha", { handleId: "h_mem", text: "recall Harbor" }),
    ev(2, "turn.start", "bot_alpha", "alpha", { handleId: "h_mem", text: "recall Harbor" }),
    ev(3, "tool.call", "bot_alpha", "alpha", { handleId: "h_mem", text: "memory_read path=MEMORY.md" }),
  ]);
  appendTranscript(computer, "bot_alpha", {
    seq: 2,
    t: "2026-09-20T04:00:02.000Z",
    kind: "turn.start",
    text: "wake from operator: recall Harbor",
    handleId: "h_mem",
    from: "operator",
    to: "bot_alpha",
  });
  appendTranscript(computer, "bot_alpha", {
    seq: 3,
    t: "2026-09-20T04:00:03.000Z",
    kind: "tool.call",
    text: "memory_read path=MEMORY.md",
    handleId: "h_mem",
    from: "bot_alpha",
    to: "bot_alpha",
  });
  const live = loadDemoBundle(computer, "live");
  assert.ok(live.activities.bot_alpha?.some((row) => row.title === "memory_read"));
  const frame = projectFrame(live, 3);
  const alpha = frame.awake.find((row) => row.slug === "alpha");
  assert.equal(alpha?.activity, "memory_read");
});
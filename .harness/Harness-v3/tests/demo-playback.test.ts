import assert from "node:assert/strict";
import { test } from "node:test";

import {
  DEFAULT_DEMO_PLAYBACK,
  beatSlotMs,
  buildWallMarks,
  clampPlaybackSettings,
  collectBeats,
  cursorAt,
  formatShowClock,
  projectPlayhead,
  revealText,
  showMsForBeat,
  showMsForSeq,
  timelineTotalMs,
} from "../src/demo-playback.ts";
import type { DemoBundle } from "../src/demo-replay.ts";

function sampleBundle(): DemoBundle {
  return {
    source: "recording",
    recordedAt: "2026-09-20T10:33:16.623Z",
    lastSeq: 5,
    bots: [
      { id: "bot_email", slug: "email", name: "Email", purpose: "inbox", color: "teal" },
      { id: "bot_ap", slug: "ap", name: "AP", purpose: "bills", color: "blue" },
    ],
    events: [
      {
        t: "2026-09-20T10:00:00.000Z",
        seq: 1,
        type: "send.accepted",
        from: "operator",
        to: "bot_email",
        slug: "email",
        handleId: "h_email_1",
        text: "hello email",
      },
      {
        t: "2026-09-20T10:00:00.100Z",
        seq: 2,
        type: "turn.start",
        to: "bot_email",
        slug: "email",
        handleId: "h_email_1",
      },
      {
        t: "2026-09-20T10:00:05.000Z",
        seq: 3,
        type: "send.accepted",
        from: "email",
        to: "bot_ap",
        slug: "ap",
        handleId: "h_ap_3",
        text: "please pay",
      },
      {
        t: "2026-09-20T10:00:05.100Z",
        seq: 4,
        type: "turn.start",
        to: "bot_ap",
        slug: "ap",
        handleId: "h_ap_3",
      },
      {
        t: "2026-09-20T10:00:08.000Z",
        seq: 5,
        type: "turn.end",
        to: "bot_email",
        slug: "email",
        handleId: "h_email_1",
      },
    ],
    transcripts: {
      bot_email: [
        { seq: 2, t: "2026-09-20T10:00:00.100Z", kind: "turn.start", text: "hello email" },
        { seq: 5, t: "2026-09-20T10:00:08.000Z", kind: "handoff.done", text: "invoice parked" },
      ],
      bot_ap: [
        { seq: 4, t: "2026-09-20T10:00:05.100Z", kind: "turn.start", text: "please pay this bill" },
      ],
    },
    activities: {},
  };
}

test("clampPlaybackSettings rejects junk without throwing", () => {
  const settings = clampPlaybackSettings({
    timing: "wall",
    wallSpeed: 99,
    beatMs: 10,
    beatSpeed: Number.NaN,
    streamHold: 4,
    showTimestamps: true,
  });
  assert.equal(settings.timing, "wall");
  assert.equal(settings.wallSpeed, 8);
  assert.equal(settings.beatMs, 200);
  assert.equal(settings.beatSpeed, DEFAULT_DEMO_PLAYBACK.beatSpeed);
  assert.equal(settings.streamHold, 0.45);
  assert.equal(settings.showTimestamps, true);
});

test("revealText is grapheme-safe", () => {
  assert.equal(revealText("hello", 0), "");
  assert.equal(revealText("hello", 1), "hello");
  assert.equal(revealText("👍👍👍", 0.2), "👍");
});

test("showMsForSeq lands on the last beat at or before that protocol seq", () => {
  const beats = collectBeats(sampleBundle());
  const settings = clampPlaybackSettings({ timing: "beat", beatMs: 1000, beatSpeed: 1, leadMs: 0 });
  assert.equal(cursorAt(beats, showMsForSeq(beats, 2, settings), settings).seq, 2);
  assert.equal(cursorAt(beats, showMsForSeq(beats, 3, settings), settings).seq, 2);
  assert.equal(cursorAt(beats, showMsForSeq(beats, 5, settings), settings).seq, 5);
  assert.equal(cursorAt(beats, showMsForSeq(beats, 99, settings), settings).seq, 5);
});

test("beat timeline is lead plus one slot per transcript line", () => {
  const bundle = sampleBundle();
  const beats = collectBeats(bundle);
  assert.equal(beats.length, 3);
  const settings = clampPlaybackSettings({ timing: "beat", beatMs: 1000, beatSpeed: 2, leadMs: 400 });
  assert.equal(beatSlotMs(settings), 500);
  assert.equal(timelineTotalMs(beats, settings), 400 + 3 * 500);
  const held = cursorAt(beats, 200, settings);
  assert.equal(held.seq, 2);
  assert.equal(held.beatIndex, 0);
  assert.equal(held.revealFrac, 0);
  const first = cursorAt(beats, 401, settings);
  assert.equal(first.seq, 2);
  assert.equal(first.beatIndex, 0);
});

test("beat speed does not change wall marks, and wall gap clamp is independent of beatMs", () => {
  const beats = collectBeats(sampleBundle());
  const wallA = clampPlaybackSettings({
    timing: "wall",
    wallSpeed: 2,
    wallMaxGapMs: 2000,
    beatMs: 400,
    leadMs: 0,
  });
  const wallB = clampPlaybackSettings({
    timing: "wall",
    wallSpeed: 2,
    wallMaxGapMs: 2000,
    beatMs: 4000,
    leadMs: 0,
  });
  const marksA = buildWallMarks(beats, wallA);
  const marksB = buildWallMarks(beats, wallB);
  assert.deepEqual(
    marksA.map((mark) => mark.showMs),
    marksB.map((mark) => mark.showMs),
  );
  const first = marksA.find((mark) => mark.beatIndex === 0);
  const second = marksA.find((mark) => mark.beatIndex === 1);
  assert.ok(first);
  assert.ok(second);
  const gap = (second?.showMs ?? 0) - (first?.showMs ?? 0);
  assert.equal(gap, 1000);
  const uncapped = clampPlaybackSettings({
    timing: "wall",
    wallSpeed: 1,
    wallMaxGapMs: 0,
    leadMs: 0,
  });
  const wide = buildWallMarks(beats, uncapped);
  const wideFirst = wide.find((mark) => mark.beatIndex === 0);
  const wideSecond = wide.find((mark) => mark.beatIndex === 1);
  assert.ok(wideFirst);
  assert.ok(wideSecond);
  assert.equal((wideSecond?.showMs ?? 0) - (wideFirst?.showMs ?? 0), 5000);
});

test("playhead streams the current beat then holds, without jumping panes", () => {
  const bundle = sampleBundle();
  const settings = clampPlaybackSettings({
    timing: "beat",
    beatMs: 2000,
    beatSpeed: 1,
    leadMs: 0,
    stream: true,
    streamCharsPerSec: 40,
    streamHold: 0.2,
  });
  const early = projectPlayhead(bundle, 40, settings);
  assert.equal(early.frame.awake.length, 1);
  assert.equal(early.frame.awake[0]?.slug, "email");
  const first = early.frame.awake[0]?.messages[0];
  assert.ok(first);
  const reveal = early.reveals[`bot_email:${first?.seq}:${first?.kind}`];
  assert.ok(reveal);
  assert.equal(reveal?.complete, false);
  assert.ok((reveal?.revealed.length ?? 0) > 0);
  assert.ok((reveal?.revealed.length ?? 0) < (first?.text.length ?? 0));
  const mid = projectPlayhead(bundle, showMsForBeat(collectBeats(bundle), 1, settings) + 80, settings);
  assert.equal(mid.frame.awake.length, 2);
  const slugs = mid.frame.awake.map((pane) => pane.slug).sort();
  assert.deepEqual(slugs, ["ap", "email"]);
  const instant = projectPlayhead(bundle, 40, { ...settings, stream: false });
  const instantRow = instant.frame.awake[0]?.messages[0];
  const instantReveal = instant.reveals[`bot_email:${instantRow?.seq}:${instantRow?.kind}`];
  assert.equal(instantReveal?.revealed, instantRow?.text);
  assert.equal(instantReveal?.complete, true);
});

test("formatShowClock pads seconds", () => {
  assert.equal(formatShowClock(0), "0:00");
  assert.equal(formatShowClock(65_000), "1:05");
});

test("playhead never drops to an empty stage after the first send", () => {
  const bundle: DemoBundle = {
    source: "recording",
    lastSeq: 6,
    bots: [
      { id: "bot_email", slug: "email", name: "Email", purpose: "inbox", color: "teal" },
      { id: "bot_ap", slug: "ap", name: "AP", purpose: "bills", color: "blue" },
    ],
    events: [
      {
        t: "2026-09-20T10:00:00.000Z",
        seq: 1,
        type: "send.accepted",
        to: "bot_email",
        slug: "email",
        handleId: "h_email",
        text: "hello email",
      },
      {
        t: "2026-09-20T10:00:00.100Z",
        seq: 2,
        type: "turn.start",
        to: "bot_email",
        slug: "email",
        handleId: "h_email",
      },
      {
        t: "2026-09-20T10:00:01.000Z",
        seq: 3,
        type: "turn.end",
        to: "bot_email",
        slug: "email",
        handleId: "h_email",
      },
      {
        t: "2026-09-20T10:00:08.000Z",
        seq: 4,
        type: "send.accepted",
        to: "bot_ap",
        slug: "ap",
        handleId: "h_ap",
        text: "please pay",
      },
      {
        t: "2026-09-20T10:00:08.100Z",
        seq: 5,
        type: "turn.start",
        to: "bot_ap",
        slug: "ap",
        handleId: "h_ap",
      },
      {
        t: "2026-09-20T10:00:09.000Z",
        seq: 6,
        type: "turn.end",
        to: "bot_ap",
        slug: "ap",
        handleId: "h_ap",
      },
    ],
    transcripts: {
      bot_email: [
        { seq: 2, t: "2026-09-20T10:00:00.100Z", kind: "turn.start", text: "hello email" },
        { seq: 3, t: "2026-09-20T10:00:01.000Z", kind: "handoff.done", text: "parked" },
      ],
      bot_ap: [
        { seq: 5, t: "2026-09-20T10:00:08.100Z", kind: "turn.start", text: "please pay this bill" },
        { seq: 6, t: "2026-09-20T10:00:09.000Z", kind: "handoff.done", text: "queued" },
      ],
    },
    activities: {},
  };
  const settings = clampPlaybackSettings({ timing: "beat", beatMs: 400, leadMs: 0, stream: false });
  const open = projectPlayhead(bundle, 0, settings);
  assert.equal(open.frame.awake.length, 1);
  assert.equal(open.frame.awake[0]?.slug, "email");
  const gap = projectPlayhead(bundle, showMsForBeat(collectBeats(bundle), 1, settings), settings);
  assert.equal(gap.seq, 3);
  assert.equal(gap.frame.awake.length, 1);
  assert.equal(gap.frame.awake[0]?.slug, "email");
  assert.equal(gap.frame.awake[0]?.held, true);
  const total = timelineTotalMs(collectBeats(bundle), settings);
  for (let show = 0; show <= total; show += 50) {
    const head = projectPlayhead(bundle, show, settings);
    assert.ok(head.frame.awake.length >= 1, `empty stage at ${show}ms seq ${head.seq}`);
  }
});

test("collectBeats and playhead honor director in/out seq", () => {
  const bundle = sampleBundle();
  const cut = collectBeats(bundle, { maxPanes: 6, featured: [], seqFrom: 4, seqTo: 5 });
  assert.ok(cut.every((beat) => beat.seq >= 4 && beat.seq <= 5));
  assert.ok(cut.length < collectBeats(bundle).length);
  const settings = clampPlaybackSettings({ timing: "beat", beatMs: 400, leadMs: 0, stream: false });
  const head = projectPlayhead(bundle, 0, settings, { maxPanes: 6, featured: ["ap"], seqFrom: 4, seqTo: 5 });
  assert.ok(head.seq >= 4);
});

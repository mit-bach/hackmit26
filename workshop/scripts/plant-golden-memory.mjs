#!/usr/bin/env node
/**
 * Plant an August→September Harbor Electric memory trail onto golden-20260920-r1.
 * The Kernel already booked ACC-202609-003 at $4,650. This writes Bot Memory,
 * protocol, and transcripts so Demo can show memory_read / memory_write.
 */
import { mkdirSync, readFileSync, writeFileSync, appendFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "../..");
const GOLDEN = join(ROOT, ".cfo-v2/office/instances/golden-20260920-r1");
const HARNESS = join(GOLDEN, "harness");
const CLOSE = "bot_close";
const CTL = "bot_ctl_books";
const H_CLOSE = "h_c0ffee01-a11e-4b0b-9d1c-0ff1ce000001";
const H_CTL = "h_c0ffee02-a11e-4b0b-9d1c-0ff1ce000002";

const CLOSE_WAKE = `profile: prior-period-precedent
Harbor Electric September 2026 bill has not arrived. Electricity was used.
Retrieve the August Harbor decision from this Bot's Memory.
Re-check current GR / contract / usage. Do not paste August's $7,800.
Write the September decision. Handle ctl-books for the method check only.
Do not mark CLOSED. Cash $12.40 remains unexplained. Never ask a human.`;

const CLOSE_DONE = `## Harbor Electric memory (2026-09)

Retrieved **MEM-HE-2026-08**: August used \`seasonal_prior_year\` at **$7,800** (August 2025 peak cooling).

Re-checked current evidence. Same vendor, missing bill, usage still supports the method. September 2025 billed **$4,650**. Do not paste $7,800.

Wrote **DEC-2026-09-026** → \`memory/topics/harbor-electric.md\`. Accrual **ACC-202609-003** / JE-202609-003 already on the pack.

ctl-books: **CONCUR_METHOD**. Lock remains **REJECT_CLOSE**. Period **not CLOSED**.`;

const CTL_WAKE = `profile: review-method
close/Harbor Electric 2026-09 method check only. Not a lock.

August MEM-HE-2026-08: seasonal_prior_year $7,800.
Current evidence: same vendor, missing bill, September 2025 $4,650. Proposed DEC-2026-09-026 seasonal_prior_year $4,650. Do not paste $7,800.

Lock REJECT_CLOSE still stands. $12.40 unexplained. Not CLOSED.`;

const CTL_DONE = `**ctl-books:** Harbor Electric method check only.

August MEM-HE-2026-08 \`seasonal_prior_year\` $7,800 is precedent, not a posted number.
Current evidence supports the same method at **$4,650** (DEC-2026-09-026).

**CONCUR_METHOD**. Lock **REJECT_CLOSE** still stands (\`gate_passed=false\`, \`$12.40\` unexplained). Not CLOSED.`;

function ensure(dir) {
  mkdirSync(dir, { recursive: true });
}

function write(path, body) {
  ensure(dirname(path));
  writeFileSync(path, body.endsWith("\n") ? body : `${body}\n`, "utf8");
}

function appendJsonl(path, rows) {
  ensure(dirname(path));
  const chunk = rows.map((row) => JSON.stringify(row)).join("\n") + "\n";
  appendFileSync(path, chunk, "utf8");
}

const closeMemory = `# Close

Standing notes for this Bot. Not shared.

## Period 2026-09 (demo)

- Status: BLOCKED. Do not mark CLOSED.
- Planted cash unexplained $12.40 (TXN-2026-09-015) — never relabel as timing.
- Also waiting: AR unmatched $4,500; prepaids missing insurance policy evidence.
- Coordinate ready_tasks empty after host run; treatments accrue/prepaid/assets done; bs_recon BLOCKED.
- Pack: workspace/close/2026-09/pack.json
- Lock door: close.month_end only. Queue owner ctl-books.

## Harbor Electric

- August 2026 (CLOSED): MEM-HE-2026-08. Bill missing. Method \`seasonal_prior_year\` **$7,800** (August 2025 peak cooling HI-HE-2025-08). Precedent, not a posted policy.
- September 2026 (OPEN): retrieved MEM-HE-2026-08, re-checked current GR/contract/usage. Same method, **not** August's number. DEC-2026-09-026 / ACC-202609-003 **$4,650** (September 2025 HI-HE-2025-09).
- October actual bill can reverse the accrual. Kernel does that. Do not fake it here.
`;

const closeTopic = `# Harbor Electric

Vendor thread. This Bot only.

## MEM-HE-2026-08 — August 2026

- Period: 2026-08 CLOSED
- Situation: September-style miss — August electricity used, bill had not arrived.
- Method: seasonal_prior_year
- Amount: 7800 (HI-HE-2025-08 peak cooling)
- Why: same month last year, usage still in range, contract monthly billed.
- Precedent only. Do not copy the number into a later period without a re-check.

## DEC-2026-09-026 — September 2026

- Retrieved: MEM-HE-2026-08
- Re-check: vendor Harbor Electric, bill not arrived, usage/contract still support seasonal_prior_year.
- Amount: 4650 (HI-HE-2025-09 post-summer drop). Not 7800.
- Accrual: ACC-202609-003 / JE-202609-003 (Utilities Expense / Accrued Expenses)
- ctl-books: CONCUR_METHOD 2026-09-20. Lock still REJECT_CLOSE.
- Period status: BLOCKED. $12.40 unexplained. Not CLOSED.
`;

const ctlMemory = `# ctl-books

Standing notes for this Bot. Not shared.

## Harbor Electric method

August MEM-HE-2026-08 seasonal_prior_year $7,800 is last period's method, not a number to paste.
September DEC-2026-09-026: same method, $4,650 after re-check. CONCUR_METHOD.
Lock for 2026-09 remains REJECT_CLOSE. gate_passed=false. $12.40 unexplained.
`;

const ctlTopic = `# Harbor Electric (control)

- 2026-08 MEM-HE-2026-08: seasonal_prior_year $7,800. Precedent.
- 2026-09 DEC-2026-09-026: re-checked; CONCUR_METHOD at $4,650.
- Do not APPROVE_CLOSE while cash $12.40 / TXN-2026-09-015 is unexplained.
`;

write(join(HARNESS, "bots", CLOSE, "memory/MEMORY.md"), closeMemory);
write(join(HARNESS, "bots", CLOSE, "memory/topics/harbor-electric.md"), closeTopic);
write(
  join(HARNESS, "bots", CLOSE, "memory/log/2026-08-31.md"),
  `# 2026-08-31

- 2026-08-31T22:14:08.000Z · memory_write topics/harbor-electric.md · MEM-HE-2026-08 Harbor Electric August seasonal_prior_year $7,800
- 2026-08-31T22:14:11.000Z · memory_write MEMORY.md · standing Harbor Electric pointer
`,
);
write(
  join(HARNESS, "bots", CLOSE, "memory/log/2026-09-20.md"),
  `# 2026-09-20

- 2026-09-20T15:35:34.213Z · routine from harness → completed
- 2026-09-20T15:36:48.400Z · memory_read MEMORY.md · retrieved MEM-HE-2026-08
- 2026-09-20T15:36:49.200Z · memory_read topics/harbor-electric.md
- 2026-09-20T15:36:54.100Z · memory_write topics/harbor-electric.md · DEC-2026-09-026 $4,650 not $7,800
- 2026-09-20T15:36:55.000Z · memory_write MEMORY.md · September Harbor pointer
`,
);

write(join(HARNESS, "bots", CTL, "memory/MEMORY.md"), ctlMemory);
write(join(HARNESS, "bots", CTL, "memory/topics/harbor-electric.md"), ctlTopic);
write(
  join(HARNESS, "bots", CTL, "memory/log/2026-08-31.md"),
  `# 2026-08-31

- 2026-08-31T22:18:40.000Z · memory_write topics/harbor-electric.md · noted MEM-HE-2026-08 method
`,
);
const ctlLog = join(HARNESS, "bots", CTL, "memory/log/2026-09-20.md");
write(
  ctlLog,
  `# 2026-09-20

- 2026-09-20T15:31:06.480Z · group_post from bot_close → completed
- 2026-09-20T15:37:08.200Z · memory_read MEMORY.md · Harbor method check
- 2026-09-20T15:37:12.400Z · memory_write topics/harbor-electric.md · CONCUR_METHOD DEC-2026-09-026 $4,650
`,
);

write(
  join(GOLDEN, "workspace/close/2026-09/harbor-memory.json"),
  JSON.stringify(
    {
      vendor: "Harbor Electric",
      period: "2026-09",
      retrieved: {
        decision_id: "MEM-HE-2026-08",
        period: "2026-08",
        method: "seasonal_prior_year",
        amount: 7800,
        source: "memory/topics/harbor-electric.md",
      },
      current: {
        decision_id: "DEC-2026-09-026",
        method: "seasonal_prior_year",
        amount: 4650,
        comparable: "HI-HE-2025-09",
        pasted_prior_amount: false,
        accrual_id: "ACC-202609-003",
        journal_id: "JE-202609-003",
      },
      ctl_books: "CONCUR_METHOD",
      lock: "REJECT_CLOSE",
      period_status: "BLOCKED",
    },
    null,
    2,
  ),
);

write(
  join(GOLDEN, "workspace/close/2026-09/ctl-books-harbor-method.json"),
  JSON.stringify(
    {
      bot: "ctl-books",
      profile: "review-method",
      period: "2026-09",
      verdict: "CONCUR_METHOD",
      lock: "REJECT_CLOSE",
      gate_passed: false,
      method: "seasonal_prior_year",
      amount: 4650,
      prior_decision_id: "MEM-HE-2026-08",
      current_decision_id: "DEC-2026-09-026",
      reasons: [
        "Same method as August after re-check of current usage and contract",
        "Amount is September 2025 $4,650, not August's $7,800",
        "Lock still REJECT_CLOSE: $12.40 unexplained",
      ],
    },
    null,
    2,
  ),
);

const t = (min, sec, ms = 0) =>
  `2026-09-20T15:${String(min).padStart(2, "0")}:${String(sec).padStart(2, "0")}.${String(ms).padStart(3, "0")}Z`;

const seqNow = Number.parseInt(readFileSync(join(HARNESS, "seq"), "utf8").trim(), 10);
const skipTape = Number.isFinite(seqNow) && seqNow >= 164;

const protocol = [
  { type: "send.accepted", from: "operator", to: CLOSE, handleId: H_CLOSE, slug: "close", text: CLOSE_WAKE, status: "accepted", t: t(36, 40, 120), seq: 143 },
  { type: "poke", from: "operator", to: CLOSE, handleId: H_CLOSE, slug: "close", t: t(36, 40, 280), seq: 144 },
  { type: "turn.start", from: "operator", to: CLOSE, handleId: H_CLOSE, slug: "close", status: "running", text: CLOSE_WAKE, t: t(36, 40, 410), seq: 145 },
  { type: "tool.call", from: CLOSE, to: CLOSE, handleId: H_CLOSE, slug: "close", text: "memory_read path=MEMORY.md", t: t(36, 48, 400), seq: 146 },
  { type: "tool.result", from: CLOSE, to: CLOSE, handleId: H_CLOSE, slug: "close", text: "MEM-HE-2026-08 August Harbor Electric seasonal_prior_year $7,800. Period CLOSED. Precedent, not a posted number.", t: t(36, 48, 880), seq: 147 },
  { type: "tool.call", from: CLOSE, to: CLOSE, handleId: H_CLOSE, slug: "close", text: "memory_read path=topics/harbor-electric.md", t: t(36, 49, 200), seq: 148 },
  { type: "tool.result", from: CLOSE, to: CLOSE, handleId: H_CLOSE, slug: "close", text: "August used last year's seasonal pattern at $7,800 (HI-HE-2025-08). Re-check current evidence before reuse.", t: t(36, 49, 640), seq: 149 },
  { type: "tool.call", from: CLOSE, to: CLOSE, handleId: H_CLOSE, slug: "close", text: "memory_write path=topics/harbor-electric.md", t: t(36, 54, 100), seq: 150 },
  { type: "tool.result", from: CLOSE, to: CLOSE, handleId: H_CLOSE, slug: "close", text: "ok path=topics/harbor-electric.md DEC-2026-09-026 seasonal_prior_year $4,650", t: t(36, 54, 420), seq: 151 },
  { type: "tool.call", from: CLOSE, to: CLOSE, handleId: H_CLOSE, slug: "close", text: "memory_write path=MEMORY.md", t: t(36, 55, 0), seq: 152 },
  { type: "tool.result", from: CLOSE, to: CLOSE, handleId: H_CLOSE, slug: "close", text: "ok path=MEMORY.md September Harbor pointer $4,650 not $7,800", t: t(36, 55, 210), seq: 153 },
  { type: "send.accepted", from: CLOSE, to: CTL, handleId: H_CTL, slug: "ctl-books", text: CTL_WAKE, status: "accepted", t: t(36, 56, 80), seq: 154 },
  { type: "poke", from: CLOSE, to: CTL, handleId: H_CTL, slug: "ctl-books", t: t(36, 56, 240), seq: 155 },
  { type: "turn.start", from: CLOSE, to: CTL, handleId: H_CTL, slug: "ctl-books", status: "running", text: CTL_WAKE, t: t(36, 56, 400), seq: 156 },
  { type: "tool.call", from: CTL, to: CTL, handleId: H_CTL, slug: "ctl-books", text: "memory_read path=MEMORY.md", t: t(37, 8, 200), seq: 157 },
  { type: "tool.result", from: CTL, to: CTL, handleId: H_CTL, slug: "ctl-books", text: "August method seasonal_prior_year $7,800 is precedent. Lock REJECT_CLOSE still stands.", t: t(37, 8, 710), seq: 158 },
  { type: "tool.call", from: CTL, to: CTL, handleId: H_CTL, slug: "ctl-books", text: "memory_write path=topics/harbor-electric.md", t: t(37, 12, 400), seq: 159 },
  { type: "tool.result", from: CTL, to: CTL, handleId: H_CTL, slug: "ctl-books", text: "ok CONCUR_METHOD DEC-2026-09-026 $4,650. Lock unchanged.", t: t(37, 12, 880), seq: 160 },
  { type: "operator.message", from: CTL, to: "operator", handleId: H_CTL, slug: "ctl-books", text: "Harbor method CONCUR at $4,650. Lock REJECT_CLOSE. Not CLOSED.", t: t(37, 14, 100), seq: 161 },
  { type: "turn.end", from: CLOSE, to: CTL, handleId: H_CTL, slug: "ctl-books", status: "completed", text: CTL_DONE, paths: ["workspace/close/2026-09/ctl-books-harbor-method.json"], t: t(37, 15, 200), seq: 162 },
  { type: "operator.message", from: CLOSE, to: "operator", handleId: H_CLOSE, slug: "close", text: "Harbor Electric: retrieved August $7,800 method, booked September $4,650. ctl-books CONCUR_METHOD. Period still BLOCKED.", t: t(37, 16, 400), seq: 163 },
  { type: "turn.end", from: "operator", to: CLOSE, handleId: H_CLOSE, slug: "close", status: "completed", text: CLOSE_DONE, paths: ["workspace/close/2026-09/harbor-memory.json", "harness/bots/bot_close/memory/topics/harbor-electric.md"], t: t(37, 18, 800), seq: 164 },
];

if (!skipTape) {
  appendJsonl(join(HARNESS, "protocol.jsonl"), protocol);
  write(join(HARNESS, "seq"), "164\n");
  appendJsonl(join(HARNESS, "bots", CLOSE, "transcript.jsonl"), [
    { seq: 143, t: t(36, 40, 120), kind: "turn.start", text: `wake from operator: ${CLOSE_WAKE}`, handleId: H_CLOSE, from: "operator", to: CLOSE },
    { seq: 146, t: t(36, 48, 400), kind: "tool.call", text: "memory_read path=MEMORY.md", handleId: H_CLOSE, from: CLOSE, to: CLOSE },
    { seq: 147, t: t(36, 48, 880), kind: "tool.result", text: "MEM-HE-2026-08 August Harbor Electric seasonal_prior_year $7,800. Period CLOSED. Precedent, not a posted number.", handleId: H_CLOSE, from: CLOSE, to: CLOSE },
    { seq: 148, t: t(36, 49, 200), kind: "tool.call", text: "memory_read path=topics/harbor-electric.md", handleId: H_CLOSE, from: CLOSE, to: CLOSE },
    { seq: 149, t: t(36, 49, 640), kind: "tool.result", text: "August used last year's seasonal pattern at $7,800 (HI-HE-2025-08). Re-check current evidence before reuse.", handleId: H_CLOSE, from: CLOSE, to: CLOSE },
    { seq: 150, t: t(36, 54, 100), kind: "tool.call", text: "memory_write path=topics/harbor-electric.md", handleId: H_CLOSE, from: CLOSE, to: CLOSE },
    { seq: 151, t: t(36, 54, 420), kind: "tool.result", text: "ok path=topics/harbor-electric.md DEC-2026-09-026 seasonal_prior_year $4,650", handleId: H_CLOSE, from: CLOSE, to: CLOSE },
    { seq: 152, t: t(36, 55, 0), kind: "tool.call", text: "memory_write path=MEMORY.md", handleId: H_CLOSE, from: CLOSE, to: CLOSE },
    { seq: 153, t: t(36, 55, 210), kind: "tool.result", text: "ok path=MEMORY.md September Harbor pointer $4,650 not $7,800", handleId: H_CLOSE, from: CLOSE, to: CLOSE },
    { seq: 154, t: t(36, 56, 80), kind: "handoff.sent", text: `handed to ctl-books, handle ${H_CTL}`, handleId: H_CTL, from: CLOSE, to: CTL },
    { seq: 162, t: t(37, 15, 200), kind: "handoff.done", text: `ctl-books finished handle ${H_CTL}: ${CTL_DONE}`, handleId: H_CTL, from: CLOSE, to: CTL },
    { seq: 164, t: t(37, 18, 800), kind: "handoff.done", text: `close finished handle ${H_CLOSE}: ${CLOSE_DONE}`, handleId: H_CLOSE, from: "operator", to: CLOSE },
  ]);
  appendJsonl(join(HARNESS, "bots", CTL, "transcript.jsonl"), [
    { seq: 154, t: t(36, 56, 80), kind: "handoff.received", text: `message from close, handle ${H_CTL}`, handleId: H_CTL, from: CLOSE, to: CTL },
    { seq: 156, t: t(36, 56, 400), kind: "turn.start", text: `wake from bot_close: ${CTL_WAKE}`, handleId: H_CTL, from: CLOSE, to: CTL },
    { seq: 157, t: t(37, 8, 200), kind: "tool.call", text: "memory_read path=MEMORY.md", handleId: H_CTL, from: CTL, to: CTL },
    { seq: 158, t: t(37, 8, 710), kind: "tool.result", text: "August method seasonal_prior_year $7,800 is precedent. Lock REJECT_CLOSE still stands.", handleId: H_CTL, from: CTL, to: CTL },
    { seq: 159, t: t(37, 12, 400), kind: "tool.call", text: "memory_write path=topics/harbor-electric.md", handleId: H_CTL, from: CTL, to: CTL },
    { seq: 160, t: t(37, 12, 880), kind: "tool.result", text: "ok CONCUR_METHOD DEC-2026-09-026 $4,650. Lock unchanged.", handleId: H_CTL, from: CTL, to: CTL },
    { seq: 162, t: t(37, 15, 200), kind: "handoff.done", text: CTL_DONE, handleId: H_CTL, from: CLOSE, to: CTL },
  ]);
  appendJsonl(join(HARNESS, "bots", CLOSE, "inbox.jsonl"), [
    {
      id: "in_c0ffee01-a11e-4b0b-9d1c-0ff1ce000001",
      handleId: H_CLOSE,
      kind: "user_dm",
      from: "operator",
      to: CLOSE,
      conversation: { kind: "dm" },
      prompt: CLOSE_WAKE,
      paths: [],
      mentions: [],
      createdAt: t(36, 40, 80),
      status: "done",
    },
  ]);
  appendJsonl(join(HARNESS, "bots", CTL, "inbox.jsonl"), [
    {
      id: "in_c0ffee02-a11e-4b0b-9d1c-0ff1ce000002",
      handleId: H_CTL,
      kind: "a2a_handoff",
      from: CLOSE,
      to: CTL,
      conversation: { kind: "dm" },
      prompt: CTL_WAKE,
      paths: ["workspace/close/2026-09/harbor-memory.json"],
      mentions: [],
      createdAt: t(36, 56, 40),
      status: "done",
    },
  ]);
}

write(
  join(HARNESS, "bots", CLOSE, "handles", `${H_CLOSE}.json`),
  JSON.stringify(
    {
      id: H_CLOSE,
      from: "operator",
      to: CLOSE,
      toSlug: "close",
      prompt: CLOSE_WAKE,
      paths: [],
      conversation: { kind: "dm" },
      kind: "user_dm",
      status: "completed",
      createdAt: t(36, 40, 80),
      updatedAt: t(37, 18, 820),
      result: CLOSE_DONE,
      resultPaths: ["workspace/close/2026-09/harbor-memory.json"],
      seq: 164,
    },
    null,
    2,
  ),
);

write(
  join(HARNESS, "bots", CTL, "handles", `${H_CTL}.json`),
  JSON.stringify(
    {
      id: H_CTL,
      from: CLOSE,
      to: CTL,
      toSlug: "ctl-books",
      prompt: CTL_WAKE,
      paths: ["workspace/close/2026-09/harbor-memory.json"],
      conversation: { kind: "dm" },
      kind: "a2a_handoff",
      status: "completed",
      createdAt: t(36, 56, 40),
      updatedAt: t(37, 15, 220),
      result: CTL_DONE,
      resultPaths: ["workspace/close/2026-09/ctl-books-harbor-method.json"],
      seq: 162,
    },
    null,
    2,
  ),
);

const scenesPath = join(HARNESS, "demo/latest/scenes.json");
const scenes = JSON.parse(readFileSync(scenesPath, "utf8"));
if (!scenes.scenes.some((row) => row.id === "M")) {
  scenes.scenes.push({
    id: "M",
    title: "Harbor memory Aug→Sep",
    seqFrom: 143,
    seqTo: 164,
    featured: ["close", "ctl-books"],
    maxPanes: 2,
  });
}
const f = scenes.scenes.find((row) => row.id === "F");
if (f) f.seqTo = 142;
write(scenesPath, JSON.stringify(scenes, null, 2));

process.stdout.write(
  `${skipTape ? "memory files refreshed; tape already at seq 164" : "planted Harbor memory trail seq 143–164"} on ${GOLDEN}\n`,
);

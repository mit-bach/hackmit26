import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { callConnectedTool } from "../cfo/engine/call.ts";
import { completeStep } from "../cfo/engine/complete.ts";
import { readBillFacts } from "../cfo/engine/kernel.ts";
import { readItem, seedItem } from "../cfo/engine/ledger.ts";

const computerRoot = join(import.meta.dirname, "..", "instances", "prove", "engine");

function seedBill(id = "bill:INV-001"): void {
  const facts = readBillFacts(computerRoot, "INV-001");
  assert.equal(facts.amount, 12450);
  assert.equal(facts.po_id, "PO-101");
  assert.equal(facts.receipt_id, "GR-101");
  seedItem(computerRoot, {
    id,
    workflow: "open_bill",
    step: "match",
    owner: "ap",
    facts: {
      invoice_id: "INV-001",
      amount: facts.amount,
      po_id: facts.po_id,
      receipt_id: facts.receipt_id,
    },
    pendingWrite: null,
    history: [],
  });
}

function approve(id: string) {
  return completeStep({
    computerRoot,
    caller: "ap",
    item: id,
    wakeStep: "match",
    result: { decision: "APPROVE", reason: "clean three-way match", evidence_used: ["PO-101", "GR-101"] },
    paths: ["sandboxes/ap/packets/INV-001.json"],
  });
}

seedBill();
const prior = callConnectedTool({
  computerRoot,
  caller: "ap",
  item: "bill:INV-001",
  op: "tools.get_prior_cases",
  args: { exception_type: "vendor_mismatch", vendor: "Acme Supplies" },
});
assert.equal(prior.ok, false);
assert.equal(prior.error, "get_prior_cases is not available at step match of bill:INV-001");

const prose = completeStep({
  computerRoot,
  caller: "ap",
  item: "bill:INV-001",
  wakeStep: "match",
  result: "I do not concur",
});
assert.equal(prose.ok, false);
assert.match(prose.error ?? "", /schema/);
const also = completeStep({
  computerRoot,
  caller: "ap",
  item: "bill:INV-001",
  wakeStep: "match",
  result: "CONCUR is not possible",
});
assert.equal(also.ok, false);
assert.match(also.error ?? "", /schema/);
assert.equal(readItem(computerRoot, "bill:INV-001").history.length, 0);
assert.equal(readItem(computerRoot, "bill:INV-001").step, "match");

const approved = approve("bill:INV-001");
assert.equal(approved.ok, true);
if (!approved.ok || !approved.enqueued) throw new Error(approved.ok ? "missing enqueue" : approved.error);
assert.equal(approved.enqueued.owner, "ctl-pay");
assert.equal(readItem(computerRoot, "bill:INV-001").step, "review-match");
const handlePath = join(
  computerRoot,
  "harness",
  "bots",
  "bot_ctl_pay",
  "handles",
  `${approved.enqueued.handleId}.json`,
);
const handle = JSON.parse(readFileSync(handlePath, "utf8")) as { prompt?: string };
assert.equal(typeof handle.prompt, "string");
assert.doesNotMatch(handle.prompt ?? "", /bot_send_prompt/);
assert.match(handle.prompt ?? "", /kind: item_step/);
assert.match(handle.prompt ?? "", /step: review-match/);
console.log("HANDLE", approved.enqueued.handleId);

const refused = completeStep({
  computerRoot,
  caller: "ctl-pay",
  item: "bill:INV-001",
  wakeStep: "review-match",
  result: { decision: "REFUSE", reason: "packet incomplete" },
});
assert.equal(refused.ok, true);
const afterRefuse = readItem(computerRoot, "bill:INV-001");
assert.equal(afterRefuse.history.at(-1)?.result.decision, "REFUSE");
const writeAfterRefuse = callConnectedTool({
  computerRoot,
  caller: "ctl-pay",
  item: "bill:INV-001",
  op: "accrual.tools.create_accrual",
  args: { vendor: "Acme Supplies", period: "2026-09", method: "trailing_average", confidence: 0.5, evidence: [], reasoning_summary: "no" },
  idempotencyKey: "write-refuse",
});
assert.equal(writeAfterRefuse.ok, false);
assert.equal(readItem(computerRoot, "bill:INV-001").history.at(-1)?.result.decision, "REFUSE");
assert.notEqual(writeAfterRefuse.error, "CONCUR");

seedBill();
const again = approve("bill:INV-001");
assert.equal(again.ok, true);
const concurred = completeStep({
  computerRoot,
  caller: "ctl-pay",
  item: "bill:INV-001",
  wakeStep: "review-match",
  result: { decision: "CONCUR", reason: "kernel allows the match", evidence_used: ["PO-101"] },
});
assert.equal(concurred.ok, true);
if (!concurred.ok || !concurred.enqueued) throw new Error("pay run was not enqueued");
assert.equal(concurred.enqueued.owner, "pay");
assert.equal(readItem(computerRoot, "bill:INV-001").history.at(-1)?.result.decision, "CONCUR");

seedItem(computerRoot, {
  id: "accrual:2026-09-acme",
  workflow: "month_end",
  step: "accrue",
  owner: "close",
  facts: { vendor: "Acme Supplies", period: "2026-09" },
  pendingWrite: null,
  history: [],
});
const firstWrite = callConnectedTool({
  computerRoot,
  caller: "close",
  item: "accrual:2026-09-acme",
  op: "accrual.tools.create_accrual",
  args: { vendor: "Acme Supplies", period: "2026-09", method: "trailing_average", confidence: 0.8, evidence: ["usage"], reasoning_summary: "missing invoice" },
  idempotencyKey: "accrual-k",
});
assert.equal(firstWrite.ok, false);
assert.equal(firstWrite.pending, true);
assert.ok(firstWrite.enqueued?.handleId);
const verifierHandle = firstWrite.enqueued?.handleId ?? "";
assert.notEqual(verifierHandle, "null");
const verified = completeStep({
  computerRoot,
  caller: "ctl-books",
  item: "accrual:2026-09-acme",
  wakeStep: "review-treatment",
  result: { decision: "CONCUR", reason: "estimate matches the kernel" },
});
assert.equal(verified.ok, true);
const mismatched = callConnectedTool({
  computerRoot,
  caller: "close",
  item: "accrual:2026-09-acme",
  op: "accrual.tools.create_accrual",
  args: { vendor: "Acme Supplies", period: "2026-09", method: "trailing_average", confidence: 0.1, evidence: ["other"], reasoning_summary: "different" },
  idempotencyKey: "accrual-k",
});
assert.equal(mismatched.ok, false);
assert.match(mismatched.error ?? "", new RegExp(verifierHandle));
assert.doesNotMatch(mismatched.error ?? "", /null/);
assert.equal(readItem(computerRoot, "accrual:2026-09-acme").pendingWrite?.verifierHandle, verifierHandle);

seedItem(computerRoot, {
  id: "close:2026-09-accrue",
  workflow: "month_end",
  step: "accrue",
  owner: "close",
  facts: { period: "2026-09" },
  pendingWrite: null,
  history: [],
});
const treatment = completeStep({
  computerRoot,
  caller: "close",
  item: "close:2026-09-accrue",
  wakeStep: "accrue",
  result: { decision: "PROPOSE", reason: "invoice missing", evidence_used: [] },
});
assert.equal(treatment.ok, true);
if (!treatment.ok || !treatment.enqueued) throw new Error("month_end did not enqueue");
assert.equal(treatment.enqueued.owner, "ctl-books");
assert.equal(readItem(computerRoot, "close:2026-09-accrue").step, "review-treatment");

seedItem(computerRoot, {
  id: "cash:line-1",
  workflow: "cash_line",
  step: "reconcile",
  owner: "cash",
  facts: { line_id: "line-1", amount: 10 },
  pendingWrite: null,
  history: [],
});
const rec = completeStep({
  computerRoot,
  caller: "cash",
  item: "cash:line-1",
  wakeStep: "reconcile",
  result: { decision: "UNEXPLAINED", reason: "no candidate" },
});
assert.equal(rec.ok, true);
if (!rec.ok || !rec.enqueued) throw new Error("cash_line did not enqueue");
assert.equal(rec.enqueued.owner, "ctl-cash");
assert.equal(readItem(computerRoot, "cash:line-1").step, "review-rec");

console.log("PROOF_E_OK");
console.log("HANDLE", approved.enqueued.handleId);
console.log("VERIFIER_HANDLE", verifierHandle);

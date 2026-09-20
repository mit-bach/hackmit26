# Invoice error detection scorecard

Evaluated the current 15-agent Maximor kernel as a black-box finance product. Entry points: `classify_text` / `inbox.handoff` → `decide_ap(live=False)` → `policy_eligible_for_pool`. The old 43-agent `run_ap_workflow` was not used.

## 1. Executive summary

**Can the agentic system find planted invoice errors?** After recovering ground truth and repairing four deterministic gaps: **yes, on this pack.**

| Metric | Baseline (pre-fix) | After fixes | Delta |
| --- | --- | --- | --- |
| Total cases | 84 | 91 | +7 (red-team / mutation / identity) |
| Correct | 67 | 91 | +24 |
| Incorrect | 17 | 0 | −17 |
| False positives | 7 | 0 | −7 |
| False negatives | 10 | 0 | −10 |
| Error detection recall | 83.87% (52/62 planted) | 100% (69/69) | +16.13 pp |
| Error detection precision | 91.23% | 100% | +8.77 pp |
| Clean-case accuracy | 77.27% (17/22) | 100% (22/22) | +22.73 pp |
| Action accuracy | 79.76% | 100% | +20.24 pp |

The system already caught three-way match holds (partial receipt, price mismatch, missing GR, unapproved PO, approval limit, handwritten duplicates). It failed on **document classification**, **invoice-number identity**, **line-item arithmetic**, and **already-paid payment scheduling**. Those were pre-existing kernel bugs, not 43→15 migration artifacts.

Matching APPROVE on a clean paid invoice is still correct. Paying it again is not. Those two decisions are now split.

## 2. Dataset / test inventory

Full case table: `docs/invoice_error_eval_inventory.md`.

| Pack | Location | Cases in this eval |
| --- | --- | --- |
| Canonical demo AP | `.cfo/data/demo/invoices.json` + `sample_data/agents/ap_ar.py` | 20 (INV-001–021 except INV-011 which is not operational AP) |
| Demo ingestion | `.cfo/data/demo/ingestion/emails.json` | 10 MSG-E-* |
| Handwritten fixtures | `.cfo/data/invoices.json` | 10 (same IDs, different facts) |
| Inbox fixtures | `.cfo/inbox/fixtures.py` | 10 |
| Holdout AP | `.cfo/discrepancy/holdout_catalog.py` | 7 |
| Adversarial classification | eval runner | 8 + 3 red-team |
| Identity / math / mutations / memory / restart / cross-workflow | eval runner | remaining |

Git history: commit `9917178` moved `data/` → `.cfo/data/`. No AP planted-error pack was lost. `tests/test_audit_adversarial.py` still exists under `.cfo/tests/`.

**Two overlapping ID spaces.** Demo INV-018 is a clean Dell invoice. Handwritten INV-018 is a Notion duplicate of INV-010. They must not be scored as one company.

## 3. Total planted errors

- Baseline pack: **62** planted / **22** clean
- After adding mutations, identity punctuation, and independent red-team docs: **69** planted / **22** clean

## 4. Errors correctly detected

After fixes: **69 / 69** planted cases correct, including detection **and** downstream action (no pay on holds or already-paid bills).

Already-correct at baseline (not broken by the 15-agent path):

- DEMO-INV-003 partial receipt HOLD
- DEMO-INV-004 material amount HOLD
- DEMO-INV-005 / 010 goods not received HOLD
- DEMO-INV-006 / 007 duplicate HOLD
- DEMO-INV-008 PO not approved HOLD
- DEMO-INV-009 approval limit HOLD
- DEMO-INV-020 missing PO HOLD
- DEMO-INV-021 vendor alias APPROVE with CASE-001
- Handwritten FIX-INV-011–020 (small variance APPROVE, material HOLD, missing PO/GR, alias, duplicate, partial, unapproved PO)
- Holdout HO-AP-001–008 match/approval/duplicate holds
- Inbox quote/PO/GR/statement/payment/credit routing
- Inbox business duplicate

## 5. Errors missed (baseline false negatives)

| Case | Miss | Root cause |
| --- | --- | --- |
| DEMO-MSG-E-PO | PO classified `not_invoice` instead of `purchase_order` | `classify_text` only treated requisitions as POs |
| DEMO-MSG-E-RCPT | Uber receipt classified `not_invoice` instead of `receipt` | Receipt tokens required “uber trip receipt”; `"this is not an invoice"` stole other types |
| ADV-QUOTE-LAYOUT | Quote with vendor/lines/total/`valid through` → `not_invoice` | Missing quote tokens |
| ADV-PO-LAYOUT | PO layout → `not_invoice` | Same PO-token gap |
| ADV-RECEIPT-PAID | Paid receipt → `not_invoice` | Same receipt-token gap |
| ADV-CREDIT-MEMO | Credit memo → `statement` | `"this is not an invoice"` mapped everything to statement |
| ID-NORM-PUNCT | `ABC/23781` ≠ `ABC-23781` canonical key | `identity.normalize_invoice_number` only stripped spaces |
| MATH-LINE-SUM | Line items 80+50 vs subtotal 100 accepted | No line-item sum/extension check |
| XWF-PAID-NO-RESCHEDULE | INV-001 still payment-eligible after PAY-AP-001 | `policy_eligible_for_pool` ignored `canonical/vendor_payments.json` |
| RESTART-DUP | Eval expected transport `DUPLICATE_DELIVERY` after inbox reset | Ground-truth error: overlay reload correctly yields `BUSINESS_DUPLICATE` |

MUT-AMT-1 / MUT-AMT-001 were also incorrect because clones reused INV-001’s vendor invoice number (duplicate HOLD). That was a **test construction** bug, not a detector miss.

## 6. False positives (baseline)

Clean demo invoices INV-001, 014, 015, 016, 017 were marked FP because matching correctly APPROVEd while the scheduler still treated them as payable. After the payment-state fix they remain **APPROVE** for three-way match and **ineligible** for the pay pool.

DEMO-MSG-E-DUP-001 (same invoice, different filename) was a scoring bug: classifying a duplicate copy as `invoice` is required; registration must collapse it. Inbox `INBOX-DUP-BUSINESS` already held the second copy.

No clean three-way invoice was held for a phantom match exception.

## 7. Incorrect actions after correct detection

At baseline, AP matching of INV-001 was correct (APPROVE, no exceptions) but **pay.schedule would still put it in the pool**. Same for grouped Northline INV-014–016, Helios fee-netted INV-017, and early-paid GitHub INV-012 (`PAY-AP-012`).

Holds were already payment-ineligible via `BLOCKING_EXCEPTIONS`.

## 8. Category performance (after)

| CATEGORY | CASES | CORRECT | MISSED | FALSE POSITIVES | ACTION CORRECT |
| --- | --- | --- | --- | --- | --- |
| AS clean / control | 22 | 22 | 0 | 0 | 22 |
| A duplicate | 10 | 10 | 0 | 0 | 10 |
| B formatted duplicate | 4 | 4 | 0 | 0 | 4 |
| C same invoice different filename | 1 | 1 | 0 | 0 | 1 |
| D quote as invoice | 5 | 5 | 0 | 0 | 5 |
| E receipt as invoice | 4 | 4 | 0 | 0 | 4 |
| F statement as invoice | 2 | 2 | 0 | 0 | 2 |
| G PO as invoice | 5 | 5 | 0 | 0 | 5 |
| H bank/card as invoice | 1 | 1 | 0 | 0 | 1 |
| I vendor mismatch / alias | 5 | 5 | 0 | 0 | 5 |
| P wrong total | 2 | 2 | 0 | 0 | 2 |
| Q line-item sum | 1 | 1 | 0 | 0 | 1 |
| T PO price mismatch | 4 | 4 | 0 | 0 | 4 |
| W goods not received (held/paid) | 3 | 3 | 0 | 0 | 3 |
| X partial receipt | 3 | 3 | 0 | 0 | 3 |
| Y missing PO | 5 | 5 | 0 | 0 | 5 |
| Z missing GR | 3 | 3 | 0 | 0 | 3 |
| AB already paid | 2 | 2 | 0 | 0 | 2 |
| AC credit memo | 2 | 2 | 0 | 0 | 2 |
| AF fee-netted wire (AP clean) | 1 | 1 | 0 | 0 | 1 |
| AH invalid approval | 4 | 4 | 0 | 0 | 4 |
| AP OCR messy invoice | 1 | 1 | 0 | 0 | 1 |
| AQ missing required field | 1 | 1 | 0 | 0 | 1 |

## 9. Root causes

| Code | Meaning | Where it showed up |
| --- | --- | --- |
| B DOCUMENT CLASSIFICATION | `classify_text` weak PO/quote/receipt/credit tokens; inbox mapped `receipt` → `GOODS_RECEIPT` | MSG-E-PO, MSG-E-RCPT, ADV-* |
| C/D CANONICAL / DUPLICATE | identity key kept punctuation; `existing_ap_match` used exact upper-case | ABC/23781 vs ABC-23781 |
| G DETERMINISTIC FINANCE LOGIC | no line-item sum/extension validation | MATH-LINE-SUM |
| R ACCOUNTING / PAYMENT STATE | vendor payments unused by scheduler; `decide_ap` later incorrectly reused pool eligibility as a match HOLD | INV-001/012/014–017 |
| T GROUND-TRUTH PROBLEM | +$1 treated as material despite P-009 $300/3%; restart expected transport duplicate after inbox reset; `Acme Supplies Inc` is the same vendor after suffix strip | MUT-AMT-1, RESTART-DUP, MUT-VENDOR-SPELL |
| V PRE-EXISTING BUG | all product misses existed in kernel Python, not in grain-bot wiring | classification, identity, payments, math |
| J WRONG SKILL ASSIGNMENT | source `office/bots/ap/roster.json` omitted `prior-period-precedent` (compiled harness roster already had it) | grain bot_ap investigate |

Not “LLM mistake.” `decide_ap(live=False)` is Kernel policy.

## 10. Repairs made

1. **`classify_text`**: ordered detectors for credit memo, quote (`valid through` / `this is a quote`), purchase order, packing list, bank/card, reimbursement vs paid receipt. `"this is not an invoice"` is no longer a statement.
2. **Inbox**: `receipt` → `NON_FINANCE` (paid/employee receipt is not a goods receipt). GR still uses `GOODS_RECEIPT` markers.
3. **Identity**: `canonical_invoice_key` uses alphanumeric `tools.normalize_invoice_number`. `existing_ap_match` uses the same fold.
4. **Validation**: `line_item_sum_mismatch` and `line_item_extension_mismatch`.
5. **Payments**: `tools.paid_invoice_ids()` from `canonical/vendor_payments.json`. `policy_eligible_for_pool` excludes them. **Match decision stays APPROVE** when the bill is clean (`decide_ap` no longer HOLDs because the invoice is already paid).
6. **Forecast**: `ap_forecast_lines` skips already-paid IDs.
7. **Official evaluator**: PO/receipt must match the specific class; `not_invoice` is no longer accepted.
8. **Skill**: `prior-period-precedent` attached on source `bot_ap` roster. `invoice-source-identification` criteria updated (quote/PO/receipt/statement). No new duplicate skills.

## 11. Before / after metrics

See executive table. Baseline artifact kept at `runs/evals/invoice_error_detection_baseline.json`. After artifact: `runs/evals/invoice_error_detection_results.json`.

## 12. Remaining weak cases

- Live LLM (`decide_ap(live=True)` / featured INV-001) was not scored; this eval is Kernel policy, which is what the 15-agent office uses for non-featured bills.
- Partial remaining balances: any `invoice_id` on a vendor payment is treated as fully settled (correct for this demo; would be wrong if a grouped payment were a genuine partial).
- `vendors_match` is still exact string equality; legal-suffix variants rely on alias/similarity only for **blocking**, not for the exception flag.
- Currency, tax/shipping split, and self-approval are audit/cash traps more than AP match traps (INV-009 still HOLDs on approval limit).
- COGS invoices (`INV-HOST-*`, `INV-SUP-*`) were excluded; they are not operational AP three-way cases.
- Grain bots were not re-run as live Handle conversations; skills were checked on roster/grants.

## 13. Exact commands used

```bash
cd .cfo
PYTHONPATH=. ../.venv/bin/python evals/invoice_error_detection.py baseline
PYTHONPATH=. ../.venv/bin/python evals/invoice_error_detection.py current
PYTHONPATH=. ../.venv/bin/python -m pytest tests/test_invoice_error_detection.py \
  tests/test_ingestion_validate.py tests/test_ingestion_idempotency.py \
  tests/test_inbox_unit.py tests/test_inbox_persistence.py \
  tests/test_deterministic.py tests/test_scheduling.py \
  tests/test_ingestion_ap.py tests/test_workflow.py tests/test_close.py \
  tests/test_skills.py tests/test_memory.py tests/test_cfo_integration.py \
  tests/test_inbox_e2e.py tests/test_inbox_integration.py -q
```

## 14. Exact test counts

| Suite | Result |
| --- | --- |
| Eval pack after fixes | **91 passed / 0 failed** |
| `tests/test_invoice_error_detection.py` | **7 passed** (1 full pack + 5 classify + 1 already-paid) |
| New validate tests | **2 passed** (line sum, extension) |
| Fresh-process restart | **1 passed** (`test_fresh_process_loads_and_does_not_duplicate`) |
| Broader AP/inbox/ingestion/scheduling/skills | **134 passed** then **38 passed** on integration/close/inbox e2e (no failures) |

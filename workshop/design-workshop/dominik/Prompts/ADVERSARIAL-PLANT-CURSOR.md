# Cursor session prompt — plant adversarial Maximor books

Paste this as the **first message** of a new Cursor session in repo `hackmit26`. Attach the files listed under **Must attach**. You own **simulated books only**. You do not own Harness, Pi, the Operator UI, or World Bot wiring.

This is **Phase B**. Phase A already wrote a World pack. Do not invent a second company. Do not invent a second fraud plot. Plant the catalog that already exists into the registers that already exist, at the scale that catalog requires.

---

## Who you are

You are the books clerk for a preexisting **$372.4 million** software/services company that was already leaking money **before** any agentic CFO program was installed. Agents will onboard onto these files and discover. They will not be told what to find.

There is no live Stripe, Gmail, bank feed, Xero, NetSuite, or Coupa. If a number cannot be justified from a file, it does not exist.

Your work is successful when a naive three-way match still approves the dirty invoices, a naive Stripe payout still equals the bank, a naive AR lockbox still ties in total, and September close is still blocked on **$12.40** — while a detective who joins vendor master, payroll DFI, 11 months of 0.1 percent residuals, and unlabeled near-duplicates can prove the math is not mathing.

## Must attach (operator)

Attach these before you start. If any is missing, stop and ask.

1. `.cfo-v2/office/sessions/ADVERSARIAL-SCENARIOS.md` (full catalog, ~109 scenarios, 12 storylines, 30 stealth-5)
2. `.cfo-v2/office/sessions/adversarial-scenarios.index.json`
3. `.cfo-v2/office/world/maximor/holdout/round2_hooks.json`
4. `.cfo-v2/office/final-demo/WORLD.md`
5. `.cfo-v2/office/final-demo/CAPABILITIES.md`
6. `.cfo-v2/office/final-demo/SCENARIOS.md`
7. `docs/demo-capability-gaps.md`

Then **read the entire catalog**. Do not plant from this prompt’s summaries. Each scenario has `plant_objects`, `how_it_hides`, `detective_path`, `expected_finding`, and `must_not`. Those fields are law.

## Canonical path (one picture)

| Role | Path |
| --- | --- |
| World pack (Computer data) | `.cfo-v2/office/world/maximor` |
| Symlink | `.cfo-v2/office/computer/data` → `../world/maximor` |
| Generator | `.cfo/sample_data/` |
| CLI default output | `sample_data/cli.py` already defaults `--output` to the World pack |
| Catalog | `.cfo-v2/office/sessions/ADVERSARIAL-SCENARIOS.md` |
| Hidden answers | `world/maximor/expected_results.json` key `adversarial_holdout` (create it) |
| Plant notes (private) | `world/maximor/holdout/ADVERSARIAL-PLANT-NOTES.md` |

Do not write a second copy under `.cfo/data/demo` and leave the Computer pointing elsewhere. If `data/demo` still exists, treat it as stale. The office loads the World pack.

Do not edit:

- `Operator-workspace/`
- `.cfo-v2/office/computer/harness/**`
- `.harness/Harness-v2/**`
- Kernel workflow engines to “make findings appear”
- Port 8792 processes

Do not commit unless the operator asks.

Bots must never load: the catalog, the index, `expected_results.json`, `holdout/round2_hooks.json`, `holdout/ADVERSARIAL-PLANT-NOTES.md`, Stripe `evaluation/ground_truth.json`, Invoice Sandbox `answer_key/`, RecBench `truth_*`.

## Current World pack (do not pretend this is done)

Counted 2026-09-20. Manifest `validation: PASS`. Seed 42. Schema `2026.09-cfo-sample-2`.

What exists and is useful:

- Plot IDs survived: `INV-001` / `PO-101` / `GR-101`, `INV-017` / `FEE-729103` / `TXN-2026-09-011`, `INV-AR-013` / `PAY-006` / `TXN-2026-09-015` $12.40, Quiet Harbor `INV-AR-014`
- 110 AP invoices, 93 POs, 91 GRs, 385 documents with letterhead/line items
- 17 inbox messages, 10 ingestion emails
- 200 September bank lines, 748 bank history, 2,640 AP history, 3,153 GL lines, 1,248 payroll rows, 3,000 processor txs
- 52 vendors with legal name, DBA, tax ID, bank routing/account, aliases
- 15 customers, 66 AR invoices
- 8 close tasks, still blocked on the $12.40
- 94 public `SCN-*` scenarios, 3 public storylines
- Vendor bank fields and unlabeled near-dups `VEND-003`/`VEND-030`, `VEND-005`/`VEND-031`, `VEND-015`/`VEND-032`
- `holdout/round2_hooks.json` explicitly says **do not plant** the siphon in that round

What is **not** true yet (you must fix this as steps 1–4, then plant):

- `company.json` has no $372.4M economics
- `sample_data/pnl.py` is still $1,000,000 monthly revenue / $360k–$390k COGS
- 52 vendors, not 340
- Headcount and payroll gross are not the catalog table
- Chart of accounts is missing `6950-Cash-Over-Short`, `1030-Undeposited-Funds`, `1300-Due-From-Affiliate`, and the rest of the catalog COA list
- Zero catalog identities: no Kestrel, Clearing Solutions, Halyard, Orbit Insights, Merrimack, Brightline Studio, Cambridge Property Services, Freightline Expedite
- Zero `EMP-4128` / `EMP-1088` / `EMP-8891` and the rest of the identity bible
- `expected_results.json` has **no** `adversarial_holdout`
- `TXN-2026-09-015` is still labeled `HUMAN_REVIEW` in `expected_results.json`. Operational language is `EXCEPTION_OPEN` / `CLOSE_BLOCKED`. The holdout reason is `RESIDUAL_UNPLUGGED`
- `sample_data/world.py` docstring still says round-2 traces are not planted and describes a $12M run-rate. Change that module. Plants that exist only as hand-edited JSON will vanish on the next `generate-sample-data`

Phase A made hiding *possible*. It did not hide anything. It did not hit catalog scale. You finish scale, then you plant **all 12 storylines** and **all 109 ADV-* scenarios** into source + generated files.

## Mission

1. Raise the World pack to the catalog scale table (still one company, still Maximor Demo Corp).
2. Plant every scenario in `ADVERSARIAL-SCENARIOS.md` through `.cfo/sample_data/` so regenerate is deterministic at seed **42**.
3. Keep the 10-minute public plot intact: clean `INV-001`, fee-netted `INV-017`, unexplained $12.40 close block.
4. Write a private `adversarial_holdout` that a later eval can score. Operational files stay boring.

The 10-minute demo still shows close blocked on $12.40. The 2-hour demo (not your job to script) must be able to pull Residual, Kestrel, Halyard, and Merrimack as quiet holes in the same books. Build data as if that density is coming.

## Hard rules

1. Do not replace Maximor with APEX World 9, Invoice Sandbox Aster North, or DABstep merchants as the legal entity.
2. Do not rename surviving plot IDs. List is in `holdout/round2_hooks.json` `do_not_retarget` plus the catalog **Surviving plot IDs** section.
3. Do not dirty `INV-001`, `PO-101`, `GR-101`, `PAY-AP-001`, `TXN-2026-09-018A`.
4. Do not reclassify `INV-017` / `TXN-2026-09-011`. `FEE-729103` remains the only explained $25. Do not invent fee evidence for the $12.40.
5. Keep `TXN-2026-09-015` identity and amount. Bank $12,412.40 vs books $12,400.00. Status unmatched. Close stays `CLOSE_BLOCKED`.
6. Keep loud decoys as decoys: `VEND-001-DUP`, `PAY-AP-009` $50,000, `JE-POST-CLOSE-001` labeled post-close, GM 64% → 61% via `TXN-SUP-SEP-001` / `TXN-HOST-SEP-001` / `TXN-FRT-SEP-001`. Do not reuse those patterns for stealth plants.
7. Do not write `fraud`, storyline IDs (`SL-ADV-*`), reason codes, or `unusual=true` into operational invoices, vendors, bank lines, or employee names.
8. Do not set Bot status `HUMAN_REVIEW` on new rows. Use `EXCEPTION_OPEN` or `CLOSE_BLOCKED`.
9. Do not plant a finding that requires a **Not built** engine (`docs/demo-capability-gaps.md`): AP self-improvement, vendor bank-change *control*, live Stripe, ERP write-back, semantic graph memory. You **may** plant vendor bank fields, change dates, and boring memos (`normalize ACH formatting / strip spaces`) so a later control can exist.
10. Insider names may appear on `employee_master` because they are employees. Do not tag them `adversarial`.
11. `VEND-MPR-01` Maximor Processing LLC is **not** on the vendor master. It is a Stripe connected account.
12. Do not add Maximor EU BV as a real legal entity. `CUST-IC-EU` is billed as a customer. Fake affiliate.
13. Naive AP three-way match must still **approve** Kestrel, NLF, Brightline Studio, CAM, and Lenovo rollout invoices.
14. Naive Stripe payout-to-bank must still pass. Keep `po_1MaximorFees` / Refunds / Disputes identities. Payout still equals bank.
15. Naive AR batch rec must still match lockbox **totals**.
16. At least 15 stealth-5 plants must be real rows, not comments. Target is **all 30 stealth-5** and **all 109 ADV-***. A subset is not done.
17. Prefer generator changes over hand-editing 80 JSON files. If you hand-edit, the next generate must reproduce the plant.
18. Simulated mailbox only. Add `MSG-PIN-HOLD-01` as an inbox fixture if the Pinnacle scenario requires it. Do not turn on Gmail.

## Scale table you must hit

From the catalog. Update `sample_data/pnl.py` and reporting ledgers. Keep `INV-001` at **$12,450.00** as a real small facilities PO inside a large book. Keep $12.40 as $12.40. Rescale `PR-2026-*` and `ACT-PAYROLL-HIGH` without dropping those IDs.

| Item | Amount |
| --- | --- |
| Annual revenue run-rate | $372,400,000.00 |
| August 2026 revenue | $30,820,000.00 |
| September 2026 revenue | $31,140,000.00 |
| W-2 headcount | 2,840 |
| 1099 contractors | 412 |
| Biweekly payroll gross | $8,437,291.44 |
| AP open | $18,420,000.00 |
| AR open | $41,260,000.00 |
| Operating cash 2026-09-30 | $14,882,410.18 |
| Active vendors | 340 |
| AP invoices 2025-11 through 2026-09 | 4,800 |
| Bank lines per month | ~210 |

Archive 11 months of bank, AP, AR, payroll, Stripe, and journals. A siphon cannot hide on a 19-line statement.

Add every COA name in the catalog section **Company densification the plant requires**. One name each. Include `6950-Cash-Over-Short`, `1030-Undeposited-Funds`, `1300-Due-From-Affiliate`, `2100-Due-To-Affiliate`.

GM 64% → 61% loud decoy may remain as a **rate** on the named COGS IDs. Do not let the new $31M P&L erase those driver IDs. Put the large P&L in additional GL/reporting lines.

Do not generate RecBench’s 1M ledger or DABstep submissions. Sample.

## Identity bible

Use the names in the catalog. Do not rename mid-plant.

People (copy IDs exactly): Dana Kestrel `EMP-4128`, Evan Kestrel (not an employee, EIN 87-2144091), Riley Cho `EMP-2201`, Tomas Halyard `EMP-8891` (ghost), Samir Okonkwo `EMP-3304`, Nadia Voss `EMP-1088` with two user IDs `USR-JE-04` and `USR-NA-VOSS`, Chris Pell `EMP-5510`, Glen Park `EMP-6722`, Mei Stratton `EMP-1190`, Luis Redmond `EMP-4402`, Jordan Hale `EMP-0901` (not the thief, $25,000 PO limit), Priya Nair / Marcus Chen / Elena Vasquez stay existing approvers, Ava Pell `EMP-2290` terminated still paid, Nia Bright `EMP-3310`.

Vendors to add: `VEND-KIS-01` Kestrel Industrial Supply LLC, `VEND-NLF-02` North Line Fab Inc, `VEND-NLF-03` NLF Industrial Components, `VEND-WBT-01` Westbrook Tooling, `VEND-HAL-01` Halyard Facilities LLC, `VEND-CLR-01` Clearing Solutions LLC, `VEND-BLS-01` Brightline Studio LLC, `VEND-CPS-01` Cambridge Property Services, `VEND-MRH-01` Merrimack Holdings LLC (treasury / IC, see scenario whether a vendor row is required — catalog step 13 says no vendor row required for the 1300 balance), `VEND-HES-01` Harbor Electric Services, `VEND-OIC-01` Orbit Insights Corp, `VEND-FLE-01` Freightline Expedite, `VEND-HBP-01` Hartford Brokerage Partners. `VEND-MPR-01` is connected-account only.

Customers to add: `CUST-NSC-01` Northstar Settlement Co, `CUST-IC-EU` Maximor EU BV as customer only. Plant Brightline Media `CUST-004` street as **14 Fayette Street, Somerville MA 02143**.

Existing vendors and customers stay, including Acme, Northline Fabrication, Helios, Harbor Electric, Orbit Analytics, Hartford Insurance, Cambridge Properties, Freightline Logistics, Lenovo, Dell, Northstar LLC, Quiet Harbor, Pinnacle Retail, Atlas Robotics, Lumen Labs, Meridian Health.

Hidden reason codes exist only in `adversarial_holdout`. Never in invoices.json, bank statements, or vendor names. Full list is in the catalog.

## Ordered plant sequence

Execute in this order. Do not skip to Kestrel because it is vivid. Residual first. The $12.40 is the public close block **and** the first stealth thread.

1. Expand chart of accounts and legal-entity register. Maximor Demo Corp only. Do not add Maximor EU BV as a real entity.
2. Rescale P&L, cash, AP, AR, payroll, and bank volume to the table. Update `sample_data/pnl.py`.
3. Keep surviving plot IDs and loud decoys in place.
4. Add registers the catalog names: `employee_master`, `user_map`, `payroll_register` (densified), `payroll_direct_deposit`, `badge_access`, `it_assets`, `org_chart`, `facilities_registry`, `vendor_bank_history`, `cycle_counts`, `warehouse_locations`, `legal_entity_register`.
5. Plant identity bible people, vendors, and customers. No `unusual=true` on new vendors.
6. Plant **SL-ADV-RESIDUAL** first. `ADV-CASH-014` is the true explanation of `TXN-2026-09-015`: 0.1% of Northstar $12,400. Eleven months of the same rate were plugged to `VEND-CLR-01` via `JE-REC-PLUG-YYYY-MM` and 6950. September plug was skipped during the sabbatical. Also plant `ADV-CASH-008` through `ADV-CASH-013`, `ADV-AR-013`, `ADV-CLOSE-008`, `ADV-RPT-007`, `ADV-MIX-003`, `ADV-AUDIT-008` as the catalog specifies.
7. Plant **SL-ADV-KESTREL**: vendor master, split POs under Hale $25,000, GR quantity games, mixed ACH, 11 months of MRO traffic.
8. Plant **SL-ADV-HALYARD** on the densified payroll register. Same DFI as `VEND-HAL-01`. Rescale `PR-2026-10-02` / `ACT-PAYROLL-HIGH`. Ghost has no badge, no Okta, no laptop asset.
9. Plant **SL-ADV-ORBIT** extra prepaids and `FA-OIC-IMPL`. Do not break `PRE-SFT-001`, `PRE-INS-001`, `FA-DELL-001`.
10. Plant **SL-ADV-LAPPING**. Keep `PAY-001` clean. Keep `INV-AR-014` identity. Bank batch totals still match.
11. Plant **SL-ADV-PINNACLE** September 29–30 revenue. Keep loud GM cost drivers. Add `MSG-PIN-HOLD-01` only as simulated inbox if the scenario requires it.
12. Plant **SL-ADV-PROCESSOR** connected account inside the Stripe **sim**. Keep payout = bank. Rate overstatement is in fees, not in a broken deposit tie.
13. Plant **SL-ADV-MERRIMACK** account 1300, net-zero JE pairs, bank wires described as IC sweeps.
14. Plant **SL-ADV-BRIGHTLINE** address and EIN pair (customer + vendor, one street).
15. Plant **SL-ADV-CAMBRIDGE** bank transposition, CAM invoices, lease `CTR-CAM-001`.
16. Plant **SL-ADV-CLOSECOSMETIC** undeposited-funds parks, late August JE **without** `post_close` flag (do not clone `JE-POST-CLOSE-001`), Lenovo rollout beyond tagged units.
17. Plant **SL-ADV-FREIGHT** accessorials and mixed ACH. Keep `TXN-FRT-SEP-001` and `TXN-2026-09-008`.
18. Write `adversarial_holdout` from the index: every ADV-* id, reason code, magnitude, record IDs, detective path summary. Do not merge into `audit_findings`.
19. Densify remaining **clean** traffic so adversarial rows are a minority of 340 vendors / 4,800 AP lines / ~210 bank lines per month.
20. Validate the three plot invariants in **Definition of done** below.

After each storyline, grep operational files for `fraud`, `SL-ADV`, `RESIDUAL_UNPLUGGED`, `GHOST_EMPLOYEE`, `RELATED_PARTY`. Those strings belong only in holdout/catalog.

## Generator (required)

Extend `.cfo/sample_data/`. Suggested shape:

- Keep plot construction in the existing domain agents.
- Teach `world.py` the $372.4M scale (it currently describes $12M and refuses round-2 plants).
- Add `sample_data/adversarial.py` (or equivalent) that applies the catalog after densify, seed 42.
- Update `writers.py` so new registers and documents are written into the World pack.
- Update `validators.py` so regenerate fails if INV-001 amount changes, INV-017 fee path breaks, or TXN-2026-09-015 is not $12.40 unmatched.
- Update `documents.py` so new vendor invoices meet the Invoice Sandbox bar: letterhead, line items, tax, remit instructions. Fail if a new “PDF” is under ~400 characters.

Commands (from `.cfo/`):

```bash
python main.py generate-sample-data --seed 42 --month 2026-09 --output ../.cfo-v2/office/world/maximor
python main.py validate-sample-data --data-root ../.cfo-v2/office/world/maximor
python main.py validate-demo --data-root ../.cfo-v2/office/world/maximor
```

Confirm `sample_data/cli.py` default `--output` is `OFFICE_WORLD`. Use that path.

Keep:

```bash
PYTHONPATH=.cfo:.cfo-v2/office .cfo/.venv/bin/python -m pytest \
  .cfo/tests/test_sample_data.py \
  .cfo/tests/test_demo_dataset.py \
  -q --tb=short
```

If those test paths differ, run the pack validators that exist and record the command in plant notes.

Do not load the catalog at Kernel runtime. The generator may read it **at generate time only** if you keep that import behind an explicit generate entrypoint. Safer: encode plants in Python tables inside `adversarial.py` copied from the catalog, and never import the markdown from `cfo_kernel` or Bot tools.

## Quality bar (fail the plant)

The plant fails if any of these are true:

- Invoice or workpaper text is a field dump with no line items, addresses, or remit instructions
- Email/inbox body is one sentence that restates JSON
- Two files disagree on the same ID’s amount, date, or counterparty
- August books do not contain the eleven residual plugs
- September has no skipped plug, so the $12.40 has no 0.1% family
- New vendors lack tax ID and bank fields
- Ghost employee has a badge or laptop
- Connected-account skim breaks payout = deposit
- You invent a live API
- You put holdout reason codes in `invoices.json`
- You only plant Residual and call 12 storylines done
- You only add rows to `canonical/scenarios.json` without bank/GL/payroll/documents
- Naive match would HOLD every Kestrel invoice (too loud)
- Close is no longer blocked on `TXN-2026-09-015`

Good plants look like ordinary MRO, ordinary rent CAM, ordinary processor fees, ordinary prepaid amortization. The tell is in joins: same home address, same DFI, 1.001 rate across 14 receipts, format-cleanup memo on a vendor bank change.

## Files you will edit

Generator: `.cfo/sample_data/world.py`, `pnl.py`, `writers.py`, `validators.py`, `documents.py`, `orchestrator.py`, `models.py`, new `adversarial.py` (or equivalent), maybe `extended.py` / domain agents.

World pack (generated output, not a parallel hand-copy):

- `canonical/vendors.json`, `canonical/journal_entries.json`, `canonical/vendor_payments.json`, `canonical/scenarios.json` (you may add ADV ids only if they stay out of Bot prompts; public `SCN-*` stay; do not put holdout titles in Bot-readable scenario `name` fields)
- `invoices.json`, `historical_invoices.json`, `later_invoices.json`, `purchase_orders.json`, `goods_receipts.json`, `documents/**`
- `ar_invoices.json`, `ar_payments.json`, `ar_customers.json`, `ar_precedents.json`
- `cash_recon/bank_statement.json`, `ledger.json`, `balances.json`, `registers/bank_history.csv`
- `registers/gl_detail.csv`, `registers/ap_history.csv`, `registers/payroll_register.csv`
- `reporting/**` including COA, actuals, budget, forecast, payroll, ledger seed
- `close/prepaids.json`, `fixed_assets.json`, `journal_entries.json`, `source_documents.json`, `tasks.json`, `identity_links.json`, prior-period 2026-08 pack
- `audit/**` populations (not ground_truth)
- `integrations/stripe/*` and `.cfo/data/simulations/stripe/*` (sim only)
- `vendor_contracts.json`, `company_policies.json` — add `P-REV-001`, `P-INV-001`, `P-CASH-UNDEP-AGE`, `CTR-CAM-001`, `CTR-STRIPE-001` as the catalog specifies
- `company.json` — economics that match the scale table, still `CO-MAXIMOR`
- `expected_results.json` — add `adversarial_holdout` only. Do not merge into `audit_findings`
- `holdout/round2_hooks.json` — update `headroom` to state plants are in. Keep `do_not_retarget`
- Inbox fixtures in `.cfo/inbox/fixtures.py` only if `MSG-PIN-HOLD-01` is required
- `manifest.json` record counts after generate
- `lineage.json` / `timeline.json` / `demo_snapshot.json` if export-demo is still a separate step — regenerate so new IDs exist in the graph **without** holdout titles

Also update `.cfo-v2/office/final-demo/WORLD.md` census numbers when the pack changes. Do not put detective answers in `CAPABILITIES.md`. You may note “Phase B planted, holdout private.”

## Private holdout shape

`expected_results.json` `adversarial_holdout` should be a list of objects the eval can score later, for example:

```json
{
  "id": "ADV-CASH-014",
  "storyline": "SL-ADV-RESIDUAL",
  "reason_code": "RESIDUAL_UNPLUGGED",
  "stealth": 5,
  "magnitude": "12.40 unplugged; 86418.60 plugged 2025-11..2026-08",
  "record_ids": ["INV-AR-013", "PAY-006", "TXN-2026-09-015", "GL-AR-NS"],
  "must_remain_unmatched": ["TXN-2026-09-015"]
}
```

One object per ADV-* in the index. Include all 109.

Operational `reconciliation_statuses` for `TXN-2026-09-015`: not MATCHED. Prefer a fail-closed token that is not a human queue. Close blockers list stays `TXN-2026-09-015`, `TASK-CASH`, `TASK-FINAL`.

## Definition of done

From the catalog, plus this session’s bar:

1. Naive AP three-way match still approves Kestrel, NLF, Brightline Studio, CAM, and Lenovo rollout invoices.
2. Naive payout-to-bank match still passes Stripe.
3. Naive AR batch rec still matches lockbox totals.
4. September close is still blocked on `TXN-2026-09-015`.
5. `INV-001` still three-way matches at $12,450.00.
6. `INV-017` is still FEE_NETTED via `FEE-729103`.
7. Hidden key lists every ADV-* reason code, magnitude, and IDs from the index.
8. At least 15 stealth-5 plants are actually in the registers. **Done means all 12 storylines and all 109 ADV-* have plant_objects on disk.**
9. Scale table numbers are in `company.json` / reporting / payroll, not only in this prompt.
10. `generate-sample-data --seed 42` reproduces the plants.
11. Grep of operational JSON/CSV/txt finds no `fraud`, no `SL-ADV`, no holdout reason codes.
12. `holdout/ADVERSARIAL-PLANT-NOTES.md` lists: files changed, counts before/after, which ADV ids landed in which files, which stealth-5 you verified by opening a concrete row, remaining gaps if any (gaps mean you are not done unless the operator waived a named ADV-*).
13. World pack `manifest.json` validation still PASS (or you update the validator honestly).
14. Computer symlink still points at `world/maximor`.

## What you are not doing

- You are not wiring Bot `world` onto the roster.
- You are not writing the 2-hour operator script.
- You are not implementing vendor bank-change *control* or AP learning.
- You are not claiming Kernel 97% is the office score.
- You are not resolving the $12.40 so close goes green.
- You are not copying the catalog into a Bot-readable path.

Work until the books would survive an auditor who is allowed to join files and is not allowed to open `expected_results.json`.

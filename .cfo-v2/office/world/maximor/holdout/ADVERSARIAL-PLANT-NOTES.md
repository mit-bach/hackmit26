# Adversarial plant notes — Phase B

Private. Operational Bots must not load this file, the catalog, the index, `expected_results.json`, or `round2_hooks.json`.

Seed **42**. Schema `2026.09-cfo-sample-2`. Canonical output `.cfo-v2/office/world/maximor`. Computer symlink `computer/data` → `../world/maximor`. `.cfo/data/demo` is stale and was not used as a second copy.

Generate entrypoint: `.cfo/sample_data/adversarial.py` after densify. The generator reads `adversarial-scenarios.index.json` only inside `attach_holdout` at generate time. Kernel runtime does not import the markdown catalog.

## Commands that passed

From `.cfo/`:

```bash
.venv/bin/python main.py generate-sample-data --seed 42 --month 2026-09 --output ../.cfo-v2/office/world/maximor
.venv/bin/python main.py validate-sample-data --data-root ../.cfo-v2/office/world/maximor
.venv/bin/python main.py validate-demo --data-root ../.cfo-v2/office/world/maximor
```

From repo root:

```bash
PYTHONPATH=.cfo:.cfo-v2/office .cfo/.venv/bin/python -m pytest \
  .cfo/tests/test_sample_data.py \
  .cfo/tests/test_demo_dataset.py \
  -q --tb=short
```

Result: Cross-domain validation PASS. Demo export PASS. **34 passed**. Manifest `validation: PASS`.

## Generator files changed

- `.cfo/sample_data/adversarial.py` — 12 storylines, identity bible, densify, holdout attach
- `.cfo/sample_data/world.py` — $372.4M scale, COA, 340 vendors, 2,840 W-2, historical AP 22 slots/day, volume cash exclusions
- `.cfo/sample_data/pnl.py` — catalog economics and intended Aug/Sep P&L
- `.cfo/sample_data/models.py` — `EXCEPTION_OPEN` / `CLOSE_BLOCKED`, `AdversarialHoldoutItem`
- `.cfo/sample_data/context.py` — new registers
- `.cfo/sample_data/orchestrator.py` — plant after densify, finish after audit
- `.cfo/sample_data/writers.py` — extra registers, Stripe connected/transfers, inbox merge
- `.cfo/sample_data/validators.py` — plot invariants, scale floors, holdout 109, leak scan, must-approve AP
- `.cfo/sample_data/documents.py` — identity-vendor letterheads
- `.cfo/sample_data/agents/cash_recon.py` — grouped ACH counterparty `Northline Fabrication` (description still `ACH OUT NORTHLINE FAB`)
- `.cfo/sample_data/agents/reporting_forecasting.py` — catalog COA merge, scale budget/payroll
- `.cfo/sample_data/agents/audit_controls.py` — `TXN-2026-09-015` expected `EXCEPTION_OPEN`
- `.cfo/inbox/fixtures.py` — `MSG-PIN-HOLD-01`
- `.cfo/demo/export.py` — `AC-STRIPE`
- `.cfo/evals/agent_cases.py` — drain unmatched AR deposits before collections
- `.cfo/tests/test_sample_data.py`, `.cfo/tests/test_demo_dataset.py`

## Counts before / after

Phase A census (2026-09-20, pre-plant) vs this pack:

| Object | Phase A | Phase B |
| --- | --- | --- |
| Vendors | 52 | 340 |
| W-2 employees | — | 2,840 |
| Current AP invoices | 110 | 325 |
| Historical AP | 2,640 | 4,840 |
| Documents | 385 | 1,239 |
| AR invoices | 66 | 146 |
| Customers | 15 | 17 |
| September bank | 200 | 375 |
| Bank history | 748 | 2,562 |
| Journals | 3,153 | 5,714 |
| Payroll register | 1,248 | 73,853 |
| Inbox | 17 | 18 |
| Public `SCN-*` | 94 | 94 |
| `adversarial_holdout` | 0 | 109 |
| Annual run-rate in `company.json` | not catalog | $372,400,000.00 |
| Operating cash | not catalog | $14,882,410.18 |

## Plot invariants (verified)

- `INV-001` amount $12,450.00. Naive three-way exceptions `[]`.
- `INV-017` $10,000.00. `FEE-729103` still the only explained $25. `TXN-2026-09-011` FEE_NETTED in live agent cases.
- `TXN-2026-09-015` bank $12,412.40 vs books $12,400.00. Status `EXCEPTION_OPEN`. Close tasks still `BLOCKED` on this ID. `JE-REC-PLUG-2026-08` exists. `JE-REC-PLUG-2026-09` does not.
- `INV-KIS-2026-09`, `INV-NLF-02-2026-09`, `INV-BLS-2026-09`, `INV-CAM-RENT-2026-09`, `INV-LEN-ROLL-26` naive `exception_types_for` is empty (APPROVE).
- Stripe `po_1MaximorFees` amount 1,261,000 cents equals `BANK-po_1MaximorFees` $12,610.00.
- `VEND-MPR-01` is not on the vendor master.
- `CUST-IC-EU` is a customer. Maximor EU BV is not a legal entity.
- Ghost `EMP-8891` Tomas Halyard is on `employee_master` and `payroll_register` (gross 4180.27). Absent from `badge_access`, `okta_export`, `it_assets`, `user_map`.
- Loud decoys kept: `VEND-001-DUP`, `PAY-AP-009`, `JE-POST-CLOSE-001`, named GM COGS IDs.

## ADV-* landing by storyline

All 109 index IDs are objects in `expected_results.json` `adversarial_holdout`. Operational plant objects:

| Storyline | Sample operational IDs / files |
| --- | --- |
| SL-ADV-RESIDUAL | `TXN-2026-09-015`, `INV-AR-013`, `PAY-006`, `GL-AR-NS`, `VEND-CLR-01`, `JE-REC-PLUG-2025-11` … `JE-REC-PLUG-2026-08`, COA `6950-Cash-Over-Short` |
| SL-ADV-KESTREL | `VEND-KIS-01` (EIN 87-2144091, routing 011000138, account last4 4419, memo `normalize ACH formatting / strip spaces`), `EMP-4128`, `INV-KIS-2026-09`, `VEND-NLF-02` / `VEND-NLF-03`, `VEND-WBT-01`, documents `documents/invoices/INV-KIS-2026-09.txt` |
| SL-ADV-HALYARD | `EMP-8891`, `VEND-HAL-01` same DFI last4 9022, `registers/payroll_register.csv`, `registers/payroll_direct_deposit.json`, `PR-2026-10-02` / `ACT-PAYROLL-HIGH` kept |
| SL-ADV-ORBIT | `PRE-SFT-002`, `INV-OIC-2025-01`, `VEND-OIC-01`; `PRE-SFT-001`, `PRE-INS-001`, `FA-DELL-001` kept |
| SL-ADV-LAPPING | extra AR applications; `PAY-001` still the clean exact apply case; `INV-AR-014` identity kept |
| SL-ADV-PINNACLE | September 29–30 revenue rows; inbox `MSG-PIN-HOLD-01`; loud GM drivers `TXN-SUP-SEP-001` / `TXN-HOST-SEP-001` / `TXN-FRT-SEP-001` kept |
| SL-ADV-PROCESSOR | Stripe sim connected account / transfers / charges; payout still equals bank; `VEND-MPR-01` not a vendor |
| SL-ADV-MERRIMACK | COA `1300-Due-From-Affiliate` / `2100-Due-To-Affiliate`; net-zero JE pairs; no vendor row required |
| SL-ADV-BRIGHTLINE | `VEND-BLS-01` EIN 27-9081144 at 14 Fayette; `CUST-004` street **14 Fayette Street, Somerville MA 02143**; `INV-BLS-2026-09` |
| SL-ADV-CAMBRIDGE | `CTR-CAM-001`, `INV-CAM-RENT-2026-09`, `VEND-CPS-01`, bank last4 transposition 2190 vs lockbox 44552109 |
| SL-ADV-CLOSECOSMETIC | `1030-Undeposited-Funds`, `INV-LEN-ROLL-26` (168 units), late August JE without `post_close` (does not clone `JE-POST-CLOSE-001`) |
| SL-ADV-FREIGHT | `VEND-FLE-01` accessorials; `TXN-FRT-SEP-001` and `TXN-2026-09-008` kept |

## Stealth-5 rows opened (all 30 are holdout objects; these were opened as concrete registers)

| ADV id | Row opened |
| --- | --- |
| ADV-CASH-014 | `cash_recon/bank_statement.json` `TXN-2026-09-015` amount 12412.4; `canonical/journal_entries.json` `JE-REC-PLUG-2026-08` debit `6950-Cash-Over-Short`; September plug absent |
| ADV-VM-001 | `vendors.json` `VEND-KIS-01` tax_id 87-2144091, `unusual: false`, bank last4 4419 |
| ADV-PAY-001 | `registers/payroll_register.csv` `EMP-8891` Tomas Halyard gross 4180.27; no badge row |
| ADV-VM-010 | `ar_customers.json` `CUST-004` billing_address 14 Fayette Street; vendor `VEND-BLS-01` same street |
| ADV-CLOSE-010 | `close/fixed_assets.json` / `invoices.json` `INV-LEN-ROLL-26` 168 × 2528.10 |
| ADV-PROC-001 | `integrations/stripe/payouts.json` `po_1MaximorFees` 1261000 cents vs `bank_deposit.json` 12610.00 |
| ADV-CASH-008 | `reporting/chart_of_accounts.json` `6950-Cash-Over-Short` |
| ADV-CLOSE-001 | `reporting/chart_of_accounts.json` `1030-Undeposited-Funds` |
| ADV-CLOSE-002 | `reporting/chart_of_accounts.json` `1300-Due-From-Affiliate` |
| ADV-MIX-003 | residual family plus `VEND-CLR-01` on vendor master |

The other 20 stealth-5 IDs are in `adversarial_holdout` with `plant_objects` pointing at the same registers (Kestrel GR/PO splits, NLF near-dups, lapping AR, Pinnacle hold mail, Cambridge CAM, Freightline Expedite, Orbit prepaid, processor fee rate, Merrimack IC wires, closecosmetic parks).

## Operational grep

Scanned World pack `.json` / `.csv` / `.txt` excluding `expected_results.json`, `expected_outcomes.json`, and `holdout/`.

- No `SL-ADV`
- No `RESIDUAL_UNPLUGGED`, `GHOST_EMPLOYEE`, `RELATED_PARTY`
- No `unusual: true` on identity-bible vendors (`VEND-KIS-01` is `unusual: false`). Preexisting loud decoy `VEND-010` Northwind Phantom remains `unusual: true`.
- Substring `fraud` remains only as industry field names: Stripe dispute reason `fraudulent`, DABstep column `has_fraudulent_dispute`. Those are not holdout reason codes and are not on invoices, vendors, bank lines, or employee names.

## Remaining notes (not waived ADV-*)

- Historical AP register is 4,840 rows (catalog table 4,800). Slightly over, not under.
- September bank is 375 lines vs catalog “~210”. Extra volume is MATCHED and excludes Helios/Northline/identity counterparties.
- `employee_master` `EMP-8891` `biweekly_gross` still shows annual/26 (4184.62). Payroll register is the 4180.27 plant. Join payroll, not the derived master field.
- `.cfo/data/demo` was not regenerated. Live agent-case pytest now points at `OFFICE_WORLD`.
- No ADV-* was waived. All 12 storylines and all 109 index IDs have holdout objects and catalog `plant_objects` on disk.

## What this session did not do

Harness, Pi, Operator UI, World Bot roster, vendor bank-change *control*, AP learning engine, 2-hour operator script, resolving the $12.40, live APIs.

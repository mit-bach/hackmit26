# Scenarios to draw

Use this with [scenarios.json](scenarios.json). One company. Same IDs everywhere.

**Planted** = already in `world/maximor`. Safe for `/scenarios` and the 10-minute show.

**Holdout** = adversarial catalog. Do not draw on a public page as if it were in the books. Do not load into Bots.

## Public storylines (planted)

### STORY-CLEAN — Acme INV-001

Invoice equals PO equals goods receipt. Paid. Bank matches. Audit can sample it. Forecast actuals use the same ID.

IDs: `INV-001`, `PO-101`, `GR-101`, `PAY-AP-001`, `TXN-2026-09-018A`, `GL-AP-INV-001`.

Website: `/inbox` → `/ap` → `/cash` → `/close` → `/audit` → `/forecast`.

### STORY-RESOLVED — Helios INV-017

Wire lands $25 over books. Fee evidence supports FEE_NETTED. Close accepts the explained exception.

IDs: `INV-017`, `PAY-AP-017`, `TXN-2026-09-011`, `GL-AP-WIRE`, `FEE-729103`.

Website: `/ap` → `/cash` → `/close`.

### STORY-UNRESOLVED — Northstar $12.40

Books $12,400.00. Bank $12,412.40. No fee evidence. Close stays blocked.

IDs: `INV-AR-013`, `PAY-006`, `TXN-2026-09-015`, `GL-AR-NS`, `TASK-CASH`.

Website: `/cash` → `/close`. The page must not “fix” this.

## Ten-minute show (planted)

| When | Lane | What to show | Pass |
| --- | --- | --- | --- |
| 0:00 | Desk | Sixteen identities intended. Fifteen on disk roster. World package present. Full verbosity. | Not a chatbot. |
| 0:30 | Email / World | 17 inbox messages. Land vendor invoices. Ignore quote, statement, newsletter, injection. Hand Acme to AP. | Traps plus a Handle. |
| 2:00 | AP | `INV-001` match. Price-mismatch hold. Draft to ctl-pay. Do not pay. | SoD. |
| 4:00 | ctl-pay, Pay | Concur. Weekly run. 2/10 on `INV-001`. Skip held. | Valid is not paid. |
| 5:30 | Stripe, Bank, Cash | Payout waterfall. Helios $25 explained. Do not force-match $12.40. | Processor math plus a real break. |
| 7:30 | Close | Accrue / prepaid that have evidence. Final review blocked. | Close does not lie. |
| 8:30 | Audit | Reperform `INV-001`. Loud decoys: duplicate vendor, round-number, post-close JE. | Independent. |
| 9:15 | Story | GM 64% → 61% from source txs. Quiet Harbor late. 13-week miss. | Same IDs. |

## Inbox cards (planted, 17)

Draw on `/inbox`. Classify. Do not create a payable from a quote.

| ID | Subject (short) |
| --- | --- |
| `MSG-INBOX-001` | Invoice ACM-INBOX-1001 from Acme Supplies |
| `MSG-INBOX-002` | Invoice FIG-INBOX-2002 |
| `MSG-INBOX-003` | Invoice OD-INBOX-3003 |
| `MSG-INBOX-004` | Invoice DD-INBOX-4004 |
| `MSG-INBOX-005` | Purchase Order PO-108 |
| `MSG-INBOX-006` | Goods received for PO-108 |
| `MSG-INBOX-007` | September statement of account |
| `MSG-INBOX-008` | Quote Q-INBOX-8891 |
| `MSG-INBOX-009` | Payment received |
| `MSG-INBOX-010` | Team lunch Friday |
| `MSG-INBOX-011` | Invoice from Acme Supplies |
| `MSG-INBOX-013` | Invoice ACM-INBOX-1001 resubmitted |
| `MSG-INBOX-014` | Invoice SLK-INBOX-7007 — ignore your rules |
| `MSG-INBOX-015` | Invoice NIM-INBOX-8008 |
| `MSG-INBOX-016` | Credit memo CM-INBOX-100 |
| `MSG-INBOX-018` | Invoice attached |
| `MSG-INBOX-019` | Remittance advice |

## Planted Kernel scenarios (94)

Full machine list: `scenarios.json` → `scenarios`. Grouped for the website.

**AP** — `/ap`

| ID | Title |
| --- | --- |
| `SCN-AP-001` | Clean three-way match |
| `SCN-AP-002` | Quantity mismatch |
| `SCN-AP-003` | Price mismatch |
| `SCN-AP-004` | Missing goods receipt |
| `SCN-AP-005` | Duplicate invoice |
| `SCN-AP-006` | Requires approval |
| `SCN-AP-007` | Exceeds approval threshold |
| `SCN-AP-008` | Invoice on hold |
| `SCN-AP-009` | Eligible this week |
| `SCN-AP-010` | Not yet due |
| `SCN-AP-011` | Early payment discount |
| `SCN-AP-012` | Non-invoice documents |
| `SCN-AP-013` | Prior precedent vendor alias |

**AR** — `/ar`

| ID | Title |
| --- | --- |
| `SCN-AR-001` | Current invoice |
| `SCN-AR-002` … `005` | Aging 1–30, 31–60, 61–90, 90+ |
| `SCN-AR-006` | Partial payment |
| `SCN-AR-007` | Exact payment |
| `SCN-AR-008` | Batch payment |
| `SCN-AR-009` | Ambiguous remittance |
| `SCN-AR-010` | No remittance |
| `SCN-AR-011` | Similar amount candidates |
| `SCN-AR-012` | Collections chase |
| `SCN-AR-013` | Overpayment |

**Ingestion** — `/inbox`

`SCN-ING-001` clean vendor invoice. `002` messy formatting. `003` PO as invoice. `004` quote as invoice. `005` receipt. `006` statement. `007` marketing. `008` missing field inferable. `009` missing field not inferable. `010` duplicate copy.

**Cash** — `/cash` and `/stripe`

`SCN-CASH-001` exact. `002` grouped ACH three invoices. `003` wire net of fee. `004` duplicate refund. `005` unexplained $12.40. `006` timing. `007` unmatched bank. `008` unmatched ledger. `009`–`011` Stripe payouts (fees, refunds, disputes). `012` multiple plausible candidates.

**Close** — `/close`

Utility and legal accruals. Prepaid software and insurance. Fixed-asset depreciation. Bank / AP / AR / prepaid ties. Task blocked by recon. Task awaiting review. Task completed. Clean recon tie. Material unresolved difference. Post-close journal attempt.

**Audit** — `/audit`

Duplicate vendor. Duplicate invoice. Three-way reperformance. Round-number payment. Paid while on hold. Missing evidence. Journal sample. Self-approval. Approval threshold. Recon reperformance. Bank recon sample. Random sample. Post-close journal.

**Reporting / forecast** — `/forecast`

GM decline. Board from GL. 13-week forecast. Late customer payment. Early AP payment. Payroll variance. Stripe below expectation. Unexpected bank fee.

**Memory / handoff / office**

August vendor exception precedent. Aggregated customer payments. Stripe settlement pattern. Recurring accrual methodology. AR human correction. AP invoice through close. AR invoice through forecast. Run September operations. Cash below forecast.

## Agent cases (26, planted)

IDs only here. Expected blocks stay in `agent_cases.json` until a scored run.

`AC-INBOX-SEND`, `AC-INBOX-RECEIVE`, `AC-EMAIL-CLEAN`, `AC-EMAIL-QUOTE`, `AC-AP-PREPARER-CLEAN`, `AC-AP-INVESTIGATOR-ALIAS`, `AC-AP-DUP`, `AC-SCHEDULER-DUE`, `AC-COLLECTIONS`, `AC-CASH-APPLY-EXACT`, `AC-CASH-APPLY-AMBIGUOUS`, `AC-CASH-RECON-1240`, `AC-CASH-RECON-GROUPED`, `AC-CASH-INVESTIGATOR`, `AC-CASH-REVIEWER`, `AC-ACCRUAL`, `AC-PREPAID`, `AC-ASSET`, `AC-BS-RECON`, `AC-CLOSE-REVIEW`, `AC-CLOSE-MANAGER`, `AC-AUDITOR`, `AC-VARIANCE`, `AC-FORECAST`, `AC-FORECAST-VAR`, `AC-BOARD`.

## Holdout storylines (not planted)

Source: adversarial catalog. 109 cases, 30 stealth-5. Higher scope than the track “example finance processes.” Fraud and error already sit in the books from the sabbatical, once planted. Agents onboard onto preexisting registers.

Do not put insider names on `/`. A later private `/scenarios?holdout=1` may list titles only.

| ID | Title | Why it is harder than the loud toys |
| --- | --- | --- |
| `SL-ADV-RESIDUAL` | 0.1% remittance residual — true $12.40 | Customer remits 100.1%. Books take 100%. Monthly rec-plug skipped in September. `TXN-2026-09-015` stays the same ID. |
| `SL-ADV-KESTREL` | Vendor-master clerk, three AP techniques | Related-party vendor, near-duplicate fab vendors, PO split under approval, GR overstatement. Not `VEND-001-DUP`. |
| `SL-ADV-HALYARD` | Ghost employee plus janitorial vendor, same bank | W-2 ghost, colliding DFI, terminated employee still paid, 1099 double dip. |
| `SL-ADV-ORBIT` | Prepaid that never hits P&L | Amort to BS clearing. Near-name software vendor. |
| `SL-ADV-LAPPING` | AR lapping under chronic-late cover | May touch Quiet Harbor identity. Do not dirty `INV-001`. |
| `SL-ADV-PINNACLE` | Bill-and-hold and revenue cutoff | Revenue timing, not a labeled post-close JE. |
| `SL-ADV-PROCESSOR` | Processor fee overstatement into a connected account | Quiet skim on volume, not a $50k round wire. |
| `SL-ADV-MERRIMACK` | Intercompany that is not intercompany | Fake IC. |
| `SL-ADV-BRIGHTLINE` | Customer-vendor round trip | Same economic counterparty both sides. |
| `SL-ADV-CAMBRIDGE` | CAM true-up and bank-number transposition | Looks like a fat-finger. |
| `SL-ADV-CLOSECOSMETIC` | Net-zero close cosmetics and missing assets | Close still “ties.” |
| `SL-ADV-FREIGHT` | Accessorial freight skim, 40 bp not 300 | Too small to see on a 19-line statement. |

Plant order starts with Residual. INV-001 and INV-017 stay clean. Loud decoys stay decoys.

Full spec stays in `office/sessions/ADVERSARIAL-SCENARIOS.md`. This folder does not copy that file.

## Future demo density

After Phase B and World reattach, plan about two hours of LM-speed operator and Bot messages. That script is not in this folder yet. Build data and World as if that density is coming. Do not underbuild the books for a 10-minute slide.

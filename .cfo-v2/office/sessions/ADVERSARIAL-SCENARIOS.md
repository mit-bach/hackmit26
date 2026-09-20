# Adversarial scenario catalog — Maximor Demo Corp

Human catalog for the data-refinement agent. Bots must never load this file. Operational registers must never copy these titles, reason codes, or the word fraud.

Company: **Maximor Demo Corp** (`CO-MAXIMOR`). August 2026 is closed. September 2026 is the open close. The fraud and error already sit in the books from the CFO sabbatical. Agents onboard onto preexisting registers.

This catalog does not replace INV-001, INV-017 / FEE-729103, or TXN-2026-09-015. It explains the $12.40 (ADV-CASH-014) and adds quieter holes at $300–450M scale.

Counts: **109 scenarios**, **12 storylines**, **30 stealth-5**. Domain mix:

- `ap`: 13
- `ar`: 14
- `audit`: 9
- `cash`: 15
- `close`: 11
- `mixed`: 8
- `payroll`: 8
- `prepaid-fa`: 7
- `processor`: 6
- `reporting`: 8
- `vendor-master`: 10

## How to use this file

1. Read surviving plot IDs and loud decoys first.
2. Densify books to the scale below so a 19-line bank statement is not the world.
3. Plant registers and identity fields named in `plant_objects`. Do not invent a new scheme.
4. Put expected findings in a new hidden key section, not in Bot-readable files.
5. Do not edit Harness. Do not edit Operator-workspace. Do not load this catalog at runtime.

## What this is not

- Not SCN-AP-001 toys (clean three-way, quantity mismatch, same-vendor duplicate invoice, $50,000 round wire, labeled post-close JE, GM 64 percent to 61 percent as the whole story).
- Not a vendor-bank-change **control** result. Vendor bank **fields** are plant targets. Findings come from comparing those fields to bank NACHA receiving accounts and payroll DFI accounts.
- Not live Stripe or live email.
- Not a request to implement NOT_IMPLEMENTED engines. Credit-memo and unapplied-cash plants stay register-visible.

## Surviving plot IDs

- `INV-001` — Clean three-way match. Do not dirty.
- `PO-101` — Acme standing desks. Do not dirty.
- `GR-101` — Full receipt. Do not dirty.
- `PAY-AP-001` — ACH to Acme. Do not dirty.
- `TXN-2026-09-018A` — Exact cash match. Do not dirty.
- `INV-017` — Helios Hardware. Fee $25 explained via FEE-729103.
- `TXN-2026-09-011` — Wire net of fee. FEE_NETTED. Do not reclassify as unexplained.
- `FEE-729103` — Keep as the explained $25 evidence.
- `TXN-2026-09-015` — Keep identity. Catalog explains the $12.40 as 0.1 percent residual (ADV-CASH-014).
- `INV-AR-013` — Northstar LLC $12,400.00. Keep identity.
- `PAY-006` — Northstar remittance. Keep identity.
- `GL-AR-NS` — Books $12,400.00. Keep identity.
- `PR-2026-10-02` — Keep identity. Rescale amount. Overlay explains the miss (ghost + OT).
- `INV-AR-014` — Quiet Harbor late collection. Keep identity. Lapping overlay may mis-apply it.

## Loud decoys (leave them; do not reuse the pattern)

- VEND-001-DUP / Acme Supplies LLC — string-normalize duplicate. Too loud. Do not reuse this pattern.
- PAY-AP-009 / INV-009 $50,000.00 round-number + self-approval. Too loud. Leave as decoy.
- JE-POST-CLOSE-001 — labeled post_close. Too loud. Leave as decoy.
- GM 64 percent to 61 percent via TXN-SUP-SEP-001 / TXN-FRT-SEP-001 / TXN-HOST-SEP-001. Too loud. Do not retell.
- VEND-010 Northwind Phantom LLC unusual=true. Decoy.
- VEND-018 Shadow Vendor LLC. Decoy.

## Company densification the plant requires

Target economics (replace the $1.0M monthly P&L in `docs/demo-data.md` by updating `sample_data/pnl.py` and reporting ledgers):

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

Keep INV-001 at $12,450.00 as a real small facilities PO inside a large book. Keep the famous $12.40 as $12.40. Rescale payroll identities `PR-2026-*` and `ACT-PAYROLL-HIGH` without dropping those IDs.

Archive 11 months of bank, AP, AR, payroll, Stripe, and journals. A slow siphon cannot hide on a 19-line September statement alone.

Chart of accounts to add (one name each): `1000-Cash`, `1010-Payroll-Imprest`, `1020-Stripe-Clearing`, `1030-Undeposited-Funds`, `1100-AR`, `1110-AR-Unapplied`, `1200-Prepaid-Software`, `1210-Prepaid-Insurance`, `1220-Prepaid-Other`, `1300-Due-From-Affiliate`, `1350-Other-Receivable`, `1400-Inventory`, `1500-PPE`, `1510-Accum-Dep`, `2000-AP`, `2100-Due-To-Affiliate`, `2200-Payroll-Accrual`, `2300-Deferred-Revenue`, `4000-Revenue`, `4100-Contra-Revenue-Returns`, `5100-Hosting`, `5200-Supplier`, `5300-Freight`, `5400-Contractors`, `6000-Operating`, `6100-Payroll`, `6200-Benefits`, `6300-Occupancy`, `6400-Professional-Fees`, `6500-Bank-Fees`, `6600-Processor-Fees`, `6900-Misc-Expense`, `6950-Cash-Over-Short`.

## Identity bible

Use these names. Do not rename mid-plant.

### People

- **Dana Kestrel** — `EMP-4128` / `USR-VM-04, USR-PREP-04` — AP vendor-master clerk. Insider for SL-ADV-KESTREL. Spouse Evan Kestrel is organizer of VEND-KIS-01.
- **Evan Kestrel** — `n/a` / `n/a` — Organizer, Kestrel Industrial Supply LLC. Not an employee. EIN 87-2144091. Same home address as Dana.
- **Riley Cho** — `EMP-2201` / `USR-FAC-01` — Facilities coordinator, Cambridge campus. Insider for SL-ADV-CAMBRIDGE. Controls CAM true-up packets.
- **Tomas Halyard** — `EMP-8891` / `USR-WH-8891` — Remote warehouse coordinator — West (ghost). No badge, no Okta login, no laptop asset. Same bank as VEND-HAL-01.
- **Samir Okonkwo** — `EMP-3304` / `USR-APPLY-02` — AR cash applier. Insider for SL-ADV-LAPPING. Weekend postings.
- **Nadia Voss** — `EMP-1088` / `USR-JE-04, USR-NA-VOSS` — Assistant controller. Posts rec plugs and net-zero pairs. Cover for residuals and cash holes. Two user IDs.
- **Chris Pell** — `EMP-5510` / `USR-PR-01` — Payroll administrator. Not the ghost. Failed deprovision on EMP-2290. Signs Halyard as 'manager of record'.
- **Glen Park** — `EMP-6722` / `USR-GR-01` — Warehouse receiving, Cambridge. GR quantity games. Lazy counts, not the Kestrel organizer.
- **Mei Stratton** — `EMP-1190` / `USR-REV-05` — Revenue accountant. Bill-and-hold and cutoff JEs for Pinnacle / Atlas.
- **Luis Redmond** — `EMP-4402` / `USR-STRIPE-01` — Processor operations. Sole Stripe/Adyen reconciler. Connected-account skim.
- **Jordan Hale** — `EMP-0901` / `USR-APPR-HALE` — Procurement manager. Existing PO approver. Not the thief. Kestrel routes split POs through Hale.
- **Priya Nair** — `EMP-0902` / `USR-APPR-NAIR` — Finance manager. Existing. Reviews by amount. Misses sub-$25k splits.
- **Marcus Chen** — `EMP-0903` / `USR-APPR-CHEN` — Engineering operations. Existing PO approver.
- **Elena Vasquez** — `EMP-0904` / `USR-APPR-VASQ` — IT manager. Existing PO approver.
- **Ava Pell** — `EMP-2290` / `USR-WH-2290` — Warehouse associate (terminated 2026-03-31, still paid). Failed deprovision. Distinct from ghost Tomas Halyard.
- **Nia Bright** — `EMP-3310` / `USR-MKT-01` — Marketing manager. Requester on Brightline Studio retainers. Emergency contact Cara Bright at 14 Fayette Street.

Existing PO approvers stay: Jordan Hale ($25,000 limit), Priya Nair, Marcus Chen, Elena Vasquez.

### Vendors to add

- `VEND-KIS-01` **Kestrel Industrial Supply LLC** — MRO overflow from Northline Fabrication
- `VEND-NLF-02` **North Line Fab Inc** — Secondary fab cell. Adjacent to real Northline at 438 D Street.
- `VEND-NLF-03` **NLF Industrial Components** — None
- `VEND-WBT-01` **Westbrook Tooling** — Looks independent. Used as PO-split counterpart. Remit street sometimes 18 Ware Street.
- `VEND-HAL-01` **Halyard Facilities LLC** — West-campus janitorial. Same DFI account as EMP-8891.
- `VEND-CLR-01` **Clearing Solutions LLC** — Bank-rec consulting / cash-over-short true-up.
- `VEND-MPR-01` **Maximor Processing LLC** — NOT on vendor master. Stripe connected account acct_1MaximorProc.
- `VEND-BLS-01` **Brightline Studio LLC** — Demand-gen retainers. Same street as customer Brightline Media CUST-004.
- `VEND-CPS-01` **Cambridge Property Services** — CAM reconciliation agent for VEND-013.
- `VEND-MRH-01` **Merrimack Holdings LLC** — IC sweep / affiliate treasury. Not a legal affiliate of CO-MAXIMOR.
- `VEND-HES-01` **Harbor Electric Services** — Near Harbor Electric VEND-015 but different normalize key. Sub-meter 'projects'.
- `VEND-OIC-01` **Orbit Insights Corp** — Near Orbit Analytics VEND-012. Implementation + 36-month platform.
- `VEND-FLE-01` **Freightline Expedite** — Accessorials next to real Freightline Logistics VEND-019. Not TXN-FRT-SEP-001.
- `VEND-HBP-01` **Hartford Brokerage Partners** — Rider invoices next to real Hartford Insurance VEND-011.

Existing vendors stay, including Acme, Northline Fabrication, Helios Hardware, Harbor Electric, Orbit Analytics, Hartford Insurance, Cambridge Properties, Freightline Logistics, Lenovo, Dell.

### Customers to add

- `CUST-NSC-01` **Northstar Settlement Co** — Receives 'fee refunds' that recycle the 0.1 percent residual.
- `CUST-IC-EU` **Maximor EU BV** — Not in the legal entity graph. Billed as a customer. Fake affiliate.

Existing customers stay: Northwind Labs, Helios Analytics, Acme Industrial, Brightline Media, Quiet Harbor, Pinnacle Retail, Atlas Robotics, Lumen Labs, Northstar LLC, Meridian Health. Plant street on Brightline Media as 14 Fayette Street, Somerville MA 02143.

### Hidden reason codes (eval key only)

`RELATED_PARTY_VENDOR`, `RELATED_PARTY_REMITTANCE`, `BANK_INSTRUMENT_DRIFT`, `NEAR_DUPLICATE_VENDOR`, `PO_SPLIT_UNDER_LIMIT`, `GR_QUANTITY_OVERSTATEMENT`, `STANDING_PO_OVERCONSUMED`, `GR_BEFORE_AUTHORIZATION`, `CROSS_VENDOR_INVOICE_NUMBER`, `REMITTANCE_RATE_RESIDUAL`, `RESIDUAL_UNPLUGGED`, `REC_PLUG_NET_ZERO`, `UNAPPLIED_CASH_PARK`, `GHOST_EMPLOYEE`, `PAYROLL_VENDOR_BANK_COLLISION`, `CONTRACTOR_W2_DOUBLE_DIP`, `TERMINATED_EMPLOYEE_PAID`, `PREPAID_AMORT_MISPOSTED`, `AMORT_REVERSAL_PAIR`, `AR_LAPPING`, `REVENUE_CUTOFF`, `CHANNEL_STUFFING`, `BILL_AND_HOLD`, `PROCESSOR_FEE_OVERSTATEMENT`, `CONNECTED_ACCOUNT_SKIM`, `FAKE_INTERCOMPANY`, `ROUND_TRIP_COUNTERPARTY`, `CAM_TRUEUP_ORPHAN`, `NET_ZERO_JE_PAIR`, `CAPITALIZED_UNRECEIVED`, `FORECAST_BIAS_FROM_AR`, `FREIGHT_SURCHARGE_SKIM`, `SELF_APPROVAL_ALIAS`, `EFFECTIVE_DATE_MISMATCH`, `MIXED_SABBATICAL_SURFACE`.

Never write these codes into invoices.json, bank statements, or vendor names.

## Storylines

| ID | Title | Insider | Span | Cumulative |
| --- | --- | --- | --- | --- |
| `SL-ADV-KESTREL` | Kestrel — vendor-master clerk, three AP techniques | Dana Kestrel EMP-4128 | 2025-11 → 2026-09 | $187,412.18 related-party remittance plus $94,618.40 near-dup fab |
| `SL-ADV-RESIDUAL` | 0.1 percent remittance residual — true explanation of $12.40 | Nadia Voss EMP-1088 (plugs) with Clearing Solutions LLC | 2025-11 → 2026-09 | $86,418.60 over 11 plugged months; $12.40 unplugged on TXN-2026-09-015 |
| `SL-ADV-HALYARD` | Ghost employee plus janitorial vendor, same bank | Chris Pell failed deprovision; Tomas Halyard is the ghost identity | 2025-04 → 2026-09 | $146,309.45 W-2 plus $28,800 facilities AP plus $18,400 1099 |
| `SL-ADV-ORBIT` | Prepaid that never hits P&L | Nadia Voss + Orbit Insights Corp | 2025-01 → 2026-09 | $180,000 PRE-SFT-002 still on BS; $96,000 software cap that should expense |
| `SL-ADV-LAPPING` | AR lapping under chronic-late cover | Samir Okonkwo EMP-3304 | 2025-12 → 2026-09 | $412,880.00 misapplied stock; bank totals still tie |
| `SL-ADV-PINNACLE` | Bill-and-hold and revenue cutoff | Mei Stratton EMP-1190 | 2026-06 → 2026-09 | $2,400,000 Pinnacle plus $1,180,000 Atlas pulled into September |
| `SL-ADV-PROCESSOR` | Processor fee overstatement into a connected account | Luis Redmond EMP-4402 | 2025-10 → 2026-09 | $214,660.18 fee delta plus $18,440 dispute-win retention |
| `SL-ADV-MERRIMACK` | Intercompany that is not intercompany | Nadia Voss + Merrimack Holdings | 2025-12 → 2026-09 | $4,851,220.00 due-from balance; $2,200,000 cash already left |
| `SL-ADV-BRIGHTLINE` | Customer-vendor round trip | shared address 14 Fayette Street; no single employee required | 2025-09 → 2026-09 | $484,800 revenue and $524,800 opex; net $40,000 cash out |
| `SL-ADV-CAMBRIDGE` | CAM true-up and bank-number transposition | Riley Cho EMP-2201 | 2025-07 → 2026-09 | $126,408.22 CAM plus $48,000 diverted rent months |
| `SL-ADV-CLOSECOSMETIC` | Net-zero close cosmetics and missing assets | Nadia Voss EMP-1088 | 2026-03 → 2026-09 | $186,420.18 cash parked; $154,214.00 of FA with no asset tag |
| `SL-ADV-FREIGHT` | Accessorial freight skim, 40 basis points not 300 | Dana Kestrel (shared) + Freightline Expedite | 2025-11 → 2026-09 | $61,288.40 accessorials |

Shared identities across storylines:

- Dana Kestrel owns vendor master. She enables Kestrel Industrial, NLF near-dups, Freightline Expedite, and (as clerk) Brightline Studio's vendor row.
- Nadia Voss posts residual plugs, Orbit reversals, IC true-ups, and cash parks. September sabbatical stops her undocumented steps, which is why close is suddenly ugly.
- Glen Park rubber-stamps GRs for Kestrel SKUs and the Lenovo rollout.

## Stealth-5 index (30 cases)

- `ADV-VM-001` (vendor-master, 2025-11 → 2026-09) — Kestrel Industrial on the vendor master
- `ADV-VM-004` (vendor-master, 2026-06-12 → 2026-09) — Kestrel Industrial bank fields after a format cleanup
- `ADV-AP-001` (ap, 2026-04-06 → 2026-04-10 and repeats monthly) — Three POs the same week under the Hale limit
- `ADV-AP-003` (ap, 2025-12 → 2026-09) — Goods receipt quantity that matches the invoice and not the floor
- `ADV-MIX-001` (mixed, 2025-11 → 2026-09) — Kestrel spend in AP, bank, forecast, and the audit sample
- `ADV-CASH-014` (cash, 2025-11 → 2026-09) — Northstar remittance residual versus invoice
- `ADV-CASH-008` (cash, 2025-11 → 2026-08) — Monthly cash-over-short plug journals
- `ADV-CASH-012` (cash, 2026-02 → 2026-08) — Northstar Settlement Co refunds that recycle the residual
- `ADV-MIX-003` (mixed, 2025-11 → 2026-09) — Residual thread across cash, close, AP, forecast
- `ADV-PAY-001` (payroll, 2025-04-14 → 2026-09) — Remote warehouse coordinator on the payroll register
- `ADV-PAY-004` (payroll, 2025-04-20 → 2026-09) — Payroll DFI account that matches Halyard Facilities
- `ADV-PRE-001` (prepaid-fa, 2025-01-06 → 2026-09) — Orbit Insights prepaid that expenses into a balance-sheet account
- `ADV-PRE-002` (prepaid-fa, 2026-03 → 2026-08) — Expense posted then reversed the next day
- `ADV-AR-001` (ar, 2025-12 → 2026-09) — Cash applications that follow a chain
- `ADV-MIX-006` (mixed, 2025-12 → 2026-09) — Lapping across apply, cash, forecast, audit
- `ADV-AR-008` (ar, 2026-09-29 → 2026-09-30) — Pinnacle bill-and-hold dated September 29
- `ADV-AR-012` (ar, 2026-09-30 email, returns 2026-10-18) — October return window already reserved in email
- `ADV-PROC-001` (processor, 2025-10 → 2026-09) — Booked processor rate versus contract rate
- `ADV-PROC-002` (processor, 2025-10 → 2026-09) — Connected account that is not a vendor
- `ADV-CLOSE-001` (close, 2025-12-11 → 2026-09) — Due-from-affiliate that is not an affiliate
- `ADV-CLOSE-002` (close, 2026-01 → 2026-08) — Intercompany true-up journals that net to zero
- `ADV-MIX-002` (mixed, 2025-12 → 2026-09) — Fake affiliate in close, cash, forecast, and journal sample
- `ADV-AUDIT-003` (audit, 2026-09 sample of 2025-09 → 2026-09) — Two Brightline legal names, one street
- `ADV-VM-010` (vendor-master, 2026-05-22 → 2026-09) — Cambridge Properties account number after format cleanup
- `ADV-AUDIT-004` (audit, 2026-09) — Vendor sample that never joins the receiving account
- `ADV-CLOSE-006` (close, 2026-03-31 → 2026-08-31) — Cash parked in undeposited funds at month-end
- `ADV-CLOSE-010` (close, 2026-09-04 posting for 2026-08-31 effective) — August effective date, September posting date, not labeled post-close
- `ADV-AUDIT-005` (audit, 2022-09-08 → 2026-09) — Two user IDs for Nadia Voss
- `ADV-FA-001` (prepaid-fa, 2026-03-18 → 2026-09) — Lenovo rollout capitalized beyond tagged units
- `ADV-MIX-008` (mixed, 2025-04 → 2026-09) — Four storylines in one two-hour sim

## Mixed-function index

- `ADV-MIX-001` — Kestrel spend in AP, bank, forecast, and the audit sample — RELATED_PARTY_REMITTANCE | September function-green, combined $72,188.20 vs $18,000 budget | INV-KIS-2026-09-*, TXN-KIS-2026-09-16, FC-MRO-KIS, AUD-SAMP-KIS-08
- `ADV-MIX-003` — Residual thread across cash, close, AP, forecast — RESIDUAL_UNPLUGGED | $12.40 visible, $86,418.60 historical, forecast miss ~$7,187.60 | TXN-2026-09-015, TASK-CASH, INV-CLR-2026-08, FC-OTHER-IN
- `ADV-MIX-006` — Lapping across apply, cash, forecast, audit — AR_LAPPING | function-green, population $412,880.00 | PAY-LAP-*, BATCH-AR-2026-09-12, forecast week 2026-09-21
- `ADV-MIX-002` — Fake affiliate in close, cash, forecast, and journal sample — FAKE_INTERCOMPANY | $4,851,220.00 receivable, $2,200,000.00 cash gone | 1300, TXN-MRH-*, FC-IC-IN, JE-IC-TU-2026-08 + JE-IC-CLR-2026-08
- `ADV-MIX-004` — Brightline in AR, AP, cash, and board pack — ROUND_TRIP_COUNTERPARTY | four greens, net $2,200.00 per month out | CUST-004, VEND-BLS-01
- `ADV-MIX-005` — Cambridge rent in AP, bank, close, and facilities payroll — BANK_INSTRUMENT_DRIFT | rent diversion $192,000 plus CAM $126,408.22 plus stipend $18,000.00 span | EMP-2201, VEND-013, VEND-CPS-01, ALLW-CHO
- `ADV-MIX-007` — Freight leak in AP, bank, COGS, and Kestrel identity — FREIGHT_SURCHARGE_SKIM | $61,288.40 plus pointer to VEND-KIS-01 $187,412.18 | VEND-FLE-01, VEND-KIS-01, EMP-4128
- `ADV-MIX-008` — Four storylines in one two-hour sim — MIXED_SABBATICAL_SURFACE | $12.40 + $146,309.45 + $187,412.18 + $4,851,220.00 | TXN-2026-09-015, EMP-8891, VEND-KIS-01, 1300

## Scenarios

Each scenario is what to hide and where. The later agent writes the JSON rows, PDFs, and months. Do not reduce a scenario to a 4-line stub.

## SL-ADV-KESTREL — Kestrel — vendor-master clerk

Insider: Dana Kestrel EMP-4128. Span: 2025-11 → 2026-09. Techniques: related-party vendor, near-duplicate fab vendors, PO split under Hale $25,000, GR quantity overstatement. Cumulative: $187,412.18 related-party remittance plus $94,618.40 near-dup fab.

### ADV-VM-001 — Kestrel Industrial on the vendor master

- **domain:** `vendor-master`
- **stealth:** 5
- **span:** 2025-11 → 2026-09
- **storyline:** `SL-ADV-KESTREL`
- **preexisting_state:** August books already contain VEND-KIS-01 as an ordinary MRO vendor. Eleven months of AP have posted. Dana Kestrel EMP-4128 is the last_modified_by on the vendor record. August close signed with AP subledger tying.
- **plant_objects:**
  - `vendor_master:VEND-KIS-01`
  - `employee_master:EMP-4128`
  - `vendor_bank:VEND-KIS-01:011000138:4419`
  - `ap_invoices:INV-KIS-2025-11 through INV-KIS-2026-09`
  - `gl:2000-AP`
  - `gl:6000-Operating`
- **how_it_hides:** The vendor name does not fuzzy-match Acme or Northline. EIN 87-2144091 is valid. Three-way match passes because Glen Park books GR equal to PO. Naive duplicate-vendor (normalize_vendor) does not fire. Amounts sit between $14,206.18 and $24,880.44, under Jordan Hale's $25,000 limit.
- **detective_path:**
  1. List vendors created after 2025-10-01 with monthly AP between $10,000 and $25,000.
  2. Join vendor_master.address and organizer_name to employee_master.home_address and emergency_contact for EMP-4128.
  3. Match EIN 87-2144091 and 18 Ware Street to Dana Kestrel's personnel file.
  4. Sum AP to VEND-KIS-01 from 2025-11 through 2026-09 ($187,412.18).
  5. Trace ACH receiving DFI account 4419 to the same routing Dana uses for payroll.
- **expected_finding:** RELATED_PARTY_VENDOR | $187,412.18 cumulative | VEND-KIS-01, EMP-4128, EIN 87-2144091, bank ****4419
- **must_not:**
  - Do not use the VEND-001 / VEND-001-DUP string-normalize pattern.
  - Do not label the vendor unusual=true.
  - Do not put the word fraud on the vendor record.
  - Do not make $24,880.44 a round $25,000.00.
  - Do not emit HUMAN_REVIEW as a Bot status.
- **demo_beat:** Judge sees an ordinary MRO vendor. Audit Bot only catches it after joining vendor address to the employee file.

### ADV-VM-002 — North Line Fab Inc beside Northline Fabrication

- **domain:** `vendor-master`
- **stealth:** 4
- **span:** 2026-01 → 2026-09
- **storyline:** `SL-ADV-KESTREL`
- **preexisting_state:** VEND-003 Northline Fabrication remains a real supplier (INV-014/015/016 grouped ACH still valid). A second vendor VEND-NLF-02 North Line Fab Inc exists from 2026-01-15 at 440 D Street, one door from 438 D Street.
- **plant_objects:**
  - `vendor_master:VEND-003`
  - `vendor_master:VEND-NLF-02`
  - `ap_invoices:INV-NLF-02-*`
  - `purchase_orders:PO-NLF-02-*`
  - `bank:TXN-NLF-02-*`
- **how_it_hides:** normalize_vendor('North Line Fab Inc') is not equal to normalize_vendor('Northline Fabrication') if the plant keeps the space and Inc. Different EIN 04-3391088 vs 04-2817762. Invoice numbers use NLF-2-##### so duplicate-invoice control is silent.
- **detective_path:**
  1. Cluster vendors by street number on D Street, Boston 02210.
  2. Compare remit names NORTHLINE FAB vs NORTH LINE FAB INC on ACH.
  3. Confirm VEND-003 invoices INV-014/015/016 still group-match TXN-2026-09-008.
  4. Sum VEND-NLF-02 AP 2026-01 through 2026-09 ($94,618.40).
  5. Check that Dana Kestrel last-touched VEND-NLF-02 on 2026-01-14.
- **expected_finding:** NEAR_DUPLICATE_VENDOR | $94,618.40 | VEND-NLF-02 vs VEND-003, 440 D Street vs 438 D Street
- **must_not:**
  - Do not merge VEND-NLF-02 into VEND-001-DUP logic.
  - Do not break PAY-AP-NORTHLINE or TXN-2026-09-008.
  - Do not name the vendor Northline Fabrication LLC (too close to the loud decoy).

### ADV-VM-003 — NLF Industrial Components on the same dock

- **domain:** `vendor-master`
- **stealth:** 4
- **span:** 2026-03 → 2026-09
- **storyline:** `SL-ADV-KESTREL`
- **preexisting_state:** A third identity VEND-NLF-03 NLF Industrial Components, Suite B of 440 D Street, starts 2026-03-02. Used when VEND-NLF-02 monthly spend would break $25,000.
- **plant_objects:**
  - `vendor_master:VEND-NLF-03`
  - `ap_invoices:INV-NLF-03-*`
  - `purchase_orders:PO-NLF-03-*`
  - `goods_receipts:GR-NLF-03-*`
- **how_it_hides:** Third legal name, third EIN 04-4419022. Each invoice still three-way matches its own PO. Spend per vendor per month stays under Hale's limit. Receiving dock scans show one BOL for both NLF vendors.
- **detective_path:**
  1. Group open AP by delivery_dock_id CAM-DOCK-4.
  2. Find BOLs that list both NLF-2 and NLF-3 SKUs on one truck.
  3. Add VEND-NLF-02 and VEND-NLF-03 monthly spend. Several months exceed $25,000 combined.
  4. Match Suite B mail forwarding to 18 Ware Street (Kestrel home).
- **expected_finding:** NEAR_DUPLICATE_VENDOR | $41,206.88 | VEND-NLF-03, CAM-DOCK-4, combined with VEND-NLF-02 above Hale limit
- **must_not:**
  - Do not create a single invoice over $25,000.
  - Do not reuse vendor_invoice_number across the two NLF IDs in a way that trips the loud duplicate control.

### ADV-VM-004 — Kestrel Industrial bank fields after a format cleanup

- **domain:** `vendor-master`
- **stealth:** 5
- **span:** 2026-06-12 → 2026-09
- **storyline:** `SL-ADV-KESTREL`
- **preexisting_state:** On 2026-06-12 vendor_bank for VEND-KIS-01 changes from account ********4401 (a real industrial lockbox Dana used as cover) to ********4419. Change_memo is 'normalize ACH formatting / strip spaces'. No dual-control field exists in the engine.
- **plant_objects:**
  - `vendor_bank_history:VEND-KIS-01`
  - `vendor_master.change_memo`
  - `bank_statement.receiving_account on TXN-KIS-* after 2026-06-12`
  - `payroll_direct_deposit:EMP-4128`
- **how_it_hides:** There is no vendor-bank-change control to fail. Naive match still pays the vendor_id on the invoice. Pre-June ACH went to 4401 and looked like a real supplier lockbox. After June, bank NACHA receiving account is 4419, which equals Dana's payroll account, but the vendor name on the statement is still KESTREL INDUSTRIAL.
- **detective_path:**
  1. Diff vendor_bank_history for VEND-KIS-01 on 2026-06-12.
  2. Do not wait for a control named bank-change. Compare vendor_bank.account_last4 to bank_statement.receiving_account_last4.
  3. Join 4419 plus routing 011000138 to payroll_direct_deposit for EMP-4128.
  4. Confirm invoices after 2026-06-12 still three-way match.
  5. Magnitude after the swap only: $62,118.90 (June-September).
- **expected_finding:** BANK_INSTRUMENT_DRIFT | $62,118.90 after 2026-06-12 | VEND-KIS-01 account 4401→4419, EMP-4128 payroll account 4419
- **must_not:**
  - Do not invent a FAIL from an unimplemented vendor-bank-change control.
  - Do not put 'fraud' in change_memo. Keep 'normalize ACH formatting / strip spaces'.
  - Do not change INV-001 Acme bank instructions.
- **demo_beat:** Ten-minute demo: Cash Bot matches ACH to AP. Audit Bot joins receiving account to payroll and the story changes.

### ADV-AP-001 — Three POs the same week under the Hale limit

- **domain:** `ap`
- **stealth:** 5
- **span:** 2026-04-06 → 2026-04-10 and repeats monthly
- **storyline:** `SL-ADV-KESTREL`
- **preexisting_state:** Jordan Hale approval_limit $25,000 is already in purchase_orders.json. August and September each contain a cluster of three POs dated within four days: PO-KIS-4601 $24,880.44, PO-WBT-4602 $24,106.18, PO-KIS-4603 $23,413.56. Economic purchase is $72,400.18 of the same SKU family KIS-MRO-7x.
- **plant_objects:**
  - `purchase_orders:PO-KIS-4601`
  - `purchase_orders:PO-WBT-4602`
  - `purchase_orders:PO-KIS-4603`
  - `ap_invoices:INV-KIS-4601`
  - `ap_invoices:INV-WBT-4602`
  - `ap_invoices:INV-KIS-4603`
  - `goods_receipts:GR-KIS-4601`
  - `goods_receipts:GR-WBT-4602`
  - `goods_receipts:GR-KIS-4603`
- **how_it_hides:** Each PO is under $25,000 so Hale can approve alone. Each invoice equals its PO and GR. Westbrook Tooling looks unrelated. SKU prefix is the join, not the vendor name. Policy P-007 alias rules never fire.
- **detective_path:**
  1. Cluster POs by requested_by EMP-4128 and by week.
  2. Join line items on sku_prefix KIS-MRO-7.
  3. Sum authorized_amount per cluster. Flag clusters above $25,000 with one requester.
  4. Match Westbrook remit address on INV-WBT-4602 to 18 Ware Street (occurs on 2026-07 and 2026-08 only — not every month).
  5. Repeat the cluster detection across 2026-04 through 2026-09. Five of six months contain a trio.
- **expected_finding:** PO_SPLIT_UNDER_LIMIT | $72,400.18 April cluster; $348,206.40 across five months | PO-KIS-4601, PO-WBT-4602, PO-KIS-4603 and monthly siblings
- **must_not:**
  - Do not plant a single PO at $50,000 (that is the loud INV-009 decoy).
  - Do not set approver equal to requester on these POs (loud SOD).
  - Do not break Hale's $25,000 limit on PO-101.
- **demo_beat:** Two-hour sim: AP Bot approves each invoice. Audit Bot clusters SKUs and the Hale limit becomes the story.

### ADV-AP-002 — Invoice numbers that are unique per vendor_id

- **domain:** `ap`
- **stealth:** 3
- **span:** 2026-05 → 2026-09
- **storyline:** `SL-ADV-KESTREL`
- **preexisting_state:** Duplicate control keys on (vendor, vendor_invoice_number). Kestrel issues KIS-10442 against VEND-KIS-01 and KIS-10442 against VEND-NLF-02. Same PDF layout, different vendor_id.
- **plant_objects:**
  - `ap_invoices:INV-KIS-10442`
  - `ap_invoices:INV-NLF-10442`
  - `ingestion:files/KIS-10442.pdf`
  - `ingestion:files/NLF-10442.pdf`
- **how_it_hides:** P-002 duplicate vendor invoice number is per vendor. Both rows pass. File hashes are not compared by the current engine. Amounts differ by $18.40 so amount-duplicate is silent.
- **detective_path:**
  1. Hash invoice PDFs regardless of vendor_id.
  2. Compare vendor_invoice_number across the whole AP population, not within vendor.
  3. Note both files share creator Dana Kestrel's laptop asset tag MX-LPT-4128 in PDF metadata.
  4. Tie both invoices to CAM-DOCK-4 receipts on the same day.
- **expected_finding:** CROSS_VENDOR_INVOICE_NUMBER | $18,406.22 + $18,424.62 | INV-KIS-10442, INV-NLF-10442, number KIS-10442
- **must_not:**
  - Do not reuse INV-006 / INV-007 same-vendor duplicate. That toy stays as decoy.
  - Do not make the amounts identical.

### ADV-AP-003 — Goods receipt quantity that matches the invoice and not the floor

- **domain:** `ap`
- **stealth:** 5
- **span:** 2025-12 → 2026-09
- **storyline:** `SL-ADV-KESTREL`
- **preexisting_state:** Three-way match uses PO qty, invoice qty, GR qty. Glen Park EMP-6722 books GR qty = invoice qty. Cycle-count file cycle_counts.json (new plant) for CAM-BIN-A14 shows persistent 6–11 percent short vs GR on SKU family KIS-MRO-7.
- **plant_objects:**
  - `goods_receipts:GR-KIS-*`
  - `cycle_counts:CC-CAM-A14-2025-12 through CC-CAM-A14-2026-09`
  - `inventory:1400-Inventory`
  - `warehouse:CAM-BIN-A14`
  - `employee_master:EMP-6722`
- **how_it_hides:** AP three-way match passes because the GR is a copy of the invoice. Shrink hits 5200-Supplier or 6900-Misc as 'cycle variance' in small monthly JEs JE-SHRINK-YYYY-MM ($1,840–$3,220), below materiality in audit/policy.json ($10,000).
- **detective_path:**
  1. Reperform three-way match on INV-KIS-* (it will pass).
  2. Join GR quantity to cycle_counts for the same SKU and bin.
  3. Sum JE-SHRINK-YYYY-MM. Eleven months = $28,614.80 labeled cycle variance.
  4. Compare Glen Park GR timestamps: 41 receipts posted 16:02–16:04, same minute as the invoice scan.
  5. Physical short vs GR on KIS-MRO-7 is 9,412 units cumulative.
- **expected_finding:** GR_QUANTITY_OVERSTATEMENT | $28,614.80 shrink JEs covering 9,412 units | GR-KIS-*, CC-CAM-A14-*, JE-SHRINK-YYYY-MM, EMP-6722
- **must_not:**
  - Do not copy INV-003 Datadog partial-receipt hold. That remains a loud quantity mismatch.
  - Do not make GR qty differ from invoice qty (that would HOLD under P-005).
  - Do not put HUMAN_REVIEW on the AP row.

### ADV-AP-004 — Freight add-on invoices under the variance policy

- **domain:** `ap`
- **stealth:** 3
- **span:** 2025-11 → 2026-09
- **storyline:** `SL-ADV-KESTREL`
- **preexisting_state:** Policy P-009 allows abs <= $300 and <= 3 percent. Kestrel does not put freight on the main invoice. Separate invoices INV-KIS-FRT-YYYY-MM for $184.22 to $287.14, no PO, paid as non-PO after Dana posts a 'standing freight PO' PO-KIS-FRT-STANDING $300.00.
- **plant_objects:**
  - `purchase_orders:PO-KIS-FRT-STANDING`
  - `ap_invoices:INV-KIS-FRT-2025-11 through INV-KIS-FRT-2026-09`
  - `company_policies:P-008`
  - `company_policies:P-009`
- **how_it_hides:** P-008 would hold missing-PO invoices. The standing PO at $300 exists and is approved by Hale. Each freight invoice is under $300 so it matches the standing PO within P-009. Eleven small invoices do not look like INV-004 price mismatch.
- **detective_path:**
  1. List invoices paid against PO-KIS-FRT-STANDING.
  2. Sum them ($2,618.47). The standing PO authorized_amount is $300, not $2,618.
  3. Test whether AP rolled up standing-PO consumption across months (it did not).
  4. Join freight invoice remit to VEND-KIS-01, not Freightline Logistics.
- **expected_finding:** STANDING_PO_OVERCONSUMED | $2,618.47 vs $300 authorized | PO-KIS-FRT-STANDING, INV-KIS-FRT-*
- **must_not:**
  - Do not use a $5,000 Slack-style price mismatch.
  - Do not pay without a PO (that would HOLD).

### ADV-AP-005 — Receipt date before purchase-order date

- **domain:** `ap`
- **stealth:** 3
- **span:** 2026-08-11 → 2026-08-14
- **storyline:** `SL-ADV-KESTREL`
- **preexisting_state:** August already closed. PO-KIS-4812 created 2026-08-14. GR-KIS-4812 received_date 2026-08-11. Invoice INV-KIS-4812 $19,406.50 dated 2026-08-13. Three-way match ignores date order.
- **plant_objects:**
  - `purchase_orders:PO-KIS-4812`
  - `goods_receipts:GR-KIS-4812`
  - `ap_invoices:INV-KIS-4812`
  - `close/tasks August TASK-AP`
- **how_it_hides:** Match engines compare amounts and quantities, not whether a receipt can precede authorization. August AP rec still ties. The GR was posted by Glen Park with memo 'dock leftover from prior PO'.
- **detective_path:**
  1. For every GR, test received_date >= po.created_date.
  2. Filter exceptions to requested_by EMP-4128.
  3. INV-KIS-4812 is $19,406.50, paid 2026-08-28 TXN-KIS-4812.
  4. Confirm August close workpapers did not include a date-order test.
- **expected_finding:** GR_BEFORE_AUTHORIZATION | $19,406.50 | PO-KIS-4812 2026-08-14, GR-KIS-4812 2026-08-11, INV-KIS-4812
- **must_not:**
  - Do not mark the invoice HOLD for missing GR.
  - Do not touch GR-101 / INV-001 dates.

### ADV-AP-006 — Westbrook Tooling remit street that sometimes matches Kestrel

- **domain:** `ap`
- **stealth:** 4
- **span:** 2026-07 → 2026-08
- **storyline:** `SL-ADV-KESTREL`
- **preexisting_state:** VEND-WBT-01 is a real-looking Connecticut tool shop. July and August remittance advice PDF footer shows 18 Ware Street. September footer reverts to 90 Progress Drive, Westbrook CT.
- **plant_objects:**
  - `vendor_master:VEND-WBT-01`
  - `ap_invoices:INV-WBT-2026-07`
  - `ap_invoices:INV-WBT-2026-08`
  - `ingestion:files/INV-WBT-2026-07.pdf`
  - `bank:TXN-WBT-2026-07`
- **how_it_hides:** Vendor master address stays 90 Progress Drive. Only the invoice PDF remit block drifts, two months only, then 'corrected'. Bank counterparty remains WESTBROOK TOOLING. Naive vendor-address match vs master passes.
- **detective_path:**
  1. Extract remit address from invoice PDFs, not only vendor_master.address.
  2. Find 18 Ware Street on INV-WBT-2026-07 and INV-WBT-2026-08.
  3. Join that street to EMP-4128.
  4. Amounts: $24,106.18 (Jul) and $23,940.00 (Aug). Not round thousands except Aug is $23,940.00 — still not $25,000.
- **expected_finding:** RELATED_PARTY_REMITTANCE | $48,046.18 | INV-WBT-2026-07, INV-WBT-2026-08, 18 Ware Street
- **must_not:**
  - Do not permanently change vendor_master.address (that would be loud).
  - Do not use $50,000.00.

### ADV-MIX-001 — Kestrel spend in AP, bank, forecast, and the audit sample

- **domain:** `mixed`
- **stealth:** 5
- **span:** 2025-11 → 2026-09
- **storyline:** `SL-ADV-KESTREL`
- **preexisting_state:** The same VEND-KIS-01 payments sit in AP open items, operating-account ACH, 13-week forecast as 'recurring MRO', and the audit random sample as low-value recurring. Each function in isolation is green.
- **plant_objects:**
  - `ap_invoices:INV-KIS-*`
  - `bank:TXN-KIS-*`
  - `reporting/forecast_lines:FC-MRO-KIS`
  - `audit/invoices sample item AUD-SAMP-KIS-08`
  - `reporting/budget MRO_industrial`
- **how_it_hides:** AP matches. Cash grouped-matches ACH to three Kestrel invoices the way Northline is supposed to work. Forecast treats the spend as in-policy MRO. Audit sampling by dollar value keeps each invoice below high_risk_min_amount $10,000 in some months and treats others as ordinary recurring.
- **detective_path:**
  1. AP Bot: list VEND-KIS-01 YTD.
  2. Cash Bot: match TXN-KIS-2026-09-16 $47,293.62 as grouped ACH of two Kestrel plus one Westbrook.
  3. Story Bot: FC-MRO-KIS week of 2026-09-21 is $24,880.44 'as planned'.
  4. Audit Bot: sample AUD-SAMP-KIS-08 PASS on three-way match.
  5. Join the four pictures on vendor_id and EMP-4128. Combined September outflow $72,188.20 vs budget $18,000 MRO.
- **expected_finding:** RELATED_PARTY_REMITTANCE | September function-green, combined $72,188.20 vs $18,000 budget | INV-KIS-2026-09-*, TXN-KIS-2026-09-16, FC-MRO-KIS, AUD-SAMP-KIS-08
- **must_not:**
  - Do not fail the Northline grouped ACH TXN-2026-09-008.
  - Do not mark the audit sample FAIL on three-way match. The fail is the join.
  - Do not use HUMAN_REVIEW on the cash grouped match.
- **demo_beat:** This is the 10-minute 'one invoice, four Bots' beat, except the invoice is boring until the join.

### ADV-AUDIT-007 — Low-value recurring MRO in the audit sample

- **domain:** `audit`
- **stealth:** 4
- **span:** 2026-09 sample of 2025-11 → 2026-09
- **storyline:** `SL-ADV-KESTREL`
- **preexisting_state:** audit/policy.json high_risk_min_amount is $10,000. Several Kestrel invoices are $8,200–$9,840. They land in the ordinary recurring bucket. Three-way reperformance PASSes.
- **plant_objects:**
  - `audit/invoices:AUD-SAMP-KIS-08`
  - `audit/policy.json round_number.ordinary_recurring_max`
  - `ap_invoices:INV-KIS-2026-02-08`
- **how_it_hides:** Round-number control uses divisors 100/1000/10000. $8,240.18 is not round. Recurring MRO is expected. Sample size does not include vendor-address-to-employee join.
- **detective_path:**
  1. Reperform three-way match on AUD-SAMP-KIS-08 (PASS).
  2. Extend the sample to all VEND-KIS-01 invoices, not the random draw.
  3. Add related-party join from ADV-VM-001.
  4. Write finding on population, not on the sample item match.
- **expected_finding:** RELATED_PARTY_VENDOR | sample PASS, population $187,412.18 | AUD-SAMP-KIS-08, VEND-KIS-01
- **must_not:**
  - Do not FAIL the sample on DUPLICATE_VENDOR (that code is owned by VEND-001-DUP).
  - Do not FAIL on ROUND_NUMBER.

### ADV-VM-011 — Harbor Electric Services beside Harbor Electric

- **domain:** `vendor-master`
- **stealth:** 4
- **span:** 2026-02 → 2026-09
- **storyline:** `SL-ADV-KESTREL`
- **preexisting_state:** VEND-015 Harbor Electric remains the clean utility accrual vendor (CTR-HE-001, ACC-HE-2026-09). VEND-HES-01 Harbor Electric Services bills sub-meter 'project power' $3,106.18 to $4,880.40. Dana Kestrel created it 2026-02-01.
- **plant_objects:**
  - `vendor_master:VEND-015`
  - `vendor_master:VEND-HES-01`
  - `ap_invoices:INV-HES-*`
  - `close/accruals:ACC-HE-2026-09`
  - `vendor_contracts:CTR-HE-001`
- **how_it_hides:** normalize_vendor keeps Services vs the utility name apart. Each HES invoice three-way matches a facilities PO under $25,000. Harbor Electric monthly accrual still posts. Two electricity vendors look like campus plus construction.
- **detective_path:**
  1. Keep ACC-HE-2026-09 and CTR-HE-001 as the clean utility path.
  2. Sum VEND-HES-01 AP February through September ($29,418.66).
  3. Meter IDs on HES invoices equal Harbor Electric's Cambridge campus meters with suffix -P.
  4. created_by USR-VM-04. Remit address forwards to 18 Ware Street on two invoices (2026-05 and 2026-08).
- **expected_finding:** NEAR_DUPLICATE_VENDOR | $29,418.66 | VEND-HES-01 vs VEND-015, ACC-HE-2026-09 untouched
- **must_not:**
  - Do not break Harbor Electric accrual or later_invoices Harbor bills.
  - Do not use the Acme Supplies LLC normalize pattern.
## SL-ADV-RESIDUAL — 0.1 percent remittance residual

Insider: Nadia Voss EMP-1088 (plugs) with Clearing Solutions LLC. Span: 2025-11 → 2026-09. Techniques: customer remits 100.1 percent, books take 100 percent, monthly rec plug to VEND-CLR-01, September plug skipped during CFO sabbatical. Cumulative: $86,418.60 over 11 plugged months; $12.40 unplugged on TXN-2026-09-015.

### ADV-CASH-014 — Northstar remittance residual versus invoice

- **domain:** `cash`
- **stealth:** 5
- **span:** 2025-11 → 2026-09
- **storyline:** `SL-ADV-RESIDUAL`
- **preexisting_state:** Canonical unexplained item remains: INV-AR-013 $12,400.00, PAY-006, bank TXN-2026-09-015 $12,412.40, GL-AR-NS $12,400.00. No FEE-729103 analog. Close TASK-CASH / TASK-FINAL blocked. August books already contain eleven months of the same 0.1 percent pattern that was plugged.
- **plant_objects:**
  - `ar_invoices:INV-AR-013`
  - `ar_payments:PAY-006`
  - `bank:TXN-2026-09-015`
  - `gl:GL-AR-NS`
  - `close/tasks:TASK-CASH`
  - `historical_ar:INV-NS-*`
  - `bank_archive:TXN-NS-*-residual`
- **how_it_hides:** A one-line recon sees $12.40 and stops. The amount is small versus $10,000 materiality. Northstar is coded on_time. The 0.1 percent rate (12.40 / 12,400 = 0.001) is the signal, not the $12.40. Prior months the residual was journaled away so cash rec tied.
- **detective_path:**
  1. Keep TXN-2026-09-015 unmatched. Do not force MATCHED.
  2. Compute bank_amount / invoice_amount for every Northstar cash line 2025-11 through 2026-09. Rate is 1.001 on 14 of 14 receipts.
  3. Extend the ratio test to Meridian Health and Lumen Labs ACH (ADV-AR-013).
  4. Find JE-REC-PLUG-YYYY-MM in August and prior. None exists for 2026-09.
  5. Tie residual population to VEND-CLR-01 payments (ADV-CASH-009).
  6. Reason code is RESIDUAL_UNPLUGGED, not UNEXPLAINED_DIFFERENCE as a dead end.
- **expected_finding:** RESIDUAL_UNPLUGGED | $12.40 on TXN-2026-09-015 which is 0.1 percent of $12,400.00; $86,418.60 plugged 2025-11..2026-08 | INV-AR-013, PAY-006, TXN-2026-09-015, GL-AR-NS, JE-REC-PLUG-*
- **must_not:**
  - Do not invent fee evidence for the $12.40 (INV-017 / FEE-729103 stays the only explained $25).
  - Do not rename TXN-2026-09-015.
  - Do not put HUMAN_REVIEW on the cash row. Status stays EXCEPTION_OPEN / CLOSE_BLOCKED until the residual rate is written up.
  - Do not make $12.40 the only planted residual.
- **demo_beat:** Judge already knows the $12.40 blocks close. The 2-hour win is showing it is the unplugged 0.1 percent remainder, not a mystery penny.

### ADV-CASH-008 — Monthly cash-over-short plug journals

- **domain:** `cash`
- **stealth:** 5
- **span:** 2025-11 → 2026-08
- **storyline:** `SL-ADV-RESIDUAL`
- **preexisting_state:** August close already includes JE-REC-PLUG-2026-08 $7,206.18 Dr 6950-Cash-Over-Short Cr 2000-AP VEND-CLR-01. Prior months exist back to 2025-11. Each plug equals that month's 0.1 percent residuals within $0.08.
- **plant_objects:**
  - `gl:JE-REC-PLUG-2025-11 through JE-REC-PLUG-2026-08`
  - `gl:6950-Cash-Over-Short`
  - `close/journal_entries`
  - `employee_master:EMP-1088`
- **how_it_hides:** Each JE nets with the later AP payment so 6950 ends near zero. Close checklist 'cash over/short under $50' passes. Poster is USR-JE-04 (Nadia). Approver is USR-REV-04, a shared close mailbox, so SOD-002 looks populated.
- **detective_path:**
  1. List journals with memo containing 'rec true-up' or account 6950.
  2. For each month, sum (bank - AR applied) on 1.001-rate customers. Compare to the plug.
  3. Confirm no JE-REC-PLUG-2026-09 exists.
  4. Check approver_id USR-REV-04 has no person in employee_master.
- **expected_finding:** REC_PLUG_NET_ZERO | $86,418.60 across 11 months | JE-REC-PLUG-2025-11..JE-REC-PLUG-2026-08, 6950-Cash-Over-Short, USR-JE-04
- **must_not:**
  - Do not label these post_close=true (that is the loud JE-POST-CLOSE-001 decoy).
  - Do not use round $7,000.00 plugs.

### ADV-CASH-009 — Clearing Solutions LLC paid from the plug

- **domain:** `cash`
- **stealth:** 4
- **span:** 2025-12 → 2026-09
- **storyline:** `SL-ADV-RESIDUAL`
- **preexisting_state:** VEND-CLR-01 invoices CLR-RET-YYYY-MM for 'bank rec support' equal to last month's plug, paid ACH 12 days after close. September 2026 still has AP open INV-CLR-2026-08 $7,206.18, not yet paid because close is blocked.
- **plant_objects:**
  - `vendor_master:VEND-CLR-01`
  - `ap_invoices:INV-CLR-2025-12 through INV-CLR-2026-08`
  - `bank:TXN-CLR-*`
  - `canonical/vendor_payments:PAY-CLR-*`
- **how_it_hides:** Vendor looks like a consultant. Amounts are not round. Three-way match uses a standing SOW CTR-CLR-001 $10,000/month retainer, so each invoice is 'under contract'. Cash rec of the ACH matches AP.
- **detective_path:**
  1. Compare INV-CLR-YYYY-MM amount to JE-REC-PLUG for the prior month. Equal within $0.08.
  2. CTR-CLR-001 monthly_minimum is $10,000 but invoices are $6,100–$8,800. The retainer is cover, not economics.
  3. Vendor EIN 85-2201988 organizer is a registered agent in Wilmington with no operating website.
  4. Payment initiator USR-JE-04, not USR-PAY-01, on 8 of 11 ACH (SOD on payment initiation).
- **expected_finding:** RELATED_PARTY_REMITTANCE | $86,418.60 | VEND-CLR-01, INV-CLR-*, PAY-CLR-*, CTR-CLR-001 vs actuals
- **must_not:**
  - Do not mark VEND-CLR-01 unusual=true.
  - Do not pay INV-CLR-2026-08 automatically in September (close is blocked; AP may still show open).

### ADV-CASH-010 — Account 6950 that always finishes near zero

- **domain:** `cash`
- **stealth:** 4
- **span:** 2025-11 → 2026-08
- **storyline:** `SL-ADV-RESIDUAL`
- **preexisting_state:** Trial balance 6950-Cash-Over-Short is $12.18 credit at August 31 and $12.40 debit at September 20 (the Northstar residual). Close materiality treats 6950 as a clearing account.
- **plant_objects:**
  - `reporting/ledger_seed:6950-Cash-Over-Short`
  - `close/materiality.json`
  - `gl:JE-REC-PLUG-*`
- **how_it_hides:** A BS tie-out of 6950 'to activity' passes because the schedule is a copy of the plugs. Nobody asks why a clearing account has $86k of annual throughput.
- **detective_path:**
  1. Pull 6950 YTD debits and credits, not the ending balance.
  2. Throughput $86,418.60 vs ending $12.18 is the finding.
  3. Map every credit in 6950 to a VEND-CLR-01 invoice.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** REC_PLUG_NET_ZERO | throughput $86,418.60 vs ending $12.18 | 6950-Cash-Over-Short
- **must_not:**
  - Do not set 6950 ending balance to $0.00 in September (the $12.40 must remain).

### ADV-CASH-011 — Undeposited funds used as a residual parking lot

- **domain:** `cash`
- **stealth:** 4
- **span:** 2026-03 → 2026-09
- **storyline:** `SL-ADV-RESIDUAL`
- **preexisting_state:** Some 0.1 percent residuals never hit 6950. They sit in 1030-Undeposited-Funds as $40–$180 slices with memo 'ACH batch remainder'. September 1030 includes $12.40 plus $1,108.66 of older slices.
- **plant_objects:**
  - `gl:1030-Undeposited-Funds`
  - `bank:undeposited_batch_refs`
  - `close/tasks:TASK-CASH`
- **how_it_hides:** Cash recon of deposited items still matches. 1030 is a standard float account. Aging of undeposited slices is not a Kernel control.
- **detective_path:**
  1. Age 1030 items. Anything >5 business days is an exception at this company (policy plant P-CASH-UNDEP-AGE).
  2. Sum slices with memo ACH batch remainder ($1,121.06 including $12.40).
  3. Match slice sizes to 0.1 percent of the same-day AR batch.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** UNAPPLIED_CASH_PARK | $1,121.06 aged in 1030 | 1030-Undeposited-Funds, including TXN-2026-09-015 residual
- **must_not:**
  - Do not clear 1030 as part of forcing a September match.

### ADV-CASH-012 — Northstar Settlement Co refunds that recycle the residual

- **domain:** `cash`
- **stealth:** 5
- **span:** 2026-02 → 2026-08
- **storyline:** `SL-ADV-RESIDUAL`
- **preexisting_state:** CUST-NSC-01 Northstar Settlement Co receives small AP-like refunds REF-NSC-* of $600–$1,200 labeled 'duplicate lockbox return'. Cash leaves operating account. AR for Northstar LLC stays clean.
- **plant_objects:**
  - `ar_customers:CUST-NSC-01`
  - `bank:TXN-NSC-REF-*`
  - `gl:6900-Misc-Expense`
  - `ar_customers:CUST-009`
- **how_it_hides:** Refunds are not linked to INV-AR-013. Bank description NORTHSTAR SETTLEMENT looks like the customer family. Amounts do not equal any single residual, so one-to-one recon does not connect them. Books expense them as lockbox errors.
- **detective_path:**
  1. Sum REF-NSC-* ($8,406.00 through August).
  2. Compare to 0.1 percent of Northstar LLC receipts over the same window ($8,388.20). Gap $17.80.
  3. Confirm CUST-NSC-01 has no open AR invoices of its own.
  4. Do not treat this as the $12.40 itself. It is the recycle path for plugged months.
- **expected_finding:** RELATED_PARTY_REMITTANCE | $8,406.00 refunds vs $8,388.20 residuals | CUST-NSC-01, REF-NSC-*, CUST-009
- **must_not:**
  - Do not merge CUST-NSC-01 into CUST-009.
  - Do not explain TXN-2026-09-015 as a Settlement Co refund (September refund was not sent).

### ADV-CASH-013 — Wire instructions that ask customers for 0.1 percent cover

- **domain:** `cash`
- **stealth:** 4
- **span:** 2025-11 → 2026-09
- **storyline:** `SL-ADV-RESIDUAL`
- **preexisting_state:** Customer portal PDF remit-to (new plant customer_instructions/northstar_wire.pdf) says 'include 0.10 percent correspondent cover on ACH'. Books AR invoices stay at face. The instruction is not in company_policies.json.
- **plant_objects:**
  - `ingestion:customer_instructions/northstar_wire.pdf`
  - `ingestion:customer_instructions/meridian_wire.pdf`
  - `ingestion:customer_instructions/lumen_wire.pdf`
  - `ar_customers:CUST-009`
  - `ar_customers:CUST-010`
  - `ar_customers:CUST-008`
- **how_it_hides:** Cash application uses invoice face. The extra 0.1 percent is 'customer error' in apply-cash notes. No processor fee evidence exists, so it is not FEE_NETTED.
- **detective_path:**
  1. Read the remit-to PDFs. Extract the 0.10 percent sentence.
  2. Confirm company_policies has no such fee.
  3. Confirm Stripe/Adyen are not in the path for these ACH customers.
  4. Tie the instruction author to USR-APPLY-02 or USR-JE-04 in PDF metadata (Nadia).
- **expected_finding:** REMITTANCE_RATE_RESIDUAL | 0.10 percent instruction vs 0 percent policy | northstar_wire.pdf, meridian_wire.pdf, lumen_wire.pdf
- **must_not:**
  - Do not attach this instruction to INV-017 Helios Hardware.
  - Do not call it a bank fee in operational files.

### ADV-AR-013 — Meridian and Lumen ACH at the same 1.001 rate

- **domain:** `ar`
- **stealth:** 4
- **span:** 2025-12 → 2026-09
- **storyline:** `SL-ADV-RESIDUAL`
- **preexisting_state:** CUST-010 Meridian Health and CUST-008 Lumen Labs already exist. Their unlabeled remittance toys (PAY-004, PAY-005) stay. Additional ACH receipts PAY-MER-* and PAY-LUM-* are 1.001 times invoice face.
- **plant_objects:**
  - `ar_payments:PAY-MER-2025-12 through PAY-MER-2026-09`
  - `ar_payments:PAY-LUM-2026-01 through PAY-LUM-2026-09`
  - `ar_invoices:INV-AR-MER-*`
  - `ar_invoices:INV-AR-LUM-*`
- **how_it_hides:** Apply-cash still has the Lumen $5,000 ambiguous pair as a separate toy. The 1.001 receipts are larger ($18k–$62k) and apply cleanly to named invoices, so Apply Bot is green. Residuals hit 1030 or 6950.
- **detective_path:**
  1. Compute bank/invoice for Meridian and Lumen named-invoice ACH.
  2. Exclude PAY-004 $5,000 ambiguous pair from the rate test.
  3. Add residuals to the Northstar series. Combined unplugged September residual is $12.40 + $48.62 + $31.10 = $92.12. Only $12.40 is on the famous TXN.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** REMITTANCE_RATE_RESIDUAL | September extras $48.62 Meridian + $31.10 Lumen plus $12.40 Northstar | PAY-MER-2026-09, PAY-LUM-2026-09, PAY-006
- **must_not:**
  - Do not destroy PAY-004 HUMAN_REVIEW identity in expected_results. Operational status for PAY-004 should become EXCEPTION_OPEN, not stay HUMAN_REVIEW as a Bot output.
  - Do not change Lumen's two $5,000 open invoices.

### ADV-CLOSE-008 — August close plugged, September close not

- **domain:** `close`
- **stealth:** 4
- **span:** 2026-08-31 → 2026-09-20
- **storyline:** `SL-ADV-RESIDUAL`
- **preexisting_state:** August period CLOSED 2026-09-03. JE-REC-PLUG-2026-08 posted 2026-09-02 16:10, still inside August close_timestamp. September has no plug because the CFO sabbatical began 2026-09-08 and Nadia did not run the undocumented step.
- **plant_objects:**
  - `audit/periods:2026-08`
  - `close/journal_entries:JE-REC-PLUG-2026-08`
  - `close/tasks:TASK-CASH`
  - `close/tasks:TASK-FINAL`
- **how_it_hides:** The missing September plug looks like a process miss, which is true. The detective question is why the process existed. Close Bot will block on $12.40 as designed.
- **detective_path:**
  1. Compare August TASK-CASH workpaper to September.
  2. August workpaper includes line 'over/short true-up $7,206.18'. September workpaper has a blank true-up line.
  3. Do not auto-post a September plug. The demo needs the block.
  4. Write the finding as undocumented close step plus residual rate, not as 'forgot a journal'.
- **expected_finding:** RESIDUAL_UNPLUGGED | August plugged $7,206.18, September unplugged $12.40 (and $92.12 population) | JE-REC-PLUG-2026-08 vs missing JE-REC-PLUG-2026-09, TASK-CASH
- **must_not:**
  - Do not close September.
  - Do not mark JE-REC-PLUG-2026-08 as post_close.
- **demo_beat:** Close stays blocked. The beat is the blank true-up line in the September workpaper.

### ADV-RPT-007 — Other income that was never booked on the residuals

- **domain:** `reporting`
- **stealth:** 3
- **span:** 2025-11 → 2026-09
- **storyline:** `SL-ADV-RESIDUAL`
- **preexisting_state:** If 0.1 percent were a customer-paid fee, it would be 4000-Revenue or other income. It never hits P&L. Board pack other-income is $0.00.
- **plant_objects:**
  - `reporting/actuals`
  - `reporting/ledger_seed:4000-Revenue`
  - `gl:6950-Cash-Over-Short`
  - `reporting/budget`
- **how_it_hides:** GM 64→61 remains the loud cost story and is untouched. Residual cash never reaches revenue, so flux analysis on GM does not see it.
- **detective_path:**
  1. Tie bank cash-in to revenue + AR movement + residual parking.
  2. Show $86,418.60 cash-in with no revenue, no AP reduction except VEND-CLR-01.
  3. Do not attribute GM drop to this thread.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** REMITTANCE_RATE_RESIDUAL | $86,418.60 cash-in never in 4000-Revenue | 6950 vs 4000, VEND-CLR-01
- **must_not:**
  - Do not retell TXN-SUP-SEP-001 GM drivers.

### ADV-MIX-003 — Residual thread across cash, close, AP, forecast

- **domain:** `mixed`
- **stealth:** 5
- **span:** 2025-11 → 2026-09
- **storyline:** `SL-ADV-RESIDUAL`
- **preexisting_state:** Same $12.40 is a cash exception, a close blocker, a 6950 throughput story, a VEND-CLR-01 AP vendor, and a 13-week cash forecast that assumes residuals continue as 'other inflow'.
- **plant_objects:**
  - `bank:TXN-2026-09-015`
  - `close/tasks:TASK-CASH`
  - `vendor_master:VEND-CLR-01`
  - `reporting/forecast_lines:FC-OTHER-IN`
  - `gl:6950-Cash-Over-Short`
- **how_it_hides:** Each Bot sees one slice. Forecast FC-OTHER-IN $7,200 per month is the trailing plug, labeled 'lockbox variance mean'. It will miss in September because the plug was not paid and the $12.40 is not $7,200.
- **detective_path:**
  1. Cash: EXCEPTION_OPEN on TXN-2026-09-015.
  2. Close: CLOSE_BLOCKED.
  3. AP: INV-CLR-2026-08 still open.
  4. Story: FC-OTHER-IN week 2026-09-28 misses by ~$7,187.60.
  5. Join on rate 0.001 and VEND-CLR-01.
- **expected_finding:** RESIDUAL_UNPLUGGED | $12.40 visible, $86,418.60 historical, forecast miss ~$7,187.60 | TXN-2026-09-015, TASK-CASH, INV-CLR-2026-08, FC-OTHER-IN
- **must_not:**
  - Do not satisfy the forecast by booking other income.
  - Keep Quiet Harbor INV-AR-014 as a separate forecast-miss driver.
- **demo_beat:** 2-hour sim: four Bots, one rate.

### ADV-AUDIT-008 — Bank rec sample that ties after the plug

- **domain:** `audit`
- **stealth:** 3
- **span:** 2026-08 sample
- **storyline:** `SL-ADV-RESIDUAL`
- **preexisting_state:** August rec sample REC-AUG-PLUG includes the plug JE and the CLR payment. Reperformance PASSes. September sample still includes REC-NS-1240.
- **plant_objects:**
  - `audit/reconciliations:REC-AUG-PLUG`
  - `audit/reconciliations:REC-NS-1240`
  - `gl:JE-REC-PLUG-2026-08`
- **how_it_hides:** Auditor who only re-performs August will bless the plug. The control is 'rec performed', not 'plug explained'.
- **detective_path:**
  1. Reperform REC-AUG-PLUG (arithmetic PASS).
  2. Ask what the plug represents. No support beyond a spreadsheet tab 'NS-MER-LUM 0.1%'.
  3. Carry that tab to September and it predicts $12.40 on Northstar plus Meridian/Lumen extras.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** REC_PLUG_NET_ZERO | August rec PASS with unexplained methodology | REC-AUG-PLUG, REC-NS-1240
- **must_not:**
  - Do not change REC-NS-1240 identity.
  - Do not use expected_result HUMAN_REVIEW as the adversarial reason code.
## SL-ADV-HALYARD — Ghost employee and colliding vendor bank

Insider: Chris Pell failed deprovision; Tomas Halyard is the ghost identity. Span: 2025-04 → 2026-09. Techniques: ghost W-2, vendor with colliding DFI account, terminated employee still paid, 1099 double dip. Cumulative: $146,309.45 W-2 plus $28,800 facilities AP plus $18,400 1099.

### ADV-PAY-001 — Remote warehouse coordinator on the payroll register

- **domain:** `payroll`
- **stealth:** 5
- **span:** 2025-04-14 → 2026-09
- **storyline:** `SL-ADV-HALYARD`
- **preexisting_state:** Densified payroll register includes EMP-8891 Tomas Halyard, title Remote warehouse coordinator — West, start 2025-04-14, biweekly gross $4,180.27. August payroll JE already posted. Headcount report to the board says 2,840. Register distinct EMP IDs: 2,841.
- **plant_objects:**
  - `payroll_register:EMP-8891`
  - `employee_master:EMP-8891`
  - `reporting/payroll:PR-2026-09-25`
  - `gl:JE-PAYROLL-2026-08`
  - `gl:JE-PAYROLL-2026-09`
  - `org_chart:West Warehouse`
- **how_it_hides:** Gross $4,180.27 has cents, not a round $4,000. Withholding, 401k, and medical elections exist. Chris Pell is manager_of_record. The line looks like every other remote warehouse row. $70,000 toy payroll is rescaled; the ghost is a few hundredths of a percent.
- **detective_path:**
  1. Count distinct emp_id on payroll_register vs employee_master.status=active vs badge_access last 90 days.
  2. EMP-8891 has payroll and an employee_master row, but badge_last_seen is null and okta_last_login is null.
  3. Org chart West Warehouse manager seat is vacant since 2025-03-31 (Ava Pell termination).
  4. Sum gross 2025-04-14 through 2026-09-25 = $146,309.45.
- **expected_finding:** GHOST_EMPLOYEE | $146,309.45 gross | EMP-8891, PR-2026-09-25, vacant manager seat West Warehouse
- **must_not:**
  - Do not name the employee 'Test User' or 'Ghost'.
  - Do not use a $50,000 bonus (loud round).
  - Do not leave biweekly payroll at $70,000 for a $372M company. Rescale and keep PR-2026-10-02 as identity.
- **demo_beat:** Board headcount 2,840 vs register 2,841 is the quiet tell.

### ADV-PAY-002 — No badge, no Okta, no laptop asset

- **domain:** `payroll`
- **stealth:** 4
- **span:** 2025-04-14 → 2026-09
- **storyline:** `SL-ADV-HALYARD`
- **preexisting_state:** IT asset register and badge_access are new densify files. EMP-8891 has none. Every other West Warehouse employee has MX-LPT-* and badge CAM-*.
- **plant_objects:**
  - `badge_access:EMP-8891`
  - `it_assets:MX-LPT-*`
  - `fixed_assets:laptop population`
  - `okta_export:EMP-8891`
- **how_it_hides:** Payroll does not join to IT. Close FA rec only looks at FA-DELL-001 and the Lenovo rollout. A missing laptop is not material to PPE.
- **detective_path:**
  1. Left join payroll remote employees to it_assets and badge_access.
  2. EMP-8891 is the only remote warehouse row with both joins empty.
  3. Expense reports for EMP-8891: zero rows.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** GHOST_EMPLOYEE | $0 IT assets, $0 badges, $146,309.45 payroll | EMP-8891
- **must_not:**
  - Do not delete FA-DELL-001.
  - Do not create a fake laptop to make the ghost look real.

### ADV-PAY-003 — Employer taxes remitted on the ghost

- **domain:** `payroll`
- **stealth:** 3
- **span:** 2025-04 → 2026-09
- **storyline:** `SL-ADV-HALYARD`
- **preexisting_state:** 941 deposits include FICA on $4,180.27. The tax payment is real cash out. That makes the ghost expensive and more believable.
- **plant_objects:**
  - `payroll_tax:941-2025-Q2 through 941-2026-Q3`
  - `bank:TXN-941-*`
  - `gl:6200-Benefits`
- **how_it_hides:** Tax rec ties. Auditors who test 941 to payroll totals will pass. The extra $319.79 biweekly employer FICA is inside the tax deposit.
- **detective_path:**
  1. Recompute 941 from the register. It ties, including EMP-8891.
  2. The finding is not a tax break. It is that taxes were paid on an employee with no labor evidence.
  3. Employer FICA extra $11,192.65 across the span.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** GHOST_EMPLOYEE | employer FICA $11,192.65 on top of gross | 941 filings, EMP-8891
- **must_not:**
  - Do not plant a 941 mismatch. The ghost is in the filings on purpose.

### ADV-PAY-004 — Payroll DFI account that matches Halyard Facilities

- **domain:** `payroll`
- **stealth:** 5
- **span:** 2025-04-20 → 2026-09
- **storyline:** `SL-ADV-HALYARD`
- **preexisting_state:** EMP-8891 direct deposit routing 211370545 account ****9022. VEND-HAL-01 Halyard Facilities LLC uses the same DFI account for janitorial AP. Vendor first_seen 2025-04-20, six days after the employee start.
- **plant_objects:**
  - `payroll_direct_deposit:EMP-8891`
  - `vendor_bank:VEND-HAL-01`
  - `ap_invoices:INV-HAL-*`
  - `bank:TXN-HAL-*`
  - `bank:TXN-PAYROLL-*`
- **how_it_hides:** No engine compares payroll DFI accounts to vendor DFI accounts. Both ACH descriptions look normal: PAYROLL MAXIMOR vs HALYARD FACILITIES. Nevada PO box vs 'remote West' employee.
- **detective_path:**
  1. Join payroll_direct_deposit.account_hash to vendor_bank.account_hash.
  2. Hit: EMP-8891 and VEND-HAL-01, routing 211370545, last4 9022.
  3. AP to VEND-HAL-01 $2,400.00 per month x 12 months in span = $28,800.00 (this one is round — monthly janitorial often is. Pair it with the non-round payroll so amount is not the only signal).
  4. Vendor has no insurance cert, no W-9 on file.
- **expected_finding:** PAYROLL_VENDOR_BANK_COLLISION | $146,309.45 payroll + $28,800.00 AP | EMP-8891, VEND-HAL-01, routing 211370545 account ****9022
- **must_not:**
  - Do not rely on unimplemented vendor-bank-change control.
  - The $2,400 round monthly is allowed only because payroll cents exist as the other signal.
- **demo_beat:** Mixed-function beat: payroll Bot and AP Bot both green until the DFI join.

### ADV-PAY-005 — 1099 to the same person as the W-2

- **domain:** `payroll`
- **stealth:** 4
- **span:** 2026-01 → 2026-09
- **storyline:** `SL-ADV-HALYARD`
- **preexisting_state:** Contractor CTR-HALYARD-1099 Tomas Halyard dba Halyard Weekend Coverage, $2,300.00 per month, paid from 5400-Contractors via VEND-HAL-01 extra invoices INV-HAL-WKND-*.
- **plant_objects:**
  - `contractors:CTR-HALYARD-1099`
  - `ap_invoices:INV-HAL-WKND-*`
  - `payroll_register:EMP-8891`
  - `gl:5400-Contractors`
- **how_it_hides:** W-2 and 1099 files are separate. Name match is not a Kernel control. Weekend coverage invoices have packing-slip-like GRs Glen Park rubber-stamps.
- **detective_path:**
  1. Fuzzy-match contractor legal_name to employee legal_name.
  2. SSN last4 on W-4 and W-9 both 4419 (plant W-9). Same last4 as Kestrel bank is coincidence? Use 9022 last4 for Halyard SSN-last4 to avoid cross-storyline collision. Plant TIN last4 9022.
  3. Sum INV-HAL-WKND-* $18,400.00 Jan–Aug plus September open $2,300.00.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** CONTRACTOR_W2_DOUBLE_DIP | $18,400.00 1099 on top of W-2 | CTR-HALYARD-1099, EMP-8891, INV-HAL-WKND-*
- **must_not:**
  - Do not use Dana Kestrel's bank last4 on this person.

### ADV-PAY-006 — Org chart manager seat left empty

- **domain:** `payroll`
- **stealth:** 3
- **span:** 2025-03-31 → 2026-09
- **storyline:** `SL-ADV-HALYARD`
- **preexisting_state:** Ava Pell EMP-2290, warehouse associate, terminated 2026-03-31 (also ADV-PAY-008). Her former manager role 'West Warehouse Coordinator' was the seat Tomas allegedly fills, but org_chart.manager_emp_id for the remaining West staff is null.
- **plant_objects:**
  - `org_chart:West Warehouse`
  - `employee_master:EMP-2290`
  - `employee_master:EMP-8891`
- **how_it_hides:** HRIS allows a vacant manager. Payroll still runs. Headcount reports hide vacancies by showing filled-role titles.
- **detective_path:**
  1. List employees with manager_emp_id pointing at EMP-8891: zero.
  2. List employees who should report to West Warehouse Coordinator: 6 people, manager null.
  3. Tomas has no direct reports and no skip-level.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** GHOST_EMPLOYEE | 0 direct reports, 6 orphans | EMP-8891, org_chart West Warehouse
- **must_not:**
  - Do not fill the manager seat in August books.

### ADV-PAY-007 — October 2 payroll above schedule

- **domain:** `payroll`
- **stealth:** 3
- **span:** 2026-10-02
- **storyline:** `SL-ADV-HALYARD`
- **preexisting_state:** Keep identity PR-2026-10-02 and ACT-PAYROLL-HIGH. Rescale: schedule $8,437,291.44, actual $8,459,612.90. Delta $22,321.46 = ghost $4,180.27 + employer taxes $319.79 + real OT $17,821.40 (documented).
- **plant_objects:**
  - `reporting/payroll:PR-2026-10-02`
  - `reporting/actuals:ACT-PAYROLL-HIGH`
  - `payroll_register:2026-10-02`
- **how_it_hides:** Story Bot can explain the miss as OT, which is partly true. The OT file OT-2026-10-02 supports $17,821.40. The remaining $4,500.06 is EMP-8891 plus FICA, not in the OT file.
- **detective_path:**
  1. Recompute actual vs schedule.
  2. Subtract supported OT $17,821.40.
  3. Remainder $4,500.06 = EMP-8891 $4,180.27 + $319.79 FICA.
  4. Do not let the OT file swallow the ghost.
- **expected_finding:** GHOST_EMPLOYEE | $4,500.06 of PR-2026-10-02 miss after supported OT | PR-2026-10-02, ACT-PAYROLL-HIGH, EMP-8891, OT-2026-10-02
- **must_not:**
  - Keep PR-2026-10-02 as a forecast-miss driver.
  - Do not keep $73,200 vs $70,000 at $372M scale. Rescale, keep IDs.
- **demo_beat:** Story Bot's OT explanation is the trap. Audit Bot peels OT off and the ghost remains.

### ADV-PAY-008 — Terminated warehouse associate still paid

- **domain:** `payroll`
- **stealth:** 4
- **span:** 2026-04-01 → 2026-09
- **storyline:** `SL-ADV-HALYARD`
- **preexisting_state:** Ava Pell EMP-2290 last_day 2026-03-31, status terminated. Payroll register still contains her at $1,842.10 biweekly through 2026-09-25. Distinct from the Tomas ghost. Chris Pell (no relation planted beyond the shared surname — actually make them siblings? Shared surname is a detective join. Plant emergency_contact of Ava = Chris Pell.)
- **plant_objects:**
  - `employee_master:EMP-2290`
  - `payroll_register:EMP-2290`
  - `employee_master:EMP-5510`
  - `badge_access:EMP-2290 last 2026-03-30`
- **how_it_hides:** Failed deprovision is a control miss. Amounts have cents. Status in HRIS is terminated but payroll_feed.include_flag stayed Y. Chris Pell EMP-5510 is payroll admin and Ava's emergency_contact.
- **detective_path:**
  1. Join employee_master.status=terminated to payroll_register.pay_date > last_day.
  2. EMP-2290 hits from PR-2026-04-11 through PR-2026-09-25 = $23,947.30.
  3. Badge stopped 2026-03-30. Okta deactivated 2026-04-02.
  4. Initiator of include_flag is USR-PR-01 Chris Pell.
- **expected_finding:** TERMINATED_EMPLOYEE_PAID | $23,947.30 | EMP-2290, USR-PR-01, last_day 2026-03-31
- **must_not:**
  - Do not collapse Ava and Tomas into one person.
  - Do not make Ava's amount $2,000.00 round.

### ADV-VM-007 — Halyard Facilities janitorial vendor

- **domain:** `vendor-master`
- **stealth:** 3
- **span:** 2025-04-20 → 2026-09
- **storyline:** `SL-ADV-HALYARD`
- **preexisting_state:** VEND-HAL-01 monthly $2,400.00, PO-HAL-STANDING, GR rubber-stamped. Nevada PO box. No workers-comp cert in vendor_contracts.
- **plant_objects:**
  - `vendor_master:VEND-HAL-01`
  - `vendor_contracts:CTR-HAL-01`
  - `ap_invoices:INV-HAL-2025-05 through INV-HAL-2026-09`
  - `purchase_orders:PO-HAL-STANDING`
- **how_it_hides:** Janitorial is expected opex. Round $2,400 is ordinary_recurring under audit policy (ordinary_recurring_max $500 is for round_number divisors of 100 — $2,400 may flag round_number. Keep it and pair with non-round weekend invoices so the vendor is not 'the round-number toy'). Standing PO $28,800 annual approved by Hale in 2025.
- **detective_path:**
  1. Vendor created 6 days after EMP-8891 start.
  2. No insurance certificate.
  3. Same DFI as ADV-PAY-004.
  4. Service location 'West campus' does not exist in facilities_registry (Maximor has Cambridge and a 3PL, not a West campus).
- **expected_finding:** RELATED_PARTY_VENDOR | $28,800.00 standing janitorial | VEND-HAL-01, PO-HAL-STANDING, no West campus in facilities_registry
- **must_not:**
  - Do not set unusual=true.
  - Do not collide with Northwind Phantom.
## SL-ADV-ORBIT — Prepaid that never hits P&L

Insider: Nadia Voss + Orbit Insights Corp. Span: 2025-01 → 2026-09. Techniques: amort posted to BS clearing, expense reversed by net-zero pair, near-name vendor vs Orbit Analytics. Cumulative: $180,000 PRE-SFT-002 still on BS; $96,000 software cap that should expense.

### ADV-PRE-001 — Orbit Insights prepaid that expenses into a balance-sheet account

- **domain:** `prepaid-fa`
- **stealth:** 5
- **span:** 2025-01-06 → 2026-09
- **storyline:** `SL-ADV-ORBIT`
- **preexisting_state:** PRE-SFT-001 Orbit Analytics $24,000 still amortizes correctly to Software Subscription Expense. A second prepaid PRE-SFT-002 Orbit Insights Corp $180,000, 36 months from 2025-01-06, monthly $5,000.00. Monthly amort JE-PRE-OIC-YYYY-MM debits 1220-Prepaid-Other, not expense.
- **plant_objects:**
  - `close/prepaids:PRE-SFT-002`
  - `close/prepaids:PRE-SFT-001`
  - `gl:JE-PRE-OIC-*`
  - `gl:1220-Prepaid-Other`
  - `vendor_master:VEND-OIC-01`
  - `ap_invoices:INV-OIC-2025-01`
- **how_it_hides:** Prepaid schedule remaining_balance declines in the workpaper copy that Close Bot reads, because the workpaper subtracts $5,000. The GL 1220 increases by $5,000 (the 'amort' is capitalized again). PRE-SFT-001 tie still PASSes. TASK-PREPAID can complete if it only inspects listed demo prepaids.
- **detective_path:**
  1. List all prepaid_id, not only PRE-SFT-001 and PRE-INS-001.
  2. For PRE-SFT-002, follow the monthly JE debit account. It is 1220, not Software Subscription Expense.
  3. GL 1220 at Aug 31 = $180,000 original (never declined) + $5,000 * 20 months if the mispost accumulates — plant so original cash $180,000 remains in 1200-Prepaid-Software and 1220 also holds $100,000 of 'amort'. Specify: cash out Jan 2025 $180,000 to 1200. Each month Dr 1220 $5,000 Cr 1200 $5,000. 1200 remaining $80,000 after 20 months looks amortized. 1220 $100,000 is a second asset. P&L expense $0.
  4. P&L software expense includes PRE-SFT-001 $2,000/month only.
- **expected_finding:** PREPAID_AMORT_MISPOSTED | $100,000 parked in 1220 after 20 months; $0 P&L | PRE-SFT-002, JE-PRE-OIC-*, 1220-Prepaid-Other, VEND-OIC-01
- **must_not:**
  - Do not break PRE-SFT-001 or PRE-INS-001 amortization.
  - Do not use $50,000.00 as the prepaid total.
- **demo_beat:** Close Bot amortizes the famous two prepaids. The third prepaid is the hole.

### ADV-PRE-002 — Expense posted then reversed the next day

- **domain:** `prepaid-fa`
- **stealth:** 5
- **span:** 2026-03 → 2026-08
- **storyline:** `SL-ADV-ORBIT`
- **preexisting_state:** Starting March 2026 Nadia also posts JE-PRE-OIC-EXP-YYYY-MM Dr Software Subscription Expense $5,000 Cr 1220, then JE-PRE-OIC-REV-YYYY-MM the next day Dr 1220 Cr 1350-Other-Receivable $5,000. Net P&L zero. 1350 grows $30,000 March–August.
- **plant_objects:**
  - `gl:JE-PRE-OIC-EXP-2026-03 through 2026-08`
  - `gl:JE-PRE-OIC-REV-2026-03 through 2026-08`
  - `gl:1350-Other-Receivable`
- **how_it_hides:** A flux on software expense that only looks at month-end net sees $0 movement from this pair. Pair nets to zero so journal-sample of one side without the other looks like a normal amort.
- **detective_path:**
  1. Find journals that reverse within 48 hours with equal amount and swapped accounts.
  2. Six pairs, $5,000.00 each, poster USR-JE-04, approver USR-NA-VOSS (same person, ADV-AUDIT-005).
  3. 1350-Other-Receivable subledger has no customer, no invoice. Memo 'Orbit implementation recoveries'.
  4. No cash ever collected on 1350.
- **expected_finding:** AMORT_REVERSAL_PAIR | $30,000 moved to 1350 | JE-PRE-OIC-EXP-*, JE-PRE-OIC-REV-*, 1350-Other-Receivable
- **must_not:**
  - Do not net the pair into a single JE (that would hide the detective path).
  - Do not label them post_close.

### ADV-PRE-003 — Expired insurance rider still on the prepaid schedule

- **domain:** `prepaid-fa`
- **stealth:** 3
- **span:** 2026-01-09 → 2026-09
- **storyline:** `SL-ADV-ORBIT`
- **preexisting_state:** PRE-INS-001 Hartford $12,000 remains correct. PRE-INS-RIDER $18,600 to Hartford Brokerage Partners VEND-HBP-01, coverage_end 2026-03-31, still has remaining_balance $9,300 on the September schedule.
- **plant_objects:**
  - `close/prepaids:PRE-INS-RIDER`
  - `vendor_master:VEND-HBP-01`
  - `ap_invoices:INV-HBP-2026-01`
  - `close/prepaids:PRE-INS-001`
- **how_it_hides:** Schedule math ($18,600 / 12 * remaining months) is internally consistent if someone forgot to stop at March. Close Bot that trusts the schedule PASSes.
- **detective_path:**
  1. Compare prepaid.end_date to remaining_balance. PRE-INS-RIDER end_date 2026-03-31 with $9,300 remaining in September is impossible under straight_line.
  2. VEND-HBP-01 is not VEND-011.
  3. No certificate of insurance after 2026-03-31.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** PREPAID_AMORT_MISPOSTED | $9,300 remaining after policy end 2026-03-31 | PRE-INS-RIDER, VEND-HBP-01
- **must_not:**
  - Do not alter PRE-INS-001 dates.

### ADV-PRE-004 — Orbit Insights versus Orbit Analytics

- **domain:** `vendor-master`
- **stealth:** 4
- **span:** 2025-01-06 → 2026-09
- **storyline:** `SL-ADV-ORBIT`
- **preexisting_state:** VEND-012 Orbit Analytics is the real SaaS vendor for PRE-SFT-001. VEND-OIC-01 Orbit Insights Corp shares the word Orbit. Different EIN, different remit, same 'analytics platform' memo style.
- **plant_objects:**
  - `vendor_master:VEND-012`
  - `vendor_master:VEND-OIC-01`
  - `vendor_contracts:CTR-OIC-001`
  - `vendor_contracts:DOC-SFT-2025`
- **how_it_hides:** normalize_vendor does not collapse Insights vs Analytics. Procurement thinks OIC is the implementation partner. $180,000 was paid on INV-OIC-2025-01 with PO-OIC-001 approved by Elena Vasquez as 'capital software'.
- **detective_path:**
  1. Compare contracts: Orbit Analytics is a $24,000 SaaS. Orbit Insights claims a 36-month platform plus implementation.
  2. Website and W-9 for VEND-OIC-01 use a WeWork Boston mailbox.
  3. PO-OIC-001 description equals Orbit Analytics SKU names from INV-020.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** NEAR_DUPLICATE_VENDOR | $180,000 | VEND-OIC-01 vs VEND-012, PO-OIC-001, INV-OIC-2025-01
- **must_not:**
  - Do not alias VEND-OIC-01 to VEND-012 in prior_cases.json.

### ADV-PRE-005 — Prepaid tie-out that only lists the two demo items

- **domain:** `close`
- **stealth:** 3
- **span:** 2026-09
- **storyline:** `SL-ADV-ORBIT`
- **preexisting_state:** TASK-PREPAID workpaper copies PRE-SFT-001 and PRE-INS-001. GL 1200+1210+1220 does not equal that workpaper once densified.
- **plant_objects:**
  - `close/tasks:TASK-PREPAID`
  - `close/prepaids`
  - `gl:1200-Prepaid-Software`
  - `gl:1210-Prepaid-Insurance`
  - `gl:1220-Prepaid-Other`
- **how_it_hides:** If Close Bot uses the planted schedule file as both sides of the rec, it ties. The detective rec is GL vs schedule vs cash.
- **detective_path:**
  1. Sum GL prepaid accounts.
  2. Sum close/prepaids remaining_balance including PRE-SFT-002 and PRE-INS-RIDER.
  3. Difference is the 1350 diversion plus any 1220 parked amort.
  4. Do not mark TASK-PREPAID complete without the GL join.
- **expected_finding:** PREPAID_AMORT_MISPOSTED | GL prepaid accounts exceed demo schedule by $189,300.00 | TASK-PREPAID, PRE-SFT-002, PRE-INS-RIDER, 1220, 1350
- **must_not:**
  - Do not let TASK-PREPAID complete in the adversarial pack without this rec.

### ADV-PRE-006 — Hartford Brokerage Partners rider invoice

- **domain:** `ap`
- **stealth:** 2
- **span:** 2026-01-09
- **storyline:** `SL-ADV-ORBIT`
- **preexisting_state:** INV-HBP-2026-01 $18,600.00 paid January 2026. Vendor name contains Hartford, so AP clerks coded it as insurance. Not the real Hartford Insurance VEND-011.
- **plant_objects:**
  - `ap_invoices:INV-HBP-2026-01`
  - `vendor_master:VEND-HBP-01`
  - `vendor_master:VEND-011`
  - `bank:TXN-HBP-2026-01`
- **how_it_hides:** String contains Hartford. Chart of account 1210. Three-way match against PO-HBP-001 'insurance rider'. Looks like PRE-INS-001's cousin.
- **detective_path:**
  1. Compare remit EIN to VEND-011. Different.
  2. Bank counterparty HARTFORD BROKERAGE PARTNERS not HARTFORD INS.
  3. No policy number that the real Hartford recognizes in source_documents.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** NEAR_DUPLICATE_VENDOR | $18,600.00 | VEND-HBP-01 vs VEND-011, INV-HBP-2026-01
- **must_not:**
  - Do not duplicate INV-019.

### ADV-CLOSE-003 — Prepaid task green on the famous two items

- **domain:** `close`
- **stealth:** 4
- **span:** 2026-09
- **storyline:** `SL-ADV-ORBIT`
- **preexisting_state:** Existing TASK-PREPAID may sit NEEDS_REVIEW. Adversarial densify must not let a Bot close prepaid by ticking PRE-SFT-001 and PRE-INS-001 only.
- **plant_objects:**
  - `close/tasks:TASK-PREPAID`
  - `close/prepaids:PRE-SFT-001`
  - `close/prepaids:PRE-INS-001`
  - `close/prepaids:PRE-SFT-002`
- **how_it_hides:** Demo design already uses two prepaids as the happy path. Extra prepaids hide behind that habit.
- **detective_path:**
  1. Complete the famous two amortizations (they should still work).
  2. Require a GL roll-forward of all 12x accounts.
  3. Block TASK-PREPAID on 1220 unexplained $100,000 and 1350 $30,000.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** PREPAID_AMORT_MISPOSTED | TASK-PREPAID blocked on 1220/1350, not on PRE-SFT-001 | TASK-PREPAID, 1220, 1350
- **must_not:**
  - Do not break Orbit Analytics PRE-SFT-001.
  - Do not use CLOSE_BLOCKED only on the $12.40. Prepaid is a second honest block.

### ADV-FA-004 — Implementation cost capitalized that should be expense

- **domain:** `prepaid-fa`
- **stealth:** 4
- **span:** 2025-01-06 → 2026-09
- **storyline:** `SL-ADV-ORBIT`
- **preexisting_state:** FA-OIC-IMPL $96,000.00, useful_life 36 months, same vendor VEND-OIC-01, same invoice split: $180,000 prepaid + $96,000 'capital implementation'. Dell FA-DELL-001 remains the clean hardware path.
- **plant_objects:**
  - `close/fixed_assets:FA-OIC-IMPL`
  - `ap_invoices:INV-OIC-2025-01`
  - `gl:JE-FA-OIC-*`
  - `close/fixed_assets:FA-DELL-001`
- **how_it_hides:** Capitalization of implementation is a judgment. The hide is that the 'asset' has no serial, no in-service ticket, and depreciation hits 1220-adjacent clearing in two months (Nadia). Remaining months hit Depreciation Expense, which looks conservative.
- **detective_path:**
  1. Split INV-OIC-2025-01 $276,000 = $180,000 PRE-SFT-002 + $96,000 FA-OIC-IMPL.
  2. No IT ticket, no serial, placed_in_service_date = invoice date.
  3. Depreciation $2,666.67/month. After 20 months $53,333.40 expense — the only Orbit amount that ever hit P&L, and it is below the line in opex not COGS.
  4. Keep FA-DELL-001 depreciation as the clean demo.
- **expected_finding:** CAPITALIZED_UNRECEIVED | $96,000 implementation with no serial | FA-OIC-IMPL, INV-OIC-2025-01, FA-DELL-001 untouched
- **must_not:**
  - Do not alter INV-018 / FA-DELL-001.

### ADV-RPT-006 — EBITDA addback named non-recurring implementation

- **domain:** `reporting`
- **stealth:** 3
- **span:** 2026-08 board pack → 2026-09
- **storyline:** `SL-ADV-ORBIT`
- **preexisting_state:** Board pack already needs densify. Plant an addback 'non-recurring Orbit implementation $5,000' each month equal to the amort that never hit P&L. Double non-recognition: not in P&L, then added back anyway from a shadow schedule.
- **plant_objects:**
  - `reporting/board_pack:EBITDA_addbacks`
  - `reporting/actuals`
  - `close/prepaids:PRE-SFT-002`
- **how_it_hides:** Story Bot that trusts the addback file will raise EBITDA. Ledger has no corresponding expense to add back.
- **detective_path:**
  1. Recompute EBITDA from GL.
  2. Addbacks that have no GL expense are the finding ($5,000 x 8 months in FY2026 YTD = $40,000).
  3. Do not use the loud GM 3-point story as this addback.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** PREPAID_AMORT_MISPOSTED | $40,000 FYTD addback with no GL expense | board_pack EBITDA_addbacks, PRE-SFT-002
- **must_not:**
  - Do not put the addback into expected_results gross_margin_drivers.
## SL-ADV-LAPPING — AR lapping under late-payer cover

Insider: Samir Okonkwo EMP-3304. Span: 2025-12 → 2026-09. Techniques: apply A remittance to B invoice, park unapplied cash, Quiet Harbor lateness as cover. Cumulative: $412,880.00 misapplied stock; bank totals still tie.

### ADV-AR-001 — Cash applications that follow a chain

- **domain:** `ar`
- **stealth:** 5
- **span:** 2025-12 → 2026-09
- **storyline:** `SL-ADV-LAPPING`
- **preexisting_state:** Samir Okonkwo USR-APPLY-02 applies customer cash. Quiet Harbor CUST-005 is already chronic_late. Helios Analytics CUST-002 is already late_payer. Pinnacle CUST-006 is already partial. Those behaviors are the cover. A chain starts 2025-12-18: Quiet Harbor cash applied to Helios invoices, Helios cash to Pinnacle, Pinnacle cash back to Quiet Harbor.
- **plant_objects:**
  - `ar_payments:PAY-LAP-*`
  - `ar_invoices:INV-AR-QH-*`
  - `ar_invoices:INV-AR-HE-*`
  - `ar_invoices:INV-AR-PIN-*`
  - `ar_precedents`
  - `employee_master:EMP-3304`
- **how_it_hides:** Bank deposits equal AR cash batches, so cash recon of AR is MATCHED. Aging looks healthier than customer behavior would imply because applications keep invoices out of 90+.
- **detective_path:**
  1. For each PAY-LAP-*, compare remittance.named_invoice_id to application.invoice_id.
  2. Build a directed graph of (payer_customer -> applied_customer). A 3-cycle QH→Helios→Pinnacle→QH appears every month.
  3. All applications after 18:00 local Friday are USR-APPLY-02.
  4. Stock in the chain at 2026-09-20 is $412,880.00.
- **expected_finding:** AR_LAPPING | $412,880.00 misapplied stock | PAY-LAP-*, USR-APPLY-02, CUST-005, CUST-002, CUST-006
- **must_not:**
  - Do not break INV-AR-007 exact payment or PAY-001.
  - Do not use HUMAN_REVIEW as the apply status. Use EXCEPTION_OPEN when remittance and application disagree.
  - Keep Quiet Harbor as collections candidate.
- **demo_beat:** Apply Bot is proud of a clean aging. Audit Bot reads remittance text.

### ADV-AR-002 — Remittance text that names a different invoice

- **domain:** `ar`
- **stealth:** 4
- **span:** 2026-01 → 2026-09
- **storyline:** `SL-ADV-LAPPING`
- **preexisting_state:** PAY-LAP-2026-09-12 $88,400.00 from Helios Analytics. Remittance body 'apply to INV-AR-HE-4412'. Applied to INV-AR-PIN-2208 Pinnacle. Amount equals PIN invoice, not HE invoice ($91,200.00).
- **plant_objects:**
  - `ar_payments:PAY-LAP-2026-09-12`
  - `ingestion:remittance/PAY-LAP-2026-09-12.txt`
  - `ar_invoices:INV-AR-HE-4412`
  - `ar_invoices:INV-AR-PIN-2208`
- **how_it_hides:** Unlabeled remittance toy is PAY-004 two equal $5,000s. This remittance is labeled, so Apply Bot that trusts the application row over the text will skip it. Amount equals a different customer's invoice, which looks like a perfect match if customer_id is ignored.
- **detective_path:**
  1. Parse remittance text first.
  2. Compare named invoice customer to bank counterparty HELIOS ANALYTICS.
  3. INV-AR-HE-4412 remains open $91,200.00. INV-AR-PIN-2208 closed.
  4. USR-APPLY-02 note: 'amount match PIN-2208'.
- **expected_finding:** AR_LAPPING | $88,400.00 | PAY-LAP-2026-09-12, INV-AR-HE-4412 left open, INV-AR-PIN-2208 closed
- **must_not:**
  - Do not convert this into the PAY-004 ambiguous $5,000 case.

### ADV-AR-003 — Unapplied cash parked then reused

- **domain:** `ar`
- **stealth:** 4
- **span:** 2026-04-03 → 2026-09
- **storyline:** `SL-ADV-LAPPING`
- **preexisting_state:** Account 1110-AR-Unapplied holds $36,208.40 from Quiet Harbor overpayments. Samir draws from it to complete later applications when a chain would otherwise break.
- **plant_objects:**
  - `gl:1110-AR-Unapplied`
  - `ar_payments:PAY-UNAPP-*`
  - `ar_ledger:unapplied_subledger`
- **how_it_hides:** Overpayment path is PARTIALLY_IMPLEMENTED in Kernel. Densify must still show 1110 activity from registers. Forecast may ignore unapplied.
- **detective_path:**
  1. Roll forward 1110 by customer.
  2. Quiet Harbor unapplied in $62,000, out $25,791.60 to Helios invoices.
  3. Ending 1110 $36,208.40 is all CUST-005.
  4. No credit memo issued (credit-memo lifecycle is partial; plant the open unapplied, do not require a refund cycle).
- **expected_finding:** UNAPPLIED_CASH_PARK | $36,208.40 ending; $25,791.60 reused | 1110-AR-Unapplied, CUST-005, PAY-UNAPP-*
- **must_not:**
  - Do not require a full credit-memo engine.
  - Do not settle PAY-007 overpay toy as this story.

### ADV-AR-004 — Aging that looks current because of the chain

- **domain:** `ar`
- **stealth:** 3
- **span:** 2026-09-20
- **storyline:** `SL-ADV-LAPPING`
- **preexisting_state:** Quiet Harbor risk_flag collections remains. Its aging however shows only $18,400 in 1-30 and $0 in 90+ after lapping. Helios shows current. Pinnacle shows partial as designed.
- **plant_objects:**
  - `ar_invoices aging snapshot 2026-09-20`
  - `ar_customers:CUST-005`
  - `reporting/balances ar`
- **how_it_hides:** Collections Bot that trusts aging will deprioritize Quiet Harbor. The customer is still late; the applications are not theirs.
- **detective_path:**
  1. Rebuild aging from invoice_date and cash with remittance-faithful applications.
  2. Faithful aging: Quiet Harbor $188,400 in 90+.
  3. Posted aging: $18,400 in 1-30.
  4. Delta $170,000 is lapping cover.
- **expected_finding:** AR_LAPPING | aging understates Quiet Harbor 90+ by $170,000.00 | CUST-005 aging snapshot vs remittance-faithful rebuild
- **must_not:**
  - Keep CUST-005 risk_flag collections.
  - Do not make INV-AR-005 the only Quiet Harbor invoice. Densify.

### ADV-AR-005 — Friday after-hours applications

- **domain:** `ar`
- **stealth:** 3
- **span:** 2025-12 → 2026-09
- **storyline:** `SL-ADV-LAPPING`
- **preexisting_state:** USR-APPLY-02 posts 38 of 41 lapping applications between Friday 18:12 and 19:04 ET. Other appliers stop at 17:30.
- **plant_objects:**
  - `ar_payments.applied_at`
  - `employee_master:EMP-3304`
  - `harness traces if present, else ledger timestamps`
- **how_it_hides:** Time of day is not a control. Volume on Friday is explained as 'week-end catch-up'.
- **detective_path:**
  1. Histogram applied_at by weekday and hour.
  2. Join those rows to remittance mismatches from ADV-AR-002.
  3. EMP-3304 badge_access on those Fridays: often already exited CAM-4 at 17:10 (VPN from home, which is allowed).
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** AR_LAPPING | 38 Friday 18:12–19:04 applications | USR-APPLY-02 timestamps
- **must_not:**
  - Do not treat after-hours as sufficient alone. Pair with remittance mismatch.

### ADV-AR-006 — Quiet Harbor late collection used as cover

- **domain:** `ar`
- **stealth:** 4
- **span:** 2026-10-09 vs applications in September
- **storyline:** `SL-ADV-LAPPING`
- **preexisting_state:** Keep INV-AR-014 and BNK-AR-FC-001 and ACT-DELAY-AR. The October 9 bank deposit is real. September applications already used a $25,000 Quiet Harbor cash as if it had arrived, applied to Helios. October cash then applies to a Pinnacle invoice.
- **plant_objects:**
  - `ar_invoices:INV-AR-014`
  - `reporting/actuals:ACT-DELAY-AR`
  - `bank:BNK-AR-FC-001`
  - `ar_payments:PAY-LAP-QH-SEP-PRE`
  - `ar_payments:PAY-014-OCT`
- **how_it_hides:** Forecast miss 'paid one week late' remains true at the bank. The hide is that September books already spent the cash in the lapping chain.
- **detective_path:**
  1. Keep the forecast miss identity.
  2. Show PAY-LAP-QH-SEP-PRE $25,000 applied 2026-09-22 with remittance 'expected QH INV-AR-014'.
  3. BNK-AR-FC-001 lands 2026-10-09 and is applied to INV-AR-PIN-2210.
  4. INV-AR-014 may show paid from the September application. Bank date disagrees.
- **expected_finding:** AR_LAPPING | $25,000.00 INV-AR-014 timing vs application | INV-AR-014, BNK-AR-FC-001, PAY-LAP-QH-SEP-PRE, PAY-014-OCT
- **must_not:**
  - Do not delete the late-customer forecast miss.
  - Do not apply October cash to INV-AR-014 if the September fake application already closed it — that is the tell.
- **demo_beat:** Story Bot says Quiet Harbor paid late. Cash Bot says the October money went to Pinnacle.

### ADV-AR-007 — Credit memo that patches a hole in the chain

- **domain:** `ar`
- **stealth:** 4
- **span:** 2026-08-28
- **storyline:** `SL-ADV-LAPPING`
- **preexisting_state:** CM-HE-088 $12,640.00 to Helios Analytics, reason 'billing adjustment'. It zeros INV-AR-HE-4390, which was the invoice that would have aged out when the chain skipped a week in August.
- **plant_objects:**
  - `ar_credit_memos:CM-HE-088`
  - `ar_invoices:INV-AR-HE-4390`
  - `gl:4100-Contra-Revenue-Returns`
- **how_it_hides:** Credit-memo lifecycle is PARTIALLY_IMPLEMENTED. Plant the memo and the GL hit as registers. Do not require a refund engine. Amount is not round. Helios is a chronic late payer, so credits look commercial.
- **detective_path:**
  1. Match CM-HE-088 to INV-AR-HE-4390. No shipping return, no ticket.
  2. Date is the Friday the lapping chain skipped (Samir PTO 2026-08-21–2026-08-27).
  3. Approver USR-APPLY-02 on his own credit (SOD).
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** AR_LAPPING | $12,640.00 credit with no return | CM-HE-088, INV-AR-HE-4390, USR-APPLY-02
- **must_not:**
  - Do not require full credit-memo settlement.
  - Do not name fraud on the credit memo.

### ADV-CASH-003 — AR bank batches that still match in total

- **domain:** `cash`
- **stealth:** 4
- **span:** 2025-12 → 2026-09
- **storyline:** `SL-ADV-LAPPING`
- **preexisting_state:** Daily AR lockbox batches BATCH-AR-YYYY-MM-DD tie to bank deposits. Cash Bot MATCHES them. Application quality is out of scope for the batch rec.
- **plant_objects:**
  - `bank:BATCH-AR-*`
  - `cash_recon/ledger AR cash`
  - `ar_payments:PAY-LAP-*`
- **how_it_hides:** One payment covering three invoices is a happy-path Kernel story (Northline AP side). Here one deposit covering three customers is also happy-path if the Bot only sums.
- **detective_path:**
  1. Reperform batch rec (PASS on amounts).
  2. Explode batch to remittance-level customer vs application-level customer.
  3. Mismatch count 41, dollars $412,880 stock.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** AR_LAPPING | batch MATCHED, exploded mismatch $412,880.00 | BATCH-AR-*, PAY-LAP-*
- **must_not:**
  - Do not fail TXN-2026-09-008 Northline grouped AP match.
  - Do not use GROUPED_MATCH as a success on these AR batches without the explode step.

### ADV-RPT-002 — Forecast collections that use application dates

- **domain:** `reporting`
- **stealth:** 4
- **span:** 2026-09 13-week
- **storyline:** `SL-ADV-LAPPING`
- **preexisting_state:** 13-week forecast uses AR open items and historical apply dates. Lapping makes apply dates look on-time. Bank dates do not.
- **plant_objects:**
  - `reporting/forecast_weeks`
  - `reporting/forecast_lines AR`
  - `ar_payments.applied_at vs bank.date`
- **how_it_hides:** Quiet Harbor miss remains one planted miss. The stealth is systematic optimism of ~$90k per week for Helios/Pinnacle collections that are actually recycled cash.
- **detective_path:**
  1. Rebuild forecast using bank dates and remittance-faithful open items.
  2. Week of 2026-09-21 AR inflow forecast $1,840,000 vs remittance-faithful $1,748,200.
  3. Delta $91,800 is lapping air.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** FORECAST_BIAS_FROM_AR | $91,800.00 week of 2026-09-21 | forecast_lines AR vs remittance-faithful rebuild
- **must_not:**
  - Keep INV-AR-014 as an additional miss, not the only one.

### ADV-MIX-006 — Lapping across apply, cash, forecast, audit

- **domain:** `mixed`
- **stealth:** 5
- **span:** 2025-12 → 2026-09
- **storyline:** `SL-ADV-LAPPING`
- **preexisting_state:** Apply Bot green, Cash Bot batch-matched, Story Bot forecast slightly optimistic, Audit sample of PAY-001 (clean) and PAY-004 (ambiguous toy) never hits PAY-LAP-*.
- **plant_objects:**
  - `ar_payments:PAY-LAP-*`
  - `bank:BATCH-AR-*`
  - `reporting/forecast_lines`
  - `audit/payments sample`
- **how_it_hides:** Audit sampling by dollar may pick large clean Northwind receipts. Lapping lives in the $80k–$90k band.
- **detective_path:**
  1. Force a directed sample of USR-APPLY-02 Friday applications.
  2. Explode one September batch.
  3. Show forecast air $91,800.
  4. Leave PAY-001 clean.
- **expected_finding:** AR_LAPPING | function-green, population $412,880.00 | PAY-LAP-*, BATCH-AR-2026-09-12, forecast week 2026-09-21
- **must_not:**
  - Do not dirty PAY-001 / INV-AR-007.
- **demo_beat:** 2-hour sim: aging is a lie; remittance text is not.
## SL-ADV-PINNACLE — Bill-and-hold and revenue cutoff

Insider: Mei Stratton EMP-1190. Span: 2026-06 → 2026-09. Techniques: September 29 bill-and-hold, 90-day return side letter, cutoff JE 23:47 Sep 30. Cumulative: $2,400,000 Pinnacle plus $1,180,000 Atlas pulled into September.

### ADV-AR-008 — Pinnacle bill-and-hold dated September 29

- **domain:** `ar`
- **stealth:** 5
- **span:** 2026-09-29 → 2026-09-30
- **storyline:** `SL-ADV-PINNACLE`
- **preexisting_state:** INV-AR-PIN-BH-01 $2,400,000.00 to Pinnacle Retail CUST-006, invoice_date 2026-09-29, terms net 90, ship_to CAM-WH-01 (Maximor's own warehouse). Revenue 4000 $2,400,000. Inventory relieved $1,104,000.
- **plant_objects:**
  - `ar_invoices:INV-AR-PIN-BH-01`
  - `inventory:CAM-WH-01 bins PIN-BH-*`
  - `gl:4000-Revenue`
  - `gl:1400-Inventory`
  - `gl:5200-Supplier`
  - `warehouse_locations:CAM-WH-01`
- **how_it_hides:** Invoice exists, customer exists, quantity matches a warehouse transfer ticket WT-BH-01 that 'moved' goods to a bill-and-hold cage still on Maximor premises. Three-way for AR is not a Kernel AP control. Cash is not due until December.
- **detective_path:**
  1. Read ship_to. It is CAM-WH-01, not a Pinnacle DC.
  2. Cycle count 2026-09-30 still counts PIN-BH SKUs in CAM-WH-01.
  3. Side letter SL-PIN-2026-09-28 grants 90-day right of return (ADV-AR-009).
  4. Revenue cut-off test: FOB destination, not yet delivered.
- **expected_finding:** BILL_AND_HOLD | $2,400,000.00 revenue; $1,104,000.00 COGS | INV-AR-PIN-BH-01, WT-BH-01, CAM-WH-01, CUST-006
- **must_not:**
  - Do not explain the loud GM drop with this. This would improve GM. Keep TXN-SUP-SEP-001 as the cost story.
  - Do not collect cash in September on this invoice.
- **demo_beat:** Story Bot can brag about September revenue. Warehouse still has the goods.

### ADV-AR-009 — Pinnacle side letter with a 90-day return right

- **domain:** `ar`
- **stealth:** 4
- **span:** 2026-09-28
- **storyline:** `SL-ADV-PINNACLE`
- **preexisting_state:** Document DOC-SL-PIN-2026-09-28 in close/source_documents, not labeled side_letter. Title 'Pinnacle Q3 fulfillment schedule'. Paragraph 4 is the return right.
- **plant_objects:**
  - `close/source_documents:DOC-SL-PIN-2026-09-28`
  - `ar_invoices:INV-AR-PIN-BH-01`
  - `company_policies revenue recognition (new plant P-REV-001)`
- **how_it_hides:** If Bots only read invoice terms net 90, they miss paragraph 4. Policy P-REV-001 (plant) forbids revenue when a unilateral return right remains.
- **detective_path:**
  1. Parse DOC-SL-PIN-2026-09-28 paragraph 4.
  2. Compare to P-REV-001.
  3. Hold revenue $2,400,000 until delivery or until the return right lapses.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** CHANNEL_STUFFING | $2,400,000.00 | DOC-SL-PIN-2026-09-28 para 4, P-REV-001, INV-AR-PIN-BH-01
- **must_not:**
  - Do not put the word fraud in the document title.
  - Do not hide the PDF from close/source_documents (it must be discoverable).

### ADV-AR-010 — Atlas Robotics pull-forward

- **domain:** `ar`
- **stealth:** 4
- **span:** 2026-09-30
- **storyline:** `SL-ADV-PINNACLE`
- **preexisting_state:** INV-AR-ATL-PF-01 $1,180,000.00 Atlas Robotics CUST-007, invoice 2026-09-30 21:10, delivery promised 2026-10-12. Atlas is a batch_payer, so a large invoice does not look odd.
- **plant_objects:**
  - `ar_invoices:INV-AR-ATL-PF-01`
  - `gl:JE-REV-ATL-PF-01`
  - `purchase_orders customer-side:PO-ATL-8841 dated 2026-10-02 (after invoice)`
- **how_it_hides:** Customer PO date is after the invoice date. Kernel AP three-way is vendor-side. AR has no PO-match engine, so the invoice posts.
- **detective_path:**
  1. Compare invoice_date to customer PO date.
  2. PO-ATL-8841 created 2026-10-02 for the same SKUs.
  3. Shipping system has no ASN until 2026-10-12.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** REVENUE_CUTOFF | $1,180,000.00 | INV-AR-ATL-PF-01, PO-ATL-8841, ASN missing at Sep 30
- **must_not:**
  - Do not dirty Atlas batch payment PAY-003 identities if they remain. Densify additional invoices instead.

### ADV-AR-011 — Goods still in the Cambridge warehouse

- **domain:** `ar`
- **stealth:** 4
- **span:** 2026-09-30
- **storyline:** `SL-ADV-PINNACLE`
- **preexisting_state:** Inventory subledger still holds PIN-BH and ATL-PF SKUs at CAM-WH-01. COGS was already relieved on the invoices.
- **plant_objects:**
  - `inventory:1400-Inventory`
  - `cycle_counts:CC-CAM-WH-01-2026-09-30`
  - `gl:5200-Supplier`
- **how_it_hides:** Inventory rec may use a perpetual that already relieved COGS, so GL 1400 declined. Floor count did not. If Close Bot recs GL to perpetual, PASS. If it recs GL to floor, FAIL.
- **detective_path:**
  1. Cycle count units vs perpetual units for PIN-BH and ATL-PF.
  2. Floor > perpetual by $1,104,000 + $507,400 = $1,611,400 at cost.
  3. That is the COGS relieved too early.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** BILL_AND_HOLD | floor over perpetual $1,611,400.00 at cost | CC-CAM-WH-01-2026-09-30, INV-AR-PIN-BH-01, INV-AR-ATL-PF-01
- **must_not:**
  - Do not force inventory rec to use only the perpetual.

### ADV-AR-012 — October return window already reserved in email

- **domain:** `ar`
- **stealth:** 5
- **span:** 2026-09-30 email, returns 2026-10-18
- **storyline:** `SL-ADV-PINNACLE`
- **preexisting_state:** Inbox fixture MSG-PIN-HOLD-01 from Pinnacle (new spec, simulated) says 'we will keep Q3 product on your floor until we see holiday sell-through'. later_invoices.json analog for AR: CM-PIN-OCT-01 dated 2026-10-18 $2,400,000 in October context only.
- **plant_objects:**
  - `inbox:MSG-PIN-HOLD-01`
  - `later_ar:CM-PIN-OCT-01`
  - `ar_invoices:INV-AR-PIN-BH-01`
- **how_it_hides:** September books do not contain the October credit. A Bot that only reads September can still read the email and the side letter.
- **detective_path:**
  1. Classify MSG-PIN-HOLD-01 as customer correspondence, not a vendor bill.
  2. Join to INV-AR-PIN-BH-01.
  3. Do not wait for October to write the finding. Cut-off is a September issue.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** CHANNEL_STUFFING | $2,400,000.00 at risk of October credit | MSG-PIN-HOLD-01, CM-PIN-OCT-01 (October context), INV-AR-PIN-BH-01
- **must_not:**
  - Do not seed the October credit into September GL.
  - Do not require live email. Simulated inbox only.
- **demo_beat:** 10-minute: Email Bot files a customer note. Revenue accountant Bot should have held the invoice.

### ADV-CLOSE-004 — Revenue journal at 23:47 on September 30

- **domain:** `close`
- **stealth:** 4
- **span:** 2026-09-30
- **storyline:** `SL-ADV-PINNACLE`
- **preexisting_state:** JE-REV-CUTOFF-01 $2,400,000 and JE-REV-CUTOFF-02 $1,180,000 posted 2026-09-30T23:47:00Z by USR-REV-05 Mei Stratton. post_close=false. Period still open.
- **plant_objects:**
  - `canonical/journal_entries:JE-REV-CUTOFF-01`
  - `canonical/journal_entries:JE-REV-CUTOFF-02`
  - `close/journal_entries`
  - `employee_master:EMP-1190`
- **how_it_hides:** Not the loud JE-POST-CLOSE-001. Effective_date and posting_date are both September 30. Time of day is the tell with the bill-and-hold docs.
- **detective_path:**
  1. List September revenue JEs after 20:00.
  2. Join to INV-AR-PIN-BH-01 and INV-AR-ATL-PF-01.
  3. Approver USR-REV-05 equals preparer EMP-1190 mapped via ADV-AUDIT-005 style alias? Mei uses one ID. Approver is USR-JE-02 (the usual rubber stamp).
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** REVENUE_CUTOFF | $3,580,000.00 | JE-REV-CUTOFF-01, JE-REV-CUTOFF-02, 2026-09-30T23:47:00Z
- **must_not:**
  - Do not set post_close=true.
  - Do not reuse JE-POST-CLOSE-001.

### ADV-RPT-003 — Product GM up while company GM down

- **domain:** `reporting`
- **stealth:** 3
- **span:** 2026-09 vs 2026-08
- **storyline:** `SL-ADV-PINNACLE`
- **preexisting_state:** Company GM still 64%→61% from the loud cost drivers. SKU family PIN-BH shows 54% GM on $2.4M that should not be in September. Without it, company GM would be worse. The stuffing masks part of the real cost hit.
- **plant_objects:**
  - `reporting/actuals product GM`
  - `gross_margin_drivers remaining TXN-SUP-SEP-001 etc.`
  - `ar_invoices:INV-AR-PIN-BH-01`
- **how_it_hides:** A Bot that stops at 'GM dropped 3 points, here are the cost txs' misses that revenue mix is also wrong.
- **detective_path:**
  1. Recompute Sep GM excluding INV-AR-PIN-BH-01 and INV-AR-ATL-PF-01.
  2. Company GM would be ~58.4% not 61%. The stuffing hid ~2.6 points.
  3. Keep the cost drivers. Add the revenue overlay as a second story.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** CHANNEL_STUFFING | stuffed revenue hid ~2.6 GM points | INV-AR-PIN-BH-01, INV-AR-ATL-PF-01, vs TXN-SUP-SEP-001 cost story
- **must_not:**
  - Do not replace TXN-SUP-SEP-001. Both stories coexist.
- **demo_beat:** Judge hears two GM stories: costs went up, and stuffed revenue hid how far.

### ADV-RPT-008 — Thirteen-week forecast counts Pinnacle cash in week 3

- **domain:** `reporting`
- **stealth:** 4
- **span:** 2026-09-14 → 2026-12-07
- **storyline:** `SL-ADV-PINNACLE`
- **preexisting_state:** Forecast week 2026-10-05 includes $2,400,000 Pinnacle. Terms are net 90 and the side letter makes cash doubtful.
- **plant_objects:**
  - `reporting/forecast_weeks:2026-10-05`
  - `reporting/forecast_lines:FC-PIN-BH`
  - `ar_invoices:INV-AR-PIN-BH-01`
- **how_it_hides:** Engine that uses invoice due_date net 90 would place cash in December. Someone overrode FC-PIN-BH to week 3 with memo 'strategic customer deposit expected'.
- **detective_path:**
  1. Compare due_date 2026-12-28 to forecast week 2026-10-05.
  2. Override user USR-REV-05.
  3. This miss will not wait until week 3 of the live demo if the Bot rebuilds from terms.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** FORECAST_BIAS_FROM_AR | $2,400,000.00 in week 2026-10-05 vs due 2026-12-28 | FC-PIN-BH, INV-AR-PIN-BH-01
- **must_not:**
  - Keep the 13 week dates in SCN-REPORT-003.
## SL-ADV-PROCESSOR — Processor fee overstatement

Insider: Luis Redmond EMP-4402. Span: 2025-10 → 2026-09. Techniques: book 3.41 percent vs contract 2.9 percent + $0.30, connected account acct_1MaximorProc, payout still equals bank. Cumulative: $214,660.18 fee delta plus $18,440 dispute-win retention.

### ADV-PROC-001 — Booked processor rate versus contract rate

- **domain:** `processor`
- **stealth:** 5
- **span:** 2025-10 → 2026-09
- **storyline:** `SL-ADV-PROCESSOR`
- **preexisting_state:** vendor_contracts CTR-STRIPE-001 2.90 percent + $0.30. GL 6600-Processor-Fees books a blended 3.41 percent on charge gross. Stripe sim payouts still equal bank deposits. po_1MaximorFees identity remains.
- **plant_objects:**
  - `vendor_contracts:CTR-STRIPE-001`
  - `integrations/stripe/charges`
  - `integrations/stripe/balance_transactions`
  - `gl:6600-Processor-Fees`
  - `integrations/stripe/payouts:po_1MaximorFees`
- **how_it_hides:** Cash recon of payout to bank PASSes (PROVIDER_PAYOUT). Fee rec that trusts Stripe fee lines also PASSes. The hide is GL 6600 > Stripe fee lines. Difference settles to connected account acct_1MaximorProc, which is not in vendor master.
- **detective_path:**
  1. Sum Stripe fee balance_transactions for Sep.
  2. Sum GL 6600 for Sep.
  3. Delta is the skim. September $18,206.40. Span $214,660.18.
  4. Contract math on charge gross should match Stripe fees within a few dollars, not GL.
- **expected_finding:** PROCESSOR_FEE_OVERSTATEMENT | $214,660.18 span; $18,206.40 in 2026-09 | CTR-STRIPE-001, 6600-Processor-Fees vs Stripe fee lines, po_1MaximorFees kept
- **must_not:**
  - Do not break payout-to-bank match.
  - Do not require live Stripe.
  - Do not change FEE-729103.
- **demo_beat:** Stripe Bot waterfall is correct. Books still leak 50 bps.

### ADV-PROC-002 — Connected account that is not a vendor

- **domain:** `processor`
- **stealth:** 5
- **span:** 2025-10 → 2026-09
- **storyline:** `SL-ADV-PROCESSOR`
- **preexisting_state:** Stripe sim includes connected account acct_1MaximorProc, transfers tr_mpr_* equal to the fee delta. VEND-MPR-01 is intentionally absent from vendor_master.
- **plant_objects:**
  - `integrations/stripe/transfers:tr_mpr_*`
  - `integrations/stripe/connected_account:acct_1MaximorProc`
  - `vendor_master (absent VEND-MPR-01)`
  - `bank (no separate bank line; netted in payout)`
- **how_it_hides:** Because transfers net inside the Stripe balance, bank never shows Maximor Processing. Vendor-master tests do not see it. Luis Redmond USR-STRIPE-01 is the account's dashboard user in stripe_users.json (new plant).
- **detective_path:**
  1. List Stripe connected accounts in the sim pack.
  2. acct_1MaximorProc legal name Maximor Processing LLC EIN 88-4412109.
  3. Join EIN to employee or vendor master: no hit. Join dashboard user to EMP-4402.
  4. Sum transfers $214,660.18.
- **expected_finding:** CONNECTED_ACCOUNT_SKIM | $214,660.18 | acct_1MaximorProc, tr_mpr_*, EMP-4402, absent from vendor_master
- **must_not:**
  - Do not add VEND-MPR-01 to the operational vendor master. Absence is the tell.
  - Do not invent a vendor-bank-change finding.

### ADV-PROC-003 — Payout that still equals the bank deposit

- **domain:** `cash`
- **stealth:** 3
- **span:** 2026-09-19
- **storyline:** `SL-ADV-PROCESSOR`
- **preexisting_state:** Keep po_1MaximorFees $12,610.00 and TXN-2026-09-019A. Densify additional payouts. Each payout equals its bank deposit. PROVIDER_PAYOUT remains correct.
- **plant_objects:**
  - `integrations/stripe/payouts:po_1MaximorFees`
  - `bank:TXN-2026-09-019A`
  - `integrations/stripe/bank_deposits`
- **how_it_hides:** The Kernel happy path is the hide. Agents who stop at payout=bank will miss ADV-PROC-001.
- **detective_path:**
  1. Match payout to bank (PASS).
  2. Continue into fee GL vs contract.
  3. Keep SCN-CASH-009 behavior on this identity.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** PROCESSOR_FEE_OVERSTATEMENT | payout MATCHED $12,610.00; fee GL still high on the densified population | po_1MaximorFees, TXN-2026-09-019A
- **must_not:**
  - Do not unmatch TXN-2026-09-019A.

### ADV-PROC-004 — Refund where the fee is not given back

- **domain:** `processor`
- **stealth:** 4
- **span:** 2026-09-22
- **storyline:** `SL-ADV-PROCESSOR`
- **preexisting_state:** Keep po_1MaximorRefunds identity. On densified refunds, Stripe returns the charge minus original fee, but GL 6600 still holds the fee and a second 'refund fee' $15.00–$45.00 books to 6600 and transfers to acct_1MaximorProc.
- **plant_objects:**
  - `integrations/stripe/refunds`
  - `integrations/stripe/payouts:po_1MaximorRefunds`
  - `gl:6600-Processor-Fees`
  - `bank:TXN-2026-09-022S`
- **how_it_hides:** Duplicate refund bank posting SCN-CASH-004 stays as a loud toy (TXN-2026-09-012A/B). This refund fee skim is inside a matched payout.
- **detective_path:**
  1. For each refund, check whether original fee reversed in GL. It did not.
  2. Extra GL 6600 on refunds $6,208.00 span.
  3. Do not confuse with TXN-2026-09-012A/B duplicate refund.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** PROCESSOR_FEE_OVERSTATEMENT | $6,208.00 extra refund fees | po_1MaximorRefunds kept, densified refunds, 6600
- **must_not:**
  - Do not remove the duplicate-refund toy.

### ADV-PROC-005 — Adyen blended rate used to explain Stripe

- **domain:** `processor`
- **stealth:** 4
- **span:** 2026-06 → 2026-09
- **storyline:** `SL-ADV-PROCESSOR`
- **preexisting_state:** A small Adyen sim (DABstep-sampled) books at 3.5 percent blended. Luis copies that blended rate into Stripe GL. Memo on JE-FEE-BLEND-YYYY-MM: 'harmonize processor rates'.
- **plant_objects:**
  - `integrations/adyen (sampled sim)`
  - `gl:JE-FEE-BLEND-*`
  - `vendor_contracts:CTR-STRIPE-001`
  - `vendor_contracts:CTR-ADYEN-001`
- **how_it_hides:** One blended rate across processors looks like a simplification. Stripe contract is cheaper. The blend overcharges Stripe volume, which is most of card volume.
- **detective_path:**
  1. Keep processor IDs on each charge.
  2. Apply each contract to its own volume.
  3. Stripe overcharge = ADV-PROC-001. Adyen GL matches Adyen contract.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** PROCESSOR_FEE_OVERSTATEMENT | blend memo hides Stripe 50 bps | JE-FEE-BLEND-*, CTR-STRIPE-001 vs CTR-ADYEN-001
- **must_not:**
  - Do not require the 450 DABstep Q&A product.
  - Sample 2–5k rows as DEMO-DESIGN says.

### ADV-PROC-006 — Dispute win that never returns to the ledger

- **domain:** `processor`
- **stealth:** 4
- **span:** 2026-07-18 → 2026-09
- **storyline:** `SL-ADV-PROCESSOR`
- **preexisting_state:** Keep po_1MaximorDisputes identity for the happy-path chargeback. Densify dispute dsp_win_4419 won 2026-08-14, $18,440.00 returned to Stripe balance then transferred to acct_1MaximorProc the same day.
- **plant_objects:**
  - `integrations/stripe/disputes:dsp_win_4419`
  - `integrations/stripe/transfers:tr_mpr_win_4419`
  - `gl:4000-Revenue`
  - `gl:6600-Processor-Fees`
  - `payouts:po_1MaximorDisputes`
- **how_it_hides:** Payout waterfall still shows a dispute line. GL never reinstates revenue or cash. Close does not look for won disputes.
- **detective_path:**
  1. List disputes with status won.
  2. Check GL cash or revenue reinstatement: none for dsp_win_4419.
  3. Transfer tr_mpr_win_4419 $18,440.00 to acct_1MaximorProc.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** CONNECTED_ACCOUNT_SKIM | $18,440.00 won dispute | dsp_win_4419, tr_mpr_win_4419, po_1MaximorDisputes kept as the other dispute story
- **must_not:**
  - Do not replace the demo chargeback payout.

### ADV-PROC-007 — Single reconciler on processor operations

- **domain:** `audit`
- **stealth:** 3
- **span:** 2025-10 → 2026-09
- **storyline:** `SL-ADV-PROCESSOR`
- **preexisting_state:** Luis Redmond EMP-4402 is initiator and reviewer on every Stripe rec workpaper REC-STRIPE-YYYY-MM. SOD-003 wants independent review when a reviewer is assigned. The reviewer_id is USR-STRIPE-01, same person.
- **plant_objects:**
  - `audit/reconciliations:REC-STRIPE-*`
  - `employee_master:EMP-4402`
  - `audit/approvals`
- **how_it_hides:** Looks like a specialized rec with a named expert. Not self-approval on INV-009.
- **detective_path:**
  1. Map reviewer_id and preparer_id to emp_id.
  2. Both are EMP-4402.
  3. Finding is SOD on processor rec, which then licenses ADV-PROC-001 testing.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** SELF_APPROVAL_ALIAS | processor recs 12 months | REC-STRIPE-*, USR-STRIPE-01, EMP-4402
- **must_not:**
  - Do not reuse APR-INV-SELF.
  - Do not call it SELF_APPROVAL if you need a distinct code. SELF_APPROVAL_ALIAS is the code.

### ADV-PROC-008 — Reserve release that is a connected-account transfer

- **domain:** `processor`
- **stealth:** 4
- **span:** 2026-09-24
- **storyline:** `SL-ADV-PROCESSOR`
- **preexisting_state:** Bank line BNK-UNX-001 $800 unexpected fee remains a forecast miss. Densify a second line TXN-STRIPE-RESERVE-REL $22,400.00 inflow labeled STRIPE RESERVE RELEASE. Stripe sim shows the money came from acct_1MaximorProc reversing a prior hold, not from Maximor's own reserve. GL credits 6600, reducing fee expense.
- **plant_objects:**
  - `bank:TXN-STRIPE-RESERVE-REL`
  - `integrations/stripe/transfers`
  - `gl:6600-Processor-Fees`
  - `reporting/actuals:ACT-UNEXPECTED kept on BNK-UNX-001`
- **how_it_hides:** Cash Bot may MATCH the inflow to a Stripe reserve account the company does not have. Forecast never planned $22,400. Luis books it as fee reversal, which improves opex.
- **detective_path:**
  1. Confirm Maximor Stripe reserve balance in sim is $0.
  2. Source of funds is acct_1MaximorProc.
  3. Keep BNK-UNX-001 $800 as a separate miss.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** CONNECTED_ACCOUNT_SKIM | $22,400.00 labeled reserve release | TXN-STRIPE-RESERVE-REL, acct_1MaximorProc, 6600 credit
- **must_not:**
  - Do not absorb BNK-UNX-001 into this line.

### ADV-CASH-004 — Stripe receipts below forecast, two causes

- **domain:** `cash`
- **stealth:** 3
- **span:** 2026-09-19
- **storyline:** `SL-ADV-PROCESSOR`
- **preexisting_state:** Keep po_1MaximorFees and ACT-STRIPE-LOW. Densify: gross charges support a higher net. Part of the miss is real refunds (demo). Part is the connected-account transfer that never hits Maximor bank.
- **plant_objects:**
  - `reporting/actuals:ACT-STRIPE-LOW`
  - `payouts:po_1MaximorFees`
  - `bank:TXN-2026-09-019A`
  - `transfers:tr_mpr_2026-09-19`
- **how_it_hides:** Story Bot can stop at 'fees and refunds'. The extra miss equals tr_mpr_2026-09-19 $1,184.22 on that payout's day (illustrative densify amount on top of the small demo payout).
- **detective_path:**
  1. Keep the forecast-miss identity.
  2. Split miss: documented Stripe fees/refunds vs connected-account transfer.
  3. Do not force the small demo payout to carry the entire $214k skim. The skim lives on densified volume; this payout is the teaching example.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** CONNECTED_ACCOUNT_SKIM | teaching delta $1,184.22 on the famous payout day; population $214,660.18 | po_1MaximorFees, ACT-STRIPE-LOW, tr_mpr_2026-09-19
- **must_not:**
  - Keep po_1MaximorFees bank amount $12,610.00 unless densify scales all Stripe together. If scaled, keep the identity and the miss.
## SL-ADV-MERRIMACK — Intercompany that is not intercompany

Insider: Nadia Voss + Merrimack Holdings. Span: 2025-12 → 2026-09. Techniques: 1300-Due-From-Affiliate, wires described as IC sweep, net-zero true-up JEs. Cumulative: $4,851,220.00 due-from balance; $2,200,000 cash already left.

### ADV-CLOSE-001 — Due-from-affiliate that is not an affiliate

- **domain:** `close`
- **stealth:** 5
- **span:** 2025-12-11 → 2026-09
- **storyline:** `SL-ADV-MERRIMACK`
- **preexisting_state:** GL 1300-Due-From-Affiliate $4,851,220.00 at Aug 31. Counterparty name Maximor EU BV CUST-IC-EU. No legal entity Maximor EU BV in company graph. No consolidation package. August close tied 1300 to a spreadsheet of 'IC invoices'.
- **plant_objects:**
  - `gl:1300-Due-From-Affiliate`
  - `ar_customers:CUST-IC-EU`
  - `close/tasks:TASK-BS`
  - `legal_entity_register (absent Maximor EU BV)`
- **how_it_hides:** BS rec of 1300 to the IC subledger PASSes. The subledger is a list of JE memos. No statutory audit of an EU BV exists.
- **detective_path:**
  1. Ask for articles of incorporation of Maximor EU BV. None in source_documents.
  2. Bank wires against this balance go to Merrimack Holdings (ADV-CASH-005).
  3. Balance grew $440,000–$520,000 per month since 2025-12.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** FAKE_INTERCOMPANY | $4,851,220.00 | 1300-Due-From-Affiliate, CUST-IC-EU, missing legal_entity
- **must_not:**
  - Do not create a real EU entity to make this wholesome.
  - Do not let TASK-BS pass on a spreadsheet rec without bank evidence.
- **demo_beat:** Close Bot recs 1300 to a schedule. Audit Bot asks whether the affiliate exists.

### ADV-CLOSE-002 — Intercompany true-up journals that net to zero

- **domain:** `close`
- **stealth:** 5
- **span:** 2026-01 → 2026-08
- **storyline:** `SL-ADV-MERRIMACK`
- **preexisting_state:** Each month JE-IC-TU-YYYY-MM Dr 1300 $480,000 Cr 2100-Due-To-Affiliate $480,000, then JE-IC-CLR-YYYY-MM Dr 2100 $480,000 Cr 1300 $40,000 Cr 1000-Cash $440,000. Net: cash leaves, 1300 grows $40,000, 2100 zeros.
- **plant_objects:**
  - `gl:JE-IC-TU-*`
  - `gl:JE-IC-CLR-*`
  - `gl:2100-Due-To-Affiliate`
  - `gl:1300-Due-From-Affiliate`
  - `bank:TXN-MRH-*`
- **how_it_hides:** Sampling one JE shows a balanced IC true-up. Sampling the pair shows cash leaving. 2100 ending balance $0 looks like a clean affiliate position.
- **detective_path:**
  1. Always pull IC journals in 48-hour pairs.
  2. Map the cash credit to TXN-MRH-* Merrimack wires.
  3. August pair: JE-IC-TU-2026-08 $512,400.00, JE-IC-CLR-2026-08 cash $472,400.00, 1300 increase $40,000.00.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** NET_ZERO_JE_PAIR | cash out $2,200,000.00 across pairs; 1300 residual growth | JE-IC-TU-*, JE-IC-CLR-*, 2100, 1300
- **must_not:**
  - Do not net the pair in the GL export. Keep two journals.
  - Do not label post_close.

### ADV-CASH-005 — Wires described as an IC sweep

- **domain:** `cash`
- **stealth:** 4
- **span:** 2025-12-11 → 2026-09
- **storyline:** `SL-ADV-MERRIMACK`
- **preexisting_state:** Bank counterparty MERRIMACK HOLDINGS LLC. Memo IC SWEEP EU. Amounts $438,220.18–$472,400.00. No vendor_id. Paid from operating cash, not a clearing account.
- **plant_objects:**
  - `bank:TXN-MRH-2025-12 through TXN-MRH-2026-08`
  - `vendor_master (no VEND-MRH-01 on master — plant the name only on the bank line, optional hidden vendor file for the plant team)`
  - `gl:1000-Cash`
- **how_it_hides:** Cash Bot may leave these as UNMATCHED bank then accept a journal explanation IC sweep. That is the intended Kernel-like path. The adversarial finding is the counterparty is not an affiliate bank.
- **detective_path:**
  1. UNMATCHED or JOURNAL_MATCH to JE-IC-CLR-* is not enough.
  2. Lookup Merrimack EIN 83-6612045 in legal_entity_register: absent.
  3. Beneficiary address 100 Low Street Newburyport. Not Amsterdam.
  4. September has no sweep yet (sabbatical). 1300 still sits.
- **expected_finding:** FAKE_INTERCOMPANY | $2,200,000.00 wires | TXN-MRH-*, memo IC SWEEP EU, EIN 83-6612045
- **must_not:**
  - Do not add a vendor-bank-change control result.
  - Optional plant of VEND-MRH-01 is plant-team only. Prefer bank-only counterparty so vendor tests miss it.

### ADV-VM-008 — Merrimack missing from the vendor master

- **domain:** `vendor-master`
- **stealth:** 3
- **span:** 2025-12-11 → 2026-09
- **storyline:** `SL-ADV-MERRIMACK`
- **preexisting_state:** 340 vendors after densify. Merrimack is not one of them. Payments still left the bank.
- **plant_objects:**
  - `vendor_master`
  - `bank:TXN-MRH-*`
  - `canonical/vendor_payments`
- **how_it_hides:** AP three-way never sees the wires because they never became invoices. They are journals. Vendor-duplicate tests are irrelevant.
- **detective_path:**
  1. List bank counterparties with no vendor_id and no customer_id.
  2. Merrimack is the largest such outflow.
  3. Compare to Harbor Electric and Lindholm which do have vendors.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** FAKE_INTERCOMPANY | $2,200,000.00 bank-only counterparty | TXN-MRH-*, vendor_master miss
- **must_not:**
  - Do not auto-create the vendor during ingestion.

### ADV-MIX-002 — Fake affiliate in close, cash, forecast, and journal sample

- **domain:** `mixed`
- **stealth:** 5
- **span:** 2025-12 → 2026-09
- **storyline:** `SL-ADV-MERRIMACK`
- **preexisting_state:** TASK-BS recs 1300. Cash explains wires as IC. Forecast FC-IC-IN week 8 collects $500,000 of the receivable. Audit journal sample hits JE-IC-TU-2026-08, which nets, and PASSes.
- **plant_objects:**
  - `close/tasks:TASK-BS`
  - `bank:TXN-MRH-*`
  - `reporting/forecast_lines:FC-IC-IN`
  - `audit/journal_entries:JE-IC-TU-2026-08`
- **how_it_hides:** Each function has a consistent story: affiliate. The company graph does not.
- **detective_path:**
  1. Close: 1300 unsupported by legal entity.
  2. Cash: beneficiary Newburyport.
  3. Story: FC-IC-IN is not collectible.
  4. Audit: sample the pair, not the true-up alone.
- **expected_finding:** FAKE_INTERCOMPANY | $4,851,220.00 receivable, $2,200,000.00 cash gone | 1300, TXN-MRH-*, FC-IC-IN, JE-IC-TU-2026-08 + JE-IC-CLR-2026-08
- **must_not:**
  - Do not PASS the journal sample on a single net-zero true-up.
- **demo_beat:** 2-hour: four greens, one missing articles of incorporation.

### ADV-RPT-004 — Forecast treats the affiliate receivable as week-8 cash

- **domain:** `reporting`
- **stealth:** 4
- **span:** 2026-11-02 week
- **storyline:** `SL-ADV-MERRIMACK`
- **preexisting_state:** FC-IC-IN $500,000 in week 2026-11-02, confidence 0.80, source 1300. No historical collection has ever occurred (wires only go out).
- **plant_objects:**
  - `reporting/forecast_lines:FC-IC-IN`
  - `reporting/forecast_weeks:2026-11-02`
  - `gl:1300-Due-From-Affiliate`
- **how_it_hides:** 13-week construction from AR/AP/payroll is the Kernel story. This line is a manual add. It looks like professional judgment.
- **detective_path:**
  1. List forecast lines with source_type affiliate.
  2. Historical cash-in from Merrimack or Maximor EU BV: $0.
  3. Remove FC-IC-IN. Week 8 operating cash drops $500,000.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** FORECAST_BIAS_FROM_AR | $500,000.00 week 2026-11-02 | FC-IC-IN, 1300
- **must_not:**
  - Keep the 13 weeks. Do not add a 14th.

### ADV-AUDIT-002 — Journal sample of a true-up that nets

- **domain:** `audit`
- **stealth:** 4
- **span:** 2026-08 sample
- **storyline:** `SL-ADV-MERRIMACK`
- **preexisting_state:** SCN-AUDIT-011 samples JE-AP-INV-001 (clean). Adversarial sample item AUD-SAMP-IC-08 is JE-IC-TU-2026-08 $512,400.00 Dr/Cr 1300/2100. Arithmetic PASS, SOD apparently populated.
- **plant_objects:**
  - `audit/journal_entries:AUD-SAMP-IC-08`
  - `gl:JE-IC-TU-2026-08`
  - `gl:JE-IC-CLR-2026-08`
- **how_it_hides:** Net-zero journals look like reclass. Policy does not require sampling the next day's clearing JE.
- **detective_path:**
  1. PASS the arithmetic on AUD-SAMP-IC-08.
  2. Expand to related_ids on the same day+1.
  3. JE-IC-CLR-2026-08 contains the cash credit. That is the fail.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** NET_ZERO_JE_PAIR | sample PASS, pair FAIL $472,400.00 cash | AUD-SAMP-IC-08, JE-IC-CLR-2026-08
- **must_not:**
  - Do not FAIL JE-AP-INV-001.
## SL-ADV-BRIGHTLINE — Customer-vendor round trip

Insider: shared address 14 Fayette Street; no single employee required. Span: 2025-09 → 2026-09. Techniques: AR to Brightline Media, AP to Brightline Studio, net cash out $2,200/month. Cumulative: $484,800 revenue and $524,800 opex; net $40,000 cash out.

### ADV-AR-014 — Brightline Media monthly platform invoices

- **domain:** `ar`
- **stealth:** 3
- **span:** 2025-09 → 2026-09
- **storyline:** `SL-ADV-BRIGHTLINE`
- **preexisting_state:** CUST-004 Brightline Media already exists as mixed payer. Densify monthly INV-AR-BLM-YYYY-MM $38,200.00 for 'analytics platform seats'. Payments arrive 12–18 days late, matching the customer profile.
- **plant_objects:**
  - `ar_customers:CUST-004`
  - `ar_invoices:INV-AR-BLM-2025-09 through INV-AR-BLM-2026-09`
  - `ar_payments:PAY-BLM-*`
  - `gl:4000-Revenue`
- **how_it_hides:** Revenue looks real. Cash comes in. Not channel stuffing. The hide is the AP mirror at the same street (ADV-AP-007).
- **detective_path:**
  1. Keep CUST-004 identity.
  2. Sum FYTD revenue $419,800.00 through August plus September open $38,200.00.
  3. Bank inflows BRIGHTLINE MEDIA match AR.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** ROUND_TRIP_COUNTERPARTY | AR $419,800.00 FYTD through Aug | INV-AR-BLM-*, CUST-004, 14 Fayette Street
- **must_not:**
  - Do not make Brightline the Quiet Harbor late story.

### ADV-AP-007 — Brightline Studio monthly retainers

- **domain:** `ap`
- **stealth:** 4
- **span:** 2025-09 → 2026-09
- **storyline:** `SL-ADV-BRIGHTLINE`
- **preexisting_state:** VEND-BLS-01 Brightline Studio LLC $40,400.00 per month demand-gen retainer, PO-BLS-STANDING $500,000 annual, approved by Hale in pieces of $24,900 (another Hale-limit split, Kestrel-adjacent technique but different insider story — requester is marketing manager EMP-3310 Nia Bright, who is a real employee).
- **plant_objects:**
  - `vendor_master:VEND-BLS-01`
  - `ap_invoices:INV-BLS-*`
  - `purchase_orders:PO-BLS-STANDING`
  - `purchase_orders:PO-BLS-SPLIT-*`
  - `employee_master:EMP-3310`
- **how_it_hides:** Marketing retainers are expected. Three-way uses a services GR 'accepted' by Nia. Amounts $40,400 are not Hale-limit. Standing PO is $500,000 so P-007 threshold is not the hide. The hide is the customer at the same address.
- **detective_path:**
  1. Vendor address 14 Fayette Street Somerville.
  2. Customer Brightline Media address 14 Fayette Street (plant on CUST-004).
  3. EIN 27-9081144 (Studio) vs 27-9081101 (Media). Consecutive.
  4. AP FYTD $444,400.00 through August.
- **expected_finding:** ROUND_TRIP_COUNTERPARTY | AP $444,400.00 FYTD through Aug | VEND-BLS-01, CUST-004, 14 Fayette Street, EINs 27-9081144 vs 27-9081101
- **must_not:**
  - Do not use Dana Kestrel as requester here.
  - Nia Bright is a real employee; she may be related to the customer. Plant emergency_contact 'Cara Bright' at 14 Fayette.

### ADV-CASH-006 — Net cash out on the Brightline pair

- **domain:** `cash`
- **stealth:** 4
- **span:** 2025-09 → 2026-09
- **storyline:** `SL-ADV-BRIGHTLINE`
- **preexisting_state:** Each month: inflow $38,200.00, outflow $40,400.00, net $2,200.00 out. Both legs MATCH. Cash rec is green.
- **plant_objects:**
  - `bank:TXN-BLM-IN-*`
  - `bank:TXN-BLS-OUT-*`
  - `cash_recon`
- **how_it_hides:** One-to-one matches hide an economic round trip. Amounts differ so they are not a same-amount red flag.
- **detective_path:**
  1. Net bank counterparties containing BRIGHTLINE.
  2. Net $2,200.00 x 13 months in span through Sep (Sep AP may still be open) = $26,400.00 through Aug, $28,600.00 if Sep paid.
  3. Plant Sep AP unpaid so net through Aug $26,400.00 cash out, Sep inflow may already have landed.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** ROUND_TRIP_COUNTERPARTY | net cash out $26,400.00 through Aug | TXN-BLM-IN-*, TXN-BLS-OUT-*
- **must_not:**
  - Do not unmatched either leg.

### ADV-RPT-005 — Revenue and opex both inflated by Brightline

- **domain:** `reporting`
- **stealth:** 3
- **span:** FY2026 YTD August
- **storyline:** `SL-ADV-BRIGHTLINE`
- **preexisting_state:** Board pack revenue and marketing opex both include Brightline. EBITDA almost unchanged (~$25k drag). Top line looks healthier.
- **plant_objects:**
  - `reporting/actuals revenue`
  - `reporting/actuals opex marketing`
  - `gl:4000-Revenue`
  - `gl:6000-Operating`
- **how_it_hides:** GM story is COGS. This is opex vs revenue. Flux vs budget may even be favorable on revenue.
- **detective_path:**
  1. Strip Brightline AR and AP from YTD.
  2. Revenue down $419,800. Marketing down $444,400. EBITDA up $24,600.
  3. Do not mix into GM 64→61.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** ROUND_TRIP_COUNTERPARTY | YTD revenue +$419,800 and opex +$444,400 | CUST-004, VEND-BLS-01
- **must_not:**
  - Do not put these IDs in gross_margin_drivers.

### ADV-AUDIT-003 — Two Brightline legal names, one street

- **domain:** `audit`
- **stealth:** 5
- **span:** 2026-09 sample of 2025-09 → 2026-09
- **storyline:** `SL-ADV-BRIGHTLINE`
- **preexisting_state:** Vendor sample and customer sample are separate. Neither sample joins address across AP and AR master data.
- **plant_objects:**
  - `audit/vendors:VEND-BLS-01`
  - `ar_customers:CUST-004`
  - `vendor_master.address`
  - `ar_customers.address (new field in densify)`
- **how_it_hides:** Duplicate-vendor control is AP-only. Related-party policy may not exist. Address join is the detective path.
- **detective_path:**
  1. Normalize street 14 Fayette St / 14 Fayette Street.
  2. Hit: CUST-004 and VEND-BLS-01.
  3. Add EIN consecutive numbers.
  4. Nia Bright EMP-3310 emergency_contact at that street.
- **expected_finding:** ROUND_TRIP_COUNTERPARTY | address join 14 Fayette Street | CUST-004, VEND-BLS-01, EMP-3310
- **must_not:**
  - Do not FAIL VEND-001-DUP as this finding.

### ADV-MIX-004 — Brightline in AR, AP, cash, and board pack

- **domain:** `mixed`
- **stealth:** 4
- **span:** 2025-09 → 2026-09
- **storyline:** `SL-ADV-BRIGHTLINE`
- **preexisting_state:** Collect Bot chases Brightline late payments. Pay Bot pays Studio on time. Cash matches both. Story includes the revenue. Nobody nets them.
- **plant_objects:**
  - `ar_invoices:INV-AR-BLM-*`
  - `ap_invoices:INV-BLS-*`
  - `bank:TXN-BLM-IN-*`
  - `bank:TXN-BLS-OUT-*`
  - `reporting/actuals`
- **how_it_hides:** Each Bot is correct on its object. The company-level net is the finding.
- **detective_path:**
  1. Collect: Brightline Media 12 days late (true).
  2. Pay: Studio within terms (true).
  3. Cash: both MATCHED.
  4. Story: net $2,200/month out and inflated top line.
- **expected_finding:** ROUND_TRIP_COUNTERPARTY | four greens, net $2,200.00 per month out | CUST-004, VEND-BLS-01
- **must_not:**
  - Do not hold Studio invoices for being related without the address join evidence.

### ADV-VM-009 — Brightline Studio standing vendor

- **domain:** `vendor-master`
- **stealth:** 2
- **span:** 2025-09-01 → 2026-09
- **storyline:** `SL-ADV-BRIGHTLINE`
- **preexisting_state:** VEND-BLS-01 first_seen 2025-09-01, created_by USR-VM-04 Dana Kestrel (shared identity across storylines: she owns vendor master, not this economics).
- **plant_objects:**
  - `vendor_master:VEND-BLS-01`
  - `employee_master:EMP-4128`
  - `employee_master:EMP-3310`
- **how_it_hides:** Kestrel created many vendors. Creation alone is not the Brightline scheme. It is a join for the 2-hour sim (one clerk, many doors).
- **detective_path:**
  1. created_by USR-VM-04.
  2. Do not attribute the round-trip cash to Dana without the Fayette join.
  3. Use this as evidence that vendor-master control is weak, which enables Kestrel and Brightline both.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** NEAR_DUPLICATE_VENDOR | created_by EMP-4128, economics with EMP-3310 | VEND-BLS-01
- **must_not:**
  - Do not collapse Brightline into Kestrel Industrial.
## SL-ADV-CAMBRIDGE — CAM true-up and account transposition

Insider: Riley Cho EMP-2201. Span: 2025-07 → 2026-09. Techniques: second vendor for CAM, ACH account last-two transposition labeled format cleanup, double occupancy accrual. Cumulative: $126,408.22 CAM plus $48,000 diverted rent months.

### ADV-VM-010 — Cambridge Properties account number after format cleanup

- **domain:** `vendor-master`
- **stealth:** 5
- **span:** 2026-05-22 → 2026-09
- **storyline:** `SL-ADV-CAMBRIDGE`
- **preexisting_state:** VEND-013 Cambridge Properties is the real landlord since 2021. On 2026-05-22 vendor_bank account 44552109 becomes 44552190. change_memo 'ACH format / strip check digit spaces'. Riley Cho EMP-2201 submitted the change. Engine has no bank-change control.
- **plant_objects:**
  - `vendor_master:VEND-013`
  - `vendor_bank_history:VEND-013`
  - `vendor_master:VEND-CPS-01`
  - `employee_master:EMP-2201`
  - `bank:TXN-CAM-RENT-* after 2026-05-22`
- **how_it_hides:** Rent invoices still say Cambridge Properties. Three-way matches the lease CTR-CAM-001 $48,000/month (densify; toy scale had no rent). ACH receiving account after May is 2190 last4, which is VEND-CPS-01 / Cho LLC, not the landlord lockbox 2109 last4.
- **detective_path:**
  1. Diff vendor_bank_history 2026-05-22. Transposition 09→90.
  2. Compare bank receiving_account to landlord lockbox on the lease.
  3. Join 44552190 to VEND-CPS-01.
  4. Rent still $48,000.00 (round, because rent is round — pair with CAM true-up cents).
  5. Do not emit a control FAIL named vendor-bank-change. Emit BANK_INSTRUMENT_DRIFT from the field compare.
- **expected_finding:** BANK_INSTRUMENT_DRIFT | $192,000.00 rent Jun–Sep at transposed account | VEND-013 44552109→44552190, VEND-CPS-01, EMP-2201, CTR-CAM-001
- **must_not:**
  - Do not implement a fake control result.
  - Do not touch Helios wire instructions.
- **demo_beat:** Landlord name on the statement, Cho's account in the NACHA details.

### ADV-AP-008 — CAM true-up invoices to Property Services

- **domain:** `ap`
- **stealth:** 4
- **span:** 2025-07 → 2026-09
- **storyline:** `SL-ADV-CAMBRIDGE`
- **preexisting_state:** VEND-CPS-01 monthly CAM INV-CPS-YYYY-MM $8,206.18–$11,440.62. Lease allows CAM true-up once a year. These are monthly.
- **plant_objects:**
  - `vendor_master:VEND-CPS-01`
  - `ap_invoices:INV-CPS-*`
  - `vendor_contracts:CTR-CAM-001`
  - `purchase_orders:PO-CPS-CAM`
- **how_it_hides:** Facilities AP is noisy. Riley Cho accepts every GR as 'CAM actuals'. Amounts have cents. Hale approves because each invoice is under $25,000.
- **detective_path:**
  1. CTR-CAM-001 CAM_true_up_cadence = annual.
  2. Count INV-CPS-* monthly = 15 invoices, $126,408.22.
  3. Landlord VEND-013 already billed Q1 2026 annual CAM $18,200.00 on INV-CAM-CAM-2026.
  4. Double bill: annual from landlord plus monthly from Services.
- **expected_finding:** CAM_TRUEUP_ORPHAN | $126,408.22 monthly CAM plus $18,200.00 annual CAM | INV-CPS-*, INV-CAM-CAM-2026, CTR-CAM-001
- **must_not:**
  - Do not merge VEND-CPS-01 into VEND-013 via normalize (Property vs Properties is close — keep Services vs Properties so normalize may or may not hit. Plant normalize keys different: cambridgepropertyservices vs cambridgeproperties).

### ADV-AP-009 — Same month rent to two Cambridge vendors

- **domain:** `ap`
- **stealth:** 3
- **span:** 2026-06 → 2026-09
- **storyline:** `SL-ADV-CAMBRIDGE`
- **preexisting_state:** After the bank swap, VEND-013 still issues rent invoices (unpaid or paid to the new account). VEND-CPS-01 also issues 'base rent reconciliation' $4,000.00 in June and August only.
- **plant_objects:**
  - `ap_invoices:INV-CAM-RENT-2026-06`
  - `ap_invoices:INV-CPS-RENT-2026-06`
  - `ap_invoices:INV-CAM-RENT-2026-08`
  - `ap_invoices:INV-CPS-RENT-2026-08`
- **how_it_hides:** Different amounts so duplicate-invoice does not fire. Different vendors. Both reference lease CTR-CAM-001.
- **detective_path:**
  1. Group AP by contract_id CTR-CAM-001 and month.
  2. June and August have two rent-like bills.
  3. Extra $8,000.00 is the finding inside the larger CAM skim.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** CAM_TRUEUP_ORPHAN | extra $8,000.00 June+August | INV-CPS-RENT-2026-06, INV-CPS-RENT-2026-08
- **must_not:**
  - Do not duplicate INV-001.

### ADV-CASH-007 — ACH counterparty name Property SVC

- **domain:** `cash`
- **stealth:** 3
- **span:** 2026-06 → 2026-09
- **storyline:** `SL-ADV-CAMBRIDGE`
- **preexisting_state:** Bank description CAMBRIDGE PROPERTY SVC even when AP vendor is Cambridge Properties. Cash Bot matches on amount and date to INV-CAM-RENT-*.
- **plant_objects:**
  - `bank:TXN-CAM-RENT-2026-06 through 2026-09`
  - `ap_invoices:INV-CAM-RENT-*`
  - `vendor_master:VEND-013`
- **how_it_hides:** Fuzzy name match Properties vs Property SVC is close enough for a naive matcher. Amount $48,000 exact.
- **detective_path:**
  1. Compare bank counterparty to vendor_master.name.
  2. Compare receiving_account last4 2190 vs lease lockbox 2109.
  3. Amount match is not enough.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** BANK_INSTRUMENT_DRIFT | $48,000.00 monthly after May | TXN-CAM-RENT-*, counterparty CAMBRIDGE PROPERTY SVC, last4 2190
- **must_not:**
  - Do not fail INV-017 fee-netted match by analogy.

### ADV-CLOSE-005 — Occupancy accrued and prepaid in the same month

- **domain:** `close`
- **stealth:** 3
- **span:** 2026-09
- **storyline:** `SL-ADV-CAMBRIDGE`
- **preexisting_state:** Close books ACC-CAM-2026-09 $48,000 because September landlord invoice 'not yet received' (it was sent to Cho's personal email). Also PRE-CAM-Q3 $24,000 remaining for 'prepaid occupancy' from a June payment of extra CAM.
- **plant_objects:**
  - `close/accruals:ACC-CAM-2026-09`
  - `close/prepaids:PRE-CAM-Q3`
  - `ap_invoices:INV-CAM-RENT-2026-09`
  - `gl:6300-Occupancy`
- **how_it_hides:** Harbor Electric accrual remains the demo accrual. This extra occupancy pair can both look supported. Expense 6300 in September = rent + accrual + CAM + prepaid amort, too high by ~$48,000 if rent invoice is also posted.
- **detective_path:**
  1. List occupancy charges in September GL.
  2. Detect double count: AP invoice + accrual on the same lease month.
  3. Keep ACC-HE-2026-09 as the clean utility accrual.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** CAM_TRUEUP_ORPHAN | ~$48,000.00 double occupancy | ACC-CAM-2026-09, INV-CAM-RENT-2026-09, PRE-CAM-Q3, ACC-HE-2026-09 untouched
- **must_not:**
  - Do not break Harbor Electric or Lindholm accruals.

### ADV-AUDIT-004 — Vendor sample that never joins the receiving account

- **domain:** `audit`
- **stealth:** 5
- **span:** 2026-09
- **storyline:** `SL-ADV-CAMBRIDGE`
- **preexisting_state:** Audit vendor sample includes VEND-013 as a long-standing low-risk landlord. Control AUD-DUP-VEND-001 does not look at bank fields. Finding must be built from registers.
- **plant_objects:**
  - `audit/vendors:VEND-013`
  - `vendor_bank_history:VEND-013`
  - `bank:TXN-CAM-RENT-*`
  - `audit/policy.json`
- **how_it_hides:** Sample PASS on duplicate-vendor and unusual=false. The detective path is the NACHA account vs lease.
- **detective_path:**
  1. Do not FAIL VEND-013 on DUPLICATE_VENDOR.
  2. Join vendor_bank to bank receiving_account to lease lockbox.
  3. Write BANK_INSTRUMENT_DRIFT on the sample expansion.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** BANK_INSTRUMENT_DRIFT | sample PASS on name, FAIL on account 44552190 | VEND-013, lease lockbox 44552109
- **must_not:**
  - Do not require unimplemented control AUD of bank change.

### ADV-MIX-005 — Cambridge rent in AP, bank, close, and facilities payroll

- **domain:** `mixed`
- **stealth:** 4
- **span:** 2025-07 → 2026-09
- **storyline:** `SL-ADV-CAMBRIDGE`
- **preexisting_state:** Riley Cho also has a $1,200.00 monthly 'stipend' on payroll coded as facilities allowance ALLW-CHO. Combined with CAM AP and rent diversion.
- **plant_objects:**
  - `payroll_register:ALLW-CHO`
  - `ap_invoices:INV-CPS-*`
  - `bank:TXN-CAM-RENT-*`
  - `close/accruals:ACC-CAM-2026-09`
  - `employee_master:EMP-2201`
- **how_it_hides:** Payroll allowance is small and ordinary. It is the identity join, not the dollars.
- **detective_path:**
  1. AP: CAM monthly.
  2. Cash: transposed rent account.
  3. Close: double occupancy.
  4. Payroll: ALLW-CHO $1,200.00 to the same person who submitted the bank change.
- **expected_finding:** BANK_INSTRUMENT_DRIFT | rent diversion $192,000 plus CAM $126,408.22 plus stipend $18,000.00 span | EMP-2201, VEND-013, VEND-CPS-01, ALLW-CHO
- **must_not:**
  - Do not call the stipend a ghost. Cho is real and badges in.
## SL-ADV-CLOSECOSMETIC — Net-zero close cosmetics

Insider: Nadia Voss EMP-1088. Span: 2026-03 → 2026-09. Techniques: undeposited-funds cash hole, effective-date vs posting-date (not labeled post_close), Lenovo rollout capitalized but not tagged. Cumulative: $186,420.18 cash parked; $154,214.00 of FA with no asset tag.

### ADV-CLOSE-006 — Cash parked in undeposited funds at month-end

- **domain:** `close`
- **stealth:** 5
- **span:** 2026-03-31 → 2026-08-31
- **storyline:** `SL-ADV-CLOSECOSMETIC`
- **preexisting_state:** JE-CASH-PARK-YYYY-MM Dr 1030-Undeposited-Funds $186,420.18 Cr 1000-Cash $186,420.18 on the last day of March, May, and August (not every month). Reversed on the 2nd of the next month except August's park is still open in September because sabbatical.
- **plant_objects:**
  - `gl:JE-CASH-PARK-2026-03`
  - `gl:JE-CASH-PARK-2026-05`
  - `gl:JE-CASH-PARK-2026-08`
  - `gl:JE-CASH-UNPARK-2026-04`
  - `gl:JE-CASH-UNPARK-2026-06`
  - `gl:1030-Undeposited-Funds`
  - `gl:1000-Cash`
  - `cash_recon/balances`
- **how_it_hides:** Bank rec of operating account uses book cash after the park, so book cash is lower and closer to an operating account that is missing Merrimack wires. 1030 rec is a 'deposit in transit' schedule that lists fake batches.
- **detective_path:**
  1. List 1030 items older than 5 days at each close.
  2. August park $186,420.18 still open. No bank deposit exists for that batch id DIT-FAKE-0831.
  3. The amount equals the residual of Merrimack August wire $472,400.00 minus IC residual $40,000 minus other plugs — plant as equal to the hole Nadia needed to hide vs bank. Specify: $186,420.18 = operating book/bank gap after IC journal but before park.
  4. Do not MATCH DIT-FAKE-0831.
- **expected_finding:** NET_ZERO_JE_PAIR | $186,420.18 parked 2026-08-31, still open | JE-CASH-PARK-2026-08, DIT-FAKE-0831, 1030, 1000
- **must_not:**
  - Do not reverse the August park in September seed. Close must see it.
  - Do not use post_close=true.
- **demo_beat:** Cash rec can look better after the park. September unpark never came.

### ADV-CLOSE-007 — Unpark journals with a different memo

- **domain:** `close`
- **stealth:** 4
- **span:** 2026-04-02 and 2026-06-02
- **storyline:** `SL-ADV-CLOSECOSMETIC`
- **preexisting_state:** JE-CASH-UNPARK-2026-04 memo 'record weekend deposits'. It reverses the park but the weekend deposit file is empty. Same for June.
- **plant_objects:**
  - `gl:JE-CASH-UNPARK-2026-04`
  - `gl:JE-CASH-UNPARK-2026-06`
  - `bank_statement April and June 1st-3rd`
- **how_it_hides:** Reversal looks like a timing difference SCN-CASH-006. There is no next-period bank item.
- **detective_path:**
  1. For each unpark, search next 5 bank days for $186,420.18. No hit.
  2. Contrast with real timing item GL-AP-HE / TXN-2026-10-001 which should remain a true timing difference.
  3. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** NET_ZERO_JE_PAIR | $186,420.18 unpark without bank | JE-CASH-UNPARK-2026-04, JE-CASH-UNPARK-2026-06 vs GL-AP-HE timing kept
- **must_not:**
  - Do not break Harbor Electric timing difference.

### ADV-CLOSE-009 — Payroll accrual reversed into other receivable

- **domain:** `close`
- **stealth:** 4
- **span:** 2026-08-31 → 2026-09-02
- **storyline:** `SL-ADV-CLOSECOSMETIC`
- **preexisting_state:** Standard payroll accrual Dr 6100 Cr 2200 $4,218,645.72 (densified). Next entry JE-PR-SHIFT-2026-08 Dr 2200 $84,000.00 Cr 6100 $84,000.00, then JE-PR-AR-2026-08 Dr 1350 $84,000.00 Cr 2200 $84,000.00. Expense down, fake receivable up.
- **plant_objects:**
  - `gl:JE-PR-ACC-2026-08`
  - `gl:JE-PR-SHIFT-2026-08`
  - `gl:JE-PR-AR-2026-08`
  - `gl:2200-Payroll-Accrual`
  - `gl:1350-Other-Receivable`
  - `reporting/payroll`
- **how_it_hides:** Payroll rec of 2200 to the register can still pass if the $84,000 is described as 'contractor reclass'. 1350 already holds Orbit recoveries (ADV-PRE-002). They mix.
- **detective_path:**
  1. Split 1350 subledger by memo. Orbit vs payroll reclass vs other.
  2. $84,000.00 payroll piece has no contractor invoice.
  3. 6100 September flux looks better by $84,000 versus budget.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** NET_ZERO_JE_PAIR | $84,000.00 payroll expense moved to 1350 | JE-PR-SHIFT-2026-08, JE-PR-AR-2026-08, 1350
- **must_not:**
  - Do not use this $84,000 to explain PR-2026-10-02.

### ADV-CLOSE-010 — August effective date, September posting date, not labeled post-close

- **domain:** `close`
- **stealth:** 5
- **span:** 2026-09-04 posting for 2026-08-31 effective
- **storyline:** `SL-ADV-CLOSECOSMETIC`
- **preexisting_state:** JE-AUG-LATE-01 $41,206.18 Dr 6000 Cr 2000, vendor Westbrook, effective_date 2026-08-31, posting_date 2026-09-04, post_close=false. August close_timestamp is 2026-09-03T18:00:00Z. This posted 14 hours after close without the post_close flag.
- **plant_objects:**
  - `canonical/journal_entries:JE-AUG-LATE-01`
  - `audit/periods:2026-08 close_timestamp`
  - `gl:JE-POST-CLOSE-001`
- **how_it_hides:** Loud decoy JE-POST-CLOSE-001 is flagged. This one is not. Recurring-template flag is true, so it looks like a scheduled AP accrual.
- **detective_path:**
  1. Compare posting_timestamp to close_timestamp regardless of post_close boolean.
  2. JE-AUG-LATE-01 posted 2026-09-04T08:12:00Z > 2026-09-03T18:00:00Z.
  3. Keep JE-POST-CLOSE-001 as the loud decoy the Kernel already finds.
  4. Vendor on the late JE is Westbrook (Kestrel split counterpart).
- **expected_finding:** EFFECTIVE_DATE_MISMATCH | $41,206.18 posted after August close without post_close flag | JE-AUG-LATE-01, CLOSE-2026-08, Westbrook
- **must_not:**
  - Do not set post_close=true on JE-AUG-LATE-01.
  - Do not delete JE-POST-CLOSE-001.
- **demo_beat:** Audit Bot that filters post_close==true misses this. Timestamp compare catches it.

### ADV-AUDIT-001 — Reviewer ID that is a distribution list

- **domain:** `audit`
- **stealth:** 4
- **span:** 2026-03 → 2026-09
- **storyline:** `SL-ADV-CLOSECOSMETIC`
- **preexisting_state:** USR-REV-04 is approver on rec plugs, IC true-ups, and cash parks. employee_master has no EMP for USR-REV-04. Directory lists it as close-review@maximor.example.
- **plant_objects:**
  - `audit/approvals`
  - `employee_master`
  - `directory:USR-REV-04`
  - `gl posters USR-JE-04`
- **how_it_hides:** SOD-002 sees preparer != approver string. It PASSes. The approver is not a person.
- **detective_path:**
  1. Resolve every approver_id to an emp_id.
  2. USR-REV-04 fails resolution.
  3. All Nadia cosmetic JEs use this approver.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** SELF_APPROVAL_ALIAS | USR-REV-04 is not a person | JE-REC-PLUG-*, JE-IC-*, JE-CASH-PARK-*, USR-JE-04
- **must_not:**
  - Do not reuse APR-INV-SELF.

### ADV-AUDIT-005 — Two user IDs for Nadia Voss

- **domain:** `audit`
- **stealth:** 5
- **span:** 2022-09-08 → 2026-09
- **storyline:** `SL-ADV-CLOSECOSMETIC`
- **preexisting_state:** USR-JE-04 and USR-NA-VOSS both map to EMP-1088. Display names 'N. Voss' and 'Nadia Voss'. Several pairs use one as preparer and the other as approver.
- **plant_objects:**
  - `employee_master:EMP-1088`
  - `user_map:USR-JE-04`
  - `user_map:USR-NA-VOSS`
  - `gl:JE-PRE-OIC-EXP-*`
  - `gl:JE-PRE-OIC-REV-*`
- **how_it_hides:** String inequality satisfies SOD. Inverse of APR-INV-SELF, which is the same ID twice.
- **detective_path:**
  1. Join user_map.emp_id.
  2. Flag journals where preparer emp_id == approver emp_id even if usr_id differs.
  3. Hits on the Orbit reversal pairs and two IC true-ups.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** SELF_APPROVAL_ALIAS | EMP-1088 as USR-JE-04 and USR-NA-VOSS | JE-PRE-OIC-REV-*, JE-IC-TU-2026-05, JE-IC-TU-2026-07
- **must_not:**
  - Do not plant the same usr_id on both sides (loud).

### ADV-FA-001 — Lenovo rollout capitalized beyond tagged units

- **domain:** `prepaid-fa`
- **stealth:** 5
- **span:** 2026-03-18 → 2026-09
- **storyline:** `SL-ADV-CLOSECOSMETIC`
- **preexisting_state:** FA-LEN-ROLL-26 $428,650.00, 168 units, vendor Lenovo VEND-020. Asset tags exist for 107 units. 61 units never tagged. GR-LEN-ROLL qty 168. Cycle count of laptops 107 + known Dell servers.
- **plant_objects:**
  - `close/fixed_assets:FA-LEN-ROLL-26`
  - `ap_invoices:INV-LEN-ROLL-26`
  - `goods_receipts:GR-LEN-ROLL`
  - `it_assets:MX-LPT-*`
  - `close/fixed_assets:FA-DELL-001`
  - `vendor_master:VEND-020`
- **how_it_hides:** Three-way match PASSes (PO 168, GR 168, INV 168). FA register uses GR qty. IT asset register is a different system. Dell cluster remains clean.
- **detective_path:**
  1. Count MX-LPT tags issued in the rollout series: 107.
  2. 61 missing = $154,214.00 at $2,528.10 unit cost.
  3. Glen Park posted GR-LEN-ROLL in 3 minutes (same pattern as Kestrel GRs).
  4. Keep INV-018 / FA-DELL-001.
- **expected_finding:** CAPITALIZED_UNRECEIVED | $154,214.00 untagged | FA-LEN-ROLL-26, GR-LEN-ROLL, 107 of 168 MX-LPT tags, VEND-020
- **must_not:**
  - Do not dirty FA-DELL-001.
  - Do not HOLD INV-LEN-ROLL-26 on three-way match.

### ADV-FA-003 — Depreciation on untagged laptops

- **domain:** `prepaid-fa`
- **stealth:** 3
- **span:** 2026-04 → 2026-09
- **storyline:** `SL-ADV-CLOSECOSMETIC`
- **preexisting_state:** Straight-line 36 months on $428,650 salvage 0. Monthly dep $11,907.00 including the missing 61 units ($4,283.58 of each month).
- **plant_objects:**
  - `runs/month_end/depreciation_schedule:FA-LEN-ROLL-26`
  - `gl:JE-FA-LEN-*`
  - `close/fixed_assets:FA-LEN-ROLL-26`
- **how_it_hides:** Depreciation rec to the schedule PASSes. The schedule trusts FA cost.
- **detective_path:**
  1. Recompute dep on tagged cost only $428,650 * 107/168.
  2. Extra dep $4,283.58 x 6 months = $25,701.48.
  3. Keep Dell dep as the demo identity.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** CAPITALIZED_UNRECEIVED | extra dep $25,701.48 | JE-FA-LEN-*, FA-LEN-ROLL-26
- **must_not:**
  - Do not change JE-FA-DELL-202609 except by densify scale if needed. Prefer leave Dell numbers.
## SL-ADV-FREIGHT — Accessorial freight skim

Insider: Dana Kestrel (shared) + Freightline Expedite. Span: 2025-11 → 2026-09. Techniques: small accessorial ACH, grouped ACH with Kestrel, COGS 40 bps, not the loud 3-point GM story. Cumulative: $61,288.40 accessorials.

### ADV-AP-010 — Freightline Expedite accessorial invoices

- **domain:** `ap`
- **stealth:** 3
- **span:** 2025-11 → 2026-09
- **storyline:** `SL-ADV-FREIGHT`
- **preexisting_state:** VEND-019 Freightline Logistics remains the real freight vendor (loud GM driver TXN-FRT-SEP-001 stays). VEND-FLE-01 Freightline Expedite bills accessorials $184.22–$612.08, 7–12 times per month.
- **plant_objects:**
  - `vendor_master:VEND-FLE-01`
  - `vendor_master:VEND-019`
  - `ap_invoices:INV-FLE-*`
  - `reporting:TXN-FRT-SEP-001`
- **how_it_hides:** Accessorials are expected in freight. Names differ enough to skip normalize. Each invoice under $300–$600, some under P-009 if matched to a standing PO PO-FLE-ACC $1,000.
- **detective_path:**
  1. Sum INV-FLE-* $61,288.40.
  2. BOL numbers on Expedite invoices reuse Logistics BOLs with suffix -X.
  3. Dana Kestrel created VEND-FLE-01 on 2025-11-10.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** FREIGHT_SURCHARGE_SKIM | $61,288.40 | VEND-FLE-01 vs VEND-019, INV-FLE-*, PO-FLE-ACC
- **must_not:**
  - Do not replace TXN-FRT-SEP-001.
  - Do not make this a 3-point GM move. It is ~40 bps on densified freight.

### ADV-CASH-001 — Small ACH to Expedite between Logistics payments

- **domain:** `cash`
- **stealth:** 3
- **span:** 2025-11 → 2026-09
- **storyline:** `SL-ADV-FREIGHT`
- **preexisting_state:** Bank lines $184.22–$612.08, counterparty FREIGHTLINE EXPEDITE. Easy to treat as bank fees or as part of Freightline Logistics.
- **plant_objects:**
  - `bank:TXN-FLE-*`
  - `ap_invoices:INV-FLE-*`
  - `cash_recon`
- **how_it_hides:** Amount match to invoices PASSes. Fuzzy match to VEND-019 would also be tempting. Either path hides a second vendor.
- **detective_path:**
  1. Do not fuzzy-merge EXPEDITE into LOGISTICS.
  2. Exact counterparty match to VEND-FLE-01.
  3. Count of small ACH ~90 items.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** FREIGHT_SURCHARGE_SKIM | ~90 ACH items $61,288.40 | TXN-FLE-*
- **must_not:**
  - Do not call these UNEXPLAINED_DIFFERENCE pennies.

### ADV-CASH-002 — Grouped ACH that mixes Expedite with Kestrel

- **domain:** `cash`
- **stealth:** 4
- **span:** 2026-07-16 and 2026-08-20
- **storyline:** `SL-ADV-FREIGHT`
- **preexisting_state:** Two ACH files include VEND-KIS-01 and VEND-FLE-01 in one NACHA batch, total matching a single bank line. Cash Bot GROUPED_MATCH like Northline.
- **plant_objects:**
  - `bank:TXN-MIX-2026-07-16`
  - `bank:TXN-MIX-2026-08-20`
  - `canonical/vendor_payments`
  - `bank:TXN-2026-09-008`
- **how_it_hides:** Grouped match is a taught happy path. Mixing two adversarial vendors in one ACH borrows that path.
- **detective_path:**
  1. Explode TXN-MIX-2026-07-16 $26,412.40 = INV-KIS-0716 $24,880.44 + INV-FLE-0716 $1,531.96.
  2. Keep TXN-2026-09-008 as clean Northline grouped match.
  3. Requester on both invoices EMP-4128.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** FREIGHT_SURCHARGE_SKIM | mixed grouped ACH $26,412.40 and $25,118.62 | TXN-MIX-2026-07-16, TXN-MIX-2026-08-20, EMP-4128
- **must_not:**
  - Do not dirty Northline grouped ACH.

### ADV-RPT-001 — Freight variance of 40 basis points

- **domain:** `reporting`
- **stealth:** 4
- **span:** 2025-11 → 2026-09
- **storyline:** `SL-ADV-FREIGHT`
- **preexisting_state:** Loud GM is 300 bps from supplier, freight, hosting source txs. Expedite adds ~40 bps of freight COGS that look like rate inflation vs Logistics contract.
- **plant_objects:**
  - `reporting/actuals freight`
  - `vendor_contracts:CTR-FRL-001`
  - `ap_invoices:INV-FLE-*`
  - `gross_margin_drivers (untouched)`
- **how_it_hides:** A Bot that found the 3-point story will stop. The 40 bps is the slow leak.
- **detective_path:**
  1. Compute freight / revenue with and without VEND-FLE-01.
  2. 40 bps on $31.1M Sep revenue ≈ $12,440 in September Expedite (plant Sep FLE $12,440.18).
  3. Do not add INV-FLE to gross_margin_drivers in the loud key.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** FREIGHT_SURCHARGE_SKIM | ~40 bps; September $12,440.18 | INV-FLE-2026-09-*, CTR-FRL-001, not TXN-FRT-SEP-001
- **must_not:**
  - Do not retell 64%→61% as this story.
- **demo_beat:** Judge already saw the 3-point drop. The quieter 40 bps is still cash.

### ADV-MIX-007 — Freight leak in AP, bank, COGS, and Kestrel identity

- **domain:** `mixed`
- **stealth:** 4
- **span:** 2025-11 → 2026-09
- **storyline:** `SL-ADV-FREIGHT`
- **preexisting_state:** Same clerk Dana Kestrel created VEND-FLE-01 and VEND-KIS-01. Freight is the small door. Kestrel Industrial is the large door.
- **plant_objects:**
  - `vendor_master:VEND-FLE-01`
  - `vendor_master:VEND-KIS-01`
  - `bank:TXN-MIX-*`
  - `reporting/actuals freight`
- **how_it_hides:** Separately each vendor is explainable. Together they share created_by, dock, and two mixed ACH files.
- **detective_path:**
  1. Vendor master created_by join.
  2. Mixed ACH explode.
  3. COGS 40 bps.
  4. Then open the Kestrel related-party join.
- **expected_finding:** FREIGHT_SURCHARGE_SKIM | $61,288.40 plus pointer to VEND-KIS-01 $187,412.18 | VEND-FLE-01, VEND-KIS-01, EMP-4128
- **must_not:**
  - Do not merge the freight finding into RELATED_PARTY_VENDOR without the created_by evidence.

### ADV-AUDIT-006 — Freight sample treated as ordinary recurring

- **domain:** `audit`
- **stealth:** 3
- **span:** 2026-09
- **storyline:** `SL-ADV-FREIGHT`
- **preexisting_state:** Small accessorials fall under ordinary_recurring round-number rules when they land on $200.00, but most have cents. Sample of freight invoices picks VEND-019 only.
- **plant_objects:**
  - `audit/invoices freight sample`
  - `ap_invoices:INV-FLE-*`
  - `audit/policy.json`
- **how_it_hides:** Population filter vendor=Freightline Logistics misses Expedite.
- **detective_path:**
  1. Search vendor names containing Freightline, not equal Logistics.
  2. Include VEND-FLE-01 in the freight sample expansion.
  3. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** FREIGHT_SURCHARGE_SKIM | Logistics sample PASS, Expedite population $61,288.40 | VEND-019 sample vs VEND-FLE-01
- **must_not:**
  - Do not FAIL VEND-019 as duplicate of VEND-FLE-01 via the Acme pattern. Use NEAR_DUPLICATE_VENDOR only if normalize keys are planted distinct.
## SL-ADV-CROSS — Cross-storyline extras

These extras bind storylines. ADV-MIX-008 is the two-hour judge path. ADV-AP-011 keeps the Acme 2/10 path clean while showing a Kestrel clawback. ADV-AP-012 is the inverse prepaid (expense too early). ADV-FA-002 is the consignment cage for Pinnacle goods.

### ADV-AP-011 — Early-payment discount taken and then the gross paid

- **domain:** `ap`
- **stealth:** 3
- **span:** 2026-06-18 → 2026-07-02
- **storyline:** `SL-ADV-KESTREL`
- **preexisting_state:** INV-KIS-0618 $24,106.18 terms 2/10. PAY-KIS-DISC $23,624.06 on 2026-06-18. PAY-KIS-GROSS-BAL $482.12 on 2026-07-02 described as 'short-pay true-up'. Net the vendor received 100 percent. Books recorded $482.12 discount income then reversed it.
- **plant_objects:**
  - `ap_invoices:INV-KIS-0618`
  - `canonical/vendor_payments:PAY-KIS-DISC`
  - `canonical/vendor_payments:PAY-KIS-GROSS-BAL`
  - `gl:discount income`
  - `bank:TXN-KIS-0618`
  - `bank:TXN-KIS-0702`
- **how_it_hides:** P-014 capture-discount is satisfied on the first payment. The second payment looks like a separate small invoice match if the Bot does not link them. INV-001 Acme 2/10 remains the clean discount demo.
- **detective_path:**
  1. Keep INV-001 discount path clean.
  2. Link the two Kestrel payments to one invoice.
  3. Net cash $24,106.18 = face. Discount was a timing siphon of $482.12 for 14 days plus a books bounce.
  4. July true-up initiator USR-VM-04.
- **expected_finding:** RELATED_PARTY_REMITTANCE | $482.12 discount clawback on INV-KIS-0618 | PAY-KIS-DISC, PAY-KIS-GROSS-BAL, INV-001 untouched
- **must_not:**
  - Do not claw back INV-001.

### ADV-AP-012 — September invoice for October service

- **domain:** `ap`
- **stealth:** 2
- **span:** 2026-09-30
- **storyline:** `SL-ADV-ORBIT`
- **preexisting_state:** INV-OIC-PREBILL $15,000.00 dated 2026-09-30, service_period 2026-10-01 to 2026-12-31, expensed immediately to 6000 not prepaid. Inverse of the prepaid that never expenses.
- **plant_objects:**
  - `ap_invoices:INV-OIC-PREBILL`
  - `close/prepaids (missing this item)`
  - `gl:6000-Operating`
  - `vendor_master:VEND-OIC-01`
- **how_it_hides:** Expense in September for Q4 service pulls opex forward, useful if someone later needs a cookie-jar. Small vs $180,000 prepaid. Easy miss.
- **detective_path:**
  1. Read service_period on the invoice PDF.
  2. Should be PRE or 1220, not 6000 in September.
  3. $15,000.00 September opex overstated.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** PREPAID_AMORT_MISPOSTED | $15,000.00 Q4 service expensed 2026-09-30 | INV-OIC-PREBILL, VEND-OIC-01
- **must_not:**
  - Do not treat as INV-020.

### ADV-FA-002 — Bill-and-hold cage tagged as consignment

- **domain:** `prepaid-fa`
- **stealth:** 3
- **span:** 2026-09-29
- **storyline:** `SL-ADV-PINNACLE`
- **preexisting_state:** Warehouse location CAM-WH-01-CAGE-B labeled consignment_customer=Pinnacle. Inventory accounting treated it as sold. Consignment policy P-INV-001 (plant) says consignment is not a sale.
- **plant_objects:**
  - `warehouse_locations:CAM-WH-01-CAGE-B`
  - `company_policies:P-INV-001`
  - `inventory:PIN-BH SKUs`
  - `ar_invoices:INV-AR-PIN-BH-01`
- **how_it_hides:** The location label 'consignment' is visible to a Bot that reads warehouse master. Revenue still booked.
- **detective_path:**
  1. Read location.consignment_customer.
  2. Apply P-INV-001.
  3. Reverse revenue and restore 1400.
  4. Write the finding with the reason code, magnitude, and IDs. Do not use HUMAN_REVIEW as a Bot status.
- **expected_finding:** BILL_AND_HOLD | consignment cage vs $2,400,000.00 sale | CAM-WH-01-CAGE-B, P-INV-001, INV-AR-PIN-BH-01
- **must_not:**
  - Do not delete the cage to hide goods.

### ADV-MIX-008 — Four storylines in one two-hour sim

- **domain:** `mixed`
- **stealth:** 5
- **span:** 2025-04 → 2026-09
- **storyline:** `SL-ADV-KESTREL`
- **preexisting_state:** A judge path that must remain plantable: (1) TXN-2026-09-015 $12.40 as 0.1 percent residual, (2) EMP-8891 ghost, (3) VEND-KIS-01 related party, (4) 1300 fake affiliate. All preexisting on August books. Agents onboard onto them.
- **plant_objects:**
  - `bank:TXN-2026-09-015`
  - `payroll_register:EMP-8891`
  - `vendor_master:VEND-KIS-01`
  - `gl:1300-Due-From-Affiliate`
  - `close/tasks:TASK-CASH`
  - `close/tasks:TASK-BS`
  - `close/tasks:TASK-PREPAID`
- **how_it_hides:** None is a billboard. Each naive match still works. The sabbatical means September did not run Nadia's plugs, so cash and prepaid and 1030 parks are more visible than August was.
- **detective_path:**
  1. Start with close blockers (cash $12.40, optional prepaid GL, optional 1030 park).
  2. Rate-test the $12.40.
  3. Headcount vs register.
  4. Vendor address vs employee home.
  5. Affiliate legal-entity test.
- **expected_finding:** MIXED_SABBATICAL_SURFACE | $12.40 + $146,309.45 + $187,412.18 + $4,851,220.00 | TXN-2026-09-015, EMP-8891, VEND-KIS-01, 1300
- **must_not:**
  - Do not force all four into the 10-minute script. 10-minute keeps INV-001 clean, INV-017 fee, $12.40 block. 2-hour opens the rest.
  - Do not name fraud in operational files.
- **demo_beat:** 10-minute: close blocked on $12.40. 2-hour: the $12.40 is a thread, and three other quiet holes exist.


## Handoff to data-refinement agent

Audience: the next Cursor session that plants books. This section is a procedure.

### Privacy

1. Keep this markdown and `adversarial-scenarios.index.json` under `.cfo-v2/office/sessions/`.
2. Add a hidden key section `adversarial_holdout` to `data/demo/expected_results.json`. Do not merge it into `audit_findings`.
3. Block operational reads of `expected_results.json`, this catalog, and the index. Same rule as the current answer key.
4. Do not write reason codes, storyline IDs, or the word fraud into operational files.
5. Do not set `unusual=true` on the new vendors.
6. Do not use Bot status `HUMAN_REVIEW`. Use `EXCEPTION_OPEN` or `CLOSE_BLOCKED`.

### Ordered plant sequence

1. Expand chart of accounts and legal-entity register (Maximor Demo Corp only). Do not add Maximor EU BV as a real entity.
2. Rescale P&L, cash, AP, AR, payroll, and bank volume to the table above. Update `sample_data/pnl.py`.
3. Keep surviving plot IDs and loud decoys in place.
4. Add employee_master, user_map, payroll_register, payroll_direct_deposit, badge_access, it_assets, org_chart, facilities_registry, vendor_bank_history, cycle_counts, warehouse_locations, legal_entity_register.
5. Plant identity bible people, vendors, and customers.
6. Plant SL-ADV-RESIDUAL first so TXN-2026-09-015 stays the close blocker and gains a true explanation.
7. Plant SL-ADV-KESTREL (vendor master, POs, GRs, invoices, mixed ACH) against 11 months of MRO traffic.
8. Plant SL-ADV-HALYARD on the densified payroll register. Rescale `PR-2026-10-02` / `ACT-PAYROLL-HIGH`.
9. Plant SL-ADV-ORBIT extra prepaids and FA-OIC-IMPL. Do not break PRE-SFT-001, PRE-INS-001, FA-DELL-001.
10. Plant SL-ADV-LAPPING remittance vs application mismatches. Keep PAY-001 clean. Keep INV-AR-014 identity.
11. Plant SL-ADV-PINNACLE September 29–30 revenue. Keep the loud GM cost drivers.
12. Plant SL-ADV-PROCESSOR connected account inside the Stripe sim. Keep po_1MaximorFees / Refunds / Disputes identities. Payout still equals bank.
13. Plant SL-ADV-MERRIMACK 1300 balance, JE pairs, and bank wires. No vendor row required.
14. Plant SL-ADV-BRIGHTLINE address and EIN pair.
15. Plant SL-ADV-CAMBRIDGE bank transposition and CAM invoices. Lease CTR-CAM-001.
16. Plant SL-ADV-CLOSECOSMETIC parks, late August JE without post_close flag, Lenovo rollout.
17. Plant SL-ADV-FREIGHT accessorials and two mixed ACH files. Keep TXN-FRT-SEP-001 and TXN-2026-09-008.
18. Write `adversarial_holdout` expected findings from the index.
19. Densify remaining clean traffic so adversarial rows are a minority.
20. Validate that INV-001 still three-way matches, INV-017 is still FEE_NETTED, and TXN-2026-09-015 is still unmatched at $12.40.

### Files you will edit

Under `.cfo/data/demo/` (and generators in `.cfo/sample_data/`):

- `canonical/vendors.json`, `canonical/journal_entries.json`, `canonical/vendor_payments.json`
- `invoices.json`, `historical_invoices.json`, `later_invoices.json`, `purchase_orders.json`, `goods_receipts.json`
- `ar_invoices.json`, `ar_payments.json`, `ar_customers.json`, `ar_precedents.json`
- `cash_recon/bank_statement.json`, `cash_recon/ledger.json`, `cash_recon/balances.json`
- `reporting/payroll.json`, `reporting/actuals.json`, `reporting/ledger_seed.json`, `reporting/forecast_lines.json`, `reporting/forecast_weeks.json`, `reporting/balances.json`, `reporting/budget.json`, `reporting/chart_of_accounts.json`
- `close/prepaids.json`, `close/fixed_assets.json`, `close/journal_entries.json`, `close/source_documents.json`, `close/tasks.json`, `close/identity_links.json`
- `audit/vendors.json`, `audit/invoices.json`, `audit/payments.json`, `audit/bank.json`, `audit/ledger.json`, `audit/approvals.json`, `audit/journal_entries.json`, `audit/reconciliations.json`
- `integrations/stripe/*` and `.cfo/data/simulations/stripe/*` (sim only)
- `vendor_contracts.json`, `company_policies.json` (add P-REV-001, P-INV-001, P-CASH-UNDEP-AGE, CTR-CAM-001, CTR-STRIPE-001)
- `expected_results.json` hidden section `adversarial_holdout` only
- new densify files listed in step 4

Also update inbox fixtures only if you add MSG-PIN-HOLD-01 as a simulated spec. Do not turn on Gmail.

Do not edit `.cfo-v2/office/computer/harness/**`. Do not edit Operator-workspace.

### What to keep private

- This catalog, the JSON index, `adversarial_holdout`, Stripe `evaluation/ground_truth.json`, and any `answer_key/`.
- Insider names may appear on employee_master (they are employees). Do not tag them `adversarial` or `fraud`.
- Vendor change memos stay boring: `normalize ACH formatting / strip spaces`.

### Definition of done for the plant

- A naive AP three-way match still approves Kestrel, NLF, Brightline Studio, CAM, and Lenovo rollout invoices.
- A naive payout-to-bank match still passes Stripe.
- A naive AR batch rec still matches lockbox totals.
- September close is still blocked on TXN-2026-09-015.
- INV-001, INV-017, FEE-729103 are still clean/explained.
- Hidden key lists every ADV-* reason code, magnitude, and IDs from the index.
- At least 15 stealth-5 plants are actually in the registers, not only in this document.

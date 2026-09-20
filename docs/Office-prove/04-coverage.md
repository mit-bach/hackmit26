# Coverage

Tick these rows in `logs/runs/<instance>/coverage.md` as procedures observe them. Do not invent a second inventory. Disk on the selected instance wins if counts moved after compile.

Bare minimum for the operation: every row has RUNS, HONEST-EMPTY, SKIP-with-reason, or BLOCKED-CORRECT. Demo-ready adds INTENDED on the pipe rows in P2–P5 and P8.

---

## A. Standing Bots

Live Roster (15). Instance snapshots may add `world`. Tick bind + one terminal Handle without tool throw.

| Slug | Class | P0 bind | One Handle | Home procedure |
| --- | --- | --- | --- | --- |
| email | Source | | | P1 |
| stripe | Source | | | P1, P4 |
| bank | Source | | | P1, P4 |
| books | Source | | | P1, P3, P5 |
| ap | Operator | | | P2 |
| pay | Operator | | | P2 |
| apply | Operator | | | P3 |
| collect | Operator | | | P3 |
| cash | Operator | | | P4 |
| close | Operator | | | P5 |
| story | Operator | | | P5 |
| ctl-pay | Verifier | | | P2, P3 write-off |
| ctl-cash | Verifier | | | P3 apply, P4 |
| ctl-books | Verifier | | | P5 |
| audit | Assurance | | | P5 |
| world | Source, disputed | | | P1, P3. SKIP if off Roster. Do not silently add |

---

## B. Routines

`client.json` `autoRoutines` is false. Prove fires them.

| Routine | Owning Bot | Profile in prompt | Procedure |
| --- | --- | --- | --- |
| weekly-pay-run | pay | schedule | P2 |
| daily-aging | collect | chase | P3 |
| month-end | close | coordinate | P5 |
| period-story | story | flux then self-Wake | P5 |
| post-close-assurance | audit | interpret then report | P5 |

---

## C. Handle edges

From live `cfo/handle-map.json`. Tick when a Harness Handle file exists from → to with that `when`, and complete or reject is terminal without throw.

| from | when | to | profile | Procedure |
| --- | --- | --- | --- | --- |
| email | bill | ap | prepare | P1, P2 |
| email | remittance | apply | apply | P1, P3 |
| stripe | deposit | cash | match | P1, P4 |
| stripe | charges | apply | apply | P1, P3 |
| stripe | waterfall_break | ctl-cash | review-rec | P4 |
| bank | line | cash | match | P1, P4 |
| books | bill | ap | prepare | P1, P2 |
| books | open-invoice | collect | chase | P1, P3 |
| books | lock-state | close | coordinate | P5 |
| ap | approve | ctl-pay | review-match | P2 |
| ap | payable | pay | schedule | P2 |
| ap | unreceived | close | coordinate | P2, P5 |
| pay | release | ctl-pay | review-pay | P2 |
| pay | wires | cash | match | P2, P4 |
| apply | identified-deposit | cash | match | P3, P4 |
| apply | ambiguous | ctl-cash | review-apply | P3 |
| collect | write-off | ctl-pay | review-pay | P3 |
| cash | sign-off | ctl-cash | review-rec | P4 |
| cash | trusted | close | coordinate | P4, P5 |
| close | treatment | ctl-books | review-treatment | P5 |
| close | assets-treatment | ctl-books | review-assets | P5 |
| close | bs-treatment | ctl-books | review-bs | P5 |
| close | lock | ctl-books | lock | P5 |
| close | pack-story | story | flux | P5 |
| close | pack-audit | audit | interpret | P5 |

Mailbox send is not a row here until AR repair adds a collect → world (or equivalent) edge. P3 ticks send in the simulated transport even if handle-map has not grown. If you add an edge, compile/grain first. Do not add a row by editing this table alone.

---

## D. Computer skills (33)

Kernel has 35. Kernel-only `synthetic-finance-scenario-design` and `cross-ledger-data-consistency` stay off grain Bots. Tick P6 when the skill name appears in the Bot’s loaded prompt/skill intersect **and** that Bot completed a turn without throw. INTENDED for a skill means remainder steered, not Kernel replay only.

| Skill | Assigned Display names (live assignments.py) | Wearer Bots | Home |
| --- | --- | --- | --- |
| inbox-triage | Finance Inbox Agent | email | P1 |
| invoice-source-identification | Finance Inbox, Email Invoice, Procurement, Vendor Portal, Employee, Physical Mail | email, books | P1 |
| invoice-field-interpretation | Finance Inbox, Email Invoice, Vendor Portal, Employee, Physical Mail | email | P1 |
| superseded-document-handling | Finance Inbox, Email Invoice, Vendor Portal, Employee, Physical Mail, AP Preparer, Exception Investigator | email, ap | P1, P2 |
| bank-charge-invoice-discovery | Bank/Card Discovery Agent | bank | P1 |
| three-way-match-analysis | AP Preparer, Exception Investigator, AP Reviewer, AP Approver, AP Audit | ap, ctl-pay | P2 |
| ap-exception-investigation | Exception Investigator, AP Reviewer, AP Approver, AP Audit | ap, ctl-pay | P2 |
| payment-prioritization | Payment Scheduler, Payment Audit | pay, ctl-pay | P2 |
| early-payment-discount-evaluation | Payment Scheduler, Payment Audit | pay, ctl-pay | P2 |
| cash-application | Cash Application Agent, Cash Application Reviewer | apply, ctl-cash | P3 |
| ar-collections-policy | Collections Agent | collect | P3 |
| cash-reconciliation-method-selection | Cash Reconciliation Preparer, Cash Reconciliation Reviewer | cash, ctl-cash | P4 |
| bank-reference-interpretation | Cash Reconciliation Preparer, Cash Exception Investigator | cash | P4 |
| reconciliation-evidence-validation | Preparer, Investigator, Reviewer cash rec | cash, ctl-cash | P4 |
| reconciliation-exception-investigation | Cash Exception Investigator, Cash Reconciliation Reviewer | cash, ctl-cash | P4 |
| accrual-evidence-evaluation | Accrual Agent | close | P5 |
| accrual-method-selection | Accrual Agent | close | P5 |
| prepaid-expense-accounting | Prepaid Preparer, Prepaid Reviewer | close, ctl-books | P5 |
| fixed-asset-depreciation | Fixed Asset Preparer, Fixed Asset Reviewer | close, ctl-books | P5 |
| balance-sheet-reconciliation | BS Preparer, BS Reviewer | close, ctl-books | P5 |
| month-end-close-coordination | Close Manager | close | P5 |
| month-end-close-review | Month-End Close Reviewer | ctl-books | P5 |
| prior-period-precedent | many reviewers + investigator + accrual + prepaid + lock | ap, cash, close, ctl-* | P2, P4, P5 |
| financial-variance-analysis | Variance Analysis Agent, Reporting Reviewer Agent | story | P5 |
| board-financial-reporting | Board Reporting Agent, Reporting Reviewer Agent | story | P5 |
| cash-forecasting | Cash Forecast Agent, Forecast Reviewer Agent | story | P5 |
| ar-cash-forecasting | Cash Forecast Agent, Forecast Reviewer Agent | story | P5 |
| forecast-vs-actual-interpretation | Forecast Variance Agent, Forecast Reviewer Agent | story | P5 |
| audit-sampling-interpretation | Auditor Agent | audit | P5 |
| control-testing-interpretation | Auditor Agent | audit | P5 |
| reconciliation-reperformance-review | Auditor Agent | audit | P5 |
| segregation-of-duties-interpretation | Auditor Agent | audit | P5 |
| audit-finding-writing | Audit Report Agent | audit | P5 |

P6 remainder Wakes exist for intake Profiles that a month instance may not hit: Vendor Portal, Employee Submission, Physical Mail, EDI, ERP. EDI and ERP have empty skill tuples in assignments. Their Catalog ops still need P7.

---

## E. Catalog ops (89 live)

`evalOnly`: `audit.tools.get_audit_ground_truth` only. Operational prove must show that op is **not** callable. Tick FORBIDDEN-OK.

Expected extras after AR repair (instance catalog had 94): `inbox.tools.send_office_outbound`, `inbox.tools.list_world_personas`, `inbox.tools.list_inbox_threads`, `inbox.tools.list_inbox_messages`, `inbox.tools.get_inbox_thread`. If live compile still has 89, P3 mailbox steps HARD/SKIP on T3. Do not tick them from a stale instance snapshot.

Wearer = a Display name whose Grant lists the op. Call must come from a Bot that wears that Display name this turn (one Profile).

### Accrual (12) — close / accrue

`compute_accrual_estimate`, `create_accrual`, `get_current_period_invoices`, `get_estimate_candidates`, `get_expected_invoices`, `get_goods_receipts`, `get_open_accruals`, `get_purchase_orders`, `get_vendor_contract`, `get_vendor_invoice_history`, `get_vendor_usage`, `reconcile_accrual_with_invoice`

`create_accrual` stays on accrue only. Other close Profiles calling it is HARD SoD.

### AR (6) — apply, collect

`get_ar_close_snapshot`, `get_ar_customer`, `get_ar_precedents`, `get_cash_application_facts`, `get_collection_candidates`, `get_collection_invoice_facts`

### Audit (10)

Operational: `get_audit_approvals`, `get_audit_invoices`, `get_audit_journals`, `get_audit_payments`, `get_audit_period`, `get_audit_policy`, `get_audit_vendors`, `get_operational_decisions`, `get_planted_reconciliations`

Forbidden: `get_audit_ground_truth`

### BS rec (3) — close / bs, ctl-books review-bs

`get_reconciliation_packet`, `list_period_reconciliations`, `list_reconciling_items`

### Cash recon (5) — cash, ctl-cash

`get_bank_transaction`, `get_candidate`, `get_fee_evidence`, `get_ledger_entry`, `get_match_candidates`

### Fixed assets (4) — close / assets

`get_capital_candidates`, `get_depreciation_schedule`, `get_fixed_asset`, `list_fixed_assets`

### Inbox (8 live) — email, world

`classify_inbox_message`, `compose_counterparty_message`, `dispatch_inbox_action`, `extract_inbox_invoice`, `get_inbox_attachment`, `get_inbox_message`, `reply_in_thread`, `send_inbox_message`

World/Counterparty wears compose/send/reply. Finance Inbox wears classify/dispatch. Do not grant World the finance send if AR repair split them. P3 checks that.

### Invoice ingestion (18) — email, books, bank Profiles

`find_related_invoice`, `get_bank_transaction`, `get_edi_document`, `get_email`, `get_email_attachment`, `get_employee_submission`, `get_erp_invoice`, `get_mail_document`, `get_procurement_record`, `get_vendor_portal_document`, `list_bank_transactions`, `list_edi_documents`, `list_email_candidates`, `list_employee_submissions`, `list_erp_invoice_records`, `list_mail_documents`, `list_procurement_records`, `list_vendor_portal_documents`

### Memory (1)

`memory.tools.get_decision_memories` — wearer per Grant. Tick if any granted Bot calls it without throw. T10 INTENDED is later.

### Prepaid (4) — close / prepaid

`get_prepaid`, `get_prepaid_schedule`, `get_prepaid_treatment_candidates`, `list_prepaids`

### Reporting (6) — story

`get_cash_forecast`, `get_forecast_checks`, `get_forecast_snapshot`, `get_period_metrics`, `get_variance_facts`, `get_variance_trace`

### Scheduling (4) — pay, ctl-pay review-pay

`get_approved_pool`, `get_cash_position`, `get_payment_candidates`, `get_treasury_policies`

### AP tools (8) — ap, ctl-pay review-match

`tools.find_duplicate_invoices`, `tools.find_relevant_policies`, `tools.get_case_evidence`, `tools.get_company_policies`, `tools.get_goods_receipt`, `tools.get_invoice`, `tools.get_prior_cases`, `tools.get_purchase_order`

P7 is the remainder sweeper when a month instance never called an op. Forced Wake is RUNS, not INTENDED.

---

## F. Empty Grants (honest vs costume)

Live `grants.json` empty `ops: []`:

| Display name | Honest? | Rule |
| --- | --- | --- |
| Close Manager | maybe | Coordinate via ready_tasks + self-Wake. HONEST-EMPTY if no office-live claim that it calls ops |
| Month-End Close Reviewer | no, if you claim lock office-live | P5 / 05 Close must give lock ops or stop the claim |
| Audit Report Agent | no, if you claim report office-live | P5 / 05 Close |
| AP/AR Sample Data Agent | yes | Off floor |
| Cash Recon Sample Data Agent | yes | Off floor |
| Close Sample Data Agent | yes | Off floor |
| Audit Controls Sample Data Agent | yes | Off floor |
| Reporting Forecasting Sample Data Agent | yes | Off floor |
| Stripe payout Display `""` | no | P0/P1 HARD bind or HONEST “stripe not office-live” |

---

## G. Pipe INTENDED rows

Tick from P2–P5 and P8, not from pytest.

| Pipe | Bare min RUNS | Demo-ready INTENDED |
| --- | --- | --- |
| Intake | Email classifies; ignore quote/injection without throw | Bill Handle ap with Kernel id `get_invoice` finds; remittance Handle apply; World round-trip if bound |
| AP | get_invoice + HOLD/APPROVE packet without throw; ctl-pay terminal | Real bill (not INV-S12); must_hold wins; weekly-pay-run Handle ctl-pay; wires identified to cash executed false |
| AR | apply facts ops; collect candidates ops | Apply first; SEND_* in mailbox; write-off to ctl-pay |
| Cash | get_match_candidates without throw | Identifier trust; `$12.40` unexplained; Stripe honest |
| Close | month-end Wake without throw; gates still BLOCKED | Computer runs/; UNLOCKED story; audit no ground truth; no CLOSED |

---

## How to tick

Copy the relevant table into `logs/runs/<instance>/coverage.md`. Fill the empty class column with INTENDED / RUNS / SOFT / HARD / SKIP / HONEST-EMPTY / BLOCKED-CORRECT. Link the step id. One op may tick on many instances. The operation-level rollup is `logs/ROLLUP.md` after all procedures.

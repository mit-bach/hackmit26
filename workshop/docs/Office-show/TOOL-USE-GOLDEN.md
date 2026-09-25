# Tool use on the golden month

Instance `golden-20260920-r1`. Source: `cfo/kernel.log.jsonl` (195 rows) and each Bot’s `harness/bots/*/pi-rpc.jsonl` (671 tool starts). Catalog: `cfo/catalog.json` (101 ops). Grants: `cfo/grants.json`.

This is the backend a founder can ask about. The agents talked. The Python tools are what make a number reliable. On this tape the tools were a thin slice of the turns, and most of them only read.

## What “your tools” are

The Catalog is the finance API. A Bot may call an op only if its Grant lists it. The kernel log is the record of those calls. Pi also has its own tools (`bash`, `read`, `write`, `ask_bot`). Those are not finance tools. They let the model open files and run shell.

Of 101 Catalog ops:

| Kind | Count | What it does |
| --- | --- | --- |
| `read` | 96 | Return a record. They do not post a journal. |
| `write-local` | 5 | `create_accrual`, `reconcile_accrual_with_invoice`, `send_inbox_message`, `reply_in_thread`, `send_office_outbound` |
| `evalOnly` | 1 | `audit.tools.get_audit_ground_truth`. Correctly absent from operational grants. Never called. |

`inbox.tools.dispatch_inbox_action` is labeled `read` and still creates bills. That label is wrong. On this tape it ran 24 times and minted `ING-006` from injection mail.

There is no Catalog op that posts a match, fills the approved pool, or marks a period CLOSED. Those decisions are either a host routine in Python, or a JSON file the model writes.

## What actually ran

Kernel log, excluding nothing:

| | |
| --- | --- |
| Calls | 195 |
| Distinct ops | 44 of 101 |
| Ok | 190 |
| Failed | 5 |
| Granted ops never called | 55 of 98 |

Calls by Bot:

| Bot | Kernel calls | What they were |
| --- | --- | --- |
| email | 74 | Classify, dispatch, read, send. Half the log. |
| world | 23 | Send and read mail. One reply. |
| cash | 20 | Bank line, candidates, fees. Four candidate lookups failed. |
| ap | 15 | Invoice, PO, GR, duplicates, policies. |
| ctl-cash | 14 | Same cash reads, as reviewer. |
| stripe | 8 | Three payout ops. All three payout tools ran. |
| ctl-pay | 6 | Case evidence and invoice reads. |
| story | 5 | Variance facts and period metrics. |
| apply | 4 | Cash-application facts. |
| pay | 4 | Pool, candidates, policies, cash position. Pool came back empty. |
| bank | 4 | List and get bank lines. |
| audit | 4 | Period, policy, planted reconciliations, operational decisions. |
| books | 2 | ERP list and get. |
| close | 1 | `kernel.health`, **forbidden**. |
| collect | 0 | No finance tool. |
| ctl-books | 0 | No finance tool. |

Pi tool starts on the same Computer (671):

| Tool | Starts | Role |
| --- | --- | --- |
| `bash` | 248 | Shell. 56 of them are `python3` one-liners over JSON. 134 are `cat` / `ls` / `rg`. |
| `call_connected_tool` | 163 | The Grant door. This is the finance API. |
| `read` | 130 | Open a file, including skill files and JSON the host already wrote. |
| `write` | 27 | Model-authored JSON packets. |
| `ask_bot` / `bot_ask` | 29 | Peer speech. |
| `search_connected_tools` | 23 | Look up the Catalog, then sometimes skip the call. |
| `memory_write` / `memory_read` | 13 | Harness memory, not `memory.tools.get_decision_memories`. |

`call_connected_tool` is 163 of 671 starts, about a quarter. `bash` plus `read` plus `write` is 405. Collect’s entire turn is two Pi tools: `ask_bot` and `message_operator`. ctl-books is twelve starts and none of them is the Grant door. The 95% / 5% guess is the right shape. The measured split on this tape is closer to three file-or-shell calls for every finance call, and many finance calls are reads.

## Ops that ran, and how

Inbox (97 calls). This is the only domain the office used hard.

- `classify_inbox_message` 20, `dispatch_inbox_action` 24, `send_inbox_message` 19, `get_inbox_message` 19, `extract_inbox_invoice` 8.
- `send_office_outbound` 1 and `reply_in_thread` 1. That pair is the single World exchange.
- `compose_counterparty_message` and `get_inbox_attachment` were granted and not called.

AP reads (19 calls under `tools.*`). `get_invoice` 3, `get_case_evidence` 10, `get_purchase_order` 1, `get_goods_receipt` 1, `find_duplicate_invoices` 2, `get_company_policies` 1, `get_prior_cases` 1. `find_relevant_policies` was not called. Enough to concur `INV-001`. Not enough to walk the vendor master.

Cash reads (33 calls). Every cash op in the Catalog was called at least once: bank transaction, ledger entry, fee evidence, pipe identifier, candidate, match candidates. Helios used fee evidence. Northstar stayed unmatched. Four `get_match_candidates` calls returned `not_found` (cash three times, ctl-cash once). The tool looks up a case file under `runs/cash_recon/cases/`. A missing case id is a hard error, not an empty list. The Bots kept going by reading other files.

Pay (6 calls). `get_approved_pool`, `get_payment_candidates`, `get_treasury_policies`, `get_cash_position` all ran. The pool was empty, so the reliable tool told the truth and the pay chapter had nothing to schedule. Nothing in the Catalog writes that pool when ctl-pay concurs.

Stripe (8 calls). `list_processor_payouts`, `get_processor_payout`, `get_payout_waterfall`. All three Stripe grants ran. No invoice candidates. Deposits were matched by later cash reads, not by a Stripe write.

Audit (4 calls). `get_audit_period`, `get_audit_policy`, `get_planted_reconciliations`, `get_operational_decisions`. The Kernel still wrote `runs/audit/2026-09-20260920T153114Z.json` with the loud `AUD-*` findings. The population tools were not used: `get_audit_vendors`, `get_audit_payments`, `get_audit_journals`, `get_audit_invoices`, `get_audit_approvals`. Ground truth was not loaded. That part is correct. The sample never opened payroll or the vendor bank fields.

Story (5 calls). `get_variance_facts` 4, `get_period_metrics` 1. Forecast tools were not called. That matches “do not forecast from unreconciled cash.” `get_variance_trace` was not called, so the variance explanation has facts and no trace.

Books (2 calls). `list_erp_invoice_records`, `get_erp_invoice`. Company discovery besides that was `bash` and `python3` over `data/`.

## Ops that should have run and did not

These are granted, in the Catalog, and relevant to the stories on this tape.

| Gap | Ops not called | Why it matters |
| --- | --- | --- |
| Close reviewer | `close.tools.get_close_gates`, `close.tools.get_close_packet` | The skill tells ctl-books to call both. It used Pi `read` on `workspace/close/2026-09/gates.json` instead. The file was already written by the month-end host. The Grant door never saw the lock. |
| Accruals | all 12 `accrual.tools.*`, including `create_accrual` | Pack status says accruals COMPLETE. The kernel log has zero accrual calls. Harbor’s $4,650 was not booked through the tool. The two write ops in the whole accrual module never ran. |
| Prepaids, assets, balance sheet | all `prepaid.tools.*`, `fixed_assets.tools.*`, `bs_recon.tools.*` | Same pattern. Host JSON says COMPLETE or BLOCKED. No Bot called the tools. |
| Collections | `get_collection_candidates`, `get_collection_invoice_facts` | Collect made zero kernel calls. `get_cash_application_facts` ran (apply), five times. Nobody loaded the chase list. |
| Audit populations | `get_audit_vendors`, `get_audit_payments`, `get_audit_journals`, `get_audit_invoices` | These are the reads that could see a ghost employee or a related-party vendor. The run used planted reconciliations instead. |
| Memory | `memory.tools.get_decision_memories` | Harbor used Harness `memory_write` / `memory_read` (2 reads, 11 writes across Bots). The finance memory tool was idle. |
| Other inboxes | EDI, portal, employee submission, physical mail, procurement list/get | Granted to source agents. The tape only dumped the finance inbox. |
| Counterparty compose | `compose_counterparty_message` | World replied with `reply_in_thread` once and never composed a new outside message. |

`kernel.health` from close failed with `forbidden`. Close Manager’s grant list is empty on purpose. The call is the model poking a host op it is not allowed to wear. It did not change the books.

## What the debugging chat changed

Port 8801, `.cfo-v2/prove-fork/`. Its kernel log on `prove-20260920-fork-month-r2` is 82 lines, 17 ops, 0 failures, almost all inbox classify and dispatch, plus a few invoice reads. It has not walked cash, close, audit, or accruals.

File diff against the live kernel: `inbox/classify.py` and `inbox/dispatch.py` only. `cash_recon/tools.py` and `close/tools.py` match the live copies. The patch forces prompt injection to `REJECT_UNSAFE_REQUEST` so dispatch does not mint a bill. That is a real tool fix. It is not on `.cfo/` yet, so golden still has the mint. No other tool module was edited.

## What to tell the founder

The reliable layer is the Catalog, and this office mostly did not live there.

1. Ninety-six of 101 ops are reads. The five writes do not include “match this bank line,” “approve this bill into the pay pool,” or “lock the month.” If a number changed, it changed in host Python or in a file the model wrote. The kernel log cannot show a match decision because no tool records one.

2. On the one month you can play, 44 ops ran. Email is half the log. Collect and the close reviewer called none. Accrual, prepaid, assets, and balance-sheet tools called none, while the close pack says several of those tasks are complete. The host did the work beside the agents. The agents then read the JSON.

3. The failures you can point at are small and specific. Four candidate lookups missed a case file. One health call was refused. The expensive failure is a tool that succeeded: `dispatch_inbox_action` created a bill from injection mail. The fork fixes that path and has not retested the rest.

4. ctl-books is the design in one picture. The skill says call `get_close_gates`. The Bot opened the file with `read`. The conclusion (REJECT_CLOSE, $12.40 still open) happens to be right. The tool that was supposed to be the authority was skipped.

5. Advice that matches the code: put the decision in the tool (match, pool insert, accrual post, gate read), log it, and stop treating `bash` over `data/*.json` as a substitute. Until that is true, a long agent transcript is not evidence that the books were touched by the backend.

# Run log — prove-20260920-fork-month-r2

- Created: 2026-09-20T15:54:42Z
- Procedure(s): P1 replay after T12 patch on copied Kernel
- Serve URL: http://127.0.0.1:8801/
- Computer path: `.cfo-v2/prove-fork/instances/prove-20260920-fork-month-r2`
- Patch: `.cfo-v2/prove-fork/.cfo/inbox/classify.py` + `dispatch.py`. Live `.cfo/inbox` unchanged.
- Fake workers: no
- Sidecar: 61151

## Sequence of steps

| Step | Class | T | Bot | Profile | Ops | Handle | Note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1-inject | RUNS | | world (sidecar RPC) | vendor | inbox.tools.send_inbox_message | | 15 fixtures. Not MSG-S12 |
| P1-S01 | INTENDED | | email | inbox | list_inbox_threads, get_inbox_message | h_0e7632f3-0f27-4982-9ca4-dce9b301f746 | 15 threads this Computer |
| P1-S02 | SOFT | T6 | email | inbox | classify, dispatch | h_2ebe6fba-92ea-435b-b866-df077e8ed80c | MSG-ACME-INV-001 VENDOR_INVOICE; ATTACH BUSINESS_DUPLICATE INV-001; forwarded_to_ap false; no AP Handle. Kernel duplicate reason stands |
| P1-S03 | INTENDED | | email | inbox | classify, dispatch | h_03703efe-f629-4ced-8c21-75cafad96ff0 | MSG-INBOX-003 CREATED ING-002; Handle ap h_5e862b97 HOLD material_amount_mismatch. Email did not HOLD |
| P1-S04 | INTENDED | | email | inbox | classify, dispatch | h_d7ce41f6-c9d5-46cf-95a5-24b75b4f17e8 | MSG-INBOX-004 CREATED ING-003; Handle ap h_fc97e5d1 HOLD missing_po |
| P1-S05 | INTENDED | | email | inbox | classify, dispatch | h_a478c2b3-ba95-4575-a273-0e2c9c3c267a | MSG-INBOX-008 CONTRACT_OR_QUOTE IGNORE; no AP Handle |
| P1-S06 | INTENDED | | email | inbox | classify, dispatch | h_02052088-f13c-4328-b90c-eb88d5d08604 | MSG-INBOX-007 VENDOR_STATEMENT IGNORE; no mint |
| P1-S07 | INTENDED | | email | inbox | classify, dispatch | h_9b52d701-2acb-4e73-a59a-98e1b336af9d | MSG-INBOX-010 NON_FINANCE IGNORE; no mint |
| P1-S08 | INTENDED | | email | inbox | classify, dispatch | h_98f5a697-2062-4530-ac95-fd74bfe0b171 | MSG-INBOX-014 REJECTED; no AP Handle; no Kernel mint |
| P1-S09 | INTENDED | | email | inbox | classify, dispatch | h_759ec75c-6dcb-41e4-b06b-8f320df1c15f | MSG-INBOX-011 NEEDS_INFORMATION; invoice_id null; outbound MSG-INBOX-011-OUT |
| P1-S16 | SOFT | T6 | world | vendor | reply_in_thread | h_a0aa7019-ee75-4e83-842f-961098df76e0 | first try failed: assistant text is not the pair thread |
| P1-S16b | INTENDED | | world | vendor | reply_in_thread, ask_bot | h_6ec195e2-5054-4328-8de0-45cb9d73b23f | THR-incomplete MSG-INBOX-011R ACM-INBOX-5005 USD 1245.00; email h_1e419451 classified VENDOR_INVOICE ING-006; world did not dispatch |
| P1-S11 | INTENDED | | email | inbox | classify, dispatch | h_eae58cb3-b4c3-4f25-bd9a-9fff5155bcd9 | MSG-INBOX-015 UNKNOWN_VENDOR CREATED ING-004; no vendor master; Handle ap h_1b8778d1 HOLD. Prior transport fail h_7f2d9979 not a Kernel throw |
| P1-S12 | INTENDED | | email | inbox | classify, dispatch | h_1ee003cf-861d-4db7-a73f-a57cc3941c47 | MSG-INBOX-016 CREDIT_MEMO UNSUPPORTED; invoice_id null; not in pay-run |
| P1-S13 | INTENDED | | email | inbox | classify, dispatch | h_e24ba9f2-2956-4c10-809f-9d854d75de78 | MSG-INBOX-018 PARSE_FAILURE; no invented invoice |
| P1-S14 | INTENDED | | email | inbox | classify, dispatch | h_29e7e1dc-9bf6-4034-9483-3a91e9602aa7 | MSG-INBOX-019 CUSTOMER_REMITTANCE ROUTED; Handle apply h_46dfddfa; no AP bill |
| P1-S15 | INTENDED | | email | inbox | classify, dispatch | h_70627919-307e-40ca-a83c-9e9c2af8b047 | MSG-INBOX-002 body bill CREATED ING-005; Handle ap h_28d4cb35 HOLD |
| P1-S17 | INTENDED | | books | erp-invoice | list ERP | h_f6e32882-9a07-4371-90d5-ce4fe6a8feee | NS-4410 landed; Handle ap; get_invoice INV-001 APPROVE-shaped. ctl-pay not sent yet (P2) |
| P1-S18 | SKIP | | books | | | | deferred: do not Handle collect until P3 apply drains |
| P1-S19 | INTENDED | | bank | card | list_bank_transactions, pack lines | h_18123e87-eee2-472c-9e85-945c73f2d0d0 | ingestion list count 0; operating pack 219 lines; Handle cash; TXN-2026-09-015 residual 12.40 not cleared |
| P1-S20 | INTENDED | | stripe | payout | list/get payout, waterfall | h_ca83d954-9f54-47d0-b406-fbeac119b9ca | three payouts; invoice_candidates 0; no AP bill |
| P1-S10 | SOFT | T6 | email | inbox | classify, dispatch | h_2ebe6fba | same row as S02: duplicate pointer to INV-001, no amount merge, no AP Handle |

## Checkpoints

See CHECKPOINT.md.

## Open holes

-

## Next action

- [x] continue this instance
- [ ] wipe
- [ ] new instance rN+1
- [ ] 05 repair agent
- [ ] skill batch edit

# Finance inbox triage — three new notes (not seeded list)

Threads from list_inbox_threads only:
1. thr-acme-acm-2026-4410
2. thr-northwind-inv-ar-001-pay-note
3. thr-fnb-stmt-2026-09-operating

## 1. Acme Supplies — msg-acme-acm-2026-4410-confirm-001

| Item | Value |
| --- | --- |
| Skill class | Vendor invoice confirmation / body invoice language |
| Auto dispatch | REQUEST_MISSING_INFORMATION (invoice_date) |
| Outbound | msg-acme-acm-2026-4410-confirm-001-OUT delivered; world vendor replied |
| Vendor reply | msg-acme-acm-2026-4410-invoice-date-001 → invoice_date **2026-09-08** |
| Fields (thread) | ACM-2026-4410, $12,450.00, PO 101, goods received, date 2026-09-08 |
| CREATE_AP | Kernel still keys off confirm msg alone → missing invoice_date; no invoice_id minted |
| Handoff | ap prepare on workspace/email/packets/acm-2026-4410-thread-ap-handoff.md → **HOLD** (get_invoice not found; AP cannot register) |
| Match/pay/close | not done |

## 2. Northwind Labs — msg-northwind-inv-ar-001-pay-note-001

| Item | Value |
| --- | --- |
| Skill class | Customer payment **commitment** (not cash sent) |
| Dispatch | RECORD_CUSTOMER_REMITTANCE / ROUTED_REMITTANCE |
| Handoff | apply on workspace/email/packets/northwind-inv-ar-001-pay-note-handoff.md |
| Apply result | **NOT applied** — unknown payment; await bank clear; no ctl-cash |
| Match/pay/close | not done |

## 3. First National — msg-fnb-stmt-2026-09-operating-001

| Item | Value |
| --- | --- |
| Skill class | BANK_NOTICE / statement availability |
| Dispatch | IGNORE (not a vendor bill) |
| Handoff | none |
| Note | $12.40 unexplained left to cash/bank-rec owners; email does not match |
| Match/pay/close | not done |

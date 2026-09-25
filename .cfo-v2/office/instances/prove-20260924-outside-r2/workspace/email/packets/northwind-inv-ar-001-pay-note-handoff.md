# Handoff to apply — Northwind payment note

- message_id: msg-northwind-inv-ar-001-pay-note-001
- thread_id: thr-northwind-inv-ar-001-pay-note
- sender: Northwind Labs <ap@northwindlabs.example>
- subject: Payment schedule — INV-AR-001
- customer: Northwind Labs (CUST-001)
- invoice: INV-AR-001
- amount: 12000.00 USD
- method: ACH
- scheduled_date: 2026-10-14

## Classification (email)

Customer payment note routed per inbox policy toward apply.
Body states payment *commitment* only — not cash already sent; apply once it clears the bank.
Not a vendor invoice. candidate null.

## Dispatch

- Kernel: RECORD_CUSTOMER_REMITTANCE / ROUTED_REMITTANCE
- target notice: inbox.notices.remittance

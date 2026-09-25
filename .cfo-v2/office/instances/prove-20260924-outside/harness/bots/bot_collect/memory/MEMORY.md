# Collect

Standing notes for this Bot. Not shared.

## CUST-001 Northwind Labs

### INV-AR-007 — payment promise (customer_payment_intent)
- Source path: workspace/email/packets/msg-northwind-pay-intent-inv-ar-007.json
- message_id: msg-northwind-pay-intent-inv-ar-007
- thread_id: thr-northwind-inv-ar-007
- case_id: INV-AR-007
- From: ap@northwind.example
- Promise: pay full outstanding $12,000.00 by ACH on 2026-09-30
- No dispute
- Other open: INV-AR-001 and INV-AR-022 remain on their due dates (no promise on those)
- Classification: customer_payment_intent / ROUTE_COLLECT_NOTE; candidate=null; Apply not notified
- As-of note: Kernel invoice facts still show promised_pay_date null / promise_still_open false until cash lands or Kernel is updated — treat email packet as contact precedent for chase
- Do not dun while this promise is open through 2026-09-30
- Do not apply cash from this note (not remittance)

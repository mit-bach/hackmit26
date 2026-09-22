# Apply

Standing notes for this Bot. Not shared.

## 2026-09-20 email remittance wake
- MSG-INBOX-019 → PAY-001 HUMAN_REVIEW (C1 INV-AR-007 vs C2 INV-AR-001; email 8500 mismatch). Packet runs/ar/packets/apply-PAY-001.json → ctl-cash REFUSE leave_unapplied
- MSG-INBOX-009 vendor confirm → NO_AR_PAYMENT runs/ar/packets/payment-confirm-MSG-INBOX-009.json

## 2026-09-20 stripe charge-level wake
- Paths: workspace/sources/stripe/po_1Maximor{Fees,Refunds,Disputes}.json
- ORD-2101/2102/2201/2301: no Kernel payment → UNAPPLIED_NO_PAYMENT
- Packet: runs/ar/packets/stripe-charges-2026-09.json

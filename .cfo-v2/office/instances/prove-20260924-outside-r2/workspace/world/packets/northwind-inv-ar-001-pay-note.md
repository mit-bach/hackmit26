# Customer inbound delivered (payment commitment)

- persona: Northwind Labs (customer CUST-001)
- sender: ap@northwindlabs.example
- message_id: msg-northwind-inv-ar-001-pay-note-001
- thread_id: thr-northwind-inv-ar-001-pay-note
- subject: Payment schedule — INV-AR-001
- recipient: ar@hackmit-cfo.example
- delivered: true
- delay_habit: on_time

Commitment (not cash applied by world):
- Invoice: INV-AR-001
- Amount to pay: $12,000.00 (full outstanding)
- When: 2026-10-14 ACH (due 2026-10-15)
- Explicitly not a remittance of funds already sent

Action for email/triage: classify. Do not apply cash from world.

# Stripe

Standing notes for this Bot. Not shared.

## Payout labels (Maximor sim)

- Destination bank deposit id pattern: `BANK-{payout_id}`
- Fee line types: `stripe_fee` / category `fee`
- Refund line type: `refund`
- Chargeback line type: `dispute` / category `chargeback`
- September 2026 payouts: po_1MaximorFees, po_1MaximorRefunds, po_1MaximorDisputes — all MATCH, invoice_candidates 0

## Paths

- Packets: `workspace/sources/stripe/po_1Maximor*.json`
- Kernel state: `runs/integrations/state.json`

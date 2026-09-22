# Bank

Standing notes for this Bot. Not shared.

## Feed honesty

- Kernel `invoice_ingestion.tools.list_bank_transactions` for maximor period 2026-09 returned count 0.
- Operating-account lines live at `data/cash_recon/bank_statement.json` (world maximor).
- Card AP discovery path stays invoice_missing when find_related_invoice has no docs. Do not invent.

## Landed 2026-09

- Index: `workspace/bank/landed/2026-09-operating.json`
- Lines: `workspace/bank/lines/*.json` (28 non-VOL)
- Required: TXN-2026-09-015 included; handed to cash/match.

## Precedents

- NORTHSTAR customer wire descriptors are AR/cash territory, not AP bills.
- Stripe payout labels (STRP / po_*) go to cash as deposits, not vendor invoices.

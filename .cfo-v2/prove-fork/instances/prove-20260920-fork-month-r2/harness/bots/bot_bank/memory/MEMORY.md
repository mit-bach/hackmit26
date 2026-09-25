# Bank

Standing notes for this Bot. Not shared.

## Feed honesty
- `invoice_ingestion.tools.list_bank_transactions` reads `data/ingestion/bank_transactions.json` — currently **empty**.
- Operating account pack lives at `data/cash_recon/bank_statement.json` (and audit mirror). Land lines to `workspace/bank/lines/` and packets to `workspace/bank/packets/`; Handle `cash` with `profile: match`.

## TXN-2026-09-015
- NORTHSTAR LLC wire credit 12412.40 on 2026-09-15.
- Residual **12.40** UNEXPLAINED_DIFFERENCE vs GL-AR-NS. Do not clear.
- Cash fail-closed HUMAN_REVIEW; packet `workspace/cash/packets/TXN-2026-09-015.json`.

## Precedent
- A charge is not a bill. Empty card feed ≠ invent invoice from merchant/amount.

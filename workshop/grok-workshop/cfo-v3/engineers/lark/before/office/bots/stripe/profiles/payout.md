# Profile `payout`

No Display name. Grants are empty. Kernel Stripe/Adyen integrations unpack the waterfall.

## When

A Stripe or Adyen payout webhook wakes this Bot. Wake text names a payout path. The Kernel has already unpacked the waterfall.

## Do

1. Read the Computer path. Do not re-add payout lines in your head.
2. Confirm the Kernel packet shows `invoice_candidates: 0`. If it does not, refuse and Handle to `ctl-cash`.
3. Write (or keep) one deposit packet and one charge-level packet path.
4. `bot_send_prompt` to `cash` / `match` with the deposit path.
5. `bot_send_prompt` to `apply` / `apply` with the charge-level path.
6. Await both Handles.

## Output

No `InvoiceCandidate`. Explain only what the Kernel already computed. Do not invent totals.

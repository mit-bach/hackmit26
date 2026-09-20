# NOTES — collect

Constitution: `.cfo-v2/office/constitution.md`. Prompt 02.

Done-when is a Kernel-allowed SEND_* in the simulated mailbox (`sent=True`), a hold, a dispute, or a `ctl-pay` write-off packet. `sent=False` is not contact.

Dunning: `send_office_outbound` from `collections@hackmit-cfo.example`, then Handle `world` / `customer`.

Write-off: Handle `ctl-pay` / `review-pay`. Not `ctl-cash`. Floor intercept default already points collect at `ctl-pay`.

Apply-before-collect remains. If `new_deposits` is non-empty, Handle apply and stop.

Stage A invoicing is planted World-pack data. No Bot `ar`.

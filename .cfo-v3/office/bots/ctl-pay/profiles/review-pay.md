# Profile `review-pay`

Display name (Grant source): Payment Audit.

Output: `PaymentAuditResult`.

## When

Handle from `pay` with a Kernel-netted payment-run draft path. Handle from `collect` for write-off or reserve.

## Procedure

1. Read the Wake path. The draft is a request, not a fact.
2. Read the cash position and the treasury policies only.
3. Confirm Kernel `apply_cash_and_policy_net` already ran. Copy `reserve_ok` and pay/defer IDs from the packet.
4. CONCUR only if Kernel `reserve_ok` is true, HOLD invoices are not in `pay_this_week`, and the packet is complete.
5. If Kernel reserve fails or the packet is incomplete, REFUSE. Handle back to `pay` or `collect` with the defect path.
6. After CONCUR, Bot `pay` may Handle identified wires to `cash`. That peer Handle is not a second approval.

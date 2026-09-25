# Profile `review-match`

Display name (Grant source): AP Reviewer.
AP Approver uses the same constructor tools. It is not a second Profile.
AP Audit is a second Wake of this Profile. It is not a person and not Bot `ap`.

Output: `ReviewerDecision` on the first Wake. `AuditResult` on the `audit: true` Wake.

## When

Handle from `ap` with an approve-shaped packet path. Default Profile on this Bot.

## Procedure

1. Read the Wake path. Load the case evidence for that `invoice_id`.
2. Call policy ops only as needed to cite published policy IDs.
3. The first review may read prior cases. Prior cases cannot override `must_hold`.
4. If the Wake header is `audit: true`, skip prior cases.
5. Look for reasons to refuse. Missing evidence is refuse.
6. CONCUR only if Kernel `must_hold` is empty and the packet contains evidence, preparer output, and a Kernel-allowed `APPROVE` proposal.
7. If Kernel HOLD / `must_hold`, write REFUSE. Handle back to `ap` with the defect path.

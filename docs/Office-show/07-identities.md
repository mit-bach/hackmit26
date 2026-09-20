# Featured identities

Do not retarget these. World pack and `final-demo/SCENARIOS.md` own them. If an id is missing on disk, skip that story. Do not mint a replacement Acme.

---

## Public storylines (must attempt)

### STORY-CLEAN — Acme

| Object | Id |
| --- | --- |
| Invoice | `INV-001` |
| PO | `PO-101` |
| GR | `GR-101` |
| Payment (when scheduled) | `PAY-AP-001` |
| Bank | `TXN-2026-09-018A` |
| GL | `GL-AP-INV-001` |
| Amount | $12,450.00 |

Show: match, 2/10 if Kernel offers it, pay-run, bank tick, audit sample, forecast actual.

### STORY-RESOLVED — Helios

| Object | Id |
| --- | --- |
| Invoice | `INV-017` |
| Payment | `PAY-AP-017` |
| Bank | `TXN-2026-09-011` |
| Fee evidence | `FEE-729103` |

Show: $25 over books, FEE_NETTED with evidence, close accepts the **explained** exception. Not a cousin of `$12.40`.

### STORY-UNRESOLVED — Northstar

| Object | Id |
| --- | --- |
| AR invoice | `INV-AR-013` |
| Payment | `PAY-006` |
| Bank | `TXN-2026-09-015` |
| GL | `GL-AR-NS` |
| Residual | **$12.40** (books $12,400.00 vs bank $12,412.40) |

Show: unexplained. `ctl-cash` does not MATCHED. Close BLOCKED. Story UNLOCKED. Holdout explanation stays holdout.

---

## Also keep

| Id | Role |
| --- | --- |
| `INV-AR-014` | Quiet Harbor late — story |
| `PR-2026-10-02` | Payroll identity — optional October |
| `VEND-001` / `VEND-001-DUP` | Loud duplicate vendor — audit decoy, already planted |
| `CASE-001` | August Acme alias precedent — discover, do not re-teach |
| `MSG-INBOX-001` … `019` | 17 inbox cards (some numbers skipped in the table; use SCENARIOS.md) |

---

## Inbox traps (must classify, must not pay)

Quote `MSG-INBOX-008`, statement `007`, lunch `010`, injection `014`. Credit memo `016` is not a payable. Remittance `019` goes to apply, not ap.

---

## Do not feature

- `INV-S12`, `MSG-S12`
- Holdout ADV-* as a public find
- Ghost employee / related party stealth (Phase B, not this goose)
- Finance Agent Benchmark filings
- `examples/cfo-floor` slug `ar`

---

## One identity across pipes

After the run, P8-style check **on this desk only** (read Handles, do not Wake “trace yourself”):

`INV-001` appears in email/ap/ctl-pay/pay/cash/close pack/audit/story without a second Kernel id.

`$12.40` is the same `TXN-2026-09-015` in cash, close, story.

Write the seqs into CHAPTERS.md. That paragraph is the portfolio thesis.

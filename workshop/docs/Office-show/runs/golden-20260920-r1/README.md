# Run — golden-20260920-r1

- Serve: http://127.0.0.1:8800/
- Instance: `golden-20260920-r1`
- Computer: `.cfo-v2/office/instances/golden-20260920-r1`
- Fake workers: no
- Catalog: 101
- Intercept default: ctl-pay
- `$12.40` still unexplained: yes
- Operator never concurred: yes
- Protocol lastSeq: **142** (close `turn.end` on month-end coordinate)
- Recording: `harness/demo/latest/` plus copy `docs/Office-show/runs/golden-20260920-r1/recording/`
- Inventory: `docs/Office-show/10-golden-inventory.md`
- Camera: `docs/Office-show/09-director.md`

## Clock

| Beat | Story time | Wall (UTC) | Notes |
| --- | --- | --- | --- |
| O | 2026-09-01 | 14:46Z | Overlay 1 books `h_e23fbca4`. Inbox dumped 19. |
| W1 | week of Sep 1 | 14:50Z | Overlay 2 email. INV-001 CONCUR. Inbox HOLDs. |
| W2 | ~2026-09-11 | | `weekly-pay-run` empty pool. |
| W3 | mid-Sep | 15:09–15:14Z | Overlay 3 bank, Overlay 6 cash, Overlay 4 stripe. |
| ME | month-end | 15:26Z | `month-end` coordinate. REJECT_CLOSE. Story UNLOCKED. Audit sampled. |

## Overlay DMs / Routine fires

1. books / erp-invoice (O)
2. email / inbox (W1)
3. bank / card (W3)
4. cash / match Helios+$12.40 (W3)
5. stripe / payout (W3)
6. Routine `weekly-pay-run`
7. Routine `month-end`

Verifiers zero Operator DMs.

## Happy-enough vs this tape

| Bar | Status |
| --- | --- |
| Discovery of preexisting company | yes |
| INV-001 → ctl-pay | CONCUR |
| Pay-run reached ctl-pay | yes, empty pool, executed false |
| Inbox traps not payable | yes (quote/statement/newsletter) |
| `$12.40` unexplained | yes |
| Close BLOCKED, story UNLOCKED | yes |
| Audit no ground truth | yes |
| Paid Acme / closed month | **no** — do not claim on the website |

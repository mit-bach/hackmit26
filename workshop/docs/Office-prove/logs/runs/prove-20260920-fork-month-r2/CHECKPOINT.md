# Checkpoint — prove-20260920-fork-month-r2

| When | Step | Class | T | Note |
| --- | --- | --- | --- | --- |
| 2026-09-20T15:54Z | select | RUNS | | sidecar 61151; golden unchanged |
| 2026-09-20T15:56Z | P1-S08 | INTENDED | | injection REJECTED; no mint |

| 2026-09-20T15:57Z | P1-S01 | INTENDED | | 15 threads this Computer; got MSG-ACME-INV-001 |
| 2026-09-20T15:58Z | P1-S02 | SOFT | T6 | MSG-ACME-INV-001 VENDOR_INVOICE CREATE_AP_INVOICE; dispatch ATTACH BUSINESS_DUPLICATE INV-001; forwarded_to_ap false; no AP Handle. Judged bill still INV-001 |

Replay from: continue P1 on this desk (S03+). Do not clone for SOFT until P1 ends.

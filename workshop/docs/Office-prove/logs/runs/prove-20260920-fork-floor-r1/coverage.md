# Coverage — prove-20260920-fork-floor-r1

Isolated fork desk. Pipes not run on this floor instance.

| Slug | Class | P0 bind | One Handle | Home procedure |
| --- | --- | --- | --- | --- |
| email | Source | RUNS | | P1 |
| stripe | Source | RUNS | | P1, P4 |
| bank | Source | RUNS | | P1, P4 |
| books | Source | RUNS | | P1, P3, P5 |
| world | Source | RUNS | | P1, P3 |
| ap | Operator | RUNS | RUNS S05 | P2 |
| pay | Operator | RUNS | | P2 |
| apply | Operator | RUNS | | P3 |
| collect | Operator | RUNS | RUNS S07 | P3 |
| cash | Operator | RUNS | | P4 |
| close | Operator | RUNS | | P5 |
| story | Operator | RUNS | | P5 |
| ctl-pay | Verifier | RUNS | | P2, P3 write-off |
| ctl-cash | Verifier | RUNS | | P3 apply, P4 |
| ctl-books | Verifier | RUNS | | P5 |
| audit | Assurance | RUNS | | P5 |

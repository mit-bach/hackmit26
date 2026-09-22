# Coverage — prove-20260920-month-r1

Copied from `docs/Office-prove/04-coverage.md` table A. Tick as observed.

| Slug | Class | P0 bind | One Handle | Home procedure |
| --- | --- | --- | --- | --- |
| email | Source | | | P1 |
| stripe | Source | | | P1, P4 |
| bank | Source | | | P1, P4 |
| books | Source | | | P1, P3, P5 |
| world | Source | | | P1, P3 |
| ap | Operator | | | P2 |
| pay | Operator | | | P2 |
| apply | Operator | | | P3 |
| collect | Operator | | | P3 |
| cash | Operator | | | P4 |
| close | Operator | | | P5 |
| story | Operator | | | P5 |
| ctl-pay | Verifier | | | P2, P3 write-off |
| ctl-cash | Verifier | | | P3 apply, P4 |
| ctl-books | Verifier | | | P5 |
| audit | Assurance | | | P5 |

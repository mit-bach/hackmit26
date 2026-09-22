# Run log — prove-20260920-fork-month-r2

- Created: 2026-09-20T15:54:42Z
- Procedure(s): P1 replay after T12 patch on copied Kernel
- Serve URL: http://127.0.0.1:8801/
- Computer path: `.cfo-v2/prove-fork/instances/prove-20260920-fork-month-r2`
- Patch: `.cfo-v2/prove-fork/.cfo/inbox/classify.py` + `dispatch.py`. Live `.cfo/inbox` unchanged.
- Fake workers: no
- Sidecar: 61151

## Sequence of steps

| Step | Class | T | Bot | Profile | Ops | Handle | Note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1-inject | RUNS | | world (sidecar RPC) | vendor | inbox.tools.send_inbox_message | | 15 fixtures. Not MSG-S12 |
| P1-S01 | INTENDED | | email | inbox | list_inbox_threads, get_inbox_message | h_0e7632f3-0f27-4982-9ca4-dce9b301f746 | 15 threads this Computer |
| P1-S02 | SOFT | T6 | email | inbox | classify, dispatch | h_2ebe6fba-92ea-435b-b866-df077e8ed80c | MSG-ACME-INV-001 VENDOR_INVOICE; ATTACH BUSINESS_DUPLICATE INV-001; no AP Handle. Batch-edit email skill after P1 |
| P1-S08 | INTENDED | | email | inbox | classify, dispatch | h_98f5a697-2062-4530-ac95-fd74bfe0b171 | MSG-INBOX-014 UNSUPPORTED_OR_UNRESOLVED REJECTED; no AP Handle; no Kernel mint |

## Checkpoints

See CHECKPOINT.md.

## Open holes

-

## Next action

- [x] continue this instance
- [ ] wipe
- [ ] new instance rN+1
- [ ] 05 repair agent
- [ ] skill batch edit

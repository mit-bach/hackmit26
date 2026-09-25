# Nothing in the prompt set gets dropped

Read the files below. Each one is an intention for this office. Your job is to check that the running system still carries that intention. If a later edit deleted it, put it back. Do not resume an old procedure, and do not treat a half-finished desk as the task.

Repo: `/Users/dominikbach/olympus/hackmit/hackmit26`. Live template: `.cfo-v2/office/`. Fork copy: `.cfo-v2/prove-fork/`. Recorded month: `.cfo-v2/office/instances/golden-20260920-r1`. Harness: `.harness/Harness-v2/`.

## The prompt set

| File | Intention |
| --- | --- |
| `workshop/docs/Office-prove/prompts/00-OPERATOR.md` | Live Pi, not fake workers. A step counts only when a granted tool actually runs. English without a tool call is not a result. Classify throws, patch the live template, do not hand-edit `grants.json`. |
| `workshop/docs/Office-prove/prompts/01-PIVOT-TO-SHOW.md` | The thing to ship is one September a person can watch. Wakes are business English. A wake that says “call tools.X” is not a demo. `$12.40` stays unexplained. September is not CLOSED. The operator does not concur for a verifier. |
| `workshop/docs/Office-prove/prompts/RESUME-FORK-THEN-MERGE-GOLDEN.md` | Prove work stays off the golden Computer until the behavior is real, then the refined Bot files and the injection reject land on the live template. A new golden is a new instance. The old tape stays. |
| `workshop/docs/Office-prove/prompts/FIX-BEHAVIOR-ISOLATED.md` | One defect, one small instance, two or three Bots. A pass is a thread that continues, or a kernel log that shows the finance call after a wake that did not name it. A status row is not a fix. |
| `workshop/docs/Office-prove/prompts/ADOPT-CONTEXT-MODULE.md` | Instructions are in the system prompt. `BOT.md`, the active profile, and the skill bodies are pasted in. “Read BOT.md” is a bug. `MEMORY.md` and recent-work lines stay out of the prefix so the cache is not rebuilt every wake. |
| `workshop/docs/Office-prove/prompts/MIGRATE-SANDBOX.md` | A Computer is created with `workspace/<slug>/{packets,handles,notes}` and `runs/<domain>/`. Bots do not invent folders. A write outside that desk is blocked. |
| `workshop/docs/Office-prove/prompts/STATE-AND-FIX.md` | What each Bot owns, which sentences in the current Bot files are broken, and the behaviors a finished office still has to show. |

Design notes those prompts were written from:

| File | Intention |
| --- | --- |
| `workshop/docs/Office-show/GOLDEN-STATE-SCOPE.md` | The recorded month is one-shot handoffs. World spoke once. Audit did not find the insider. Close left JSON. Workers stop after one reply. |
| `workshop/docs/Office-show/TOOL-USE-GOLDEN.md` | Reliability is the Catalog. On that tape most turns were shell and file reads. Whole grant sets never ran. |
| `workshop/docs/Office-show/CONTEXT-ASSEMBLY.md` | How a turn is built today, and why “go read the file” is not a system prompt. |
| `workshop/docs/Office-show/CONTEXT-MODULE.md` | Office layer plus bot layer, stable prefix, volatile text at the end of the turn. |
| `workshop/docs/Office-show/SANDBOX.md` | There was no jail. Approval level `never` lets ordinary `bash` through. A lease file that lists only `audit` confines nobody else. |
| `workshop/docs/Office-show/SANDBOX-INIT.md` | Which directory holds a packet, a handle, and a kernel trace. |

## Intentions that have to still be true

Check each one in the files and, where it is a behavior, on a new small instance. A wake that names a Catalog op does not count.

**Tools.** Finance facts come from the Grant door. A shell listing of `data/` is not that. Skills never add ops. `get_audit_ground_truth` stays off operational grants. The phrase “the finance record” in a Bot file or profile is not a tool. Replace it with the action that profile performs. Do not put Catalog ids in Operator wakes.

**Behavior.** World is everyone outside the company, reached by mail: vendor, customer, bank, employee. Collect keeps a thread on one invoice after the customer answers. `ctl-*` answer once. Other Bots do not. `$12.40` on `TXN-2026-09-015` stays unexplained. September is not CLOSED. The operator does not complete a verifier handle. Injection that looks like a bill does not mint one, including on live `.cfo/inbox/`, not only on a fork copy.

**Audit.** The unlabeled insider rows are already in `.cfo-v2/office/world/maximor/registers/` (`EMP-8891` and the vendor rows named in `STATE-AND-FIX.md`). Do not load the holdout or name the scheme in a wake. A sample that only cites the loud decoys (`PAY-AUD-002`, `VEND-ACME-DUP`, `JE-AUD-003`) missed the intention in `GOLDEN-STATE-SCOPE.md`.

**Context.** `assembleContext` is the system prompt. Office text is `office/system.md` on every Computer a serve can select, including golden. Bot text is the inlined `BOT.md`, profile, and skills. Recent work and `MEMORY.md` are not in that prefix.

**Sandbox.** Every Computer has the init directories and a lease file with all sixteen slugs. A write outside `workspace/<slug>/` and that Bot’s `memory/` is blocked, and the blocked tool result is saved. Golden’s protocol and `harness/demo/latest/` stay. Do not record over that tape.

**One office.** Template, fork, and instances do not carry different instructions for the same Bot. Where `.cfo-v2/office/bots` and `.cfo-v2/prove-fork/bots` differ, make one text and copy it. Same for `inbox/classify.py`.

If an intention above is already true in the file and in a kernel log from a clean wake, leave it. Write down the path. Do not redo it to show activity.

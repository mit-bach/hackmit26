# Sandbox

What confines a Bot on `golden-20260920-r1`, what that Bot can still touch, and the directory layout the Computer should create before anyone wakes.

## There is no sandbox

Pi’s working directory is the instance Computer. The golden AP session records `cwd` as `.cfo-v2/office/instances/golden-20260920-r1`. From there, `bash`, `read`, and `write` are Pi’s own tools. Harness does not wrap them in a chroot, a container, or a path jail.

Every Bot in `harness/roster.json` has `approvalLevel: "never"`. In `src/approvals.ts` that level asks for approval only when the command matches a delete-tree pattern or `rm -rf`. Ordinary `bash` is not consequential. A Bot can `python3` a file under `data/`, write into `.cfo/`, or write into a sibling instance, as long as the OS user can.

The only path check on a finance call is `refuseConnectedTool` in `cfo/extensions/call.ts`. It looks at `path-leases.json`. On the golden Computer that file lists one Bot:

```json
{ "audit": { "writePrefixes": ["workspace/audit/", "runs/audit/"] } }
```

If a slug has no prefixes, the function returns “allowed.” So the lease confines audit and nobody else. It only sees arguments named `path`, `dest`, or `file` on `call_connected_tool`. A `bash` redirect never goes through it.

`acquireLease` in `src/leases.ts` is a lock between two Bots on the same file for about 30 seconds. It is not a boundary. The first writer wins. The path can be anywhere.

`data/` is a symlink to the shared Maximor pack. It is not mounted read-only. `cfo/catalog.json`, `grants.json`, and `harness/roster.json` sit on the same tree the shell can edit.

## What they invented

Nobody created the folders ahead of time. The first Bot that needed a place made one. Two trees showed up, and they overlap.

`workspace/` is where Bots put packets they authored. `runs/` is where kernel tools and the month-end host put traces. Some domains exist in both.

| Path on the golden Computer | Who made it | What landed |
| --- | --- | --- |
| `workspace/books/masters`, `erp`, `ar`, `lock` | books | Discovery JSON, open-invoice roster |
| `workspace/ap` | ap | Match packets |
| `workspace/email` | email | Triage notes |
| `workspace/bank/landed`, `lines` | bank | Operating lines |
| `workspace/cash/packets`, `trusted`, `expected-outflows` | cash | Recon packets |
| `workspace/pay/plans` | pay | The empty plan |
| `workspace/close/2026-09` | close host and close | `pack.json`, gates, coordinate decision |
| `workspace/story/2026-09` | story | Flux draft |
| `workspace/audit/2026-09` | audit | Interpretation |
| `workspace/sources/stripe` | stripe | A third name, not `workspace/stripe` |
| `runs/inbox/packets`, `handles` | email, world | Classified mail |
| `runs/ap/packets`, `concurrence` | ap, ctl-pay | `INV-001` concurrence |
| `runs/ar/packets`, `handles` | apply | `PAY-001` |
| `runs/cash_recon/cases`, `packets` | cash tools | Case files. Missing ids returned `not_found` |
| `runs/pay/plans`, `concurrence` | pay | Copy of the plan, also under `workspace/pay` |
| `runs/audit` | audit kernel | The loud-control finding file |
| `runs/month_end`, `accruals`, `bs_recon`, `integrations` | host | Close and payout traces |
| `harness/bots/bot_*/memory` | Harness memory tools | Per-Bot `MEMORY.md`. Not a top-level `memory/` |

`close/2026-09/pack.json` cites an absolute path under `.cfo/runs/ingestion/`, outside this Computer. That write escaped the instance because the host process `chdir`s into `.cfo/` for imports.

## Prescribed Computer

One instance is one sandbox. The init script creates the tree empty. Bots do not invent top-level names. The script is `office/init-computer.py` (or the instance cloner calls the same function). It runs when an instance is created, before the first wake.

```text
<computer>/
  office/                 identity. Init copies it. Bots do not write it.
    system.md
    constitution.md
    bots/<slug>/BOT.md
    bots/<slug>/profiles/
  data/                   symlink to the world pack. Read-only to Bots.
  cfo/                    catalog, grants, path-leases. Compiler writes. Bots do not.
  harness/                roster, protocol, sessions. Harness writes. Bots do not,
                          except harness/bots/bot_<slug>/memory/.
  workspace/<slug>/       this Bot’s desk. The only tree it may create files in.
    packets/
    handles/
    notes/
  runs/<domain>/          kernel and host output. Tools write. Bots read.
    inbox/
    ap/
    ar/
    cash_recon/
    pay/
    audit/
    month_end/
    accruals/
    integrations/
```

`<slug>` is the roster slug: `email`, `ap`, `world`, `cash`, `close`, `ctl-pay`, and the rest. `workspace/sources/` goes away. Stripe uses `workspace/stripe/`. Period work is `workspace/close/packets/2026-09.json`, not a new top-level folder the host makes up.

`path-leases.json` lists every slug, not only audit. Each write prefix is `workspace/<slug>/`. Kernel tools that write traces use `runs/<domain>/` from Python, not from the model’s shell. `refuseConnectedTool` must reject a write when the prefix list is missing. An empty list is not “allow all.”

`bash` and Pi `write` / `edit` use the same prefix. A path outside `workspace/<slug>/` and outside `harness/bots/bot_<slug>/memory/` is blocked in the `tool_call` hook. `read` of `data/`, `office/`, `cfo/catalog.json`, and `runs/` stays allowed. `read` of another Bot’s `workspace/` or `memory/` does not. `data/` is not writable by the tool hook even if the mount is writable.

`initComputer` creates the empty directories and a one-page `workspace/<slug>/README.md` when that file is missing. It does not create packet files. How to use the directories, and how a new slug or a new kernel domain is added, is `SANDBOX-INIT.md`.

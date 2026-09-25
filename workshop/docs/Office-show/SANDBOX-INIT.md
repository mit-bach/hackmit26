# Sandbox directories

Harness creates this tree when it initializes a Computer. That happens on `initComputer`, which runs when a server starts and when a new office instance is created. Nothing else has to create the folders. New files go in the directories below. A new top-level name is not a place to put work.

The write check uses the same paths. A Bot may write `workspace/<slug>/` and `harness/bots/bot_<slug>/memory/`. `<slug>` with a hyphen uses an underscore in the bot directory: `ctl-pay` writes memory under `harness/bots/bot_ctl_pay/memory/`.

## Desk

`workspace/<slug>/` is that Bot's desk.

| Directory | What goes in it |
| --- | --- |
| `packets/` | The Bot's own work product: a match packet, a triage summary, a plan, a close note. One file per item. A period is part of the file name (`2026-09.json`), not a new folder beside `packets/`. |
| `handles/` | The Handle record for a handoff this Bot accepted or sent. |
| `notes/` | Short standing notes that are not a packet and not Memory. |

`README.md` on the desk is created once. Later edits are kept. It is a reminder of these three directories, not a second instruction file.

Do not add `workspace/sources/`, `workspace/<slug>/masters/`, or `workspace/<slug>/2026-09/`. Those names were invented during the golden month. New work does not use them.

Another Bot's `workspace/<slug>/` is not readable and not writable.

## Kernel output

`runs/<domain>/` is written by kernel tools and the month-end host. Bots read it. Bots do not invent a parallel copy of the same object under `workspace/`.

| Directory | What lands there |
| --- | --- |
| `runs/inbox/` | Classified mail, outbound handles |
| `runs/ap/` | Match packets the kernel recorded, concurrence |
| `runs/ar/` | Application packets |
| `runs/bank/` | Landed bank lines |
| `runs/cash_recon/` | Case files, match packets |
| `runs/pay/` | Pay-run plans and concurrence |
| `runs/audit/` | Audit run output |
| `runs/month_end/` | Close pack, gates, snapshots |
| `runs/accruals/` | Accrual runs |
| `runs/bs_recon/` | Balance-sheet packets |
| `runs/integrations/` | Payout traces |
| `runs/reporting/` | Forecast and variance traces |
| `runs/ingestion/` | Ingest traces for this Computer |

A new kernel domain gets a new directory under `runs/` only when a tool in the Catalog writes that domain. Adding the name to the layout list in `ensureSandboxLayout` (`src/sandbox.ts`) creates the empty directory on the next init. A Bot does not create `runs/<new>/` from a shell.

## Memory

`harness/bots/bot_<slug>/memory/` is this Bot's Memory tree, including `MEMORY.md`. It is not shared. It is not a place for packets.

## What stays out

`office/` is identity: `system.md`, constitution, `BOT.md`, profiles. `cfo/` is catalog, grants, and path leases. `data/` is the world pack. `harness/roster.json`, `protocol.jsonl`, and session logs are Harness files. None of these are desks. A new kind of finance file is either a packet on the owning Bot's desk or a kernel trace under `runs/`.

## Expanding

A new Bot slug, added to `harness/roster.json`, gets `workspace/<slug>/{packets,handles,notes}` and a memory directory the next time the Computer is initialized. No hand-made folder.

A new file type for an existing Bot goes in `packets/` with a clear file name. A new subdirectory is only worth adding if the sandbox write prefix and this document both name it. Until then the three desk directories are the whole desk.

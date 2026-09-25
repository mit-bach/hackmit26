# CFO v2 on Harness v2, and what v5 keeps

This is the map of the office that ran on `.cfo-v2` and `.harness/Harness-v2`, and where each behavior lives now. Harness v3 is the host. CFO v5 is one client of that host. A feature that v5 deleted on purpose is named as deleted.

## Two extension files

`.harness/Harness-v3/extensions/index.ts` is the host. It binds a Bot, drains the inbox, and registers the tools every Computer has: `ask_bot`, memory, rooms, approvals.

`.cfo-v5/cfo/extensions/index.ts` is the finance client. `harness/client.json` names it in `extraExtensions`. It registers `search_connected_tools`, `call_connected_tool`, and `complete_step`. It does not register `ask_bot`. The two files load in one Pi process and do not replace each other.

## Instances

v2 kept one registry at the office parent and one full Computer per id under `office/instances/<id>/`. `golden-20260920-r1` was the production desk. Ids that start with `prove-` were testing desks. Each of those directories had its own `harness/`, `workspace/<slug>/`, and `runs/`. The group was guessed from the id: `golden` became `production`, anything else used the text before the first dash.

v5 keeps that shape and states the group in a file instead of guessing it from a name:

```text
.cfo-v5/office.json
.cfo-v5/instances/live/                  group: deployment
.cfo-v5/instances/prove/engine/          group: testing
```

`live` is the Computer you serve. `prove/engine` is the Computer the engine proof writes. Each has its own `sandboxes/<slug>/` and its own `runs/`. Shared definition (kernel, world pack, catalog, Bot text, skills, seatbelt template) is linked into the instance. Runtime files are not linked across instances.

`runs/` at the top of `.cfo-v5` was one shared ledger for every Bot. That directory is gone. Kernel traces, item files, and idempotency for a desk stay inside that desk.

## What Harness v2 did, and where it went

| Behavior | v2 | Now |
| --- | --- | --- |
| Roster, rooms, routines | `harness/roster.json` | Same file. Routines no longer contain `profile:` or `bot_send_prompt`. The engine moves an item. |
| Inbox, Handle, lane, one Pi process per Bot | Harness supervisor | Harness v3. A session is not restarted per step. |
| `ask_bot` pair thread | Harness extension | Harness v3. Not used to route a bill. |
| Memory | `harness/bots/<id>/memory` | Client layout. CFO sets `sandboxes/{slug}/memory`. |
| Operator HTTP and UI | `serve` | Harness v3, pointed at one instance. |
| Sidecar process | `client.json` `sidecar`, with defaults that looked for `cfo/bin/sidecar.sh` | Only the command written in `client.json`. The Harness does not search for a kernel. |
| Extra Pi extensions | `extensions.json` and `client.json` | Same. |
| Office instance clone | Copy `cfo/`, `workspace/`, `skills/`, `office/` | Copy or link the directories named in `harness/layout.json`. |
| Wipe | Always cleared `cfo/kernel.log.jsonl` and `cfo/idempotency` | Clears the paths in `layout.json` `wipe`. |
| Demo record and replay | Harness | Harness v3, unchanged. |
| Approvals and intercept | `harness/intercept.json` | Harness v3. |
| Path regex sandbox | `sandbox.ts` prefixes `workspace/<slug>/` and a fixed list of finance `runs/` folders | The prefix check remains for a Computer with no jail. The folder names come from `layout.json`. CFO turns the regex off and uses `sandbox/seatbelt.sb`. |
| `profile:` wake header and `cfo/slug-map.json` | Harness `wake-profile.ts` swapped the Bot's grant set | Deleted in the host. v5 steps are ledger fields. The kernel still has a slug map so a Catalog call can name one display-name grant. The model does not send `profile:`. |
| `active-profile.txt` | Written by the v2 finance extension | Not written. |
| Answer-key filenames | Hardcoded in the regex sandbox | Still a small default denylist in the regex sandbox so an old Computer keeps that block. A jail Computer blocks `data/` by seatbelt instead. |
| Protocol card `SYSTEM.md` copies | Written next to every session | CFO layout sets `protocolFiles: false`. The card stays in code. |
| Skill directories registered with Pi | `resources_discover` | CFO layout sets `registerSkillDirs: false`. Skill bodies are pasted once by `assembleContext`. |

## What the finance client still owns

These were in `.cfo` and `.cfo-v2/office/computer/cfo`, and they stay under `.cfo-v5`:

- Catalog and grants, and the step-grant projection.
- The Python kernel and the sidecar script.
- The world pack in `data/`.
- The workflow engine, the item ledger, and `complete_step`.
- The finance Pi extension.
- Bot identity in `office/bots/<slug>/BOT.md`.
- The seatbelt template.
- The list of run domains (`ap`, `cash_recon`, `accruals`, and the rest) in `harness/layout.json`.

## What was deleted rather than moved

- Profile files and the `profile:` control line.
- English `## Handoffs` as the way a bill changes hands.
- A shared `workspace/<slug>/` desk.
- One `runs/` tree for every instance.
- `constitution.md` and `SUPERSEDES.md` as office law. The channels are in `office/system.md`.
- `ask_user` as a way to finish a finance step.

## Serve

```text
node .harness/Harness-v3/dist/src/cli.js serve --computer .cfo-v5/instances/live --no-open --port 8800
```

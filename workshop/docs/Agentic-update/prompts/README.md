# Office deploy — five agent prompts

Operator: Billy. These are spawn-ready briefs for **separate** Cursor agents. Do not paste all five into one agent.

The current office is a Kernel that mostly works, a grain of fifteen Bots, and a bus that is not deployable as the judged product: `--fake` in the runbook, BOT.md off Computer cwd, two Handle stores, AR send `ImportError`, World off the live Roster, AP stub Handles on a marker bill, Stripe costume, close writing `.cfo/runs`. The target is a live Pi office that finishes open items on Handles, with Verifiers concurring and no human in the completion path.

This folder is the launch pack. The source corpus stays in `docs/Agentic-update/` (`01`–`04`, `02b`, `pipes/`, `surfaces/`, `evidence/`). Those files are not prompts. These files are.

## Spawn order

1. Finish **01** first. It ships bind, live boot, BOT.md on Computer cwd, one Handle store. 02–05 will **stop** on Floor holes they do not own, or they will write a NOTES file and continue only on Kernel work they own.
2. Then spawn **02** and **03** in parallel. Their Kernel modules do not overlap. They must not rewrite the same Grant row.
3. Then **04**. Cash trusts identifiers 02 and 03 wrote.
4. Then **05**. Close is the period pass. A board pack first is a lie.

Each agent must read `00-SHARED-LAWS.md`, then only its numbered file.

## What to paste

Copy the entire numbered markdown file into a new agent. Tell it: working directory is the repo root `hackmit26`. Then either paste `00-SHARED-LAWS.md` above it, or tell it to read that path first (the numbered prompt already says to).

Prefer: “Read these two files and implement. Do not implement the other numbered prompts.”

Do **not** attach the corpus with `@`. The numbered prompt lists every path. The agent Reads them. Disk wins over `evidence/live-computer-2026-09-20.md`.

| Order | File | Specialization |
| --- | --- | --- |
| laws | [00-SHARED-LAWS.md](00-SHARED-LAWS.md) | Grain, honesty, T-categories, ownership, spawn |
| 1st | [01-FLOOR.md](01-FLOOR.md) | Live boot, Client `-e`, cwd, Handle store, intercept default |
| 2nd | [02-AR.md](02-AR.md) | Apply, collect, send, World mailbox round-trip |
| 2nd | [03-AP.md](03-AP.md) | Real bills, match, pay-run, AP learning |
| 3rd | [04-CASH.md](04-CASH.md) | Identifier trust, Stripe honesty, $12.40 stays |
| 4th | [05-CLOSE.md](05-CLOSE.md) | Computer `runs`, empty Profiles, lock, UNLOCKED, audit |

## File ownership (do not overlap)

See the table in `00-SHARED-LAWS.md`. Short form:

- 01 owns Harness generic bus, `RUN.md`, intercept **default**, Handle unlock, Computer-visible BOT.md layout.
- 02 owns `.cfo/inbox/`, `.cfo/ar/`, World bind, collect send, apply.
- 03 owns `.cfo/workflow.py`, `.cfo/agent.py`, AP scheduling, `ap` / `pay` / `ctl-pay` text.
- 04 owns `.cfo/cash_recon/`, Stripe Grants, `cash` / `ctl-cash` / `stripe`.
- 05 owns `.cfo/close/`, reporting, audit, `close` / `story` / `audit` / `ctl-books`.

If two agents append `roster.json` at the same time, rebase by grain Tests A–D. World belongs to 02. Do not rewrite `:root` of another agent’s Grant row.

## Out of scope for all five

- Fake videos and `web/` redesign (that is `design-workshop/dominik/Prompts/web-overhaul`)
- Resolving $12.40
- Live SMTP / Gmail / ACH / NetSuite
- Restoring `Runner` as the Bot bus
- Forty-three lanes
- Merging Bot `world` onto the live Roster **without** Tests A–D in prompt 02
- A new Bot `ar`

## After all five land — office done

1. Documented boot is live Pi plus Client `-e` plus sidecar. `--fake` is a demo switch, not the runbook.
2. A real vendor bill (not `INV-S12` marker) can land, match or HOLD, and reach `ctl-pay` with Kernel evidence.
3. Apply drains deposits. Collect chases only after that. A Kernel-allowed SEND_* reaches the simulated mailbox. A customer persona can reply. `sent=False` outbox-only is not done.
4. Cash ticks identifiers apply and pay already wrote. `$12.40` on `TXN-2026-09-015` stays unexplained. Close stays BLOCKED on it.
5. Close treatments and lock run against `$HARNESS_COMPUTER/runs`, not a silent `.cfo/runs` happy path. Story labels UNLOCKED when lock is missing. Audit does not fix books.
6. One Handle store is truth for Verifier unlock. Operator is emergency stop.
7. BOT.md is readable from Computer cwd. Grants match constructors. `send_office_outbound` imports. Collections Agent constructs.

Gaps stay in NOTES. Do not demo `--fake` MSG-S12 as the product.

Then run **`docs/Office-prove/`**. Repair notes are not office-live. Prove creates named instances, tasks Bots, classifies throws vs skill misses, and ticks every Skill and granted Catalog op.

Then run **`docs/Office-show/`**. One golden instance, onboarding plus a lived September, then Harness Demo record. Prove Wakes are not that tape. Scope videos from that recording.

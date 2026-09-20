# Surface — wakes and routines

A Wake starts a Bot: webhook, poll, Routine, or Handle. If work only ever runs because the same Bot continued its own turn, it is a Profile or a step, not a new Bot.

---

## Intended function of this surface

| Event | Who wakes | Next |
| --- | --- | --- |
| Invoice or remittance mail | `email` | `ap` or `apply` |
| Stripe payout.paid | `stripe` | `cash` (deposit), `apply` (charges) |
| Bank file / card feed | `bank` | `cash`; card-without-invoice stays missing-invoice |
| Books sync | `books` | `ap` / `collect` / `close` depending on the record |
| Weekly | `pay` | `ctl-pay` |
| Daily aging, after apply drain | `collect` | send / hold / write-off; or Handle apply if dirty |
| Month-end | `close` | treatment Profiles, then `ctl-books` |
| Close pack written | `story`, `audit` | packets and findings |

Routines: `weekly-pay-run`, `daily-aging`, `month-end`, `period-story`, `post-close-assurance`. Conversation `room:<id>`, not `operator_dm`.

A Wake names one Profile.

---

## What is good

Roster Routines exist with the right owning Bots and room conversations.
`daily-aging` prompt text already says: if Kernel new_deposits is non-empty, Handle apply, do not chase.
`week`/`month` cadence now parses in Harness.
Self-Wake on `close` and `story` for the next Profile is the correct substitute for children.

---

## What is broken

### Nothing starts (T5)

`autoRoutines: false`. No bank webhook. Stripe Bot cannot receive payout.paid as a Grant call. Email live proof is a stub file, not a mailbox push.

### World originations (T1)

World BOT.md: Operator may tell World to send Acme’s September invoice. Live Roster cannot bind World. That Wake is fiction on the live Computer.

### profile: header (T6)

Client `input` hook replaces Grant set on `profile:`. If Client extension is missing, the header is prose. The Bot unions nothing and also filters nothing. It has Harness tools only.

### Kernel hosts still wake themselves (T13)

`run_ap_workflow`, `run_collections`, `run_month_end` start in Python. They write Kernel-shaped next-wake records. Those are not Harness inbox items unless something copies them.

### period-story extra vs session-00 table

Constitution session-00 listed four Routines. Live Roster has five (`period-story`). WATCH recorded it. Not a sixteenth Bot. Harmless. Still two docs.

---

## Capability this surface must possess

When wakes are adequate:

1. Each Operator Bot has a named start that is not “the human typed in the Operator shell,” except as demo overlay.
2. Collect cannot start while apply has undrained deposits (Kernel gate + Routine text).
3. Close treatments are new Wakes, one Profile each.
4. Routines land on the owning Bot inbox with a Profile header the Client bind honors.

This file does not schedule the demo minute-by-minute. It requires that pipes can start without a person in the queue.

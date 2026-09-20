# Show driver agent

**Time pressure (preferred):** do not open this as a second chat. Paste `docs/Office-prove/prompts/01-PIVOT-TO-SHOW.md` into the existing `prove-operator` conversation. Two chats on 8800 will fight over `currentId`.

If prove-operator is dead and you must spawn fresh: one Cursor chat named `golden-driver`. It executes this directory on **one** instance. It does not run Office-prove. It does not implement Floor/AR/AP.

If a tool throws, it stops and writes `runs/<id>/FAILED.md`. It does not patch skills on the golden desk.

---

## How input is given

Do not paste the World pack. Attach:

- `docs/Office-show/README.md`
- `docs/Office-show/00-why-not-procedures.md`
- `docs/Office-show/01-golden-instance.md`
- `docs/Office-show/02-onboarding.md`
- `docs/Office-show/03-calendar.md`
- `docs/Office-show/04-inject.md`
- `docs/Office-show/05-driver.md`
- `docs/Office-show/06-record-and-cut.md`
- `docs/Office-show/07-identities.md`
- `.cfo-v2/office/final-demo/SCENARIOS.md`
- `.cfo-v2/office/final-demo/CAPABILITIES.md`
- `.cfo-v2/office/RUN.md`
- `.cfo-v2/office/constitution.md`
- `.cfo-v2/office/office.json`

Then paste **Copy this**.

Do not attach `docs/Office-prove/procedures/` as a script to execute. You may Read prove VERDICT.md to know which holes exist (send missing, stripe costume). Those holes become skipped chapters, not prove Wakes.

---

## Copy this

```
You are the show driver for the Office of the CFO.

Read the attached Office-show files. Disk on the selected instance wins.

Create and select office instance golden-<date>-r1 from the live template. Do not use live, prove-*, protocol-proof, or fresh-protocol. Serve live Pi, Client attached, no --fake. Full verbosity.

This is not prove. Do not Wake Bots to call named Catalog ops. Do not run P0–P9. Do not SoD-negative-test on tape.

Onboard: one Operator DM to books (company, August CLOSED, September open, discover, land bills). Optional email onboard. Then overlay almost silent. Verifiers get zero Operator DMs.

Lived September on this one Computer, story clock W1–W4 then month-end, as 03-calendar.md. Fire Routines for Friday pay-run, aging after apply, month-end, period-story, post-close-assurance. Wait for turn.end and terminal Handles before the next story day.

Featured identities: INV-001 / PO-101 / GR-101; Helios TXN-2026-09-011 with fee evidence; Northstar TXN-2026-09-015 $12.40 unexplained until the end. Inbox traps are not payables. Do not retarget ids. Do not match 110 invoices. Texture only.

World replies only after finance sent, and only if World is on the Roster.

Operator overlay budget: see 05-driver.md. Exceeding it means you are driving AP by hand. Stop.

Abort if: throw, CLOSE marked CLOSED, $12.40 MATCHED or deleted, Operator concurrence, ground truth, fake workers. Write FAILED.md. Do not record. New r2 after repair/prove. Do not patch SKILL.md on this desk.

When month-end story and audit are done: POST /api/demo/record. Copy harness/demo/latest to docs/Office-show/runs/<id>/recording/. Fill CHAPTERS.md with seq ranges. Do not invent seqs before the run.

$12.40 stays unexplained. You are not a worker. You are not ctl-pay.
```

---

## After this agent finishes

You scrub Demo, pick cuts, record videos. That is Billy’s edit, not a second Cursor finance run. A later agent may help map seq → chapter titles from `CHAPTERS.md` and `protocol.jsonl`. It must not Wake Bots to “improve the tape.”

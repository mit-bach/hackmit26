# Classification

Every step ends with one primary class. Write it in the run log. Do not invent a new class until these do not cover the event.

This file is the only place HARD vs SOFT is defined. Procedures point here.

---

## Primary classes

| Class | Meaning | Instance | Procedure | What you edit |
| --- | --- | --- | --- | --- |
| **INTENDED** | Tools returned. Open item next state matches the corpus. Fail-closed that the corpus wants counts. | Keep | Continue | Nothing for this step |
| **RUNS** | Tools returned. No throw. Next state is not yet the corpus, or you have not proven intended function, but the door worked | Keep | Continue if the procedure allows RUNS as a tick; still log if you expected INTENDED | Maybe a later skill edit if the miss is judgment |
| **SOFT** | Tools returned. Specialist judgment, Skill, or BOT.md steered wrong. Code did not throw | Keep | Continue to the end | After the procedure: `SKILL.md`, `BOT.md`, maybe Roster prompt text. Then new instance, re-run |
| **HARD** | Throw, crash, missing Grant, missing op, bind refuse, sidecar down, ImportError, two Handle stores disagree, Operator still in the completion path, identity never entered Kernel | Stop this instance | Stop this procedure | Code, constructors, compiler, Harness generic bus, intercept, Handle unlock. Then new instance or wipe |
| **BLOCKED-CORRECT** | Kernel or Verifier refused in the way the corpus requires (`$12.40` unexplained, HOLD missing GR, collect while deposits remain) | Keep | Continue | Nothing. This is a pass of law |
| **HONEST-EMPTY** | Profile has `ops: []` and the corpus already said that Profile is not a Catalog caller (Close Manager coordinate; sample-data Display names) | Keep | Tick as honest, not as office-live caller | Do not fake ops in `grants.json` |
| **SKIP** | Step cannot run because an upstream hole is named (World off Roster; Stripe empty Display name). The hole is already HARD or HONEST on another row | Keep | Continue other steps | Do not skip silently |

RUNS vs SOFT: if you expected only “does not throw,” the step is RUNS. If you expected a specific next state and did not get it, and nothing threw, the step is SOFT (skill/judgment) **unless** the miss is a missing door the model could not open. Missing door is HARD (T3).

---

## HARD — complete restart

HARD is anything that means the code, the Grant door, or the bus is not safe to keep running.

Always HARD:

1. Python traceback in sidecar or `pi-rpc.jsonl` (ImportError, TypeError, KeyError, 500-class Kernel error).
2. Constructor cannot import (`from inbox.tools import send_office_outbound` fails; Collections Agent cannot construct).
3. Compile fails (`python3 -m compiler --phase operational` non-zero).
4. Catalog op named in the Grant is not in `catalog.json`, or Pi lists a tool the Client rejects.
5. Bind refuse (`missing_display_name`, unknown slug, Client extension missing from argv).
6. Sidecar dead. `kernel.port` missing or stale after select. Serve cannot start workers.
7. Pi worker crash loop. Lane never reaches `turn.end`.
8. Handle accepted but complete path throws.
9. Two Handle stores: Harness complete does not unlock the Kernel op the Verifier already concurred (T9, T2). After Floor repair this must not happen. If it does, HARD.
10. Intercept default is the human Operator for this Client (T9).
11. `--fake` workers were used for the step you want to tick as office-live.
12. `tools.get_invoice(id)` not found for a packet Email claimed was a bill, and AP invented amounts anyway (identity break + invention). If AP HOLDs because not found, that HOLD is BLOCKED-CORRECT / INTENDED fail-closed. If the procedure’s stimulus was `INV-S12` marker as the judged bill, HARD on the procedure design: pick a real Kernel id.
13. Operational Bot called `audit.tools.get_audit_ground_truth`.
14. Close becomes CLOSED while `TXN-2026-09-015` `$12.40` is still unexplained, or someone deleted the bank line. Product law broken. HARD.
15. Finance types added to `.harness/Harness-v2/src` in a panic patch. Revert. HARD until reverted.
16. `ask_user` completed pay-run, lock, or write-off.

HARD is a **complete restart** of the prove instance after the patch:

- Write `HARD.md`.
- Patch the real layer (Kernel, constructor, compiler, Client, Harness generic).
- Recompile if Grants/Catalog changed.
- New instance (`r<n+1>`), or wipe only if `01-instance-loop.md` checkpoint rules allow.
- Replay the procedure from the last clean checkpoint. If money or mail moved, replay from P1 on a new month instance.

Do not continue the dirty Handle graph. Do not “try the next AP invoice” on the same instance after an ImportError. The process is poisoned until wipe or clone.

---

## SOFT — log and finish

SOFT is anything that means the specialist did the wrong job with working doors.

Always SOFT (log, continue):

1. Skill loaded. Model ignored it. Tools still returned.
2. Skill steered a Kernel replay so hard that the Bot spent the turn restating `must_hold` and never chose among candidates (T6, T7). Tools returned. Tick RUNS for the op if called; SOFT for the skill.
3. Wrong Handle destination (collect → `ctl-cash` for write-off) **and** intercept/handle-map/BOT.md disagree. If intercept still routes to the wrong Verifier as config, that is HARD (T2/T9, a file). If config is right and the model handled the wrong Bot, SOFT.
4. Collect wrote an outbox draft with send tool present and did not send. Skill still says preview. SOFT on the skill. (If send tool is missing, HARD T3.)
5. Apply could have chosen a unique Kernel candidate and abstained with no tie. SOFT. Apply invented a combo Kernel did not offer. If Kernel accepted the invention, HARD (Kernel door). If Kernel refused and apply stopped, INTENDED fail-closed.
6. Story numbers not labeled UNLOCKED when lock is missing. Tools returned. SOFT.
7. Audit wrote vibe language without Kernel finding ids. Tools returned. SOFT.
8. Skill assigned to doer and Verifier produced the same ranking twice and the Verifier never looked for a reason to refuse. SOFT on Verifier skill remainder (T9 mush). Grants were fine.
9. Memory not written, or written and the next ticket in **this same instance** did not change. Log T10. Continue. Do not fail the pipe’s RUNS tick for T10 on the first month instance.

After the procedure’s last step:

1. Collect every SOFT row.
2. Edit `SKILL.md` and `BOT.md` as a batch. Edit Kernel `skills/` if Computer skills are copies. Keep `assignments.py` in sync. Do not hand-edit Grant ops.
3. Do not add a numbered Kernel checklist to make the next run look INTENDED.
4. New instance. Re-run that procedure (or the skill’s home procedure).
5. If the SOFT is gone, tick INTENDED. If it remains, keep SOFT. Three SOFTs on the same skill with no throw means the remainder is still wrong, not that you may freeze Kernel into the Skill.

A SOFT never justifies `r<n+1>` by itself **during** the procedure. Finish first. The instance is still a valid trace of “what the current skills did.”

---

## RUNS vs INTENDED

**RUNS** is the bare minimum for a tool or Bot:

- Bound
- Client Grant door opened
- Catalog op returned JSON without throw
- Handle reached `completed` or `rejected` (rejected with Kernel evidence is a terminal success of the bus)
- No Operator click in the completion path

**INTENDED** is the corpus outcome on the open item:

- AP: a real Kernel bill matched or HOLD for a real `must_hold` reason; pay-run is a Kernel-netted list; `ctl-pay` saw evidence
- AR: apply before collect; Kernel-allowed SEND_* in the simulated mailbox; World can reply if World is bound
- Cash: ticks apply/pay identifiers; `$12.40` unexplained
- Close: Computer `runs/`; lock not CLOSED; story UNLOCKED if unlocked; audit does not fix books

A procedure may declare itself “bare-min complete” when every step is RUNS, BLOCKED-CORRECT, or HONEST-EMPTY, and every HARD was patched and re-run to RUNS.

A procedure may declare itself “demo-ready” only when the INTENDED line in its done-when is true.

---

## Taxonomy labels (T1–T13)

When you write HARD or SOFT, also write the category from `docs/Agentic-update/02-failure-taxonomy.md`.

Examples:

- ImportError send: HARD T3 + T13
- World folder, not on Roster: SKIP or HARD T1 depending on whether the step required a mailbox round-trip
- Skill says preview, constructor says send, send exists, model previewed: SOFT T6
- INV-S12 marker: HARD T11 + T12 if you used it as the judged bill
- `$12.40` MATCHED: HARD T12 (and product law)

Do not create T14 in a log. If you need a new kind, write a sentence in `notes.md` and still pick HARD or SOFT.

---

## Who patches what

| Layer | HARD patch | SOFT patch |
| --- | --- | --- |
| Kernel `.cfo/` Python | yes | no |
| Constructor `tools=` | yes (then compile) | no |
| `catalog.json` / `grants.json` by hand | never | never |
| Client extension | yes | no |
| Harness `src/` generic only | yes | no |
| `intercept.json`, Handle unlock | yes | no |
| `SKILL.md` | no (unless the file causes a parse crash: HARD) | yes, after procedure |
| `BOT.md`, Roster `instructions` | only if path missing (P0 HARD) | yes, after procedure, for steer |
| `assignments.py` | if intersect drops a skill the Bot must have | if you reassign remainder |
| World pack / holdout | never to make close look good | never |

---

## Decision cheat sheet

```
Did something throw, fail to bind, or omit a door the Grant promised?
  yes → HARD → stop → patch code → new instance / wipe → replay
  no  → Did the corpus want this next state (including fail-closed)?
          yes → INTENDED (or BLOCKED-CORRECT)
          no  → Is the Profile honestly empty?
                  yes → HONEST-EMPTY
                  no  → Would a better Skill/BOT.md have changed the turn?
                          yes → SOFT → log → continue
                          no  → RUNS (door works; intended not claimed)
```

If you are unsure whether a miss is a missing door or a missing skill, look at `pi-rpc.jsonl`. No tool call and no Grant for that op → HARD T3. Tool call succeeded, wrong English or wrong Handle → SOFT.

---

## Logging minimum

Every classified step writes one row:

```
step: P2-S04
class: SOFT
t-categories: T6,T7
bot: ap
profile: prepare
ops: tools.get_invoice, tools.get_case_evidence
handle: h_…
note: restated must_hold; HOLD was Kernel-correct; skill added no remainder
```

HARD rows also attach the traceback. SOFT rows name the skill files to edit later.

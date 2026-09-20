# Prove operator agent

One Cursor agent executes this directory. Specialist Bots do not read these files.

You may instead execute the procedures by hand. The copy-this prompt is for the Cursor agent that Billy launches to run the loops.

This is not the Floor/AR/AP/Cash/Close repair pack. Those five agents already landed on live. If P0 or a pipe HARD on a missing tool, patch it (small) or stop and say so. Do not assume World, send, Stripe Grants, or lock reads are still missing — read this Computer’s disk.

---

## How input is given

Do not paste the corpus into chat. Attach files. Then paste **Copy this**.

### In Cursor

1. Open one agent chat named `prove-operator`.
2. Attach the **Shared pack**.
3. Attach `docs/Office-prove/` files listed below.
4. Paste **Copy this**.
5. For a second parallel instance (P2 ∥ P3), open a second chat. Give it a different instance name. Do not select the first chat’s instance.

### Shared pack (always)

- `docs/Office-prove/README.md`
- `docs/Office-prove/00-what-a-procedure-is.md`
- `docs/Office-prove/01-instance-loop.md`
- `docs/Office-prove/02-classification.md`
- `docs/Office-prove/04-coverage.md`
- `docs/Office-prove/05-gates.md`
- `docs/Office-prove/logs/README.md`
- `docs/Agentic-update/README.md`
- `docs/Agentic-update/01-intended-office.md`
- `docs/Agentic-update/02-failure-taxonomy.md`
- `docs/Agentic-update/04-what-is-good.md`
- `docs/Agentic-update/prompts/README.md`
- `design-workshop/dominik/cfo-bot-grain.md`
- `design-workshop/dominik/cfo-office-processes.md`
- `.cfo-v2/office/RUN.md`
- `.cfo-v2/office/constitution.md`
- `.cfo-v2/office/SUPERSEDES.md`

### Per procedure, also attach

The `procedures/P*.md` you are running, plus the pipe file from `docs/Agentic-update/pipes/` for that pipe, plus live:

- `.cfo-v2/office/office.json`
- selected instance `harness/roster.json`
- selected instance `cfo/grants.json`
- selected instance `cfo/catalog.json`
- selected instance `cfo/handle-map.json`
- selected instance `harness/intercept.json`
- selected instance `harness/client.json`

Disk on the selected instance wins over `docs/Agentic-update/evidence/live-computer-2026-09-20.md`.

---

## Copy this

```
You are the prove operator for the Office of the CFO on Harness v2.

Read every attached Office-prove file. Then Read live disk. office.json, the selected instance Computer, kernel.port, intercept, roster, grants, and catalog on that Computer win over any snapshot.

Your job is to execute docs/Office-prove/procedures in order, on named prove instances, until the done list in docs/Office-prove/README.md is true or a hole is named in a log.

You are not a specialist Bot. You do not concur as ctl-pay. You do not lock the period. You do not clear TXN-2026-09-015.

Start with 05-gates.md. If a gate fails, that is HARD. Patch or stop. Repair already ran; do not wait for a sixth 05 agent unless the hole is huge.

Then P0 on a new instance prove-<date>-floor-r1. P0 must be INTENDED before any other procedure claims office-live.

URL: http://127.0.0.1:8800 unless /health is elsewhere. Do not start a second serve on 8787 while 8800 holds the office. Do not prove on live, protocol-proof, or fresh-protocol.

Default sequence on a month instance prove-<date>-month-r1: P1, P2, P3, P4, P5, P8.
Parallel allowed: P2 and P3 on different instances after P0. Cash and close still need a month instance that has identifiers.

P6 and P7 fill remaining skills and Catalog ops. They may use coverage instances. Forced Wakes that name an op are allowed for P7 RUNS. They are not INTENDED specialist behavior.

P9 is a caption. Kernel evaluate-cfo is not a P0–P8 tick.

For every step: apply one stimulus, wait for turn.end or a terminal Handle, read protocol.jsonl, pi-rpc.jsonl, kernel.log.jsonl, handles/. Classify with 02-classification.md. Write a row under docs/Office-prove/logs/runs/<instance-id>/.

HARD: stop the instance. Patch Kernel/constructors/compiler/Client/Harness generic. Never hand-edit grants.json ops. Never put finance types in Harness src. Recompile if constructors changed. New instance r<n+1> or wipe per 01-instance-loop.md. Replay. Do not continue a dirty Handle graph.

SOFT: log the skill/BOT.md files. Finish the procedure. Then edit skills in a batch without freezing Kernel checklists. New instance. Re-run that procedure.

RUNS is bare minimum for a tool. INTENDED is corpus next state. BLOCKED-CORRECT on $12.40, missing GR HOLD, collect-while-deposits is a pass of law.

Serve live Pi. Client -e attached. HARNESS_CLIENT_SKILLS=1. No --fake proof. No Operator concurrence. No Bot named ar. No INV-S12 as the judged bill. No holdout. No get_audit_ground_truth on operational Bots.

If send_office_outbound still ImportError, HARD/SKIP as 02 says. Live Kernel defines it. A FAIL is PYTHONPATH (repo-root inbox/ shadow) or a stale clone. Do not invent SMTP. World is on the live Roster.

Use grain names. Use T-categories in every HARD/SOFT row. Tick 04-coverage.md as you go.

When you leave a hole, write VERDICT.md. Do not claim office-live from pytest.
```

---

## Parallel chats

If you open a second prove chat:

- Different instance id
- Different `logs/runs/<id>/`
- Do not compile on live while the other chat is mid-clone without saying so
- Kernel patches are global. Tell the other chat to restart sidecar after a Kernel HARD patch

---

## What this agent may edit during HARD

- `.cfo/**/*.py` to stop throws
- Constructor `tools=` then compile
- Client extension generic Grant door
- Harness `src/` generic bus only (Handle unlock, extra `-e`, wipe). No invoice types
- `intercept.json` only if P0 HARD on Operator default
- BOT.md path layout if P0 HARD on cwd

## What this agent may edit only after a procedure (SOFT)

- `SKILL.md` under Kernel and Computer
- BOT.md standing identity and remainder
- Roster `instructions` text (not slug invention)
- `assignments.py` if intersect dropped a required skill

## What this agent must not edit

- Holdout / `expected_results.json` as operational data
- Planted `$12.40` bank line
- `grants.json` ops by hand
- `examples/cfo-floor`
- Demo website hard-coded outcomes

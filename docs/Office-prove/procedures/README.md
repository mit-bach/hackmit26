# Procedures

Each file is a restartable loop. Shared law: `../00-what-a-procedure-is.md`, `../01-instance-loop.md`, `../02-classification.md`. Tick `../04-coverage.md`. Classify every step.

---

## Shared step shape

Every step in P0–P9 uses this shape. If a step is missing a field, fill it before you run it.

```
### Snn — title
- Stimulus:
- Actor: Bot `slug` / Profile `name` (Display name)
- Must call:
- May call:
- Must not:
- Observe:
- RUNS when:
- INTENDED when:
- HARD if:
- SOFT if:
- Ticks:
```

Wait for `turn.end` in protocol or a terminal Handle status before you classify. Do not classify from a streaming sentence.

Serve URL below is `{URL}`. Default `http://127.0.0.1:8787`. Computer is `{COMPUTER}` = selected instance root.

---

## Shared stimuli snippets

Spawn:

```bash
curl -sS -X POST {URL}/api/bots/ap/spawn
```

Prove Wake (test Handle, not concurrence):

```bash
curl -sS -X POST {URL}/api/bots/ap/messages \
  -H 'content-type: application/json' \
  -d '{"text":"profile: prepare\n..."}'
```

Routine:

```bash
curl -sS -X POST {URL}/api/routines/weekly-pay-run/run
# or from Harness root:
# npx harness routine weekly-pay-run --computer {COMPUTER}
```

Observe:

```bash
curl -sS {URL}/api/bots/ap
curl -sS {URL}/api/handles
tail -n 50 {COMPUTER}/cfo/kernel.log.jsonl
tail -n 80 {COMPUTER}/harness/bots/bot_ap/pi-rpc.jsonl
```

---

## Order

| Id | File | Instance | Parallel |
| --- | --- | --- | --- |
| P0 | `P0-floor.md` | `prove-<date>-floor-rN` | no |
| P1 | `P1-intake.md` | month or pipe instance | with nothing that shares the instance |
| P2 | `P2-ap.md` | month or `prove-<date>-ap-rN` | ∥ P3 on another instance |
| P3 | `P3-ar.md` | month or `prove-<date>-ar-rN` | ∥ P2 on another instance |
| P4 | `P4-cash.md` | month (needs identifiers) | no |
| P5 | `P5-close.md` | month | no |
| P6 | `P6-skill-sweep.md` | coverage instance ok | ∥ P7 |
| P7 | `P7-catalog.md` | coverage instance ok | ∥ P6 |
| P8 | `P8-cross-pipe.md` | month | no |
| P9 | `P9-kernel-eval-bridge.md` | live Kernel, not a Bot desk | anytime as caption |

---

## Month instance default

After P0 INTENDED on the template, create `prove-<date>-month-r1`, select it, re-check P0 S01–S04 quickly (bind + sidecar on the new Computer), then P1→P8 on that desk.

If P2 HARD, do not keep going to P4 on the same dirty graph. Patch. `month-r2`. Replay P1.

---

## Profile header required

Every prove Wake starts with `profile: <slug-map profile key>` so the Client does not union Grants. If a turn ran two Profiles, HARD T6/T8.

# Logs

Judgments live here. Traces live on the instance Computer. Wipe deletes traces. Wipe must not delete judgments.

---

## Layout

```
docs/Office-prove/logs/
  README.md                 this file
  TEMPLATE-run.md
  TEMPLATE-hard-fail.md
  TEMPLATE-soft-fail.md
  TEMPLATE-verdict.md
  ROLLUP.md                 create after the first procedure; keep updating
  runs/
    _gates/GATES.md         05-gates.md results
    <instance-id>/
      README.md             copy TEMPLATE-run.md
      CHECKPOINT.md
      HARD.md               if needed
      SOFT.md               append-only
      coverage.md           ticks for this instance
      VERDICT.md
      notes.md
```

Copy templates. Do not fill templates in place.

---

## Rules

1. Create `runs/<instance-id>/` before the first stimulus.
2. One row per classified step, at the time of classification. Do not reconstruct from memory after wipe.
3. Quote traceback text. Do not paraphrase ImportError.
4. Name T-categories.
5. Name the skill files a SOFT will edit. Name the Python files a HARD will edit.
6. `ROLLUP.md` is the operation-level view across instances. Update it when a procedure ends.
7. Never write secrets (provider keys). `client.json` may exist on the Computer. Do not copy keys here.

---

## After wipe

The Computer traces are gone. The log directory remains. The next instance is `r<n+1>` with a new folder. Link the previous HARD.md in CHECKPOINT.md: “replay of prove-…-r1 P2-S04 after patch X.”

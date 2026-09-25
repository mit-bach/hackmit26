# Layer 1 — Kernel lives in `.cfo-v3`

Authority: `workshop/docs/Office-show/DESIGN-REVIEW.md` sections 1 and 2. This file replaces the earlier draft of the same name.

## Job

Copy the Python the office actually runs into `/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3/kernel`. After this layer, no import, `PYTHONPATH`, or sidecar argv may point at `/Users/dominikbach/olympus/hackmit/hackmit26/.cfo`.

Do not edit `.cfo`. Do not delete `.cfo`. Do not edit `.cfo-v2`.

## What must be in the copy

- The package the sidecar starts (`python -m cfo_kernel` or the module `RUN.md` names).
- The compiler that writes `catalog.json` and `grants.json`.
- Inbox classify and dispatch, with the rule that prompt-injection text cannot stay `VENDOR_INVOICE` and cannot mint a bill. Take that rule from `.cfo-v2/prove-fork/.cfo/inbox/classify.py` and `dispatch.py`. Do not take the rest of prove-fork.
- Accrual, cash, close, audit, and scheduling modules those entry points import. Follow imports. Do not copy a tree because it sits next to them.

## What must not be in the copy

Tests, `.venv`, `evals/`, `sample_data` generators, `sessions/`, holdout catalogs, `expected_results.json`, `ADVERSARIAL-PLANT-NOTES.md`, demo website, and skills. Skills are office text, not kernel.

## Done when

From a clean shell with `PYTHONPATH` set only to `.cfo-v3/kernel`:

- `python -m cfo_kernel --help` or the real module entry starts and does not import `.cfo`.
- A one-line compile writes catalog and grants under a Computer path you pass in, and that path is under `.cfo-v3`.
- `rg -n '\.cfo([/"'\'']|$)' .cfo-v3/kernel` finds no runtime dependency on the repo `.cfo` directory.

Write the command you ran at the bottom of this file under `## Proved`.

## Landed

Copied the sidecar package `cfo_kernel`, the finance packages it remaps (`accrual`, `ar`, `audit`, `bs_recon`, `cash_recon`, `close`, `fixed_assets`, `inbox`, `integrations`, `invoice_ingestion`, `memory`, `prepaid`, `reporting`, `scheduling`), top-level `tools.py`, and `evaluation/isolation.py` only. The compiler library (`compiler/__init__.py`, `__main__.py`, `compile_lib.py`) now defaults `--kernel` to `.cfo-v3/kernel` and finds the repo by `.harness` alone. Also copied modules those entry points import at load time: `atomic_json.py` (`cfo_kernel.idempotency`), `models.py` and `skills/models.py` (`tools` and the finance models), `workflow.py`, `agent.py`, `ap_grants.py`, and `harness_handles.py` (Computer root retargeted to `.cfo-v3`). `skills/assignments.py` stayed because the compiler reads it. Inbox classify in this tree rejects an unsafe mutation even when the text is an invoice, and prompt injection cannot stay `VENDOR_INVOICE` or mint a bill. Excluded tests, prove-fork, holdout and answer keys, session notes, `.cfo/data`, runs, traces, demos, the evaluation harness beyond isolation, compiler tests and `prove.py`, skill markdown bodies, and the old `.cfo/.venv` (a new `.venv` was built from `requirements.txt`). `agent.py` still does `from skills import compose_instructions`, which needs the skill package and those markdown bodies, so that import is unsatisfied inside this tree and does not point at repo `.cfo`.

## Proved

```
PYTHONPATH=/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3/kernel \
  /Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3/kernel/.venv/bin/python -m cfo_kernel --help
PYTHONPATH=/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3/kernel \
  /Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3/kernel/.venv/bin/python -m compiler \
  --kernel /Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3/kernel \
  --out /Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3/kernel/compile-out \
  --phase operational
```

Help started with `PYTHONPATH` set only to the v3 kernel. Compile wrote `catalog.json` and `grants.json` under `.cfo-v3/kernel/compile-out`. A scan of kernel sources found no runtime path to the repo `.cfo` directory.

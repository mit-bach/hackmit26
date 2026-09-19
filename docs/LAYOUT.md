# Repository layout

This git root is the Obsidian vault. Hidden directories are skipped by Obsidian. Git still tracks them.

| Path | Role |
| --- | --- |
| `docs/` | Product documentation. Start with [AGENTIC_SYSTEM_WORKFLOW.md](AGENTIC_SYSTEM_WORKFLOW.md). |
| `design-workshop/` | Design notes. |
| `Operator-workspace/` | Human workspace. Agents do not edit this tree. |
| `GROK-WORKSHOP/` | Workshop notes for harness bring-up. |
| `.cfo/` | Office of the CFO Python kernel: packages, skills, tests, `data/`, `runs/`. Hidden from Obsidian. |
| `.harness/` | Harness v1 (local, untracked) and Harness v2. Hidden from Obsidian. |
| `main.py`, `accrue.py`, `close.py`, `demo_month_end_close.py` | Thin shims. They `chdir` into `.cfo/` so documented CLI commands still work from the repo root. |

Module form from the repo root:

```bash
PYTHONPATH=.cfo python -m reporting.demo
```

Harness v2 from the repo root:

```bash
cd .harness/Harness-v2
npm install
npm test
```

Do not open `.cfo/` or `.harness/` as the Obsidian vault. Open this repository root.

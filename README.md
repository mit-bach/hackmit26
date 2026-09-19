# HackMIT 26 — Office of the CFO

This directory is the Obsidian vault. Python, skills, run artifacts, and Harness live in hidden folders so Obsidian does not index them.

| Open in Obsidian | Hidden from Obsidian (still in git) |
| --- | --- |
| `docs/` | `.cfo/` — finance kernel, agents, skills, tests, data, runs |
| `design-workshop/` | `.harness/` — Harness v1 / v2 |
| `Operator-workspace/` | |
| this README | |

Layout details: [`docs/LAYOUT.md`](docs/LAYOUT.md).

Architecture: [`docs/AGENTIC_SYSTEM_WORKFLOW.md`](docs/AGENTIC_SYSTEM_WORKFLOW.md).

## Python kernel

The engine README is [`.cfo/README.md`](.cfo/README.md). Copy [`.cfo/.env.example`](.cfo/.env.example) to `.cfo/.env`.

From this repo root, the old commands still work (shims enter `.cfo/`):

```bash
python3 -m venv .cfo/.venv
source .cfo/.venv/bin/activate
pip install -r requirements.txt
python main.py INV-001
python main.py skills
pytest
```

## Harness

```bash
cd .harness/Harness-v2
npm install
npm test
```

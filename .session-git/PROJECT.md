# session-git project card

**Project root:** `/Users/dominikbach/olympus/hackmit/hackmit26`

Shared repo with Rohan (`origin` = `github.com/rohan9314/hackmit26`). The git root is an Obsidian vault. Product code lives in hidden directories so Obsidian does not index it.

## Zone map

| role | roots / includes | agent write | land |
|------|------------------|-------------|------|
| product (A) | `.cfo/`, `.harness/`, `.cfo-v2/` (Client attach: compiler, Computer, Pi facade), root shims (`main.py`, `accrue.py`, `close.py`, `demo_month_end_close.py`), `pytest.ini`, `requirements.txt` | yes | pathspec |
| product-docs (B) | `docs/`, `README.md` | yes | docs |
| human-notes (C) | `Operator-workspace/` | never | notes: human |
| design-prep (D) | `design-workshop/`, `GROK-WORKSHOP/` | yes | freeze/docs |
| ide-noise (F) | `.obsidian/` | no | never |
| vendored-noise (H) | `node_modules/`, leftover `harness-impl/` runtime | no | never |
| project-config (I) | `.cursor/`, `.gitignore` | yes | chore |
| overlay (K) | `.session-git/` | yes | separate from product |

## Never land

- `.env`, `.obsidian/`, `node_modules/`, `__pycache__/`, `.DS_Store`
- leftover `harness-impl/` (live lock files after the rename)
- untracked `.harness/Harness-v1/` unless Rohan asks to adopt it
- in-progress Harness-v2 source edits parked outside the reorg commit

## Landing rules

- Pathspec only. No `git add -A`.
- End of turn: one logical land or leave dirty. Split overlay (K) from product (A) from docs (B).
- Session trailer: `session: <title>` on commits.
- Human-notes: agent never edits `Operator-workspace/`.

## Child-lite

- Read this file.
- Do not invent Operator-Workspace or A-OS paths. `Operator-workspace/` already exists here; it is human-notes.
- Leave dirty for parent unless told to land.
- If product is UNCLASSIFIED, escalate overlay fix to parent.
- Session 01+ Client attach lands under `.cfo-v2/` (product A). Do not put finance types in `.harness/Harness-v2/src`.

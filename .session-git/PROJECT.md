# session-git project card

**Project root:** `/Users/dominikbach/olympus/hackmit/hackmit26`

Shared repo with Rohan (`origin` = `github.com/rohan9314/hackmit26`). Git root is the GitHub face and Obsidian vault.

## Zone map

| role | roots / includes | agent write | land |
|------|------------------|-------------|------|
| product (A) | `.cfo/`, `.cfo-v2/`, `.harness/`, `web/`, root shims, `vercel.json` | yes | pathspec |
| product-docs (B) | `workshop/docs/`, `README.md`, `workshop/README.md` | yes | docs |
| human-notes (C) | `workshop/operator-workspace/` | never | notes: human |
| design-prep (D) | `workshop/design-workshop/`, `workshop/grok-workshop/`, `workshop/` | yes | freeze/docs |
| dead-archive (G) | `.archive/` | no | avoid |
| ide-noise (F) | `.obsidian/` | no | never |
| overlay (K) | `.session-git/` | yes | separate from product |

## Never land

- `.env`, `.obsidian/`, `node_modules/`, `__pycache__/`, `.DS_Store`, `kernel.port`
- Live office dirt under `.cfo-v2/office/computer` and `instances/` unless the operator asked to save a desk
- `workshop/grok-workshop/harness-init/facecam-record/` while that session is writing
- untracked `.harness/Harness-v1/`
- `.archive/` except a README that explains why the shadow exists

## Landing rules

- Pathspec only. No `git add -A`.
- Overlay (K) separate from product (A) from docs (B).
- Session trailer: `session: <title>` on commits.
- Do not edit `workshop/operator-workspace/`.
- Sidecar and website need `.cfo/` as well as `.cfo-v2/` and `.harness/`. Do not delete `.cfo/`.

## Child-lite

- Read this file.
- Do not invent Operator-Workspace A-OS roots. `workshop/operator-workspace/` is human-notes.
- Leave dirty for parent unless told to land.

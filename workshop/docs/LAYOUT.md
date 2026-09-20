# Repository layout

The git root is the vault and the GitHub face. Hidden directories hold the product.

| Path | Role |
| --- | --- |
| `.cfo/` | Python kernel. |
| `.cfo-v2/` | Harness office (Client system). |
| `.harness/` | Harness v2 runtime. |
| `web/` | Vite website. Vercel output. |
| `workshop/` | Notes: product docs, design-workshop, operator-workspace. |
| `.archive/root-kernel-shadow/` | Leftover root Python. Not imported. |
| `GROK-WORKSHOP/` | Live harness workshop (still at root). |
| `main.py`, `demo_web.py` | Shims into `.cfo/`. |

Compatibility links at the repo root: `docs` → `workshop/docs`, `design-workshop` → `workshop/design-workshop`, `Operator-workspace` → `workshop/operator-workspace`.

See the root [README](../../README.md).

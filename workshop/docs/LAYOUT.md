# Repository layout

Visible at the git root: `README.md`, `web/`, `workshop/`, `package.json`, `vercel.json`, `requirements.txt`.

| Path | Role |
| --- | --- |
| `.cfo/` | Python kernel. |
| `.cfo-v2/` | Harness office. |
| `.harness/` | Harness v2 runtime. |
| `web/` | Vite website. Vercel output. |
| `workshop/` | Notes, design, grok-workshop, scripts. |
| `.archive/` | Leftover root Python. Not imported. |

Kernel CLI: `cd .cfo && python main.py`. Website API: `cd .cfo && python -m demo_web`. Tests: `pytest` from the repo root (`.pytest.ini`).

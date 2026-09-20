# Maximor — Office of the CFO

HackMIT 2026. A simulated company (Maximor Demo Corp, September 2026) run by a Python finance kernel, a Harness office of standing Bots, and a website for judges.

There are two people in this repo. **Rohan** built the kernel: invoices, cash, close, audit, inbox, the first demo site. **Dominik** built the Harness office that sits on that kernel, the operator desk, and the later website overhaul. The kernel was not replaced. The office calls it.

## What you are looking at

Open this folder as the git root. Hidden directories (names that start with `.`) are still in git. Obsidian skips them.

| Path | What it is | Who |
| --- | --- | --- |
| [`.cfo/`](.cfo/README.md) | Finance **kernel**. Arithmetic, JSON books, skills, pytest, demo API. | Rohan (kernel). Dominik added `demo_web` and office remaps. |
| [`.cfo-v2/`](.cfo-v2/README.md) | **Office** on Harness: 16 Bots, Catalog, Grants, Computer, prove/show instances. | Dominik |
| [`.harness/Harness-v2/`](.harness/Harness-v2/README.md) | Harness runtime (Handles, rooms, Demo UI). Not finance. | Dominik |
| [`web/`](web/) | Vite website. Vercel builds this. | Rohan started it. Dominik overhauled routes and copy. |
| [`workshop/`](workshop/README.md) | Design notes, prove/show procedures, operator prompts. | Mixed. See the workshop README. |
| [`.archive/root-kernel-shadow/`](.archive/README.md) | Incomplete Python folders Rohan re-created at the repo root after the kernel moved into `.cfo/`. Not on the run path. | Rohan |

`GROK-WORKSHOP/` stays at the root while a live session writes into it. It belongs with the workshop notes when that session is idle.

Root CLI files (`main.py`, `demo_web.py`, …) are shims. They `chdir` into `.cfo/`.

## Run the website (what Vercel hosts)

Vercel builds `web/` (`vercel.json`). That is a static UI. Live numbers need the kernel API on your machine.

```bash
python3 -m venv .cfo/.venv
source .cfo/.venv/bin/activate
pip install -r requirements.txt
python demo_web.py --host 127.0.0.1 --port 8765
```

```bash
cd web
npm install
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` to port 8765.

Without the API, the hosted site shows saved demonstration results. It does not invent a second ledger.

Copy `.cfo/.env.example` to `.cfo/.env` if you use `OPENAI_API_KEY`. Default demo paths do not need a key.

## Run the office (standing Bots)

The office is `.cfo-v2` plus `.harness`. The sidecar still loads the kernel from `.cfo/`. That is required. Do not point live Bots at leftover folders in `.archive/`.

One-time:

```bash
source .cfo/.venv/bin/activate
pip install -r requirements.txt
cd .harness/Harness-v2 && npm install && cd ../..
cd .cfo-v2/office/computer/cfo && npm install && cd ../../../..
```

Then follow [`.cfo-v2/office/RUN.md`](.cfo-v2/office/RUN.md): compile Catalog, start the kernel sidecar, start Harness `serve` on the Computer.

Kernel CLI (same venv):

```bash
python main.py INV-001
python main.py skills
python main.py demo-inbox
pytest
```

## How the pieces connect

1. **Source data** — `.cfo/data/demo/` (immutable pack) and `.cfo-v2/office/world/` (office World).
2. **Kernel** — `.cfo/` computes candidates, postings, gates. An LLM does not own a ledger total.
3. **Office** — `.cfo-v2/office/computer` is the Harness Computer. Bots send Handles. The sidecar calls Kernel ops the Bot is granted.
4. **Website** — `web/` + `.cfo/demo_web/` read the same books and invoke the same workflows.

Do not treat `.harness/Harness-v2/examples/cfo-floor` as this office. That example is a six-Bot bind fixture.

## Explore without running Bots

| If you want | Open |
| --- | --- |
| Judge website | `web/src/` and `python demo_web.py` |
| Kernel architecture | `workshop/docs/AGENTIC_SYSTEM_WORKFLOW.md` |
| Website architecture | `workshop/docs/demo_website_architecture.md` |
| Office boot | `.cfo-v2/office/RUN.md` |
| What the office refuses | `.cfo-v2/office/SUPERSEDES.md` |
| Prove the door | `workshop/docs/Office-prove/` |
| Record the show | `workshop/docs/Office-show/` |
| Bot grain (why 16, not 6) | `workshop/design-workshop/dominik/cfo-bot-grain.md` |

Compatibility links `docs`, `design-workshop`, and `Operator-workspace` still point at `workshop/` so older paths resolve.

## Tests

```bash
source .cfo/.venv/bin/activate
pytest
cd web && npm test
cd .harness/Harness-v2 && npm test
```

## Environment

| Variable | Role |
| --- | --- |
| `OPENAI_API_KEY` | Optional for deterministic kernel demos. Required for live Pi Bots. |
| `HARNESS_COMPUTER` | Office Computer directory. Sidecar remaps `data/` and `runs/` here. |
| `STRIPE_MODE` | `mock` (default) or `live`. |
| `DEMO_LIVE_LLM=1` | Website AP path uses live agent turns. Default is kernel-deterministic. |

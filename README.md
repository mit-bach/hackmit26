# Maximor — Office of the CFO

HackMIT 2026. Maximor Demo Corp (September 2026): a Python finance kernel, a Harness office of standing Bots, and a website.

This git root is meant to stay small. Hidden folders (names that start with `.`) hold the engines. Notes live in `workshop/`.

| Path | What it is |
| --- | --- |
| [`.cfo/`](.cfo/README.md) | Finance kernel (Rohan). Demo API and remaps (Dominik). |
| [`.cfo-v2/`](.cfo-v2/README.md) | Office on Harness: 16 Bots, Catalog, Grants (Dominik). |
| [`.harness/Harness-v2/`](.harness/Harness-v2/README.md) | Harness runtime. Not finance (Dominik). |
| [`web/`](web/) | Vite website. Vercel builds this. |
| [`workshop/`](workshop/README.md) | Docs, design notes, Grok workshop, operator prompts. |
| [`.archive/`](.archive/README.md) | Leftover root Python. Not imported. |

## Website (Vercel)

Vercel builds `web/` (`vercel.json`). Live numbers need the kernel API on your machine.

```bash
python3 -m venv .cfo/.venv
source .cfo/.venv/bin/activate
pip install -r requirements.txt
cd .cfo && python -m demo_web --host 127.0.0.1 --port 8765
```

```bash
cd web
npm install
npm run dev
```

Open http://127.0.0.1:5173. Without the API, the hosted site shows saved demonstration results.

Copy `.cfo/.env.example` to `.cfo/.env` if you use `OPENAI_API_KEY`. Default demo paths do not need a key.

## Office (standing Bots)

The sidecar loads the kernel from `.cfo/`. That is required. Follow [`.cfo-v2/office/RUN.md`](.cfo-v2/office/RUN.md).

```bash
source .cfo/.venv/bin/activate
pip install -r requirements.txt
cd .harness/Harness-v2 && npm install && cd ../..
cd .cfo-v2/office/computer/cfo && npm install
```

## Kernel CLI

```bash
source .cfo/.venv/bin/activate
cd .cfo
python main.py INV-001
python main.py skills
python main.py demo-inbox
```

From the repo root:

```bash
pytest
```

## Explore

| If you want | Open |
| --- | --- |
| Kernel architecture | `workshop/docs/AGENTIC_SYSTEM_WORKFLOW.md` |
| Website architecture | `workshop/docs/demo_website_architecture.md` |
| Office boot | `.cfo-v2/office/RUN.md` |
| What the office refuses | `.cfo-v2/office/SUPERSEDES.md` |
| Prove | `workshop/docs/Office-prove/` |
| Show | `workshop/docs/Office-show/` |
| Bot grain | `workshop/design-workshop/dominik/cfo-bot-grain.md` |

# Maximor — Office of the CFO

HackMIT 2026. Maximor Demo Corp (September 2026): a Python finance kernel, a Harness office of standing Bots, and a website.

Working copy: [github.com/mit-bach/hackmit26](https://github.com/mit-bach/hackmit26).

This git root is meant to stay small. Hidden folders (names that start with `.`) hold the engines. Notes live in `workshop/`.

## Open it on a new machine

You need Node.js 22 or newer, Python 3.11 or newer, and the Pi CLI. macOS or Linux.

### 1. Tools

```bash
node -v
python3 --version
```

Install [Node.js](https://nodejs.org/) and Python if those commands fail.

Pi is the worker that runs each Bot. Install it once:

```bash
npm install -g @earendil-works/pi-coding-agent
pi --version
```

### 2. Clone

```bash
git clone https://github.com/mit-bach/hackmit26.git
cd hackmit26
```

### 3. Python kernel

```bash
python3 -m venv .cfo/.venv
source .cfo/.venv/bin/activate
pip install -r requirements.txt
```

Copy `.cfo/.env.example` to `.cfo/.env` only if you set `OPENAI_API_KEY`. The September demo pack runs without that key. Live Pi turns need a model key in the office UI (Settings) after the server is up.

### 4. Office and Harness

From the repo root, with the venv still active:

```bash
cd .harness/Harness-v2
npm install
npm run build
cd ../..

cd .cfo-v2/office/computer/cfo
npm install
cd ../../../..

ln -sfn ../world/maximor .cfo-v2/office/computer/data
mkdir -p .cfo-v2/office/computer/runs

PYTHONPATH=.cfo-v2/office python3 -m compiler --phase operational
```

The compiler writes the Catalog and Grants under the Computer. Do not hand-edit `grants.json`.

### 5. Start the office

`office.json` selects which Computer the server actually serves. The recorded September desk is `golden-20260920-r1`. Leave that id in place if you want the demo tape. To work on the live template, set `"currentId": "live"` in `.cfo-v2/office/office.json` before you start.

```bash
source .cfo/.venv/bin/activate
cd .harness/Harness-v2
node dist/src/cli.js serve --computer ../../.cfo-v2/office/computer --no-open --port 8800
```

Leave that process running. In another terminal:

```bash
open http://127.0.0.1:8800/
```

On Linux, use `xdg-open http://127.0.0.1:8800/` instead of `open`.

The page is the operator desk. Tools → Demo → recording plays the saved September tape when `currentId` is `golden-20260920-r1`.

Health check:

```bash
curl -sS http://127.0.0.1:8800/health
```

`fakeWorkers` should be `false` and `bots` should be `16`.

### 6. Website (optional)

The kernel demo API and the Vite site are separate from the office on port 8800.

```bash
source .cfo/.venv/bin/activate
cd .cfo && python -m demo_web --host 127.0.0.1 --port 8765
```

```bash
cd web
npm install
npm run dev
```

Open http://127.0.0.1:5173. Without the API on 8765, the site shows saved demonstration results.

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

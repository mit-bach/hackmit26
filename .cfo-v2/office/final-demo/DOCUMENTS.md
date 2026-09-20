# Document map

What to trust, what to ignore, and where the World pack lives. Paths are from the repo root.

## Canonical (use these)

| Path | What it is | Notes |
| --- | --- | --- |
| `.cfo-v2/office/final-demo/CAPABILITIES.md` | Product capability account | Current + planned. Prefer this over V1 JSON. |
| `.cfo-v2/office/final-demo/WORLD.md` | World pack census | Written against the data agent's output. |
| `.cfo-v2/office/final-demo/TESTING.md` | How we test | Kernel vs office vs holdout. |
| `.cfo-v2/office/final-demo/SCENARIOS.md` | Website scenario cards | Planted vs holdout. |
| `.cfo-v2/office/final-demo/scenarios.json` | Machine cards | No answer keys. |
| `.cfo-v2/office/world/maximor/` | Books the Computer loads | Symlinked at `computer/data`. |
| `.cfo-v2/office/constitution.md` | Office law | Still says fifteen grain Bots. World is an added Source Bot. SUPERSEDES human-in-the-loop completion. |
| `.cfo-v2/office/computer/harness/roster.json` | Standing Bots on disk | **15 slugs today.** World package is beside it, not in this file. |
| `.cfo-v2/office/computer/cfo/catalog.json` | Kernel ops | Includes inbox compose/send/classify. |
| `.cfo-v2/office/computer/cfo/grants.json` | Per Display name Grants | Counterparty Message Agent and Finance Inbox Agent are present. |
| `.cfo-v2/office/computer/cfo/handle-map.json` | Peer Handle edges | No World edges on disk today. |
| `.cfo-v2/office/computer/cfo/slug-map.json` | Slug → Profiles | No `world` key on disk today. |
| `.cfo-v2/office/bots/*/BOT.md` | Per-Bot law | Includes `bots/world/BOT.md`. |
| `.cfo-v2/office/RUN.md` | How to boot | Computer data symlink to `world/maximor`. Section 6 still calls inbox “not a sixteenth Bot.” That sentence is stale relative to World. |
| `docs/evaluation.md` | Maximor Finance Gauntlet | Our Kernel measure. Inspired by Invoice Sandbox, RecBench, APEX, DABstep, AccountingBench. Not those leaderboards. |
| `docs/demo-capability-gaps.md` | Honest gaps | AP learning, vendor bank-change control, Close Manager SDK, credit-memo lifecycle, graph memory. Still accurate. |
| `design-workshop/dominik/Maximor-HackMIT-Track.md` | Track brief | Example processes are a starting point. Adversarial holdout is larger. |
| `design-workshop/dominik/cfo-bot-grain.md` | Grain tests A–D | Adding World required passing those tests. |

## World pack files (data, not prose)

Under `.cfo-v2/office/world/maximor/`:

| File | Load in website? | Load in operational Bots? |
| --- | --- | --- |
| `company.json`, `vendors.json`, `customers.json`, `invoices.json`, AP/AR/cash/close/audit/reporting trees, `documents/` | Yes, as company state | Yes |
| `canonical/scenarios.json`, `canonical/storylines.json`, `timeline.json`, `lineage.json`, `demo_snapshot.json`, `demo_queries.json` | Yes, as cards and graph | Prompts only. Not gold. |
| `inbox/messages.json`, `ingestion/emails.json` | Yes | Yes |
| `system_capabilities.json` | Architecture reference only. Prefer `CAPABILITIES.md` | No need |
| `manifest.json` | Census | No need |
| `expected_results.json` | After a scored eval, grader UI only | **Never** |
| `expected_outcomes.json` | Same | **Never** |
| `agent_cases.json` | IDs and tags yes. `expected` block no until scored | **Never** the expected block |
| `holdout/round2_hooks.json` | No | **Never** |
| `cash_recon/ground_truth.json`, `audit/ground_truth.json`, Stripe eval gold | No | **Never** |

## Relevant, not canonical prose

| Path | Status | Use |
| --- | --- | --- |
| `.cfo-v2/office/sessions/ADVERSARIAL-SCENARIOS.md` | Working catalog. 109 scenarios, 12 storylines | Phase B plant spec. Bots never load it. Website holdout tab may use the summary in `SCENARIOS.md`, not this raw file. |
| `.cfo-v2/office/sessions/adversarial-scenarios.index.json` | Machine index of the catalog | Same rule. |
| `design-workshop/dominik/Prompts/DATA-REFINEMENT-CURSOR.md` | Prompt that produced the World pack (Phase A) | History. Do not run it as a Bot. |
| `design-workshop/dominik/Prompts/ADVERSARIAL-PLANT-CURSOR.md` | Paste into a new Cursor session for Phase B | Plants all 109 ADV-* into `world/maximor` through the generator. |
| `.cfo-v2/office/sessions/BENCHMARK-IMPORT.md` | Census of gitignored `reference-datasets/` | Invoice Sandbox, APEX, DABstep context, RecBench small. Quality bar, not a second company. |
| `docs/demo_website_architecture.md` | Partner website design | Routes and Kernel POST map are useful. Stale: fifteen Bots, canonical path `.cfo/data/demo`. Point at `world/maximor` and this folder. |
| `docs/demo-data.md` | Original pack README | Stale counts ($1M monthly P&L, `data/demo`). Plot IDs are still the plot IDs. |
| `docs/CFO_HARNESS_EXTENSION.md` | Compiler, sidecar, facade | Obey SUPERSEDES in the constitution. |
| `docs/LAYOUT.md` | Tree layout | Still useful. |
| `.cfo/docs/organizational-memory.md` | Memory design | Kernel memory, not a graph DB. |

## Deprecated as product story

Keep the files. Do not copy claims forward without checking this folder.

| Path | Why it is stale |
| --- | --- |
| `.cfo-v2/office/DEMO-DESIGN.md` | Design memo from 2026-09-19. Computer now points at `world/maximor`. World exists as a Bot package. Counts in the table are old. |
| `.cfo-v2/office/DEMO-WALKTHROUGH.md` | Target 10-minute script. Banner said the desk was not there yet. Use `SCENARIOS.md` + `CAPABILITIES.md` instead. |
| `.cfo-v2/office/sessions/00-PROOF.md` … `12-PROOF.md` | Session proofs. Grain history. Not the demo. |
| `.cfo/data/demo` (if still present) | Old canonical pack. Live Computer does not load it. |
| `.cfo-v2/office/world/maximor/system_capabilities.json` entrypoints like `python main.py INV-001` | V1 CLI. Office entry is Harness Bots + Kernel sidecar. |

## Do not show

| Path | Why |
| --- | --- |
| `Operator-workspace/` | Other agent's tree. Do not edit. |
| `.cfo-v2/office/reference-datasets/` | Gitignored benchmark clones. Hide `answer_key/` and RecBench `truth_*`. |
| Gauntlet `private_answers/` | Grader only. |
| Adversarial plant sequence and insider names on a public page | Holdout. Spoils the detective show. |

## Port and process notes

| Thing | Rule |
| --- | --- |
| Office | `127.0.0.1:8800` |
| Other UI agent | Leave `8792` |
| Kernel sidecar | Started by `harness serve`. Not a Bot. |
| Fake workers | Protocol only. Not the judged office. |

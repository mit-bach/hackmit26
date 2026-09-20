# HackMIT demo world — design

**Deprecated as product story.** Canonical write-up: `.cfo-v2/office/final-demo/` (start with `CAPABILITIES.md`). Computer data now points at `world/maximor`. Keep this file as a dated design memo.

Simulated data only. One company. The live office on 8800 is not yet this world.

## Verdict

Keep **Maximor Demo Corp** (`CO-MAXIMOR`, September 2026). The partner pack is a real scenario graph with a toy document layer, and the desk does not load it.

Do not replace Maximor with APEX’s law firm, DABstep’s 450 questions, or a public-company filings quiz. Use those datasets as **document quality, processor volume, and cash-match difficulty** on top of Maximor.

The show is not “call `get_invoice`.” The show is one invoice across sixteen Bots until close is blocked.

## What exists (counted 2026-09-19)

| Pack | What 8800 sees | What the pack actually is |
| --- | --- | --- |
| `.cfo/data` (Computer symlink) | **This.** 20 invoices, 4 emails, 12 bank lines | Leftover operational fixtures |
| `.cfo/data/demo` | Not loaded | Canonical: 29 AP invoices, 6 stub emails, 72 scenarios, 3 storylines, 366 KB |
| `.cfo/data/discrepancy_*` | Not loaded | Eval overlays. Holdout stays hidden from Bots |
| `.cfo/data/simulations/stripe` | On disk via the same symlink | Best intensity: 23 scenarios, 114 events, 25 charges, 21 payouts |
| Inbox fixtures | Seeded **2 of 17** | `inbox/fixtures.py` `full_inbox_specs()` — injection, quote, duplicate, remittance |
| Kernel eval | Not on the desk | 101 / 104 cases, 97%, Python workflows not Pi |

Canonical attachment text is 32–71 characters (`INVOICE ACM-2026-4410 / Amount: 12450.00`). The leftover files under `data/ingestion/files/` are better (line items, 2-page Helios scan) and the demo pack replaced them with worse stubs.

`docs/demo-data.md` advertises files that are not in the repo: `lineage.json`, `timeline.json`, `demo_queries.json`, `agent_cases.json`, `expected_outcomes.json`, `system_capabilities.json`, `demo_snapshot.json`, `memory_events.json`.

`inventory.py` claims 18 inbox scenarios. `full_inbox_specs()` returns 17.

## Track benchmarks (from Maximor-HackMIT-Track.md)

None required. Integrate most of them. Do not become a leaderboard.

| Source | License / size | Integrate? | How |
| --- | --- | --- | --- |
| [Invoice Sandbox](https://github.com/ciru-ai/invoice-sandbox-benchmark) | Generator + 112 PDFs | **Yes — documents** | Run `scripts/generate_fixture.py`. Map line-item PDFs and traps onto Maximor vendors. Hide `answer_key/` |
| [APEX-Accounting](https://huggingface.co/datasets/mercor/apex-accounting) | CC BY 4.0, ~4 MB public world | **Yes — close quality** | 90 files / 10 rubric tasks. Steal workpaper density. Do not demo World 9 (Sterling law firm). Do not claim a held-out score (160 tasks are closed) |
| [DABstep](https://huggingface.co/datasets/adyen/DABstep) | CC BY 4.0 | **Yes — processor volume** | `data/context/` only (~24 MB): `payments.csv` 138k txs, `fees.json`, `manual.md`. Sample 2–5k rows as simulated Stripe/Adyen. Skip `submissions/` / `task_scores/` (~GB) and the 450 Q&A product |
| [RecBench small](https://huggingface.co/datasets/end-close/recbench) | CC BY 4.0 | **Yes — cash difficulty** | Overlay ~200 bank/payout lines with labeled fee, duplicate, unbundle cases. Keep `truth_*` private. Do not run 1M ledger rows through Pi. Skip medium/large (6 GB) |
| BenchRec (Kaggle) | Likely login | Optional | Same job as RecBench. Prefer RecBench if Kaggle is gated |
| [Finance Agent Benchmark](https://huggingface.co/datasets/vals-ai/finance_agent_benchmark) | 50 filing questions | **No** | Equity research, not Office of the CFO |
| AccountingBench | Tweet / paper | **No as data** | Talking point only: we freeze one month so errors cannot silently compound |

Imported 2026-09-20 under `reference-datasets/` (gitignored). Counts: `sessions/BENCHMARK-IMPORT.md`.

## Target world (still Maximor)

One Computer. One `data_root`. Hidden answer keys.

| Object | Now | Show world |
| --- | --- | --- |
| AP invoices | 29 JSON stubs | ~110 with Invoice-Sandbox-grade line items, still INV-001 plot |
| Inbox | 2 seeded | All 17 fixtures + traps |
| Stripe | 3 demo payouts / unused 114-event sim | Sim pack is the Stripe Bot world; DABstep sample behind it |
| Bank | 19 lines | ~200 RecBench-style difficulties; keep TXN-2026-09-015 as the $12.40 close blocker |
| Close | 8 tasks, blocked | Same; APEX-style workpaper text |
| Judge prompts | Missing `demo_queries.json` | Generate from the three storylines |
| Eval | 97% Kernel | Keep as **our** measure. Caption: Kernel, not Pi. Live proof is Inspector Pi RPC |

## Ten-minute script

1. Desk — 15 Bots, Full verbosity, no live mailbox.
2. Email — classify 17 messages. Handle the bill. Ignore quote / statement / newsletter / injection.
3. AP — INV-001 three-way match. INV-004 price hold. Draft to ctl-pay.
4. ctl-pay + Pay — concur. Weekly run. 2/10 discount on INV-001. Skip held.
5. Stripe + Bank + Cash — payout waterfall. Unexplained $12.40. Do not force MATCHED.
6. Close — accruals that work. Final review stays blocked.
7. Audit — reperform INV-001; rediscover duplicate vendor, round-number, post-close JE.
8. Story — GM 64% → 61% from source txs; Quiet Harbor late; 13-week miss. Same IDs.

## Prompt and wiring changes (this office)

- Point Computer data at a single demo world (canonical pack + inbox overlay + Stripe sim). Stop reading the 20-invoice operational root.
- `seed_demo.py` must call `full_inbox_specs()`, not `demo_specs()`.
- Email Bot: simulated inbox. Kernel list + classify + handoff. No Gmail.
- Apply / cash prompts: `HUMAN_REVIEW` is not a Bot status. Say `EXCEPTION_OPEN` or `CLOSE_BLOCKED`. `expected_results.json` stays off operational reads.
- Email Grant must include inbox classify/handoff if that is what the demo claims. Today Email can `list_email_candidates` against ingestion JSON; the 17-spec traces are Python-side.
- Generate the missing export layer (`export-demo`) so lineage/timeline/judge prompts exist.
- Do not invent AP self-improvement, vendor bank-change control, or live Stripe. Those are still `NOT_IMPLEMENTED` in `docs/demo-capability-gaps.md`.

## Adversarial catalog (plant later, not Bot-readable)

`.cfo-v2/office/sessions/ADVERSARIAL-SCENARIOS.md` and `adversarial-scenarios.index.json`: 109 scenarios, 12 storylines. ADV-CASH-014 is the true explanation of the $12.40. Data-refinement prompt: `design-workshop/dominik/Prompts/DATA-REFINEMENT-CURSOR.md`.

## Honesty for judges

The 97% number is Kernel Python on planted JSON. It is allowed as “our measure.” It is not allowed as “the office scored 97%.” The office proof is live Pi tool traces on 8800, Handles between Bots, and close staying blocked.

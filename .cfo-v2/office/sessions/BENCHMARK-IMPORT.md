# Track benchmark import — 2026-09-20

Local cache: `.cfo-v2/office/reference-datasets/` (gitignored). Maximor stays the company.

| Source | On disk | Quality / use |
| --- | --- | --- |
| Invoice Sandbox | 177 MB. `gold_master/invoices` **112 PDFs**. CRM master, Q4 deposits, controller close notes. `answer_key/` empty until `generate_fixture.py` | **Use.** Document bar. Hide answer_key from Bots |
| APEX-Accounting | 8.6 MB after LFS. **90 world files** including real vendor PDFs and QBO xlsx workpapers. CC BY 4.0 | **Use.** Close workpaper bar. Do not switch to the law firm |
| DABstep context | 24 MB. `payments.csv` **138,236** txs + header. `fees.json` **1000** schemes. manuals | **Use.** Sample 2–5k as processor volume. Not 450 Q&A |
| RecBench small cash slice | 20 MB. **73,955** payouts, **75,138** bank lines, labels + payout↔bank truth | **Use.** Difficulty types on ~200 Maximor lines. Hide truth from Bots. Did not pull 1M ledger |
| Finance Agent Benchmark | 50-row filings quiz | **Do not load** |

Skipped: DABstep submissions/scores (~GB), RecBench medium/large, RecBench ledger.csv (141 MB / 1M rows), BenchRec Kaggle (login).

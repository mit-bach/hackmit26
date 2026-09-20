# P9 — Kernel eval bridge

**Job.** Run the Kernel scores that already exist. Caption them honestly. They are not P0–P8 ticks. They are a gate against reading a red engine as a Bot failure, and a honesty line for judges later.

**Owns.** `.cfo/` evals, not Harness Bots.

**Must not.** Quote 97% as “the office scored 97%.” Load eval Grants on the prove desk. Plant holdout into operational books to lift a score.

**Instance.** None required. Kernel live tree. Do not wipe a prove instance to run this.

---

## S01 — Caption the number

Read `.cfo-v2/office/final-demo/CAPABILITIES.md` and `docs/Agentic-update/01-intended-office.md`.

Write into `logs/ROLLUP.md`:

```
Kernel evaluate-cfo is Python workflows, not Pi.
Office-live proof is P0–P8 Handles and pi-rpc.
```

---

## S02 — Run Kernel eval if cheap

```bash
# from repo root, as RUN.md section 5
python3 main.py evaluate-cfo
```

If the entrypoint chdirs into `.cfo/`, that is expected for Kernel. It is not P5.

- RUNS: process completes; operational phase cannot open `expected_results.json` / `ground_truth.json` from Bot code paths
- HARD: eval harness itself crashes. Fix Kernel eval. Not a skill edit
- Do not tick any Catalog op office-live from this output

---

## S03 — Stripe sim / inbox demo (Kernel)

```bash
python3 main.py demo-inbox
python3 main.py simulate-stripe
```

These feed **Kernel**. P1 office-live is Bots. If demo-inbox writes overlay onto Computer `runs/ingestion/overlay.json` when `HARNESS_COMPUTER` is set, note that as a useful inject for P1. If it only writes `.cfo/`, T5 for inject — patch remap or do not use it as P1 stimulus.

`invoice_candidates` stays 0 on simulate-stripe. If not, HARD category error.

---

## S04 — close-month Kernel demo

```bash
python3 main.py close-month --month 2026-09 --seed-demo --deterministic
```

- BLOCKED-CORRECT on `$12.40` is good Kernel
- Not P5. Do not put this pack in the judged office-live folder
- `--resolve` is emergency/eval. Forbidden as office completion

---

## S05 — Track benchmarks (data, not this loop)

`sessions/BENCHMARK-IMPORT.md`: Invoice Sandbox, APEX, DABstep context, RecBench small are **document/volume/difficulty** for a later world pack. They are not prove stimuli until planted into Maximor operational data without answer keys.

P9 does not download them. P9 does not run 450 DABstep questions. P9 does not load Finance Agent Benchmark.

After this operation’s verdict, demo scoping may choose which of those overlays to plant. Not before P0–P8 have a RUNS net.

---

## S06 — Memory eval / final_agent_eval folders

`runs/final_agent_eval` and `runs/memory_eval` under Kernel are historical Python. Read if you need T10 context. Do not tick T10 INTENDED from them.

---

## Done-when

- Caption written
- You know whether Kernel is red (then stop treating Bot HOLD as a surprise)
- You have not used Kernel eval as office-live

## Forbidden

97% on the website as Pi. Eval-only tools on operational Bots. Benchmark Q&A product.

## Restart

None. P9 is not an instance loop. If evaluate-cfo throws, fix Kernel, re-run S02.

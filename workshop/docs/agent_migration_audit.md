# Agent migration audit: 43 Display names → 15 grain Bots

**Date:** 2026-09-19  
**Pre-migration kernel:** `.cfo/` OpenAI Agents SDK constructors (`Agent(name=...)`)  
**Post-migration office:** `.cfo-v2/office` Harness v2 grain (15 Bots) wrapping the same Kernel  
**Migration commits:** `ce0c807` / `29740b6` introduced `.cfo-v2`. Current kernel HEAD `8d16175` added durable AP overlay and organizational memory after the office Grants were last compiled.

The office does **not** replace Kernel arithmetic. It replaces in-process `Runner` as the Bot bus (`office/SUPERSEDES.md`). Behavioral equivalence means: every old Display-name responsibility has a current owner, Grants, skills, and Handle; Kernel workflows still produce the same finance outcomes.

This audit did **not** revert to 43 standing Bots.

---

## Prior architecture (Kernel)

45 registered Display names in `.cfo/skills/assignments.py` (docs historically said 43; the extra two are Finance Inbox Agent and Counterparty Message Agent). Constructors live under `.cfo/**/agent.py` and `agents.py`.

Workflows: AP, ingestion, inbox, payment scheduling, AR collections/cash apply, cash recon, accruals, prepaid, fixed assets, BS recon, month-end close, audit, reporting/forecast, sample-data generation.

Memory: `memory.tools.get_decision_memories` plus workflow hooks in `memory/hooks.py`. Skill `prior-period-precedent`.

Canonical AP: `tools.all_invoices` / `load_invoice` plus durable overlay `runtime_invoices.json`.

---

## Current architecture (Office)

15 grain slugs: `email`, `stripe`, `bank`, `books`, `ap`, `pay`, `apply`, `collect`, `cash`, `close`, `story`, `ctl-pay`, `ctl-cash`, `ctl-books`, `audit`.

Rooms: intake, pay, cash, books-close. Verifiers own concurrence. Kernel stays in `.cfo/`.

---

## Mapping of 43/45 → 15

See `runs/evals/agent_migration_map.json` for the machine-readable table. Summary:

| Class | Old Display names | New Bot / Profile | Status |
| --- | --- | --- | --- |
| Inbox | Finance Inbox Agent | `email` / `inbox` | MERGED CORRECTLY (restored Profile + Grants) |
| Inbox | Counterparty Message Agent | fixture, not a Bot | PRESERVED (eval/fixture) |
| Sources | Email, Employee, Portal, Document | `email` profiles | MERGED CORRECTLY |
| Sources | ERP, Procurement, EDI | `books` profiles | MERGED CORRECTLY |
| Sources | Bank/Card Discovery | `bank` / `card` | PRESERVED |
| Sources | *(none)* | `stripe` / `payout` | PRESERVED (empty Grants by grain; Kernel simulates) |
| AP | Preparer, Investigator | `ap` prepare/investigate | MERGED CORRECTLY |
| AP | Reviewer, Approver, Audit | `ctl-pay` / `review-match` | MERGED CORRECTLY (Audit is a stricter Wake of the same Profile) |
| Treasury | Payment Scheduler | `pay` / `schedule` | PRESERVED |
| Treasury | Payment Audit | `ctl-pay` / `review-pay` | PRESERVED (rebuild ops denylisted) |
| AR | Cash Application | `apply` | PRESERVED |
| AR | Cash Application Reviewer | `ctl-cash` / `review-apply` | PRESERVED |
| AR | Collections | `collect` / `chase` | PRESERVED |
| Cash | Preparer, Investigator | `cash` match/investigate | MERGED CORRECTLY |
| Cash | Reviewer | `ctl-cash` / `review-rec` | PRESERVED |
| Close | Accrual, Prepaid Preparer, FA Preparer, BS Preparer, Close Manager | `close` profiles | MERGED CORRECTLY |
| Close | Prepaid Reviewer | `ctl-books` / `review-treatment` | PRESERVED |
| Close | Fixed Asset Reviewer | `ctl-books` / `review-assets` | MISSING → restored as Profile (not a 16th Bot) |
| Close | BS Reconciliation Reviewer | `ctl-books` / `review-bs` | MISSING → restored as Profile |
| Close | Month-End Close Reviewer | `ctl-books` / `lock` | PRESERVED |
| Reporting | Variance, Forecast, Forecast Variance, Board | `story` profiles | MERGED CORRECTLY |
| Reporting | Reporting Reviewer, Forecast Reviewer | dropped as lanes; `audit` samples | INTENTIONAL (Kernel validators remain) |
| Audit | Auditor, Audit Report | `audit` interpret/report | MERGED CORRECTLY |
| Sample data | five agents | Kernel/eval only | INTENTIONAL |

---

## Missing responsibilities found

Classified per Part 19.

### A / B / C — compiler dropped memory and inbox

Stale `grants.json` was compiled before organizational memory and inbox constructors existed. The compiler also could not:

1. follow `from memory.tools import get_decision_memories` re-exports,
2. catalog `function_tool(fn)` assignments in `inbox/tools.py`,
3. unwrap `tools=list(COUNTERPARTY_TOOLS)`.

**Effect:** Exception Investigator, Accrual, Cash, Prepaid Bots could not call `get_decision_memories`. `prior-period-precedent` was assigned in Kernel but absent from compiled Grants. Finance Inbox Agent was not in Grants or slug-map.

**Fix:** compiler resolution + recompile. Copy `prior-period-precedent` and `month-end-close-review` onto the Computer. Add roster skill intersections so Pi actually loads them.

### A / B — ctl-books union gap

Grain mapped FA Reviewer and BS Reviewer onto Profile name `review-treatment` while forbidding Grant unions. Grant source was Prepaid Reviewer only. FA/BS review tools were unreachable.

**Fix:** additional Profiles on the same Bot (`review-assets`, `review-bs`) and Handle edges. Not a sixteenth Bot.

### H / L — disk identity vs in-memory registry

Office tests and Sidecar expected `invoice_ingestion.registry.configure_paths` and `tools.configure_overlay_path`. The durable-inbox kernel had an in-memory registry and only `configure_runtime_dir`. Cross-process canonical identity was lost.

**Fix:** disk-backed registry (`atomic_json.py`) plus overlay path alias, without abandoning `runtime_invoices.json`.

### E / P — close host missing

`office/bots/close/HOST.md` named `close.host.run_close_host`, but the module did not exist. Treatment Handles could not be written.

**Fix:** `.cfo/close/host.py` sequences Profiles, writes Handle payloads, never marks CLOSED.

### I — prompt compression

Merged BOT.md files dropped FA/BS tool lists and inbox Profile ops. Restored in BOT.md / profile markdown. Old constructor instruction blocks remain in Kernel; Pi loads skills + BOT.md, not 43 pasted prompts.

### G / H / L — Sidecar did not remap organizational memory

`cfo_kernel.paths.attach_computer` remapped overlay, cash cases, packets, close, AR, audit, reporting, and accruals, but not `memory.store`. Decision memories written through the Sidecar landed in `.cfo/runs/memory` instead of `<computer>/runs/memory`, so a restarted Sidecar could not retrieve prior-period precedent.

**Fix:** `memory.store.configure_paths(runs / "memory")` in `_remap_kernel`. Accrual ledger also gained `configure_paths` so attach can point open accruals at the Computer.

### N / O — August Stripe memory hid the September demo payout

`_seed_august_memory` writes an August Stripe payout into the shared integrations store. `seed_provider_payouts` then saw “a Stripe payout already exists” and skipped `po_1HackMIT97420`. September cash recon classified `TXN-2026-09-019A` as `EXACT_MATCH` instead of `PROVIDER_PAYOUT`. Cross-workflow demo metrics were 44/45.

This is an old Kernel isolation bug exposed by wiring memory into the company demo after the office overlay existed. It is not a reason to split Bots.

**Fix:** seed demo payouts by canonical ID, then clear cash/integration working state after August memory is written.

### B / L — cash bind was process-local

Sidecar `kernel.bind_cash_case` expected `bind_case(..., persist=True, case_id=...)`. This branch’s tools were in-memory only.

**Fix:** restore `cash_recon.case_store` and persistent `bind_case` without changing candidate math.

---

## Root causes

1. Office Grants compiled against an older Kernel and never recompiled after memory/inbox landed.
2. Compiler assumed every tool is `@function_tool` in the imported module.
3. Grain “do not union Grants” was implemented by dropping FA/BS tools instead of adding Profiles.
4. Two persistence designs (in-memory registry vs disk overlay) were not merged when `.cfo-v2` was checked out onto `durable-inbox-ap-persistence`.
5. Session docs described a close host that was never implemented.
6. Sidecar Computer remap omitted `memory.store` (and originally `accrual.ledger.configure_paths`).
7. Provider seeding treated “any Stripe payout” as “the September demo payout is present.”

---

## Fixes made

- Compiler: re-export follow, `function_tool()` wrappers, `list()` tools=, inbox + memory catalog classes
- Recompiled `catalog.json`, `grants.json`, `grants.eval.json`
- Disk-backed invoice registry + `configure_overlay_path`
- Close host
- ctl-books Profiles `review-assets` / `review-bs` and Handle edges
- email Profile `inbox` for Finance Inbox Agent
- Computer copies of `prior-period-precedent` and `month-end-close-review`
- Roster skill intersections for memory
- pytest paths include `.cfo-v2/office`
- Sidecar remaps memory onto `<computer>/runs/memory`
- Accrual ledger `configure_paths`
- Persistent cash-case bind for Sidecar restart
- Demo Stripe/Adyen seed by payout ID; August memory no longer suppresses September `PROVIDER_PAYOUT`

---

## Tests restored / added

Historical Kernel tests were not deleted by the 15-bot overlay; they still live under `.cfo/tests/` (the old top-level `tests/` path was a vault move, not a coverage deletion). Office tests from `origin/main` were restored onto this branch.

Migration-specific coverage:

- `.cfo-v2/office/compiler/test_compile_memory_reexport.py`
- `.cfo-v2/office/tests/test_agent_consolidation_regressions.py`
- `.cfo/tests/test_kernel_agent_consolidation_regressions.py`
- `.cfo/tests/test_cfo_kernel.py` (Sidecar overlay, cash case, memory remap, live Grants)

Existing Harbor, Stripe simulation, inbox persistence (fresh process), close `$12.40`, CFO company demo, and skill-registry tests remain the behavioral baseline.

### Historical test mapping

| Old test | What it proved | Current equivalent | Status | Result |
| --- | --- | --- | --- | --- |
| `tests/test_workflow.py` | AP three-way match / HOLD | `.cfo/tests/test_workflow.py` | PRESERVED | pass |
| `tests/test_cfo_integration.py` | AP→cash→close→forecast→audit identity | `.cfo/tests/test_cfo_integration.py` | PRESERVED; Stripe seed bug fixed | pass |
| `tests/test_memory.py` | Harbor / Stripe / prepaid precedent | `.cfo/tests/test_memory.py` | PRESERVED | pass |
| `tests/test_inbox_persistence.py` | Fresh-process overlay + cross-workflow IDs | `.cfo/tests/test_inbox_persistence.py` | PRESERVED | pass |
| `tests/test_stripe_simulation.py` | Gross−fees−refunds−disputes = payout = bank | `.cfo/tests/test_stripe_simulation.py` | PRESERVED | pass |
| session-12 office tests | 15 bots, no human, Handles, Sidecar | `.cfo-v2/office/tests/test_session12_*.py` | RESTORED from origin/main | pass |

---

## Test results (2026-09-19)

Command: `.venv/bin/python -m pytest`

**608 passed, 0 failed, 0 skipped.**

Approximate layers (all green inside the same run):

| Layer | Collected | Result |
| --- | --- | --- |
| unit | 165 | 165/165 |
| tool | 56 | 56/56 |
| agent / office | 44 | 44/44 |
| workflow | 220 | 220/220 |
| memory / restart | 46 | 46/46 |
| historical / eval | 37 | 37/37 |
| integration / Stripe / company demo | 40 | 40/40 |
| **total** | **608** | **608/608** |

---

## 15-bot design after repair

The grain still makes sense. Do not add a 16th Bot.

Overloaded Bots that remain correct because Profiles are not Grant unions:

- `email` — inbox + source-document profiles
- `close` — accrue / prepaid / assets / bs / coordinate
- `ctl-books` — review-treatment / review-assets / review-bs / lock
- `story` — flux / forecast / forecast-miss / board

`stripe` stays Grant-empty by grain; Kernel `simulate-stripe` is the finance path.

---

## Remaining limitations

- Live Pi turns and Handle *completion* are still `--fake` / session-12 unproven.
- Stripe Bot Grants stay empty by grain; Kernel `simulate-stripe` is the finance path.
- Reporting/Forecast Reviewer Display names are not Profiles; validators + audit sampling stand in.
- Sample-data agents are not Bots.
- `HUMAN_REVIEW` remains a fail-closed Kernel status; Verifiers own the queue, they do not auto-post planted traps.
- Close host writes Handle payloads; it does not live-send Harness protocol messages.
- Session 02 Sidecar fixtures still predate memory Catalog ops; live `computer/cfo/catalog.json` is the Grant SoT.

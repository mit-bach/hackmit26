# Session 01 — Client attach (compiler + Pi facade)

Date: 2026-09-19. Kernel/unit proofs. Handle completion was not live-proven. Pi was not driven.

## Commands

```bash
python3 .cfo-v2/office/compiler/__main__.py --phase operational
python3 .cfo-v2/office/compiler/prove.py
cd .cfo-v2/office/computer/cfo && npm test
npx tsc -p .harness/Harness-v2/tsconfig.json --noEmit
```

Exact Pi load (flags from `.harness/Harness-v2/README.md` and `src/cli.ts`; `-e` exists, no invented flags):

```bash
HARNESS_BOT=ap \
HARNESS_COMPUTER=/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v2/office/computer \
HARNESS_V2_ROOT=/Users/dominikbach/olympus/hackmit/hackmit26/.harness/Harness-v2 \
HARNESS_CLIENT_SKILLS=1 \
CFO_EVAL_PHASE=operational \
  pi -e .harness/Harness-v2/extensions/index.ts \
     -e .cfo-v2/office/computer/cfo/extensions/index.ts \
     --name ap
```

Wrapper: `.cfo-v2/office/computer/cfo/bin/pi-bot.sh <slug>`.

Headless workers: `HARNESS_EXTRA_EXTENSIONS=<cfo extensions/index.ts>` plus `HARNESS_CLIENT_SKILLS=1`. `harness bot` / `harness serve` only passed one `-e` until this session added `extraExtensionArgs()` in Harness `src/pkg.ts` (generic extra `-e` list, no finance types).

## Compile (exit 0)

- Catalog ops: **80**
- Display names: **43**
- `get_bank_transaction` collision qualified as `cfo_invoice_ingestion_get_bank_transaction` and `cfo_cash_recon_get_bank_transaction`
- `ar.tools.get_ar_close_snapshot` and `bs_recon.tools.list_period_reconciliations` are Catalog-only (no constructor → not granted)
- Warning: `AGENT_SKILLS` has `Stripe Payout Agent` with no `Agent()` constructor (Connectors refused at bind)

### AP Preparer ≠ AP Approver

AP Preparer:

- `tools.get_invoice`
- `tools.get_purchase_order`
- `tools.get_goods_receipt`
- `tools.find_duplicate_invoices`
- `tools.get_case_evidence`

AP Approver:

- `tools.get_case_evidence`
- `tools.get_company_policies`
- `tools.find_relevant_policies`
- `tools.get_prior_cases`

`create_accrual` is only on Accrual Agent (`close` / Profile `accrue`).

Auditor Agent operational Grants omit `audit.tools.get_audit_ground_truth`. Evaluation copy is `cfo/grants.eval.json` and still lists that op. Bind phase `operational` also hides it.

## Fake bind

`npm test` in `.cfo-v2/office/computer/cfo` (8/8):

1. AP Preparer grants differ from AP Approver
2. `ap` / Profile `prepare` `search_connected_tools({query:"create_accrual"})` is empty; `call_connected_tool` on `accrual.tools.create_accrual` returns `forbidden`
3. `audit` / Profile `interpret` / `CFO_EVAL_PHASE=operational` cannot see `get_audit_ground_truth`
4. `close` / `accrue` `create_accrual` without idempotency key → `idempotency_required`; with key → `verifier_required` to `ctl-books` (never `ask_user`)
5. Slug-map list union throws
6. `stripe` / `payout` has no Display name in Grants → no Connectors
7. Skill names: grant ∩ roster
8. Wake `profile:` header replaces the Grant set; it does not union

## Verifier routing (Client workaround)

Harness `tool_call` intercept only knows the human Operator (`ask_user`, `waitForApproval`). This office does not park pay-run, period lock, or `create_accrual` there.

Client extension:

1. Registers `search_connected_tools` / `call_connected_tool` only when `HARNESS_BOT` is set.
2. Resolves slug → Profile → one Grant set. A later Wake `profile: <name>` **replaces** that set.
3. `call_connected_tool` refuses off-grant names (`forbidden`). Does not call the Sidecar.
4. `evalOnly` ops are omitted from production Grants and hidden again in operational phase.
5. Mutating ops require `idempotency_key`.
6. Consequential Kernel ops (`create_accrual`, `reconcile_accrual_with_invoice`, `side-effect-external`, pay-run / write-off / period-lock name patterns) write `workspace/verifier/<ctl-*>/<key>.json` and return `verifier_required` with verifier slug + `bot_send_prompt` instruction. They do **not** call the Sidecar and do **not** call `ask_user`.
7. `pi.on("tool_call")` **blocks** Harness `ask_user`.
8. If `HARNESS_V2_ROOT` is set, the Client tries `sendPrompt` to the Verifier. If the Roster is missing or import fails, the packet is still on disk. **Await/done was not live-proven.**
9. Routing table: accrual treatments → `ctl-books` / `review-treatment`; period lock → `ctl-books` / `lock`; cash post/sign-off → `ctl-cash`; money-out / external side effect → `ctl-pay`.

Sidecar HTTP is not in this session. Granted read ops return `sidecar_unavailable` rather than invented amounts.

## Skill intersect

Harness v2 still adds `<computer>/skills` as a whole directory. Other sessions already populated that tree.

Client workaround:

- `HARNESS_CLIENT_SKILLS=1` skips that whole-directory entry in Harness `extensions/index.ts` (generic; no finance types).
- This extension then adds `<computer>/skills/<name>` (and `.cfo/skills/<name>`) only when `name` is in **grant.skills ∩ roster.skills** (roster empty → grant skills only).

## Disk

| Path | Role |
| --- | --- |
| `.cfo-v2/office/compiler/compile_lib.py` | AST compiler |
| `.cfo-v2/office/compiler/__main__.py` | `cfo-catalog compile` CLI |
| `.cfo-v2/office/compiler/prove.py` | SoD assertions |
| `.cfo-v2/office/computer/cfo/catalog.json` | 80 ops |
| `.cfo-v2/office/computer/cfo/grants.json` | production Grants |
| `.cfo-v2/office/computer/cfo/grants.eval.json` | evaluation Grants (ground truth kept) |
| `.cfo-v2/office/computer/cfo/catalog.overrides.json` | mutability / evalOnly |
| `.cfo-v2/office/computer/cfo/slug-map.json` | 15 grain slugs, Profiles, no Grant union |
| `.cfo-v2/office/computer/cfo/extensions/` | Pi facade |
| `.cfo-v2/office/computer/cfo/bin/pi-bot.sh` | two `-e` launcher |
| `.harness/Harness-v2/src/pkg.ts` | `HARNESS_EXTRA_EXTENSIONS` |
| `.harness/Harness-v2/extensions/index.ts` | `HARNESS_CLIENT_SKILLS=1` opt-out |

No finance types under `.harness/Harness-v2/src`. Kernel math was not rewritten.

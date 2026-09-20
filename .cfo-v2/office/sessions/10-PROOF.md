# Session 10 proof — Bot `story`

Handle completion was not live-proven. No Pi turn. Proofs are Kernel / unit / Compiler.

## Commands

```bash
# Compiler (temp out dir; did not overwrite Computer catalog as the session-10 SoT)
PYTHONPATH=.cfo-v2/office/compiler python3 .cfo-v2/office/compiler/__main__.py \
  --out /tmp/cfo-story-compile.qHoNZF --phase operational

# Reporting + skills
cd /Users/dominikbach/olympus/hackmit/hackmit26
PYTHONPATH=.cfo .cfo/.venv/bin/python -m pytest \
  .cfo/tests/test_reporting.py .cfo/tests/test_skills.py -q
# 31 passed

PYTHONPATH=.cfo .cfo/.venv/bin/python -m pytest .cfo/tests/test_reporting.py \
  -k "variance_traces or cash_forecast_is_thirteen or forecast_snapshots or board_pack_ties" -q
# 4 passed (contributor sums, 13-week roll-forward, immutable snapshots, board evidence)

# Board evidence ids (Kernel pack, cwd=.cfo so repo-root close.py does not shadow)
PYTHONPATH=. .cfo/.venv/bin/python - <<'PY'
from reporting.board import build_board_pack
from reporting.reviewer import review_board_pack
# ... seed, analyze_variance, build_board_pack ...
PY
```

Collection initially failed: `scheduling/host.py` imported `invoice_ingestion.persist` (that module is not on disk). Session 10 changed that import to `atomic_json.write_json_atomic`, which the rest of the Kernel already uses.

## Compiler — story has no mutating finance Catalog ops

Compile wrote `/tmp/cfo-story-compile.qHoNZF/{catalog,grants}.json`. Story Display names vs Catalog:

| Display name | Profile | Ops | mutability |
| --- | --- | --- | --- |
| Variance Analysis Agent | `flux` | `reporting.tools.get_period_metrics`, `get_variance_facts`, `get_variance_trace` | read |
| Cash Forecast Agent | `forecast` | `get_cash_forecast`, `get_forecast_snapshot`, `get_forecast_checks` | read |
| Forecast Variance Agent | `forecast-miss` | same three forecast ops | read |
| Board Reporting Agent | `board` | `get_period_metrics`, `get_variance_facts`, `get_cash_forecast` | read |

Fragment `.cfo-v2/office/computer/cfo/grants.story.json` matches those four Grant sets. Reporting Reviewer Agent and Forecast Reviewer Agent still exist as Compiler constructors. They are not slug-map Profiles on `story`. `audit` samples the pack.

Catalog write-like ops remain `accrual.tools.create_accrual` and `accrual.tools.reconcile_accrual_with_invoice`. Neither is on a `story` Grant.

## Board output uses Kernel evidence ids

Deterministic pack for period `2026-09`:

- Every section with narrative has `evidence_refs`.
- Pack refs include `metric:…`, `variance:…`, `txn:…`, `statement:2026-09`.
- `review_board_pack` → `APPROVE` (“Board-pack numbers tie to ledger metrics and narratives carry evidence.”).
- `unsupported_claims` empty on the Kernel pack.
- `flag_unsupported_claims(..., "Gross margin fell because of a recession.")` flags the invented cause.

A live model was not run. Profile `board` must omit any sentence that lacks a Kernel evidence id.

## Disk

```
.cfo-v2/office/bots/story/BOT.md
.cfo-v2/office/bots/story/profiles/flux.md
.cfo-v2/office/bots/story/profiles/forecast.md
.cfo-v2/office/bots/story/profiles/forecast-miss.md
.cfo-v2/office/bots/story/profiles/board.md
.cfo-v2/office/bots/story/roster.json
.cfo-v2/office/computer/cfo/grants.story.json
.cfo-v2/office/computer/harness/roster.json   # story connectors + Routine period-story
.cfo-v2/office/computer/skills/financial-variance-analysis/SKILL.md
.cfo-v2/office/computer/skills/cash-forecasting/SKILL.md
.cfo-v2/office/computer/skills/ar-cash-forecasting/SKILL.md
.cfo-v2/office/computer/skills/forecast-vs-actual-interpretation/SKILL.md
.cfo-v2/office/computer/skills/board-financial-reporting/SKILL.md
.cfo-v2/office/sessions/10-PROOF.md
.cfo/skills/assignments.py                    # aliases flux, forecast-miss
.cfo/skills/README.md                         # Used By → Bot story Profiles
.cfo/skills/{five reporting skills}/SKILL.md  # When to Use names Profiles
```

Roster still has fifteen slugs. Room `books-close` members: `close`, `ctl-books`, `story`, `audit`. `approvalLevel` for `story` is `never`. Forecast snapshots stay create-only under `.cfo/runs/reporting/forecasts/`.

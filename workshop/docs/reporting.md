# Reporting and forecasting

Python computes statements, variances, and the 13-week cash forecast. Agents interpret those facts. They do not own totals.

```
Canonical ledger / AP / AR / payroll
        ↓
Reporting calculation (statements.py, ledger.py)
        ↓
VarianceAnalysisAgent
        ↓
ReportingReviewerAgent
        ↓
BoardReportingAgent

AP pool + AR invoices + payroll schedule
        ↓
Forecast builder (forecast.py)
        ↓
CashForecastAgent
        ↓
ForecastReviewerAgent
        ↓
immutable snapshot
        ↓
actual cash
        ↓
ForecastVarianceAgent
```

## Source of truth

| Number | Owner |
| --- | --- |
| Revenue, COGS, gross margin, opex, operating income | `reporting/ledger.py` + `reporting/statements.py` |
| Cash / AP / AR period balances | `data/reporting/balances.json` (point-in-time), plus operational journals when posted |
| AP outflows | Existing invoices + approved pool + `APForecastDecision` overlay. Held invoices are not committed. |
| AR inflows | Existing `CustomerInvoice` records via `reporting/sources.py` (`Receivable` is an adapter, not a second subledger) |
| Payroll | `data/reporting/payroll.json` → `ForecastLine` |
| Forecast weekly totals | Recalculated from forecast lines |
| Forecast history | `runs/reporting/forecasts/` — never overwritten |

The model may choose which verified facts to emphasize. It may not invent residual explanations or recompute margins.

## Provenance

A document ID stays stable across AP, payment scheduling, the forecast line, bank activity, cash reconciliation, the shared close ledger, variance analysis, and the board pack. Links are written with `close.context.remember_link` and surfaced on `ReportingRun.provenance`.

Example:

```
INV-002
  → AP approval / schedule
  → forecast line FL-AP-INV-002
  → bank BNK-INV-002
  → recon REC-INV-002
  → close JE + reporting JE
  → variance / board evidence
```

## Confidence and human review

- AR collection dates: promised date, then historical days late, then due date.
- Confidence below `low_confidence_threshold` (0.50) is flagged. Helios-style chronic late payers stay on the forecast but are called out.
- Held AP is listed, not paid.
- Reviewers escalate when contributor sums break, a narrative invents a cause, or a material residual is unexplained.

## Skills

| Skill | Agents |
| --- | --- |
| `financial-variance-analysis` | Variance Analysis Agent, Reporting Reviewer Agent |
| `cash-forecasting` | Cash Forecast Agent, Forecast Reviewer Agent |
| `ar-cash-forecasting` (reused) | Cash Forecast Agent, Forecast Reviewer Agent |
| `forecast-vs-actual-interpretation` | Forecast Variance Agent, Forecast Reviewer Agent |
| `board-financial-reporting` | Board Reporting Agent, Reporting Reviewer Agent |

No skill performs arithmetic.

## Demo

The August / September P&L is synthetic ledger activity in `reporting/seed.py` (not a live ERP export). AP invoices, AR customers, and the payment pool are the same records used by the rest of the repo. Stripe/Adyen are not required.

```bash
python main.py demo-reporting
python -m reporting.demo
python main.py reporting 2026-09 2026-09-19
```

`--llm` uses the live agents. Without a key, Python writes the narratives from the same facts.

Planted forecast-vs-actual items (known as of 2026-10-04):

- Quiet Harbor `INV-AR-FC-001` paid late
- GitHub `INV-009` paid earlier than the deferred date
- Payroll `PR-2026-10-02` $73,200 vs $70,000
- Unforecast bank charge `BNK-UNX-001`

## What is not connected

- Budget vs actual uses `data/reporting/budget.json` (fixture), not an FP&A system.
- Opening cash for the forecast uses `data/reporting/balances.json` / an explicit beginning balance, not a live bank API.
- Board packs are structured Markdown from Python metrics. They are not uploaded to a board portal.
- Close packets (`python main.py close`) remain the operational close report. The board pack is the financial narrative layered on the same IDs.

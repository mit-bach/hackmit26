---
name: cash-forecasting
description: Interpret a Python 13-week cash forecast built from AP, AR, and payroll lines. Use when judging timing risk, holds, or low-confidence collections.
status: new
---

# Cash Forecasting

## Purpose

Explain a rolling weekly cash forecast that Python already assembled from approved AP, open receivables, and payroll schedules.

## When to Use

Apply when the Cash Forecast Agent or Forecast Reviewer Agent reviews a `CashForecastSnapshot`. Weekly totals have already been rolled forward from forecast lines.

## Inputs / Evidence

Use get_cash_forecast and get_forecast_checks. Authoritative Python outputs include:

- beginning cash and 13 weekly totals
- forecast lines with source type, source ID, date, amount, confidence, and rationale
- held AP invoices
- low-confidence AR assumptions
- arithmetic validation errors

Do not rebuild the week grid and do not recalculate ending cash.

## Procedure

1. Confirm Python reports 13 weeks and a clean roll-forward.
2. Treat held AP invoices as uncommitted. Do not speak as if they will be paid.
3. Call out AR lines below the low-confidence threshold as assumption risk.
4. Describe AP timing from scheduled pay dates, not raw invoice due dates, when they differ.
5. Use payroll lines as written on the payroll schedule.
6. Treat live AR expected collections as the forecast-facing receipts number. The static cash-position field is fallback only.
7. A promise-to-pay date outranks the original due date. Disputed invoices are never certain near-term cash.
8. HUMAN_REVIEW or unapplied customer cash is money already received. Do not also treat those invoices as future collections.

## Decision Criteria

- Arithmetic errors are blocking.
- A hold is not a payment.
- Low-confidence collections stay on the forecast but must be labeled uncertain.
- A date move on an AP invoice is a forecast change, not a new vendor.

## Output Expectations

Return judgments about timing risk, holds, and weak AR assumptions. Cite forecast IDs and source IDs. Do not change amounts.

## Boundaries

- Do not calculate weekly cash yourself.
- Do not invent inflows or pull in invoices that are not in the line list.
- Do not treat a held invoice as committed.
- Do not override Python confidence scores.

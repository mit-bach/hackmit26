DISCREPANCY STRESS TEST
Dataset: data/discrepancy_demo / seed 42 / 2026-09
Phase: final

AP
8 / 8 detected

AR
6 / 6 detected

CASH
7 / 7 detected

CLOSE
7 / 7 detected

AUDIT
7 / 7 detected

REPORTING
4 / 4 detected

FORECASTING
6 / 6 detected

CROSS FUNCTION
5 / 5 detected

FIXES APPLIED:
AP-DISC-005: Duplicate invoice detection now normalizes invoice numbers and vendor names before matching.
  files: tools.py, skills/three-way-match-analysis/SKILL.md
  test: tests/test_discrepancies.py::test_normalized_duplicate_invoice_is_surfaced
AP-DISC-006: Approval-limit exceptions now block AP approval and payment-pool eligibility.
  files: workflow.py, scheduling/cash.py
  test: tests/test_discrepancies.py::test_approval_threshold_is_held
AR-DISC-001: Invoice-reference extraction now accepts live invoice IDs and broader INV/AR-INV tokens; partials keep a remaining balance.
  files: ar/cash.py, skills/cash-application/SKILL.md
  test: tests/test_discrepancies.py::test_ar_partial_payment_is_preserved
AR-DISC-002: Named-invoice overpayments route to HUMAN_REVIEW and preserve the residual.
  files: ar/cash.py, skills/cash-application/SKILL.md
  test: tests/test_discrepancies.py::test_ar_overpayment_residual_is_preserved
AR-DISC-004: Unknown remittance invoice IDs are missing-reference facts and force HUMAN_REVIEW.
  files: ar/cash.py
  test: tests/test_discrepancies.py::test_invalid_invoice_reference_is_surfaced
AR-DISC-005: Conflicting payer / remittance / tagged-customer evidence routes to HUMAN_REVIEW.
  files: ar/cash.py
  test: tests/test_discrepancies.py::test_customer_identity_conflict_is_surfaced
AR-DISC-006: Already-posted payments return UNAPPLIED and do not apply cash again.
  files: ar/workflow.py
  test: tests/test_discrepancies.py::test_double_cash_application_is_caught
CLOSE-DISC-001: AP/AR/prepaid/FA packets compare optional period GL control balances to the subledger and keep unexplained differences open.
  files: bs_recon/packets.py, skills/balance-sheet-reconciliation/SKILL.md
  test: tests/test_discrepancies.py::test_ap_gl_discrepancy_blocks_close
REPORT-DISC-002: GM explanations include revenue transactions and reject a supplier-cost story when a larger verified driver exists.
  files: reporting/variance.py, skills/financial-variance-analysis/SKILL.md
  test: tests/test_discrepancies.py::test_unsupported_variance_narrative_is_rejected
CASH-DISC-004: Same-vendor groups that do not sum to the bank amount now preserve the residual as an unexplained difference instead of a silent unmatched item or a forced grouped match.
  files: cash_recon/candidates.py, skills/cash-reconciliation-method-selection/SKILL.md
  test: tests/test_discrepancies.py::test_grouped_ach_residual_is_detected
FORECAST-DISC-002: Forecast integrity review flags coverage gaps, duplicate outflows, opening-cash mismatches, and unjustified early AR receipts.
  files: reporting/forecast.py, skills/cash-forecasting/SKILL.md
  test: tests/test_discrepancies.py::test_forecast_opening_cash_and_duplicates

INITIAL RESULT
33 / 50 passed
AFTER FIXES
50 / 50 passed
Recall: 100.00%  Unsafe auto-resolution: 0.00%

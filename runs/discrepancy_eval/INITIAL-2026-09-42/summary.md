DISCREPANCY STRESS TEST
Dataset: data/discrepancy_demo / seed 42 / 2026-09
Phase: initial

AP
6 / 8 detected
FAILED:
AP-DISC-005
Expected: expected HOLD got APPROVE
Actual: APPROVE
Agent: AP policy / decide_ap
  expected HOLD got APPROVE
AP-DISC-006
Expected: approval_limit_exceeded
Actual: APPROVE
Agent: AP policy / decide_ap
  approval_limit_exceeded

AR
1 / 6 detected
FAILED:
AR-DISC-001
Expected: No plausible invoice match was found; cash stays unapplied.
Actual: UNAPPLIED
Agent: Cash Application Agent
  No plausible invoice match was found; cash stays unapplied.
AR-DISC-002
Expected: No plausible invoice match was found; cash stays unapplied.
Actual: UNAPPLIED
Agent: Cash Application Agent
  No plausible invoice match was found; cash stays unapplied.
AR-DISC-004
Expected: No plausible invoice match was found; cash stays unapplied.
Actual: UNAPPLIED
Agent: Cash Application Agent
  No plausible invoice match was found; cash stays unapplied.
AR-DISC-005
Expected: Invoice is explicitly named and the amount is valid against the outstanding balance.
Actual: AUTO_APPLY
Agent: Cash Application Agent
  Invoice is explicitly named and the amount is valid against the outstanding balance.
AR-DISC-006
Expected: Already posted.
Actual: AUTO_APPLY
Agent: Cash Application Agent
  Already posted.

CASH
3 / 7 detected
FAILED:
CASH-DISC-003
Expected: FEE_NETTED
Actual: EXPLAINED_EXCEPTION
Agent: Cash Reconciliation Preparer
  FEE_NETTED
CASH-DISC-004
Expected: UNMATCHED_BANK
Actual: HUMAN_REVIEW
Agent: Cash Reconciliation Preparer
  UNMATCHED_BANK
CASH-DISC-005
Expected: UNMATCHED_LEDGER
Actual: HUMAN_REVIEW
Agent: Cash Reconciliation Preparer
  UNMATCHED_LEDGER
CASH-DISC-006
Expected: UNMATCHED_BANK
Actual: HUMAN_REVIEW
Agent: Cash Reconciliation Preparer
  UNMATCHED_BANK

CLOSE
6 / 7 detected
FAILED:
CLOSE-DISC-001
Expected: AP subledger vs GL
Actual: TIED
Agent: Close AP recon
  AP subledger vs GL

AUDIT
7 / 7 detected

REPORTING
2 / 4 detected
FAILED:
REPORT-DISC-002
Expected: narrative check
Actual: ACCEPTED
Agent: Variance Analysis Agent
  narrative check
REPORT-DISC-003
Expected: contributor completeness
Actual: OPEN
Agent: Reporting Reviewer
  contributor completeness

FORECASTING
3 / 6 detected
FAILED:
FORECAST-DISC-002
Expected: AP coverage
Actual: COVERED
Agent: Cash Forecast Agent
  AP coverage
FORECAST-DISC-003
Expected: duplicate outflow
Actual: OK
Agent: Cash Forecast Agent
  duplicate outflow
FORECAST-DISC-004
Expected: opening cash roll-forward
Actual: OK
Agent: Cash Forecast Agent
  opening cash roll-forward

CROSS FUNCTION
5 / 5 detected

INITIAL RESULT
33 / 50 passed
Recall: 88.00%  Unsafe auto-resolution: 2.00%

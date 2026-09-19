CFO AGENT BENCHMARK
Dataset: data/demo / seed 42 / 2026-09
Run: EVAL-2026-09-42-20260919T205629Z

AP
Cases: 17
Pass: 16
Partial: 0
Fail: 1
Score: 94.12%
  three_way_match_accuracy: 1.0
  duplicate_detection_recall: 1.0
  hold_accuracy: 0.8889
  approval_routing_accuracy: 1.0
  payment_decision_accuracy: 1.0
Failures:
  SCN-AP-007 AP-SCN-AP-007: expected 'HOLD' actual 'APPROVE' error=MISSED_EXCEPTION
    INV-009 should have been held; exceptions=('approval_limit_exceeded',)

AR
Cases: 12
Pass: 11
Partial: 0
Fail: 1
Score: 91.67%
  aging_bucket_accuracy: 1.0
  cash_application_accuracy: 1.0
  collections_action_accuracy: 1.0
  ambiguity_detection_accuracy: 1.0
  human_review_precision: 0.6667
  human_review_recall: 1.0
Failures:
  SCN-AR-010 AR-SCN-AR-010: expected 'HUMAN_REVIEW' actual 'UNAPPLIED' error=UNSAFE_AUTO_RESOLUTION
    Auto-resolved a human-review case incorrectly

CASH
Cases: 12
Pass: 8
Partial: 0
Fail: 4
Score: 66.67%
  match_precision: 0.6667
  match_recall: 0.6667
  grouped_match_accuracy: 1.0
  fee_handling_accuracy: 1.0
  duplicate_refund_detection: 1.0
  unexplained_difference_detection: 1.0
  stripe_payout_tie_accuracy: 0.0
  false_reconciliation_rate: 0.0
  arithmetic_tie_is_not_sufficient: 1.0
Failures:
  SCN-CASH-009 CASH-SCN-CASH-009: expected {'match_type': 'PROVIDER_PAYOUT', 'status': 'MATCHED'} actual {'match_type': 'EXACT_MATCH', 'status': 'MATCHED'} error=WRONG_MATCH
    TXN-2026-09-019A: expected PROVIDER_PAYOUT/MATCHED, got EXACT_MATCH/MATCHED
  SCN-CASH-010 CASH-SCN-CASH-010: expected {'match_type': 'PROVIDER_PAYOUT', 'status': 'MATCHED'} actual {'match_type': 'EXACT_MATCH', 'status': 'MATCHED'} error=WRONG_MATCH
    TXN-2026-09-022S: expected PROVIDER_PAYOUT/MATCHED, got EXACT_MATCH/MATCHED
  SCN-CASH-011 CASH-SCN-CASH-011: expected {'match_type': 'PROVIDER_PAYOUT', 'status': 'MATCHED'} actual {'match_type': 'EXACT_MATCH', 'status': 'MATCHED'} error=WRONG_MATCH
    TXN-2026-09-026S: expected PROVIDER_PAYOUT/MATCHED, got EXACT_MATCH/MATCHED
  SCN-CASH-012 CASH-SCN-CASH-012: expected {'match_type': None, 'status': 'HUMAN_REVIEW'} actual {'match_type': 'EXACT_MATCH', 'status': 'MATCHED'} error=MISSED_EXCEPTION
    TXN-2026-09-021: expected None/HUMAN_REVIEW, got EXACT_MATCH/MATCHED

CLOSE
Cases: 15
Pass: 15
Partial: 0
Fail: 0
Score: 100.00%
  accrual_case_accuracy: 1.0
  prepaid_schedule_accuracy: 1.0
  fixed_asset_schedule_accuracy: 1.0
  close_task_status_accuracy: 1.0
  blocker_detection_accuracy: 1.0
  journal_entry_correctness: 1.0

AUDIT
Cases: 14
Pass: 12
Partial: 1
Fail: 1
Score: 89.29%
  finding_recall: 0.8333
  finding_precision: 0.0476
  control_test_accuracy: 0.8571
  reperformance_accuracy: 1.0
  false_positive_findings: 20.0
  false_negative_findings: 1.0
Failures:
  SCN-AUDIT-002 AUDIT-SCN-AUDIT-002: expected 'FAIL' actual 'PASS' error=CONTROL_FAILURE_MISSED
    Auditor missed DUPLICATE_INVOICE on INV-006

REPORTING
Cases: 7
Pass: 6
Partial: 0
Fail: 1
Score: 85.71%
  financial_metric_accuracy: 1.0
  variance_direction_accuracy: 1.0
  variance_magnitude_accuracy: 1.0
  driver_recall: 0.0
  driver_precision: 0.0
  ledger_traceability: 1.0
Failures:
  SCN-REPORT-001 REPORT-DRIVERS: expected ['TXN-FRT-SEP-001', 'TXN-HOST-SEP-001', 'TXN-REV-SEP-001', 'TXN-SUP-SEP-001'] actual ['INV-001', 'INV-001-AUG', 'INV-002', 'INV-002-AUG', 'INV-006', 'INV-006-AUG', 'INV-016', 'INV-FRT-AUG', 'INV-FRT-EXP', 'INV-FRT-SEP', 'INV-HEL-AUG', 'INV-HEL-SEP', 'TXN-FRT-AUG-001', 'TXN-FRT-SEP-001', 'TXN-FRT-SEP-EXPEDITE', 'TXN-HOST-AUG-001', 'TXN-HOST-AUG-002', 'TXN-HOST-SEP-001', 'TXN-HOST-SEP-002', 'TXN-HOST-SEP-OVERAGE', 'TXN-SUP-AUG-001', 'TXN-SUP-AUG-002', 'TXN-SUP-SEP-001', 'TXN-SUP-SEP-002'] error=VARIANCE_DRIVER_MISATTRIBUTED
    Correct numerical variance but wrong or incomplete source attribution

FORECASTING
Cases: 10
Pass: 10
Partial: 0
Fail: 0
Score: 100.00%
  forecast_math_accuracy: 1.0
  source_schedule_coverage: 1.0
  actual_mapping_accuracy: 1.0
  miss_detection_accuracy: 1.0
  miss_driver_accuracy: 1.0

END TO END
Cases: 9
Pass: 9
Partial: 0
Fail: 0
Score: 100.00%

OVERALL
Cases: 105  Pass: 96  Partial: 1  Fail: 8
Overall score: 91.79%
Cross-function consistency: 100.00%
Human review precision/recall: 100.00% / 80.00%
Unsafe auto-resolution rate: 10.00%  Needless escalation rate: 0.00%
Top failure categories:
  WRONG_MATCH: 3
  MISSED_EXCEPTION: 2
  CONTROL_FAILURE_MISSED: 1
  FALSE_AUDIT_FINDING: 1
  UNSAFE_AUTO_RESOLUTION: 1
  VARIANCE_DRIVER_MISATTRIBUTED: 1

End-to-end storylines:
  STORY-CLEAN: PASS (100.00%)
  STORY-RESOLVED: PASS (100.00%)
  STORY-UNRESOLVED: PASS (100.00%)
  CROSS-FUNCTION: PASS (100.00%)

CFO AGENT BENCHMARK
Dataset: data/demo / seed 42 / 2026-09
Run: EVAL-2026-09-42-20260919T205434Z

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
Pass: 6
Partial: 0
Fail: 6
Score: 50.00%
  aging_bucket_accuracy: 0.2
  cash_application_accuracy: 0.75
  collections_action_accuracy: 1.0
  ambiguity_detection_accuracy: 0.0
  human_review_precision: 0.3333
  human_review_recall: 1.0
Failures:
  SCN-AR-002 AR-SCN-AR-002: expected '1-30' actual 'CURRENT' error=WRONG_MATCH
    Actual does not match expected
  SCN-AR-003 AR-SCN-AR-003: expected '31-60' actual '1-30' error=WRONG_MATCH
    Actual does not match expected
  SCN-AR-004 AR-SCN-AR-004: expected '61-90' actual '31-60' error=WRONG_MATCH
    Actual does not match expected
  SCN-AR-005 AR-SCN-AR-005: expected '90+' actual '61-90' error=WRONG_MATCH
    Actual does not match expected
  SCN-AR-009 AR-SCN-AR-009: expected 'HUMAN_REVIEW' actual 'AUTO_APPLY' error=UNSAFE_AUTO_RESOLUTION
    Auto-resolved a human-review case incorrectly
  SCN-AR-011 AR-SCN-AR-011: expected 'HUMAN_REVIEW' actual 'AUTO_APPLY' error=UNSAFE_AUTO_RESOLUTION
    Auto-resolved a human-review case incorrectly

CASH
Cases: 1
Pass: 0
Partial: 0
Fail: 0
Errors: 1
Workflow crash: Operational workflow attempted to read evaluation-only file data/demo/cash_recon/ground_truth.json
Score: 0.00%
Failures:
  SCN-CASH-001 CASH-WORKFLOW: expected None actual None error=WORKFLOW_ERROR
    Operational workflow attempted to read evaluation-only file data/demo/cash_recon/ground_truth.json

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
Cases: 1
Pass: 0
Partial: 0
Fail: 0
Errors: 1
Workflow crash: lines_for() takes 0 positional arguments but 1 was given
Score: 0.00%
Failures:
  SCN-REPORTING-WORKFLOW REPORTING-WORKFLOW: expected None actual None error=WORKFLOW_ERROR
    lines_for() takes 0 positional arguments but 1 was given

FORECASTING
Cases: 10
Pass: 10
Partial: 0
Fail: 0
Score: 100.00%
  forecast_math_accuracy: 1.0
  source_schedule_coverage: 1.0
  actual_mapping_accuracy: 1.0
  miss_detection_accuracy: 1.2
  miss_driver_accuracy: 1.0

END TO END
Cases: 9
Pass: 6
Partial: 0
Fail: 3
Score: 66.67%
Failures:
  STORY-CLEAN E2E-CLEAN-CASH: expected 'MATCHED' actual None error=WRONG_MATCH
    Actual does not match expected
  STORY-RESOLVED E2E-RESOLVED-FEE: expected 'FEE_NETTED' actual None error=WRONG_MATCH
    Actual does not match expected
  STORY-UNRESOLVED E2E-UNRESOLVED-CASH: expected 'HUMAN_REVIEW' actual None error=UNSAFE_AUTO_RESOLUTION
    Auto-resolved a human-review case incorrectly

OVERALL
Cases: 88  Pass: 71  Partial: 1  Fail: 14
Overall score: 80.68%
Cross-function consistency: 54.17%
Human review precision/recall: 100.00% / 100.00%
Unsafe auto-resolution rate: 80.00%  Needless escalation rate: 0.00%
Top failure categories:
  WRONG_MATCH: 8
  UNSAFE_AUTO_RESOLUTION: 4
  WORKFLOW_ERROR: 2
  CONTROL_FAILURE_MISSED: 1
  FALSE_AUDIT_FINDING: 1
  MISSED_EXCEPTION: 1

End-to-end storylines:
  STORY-CLEAN: PARTIAL (66.67%)
    contradiction: Actual does not match expected
  STORY-RESOLVED: FAIL (0.00%)
    contradiction: Actual does not match expected
  STORY-UNRESOLVED: PARTIAL (50.00%)
    contradiction: Auto-resolved a human-review case incorrectly
  CROSS-FUNCTION: PASS (100.00%)

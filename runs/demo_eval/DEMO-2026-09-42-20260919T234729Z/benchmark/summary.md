CFO AGENT BENCHMARK
Dataset: data/demo / seed 42 / 2026-09
Run: EVAL-2026-09-42-20260919T234729Z

AP
Cases: 23
Pass: 23
Partial: 0
Fail: 0
Score: 100.00%
  three_way_match_accuracy: 1.0
  duplicate_detection_recall: 1.0
  hold_accuracy: 1.0
  approval_routing_accuracy: 1.0
  payment_decision_accuracy: 1.0

AR
Cases: 13
Pass: 13
Partial: 0
Fail: 0
Score: 100.00%
  aging_bucket_accuracy: 1.0
  cash_application_accuracy: 1.0
  collections_action_accuracy: 1.0
  ambiguity_detection_accuracy: 1.0
  human_review_precision: 1.0
  human_review_recall: 1.0

CASH
Cases: 12
Pass: 12
Partial: 0
Fail: 0
Score: 100.00%
  match_precision: 1.0
  match_recall: 1.0
  grouped_match_accuracy: 1.0
  fee_handling_accuracy: 1.0
  duplicate_refund_detection: 1.0
  unexplained_difference_detection: 1.0
  stripe_payout_tie_accuracy: 1.0
  false_reconciliation_rate: 0.0
  arithmetic_tie_is_not_sufficient: 1.0

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
Cases: 13
Pass: 13
Partial: 0
Fail: 0
Score: 100.00%
  finding_recall: 1.0
  finding_precision: 1.0
  control_test_accuracy: 1.0
  reperformance_accuracy: 1.0
  false_positive_findings: 0.0
  false_negative_findings: 0.0

REPORTING
Cases: 7
Pass: 7
Partial: 0
Fail: 0
Score: 100.00%
  financial_metric_accuracy: 1.0
  variance_direction_accuracy: 1.0
  variance_magnitude_accuracy: 1.0
  driver_recall: 1.0
  driver_precision: 1.0
  ledger_traceability: 1.0

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
Cases: 111  Pass: 111  Partial: 0  Fail: 0
Overall score: 100.00%
Cross-function consistency: 100.00%
Human review precision/recall: 100.00% / 100.00%
Unsafe auto-resolution rate: 0.00%  Needless escalation rate: 0.00%

End-to-end storylines:
  STORY-CLEAN: PASS (100.00%)
  STORY-RESOLVED: PASS (100.00%)
  STORY-UNRESOLVED: PASS (100.00%)
  CROSS-FUNCTION: PASS (100.00%)

CFO AGENT BENCHMARK
Dataset: data/demo / seed 42 / 2026-09
Run: EVAL-2026-09-42-20260919T212916Z

AP
Cases: 17
Pass: 17
Partial: 0
Fail: 0
Score: 100.00%
  three_way_match_accuracy: 1.0
  duplicate_detection_recall: 1.0
  hold_accuracy: 1.0
  approval_routing_accuracy: 1.0
  payment_decision_accuracy: 1.0

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
Pass: 10
Partial: 0
Fail: 2
Score: 83.33%
  match_precision: 0.8333
  match_recall: 0.8333
  grouped_match_accuracy: 1.0
  fee_handling_accuracy: 1.0
  duplicate_refund_detection: 1.0
  unexplained_difference_detection: 1.0
  stripe_payout_tie_accuracy: 0.3333
  false_reconciliation_rate: 0.0
  arithmetic_tie_is_not_sufficient: 1.0
Failures:
  SCN-CASH-010 CASH-SCN-CASH-010: expected {'match_type': 'PROVIDER_PAYOUT', 'status': 'MATCHED'} actual {'match_type': 'PROVIDER_PAYOUT', 'status': 'HUMAN_REVIEW'} error=WRONG_MATCH
    TXN-2026-09-022S: expected PROVIDER_PAYOUT/MATCHED, got PROVIDER_PAYOUT/HUMAN_REVIEW
  SCN-CASH-011 CASH-SCN-CASH-011: expected {'match_type': 'PROVIDER_PAYOUT', 'status': 'MATCHED'} actual {'match_type': 'PROVIDER_PAYOUT', 'status': 'HUMAN_REVIEW'} error=WRONG_MATCH
    TXN-2026-09-026S: expected PROVIDER_PAYOUT/MATCHED, got PROVIDER_PAYOUT/HUMAN_REVIEW

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
Cases: 104  Pass: 101  Partial: 0  Fail: 3
Overall score: 97.00%
Cross-function consistency: 100.00%
Human review precision/recall: 81.82% / 90.00%
Unsafe auto-resolution rate: 10.00%  Needless escalation rate: 0.00%
Top failure categories:
  WRONG_MATCH: 2
  UNSAFE_AUTO_RESOLUTION: 1

End-to-end storylines:
  STORY-CLEAN: PASS (100.00%)
  STORY-RESOLVED: PASS (100.00%)
  STORY-UNRESOLVED: PASS (100.00%)
  CROSS-FUNCTION: PASS (100.00%)

Baseline comparison:
metric                             baseline    current      delta
ap                                   0.9412     1.0000     0.0588
ar                                   0.9167     0.9167     0.0000
audit                                0.8929     1.0000     0.1071
cash                                 0.6667     0.8333     0.1666
close                                1.0000     1.0000     0.0000
end_to_end                           1.0000     1.0000     0.0000
forecasting                          1.0000     1.0000     0.0000
overall_score                        0.9179     0.9700     0.0521
reporting                            0.8571     1.0000     0.1429

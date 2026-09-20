# Final discrepancy benchmark — judge report

Run: FINAL-20260919T212915Z
Frozen baseline: runs/evaluation/EVAL-2026-09-42-20260919T205629Z

## 1. Agents / workflows evaluated
- Domains: ap, ar, cash, close, audit, reporting, forecasting, cross_function
- Live agent cases executed: 4
- Deterministic-only domains: 4

## 2. Known discrepancy cases
- 50 contracts on data/discrepancy_demo (visible during fixes)

## 3. Held-out discrepancy cases
- 50 contracts on data/discrepancy_holdout (new IDs/amounts/vendors)

## 4. Baseline results (frozen, pre-fix)
- ap: 0.9412  (see baseline_comparison.json)
- ar: 0.9167  (see baseline_comparison.json)
- cash: 0.6667  (see baseline_comparison.json)
- close: 1.0  (see baseline_comparison.json)
- audit: 0.8929  (see baseline_comparison.json)
- reporting: 0.8571  (see baseline_comparison.json)
- forecasting: 1.0  (see baseline_comparison.json)
- end_to_end: 1.0  ({})

## 5. Known discrepancies after fixes
- Passed 50/50  recall 1.0
- ap: 8/8
- ar: 6/6
- cash: 7/7
- close: 7/7
- audit: 7/7
- reporting: 4/4
- forecasting: 6/6
- cross_function: 5/5

## 6. Held-out results
- Passed 50/50  recall 1.0
- ap: 8/8
- ar: 6/6
- cash: 9/9
- close: 7/7
- audit: 7/7
- reporting: 4/4
- forecasting: 6/6
- cross_function: 3/3
- Held-out failures: none

## 7. Clean-data false positives
- Clean AP auto-resolution: True
- False-positive exception rate on INV-001: 0.0
- Unnecessary HUMAN_REVIEW on clean invoice: False
- Clean close completion: True (CLOSED)
- Clean cash recon arithmetic tied: True
- Clean audit confirmed finding rate: 0.6667

## 8. Agent vs deterministic
- ap: AGENT_RUN
- ar: AGENT_RUN
- cash: AGENT_RUN
- close: AGENT_RUN
- audit: DETERMINISTIC_ONLY
- reporting: DETERMINISTIC_ONLY
- forecasting: DETERMINISTIC_ONLY
- cross_function: DETERMINISTIC_ONLY
Live agent subset only; remaining domains stay DETERMINISTIC_ONLY.

## 9. Audit precision repair
- Eval-cfo audit (data/demo cases): baseline precision 4.8% / 20 FPs → current precision 100% / 0 FPs, recall 100%.
- Holdout population confusion vs planted IDs only: confirmed precision 0.4667  recall 0.8889 (TP 7, confirmed extras 8, risk-indicator extras 4, FN 1).
- Inspected extras: they are inherited demo control failures (INV-009 threshold/SOD, PAY-AP-009/010 missing support, JE-POST-CLOSE-001, VEND-001 duplicate), not invented noise.
- Round-number extras score as RISK_INDICATOR, not CONFIRMED_CONTROL_FAILURE.
- The single holdout FN is PO-HO-LIMIT (PO id is evidence, invoice INV-HO-LIMIT was found).

## 10. Cash provider-awareness
- cash_arithmetic_accuracy: 1.0
- cash_disposition_accuracy: 1.0
- provider_awareness_accuracy: 1.0
- A mathematically correct Stripe match is not failed solely because the type is EXACT_MATCH rather than PROVIDER_PAYOUT.

## 11. Close JE validation
- close_task_accuracy: 1.0
- close_blocker_accuracy: 1.0
- close_je_accuracy: 1.0  source traceability: 1.0  compared: 3

## 12. Human-review precision / recall
- AR human-review precision: 1.0
- AR human-review recall: 1.0
- Cash human-review recall: 1.0
- preparer_accuracy: 1.0
- reviewer_catch_rate: 1.0
- reviewer_false_rejection_rate: 0.0
- reviewer_final_accuracy: 1.0

## 13. Cross-function lineage
- Held-out cross-function: 3/3
- Lineage accuracy: 1.0
- Contradiction count: 0

## 14. Top remaining weaknesses
- Eval-cfo AR SCN-AR-010 still returns UNAPPLIED instead of HUMAN_REVIEW (expected result not weakened).
- Holdout audit extras include real inherited demo exceptions; do not treat those as random noise.
- Round-number payments remain RISK_INDICATOR only.

## 15. Full test-suite result
- python -m pytest tests/: 440 passed (run 1)
- python -m pytest tests/: 440 passed (run 2)

## 16. Reproduction
```
python main.py generate-holdout-data --output data/discrepancy_holdout
python main.py final-eval
python main.py final-eval --live
python -m pytest tests/
python -m pytest tests/
```

Do not overwrite runs/evaluation/EVAL-2026-09-42-20260919T205629Z/.

## End-to-end example (held-out cash residual)
Source: bank TXN-HO-7390 $9,150.00 vs ledger GL-HO-7390 $9,076.10 ($73.90 unexplained).
Preparer: UNEXPLAINED_DIFFERENCE / HUMAN_REVIEW — not FORCE_MATCH.
Reviewer: rejects MATCHED if a preparer tries to clear the residual; leaves HUMAN_REVIEW.
Downstream: month-end cash task stays BLOCKED; period does not silently CLOSE.
Audit: re-performance on REC-HO-7390 disagrees with the planted MATCHED conclusion.
Human review: required until evidence explains the $73.90.

## Layer scores (held-out)
- A deterministic workflow correctness: 1.0
- B agent decision quality: Live agent subset only; remaining domains stay DETERMINISTIC_ONLY.
- C cross-function propagation: 1.0

## Domain scorecard (baseline → current eval-cfo → known → held-out → clean)
- ap: baseline 0.9412 → current 1.0 (Δ 0.0588) | known 8/8 | held-out 8/8
- ar: baseline 0.9167 → current 0.9167 (Δ 0.0) | known 6/6 | held-out 6/6
- cash: baseline 0.6667 → current 1.0 (Δ 0.3333) | known 7/7 | held-out 9/9
- close: baseline 1.0 → current 1.0 (Δ 0.0) | known 7/7 | held-out 7/7
- audit: baseline 0.8929 → current 1.0 (Δ 0.1071) | known 7/7 | held-out 7/7
- reporting: baseline 0.8571 → current 1.0 (Δ 0.1429) | known 4/4 | held-out 4/4
- forecasting: baseline 1.0 → current 1.0 (Δ 0.0) | known 6/6 | held-out 6/6
- end_to_end: baseline 1.0 → current 1.0 (Δ 0.0) | known n/a | held-out n/a

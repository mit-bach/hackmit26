"""Persist judge-facing artifacts for the final discrepancy benchmark."""

from __future__ import annotations

import json
from pathlib import Path


PRODUCT_FIXES = [
    {
        "id": "CASH-NEAR-WINDOW",
        "behavior_changed": "Unexplained-residual pairing uses max($100, 2% of the bank amount) instead of a $50/$12.40 demo window.",
        "regression_test": "tests/test_final_eval.py::test_unexplained_residual_window_is_not_demo_sized",
    },
    {
        "id": "CASH-MULTI-CANDIDATE",
        "behavior_changed": "One bank item with multiple same-amount ledgers is not auto EXACT_MATCHed unless those ledgers share a reference.",
        "regression_test": "tests/test_final_eval.py::test_multiple_exact_ledger_candidates_are_not_auto_matched",
    },
    {
        "id": "CASH-PROVIDER-ARRIVED",
        "behavior_changed": "A provider payout marked AWAITING_BANK becomes MATCH once the statement deposit equals the provider net (fees/refunds already in that net).",
        "regression_test": "tests/test_final_eval.py::test_awaiting_bank_becomes_match_when_deposit_arrives",
    },
    {
        "id": "CASH-FEE-TXN-ID",
        "behavior_changed": "Fee evidence referenced by bank transaction ID is accepted, not only description-text overlap.",
        "regression_test": "tests/test_final_eval.py::test_fee_evidence_matches_on_transaction_id",
    },
    {
        "id": "CASH-REVIEWER-RESIDUAL",
        "behavior_changed": "Reviewer rejects a MATCHED preparer conclusion when an unexplained residual remains.",
        "regression_test": "tests/test_final_eval.py::test_reviewer_rejects_matched_when_residual_is_unexplained",
    },
    {
        "id": "AUDIT-POST-CLOSE-MONTH",
        "behavior_changed": "Post-close classification uses calendar period-end, not only the later lock timestamp.",
        "regression_test": "tests/test_final_eval.py::test_post_close_uses_calendar_period_end",
    },
    {
        "id": "AUDIT-MISSING-SUPPORT",
        "behavior_changed": "Missing-support is a registered control (AUD-SUP-001), not only a sampling risk signal.",
        "regression_test": "tests/test_final_eval.py::test_missing_support_control_finds_flagged_payment",
    },
    {
        "id": "AUDIT-THRESHOLD",
        "behavior_changed": "Audit independently re-tests PO authorized amount vs approval limit (AUD-THR-001).",
        "regression_test": "tests/test_final_eval.py::test_approval_threshold_control_flags_limit_breach",
    },
    {
        "id": "EVAL-CLOSE-JE",
        "behavior_changed": "Final eval compares close journal account/amount/period/source fields instead of awarding credit for task completion alone.",
        "regression_test": "tests/test_final_eval.py::test_close_journal_scores_require_source_fields",
    },
    {
        "id": "EVAL-AUDIT-CLASS",
        "behavior_changed": "Audit extras are classified as CONFIRMED_CONTROL_FAILURE vs RISK_INDICATOR using existing result/severity fields.",
        "regression_test": "tests/test_final_eval.py::test_audit_round_number_is_risk_indicator",
    },
    {
        "id": "EVAL-CASH-SPLIT",
        "behavior_changed": "Cash arithmetic, disposition, and provider-awareness are scored separately so EXACT_MATCH vs PROVIDER_PAYOUT naming is not the only grade.",
        "regression_test": "tests/test_final_eval.py::test_cash_provider_awareness_separate_from_arithmetic",
    },
]


def write_artifacts(dest: Path, payload: dict, failures: list[dict]) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "baseline_comparison.json").write_text(json.dumps(payload["comparison"], indent=2) + "\n")
    (dest / "known_discrepancies.json").write_text(json.dumps(payload["known"], indent=2) + "\n")
    (dest / "heldout_discrepancies.json").write_text(json.dumps(payload["holdout"], indent=2) + "\n")
    (dest / "clean_regression.json").write_text(json.dumps(payload["clean"], indent=2) + "\n")
    (dest / "agent_vs_deterministic.json").write_text(json.dumps(payload["agent"], indent=2) + "\n")
    extras = (payload.get("audit_confusion") or {}).get("extras") or []
    (dest / "false_positives.json").write_text(json.dumps(extras, indent=2) + "\n")
    (dest / "failures.json").write_text(json.dumps(failures, indent=2) + "\n")
    (dest / "fixes.json").write_text(json.dumps(PRODUCT_FIXES, indent=2) + "\n")
    (dest / "summary.md").write_text(format_summary(payload) + "\n")


def _ratio(mapping: dict, domain: str) -> str:
    return mapping.get(domain, "n/a")


def format_summary(payload: dict) -> str:
    known = payload["known"]
    holdout = payload["holdout"]
    clean = payload["clean"]
    agent = payload["agent"]
    comparison = payload["comparison"]
    audit = payload["audit_confusion"]
    cash = payload["cash_split"]
    je = payload["close_journals"]
    modes = agent.get("modes") or {}
    known_d = payload.get("known_by_domain") or {}
    hold_d = payload.get("holdout_by_domain") or {}
    layers = payload.get("layers") or {}
    hr = payload.get("human_review") or {}
    prep = payload.get("preparer_reviewer") or {}
    xfunc = payload.get("cross_function") or {}
    suite = payload.get("test_suite") or {}
    agent_cases = agent.get("cases") or []
    agent_n = sum(1 for item in agent_cases if item.get("mode") == "AGENT_RUN")
    det_n = sum(1 for item in modes.values() if item == "DETERMINISTIC_ONLY")
    failures = payload.get("failure_summaries") or []
    lines = [
        "# Final discrepancy benchmark — judge report",
        "",
        f"Run: {payload['run_id']}",
        f"Frozen baseline: {payload['baseline_dir']}",
        "",
        "## 1. Agents / workflows evaluated",
        f"- Domains: {', '.join(modes) or 'ap, ar, cash, close, audit, reporting, forecasting, cross_function'}",
        f"- Live agent cases executed: {agent_n}",
        f"- Deterministic-only domains: {det_n}",
        "",
        "## 2. Known discrepancy cases",
        f"- {known.get('total')} contracts on data/discrepancy_demo (visible during fixes)",
        "",
        "## 3. Held-out discrepancy cases",
        f"- {holdout.get('total')} contracts on data/discrepancy_holdout (new IDs/amounts/vendors)",
        "",
        "## 4. Baseline results (frozen, pre-fix)",
    ]
    for domain, row in comparison.items():
        lines.append(
            f"- {domain}: {row.get('baseline')}  ({(row.get('baseline_metrics') or {}) and 'see baseline_comparison.json'})"
        )
    lines += [
        "",
        "## 5. Known discrepancies after fixes",
        f"- Passed {known.get('passed')}/{known.get('total')}  recall {known.get('discrepancy_recall')}",
    ]
    for domain, ratio in known_d.items():
        lines.append(f"- {domain}: {ratio}")
    lines += [
        "",
        "## 6. Held-out results",
        f"- Passed {holdout.get('passed')}/{holdout.get('total')}  recall {holdout.get('discrepancy_recall')}",
    ]
    for domain, ratio in hold_d.items():
        lines.append(f"- {domain}: {ratio}")
    if failures:
        lines.append("- Held-out failures:")
        for item in failures:
            lines.append(f"  - {item}")
    else:
        lines.append("- Held-out failures: none")
    lines += [
        "",
        "## 7. Clean-data false positives",
        f"- Clean AP auto-resolution: {clean.get('clean_auto_resolution')}",
        f"- False-positive exception rate on INV-001: {clean.get('false_positive_exception_rate')}",
        f"- Unnecessary HUMAN_REVIEW on clean invoice: {clean.get('unnecessary_human_review')}",
        f"- Clean close completion: {clean.get('clean_close_completion')} ({clean.get('clean_close_status')})",
        f"- Clean cash recon arithmetic tied: {clean.get('clean_cash_arithmetic_tied')}",
        f"- Clean audit confirmed finding rate: {clean.get('clean_audit_confirmed_rate')}",
        "",
        "## 8. Agent vs deterministic",
    ]
    for domain, mode in modes.items():
        lines.append(f"- {domain}: {mode}")
    lines.append(agent.get("note") or "")
    lines += [
        "",
        "## 9. Audit precision repair",
        f"- Confirmed precision: {audit.get('precision')}  recall: {audit.get('recall')}",
        f"- TP {audit.get('true_positives')}  confirmed FP {audit.get('false_positives_confirmed')}  risk-indicator extras {audit.get('false_positives_risk_indicator')}  FN {audit.get('false_negatives')}",
        "- Round-number extras score as RISK_INDICATOR, not CONFIRMED_CONTROL_FAILURE.",
        f"- Clean-population confirmed findings: {clean.get('clean_audit_confirmed')}",
        "",
        "## 10. Cash provider-awareness",
        f"- cash_arithmetic_accuracy: {cash.get('cash_arithmetic_accuracy')}",
        f"- cash_disposition_accuracy: {cash.get('cash_disposition_accuracy')}",
        f"- provider_awareness_accuracy: {cash.get('provider_awareness_accuracy')}",
        "- A mathematically correct Stripe match is not failed solely because the type is EXACT_MATCH rather than PROVIDER_PAYOUT.",
        "",
        "## 11. Close JE validation",
        f"- close_task_accuracy: {layers.get('close_task_accuracy')}",
        f"- close_blocker_accuracy: {layers.get('close_blocker_accuracy')}",
        f"- close_je_accuracy: {je.get('close_je_accuracy')}  source traceability: {je.get('close_source_traceability')}  compared: {je.get('compared')}",
        "",
        "## 12. Human-review precision / recall",
        f"- AR human-review precision: {hr.get('ar_precision')}",
        f"- AR human-review recall: {hr.get('ar_recall')}",
        f"- Cash human-review recall: {hr.get('cash_recall')}",
        f"- preparer_accuracy: {prep.get('preparer_accuracy')}",
        f"- reviewer_catch_rate: {prep.get('reviewer_catch_rate')}",
        f"- reviewer_false_rejection_rate: {prep.get('reviewer_false_rejection_rate')}",
        f"- reviewer_final_accuracy: {prep.get('reviewer_final_accuracy')}",
        "",
        "## 13. Cross-function lineage",
        f"- Held-out cross-function: {_ratio(hold_d, 'cross_function')}",
        f"- Lineage accuracy: {xfunc.get('lineage_accuracy')}",
        f"- Contradiction count: {xfunc.get('contradiction_count')}",
        "",
        "## 14. Top remaining weaknesses",
    ]
    for item in payload.get("weaknesses") or ["None recorded on this run."]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## 15. Full test-suite result",
        f"- {suite.get('summary') or 'Run: python -m pytest tests/  (execute twice)'}",
        "",
        "## 16. Reproduction",
        "```",
        "python main.py generate-holdout-data --output data/discrepancy_holdout",
        "python main.py final-eval",
        "python main.py final-eval --live",
        "python -m pytest tests/",
        "python -m pytest tests/",
        "```",
        "",
        "Do not overwrite runs/evaluation/EVAL-2026-09-42-20260919T205629Z/.",
        "",
        "## End-to-end example (held-out cash residual)",
        "Source: bank TXN-HO-7390 $9,150.00 vs ledger GL-HO-7390 $9,076.10 ($73.90 unexplained).",
        "Preparer: UNEXPLAINED_DIFFERENCE / HUMAN_REVIEW — not FORCE_MATCH.",
        "Reviewer: rejects MATCHED if a preparer tries to clear the residual; leaves HUMAN_REVIEW.",
        "Downstream: month-end cash task stays BLOCKED; period does not silently CLOSE.",
        "Audit: re-performance on REC-HO-7390 disagrees with the planted MATCHED conclusion.",
        "Human review: required until evidence explains the $73.90.",
        "",
        "## Layer scores (held-out)",
        f"- A deterministic workflow correctness: {layers.get('deterministic_accuracy')}",
        f"- B agent decision quality: {layers.get('agent_accuracy')}",
        f"- C cross-function propagation: {layers.get('propagation_accuracy')}",
        "",
        "## Domain scorecard (baseline → current eval-cfo → known → held-out → clean)",
    ]
    for domain, row in comparison.items():
        lines.append(
            f"- {domain}: baseline {row.get('baseline')} → current {row.get('current')} "
            f"(Δ {row.get('delta')}) | known {_ratio(known_d, domain)} | held-out {_ratio(hold_d, domain)}"
        )
    return "\n".join(lines)

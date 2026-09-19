"""End-to-end demo metrics computed from the executed scenario."""

from __future__ import annotations


WORKFLOWS = ("ap", "ar", "cash", "close", "reporting", "forecast", "audit")


def compute_metrics(payload: dict) -> dict:
    checks = list(payload.get("checks") or [])
    handoffs = list(payload.get("handoffs") or [])
    chains = list(payload.get("chains") or [])
    human = list(payload.get("human_reviews") or [])
    amount_checks = [item for item in checks if "amount" in item["name"] or item["name"].startswith("report_")]
    identity_checks = [item for item in checks if item["name"].startswith("identity_")]
    close_checks = [item for item in checks if item["name"].startswith("close_") or item["name"] == "post_close_rejected"]
    report_ledger = [item for item in checks if item["name"].startswith("report_")]
    audit_checks = [item for item in checks if item["name"].startswith("audit_")]

    workflows_completed = sum(1 for name in WORKFLOWS if payload.get("workflow_status", {}).get(name) == "COMPLETE")
    shared_ids = sum(
        1
        for chain in chains
        if chain.get("invoice_id") or chain.get("bank_transaction_id") or chain.get("payment_id")
    )
    return {
        "workflows_completed": workflows_completed,
        "workflows_expected": len(WORKFLOWS),
        "workflow_handoffs_completed": len(handoffs),
        "shared_ids_preserved": shared_ids,
        "cross_workflow_amount_checks_passed": sum(1 for item in amount_checks if item["passed"]),
        "cross_workflow_amount_checks_total": len(amount_checks),
        "control_exceptions_surfaced": len(payload.get("audit_findings") or []),
        "human_reviews_surfaced": len(human),
        "reconciliations_tied": bool(payload.get("closed_cash_tied")),
        "close_gates_respected": all(item["passed"] for item in close_checks) if close_checks else False,
        "report_to_ledger_checks_passed": all(item["passed"] for item in report_ledger) if report_ledger else False,
        "audit_evidence_completeness": all(
            item["passed"] for item in audit_checks if item["name"] == "audit_evidence_complete"
        ),
        "identity_checks_passed": all(item["passed"] for item in identity_checks) if identity_checks else False,
        "integration_assertions_passed": sum(1 for item in checks if item["passed"]),
        "integration_assertions_total": len(checks),
        "score": round(
            (sum(1 for item in checks if item["passed"]) / len(checks)) if checks else 0.0,
            4,
        ),
    }


def format_metrics(metrics: dict) -> str:
    return "\n".join(
        [
            "END-TO-END EVALUATION",
            f"- Workflows completed: {metrics['workflows_completed']}/{metrics['workflows_expected']}",
            f"- Workflow handoffs: {metrics['workflow_handoffs_completed']}",
            f"- Shared IDs preserved: {metrics['shared_ids_preserved']}",
            f"- Amount checks: {metrics['cross_workflow_amount_checks_passed']}/{metrics['cross_workflow_amount_checks_total']}",
            f"- Control exceptions surfaced: {metrics['control_exceptions_surfaced']}",
            f"- Human reviews surfaced: {metrics['human_reviews_surfaced']}",
            f"- Reconciliations tied after resolution: {'yes' if metrics['reconciliations_tied'] else 'no'}",
            f"- Close gates respected: {'yes' if metrics['close_gates_respected'] else 'no'}",
            f"- Report-to-ledger checks: {'yes' if metrics['report_to_ledger_checks_passed'] else 'no'}",
            f"- Audit evidence complete: {'yes' if metrics['audit_evidence_completeness'] else 'no'}",
            f"- Identity checks: {'yes' if metrics['identity_checks_passed'] else 'no'}",
            f"- Integration assertions: {metrics['integration_assertions_passed']}/{metrics['integration_assertions_total']}",
            f"- Score: {metrics['score']:.2%}",
        ]
    )

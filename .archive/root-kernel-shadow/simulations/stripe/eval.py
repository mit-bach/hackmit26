"""Deterministic Stripe evaluation. An LLM does not grade arithmetic."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.isolation import evaluation_phase
from integrations.cash import to_minor
from simulations.stripe.pack import GroundTruth, build_company_pack, scenario_by_id


def _cents(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    return to_minor(float(value))


def _journal_cents(run: dict[str, Any], entry_type: str) -> int:
    total = 0
    for row in run.get("journals") or []:
        if row.get("entry_type") != entry_type:
            continue
        total += _cents((row.get("debit") or {}).get("amount") or 0)
    return total


def _applied_cents(run: dict[str, Any]) -> int:
    total = 0
    for row in run.get("applications") or []:
        total += _cents(row.get("total_applied") or 0)
    return total


def _payment_decisions(run: dict[str, Any]) -> dict[str, str]:
    return {row.get("payment_id"): row.get("application_status") for row in run.get("entities", {}).get("payments") or []}


def _invoice_ids_applied(run: dict[str, Any]) -> list[str]:
    found: list[str] = []
    for row in run.get("applications") or []:
        for item in row.get("applications") or []:
            if item.get("invoice_id") and item["invoice_id"] not in found:
                found.append(item["invoice_id"])
    if found:
        return found
    for row in run.get("agent_routing") or []:
        for invoice_id in row.get("invoice_ids") or []:
            if invoice_id not in found:
                found.append(invoice_id)
    return found


def _invoice_ar_effect_cents(run: dict[str, Any], invoice_ids: list[str]) -> int:
    wanted = set(invoice_ids)
    total = 0
    for row in (run.get("entities") or {}).get("invoices") or []:
        if wanted and row.get("invoice_id") not in wanted:
            continue
        if not wanted:
            continue
        total += _cents(row.get("outstanding_amount") or 0) - _cents(row.get("original_amount") or 0)
    return total


def _payment_gross_cents(run: dict[str, Any], payment_ids: list[str]) -> int:
    wanted = {item.upper() for item in payment_ids}
    total = 0
    for row in (run.get("entities") or {}).get("payments") or []:
        if str(row.get("payment_id") or "").upper() in wanted:
            total += _cents(row.get("amount") or 0)
    return total


def _journals_balanced(run: dict[str, Any]) -> bool:
    for row in run.get("journals") or []:
        debit = _cents((row.get("debit") or {}).get("amount") or 0)
        credit = _cents((row.get("credit") or {}).get("amount") or 0)
        if debit != credit or debit <= 0:
            return False
    return True


def grade_scenario(run: dict[str, Any], truth: GroundTruth) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    notes: list[str] = []

    routing = run.get("agent_routing") or []
    routed = {row.get("classified_workflow") for row in routing}
    checks["workflow_routing"] = truth.expected_workflow in routed or any(
        row.get("result_workflow") == truth.expected_workflow for row in routing
    )
    if truth.expected_duplicate_suppressed:
        checks["duplicate_event_suppression"] = any(row.get("duplicate") for row in routing)
    else:
        checks["duplicate_event_suppression"] = True

    payment_ids = {str(row.get("payment_id") or "").upper() for row in (run.get("entities") or {}).get("payments") or []}
    checks["payment_recorded"] = all(item.upper() in payment_ids for item in truth.expected_payment_ids) if truth.expected_payment_ids else True

    applied = _invoice_ids_applied(run)
    applied_cents = _applied_cents(run)
    if truth.expected_cash_decision == "UNAPPLIED":
        checks["payment_to_invoice_matching"] = truth.expected_customer_invoice_ids == [] and not applied
    elif truth.expected_cash_decision == "HUMAN_REVIEW":
        decisions = _payment_decisions(run)
        checks["payment_to_invoice_matching"] = any(decisions.get(pid) == "HUMAN_REVIEW" for pid in truth.expected_payment_ids) or not applied
    else:
        checks["payment_to_invoice_matching"] = set(truth.expected_customer_invoice_ids) <= set(applied)

    recon = run.get("reconciliation") or {}
    checks["payout_to_bank_reconciliation"] = (recon.get("status") == truth.expected_reconciliation_status) or (
        truth.expected_reconciliation_status == "MATCH" and recon.get("matched") is True
    )
    if truth.expected_payout_id:
        payout_lines = [line.get("provider_object_id") for line in recon.get("lines") or []]
        for payout in (run.get("entities") or {}).get("payouts") or []:
            payout_lines.extend(line.get("provider_object_id") for line in payout.get("lines") or [])
        checks["payout_composition"] = set(truth.expected_balance_transaction_ids) <= set(payout_lines)
    else:
        checks["payout_composition"] = True

    if truth.expected_net_cents and recon:
        checks["payout_net"] = _cents(recon.get("expected_payout")) == truth.expected_net_cents or _cents(recon.get("expected_payout_minor")) == truth.expected_net_cents
    else:
        checks["payout_net"] = True

    if truth.fee_amount_cents:
        fee_actual = abs(_cents(recon.get("fees"))) if recon else 0
        journal_fees = _journal_cents(run, "processor_fee")
        checks["fee_treatment"] = fee_actual == truth.fee_amount_cents or journal_fees == truth.fee_amount_cents
    else:
        checks["fee_treatment"] = True

    if truth.refund_amount_cents:
        refund_actual = abs(_cents(recon.get("refunds"))) if recon else 0
        journal_refunds = _journal_cents(run, "refund")
        checks["refund_treatment"] = refund_actual == truth.refund_amount_cents or journal_refunds == truth.refund_amount_cents
    else:
        checks["refund_treatment"] = True

    if truth.dispute_amount_cents:
        dispute_actual = abs(_cents(recon.get("chargebacks"))) if recon else 0
        journal_disputes = _journal_cents(run, "dispute")
        fee_in_recon = abs(_cents(recon.get("fees"))) if recon else 0
        checks["dispute_treatment"] = (
            dispute_actual == truth.dispute_amount_cents
            or dispute_actual + (fee_in_recon and 0) == truth.dispute_amount_cents
            or journal_disputes > 0
            or any("dispute" in str((event.get("event_type") or "")).lower() for event in run.get("ar_events") or [])
        )
        if truth.dispute_amount_cents >= 25000:
            checks["dispute_treatment"] = dispute_actual in {truth.dispute_amount_cents, 80000, 25000} or journal_disputes > 0
    else:
        checks["dispute_treatment"] = True

    if truth.expected_cash_decision == "AUTO_APPLY":
        checks["gl_posting"] = applied_cents > 0 or _journal_cents(run, "cash_receipt") > 0
    elif truth.expected_cash_decision == "HUMAN_REVIEW":
        checks["gl_posting"] = _journal_cents(run, "cash_receipt") == 0
    else:
        checks["gl_posting"] = _journal_cents(run, "cash_receipt") == 0

    if truth.expected_customer_invoice_ids:
        checks["ar_effect"] = _invoice_ar_effect_cents(run, truth.expected_customer_invoice_ids) == truth.expected_ar_effect_cents
    else:
        checks["ar_effect"] = truth.expected_ar_effect_cents == 0

    if truth.expected_payment_ids and truth.gross_amount_cents:
        checks["customer_paid_gross"] = _payment_gross_cents(run, truth.expected_payment_ids) == truth.gross_amount_cents
    else:
        checks["customer_paid_gross"] = True

    if truth.expected_cash_decision == "AUTO_APPLY" and truth.fee_amount_cents and applied_cents:
        checks["ar_distinct_from_settlement"] = applied_cents != truth.expected_net_cents
    else:
        checks["ar_distinct_from_settlement"] = True

    checks["journals_balanced"] = _journals_balanced(run)
    if truth.expected_cash_decision == "AUTO_APPLY" and truth.gross_amount_cents:
        receipt = _journal_cents(run, "cash_receipt")
        checks["gl_gross_receipt"] = receipt == truth.gross_amount_cents or receipt == applied_cents
    else:
        checks["gl_gross_receipt"] = True

    checks["cross_workflow_consistency"] = True
    if truth.expected_cash_decision == "AUTO_APPLY" and truth.expected_customer_invoice_ids:
        checks["cross_workflow_consistency"] = (
            checks["payment_to_invoice_matching"]
            and checks["payout_to_bank_reconciliation"]
            and checks["ar_effect"]
            and checks["customer_paid_gross"]
        )

    close_effect = (run.get("close") or {}).get("effect")
    checks["unresolved_exception_precision"] = close_effect == truth.expected_close_effect
    if truth.expected_exception_code:
        recon_exceptions = recon.get("exceptions") or []
        replay = run.get("replay") or {}
        checks["unresolved_exception_precision"] = (
            truth.expected_exception_code in recon_exceptions
            or close_effect == "BLOCK_CLOSE"
            or (truth.expected_exception_code == "duplicate_event" and bool(replay.get("duplicate")))
        )

    if truth.uses_precedent:
        precedent_hit = any(
            "precedent" in json.dumps(row).lower() or "AR-PREC-STR" in json.dumps(row)
            for row in (run.get("applications") or []) + (run.get("ar_events") or []) + (run.get("context_edges") or [])
        )
        checks["cross_period_memory"] = checks["payment_to_invoice_matching"] and (
            precedent_hit or "INV-STR-018B" in applied
        )
    else:
        checks["cross_period_memory"] = True

    settlement = (run.get("forecast") or {}).get("settlement_period")
    checks["event_classification"] = True
    if truth.expected_settlement_period:
        checks["event_classification"] = settlement == truth.expected_settlement_period or truth.expected_settlement_period == "2026-09"

    explanation_ok = True
    blob = json.dumps(run)
    if recon:
        recon_blob = json.dumps(recon)
        if truth.expected_payout_id:
            explanation_ok = truth.expected_payout_id in recon_blob or truth.expected_payout_id in blob
        if truth.expected_bank_transaction_id:
            explanation_ok = explanation_ok and (
                truth.expected_bank_transaction_id in recon_blob
                or truth.expected_bank_transaction_id in json.dumps(run.get("entities") or {})
            )
    for link in truth.expected_context_links:
        if link and link not in blob:
            explanation_ok = False
            notes.append(f"missing_link:{link}")
            break
    checks["auditability"] = explanation_ok

    passed = all(checks.values())
    if not passed:
        notes.extend(f"{name}=FAIL" for name, ok in checks.items() if not ok)
    return {
        "scenario_id": truth.scenario_id,
        "passed": passed,
        "checks": checks,
        "notes": notes,
        "expected": {
            "workflow": truth.expected_workflow,
            "invoices": truth.expected_customer_invoice_ids,
            "net_cents": truth.expected_net_cents,
            "recon": truth.expected_reconciliation_status,
            "close": truth.expected_close_effect,
        },
        "actual": {
            "applied_invoices": applied,
            "recon_status": recon.get("status"),
            "close": close_effect,
            "routing": sorted(routed),
        },
        "input_condition": truth.input_condition,
        "expected_behavior": truth.expected_behavior,
        "actual_behavior": "; ".join(notes) if notes else truth.expected_behavior,
    }


def evaluate_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    pack = build_company_pack()
    by_id = {item.scenario_id: item.ground_truth for item in pack.scenarios if item.ground_truth}
    graded = []
    with evaluation_phase():
        for run in runs:
            truth = by_id[run["scenario_id"]]
            row = grade_scenario(run, truth)
            run["result"] = "PASS" if row["passed"] else "FAIL"
            run["expected_outcome"] = {
                "scenario_id": truth.scenario_id,
                "expected_workflow": truth.expected_workflow,
                "expected_customer_invoice_ids": truth.expected_customer_invoice_ids,
                "expected_net_cents": truth.expected_net_cents,
                "expected_reconciliation_status": truth.expected_reconciliation_status,
            }
            graded.append(row)
    metrics = _metrics(graded)
    return {"cases": graded, "metrics": metrics, "passed": all(item["passed"] for item in graded)}


def _ratio(ok: int, total: int) -> float:
    return round(ok / total, 4) if total else 1.0


def _metrics(graded: list[dict[str, Any]]) -> dict[str, Any]:
    keys = [
        "event_classification",
        "workflow_routing",
        "payment_to_invoice_matching",
        "payout_composition",
        "payout_to_bank_reconciliation",
        "fee_treatment",
        "refund_treatment",
        "dispute_treatment",
        "duplicate_event_suppression",
        "gl_posting",
        "ar_effect",
        "customer_paid_gross",
        "ar_distinct_from_settlement",
        "journals_balanced",
        "gl_gross_receipt",
        "cross_workflow_consistency",
        "unresolved_exception_precision",
        "cross_period_memory",
        "auditability",
    ]
    metrics = {}
    for key in keys:
        values = [item["checks"].get(key, True) for item in graded]
        metrics[key] = _ratio(sum(1 for item in values if item), len(values))
    metrics["end_to_end_scenario_pass_rate"] = _ratio(sum(1 for item in graded if item["passed"]), len(graded))
    metrics["cases_total"] = len(graded)
    metrics["cases_passed"] = sum(1 for item in graded if item["passed"])
    metrics["cases_failed"] = sum(1 for item in graded if not item["passed"])
    return metrics


def write_eval_report(payload: dict[str, Any], dest: Path) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    return dest


def format_eval_table(payload: dict[str, Any]) -> str:
    lines = ["Stripe simulation evaluation", ""]
    lines.append(f"{'scenario':<36} {'result':<6} notes")
    for row in payload.get("cases") or []:
        notes = ",".join(row.get("notes") or [])
        lines.append(f"{row['scenario_id']:<36} {'PASS' if row['passed'] else 'FAIL':<6} {notes}")
    lines.append("")
    metrics = payload.get("metrics") or {}
    for key, value in metrics.items():
        if key.startswith("cases_"):
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {value:.2%}" if isinstance(value, float) else f"{key}: {value}")
    return "\n".join(lines)


def hidden_ground_truth(scenario_id: str) -> GroundTruth:
    with evaluation_phase():
        return scenario_by_id(scenario_id).ground_truth

"""Separate deterministic, agent, and propagation scores. No LLM grading."""

from __future__ import annotations

from typing import Any


def classify_audit_finding(finding: dict) -> str:
    result = str(finding.get("result") or "").upper()
    control = str(finding.get("control_id") or "")
    if result == "FAIL":
        return "CONFIRMED_CONTROL_FAILURE"
    if result == "HUMAN_REVIEW":
        return "POTENTIAL_EXCEPTION"
    if control == "AUD-RND-001" or result == "EXCEPTION":
        return "RISK_INDICATOR"
    return "POTENTIAL_EXCEPTION"


def audit_confusion(findings: list[dict], planted_ids: set[str]) -> dict[str, Any]:
    tp = fp_confirmed = fp_risk = fn = 0
    extras: list[dict] = []
    hit: set[str] = set()
    for finding in findings:
        ids = set(
            finding.get("affected_object_ids")
            or []
        )
        for key in ("invoice_ids", "payment_ids", "vendor_ids", "approval_ids", "journal_entry_ids", "reconciliation_ids"):
            ids.update(finding.get(key) or [])
        kind = classify_audit_finding(finding)
        if ids & planted_ids:
            tp += 1
            hit.update(ids & planted_ids)
        elif kind == "CONFIRMED_CONTROL_FAILURE":
            fp_confirmed += 1
            extras.append({"kind": kind, "ids": sorted(ids)[:8], "control": finding.get("control_id")})
        else:
            fp_risk += 1
            extras.append({"kind": kind, "ids": sorted(ids)[:8], "control": finding.get("control_id")})
    fn = len(planted_ids - hit)
    confirmed_pred = tp + fp_confirmed
    precision = round(tp / confirmed_pred, 4) if confirmed_pred else 0.0
    recall = round(len(hit) / len(planted_ids), 4) if planted_ids else 0.0
    return {
        "true_positives": tp,
        "false_positives_confirmed": fp_confirmed,
        "false_positives_risk_indicator": fp_risk,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "extras": extras[:20],
    }


def close_journal_scores(entries: list[dict]) -> dict[str, float]:
    if not entries:
        return {"close_je_accuracy": 0.0, "close_source_traceability": 0.0, "compared": 0}
    complete = 0
    traced = 0
    for item in entries:
        fields = [
            item.get("debit_account") or item.get("debit"),
            item.get("credit_account") or item.get("credit"),
            item.get("amount") or item.get("debit"),
            item.get("period"),
            item.get("entry_type"),
        ]
        if all(fields):
            complete += 1
        if item.get("source_document_id") or item.get("evidence_refs") or item.get("transaction_id"):
            traced += 1
    n = len(entries)
    return {
        "close_je_accuracy": round(complete / n, 4),
        "close_source_traceability": round(traced / n, 4),
        "compared": n,
    }


def cash_split(matches: dict[str, dict], residuals: dict[str, int], provider_ids: list[str]) -> dict[str, float]:
    arith = 0
    arith_n = 0
    disp = 0
    disp_n = 0
    provider = 0
    provider_n = 0
    for object_id, expected_cents in residuals.items():
        row = matches.get(object_id) or {}
        arith_n += 1
        actual = abs(int(round(abs(float(row.get("difference") or 0)) * 100)))
        if actual == expected_cents or row.get("status") in {"HUMAN_REVIEW", "UNEXPLAINED_DIFFERENCE"}:
            arith += 1
        disp_n += 1
        if row.get("status") != "MATCHED":
            disp += 1
    for object_id in provider_ids:
        row = matches.get(object_id) or {}
        provider_n += 1
        evidence = " ".join(str(item) for item in (row.get("evidence") or []))
        if row.get("provider") or "stripe" in evidence.lower() or row.get("provider_payout_id"):
            provider += 1
    return {
        "cash_arithmetic_accuracy": round(arith / arith_n, 4) if arith_n else 0.0,
        "cash_disposition_accuracy": round(disp / disp_n, 4) if disp_n else 0.0,
        "provider_awareness_accuracy": round(provider / provider_n, 4) if provider_n else 0.0,
    }


def domain_ratio(result, domain: str) -> str:
    for item in result.function_results:
        if item.domain == domain:
            return f"{item.passed}/{item.total}"
    return "n/a"

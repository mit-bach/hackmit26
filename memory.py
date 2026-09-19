from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from models import Precedent
from tools import _normalize_vendor

MEMORY_PATH = Path(__file__).resolve().parent / "data" / "precedents.json"
MIN_SIMILARITY = 0.7


def issue_types_from_checks(checks: dict) -> list[str]:
    types: list[str] = []
    if checks.get("duplicate_detected"):
        types.append("duplicate")
    if not checks.get("po_exists"):
        types.append("missing_po")
    elif not checks.get("po_is_approved"):
        types.append("po_not_approved")
    if checks.get("receipt_status") in {"missing", "not_received"}:
        types.append("goods_not_received")
    if checks.get("receipt_status") == "partial":
        types.append("partial_receipt")
    if checks.get("po_exists") and not checks.get("vendors_match_exactly"):
        types.append("vendor_mismatch")
    if checks.get("amount_discrepancy_class") == "small_discrepancy":
        types.append("small_amount_discrepancy")
    if checks.get("amount_discrepancy_class") == "material_mismatch":
        types.append("material_amount_mismatch")
    return types or ["other"]


def situation_from_checks(invoice_id: str, checks: dict) -> dict:
    return {
        "invoice_id": invoice_id,
        "issue_types": issue_types_from_checks(checks),
        "invoice_vendor": checks.get("invoice_vendor"),
        "po_vendor": checks.get("po_vendor"),
        "amount_difference": checks.get("amount_difference"),
        "percent_difference": checks.get("percent_difference"),
        "amount_discrepancy_class": checks.get("amount_discrepancy_class"),
        "receipt_status": checks.get("receipt_status"),
        "vendor_invoice_number": checks.get("vendor_invoice_number"),
        "po_exists": checks.get("po_exists"),
        "po_is_approved": checks.get("po_is_approved"),
        "duplicate_detected": checks.get("duplicate_detected"),
        "vendors_match_exactly": checks.get("vendors_match_exactly"),
        "vendors_are_similar": checks.get("vendors_are_similar"),
    }


def load_precedents() -> list[Precedent]:
    if not MEMORY_PATH.exists():
        return []
    raw = json.loads(MEMORY_PATH.read_text())
    if not isinstance(raw, list):
        return []
    return [Precedent.model_validate(item) for item in raw]


def _write_precedents(items: list[Precedent]) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = [item.model_dump() for item in items]
    MEMORY_PATH.write_text(json.dumps(payload, indent=2) + "\n")


def save_correction(
    invoice_id: str,
    corrected_decision: str,
    note: str,
    checks: dict,
) -> Precedent:
    items = load_precedents()
    next_id = f"PRE-{len(items) + 1:03d}"
    record = Precedent(
        id=next_id,
        invoice_id=invoice_id,
        corrected_decision=corrected_decision,  # type: ignore[arg-type]
        note=note.strip(),
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        situation=situation_from_checks(invoice_id, checks),
    )
    items.append(record)
    _write_precedents(items)
    return record


def _vendor_pair(checks_or_situation: dict) -> tuple[str, str]:
    return (
        _normalize_vendor(checks_or_situation.get("invoice_vendor") or ""),
        _normalize_vendor(checks_or_situation.get("po_vendor") or ""),
    )


def score_precedent(invoice_id: str, checks: dict, stored: Precedent) -> tuple[float, str]:
    sit = stored.situation
    if stored.invoice_id == invoice_id:
        return 1.0, f"human correction of the same invoice {invoice_id}"

    current_issues = set(issue_types_from_checks(checks))
    stored_issues = set(sit.get("issue_types") or [])
    overlap = current_issues & stored_issues
    if not overlap:
        return 0.0, "no overlapping exception type"

    if "duplicate" in overlap:
        if checks.get("vendor_invoice_number") and checks.get("vendor_invoice_number") == sit.get(
            "vendor_invoice_number"
        ):
            return 0.95, "same vendor invoice number was previously treated as a duplicate"
        return 0.0, "duplicate precedent does not apply to a different invoice number"

    if "vendor_mismatch" in overlap:
        if _vendor_pair(checks) == _vendor_pair(sit) and _vendor_pair(checks) != ("", ""):
            return 0.95, "same vendor-name mismatch pattern"
        current_left, current_right = _vendor_pair(checks)
        stored_left, stored_right = _vendor_pair(sit)
        if current_left and stored_left and (
            current_left == stored_left or current_right == stored_right
        ):
            return 0.8, "related vendor-name mismatch"
        return 0.0, "vendor mismatch precedent is for a different vendor pair"

    if "small_amount_discrepancy" in overlap:
        if checks.get("invoice_vendor") and checks.get("invoice_vendor") == sit.get("invoice_vendor"):
            return 0.9, "same vendor had a small amount discrepancy accepted or rejected before"
        return 0.8, "similar small amount discrepancy"

    if overlap & {
        "missing_po",
        "goods_not_received",
        "partial_receipt",
        "po_not_approved",
        "material_amount_mismatch",
    }:
        if checks.get("invoice_vendor") == sit.get("invoice_vendor"):
            issue = sorted(overlap)[0]
            return 0.85, f"same vendor previously had a {issue} correction"
        return 0.0, "blocking-exception precedent does not generalize across vendors"

    return 0.0, "not similar enough"


def find_similar_precedents(invoice_id: str, checks: dict) -> list[dict]:
    matches: list[dict] = []
    for stored in load_precedents():
        score, why = score_precedent(invoice_id, checks, stored)
        if score < MIN_SIMILARITY:
            continue
        matches.append(
            {
                "precedent_id": stored.id,
                "source_invoice_id": stored.invoice_id,
                "corrected_decision": stored.corrected_decision,
                "note": stored.note,
                "issue_types": stored.situation.get("issue_types"),
                "similarity": round(score, 2),
                "why_similar": why,
            }
        )
    matches.sort(key=lambda item: item["similarity"], reverse=True)
    return matches

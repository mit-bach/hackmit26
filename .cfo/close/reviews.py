"""Persisted month-end review queue. Dedupes by period + workflow + source case."""

from __future__ import annotations

import json
from pathlib import Path

from close.dates import now_iso
from close.models import BLOCKING_REVIEW_STATUSES, ReviewItem

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "runs" / "month_end"
REVIEWS_PATH = STATE_DIR / "reviews.json"

CASH_CHAIN = ["cash", "bs_recon", "exceptions", "final_review", "mark_closed"]
AR_CHAIN = ["ar", "bs_recon", "exceptions", "final_review", "mark_closed"]
PREPAID_CHAIN = ["prepaid", "bs_recon", "exceptions", "final_review", "mark_closed"]


def configure_paths(directory: Path) -> None:
    global STATE_DIR, REVIEWS_PATH
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    STATE_DIR = directory
    REVIEWS_PATH = directory / "reviews.json"


def reset_reviews() -> None:
    REVIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    REVIEWS_PATH.write_text("[]\n")


def load_reviews(period: str = "") -> list[ReviewItem]:
    if not REVIEWS_PATH.exists():
        return []
    raw = json.loads(REVIEWS_PATH.read_text())
    items = [ReviewItem.model_validate(item) for item in raw]
    if period:
        items = [item for item in items if item.period == period]
    return items


def save_reviews(rows: list[ReviewItem]) -> None:
    REVIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    REVIEWS_PATH.write_text(json.dumps([item.model_dump() for item in rows], indent=2) + "\n")


def get_review(review_id: str) -> ReviewItem | None:
    for item in load_reviews():
        if item.review_id == review_id:
            return item
    return None


def upsert_review(item: ReviewItem) -> ReviewItem:
    rows = load_reviews()
    for index, existing in enumerate(rows):
        if existing.review_id == item.review_id or (
            existing.period == item.period
            and existing.source_workflow == item.source_workflow
            and existing.source_case_id == item.source_case_id
        ):
            rows[index] = item
            save_reviews(rows)
            return item
    rows.append(item)
    save_reviews(rows)
    return item


def find_review(period: str, source_workflow: str, source_case_id: str) -> ReviewItem | None:
    for item in load_reviews(period):
        if item.source_workflow == source_workflow and item.source_case_id == source_case_id:
            return item
    return None


def blocking_reviews(period: str) -> list[ReviewItem]:
    return [item for item in load_reviews(period) if item.status in BLOCKING_REVIEW_STATUSES]


def review_id_for(period: str, source_workflow: str, source_case_id: str) -> str:
    token = source_case_id.replace("_", "-").upper()
    return f"REV-{period}-{source_workflow.upper()}-{token}"


def enqueue_review(
    *,
    period: str,
    source_workflow: str,
    source_case_id: str,
    issue_type: str,
    description: str,
    amount: float | None = None,
    evidence_refs: list[str] | None = None,
    proposed_resolution: str = "",
    assigned_role: str = "",
    downstream_tasks_affected: list[str] | None = None,
) -> ReviewItem:
    existing = find_review(period, source_workflow, source_case_id)
    if existing is not None:
        if existing.status == "RESOLVED":
            return existing
        updated = existing.model_copy(
            update={
                "description": description,
                "amount": amount if amount is not None else existing.amount,
                "evidence_refs": list(evidence_refs or existing.evidence_refs),
                "proposed_resolution": proposed_resolution or existing.proposed_resolution,
            }
        )
        return upsert_review(updated)
    item = ReviewItem(
        review_id=review_id_for(period, source_workflow, source_case_id),
        period=period,
        source_workflow=source_workflow,
        source_case_id=source_case_id,
        issue_type=issue_type,
        description=description,
        amount=amount,
        evidence_refs=list(evidence_refs or []),
        proposed_resolution=proposed_resolution,
        status="OPEN",
        assigned_role=assigned_role,
        downstream_tasks_affected=list(downstream_tasks_affected or []),
    )
    return upsert_review(item)


def harvest_review_items(period: str, *, scenario: str = "demo") -> list[ReviewItem]:
    """Create missing review items from live source objects. Never duplicates."""
    if scenario == "clean":
        return load_reviews(period)
    _harvest_cash(period)
    if scenario == "demo":
        _harvest_ar(period)
        _harvest_prepaid(period)
    return load_reviews(period)


def _harvest_cash(period: str) -> None:
    from cash_recon.store import get_report

    report = get_report(period)
    if report is None:
        return
    for match in report.matches:
        if match.match_type != "UNEXPLAINED_DIFFERENCE":
            continue
        amount = abs(float(match.difference or report.unexplained_difference or 0))
        enqueue_review(
            period=period,
            source_workflow="cash",
            source_case_id=match.bank_transaction_ids[0] if match.bank_transaction_ids else match.reconciliation_id,
            issue_type="unexplained_cash_difference",
            description=f"Cash: ${amount:,.2f} unexplained difference",
            amount=amount,
            evidence_refs=list(match.evidence or match.bank_transaction_ids or []),
            proposed_resolution=(
                "Classify the difference as a reconciling item with evidence, "
                "or post an approved correcting cash entry."
            ),
            assigned_role="Cash Reconciliation Reviewer",
            downstream_tasks_affected=list(CASH_CHAIN),
        )


def _harvest_ar(period: str) -> None:
    from ar.store import get_payment

    payment = get_payment("PAY-CLOSE-4500")
    if payment is None:
        return
    unmatched = payment.application_status in {"UNMATCHED", "HUMAN_REVIEW"} and payment.unapplied_amount > 0
    if not unmatched:
        return
    enqueue_review(
        period=period,
        source_workflow="ar",
        source_case_id=payment.payment_id,
        issue_type="unmatched_customer_payment",
        description="AR: $4,500 unmatched customer payment",
        amount=float(payment.unapplied_amount or payment.amount),
        evidence_refs=[payment.payment_id, payment.bank_reference],
        proposed_resolution="Associate PAY-CLOSE-4500 with the correct customer invoice(s) and apply cash.",
        assigned_role="Cash Application Reviewer",
        downstream_tasks_affected=list(AR_CHAIN),
    )


def _harvest_prepaid(period: str) -> None:
    from prepaid.store import get_item

    item = get_item("PRE-INS-MISSING")
    if item is None:
        return
    if item.evidence_refs and item.source_document_id:
        return
    enqueue_review(
        period=period,
        source_workflow="prepaid",
        source_case_id=item.prepaid_id,
        issue_type="missing_prepaid_evidence",
        description="Prepaids: missing insurance policy evidence",
        amount=float(item.total_amount),
        evidence_refs=list(item.evidence_refs),
        proposed_resolution="Attach the Northshore flood policy packet (DOC-NS-FLOOD-2026) to PRE-INS-MISSING.",
        assigned_role="Prepaid Reviewer",
        downstream_tasks_affected=list(PREPAID_CHAIN),
    )


def apply_review_views(state) -> None:
    """Keep checklist exception lists aligned with the persisted queue."""
    rows = load_reviews(state.period.period)
    state.review_ids = [item.review_id for item in rows]
    blocking = [item for item in rows if item.status in BLOCKING_REVIEW_STATUSES]
    state.human_review_items = [item.description for item in blocking]
    kept = [item for item in state.exceptions if item.kind not in {"cash_unexplained", "prepaid_evidence", "bs_recon"}]
    from close.models import CloseException

    for item in blocking:
        kind = {
            "cash": "cash_unexplained",
            "ar": "bs_recon",
            "prepaid": "prepaid_evidence",
        }.get(item.source_workflow, "bs_recon")
        kept.append(CloseException(kind=kind, ref=item.source_case_id, detail=item.description))
    state.exceptions = kept
    state.resolutions = []
    from close.models import ReviewResolution

    for item in rows:
        if item.status != "RESOLVED":
            continue
        state.resolutions.append(
            ReviewResolution(
                resolution_id=f"RES-{item.review_id}",
                item_id=item.source_case_id,
                period=item.period,
                resolution=item.decision_reason or item.resolution_action,
                reviewer=item.reviewer or "human",
                created_at=item.decided_at or now_iso(),
                original_status="OPEN",
                original_detail=item.description,
            )
        )

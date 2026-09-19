"""Post prepaid amortization. Arithmetic and controls stay in Python."""

from __future__ import annotations

from close.context import remember_link
from close.dates import money, period_from_date
from close.ledger import find_by_key, post_entry
from prepaid.models import PrepaidItem, PrepaidScheduleLine
from prepaid.schedule import generate_schedule, validate_prepaid
from prepaid.store import get_item, lines_for, upsert_item, upsert_line


def _posted_line(item: PrepaidItem, period: str) -> PrepaidScheduleLine | None:
    for line in lines_for(item.prepaid_id):
        if line.period == period and line.status == "posted":
            return line
    return None


def post_schedule_line(
    item: PrepaidItem,
    line: PrepaidScheduleLine,
    *,
    close_period: str,
    evidence_refs: list[str] | None = None,
) -> PrepaidScheduleLine:
    validate_prepaid(item)
    evidence = list(evidence_refs or item.evidence_refs or line.evidence_refs)
    if not evidence or not item.source_document_id:
        raise ValueError("Missing evidence: amortization cannot be posted without a source document.")
    start_period = period_from_date(item.start_date)
    end_period = period_from_date(item.end_date)
    if line.period < start_period:
        raise ValueError("Amortization before the service start date is not allowed.")
    if line.period > end_period:
        raise ValueError("Amortization after the service end date is not allowed.")
    existing = _posted_line(item, line.period)
    if existing:
        return existing
    posted_amount = money(sum(row.amount for row in lines_for(item.prepaid_id, status="posted")))
    if money(posted_amount + line.amount) - 0.001 > money(item.total_amount):
        raise ValueError("Over-amortization: cumulative amortization may not exceed original prepaid cost.")
    key = f"prepaid:{item.prepaid_id}:{line.period}"
    already = find_by_key(key)
    if already:
        posted = line.model_copy(
            update={
                "status": "posted",
                "journal_entry_id": already["entry_id"],
                "evidence_refs": evidence,
                "posted_in_period": close_period,
            }
        )
        return upsert_line(posted)
    journal = post_entry(
        period=close_period,
        memo=f"Amortize {item.prepaid_id} {item.description} for {line.period}",
        debit_account=item.expense_account,
        credit_account=item.initial_account,
        amount=line.amount,
        entry_type="prepaid_amortization",
        idempotency_key=key,
        source_document_id=item.source_document_id,
        transaction_id=item.transaction_id or item.prepaid_id,
        evidence_refs=evidence,
        related_ids={"prepaid_id": item.prepaid_id, "service_period": line.period},
    )
    posted = line.model_copy(
        update={
            "status": "posted",
            "journal_entry_id": journal["entry_id"],
            "evidence_refs": evidence,
            "posted_in_period": close_period,
        }
    )
    upsert_line(posted)
    remember_link(
        source_document_id=item.source_document_id,
        transaction_id=item.transaction_id or item.prepaid_id,
        journal_entry_id=journal["entry_id"],
        account_id=item.expense_account,
        extra={"prepaid_id": item.prepaid_id, "service_period": line.period},
    )
    return posted


def amortize_item(
    prepaid_id: str,
    close_period: str,
    *,
    method: str | None = None,
    through_period: str | None = None,
) -> list[PrepaidScheduleLine]:
    item = get_item(prepaid_id)
    if item is None:
        raise ValueError(f"Unknown prepaid {prepaid_id}")
    chosen = method or item.amortization_method
    schedule = generate_schedule(item, chosen)
    cutoff = through_period or close_period
    posted: list[PrepaidScheduleLine] = []
    for line in schedule:
        if line.period > cutoff:
            upsert_line(line)
            continue
        if line.period < close_period and not item.late_discovery:
            historical = line.model_copy(
                update={"status": "posted", "posted_in_period": line.period, "journal_entry_id": None}
            )
            existing = _posted_line(item, line.period)
            upsert_line(existing or historical)
            continue
        posted.append(post_schedule_line(item, line, close_period=close_period))
    remaining = money(item.total_amount - sum(row.amount for row in posted))
    status = "fully_amortized" if remaining == 0 else item.status
    upsert_item(item.model_copy(update={"amortization_method": chosen, "status": status}))
    return posted


def remaining_by_account() -> dict[str, float]:
    from prepaid.store import load_items, load_schedule

    totals: dict[str, float] = {}
    posted = {(line.prepaid_id, line.period) for line in load_schedule() if line.status == "posted"}
    for item in load_items():
        if not item.start_date or not item.end_date:
            continue
        schedule = generate_schedule(item, item.amortization_method)
        leftover = money(sum(line.amount for line in schedule if (item.prepaid_id, line.period) not in posted))
        totals[item.initial_account] = money(totals.get(item.initial_account, 0) + leftover)
    return totals

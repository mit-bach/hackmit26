"""English explanations for finance decisions. JSON stays internal."""

from __future__ import annotations

from typing import Any


def money(value: float | int | None) -> str:
    if value is None:
        return "an unknown amount"
    return f"${float(value):,.2f}"


def join_ids(ids: list[str] | tuple[str, ...] | None) -> str:
    rows = [str(item) for item in (ids or []) if item]
    if not rows:
        return "no linked records"
    if len(rows) == 1:
        return rows[0]
    if len(rows) == 2:
        return f"{rows[0]} and {rows[1]}"
    return ", ".join(rows[:-1]) + f", and {rows[-1]}"


def label_record(record_id: str, *, vendor: str | None = None, description: str | None = None) -> str:
    name = (vendor or description or "").strip()
    if name and record_id:
        return f"{name} ({record_id})"
    return name or record_id or "an unnamed record"


def explain_decision(
    *,
    happened: str,
    selected: list[str] | None = None,
    rejected: list[str] | None = None,
    why: str,
    books_change: str | None = None,
    other_workflows: list[str] | None = None,
    prior: str | None = None,
    uncertainty: str | None = None,
) -> dict[str, Any]:
    paragraphs = [happened.strip()]
    if selected:
        paragraphs.append("Records that mattered: " + join_ids(selected) + ".")
    if rejected:
        paragraphs.append("Records that were not treated as valid evidence: " + join_ids(rejected) + ".")
    paragraphs.append(why.strip())
    if books_change:
        paragraphs.append(books_change.strip())
    if other_workflows:
        paragraphs.append("Elsewhere in the office: " + " ".join(item.rstrip(".") + "." for item in other_workflows))
    if prior:
        paragraphs.append(prior.strip())
    if uncertainty:
        paragraphs.append("Remaining uncertainty: " + uncertainty.strip().rstrip(".") + ".")
    narrative = " ".join(paragraphs)
    return {
        "what_happened": happened,
        "records_that_mattered": list(selected or []),
        "records_rejected": list(rejected or []),
        "why": why,
        "books_change": books_change,
        "other_workflows": list(other_workflows or []),
        "prior_decision": prior,
        "uncertainty": uncertainty,
        "narrative": narrative,
    }


def explain_ap(invoice_id: str, vendor: str, decision: str, exceptions: list[str], *, amount: float | None = None) -> dict[str, Any]:
    if decision == "HOLD" and "duplicate" in exceptions:
        return explain_decision(
            happened=f"Maximor received a bill from {label_record(invoice_id, vendor=vendor)} for {money(amount)}.",
            selected=[invoice_id],
            rejected=[invoice_id],
            why="The same vendor invoice number is already on the books, so this copy is a duplicate rather than a new payable.",
            books_change="No new accounts-payable balance was created.",
            other_workflows=[
                "The payment queue will not include this copy.",
                "The cash forecast will not treat it as a new outflow.",
                "Month-end close will not add a second payable.",
            ],
        )
    if decision == "HOLD":
        return explain_decision(
            happened=f"Maximor reviewed {label_record(invoice_id, vendor=vendor)} for {money(amount)} and did not approve it.",
            selected=[invoice_id],
            why="The three-way match or policy checks found " + join_ids(exceptions) + ".",
            books_change="The invoice stays on hold and is not scheduled for payment.",
        )
    return explain_decision(
        happened=f"Maximor approved {label_record(invoice_id, vendor=vendor)} for {money(amount)}.",
        selected=[invoice_id],
        why="Purchase order, receiving, and invoice amounts agree, and no blocking exception remains.",
        books_change="The invoice may enter the weekly payment pool unless it is already paid.",
    )


def explain_cash(match) -> dict[str, Any]:
    bank_ids = list(getattr(match, "bank_transaction_ids", None) or [])
    ledger_ids = list(getattr(match, "ledger_entry_ids", None) or [])
    status = getattr(match, "status", "")
    match_type = getattr(match, "match_type", "")
    if match_type == "PROVIDER_PAYOUT":
        why = "The bank deposit is the Stripe or Adyen payout net of fees, refunds, and chargebacks — not a single customer invoice."
    elif match_type == "GROUPED_MATCH":
        why = "One bank payment settled several ledger items from the same counterparty."
    elif match_type == "FEE_NETTED":
        why = "The bank amount is the ledger amount minus a documented bank fee."
    elif match_type == "UNEXPLAINED_DIFFERENCE":
        why = "The amounts are close, but Maximor does not have evidence that the leftover is a fee, timing item, or valid match."
    elif status in {"HUMAN_REVIEW", "UNMATCHED"}:
        why = "The available records do not uniquely identify a valid economic relationship."
    else:
        why = "Bank and ledger amounts, dates, and counterparties support the same cash event."
    return explain_decision(
        happened=f"Cash reconciliation classified this activity as {match_type or status}.",
        selected=bank_ids + ledger_ids,
        why=why,
        books_change="Source bank and ledger rows were not rewritten to force a tie.",
    )


def explain_accrual_correction(
    vendor: str,
    period: str,
    estimated: float,
    actual: float,
    invoice_id: str,
    prior_id: str | None = None,
) -> dict[str, Any]:
    error = round(actual - estimated, 2)
    direction = "higher" if error > 0 else "lower"
    return explain_decision(
        happened=(
            f"In {period}, the actual {vendor} bill {invoice_id} arrived at {money(actual)}. "
            f"The earlier estimate was {money(estimated)}."
        ),
        selected=[invoice_id] + ([prior_id] if prior_id else []),
        why=(
            f"The estimate was {money(abs(error))} {direction} than the invoice. "
            "Current evidence replaces the prior estimate; memory is precedent, not an override."
        ),
        books_change=(
            f"The open accrual is reversed and the actual invoice is booked. "
            f"The estimation difference of {money(error)} is retained in the history."
        ),
        other_workflows=[
            "Close, reporting, and audit keep the reversal and the actual bill as linked evidence.",
        ],
        prior=f"Prior decision {prior_id} is kept as history." if prior_id else None,
    )

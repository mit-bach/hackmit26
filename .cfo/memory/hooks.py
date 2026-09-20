"""Workflow adapters. Keep arithmetic in existing domain modules."""

from __future__ import annotations

from memory.format import PRECEDENT_INSTRUCTION
from memory.models import MemoryEvidence, MemoryLookup, MemoryQuery
from memory.retrieve import lookup_memories
from memory.write import (
    is_reusable_ap_decision,
    is_reusable_cash_decision,
    is_reusable_prepaid_decision,
    write_decision,
)

STANDARD_CASH_HYPOTHESES = [
    "fee",
    "rounding",
    "foreign_exchange",
    "partial_payment",
    "duplicate_or_missing",
    "timing_difference",
]


def cash_query(candidate, period: str) -> MemoryQuery:
    provider = (getattr(candidate, "provider", None) or "").lower() or None
    situation = "payout_difference" if provider else (getattr(candidate, "match_type", "") or "").lower()
    tags = ["cash_reconciliation"]
    if provider:
        tags.append(provider)
    if getattr(candidate, "match_type", None):
        tags.append(str(candidate.match_type).lower())
    return MemoryQuery(
        workflow="cash_reconciliation",
        entity_type="payment_provider" if provider else None,
        entity_id=provider,
        situation_type=situation if provider else None,
        tags=tags,
        prior_to_period=period,
        exclude_period=period,
        limit=5,
    )


def lookup_for_cash(candidate, period: str) -> MemoryLookup:
    return lookup_memories(cash_query(candidate, period))


def stripe_explains_difference(candidate) -> bool:
    evidence = [str(item) for item in getattr(candidate, "evidence", [])]
    blob = " ".join(evidence).lower()
    has_fee = "stripe_fee:" in blob or "processor_fee:" in blob or "fees:" in blob
    has_cb = "chargeback:" in blob or "chargebacks:" in blob
    explained = "reductions_equal_difference" in blob or "processor_reductions:" in blob
    if getattr(candidate, "match_type", None) == "FEE_NETTED" and getattr(candidate, "provider", None) == "stripe":
        return True
    return explained and (has_fee or has_cb)


def apply_cash_investigation(candidate, investigation, lookup: MemoryLookup):
    """Annotate a Python investigation with prior-period influence.

    Memory never changes amounts. It only changes which hypotheses are
    walked first and whether a prior treatment is reused after evidence check.
    """
    explained = stripe_explains_difference(candidate)
    findings = list(investigation.findings)
    issues = list(investigation.issues_investigated)
    unsupported = list(investigation.unsupported_hypotheses)
    supported = list(investigation.supported_explanations)
    lookup.current_evidence_checked = True
    lookup.decision = investigation.recommendation

    def _count(note) -> int:
        return len(note.issues_investigated) + len(note.unsupported_hypotheses)

    if not lookup.memory_enabled or not lookup.precedents:
        walked = list(dict.fromkeys(issues + STANDARD_CASH_HYPOTHESES))
        still_open = [] if explained else [item for item in STANDARD_CASH_HYPOTHESES if item not in supported]
        findings = findings + [
            "Checked fee, rounding, FX, partial payment, duplicate/missing entry, and timing against current evidence."
        ]
        investigation = investigation.model_copy(
            update={
                "issues_investigated": walked,
                "unsupported_hypotheses": still_open,
                "findings": findings,
            }
        )
        lookup.precedent_used = False
        lookup.investigation_steps = _count(investigation)
        return investigation, lookup

    top = lookup.precedents[0]
    lookup.precedent_relevance = top.reusable_precedent
    entity_match = (getattr(candidate, "provider", "") or "").lower() == (top.entity_id or "").lower()

    if entity_match and explained:
        lookup.precedent_used = True
        lookup.evidence_supports_precedent = True
        lookup.decision = "reconcile payout net of fees and chargebacks"
        lookup.skipped_hypotheses = [item for item in STANDARD_CASH_HYPOTHESES if item != "fee"]
        focused_issues = ["prior_precedent", "stripe_fees_and_chargebacks"]
        focused_findings = [
            f"Retrieved {top.decision_id} from {top.period}.",
            top.reusable_precedent,
            "Current Stripe fees and chargebacks equal the bank versus ledger difference.",
            PRECEDENT_INSTRUCTION,
        ]
        investigation = investigation.model_copy(
            update={
                "issues_investigated": focused_issues,
                "findings": focused_findings,
                "supported_explanations": list(dict.fromkeys(supported + [candidate.match_type, "processor_net_payout"])),
                "unsupported_hypotheses": [],
                "evidence_used": list(dict.fromkeys(list(investigation.evidence_used) + [top.decision_id])),
            }
        )
        lookup.investigation_steps = _count(investigation)
        return investigation, lookup

    lookup.precedent_used = False
    lookup.evidence_supports_precedent = False
    lookup.deviation = (
        f"{top.decision_id} was retrieved but current evidence does not support "
        f"the same {top.accounting_treatment} treatment."
    )
    extra = [
        f"Retrieved {top.decision_id} from {top.period}.",
        lookup.deviation,
        PRECEDENT_INSTRUCTION,
    ]
    investigation = investigation.model_copy(
        update={
            "issues_investigated": list(dict.fromkeys(["prior_precedent"] + issues)),
            "findings": extra + findings,
            "unsupported_hypotheses": unsupported,
        }
    )
    lookup.investigation_steps = _count(investigation)
    return investigation, lookup


def write_cash_memory(match, trace) -> tuple | None:
    if not is_reusable_cash_decision(
        match_type=match.match_type,
        provider=match.provider,
        status=match.status,
        replay=getattr(trace, "replay", False),
    ):
        return None
    provider = (match.provider or "processor").lower()
    evidence = [
        MemoryEvidence(kind="match_evidence", label=item)
        for item in list(match.evidence)[:12]
    ]
    if match.bank_amount:
        evidence.append(
            MemoryEvidence(
                kind="bank_deposit",
                label="bank_deposit",
                amount=match.bank_amount,
                amount_minor=match.bank_amount_minor,
            )
        )
    if match.ledger_amount:
        evidence.append(
            MemoryEvidence(
                kind="ledger_entry",
                label="ledger_gross_or_net",
                amount=match.ledger_amount,
                amount_minor=match.ledger_amount_minor,
            )
        )
    if match.difference:
        evidence.append(
            MemoryEvidence(
                kind="difference",
                label="payout_difference",
                amount=match.difference,
                amount_minor=match.difference_minor,
            )
        )
    fingerprint = "|".join(
        [
            match.provider_payout_id or match.match_key or match.reconciliation_id,
            match.match_type,
            str(match.bank_amount_minor),
            str(match.ledger_amount_minor),
            str(match.difference_minor),
        ]
    )
    return write_decision(
        period=match.period,
        workflow="cash_reconciliation",
        entity_type="payment_provider",
        entity_id=provider,
        situation_type="payout_difference",
        situation_summary=(
            f"{provider.title()} payout was lower than gross receipts; "
            f"difference {abs(match.difference):.2f} matched processor reductions."
        ),
        evidence=evidence,
        decision="reconcile payout net of fees and chargebacks",
        reasoning_summary=(
            "Bank deposit equals the processor net. Gross receipts minus fees, "
            "chargebacks, and refunds explain the difference exactly."
        ),
        accounting_treatment="net_payout_fees_and_chargebacks",
        outcome=match.status,
        reusable_precedent=(
            f"{provider.title()} payouts may arrive net of processing fees and chargebacks"
        ),
        source_trace_ids=[match.reconciliation_id],
        tags=["stripe", "payout_difference", "fees", "chargebacks", "cash_reconciliation"]
        if provider == "stripe"
        else [provider, "payout_difference", "cash_reconciliation"],
        fingerprint=fingerprint,
        entity_name=provider.title(),
        accounting_category="cash",
    )


def prepaid_query(item, period: str) -> MemoryQuery:
    vendor = (getattr(item, "vendor", "") or "").strip()
    return MemoryQuery(
        workflow="prepaid",
        entity_type="vendor",
        entity_id=vendor.lower(),
        situation_type="prepaid_treatment",
        tags=["prepaid", vendor.lower()],
        accounting_category="prepaid_expense",
        prior_to_period=period,
        exclude_period=period,
        limit=5,
    )


def lookup_for_prepaid(item, period: str) -> MemoryLookup:
    return lookup_memories(prepaid_query(item, period))


def apply_prepaid_precedent(item, selected_method: str, lookup: MemoryLookup) -> MemoryLookup:
    lookup.current_evidence_checked = True
    lookup.decision = selected_method
    if not lookup.memory_enabled or not lookup.precedents:
        lookup.precedent_used = False
        return lookup
    top = lookup.precedents[0]
    lookup.precedent_relevance = top.reusable_precedent
    same_vendor = (getattr(item, "vendor", "") or "").lower() == (top.entity_id or "").lower()
    if same_vendor and selected_method == top.accounting_treatment:
        lookup.precedent_used = True
        lookup.evidence_supports_precedent = True
        return lookup
    lookup.precedent_used = False
    lookup.evidence_supports_precedent = False
    if same_vendor:
        lookup.deviation = (
            f"{top.decision_id} treated {top.entity_id} as {top.accounting_treatment}; "
            f"current service-period evidence supports {selected_method}."
        )
    return lookup


def write_prepaid_memory(item, period: str, *, selected_method: str, reviewer_decision: str, trace_id: str):
    if not is_reusable_prepaid_decision(selected_method=selected_method, reviewer_decision=reviewer_decision):
        return None
    vendor = (item.vendor or "").strip()
    fingerprint = "|".join(
        [
            vendor.lower(),
            item.source_document_id or item.prepaid_id,
            selected_method,
            str(item.total_amount),
            item.start_date,
            item.end_date,
        ]
    )
    return write_decision(
        period=period,
        workflow="prepaid",
        entity_type="vendor",
        entity_id=vendor.lower(),
        situation_type="prepaid_treatment",
        situation_summary=(
            f"{vendor} invoice covering {item.start_date} to {item.end_date} "
            f"classified as {selected_method}."
        ),
        evidence=[
            MemoryEvidence(kind="prepaid_item", label=item.prepaid_id, amount=item.total_amount, reference=item.source_document_id),
            MemoryEvidence(kind="service_period", label=f"{item.start_date}:{item.end_date}"),
            *[MemoryEvidence(kind="document", label=ref) for ref in list(item.evidence_refs)[:6]],
        ],
        decision=selected_method,
        reasoning_summary=(
            f"Service period spans {item.start_date} through {item.end_date}. "
            f"Python selected {selected_method}."
        ),
        accounting_treatment=selected_method,
        outcome="amortized" if selected_method != "immediate_expense" else "expensed",
        reusable_precedent=(
            f"{vendor} multi-month software or service invoices are prepaid and amortized; "
            "confirm the current coverage dates before reusing the method."
        ),
        source_trace_ids=[trace_id],
        tags=["prepaid", vendor.lower(), selected_method],
        fingerprint=fingerprint,
        entity_name=vendor,
        accounting_category="prepaid_expense",
    )


def ap_query(evidence, period: str | None = None) -> MemoryQuery:
    invoice = getattr(evidence, "invoice", None)
    vendor = ""
    if invoice is not None:
        vendor = (getattr(invoice, "vendor", "") or "").strip()
    exceptions = list(getattr(evidence, "exception_types", []) or [])
    return MemoryQuery(
        workflow="accounts_payable",
        entity_type="vendor",
        entity_id=vendor.lower() or None,
        situation_type="vendor_invoice_pattern",
        tags=["accounts_payable", *exceptions],
        prior_to_period=period,
        exclude_period=period,
        limit=5,
    )


def lookup_for_ap(evidence, period: str | None = None) -> MemoryLookup:
    return lookup_memories(ap_query(evidence, period))


def write_ap_memory(evidence, final, *, period: str, trace_id: str):
    exceptions = list(getattr(evidence, "exception_types", []) or [])
    decision = getattr(final, "decision", "")
    if not is_reusable_ap_decision(exception_types=exceptions, decision=decision):
        return None
    invoice = getattr(evidence, "invoice", None)
    vendor = (getattr(invoice, "vendor", "") or "").strip() if invoice else ""
    invoice_id = getattr(final, "invoice_id", "") or getattr(evidence, "invoice_id", "")
    situation = "vendor_invoice_pattern"
    fingerprint = "|".join([vendor.lower(), invoice_id, decision, ",".join(sorted(exceptions))])
    return write_decision(
        period=period,
        workflow="accounts_payable",
        entity_type="vendor",
        entity_id=vendor.lower(),
        situation_type=situation,
        situation_summary=(
            f"{vendor or invoice_id} AP exception {', '.join(exceptions)} resolved as {decision}."
        ),
        evidence=[
            MemoryEvidence(kind="invoice", label=invoice_id, reference=vendor),
            *[MemoryEvidence(kind="exception", label=item) for item in exceptions],
        ],
        decision=decision,
        reasoning_summary=(getattr(final, "reasons", None) or ["Exception resolved from current evidence."])[0],
        accounting_treatment=decision.lower(),
        outcome=decision,
        reusable_precedent=(
            f"Prior {vendor or 'vendor'} exception {', '.join(exceptions)} was {decision}. "
            "Reuse only when current match facts support the same treatment."
        ),
        source_trace_ids=[trace_id],
        tags=["accounts_payable", *exceptions, vendor.lower()],
        fingerprint=fingerprint,
        entity_name=vendor or None,
        accounting_category="ap",
    )

"""Discoverable audit controls. Each control is deterministic Python."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from calendar import monthrange
from datetime import date
from typing import Any

from audit.models import (
    AccountingPeriod,
    AuditApproval,
    AuditInvoice,
    AuditJournalEntry,
    AuditPayment,
    AuditVendor,
    ControlException,
    ControlResult,
    ControlSpec,
    OperationalDecision,
    ReperformanceRecord,
)
from audit.policy import AuditPolicy, RoundNumberPolicy, SodRule
from invoice_ingestion.identity import canonical_invoice_key
from tools import (
    collect_case_evidence,
    has_duplicate_vendor_invoice_number,
    load_duplicate_invoices,
    load_invoice,
    normalize_vendor,
)


def fixture_invoice_key(invoice: AuditInvoice) -> str:
    """Collapse formatting the same way ingestion near-duplicate matching does."""
    vendor_key = normalize_vendor(invoice.vendor)
    number = (invoice.vendor_invoice_number or "").replace("-", "").replace(" ", "").upper()
    if vendor_key and number:
        return f"{vendor_key}:{number}"
    return canonical_invoice_key(vendor=invoice.vendor, vendor_invoice_number=invoice.vendor_invoice_number) or (
        invoice.vendor_invoice_number or invoice.invoice_id
    )

ControlFn = Callable[..., ControlResult]

REGISTRY: dict[str, tuple[ControlSpec, ControlFn]] = {}


def register(spec: ControlSpec):
    def decorator(fn: ControlFn) -> ControlFn:
        REGISTRY[spec.control_id] = (spec, fn)
        return fn

    return decorator


def list_controls() -> list[ControlSpec]:
    return [spec for spec, _fn in REGISTRY.values()]


def get_control(control_id: str) -> tuple[ControlSpec, ControlFn]:
    if control_id not in REGISTRY:
        raise KeyError(f"Unknown control {control_id}")
    return REGISTRY[control_id]


def _result_of(exceptions: list[ControlException]) -> str:
    if any(item.result == "FAIL" for item in exceptions):
        return "FAIL"
    if any(item.result == "EXCEPTION" for item in exceptions):
        return "EXCEPTION"
    if any(item.result == "HUMAN_REVIEW" for item in exceptions):
        return "HUMAN_REVIEW"
    if any(item.result == "NOT_TESTED" for item in exceptions):
        return "NOT_TESTED"
    return "PASS"


def _base(spec: ControlSpec, audit_run_id: str, tested_ids: list[str], exceptions: list[ControlException], **kwargs) -> ControlResult:
    return ControlResult(
        control_id=spec.control_id,
        control_name=spec.control_name,
        control_description=spec.control_description,
        control_type=spec.control_type,
        population=spec.population,
        test_method=spec.test_method,
        policy_reference=spec.policy_reference,
        result=_result_of(exceptions),  # type: ignore[arg-type]
        evidence=list(kwargs.get("evidence") or []),
        exceptions=exceptions,
        tested_ids=tested_ids,
        audit_run_id=audit_run_id,
        facts=dict(kwargs.get("facts") or {}),
    )


def is_round_amount(amount: float, divisors: list[float]) -> list[float]:
    cents = int(round(float(amount) * 100))
    hits: list[float] = []
    for divisor in divisors:
        divisor_cents = int(round(float(divisor) * 100))
        if divisor_cents > 0 and cents % divisor_cents == 0:
            hits.append(float(divisor))
    return hits


def vendor_is_new(vendor: AuditVendor | None, payment_date: str, *, new_days: int = 90) -> bool:
    if vendor is None or not vendor.first_seen or not payment_date:
        return False
    try:
        first = date.fromisoformat(vendor.first_seen[:10])
        paid = date.fromisoformat(payment_date[:10])
    except ValueError:
        return False
    return (paid - first).days <= new_days


def classify_round_number(
    payment: AuditPayment,
    vendor: AuditVendor | None,
    hits: list[float],
    policy: RoundNumberPolicy,
) -> tuple[str, bool]:
    """Return (class, ordinary). Ordinary recurring SaaS is not treated as fraud."""
    if not hits:
        return "NOT_ROUND", False
    new_vendor = vendor_is_new(vendor, payment.payment_date) or bool(vendor and vendor.unusual)
    manual = payment.source == "manual"
    largest = max(hits)
    ordinary = (
        payment.recurring
        and payment.source == "automated"
        and payment.amount <= policy.ordinary_recurring_max
        and all(item in set(policy.ordinary_recurring_divisors) or item <= 100 for item in hits)
        and not new_vendor
        and not manual
    )
    if ordinary:
        return "ORDINARY_ROUND", True
    if policy.elevate_manual_new_vendor and manual and new_vendor and payment.amount >= policy.high_risk_min_amount:
        return "SUSPICIOUS_ROUND", False
    if largest >= 10000 or payment.amount >= policy.high_risk_min_amount:
        return "SUSPICIOUS_ROUND", False
    return "ROUND_CANDIDATE", False


@register(
    ControlSpec(
        control_id="AUD-RND-001",
        control_name="Round-number payments",
        control_description="Flag payments whose amount is divisible by a configured round-number divisor, then classify using vendor and source context.",
        control_type="preventive",
        population="payments",
        test_method="deterministic_threshold",
        policy_reference="AUD-RND",
    )
)
def run_round_number_payments(
    *,
    payments: list[AuditPayment],
    vendors: list[AuditVendor],
    policy: AuditPolicy,
    audit_run_id: str,
    sample_ids: list[str] | None = None,
) -> ControlResult:
    spec = REGISTRY["AUD-RND-001"][0]
    vendor_map = {item.vendor_id: item for item in vendors}
    wanted = set(sample_ids) if sample_ids is not None else {item.payment_id for item in payments}
    exceptions: list[ControlException] = []
    tested: list[str] = []
    for payment in payments:
        if payment.payment_id not in wanted:
            continue
        tested.append(payment.payment_id)
        if payment.amount < policy.round_number.min_amount:
            continue
        hits = is_round_amount(payment.amount, policy.round_number.divisors)
        vendor = vendor_map.get(payment.vendor_id)
        classification, ordinary = classify_round_number(payment, vendor, hits, policy.round_number)
        if classification == "NOT_ROUND":
            continue
        result = "PASS" if ordinary else "EXCEPTION"
        facts = {
            "payment_id": payment.payment_id,
            "amount": payment.amount,
            "round_number_divisors": hits,
            "vendor": payment.vendor_name,
            "vendor_id": payment.vendor_id,
            "vendor_first_seen": vendor.first_seen if vendor else None,
            "new_vendor": vendor_is_new(vendor, payment.payment_date),
            "payment_method": payment.payment_method,
            "manual": payment.source == "manual",
            "source": payment.source,
            "recurring": payment.recurring,
            "invoice_ids": list(payment.invoice_ids),
            "approval_ids": list(payment.approval_ids),
            "classification": classification,
            "ordinary": ordinary,
        }
        exceptions.append(
            ControlException(
                object_id=payment.payment_id,
                object_type="payment",
                result=result,  # type: ignore[arg-type]
                detail=(
                    f"{payment.payment_id} amount {payment.amount:.2f} is divisible by {hits} "
                    f"({classification})."
                ),
                facts=facts,
                evidence_ids=[payment.payment_id, *payment.invoice_ids, *payment.approval_ids],
                related_ids={
                    "payments": [payment.payment_id],
                    "invoices": list(payment.invoice_ids),
                    "vendors": [payment.vendor_id] if payment.vendor_id else [],
                    "approvals": list(payment.approval_ids),
                },
                monetary_exposure=payment.amount,
            )
        )
    return _base(spec, audit_run_id, tested, exceptions, facts={"divisors": policy.round_number.divisors})


@register(
    ControlSpec(
        control_id="AUD-SUP-001",
        control_name="Missing payment support",
        control_description="Flag payments whose source record marks supporting documents as missing.",
        control_type="detective",
        population="payments",
        test_method="deterministic_attribute",
        policy_reference="AUD-SUP",
    )
)
def run_missing_support_payments(
    *,
    payments: list[AuditPayment],
    audit_run_id: str,
    sample_ids: list[str] | None = None,
) -> ControlResult:
    spec = REGISTRY["AUD-SUP-001"][0]
    wanted = set(sample_ids) if sample_ids is not None else {item.payment_id for item in payments}
    exceptions: list[ControlException] = []
    tested: list[str] = []
    for payment in payments:
        if payment.payment_id not in wanted:
            continue
        tested.append(payment.payment_id)
        if not payment.missing_support:
            continue
        exceptions.append(
            ControlException(
                object_id=payment.payment_id,
                object_type="payment",
                result="FAIL",
                detail=f"{payment.payment_id} is marked missing_support in the payment record.",
                facts={"payment_id": payment.payment_id, "missing_support": True, "invoice_ids": list(payment.invoice_ids)},
                evidence_ids=[payment.payment_id, *payment.invoice_ids],
                related_ids={"payments": [payment.payment_id], "invoices": list(payment.invoice_ids)},
                monetary_exposure=payment.amount,
            )
        )
    return _base(spec, audit_run_id, tested, exceptions)


@register(
    ControlSpec(
        control_id="AUD-THR-001",
        control_name="Approval threshold violation",
        control_description="Independently re-test whether a PO's authorized amount exceeds the approver's documented limit.",
        control_type="detective",
        population="invoices",
        test_method="deterministic_threshold",
        policy_reference="AUD-THR",
    )
)
def run_approval_threshold_invoices(
    *,
    audit_invoices: list[AuditInvoice] | None = None,
    audit_run_id: str,
    sample_ids: list[str] | None = None,
) -> ControlResult:
    from tools import all_invoices, exception_types_for, load_invoice, load_purchase_order

    spec = REGISTRY["AUD-THR-001"][0]
    exceptions: list[ControlException] = []
    tested: list[str] = []
    population_ids = {item.invoice_id for item in (audit_invoices or [])}
    operational = {item.invoice_id: item for item in all_invoices()}
    invoice_ids = population_ids or set(operational)
    wanted = set(sample_ids) if sample_ids is not None else invoice_ids
    for invoice_id in sorted(invoice_ids):
        invoice = operational.get(invoice_id) or load_invoice(invoice_id)
        if invoice is None or invoice.invoice_id not in wanted:
            continue
        tested.append(invoice.invoice_id)
        types = exception_types_for(invoice.invoice_id)
        if "approval_limit_exceeded" not in types:
            continue
        purchase_order = load_purchase_order(invoice.po_id)
        exceptions.append(
            ControlException(
                object_id=invoice.invoice_id,
                object_type="invoice",
                result="FAIL",
                detail=(
                    f"{invoice.invoice_id} authorized amount exceeds the documented approval limit "
                    f"{getattr(purchase_order, 'approval_limit', None)}."
                ),
                facts={
                    "invoice_id": invoice.invoice_id,
                    "po_id": invoice.po_id,
                    "authorized_amount": getattr(purchase_order, "authorized_amount", None),
                    "approval_limit": getattr(purchase_order, "approval_limit", None),
                },
                evidence_ids=[invoice.invoice_id, invoice.po_id or ""],
                related_ids={
                    "invoices": [invoice.invoice_id],
                    "purchase_orders": [invoice.po_id] if invoice.po_id else [],
                },
                monetary_exposure=invoice.amount,
            )
        )
    return _base(spec, audit_run_id, tested, exceptions)


def _period_end_stamp(period: str) -> str:
    year, month = [int(part) for part in period.split("-")[:2]]
    last = monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-{last:02d}T23:59:59Z"


def classify_post_close(
    entry: AuditJournalEntry,
    period: AccountingPeriod,
) -> str:
    posted = entry.posting_timestamp or entry.posting_date
    if not posted:
        return "HUMAN_REVIEW"
    period_end = _period_end_stamp(period.period)
    after_month = posted[:10] > period_end[:10]
    after_lock = bool(period.close_timestamp) and posted > period.close_timestamp
    if after_month or after_lock:
        if entry.authorized and entry.authorization_id:
            return "AUTHORIZED_POST_CLOSE_ADJUSTMENT"
        if period.status != "CLOSED" and not period.close_timestamp:
            return "HUMAN_REVIEW"
        return "UNAUTHORIZED_POST_CLOSE_ENTRY"
    if period.status != "CLOSED" or not period.close_timestamp:
        return "HUMAN_REVIEW"
    return "PASS"


@register(
    ControlSpec(
        control_id="AUD-PCE-001",
        control_name="Post-close journal entries",
        control_description="Detect journal entries posted after the accounting period was closed. Authorization must be structured, not inferred from memo text.",
        control_type="detective",
        population="journal_entries",
        test_method="deterministic_cutoff",
        policy_reference="AUD-PCE",
    )
)
def run_post_close_entries(
    *,
    journals: list[AuditJournalEntry],
    period: AccountingPeriod,
    audit_run_id: str,
    sample_ids: list[str] | None = None,
) -> ControlResult:
    spec = REGISTRY["AUD-PCE-001"][0]
    wanted = set(sample_ids) if sample_ids is not None else {item.entry_id for item in journals}
    exceptions: list[ControlException] = []
    tested: list[str] = []
    for entry in journals:
        if entry.entry_id not in wanted:
            continue
        if entry.period != period.period:
            continue
        tested.append(entry.entry_id)
        classification = classify_post_close(entry, period)
        result = {
            "PASS": "PASS",
            "AUTHORIZED_POST_CLOSE_ADJUSTMENT": "PASS",
            "UNAUTHORIZED_POST_CLOSE_ENTRY": "FAIL",
            "HUMAN_REVIEW": "HUMAN_REVIEW",
        }[classification]
        if classification == "PASS":
            continue
        exceptions.append(
            ControlException(
                object_id=entry.entry_id,
                object_type="journal_entry",
                result=result,  # type: ignore[arg-type]
                detail=(
                    f"{entry.entry_id} posted {entry.posting_timestamp} vs close "
                    f"{period.close_timestamp or '(missing)'} → {classification}."
                ),
                facts={
                    "journal_entry_id": entry.entry_id,
                    "accounting_period": entry.period,
                    "close_timestamp": period.close_timestamp,
                    "close_status": period.status,
                    "posting_timestamp": entry.posting_timestamp,
                    "effective_date": entry.effective_date,
                    "poster": entry.poster_id,
                    "authorization_id": entry.authorization_id,
                    "authorized": entry.authorized,
                    "authorization_policy": entry.authorization_policy,
                    "reason": entry.memo,
                    "classification": classification,
                    "linked_source_records": list(entry.related_source_ids),
                },
                evidence_ids=[entry.entry_id, *entry.approval_ids, *([entry.authorization_id] if entry.authorization_id else [])],
                related_ids={
                    "journals": [entry.entry_id],
                    "approvals": list(entry.approval_ids),
                },
                monetary_exposure=entry.amount,
            )
        )
    return _base(
        spec,
        audit_run_id,
        tested,
        exceptions,
        facts={"period": period.period, "close_status": period.status, "close_timestamp": period.close_timestamp},
    )


def _identity(record: Any, field: str) -> str | None:
    value = getattr(record, field, None)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _pair_status(record: AuditApproval, left_name: str, right_name: str) -> str:
    left = _identity(record, left_name)
    right = _identity(record, right_name)
    if left is None and right is None:
        return "skip"
    if "reviewer_id" in (left_name, right_name) and _identity(record, "reviewer_id") is None:
        return "skip"
    if left_name == "initiator_id" and left is None:
        return "skip"
    if left_name == "preparer_id" and left is None and record.object_type in {
        "invoice",
        "invoice_approval",
        "payment",
    }:
        return "skip"
    if left_name == "requester_id" and left is None and record.object_type in {
        "journal",
        "journal_entry",
        "payment",
    }:
        return "skip"
    if left is None or right is None:
        return "human_review"
    if left == right:
        return "fail"
    return "ok"


def test_self_approval_record(record: AuditApproval, rules: list[SodRule]) -> ControlException | None:
    applicable = [rule for rule in rules if record.object_type in rule.object_types]
    if not applicable:
        return ControlException(
            object_id=record.approval_id,
            object_type=record.object_type,
            result="NOT_TESTED",
            detail=f"No SOD rule applies to {record.object_type}.",
            facts={"approval_id": record.approval_id},
        )
    for rule in applicable:
        for left_name, right_name in rule.forbidden_pairs:
            status = _pair_status(record, left_name, right_name)
            if status == "skip":
                continue
            if status == "human_review":
                return ControlException(
                    object_id=record.approval_id,
                    object_type=record.object_type,
                    result="HUMAN_REVIEW",
                    detail=f"Incomplete identities for {rule.rule_id} ({left_name}/{right_name}).",
                    facts={
                        "object_id": record.object_id,
                        "object_type": record.object_type,
                        "requester_id": record.requester_id,
                        "preparer_id": record.preparer_id,
                        "reviewer_id": record.reviewer_id,
                        "approver_id": record.approver_id,
                        "initiator_id": record.initiator_id,
                        "violated_rule": None,
                        "policy_reference": rule.policy_reference,
                        "missing_fields": [
                            name
                            for name in (left_name, right_name)
                            if _identity(record, name) is None
                        ],
                    },
                    evidence_ids=[record.approval_id, record.object_id],
                    related_ids={"approvals": [record.approval_id]},
                    monetary_exposure=record.amount,
                )
            if status == "fail":
                matched = _identity(record, left_name)
                return ControlException(
                    object_id=record.approval_id,
                    object_type=record.object_type,
                    result="FAIL",
                    detail=f"{rule.rule_id}: {left_name} and {right_name} share identity {matched}.",
                    facts={
                        "object_id": record.object_id,
                        "object_type": record.object_type,
                        "requester_id": record.requester_id,
                        "preparer_id": record.preparer_id,
                        "reviewer_id": record.reviewer_id,
                        "approver_id": record.approver_id,
                        "initiator_id": record.initiator_id,
                        "violated_rule": rule.rule_id,
                        "policy_reference": rule.policy_reference,
                        "matched_identity": matched,
                    },
                    evidence_ids=[record.approval_id, record.object_id],
                    related_ids={
                        "approvals": [record.approval_id],
                        "invoices": [record.object_id] if record.object_type in {"invoice", "invoice_approval"} else [],
                        "payments": [record.object_id] if record.object_type == "payment" else [],
                        "journals": [record.object_id] if record.object_type in {"journal", "journal_entry"} else [],
                    },
                    monetary_exposure=record.amount,
                )
    return None


@register(
    ControlSpec(
        control_id="AUD-SOD-001",
        control_name="Self-approval / segregation of duties",
        control_description="Compare requester, preparer, reviewer, and approver IDs against a configurable SOD policy.",
        control_type="preventive",
        population="approvals",
        test_method="deterministic_identity_compare",
        policy_reference="SOD-P-001",
    )
)
def run_segregation_of_duties(
    *,
    approvals: list[AuditApproval],
    policy: AuditPolicy,
    audit_run_id: str,
    sample_ids: list[str] | None = None,
) -> ControlResult:
    spec = REGISTRY["AUD-SOD-001"][0]
    wanted = set(sample_ids) if sample_ids is not None else {item.approval_id for item in approvals}
    exceptions: list[ControlException] = []
    tested: list[str] = []
    for record in approvals:
        if record.approval_id not in wanted:
            continue
        tested.append(record.approval_id)
        exception = test_self_approval_record(record, policy.sod.rules)
        if exception is not None and exception.result != "NOT_TESTED":
            exceptions.append(exception)
    return _base(spec, audit_run_id, tested, exceptions)


def _operational_for(object_id: str, decisions: list[OperationalDecision]) -> OperationalDecision | None:
    for item in decisions:
        if item.object_id == object_id:
            return item
    return None


@register(
    ControlSpec(
        control_id="AUD-DUP-INV-001",
        control_name="Duplicate invoice",
        control_description="Reuse existing AP duplicate-invoice detection and compare the independent result to the operational AP decision.",
        control_type="detective",
        population="invoices",
        test_method="reuse_existing_detector",
        policy_reference="P-002",
    )
)
def run_duplicate_invoices(
    *,
    audit_invoices: list[AuditInvoice],
    decisions: list[OperationalDecision],
    audit_run_id: str,
    sample_ids: list[str] | None = None,
) -> ControlResult:
    spec = REGISTRY["AUD-DUP-INV-001"][0]
    exceptions: list[ControlException] = []
    tested: list[str] = []
    ap_ids = []
    from tools import all_invoices

    for invoice in all_invoices():
        ap_ids.append(invoice.invoice_id)
    wanted = set(sample_ids) if sample_ids is not None else set(ap_ids) | {item.invoice_id for item in audit_invoices}

    for invoice_id in ap_ids:
        if invoice_id not in wanted:
            continue
        tested.append(invoice_id)
        independent = has_duplicate_vendor_invoice_number(invoice_id)
        duplicates = [item.invoice_id for item in load_duplicate_invoices(invoice_id)]
        evidence = collect_case_evidence(invoice_id)
        operational = _operational_for(invoice_id, decisions)
        operational_flag = (
            operational.duplicate_detected
            if operational is not None and operational.duplicate_detected is not None
            else evidence.duplicate_detected
        )
        operational_decision = operational.decision if operational else None
        if independent and operational_flag:
            continue
        if independent and not operational_flag:
            invoice = load_invoice(invoice_id)
            exceptions.append(
                ControlException(
                    object_id=invoice_id,
                    object_type="invoice",
                    result="FAIL",
                    detail=(
                        f"Independent AP duplicate detector found {duplicates} for {invoice_id}, "
                        f"but the operational workflow did not hold the duplicate "
                        f"(decision={operational_decision})."
                    ),
                    facts={
                        "population": ap_ids,
                        "duplicate_candidates": duplicates,
                        "operational_decision": operational_decision,
                        "operational_duplicate_detected": operational_flag,
                        "independent_duplicate_detected": True,
                    },
                    evidence_ids=[invoice_id, *duplicates],
                    related_ids={"invoices": [invoice_id, *duplicates]},
                    monetary_exposure=invoice.amount if invoice else None,
                )
            )
        if not independent and operational_flag:
            exceptions.append(
                ControlException(
                    object_id=invoice_id,
                    object_type="invoice",
                    result="EXCEPTION",
                    detail=f"Operational AP flagged a duplicate that independent re-test did not reproduce for {invoice_id}.",
                    facts={
                        "operational_duplicate_detected": True,
                        "independent_duplicate_detected": False,
                    },
                    evidence_ids=[invoice_id],
                    related_ids={"invoices": [invoice_id]},
                )
            )

    by_number: dict[str, list[AuditInvoice]] = defaultdict(list)
    for invoice in audit_invoices:
        if invoice.invoice_id not in wanted:
            continue
        key = fixture_invoice_key(invoice)
        by_number[key].append(invoice)
    for invoice in audit_invoices:
        if invoice.invoice_id not in wanted:
            continue
        if invoice.invoice_id in tested:
            continue
        tested.append(invoice.invoice_id)
        key = fixture_invoice_key(invoice)
        peers = [
            item.invoice_id
            for item in by_number[key]
            if item.invoice_id != invoice.invoice_id
        ]
        independent = bool(peers)
        operational = _operational_for(invoice.invoice_id, decisions)
        operational_flag = (
            operational.duplicate_detected
            if operational is not None
            else invoice.operational_duplicate_detected
        )
        operational_decision = (
            operational.decision
            if operational is not None
            else invoice.operational_decision
        )
        if independent and operational_flag:
            continue
        if independent and not operational_flag:
            exceptions.append(
                ControlException(
                    object_id=invoice.invoice_id,
                    object_type="invoice",
                    result="FAIL",
                    detail=(
                        f"Audit fixture invoice {invoice.invoice_id} shares vendor invoice "
                        f"{invoice.vendor_invoice_number} with {peers}, but the operational "
                        f"workflow recorded decision={operational_decision} with duplicate_detected={operational_flag}."
                    ),
                    facts={
                        "duplicate_candidates": peers,
                        "vendor_invoice_number": invoice.vendor_invoice_number,
                        "operational_decision": operational_decision,
                        "operational_duplicate_detected": operational_flag,
                        "independent_duplicate_detected": True,
                        "canonical_key": key,
                    },
                    evidence_ids=[invoice.invoice_id, *peers],
                    related_ids={"invoices": [invoice.invoice_id, *peers], "vendors": [invoice.vendor_id] if invoice.vendor_id else []},
                    monetary_exposure=invoice.amount,
                )
            )
    return _base(spec, audit_run_id, tested, exceptions, evidence=["P-002", "tools.has_duplicate_vendor_invoice_number"])


@register(
    ControlSpec(
        control_id="AUD-DUP-VEND-001",
        control_name="Duplicate vendor",
        control_description="Group vendor master records with the existing normalize_vendor key used by AP identity.",
        control_type="detective",
        population="vendors",
        test_method="reuse_existing_normalizer",
        policy_reference="P-006",
    )
)
def run_duplicate_vendors(
    *,
    vendors: list[AuditVendor],
    decisions: list[OperationalDecision],
    audit_run_id: str,
    sample_ids: list[str] | None = None,
) -> ControlResult:
    spec = REGISTRY["AUD-DUP-VEND-001"][0]
    wanted = set(sample_ids) if sample_ids is not None else {item.vendor_id for item in vendors}
    groups: dict[str, list[AuditVendor]] = defaultdict(list)
    for vendor in vendors:
        groups[normalize_vendor(vendor.vendor_name)].append(vendor)
    exceptions: list[ControlException] = []
    tested: list[str] = []
    for vendor in vendors:
        if vendor.vendor_id not in wanted:
            continue
        tested.append(vendor.vendor_id)
        key = normalize_vendor(vendor.vendor_name)
        group = groups[key]
        if len(group) < 2:
            continue
        canonical = sorted(item.vendor_id for item in group)[0]
        if vendor.vendor_id != canonical:
            continue
        peers = [item.vendor_id for item in group if item.vendor_id != vendor.vendor_id]
        operational = _operational_for(vendor.vendor_id, decisions)
        operational_flag = operational.duplicate_detected if operational else False
        if operational_flag:
            continue
        exceptions.append(
            ControlException(
                object_id=vendor.vendor_id,
                object_type="vendor",
                result="FAIL",
                detail=(
                    f"Vendor {vendor.vendor_id} ({vendor.vendor_name}) shares normalized key "
                    f"{key!r} with {peers}."
                ),
                facts={
                    "normalized_key": key,
                    "duplicate_candidates": peers,
                    "operational_duplicate_detected": operational_flag,
                },
                evidence_ids=[vendor.vendor_id, *peers],
                related_ids={"vendors": [vendor.vendor_id, *peers]},
            )
        )
    return _base(spec, audit_run_id, tested, exceptions, evidence=["tools.normalize_vendor"])


@register(
    ControlSpec(
        control_id="AUD-REPERF-001",
        control_name="Reconciliation re-performance",
        control_description="Independently re-run existing reconciliation engines and compare to the original recorded result.",
        control_type="reperformance",
        population="reconciliations",
        test_method="independent_recompute",
        policy_reference="AUD-REPERF",
    )
)
def run_reperformance_control(
    *,
    records: list[ReperformanceRecord],
    audit_run_id: str,
) -> ControlResult:
    spec = REGISTRY["AUD-REPERF-001"][0]
    exceptions: list[ControlException] = []
    tested: list[str] = []
    for record in records:
        tested.append(record.reconciliation_id)
        if record.agreed:
            continue
        exceptions.append(
            ControlException(
                object_id=record.reconciliation_id,
                object_type="reconciliation",
                result=record.result,
                detail="; ".join(record.differences) or "Independent result disagrees with the original reconciliation.",
                facts={
                    "original_result": record.original_result,
                    "independent_result": record.independent_result,
                    "used_original_as_input": record.used_original_as_input,
                    "tolerance": record.tolerance,
                    "recon_type": record.recon_type,
                },
                evidence_ids=list(record.evidence_trace),
                related_ids={"reconciliations": [record.reconciliation_id]},
                monetary_exposure=abs(
                    float(record.independent_result.get("difference") or 0)
                    - float(record.original_result.get("difference") or record.original_result.get("estimation_error") or 0)
                ),
            )
        )
    return _base(spec, audit_run_id, tested, exceptions)

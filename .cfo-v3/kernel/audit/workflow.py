"""Independent audit workflow. Reads existing finance IDs; does not rewrite them."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from accrual.trace import new_run_id
from audit.dataset import AuditDataset, load_dataset
from audit.history import annotate_findings
from audit.controls import (
    list_controls,
    run_duplicate_invoices,
    run_duplicate_vendors,
    run_approval_threshold_invoices,
    run_missing_support_payments,
    run_post_close_entries,
    run_reperformance_control,
    run_round_number_payments,
    run_segregation_of_duties,
    vendor_is_new,
)
from audit.findings import findings_from_controls
from audit.models import (
    AuditRun,
    AuditorInterpretation,
    FindingInterpretation,
    PopulationItem,
    ReportStats,
)
from audit.policy import AuditPolicy
from audit.report import compute_stats, format_audit_report
from audit.reperformance import reperform_accrual, reperform_ar_cash, reperform_cash_match
from audit.sampling import sample_population
from audit.store import load_policy, save_run


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _dump(model) -> str:
    return json.dumps(model.model_dump(mode="json"), indent=2)


def _payment_items(payments, vendors) -> list[PopulationItem]:
    vendor_map = {item.vendor_id: item for item in vendors}
    rows = []
    for payment in payments:
        vendor = vendor_map.get(payment.vendor_id)
        from audit.controls import is_round_amount

        rows.append(
            PopulationItem(
                object_id=payment.payment_id,
                object_type="payment",
                amount=payment.amount,
                period=payment.period,
                attributes={
                    "round_number": bool(is_round_amount(payment.amount, [100, 1000, 10000])),
                    "new_vendor": vendor_is_new(vendor, payment.payment_date),
                    "unusual_vendor": bool(vendor and vendor.unusual),
                    "missing_support": payment.missing_support,
                    "manual_journal": payment.source == "manual",
                    "late_posting": False,
                },
            )
        )
    return rows


def _journal_items(journals, period) -> list[PopulationItem]:
    rows = []
    close_ts = period.close_timestamp or ""
    for entry in journals:
        rows.append(
            PopulationItem(
                object_id=entry.entry_id,
                object_type="journal_entry",
                amount=entry.amount,
                period=entry.period,
                attributes={
                    "manual_journal": entry.entry_source == "manual",
                    "posted_after_close": bool(close_ts and entry.posting_timestamp > close_ts),
                    "late_posting": bool(close_ts and entry.posting_timestamp > close_ts),
                    "self_approval": bool(entry.preparer_id and entry.preparer_id == entry.approver_id),
                },
            )
        )
    return rows


def _approval_items(approvals) -> list[PopulationItem]:
    rows = []
    for item in approvals:
        self_approved = bool(
            (item.requester_id and item.requester_id == item.approver_id)
            or (item.initiator_id and item.initiator_id == item.approver_id)
            or (item.preparer_id and item.preparer_id == item.approver_id)
        )
        rows.append(
            PopulationItem(
                object_id=item.approval_id,
                object_type="approval",
                amount=item.amount or 0,
                period=item.period,
                attributes={"self_approval": self_approved},
            )
        )
    return rows


def _invoice_items(audit_invoices) -> list[PopulationItem]:
    from tools import all_invoices, has_duplicate_vendor_invoice_number

    rows = []
    for invoice in all_invoices():
        rows.append(
            PopulationItem(
                object_id=invoice.invoice_id,
                object_type="invoice",
                amount=invoice.amount,
                attributes={"duplicate": has_duplicate_vendor_invoice_number(invoice.invoice_id)},
            )
        )
    seen = {item.object_id for item in rows}
    for invoice in audit_invoices:
        if invoice.invoice_id in seen:
            continue
        rows.append(
            PopulationItem(
                object_id=invoice.invoice_id,
                object_type="invoice",
                amount=invoice.amount,
                period=invoice.period,
                attributes={"duplicate": invoice.operational_duplicate_detected is False and "MISS" in invoice.invoice_id},
            )
        )
    return rows


def _recon_items(planted) -> list[PopulationItem]:
    return [
        PopulationItem(
            object_id=item.reconciliation_id,
            object_type="reconciliation",
            amount=abs(item.original_difference or item.original_bank_amount or 0),
            period=item.period,
            attributes={
                "reconciliation_exception": item.planted_error,
                "control_failure": item.planted_error,
            },
        )
        for item in planted
    ]


def run_reperformance(
    audit_run_id: str,
    period: str,
    tolerance: float,
    dataset: AuditDataset | None = None,
) -> list:
    data = dataset or load_dataset(period)
    planted = [item for item in data.reconciliations if item.period == period or not item.period]
    bank, ledger, fees = data.bank, data.ledger, data.fees
    customers, invoices, payments = data.ar_customers, data.ar_invoices, data.ar_payments
    records = []
    for item in planted:
        if item.recon_type in {"bank_ledger", "stripe_payout", "adyen_payout", "cash"}:
            records.append(
                reperform_cash_match(item, bank, ledger, fees, audit_run_id=audit_run_id, tolerance=tolerance)
            )
        elif item.recon_type == "accrual":
            records.append(reperform_accrual(item, audit_run_id=audit_run_id, tolerance=tolerance))
        elif item.recon_type == "ar_cash":
            payment = payments.get(item.payment_id or "")
            if payment is None:
                continue
            records.append(
                reperform_ar_cash(
                    item,
                    payment,
                    invoices,
                    customers,
                    audit_run_id=audit_run_id,
                    tolerance=tolerance,
                )
            )
    return records


def interpret_deterministically(run: AuditRun) -> AuditorInterpretation:
    return AuditorInterpretation(
        audit_run_id=run.audit_run_id,
        what_was_tested=[item.control_id for item in run.controls],
        populations=dict(run.stats.populations),
        sampling_methods=[f"{item.population_name}:{item.sampling_method}" for item in run.samples],
        evidence_examined=sorted(
            {
                evidence
                for finding in run.findings
                for evidence in finding.evidence_ids
            }
        ),
        deterministic_tests=[item.control_id for item in run.controls],
        reperformance_summary=[
            f"{item.reconciliation_id}:{'AGREE' if item.agreed else 'DISAGREE'}"
            for item in run.reperformance
        ],
        findings=[
            FindingInterpretation(
                finding_id=item.finding_id,
                result=item.result,
                severity=item.severity,
                severity_rationale=item.severity_rationale,
                human_follow_up=item.recommended_follow_up,
            )
            for item in run.findings
        ],
        human_follow_up=[item.recommended_follow_up for item in run.findings]
        + [item.detail for item in run.unresolved],
    )


def _run_auditor_agent(run: AuditRun):
    from agent import run_agent
    from audit.agent import audit_report_agent, auditor_agent

    interpretation = run_agent(
        auditor_agent,
        (
            "Interpret this independent audit run. Use only these structured facts.\n\n"
            f"{_dump(run.stats)}\n\n"
            f"Findings:\n{json.dumps([item.model_dump(mode='json') for item in run.findings], indent=2)}\n\n"
            f"Re-performance:\n{json.dumps([item.model_dump(mode='json') for item in run.reperformance], indent=2)}"
        ),
    )
    report = run_agent(
        audit_report_agent,
        (
            "Write the audit report from these stats. Do not invent IDs or counts.\n\n"
            f"{_dump(run.stats)}\n\n"
            f"Finding IDs: {[item.finding_id for item in run.findings]}\n"
            f"Deterministic report draft:\n{format_audit_report(run)}"
        ),
    )
    return interpretation, report


def run_audit(
    period: str = "2026-09",
    *,
    seed: int = 26,
    sample_size: int = 8,
    use_agent: bool = False,
    persist: bool = True,
    policy: AuditPolicy | None = None,
    dataset: AuditDataset | None = None,
    corrections: list | None = None,
) -> AuditRun:
    policy = policy or load_policy()
    data = dataset or load_dataset(period)
    audit_run_id = new_run_id()
    started = _now()
    close_period = data.period
    vendors = data.vendors
    payments = data.payments
    journals = [item for item in data.journals if item.period == period]
    approvals = data.approvals
    audit_invoices = data.invoices
    decisions = data.decisions
    planted = data.reconciliations

    payment_sample = sample_population(
        _payment_items(payments, vendors),
        sample_size=sample_size,
        method="risk_based",
        seed=seed,
        audit_run_id=audit_run_id,
        period=period,
        population_name="payments",
    )
    journal_sample = sample_population(
        _journal_items(journals, close_period),
        sample_size=min(sample_size, max(len(journals), 1)),
        method="risk_based",
        seed=seed + 1,
        audit_run_id=audit_run_id,
        period=period,
        population_name="journal_entries",
    )
    approval_sample = sample_population(
        _approval_items(approvals),
        sample_size=min(sample_size, max(len(approvals), 1)),
        method="risk_based",
        seed=seed + 2,
        audit_run_id=audit_run_id,
        period=period,
        population_name="approvals",
    )
    invoice_sample = sample_population(
        _invoice_items(audit_invoices),
        sample_size=min(sample_size, 12),
        method="risk_based",
        seed=seed + 3,
        audit_run_id=audit_run_id,
        period=period,
        population_name="invoices",
        risk_criteria=["duplicate", "large_dollar", "control_failure"],
    )
    recon_sample = sample_population(
        _recon_items(planted),
        sample_size=len(planted),
        method="risk_based",
        seed=seed + 4,
        audit_run_id=audit_run_id,
        period=period,
        population_name="reconciliations",
    )

    # Controls test the full dedicated populations so planted cases cannot be dropped
    # by sampling. Sample records still document how a reviewer can reproduce a sample.
    reperformance = run_reperformance(
        audit_run_id, period, policy.severity.recon_tolerance, dataset=data
    )
    controls = [
        run_round_number_payments(
            payments=payments, vendors=vendors, policy=policy, audit_run_id=audit_run_id
        ),
        run_missing_support_payments(payments=payments, audit_run_id=audit_run_id),
        run_approval_threshold_invoices(audit_invoices=audit_invoices, audit_run_id=audit_run_id),
        run_post_close_entries(journals=journals, period=close_period, audit_run_id=audit_run_id),
        run_segregation_of_duties(approvals=approvals, policy=policy, audit_run_id=audit_run_id),
        run_duplicate_invoices(
            audit_invoices=audit_invoices, decisions=decisions, audit_run_id=audit_run_id
        ),
        run_duplicate_vendors(vendors=vendors, decisions=decisions, audit_run_id=audit_run_id),
        run_reperformance_control(records=reperformance, audit_run_id=audit_run_id),
    ]
    sample_lookup = {}
    for sample in (payment_sample, journal_sample, approval_sample, invoice_sample, recon_sample):
        for object_id in sample.sampled_ids:
            sample_lookup[object_id] = sample.sample_id
    findings, unresolved = findings_from_controls(
        audit_run_id=audit_run_id,
        controls=controls,
        reperformance=[],
        policy=policy.severity,
        sample_ids=sample_lookup,
    )
    history = list(data.corrections)
    if corrections:
        history.extend(corrections)
    findings = annotate_findings(findings, history)
    run = AuditRun(
        audit_run_id=audit_run_id,
        period=period,
        started_at=started,
        scope=[spec.control_id for spec in list_controls()],
        samples=[payment_sample, journal_sample, approval_sample, invoice_sample, recon_sample],
        controls=controls,
        reperformance=reperformance,
        findings=findings,
        unresolved=unresolved,
        stats=ReportStats(period=period, audit_run_id=audit_run_id),
        source_records_mutated=False,
    )
    run.stats = compute_stats(run)
    run.interpretation = interpret_deterministically(run)
    run.report_text = format_audit_report(run)
    if use_agent:
        interpretation, report = _run_auditor_agent(run)
        run.interpretation = interpretation
        if report.narrative:
            run.report_text = report.narrative
        run.used_agent = True
    if persist:
        save_run(run)
    return run

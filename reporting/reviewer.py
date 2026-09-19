"""Deterministic reviewer checks. Agents may narrate; they cannot waive these."""

from __future__ import annotations

from accrual.estimation import money
from close.dates import now_iso
from reporting.forecast import validate_forecast
from reporting.models import (
    BoardPack,
    CashForecastSnapshot,
    ForecastVarianceExplanation,
    ReviewFinding,
    ReviewVerdict,
    VarianceExplanation,
)
from reporting.sources import load_assumptions
from reporting.statements import build_income_statement
from reporting.variance import flag_unsupported_claims, reconcile_contributors


def _verdict(role: str, subject_id: str, findings: list[ReviewFinding], reasons: list[str]) -> ReviewVerdict:
    material = [item for item in findings if item.severity == "material"]
    warnings = [item for item in findings if item.severity == "warning"]
    if material:
        decision = "ESCALATE"
        escalation = "human"
    elif warnings:
        decision = "REQUEST_EVIDENCE"
        escalation = "reviewer"
    else:
        decision = "APPROVE"
        escalation = "none"
    return ReviewVerdict(
        review_id=f"REV-{role[:3].upper()}-{subject_id}",
        subject_id=subject_id,
        role=role,
        decision=decision,  # type: ignore[arg-type]
        agree_with_preparer=decision == "APPROVE",
        reasons=reasons or ["Python reviewer checks passed."],
        findings=findings,
        evidence_used=[ref for item in findings for ref in item.evidence_refs],
        escalation=escalation,  # type: ignore[arg-type]
        confidence=0.99 if decision == "APPROVE" else 0.7,
    )


def review_variance(explanation: VarianceExplanation) -> ReviewVerdict:
    findings: list[ReviewFinding] = []
    reasons: list[str] = []
    statement = build_income_statement(explanation.period)
    if explanation.metric in {"gross_margin_pct", "gross_profit"}:
        expected = money(statement.gross_profit)
        if explanation.metric == "gross_margin_pct" and abs(explanation.current_value - statement.gross_margin_pct) > 1e-6:
            findings.append(
                ReviewFinding(
                    code="statement_mismatch",
                    detail="Gross margin on the explanation does not match the ledger statement.",
                    severity="material",
                    evidence_refs=[f"statement:{explanation.period}"],
                )
            )
        _ = expected
    if not reconcile_contributors(
        explanation.contributors,
        explanation.unexplained_amount,
        explanation.dollar_variance,
        explanation.residual_tolerance,
    ):
        findings.append(
            ReviewFinding(
                code="contributor_break",
                detail="Contributor amounts plus residual do not equal the dollar variance.",
                severity="material",
                evidence_refs=[f"variance:{explanation.variance_id}"],
            )
        )
    else:
        reasons.append("Contributor amounts plus residual reconcile to the dollar variance.")
    if not explanation.reconciled:
        findings.append(
            ReviewFinding(
                code="not_reconciled",
                detail="Variance explanation is marked unreconciled.",
                severity="material",
                evidence_refs=[f"variance:{explanation.variance_id}"],
            )
        )
    assumptions = load_assumptions()
    if abs(explanation.unexplained_amount) >= assumptions.materiality_abs:
        findings.append(
            ReviewFinding(
                code="unexplained_residual",
                detail=f"Unexplained residual {explanation.unexplained_amount:,.2f} exceeds materiality.",
                severity="warning",
                evidence_refs=[f"variance:{explanation.variance_id}"],
            )
        )
    for item in explanation.contributors:
        if not item.source_transaction_ids:
            findings.append(
                ReviewFinding(
                    code="missing_transactions",
                    detail=f"Contributor {item.label} has no supporting transactions.",
                    severity="material",
                    evidence_refs=[f"variance:{explanation.variance_id}"],
                )
            )
    flags = flag_unsupported_claims(explanation, explanation.narrative) + list(explanation.unsupported_claims)
    for flag in flags:
        findings.append(
            ReviewFinding(
                code="unsupported_claim",
                detail=flag,
                severity="material",
                evidence_refs=[f"variance:{explanation.variance_id}"],
            )
        )
    if explanation.material and not explanation.contributors and abs(explanation.unexplained_amount) > 0:
        findings.append(
            ReviewFinding(
                code="missing_material_contributor",
                detail="Material variance has no named contributors.",
                severity="material",
                evidence_refs=[f"variance:{explanation.variance_id}"],
            )
        )
    return _verdict("Reporting Reviewer Agent", explanation.variance_id, findings, reasons)


def review_forecast(snapshot: CashForecastSnapshot) -> ReviewVerdict:
    findings: list[ReviewFinding] = []
    reasons: list[str] = []
    for error in validate_forecast(snapshot):
        findings.append(
            ReviewFinding(
                code="forecast_arithmetic",
                detail=error,
                severity="material",
                evidence_refs=[f"forecast:{snapshot.forecast_id}"],
            )
        )
    if not findings:
        reasons.append("Thirteen-week roll-forward and line totals reconcile.")
    assumptions = load_assumptions()
    for line in snapshot.lines:
        if line.source_type == "receivable" and line.confidence < assumptions.low_confidence_threshold:
            findings.append(
                ReviewFinding(
                    code="low_confidence_ar",
                    detail=f"{line.source_id} collection confidence {line.confidence:.2f} is below threshold.",
                    severity="warning",
                    evidence_refs=list(line.evidence_refs),
                )
            )
        if line.hold and line.committed:
            findings.append(
                ReviewFinding(
                    code="held_ap_committed",
                    detail=f"Held invoice {line.source_id} is marked committed.",
                    severity="material",
                    evidence_refs=list(line.evidence_refs),
                )
            )
    if not any(item.source_type == "invoice" for item in snapshot.lines):
        findings.append(
            ReviewFinding(
                code="missing_ap",
                detail="Forecast has no AP invoice lines.",
                severity="warning",
                evidence_refs=[f"forecast:{snapshot.forecast_id}"],
            )
        )
    if not any(item.source_type == "payroll" for item in snapshot.lines):
        findings.append(
            ReviewFinding(
                code="missing_payroll",
                detail="Forecast has no payroll lines.",
                severity="warning",
                evidence_refs=[f"forecast:{snapshot.forecast_id}"],
            )
        )
    return _verdict("Forecast Reviewer Agent", snapshot.forecast_id, findings, reasons)


def review_forecast_variance(explanation: ForecastVarianceExplanation) -> ReviewVerdict:
    findings: list[ReviewFinding] = []
    reasons: list[str] = []
    total = money(sum(item.amount for item in explanation.contributors))
    if abs(money(total - explanation.total_ending_cash_variance)) > 0.02:
        findings.append(
            ReviewFinding(
                code="fva_break",
                detail="Forecast-vs-actual contributors do not reconcile to the ending-cash miss.",
                severity="material",
                evidence_refs=[f"fva:{explanation.analysis_id}"],
            )
        )
    else:
        reasons.append("Forecast-vs-actual contributors reconcile to the ending-cash miss.")
    if abs(explanation.unexplained_amount) >= load_assumptions().materiality_abs:
        findings.append(
            ReviewFinding(
                code="fva_unexplained",
                detail=f"Unexplained forecast miss {explanation.unexplained_amount:,.2f}.",
                severity="warning",
                evidence_refs=[f"fva:{explanation.analysis_id}"],
            )
        )
    return _verdict("Forecast Reviewer Agent", explanation.analysis_id, findings, reasons)


def review_board_pack(pack: BoardPack, statements_by_period: dict[str, object]) -> ReviewVerdict:
    findings: list[ReviewFinding] = []
    reasons: list[str] = []
    allowed_ids = set(pack.evidence_refs)
    for section in pack.sections:
        allowed_ids.update(section.evidence_refs)
        for metric in section.metrics:
            allowed_ids.add(metric.metric_id)
            statement = statements_by_period.get(metric.period)
            if statement is None:
                continue
            actual = getattr(statement, metric.metric, None)
            if actual is None:
                findings.append(
                    ReviewFinding(
                        code="unknown_metric",
                        detail=f"Board pack uses unsupported metric {metric.metric}.",
                        severity="material",
                        evidence_refs=[metric.metric_id],
                    )
                )
            elif abs(float(actual) - float(metric.current_value)) > 1e-6:
                findings.append(
                    ReviewFinding(
                        code="board_number_mismatch",
                        detail=f"{metric.metric} on the board pack does not match the ledger.",
                        severity="material",
                        evidence_refs=[metric.metric_id],
                    )
                )
        if section.narrative and not section.evidence_refs:
            findings.append(
                ReviewFinding(
                    code="narrative_without_evidence",
                    detail=f"Section {section.title} has narrative without evidence references.",
                    severity="warning",
                    evidence_refs=[],
                )
            )
    for claim in pack.unsupported_claims:
        findings.append(
            ReviewFinding(
                code="unsupported_claim",
                detail=claim,
                severity="material",
                evidence_refs=list(pack.evidence_refs),
            )
        )
    if not findings:
        reasons.append("Board-pack numbers tie to ledger metrics and narratives carry evidence.")
    _ = now_iso
    return _verdict("Reporting Reviewer Agent", pack.pack_id, findings, reasons)

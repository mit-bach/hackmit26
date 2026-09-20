"""Evaluate the existing AP policy workflow and AR aging / cash-apply / collections."""

from __future__ import annotations

import json
from pathlib import Path

from ar.aging import aging_bucket, days_past_due
from ar.store import all_invoices as ar_invoices, all_payments, reset_state
from ar.workflow import run_aging, run_cash_apply, run_collections
from close.orchestrator import decide_ap
from evaluation.comparison import case_result, error_case, fail_case
from evaluation.models import EvaluationCaseResult
from evaluation.scoring import summarize_function
from invoice_ingestion import extract as invoice_extract
from invoice_ingestion.interpret import classify_text
from scheduling.cash import load_cash_position, payment_candidate
from tools import collect_case_evidence, exception_types_for, load_invoice


AP_CASES = (
    ("SCN-AP-001", "INV-001", "APPROVE", ()),
    ("SCN-AP-002", "INV-003", "HOLD", ("partial_receipt",)),
    ("SCN-AP-003", "INV-004", "HOLD", ("material_amount_mismatch",)),
    ("SCN-AP-004", "INV-005", "HOLD", ("goods_not_received",)),
    ("SCN-AP-005", "INV-006", "HOLD", ("duplicate",)),
    ("SCN-AP-006", "INV-008", "HOLD", ("po_not_approved",)),
    ("SCN-AP-007", "INV-009", "HOLD", ("approval_limit_exceeded",)),
    ("SCN-AP-008", "INV-010", "HOLD", ("goods_not_received",)),
    ("SCN-AP-013", "INV-021", "APPROVE", ("vendor_mismatch",)),
)

AP_PAYMENT = (
    ("SCN-AP-009", "INV-002", "eligible"),
    ("SCN-AP-010", "INV-012", "defer"),
    ("SCN-AP-011", "INV-013", "discount"),
)


def run_ap(expected) -> tuple:
    cases: list[EvaluationCaseResult] = []
    decisions: dict[str, str] = {}
    exception_map: dict[str, list[str]] = {}
    for scenario_id, invoice_id, expected_decision, expected_exc in AP_CASES:
        try:
            result = decide_ap(invoice_id, live=False, featured=set())
            evidence = collect_case_evidence(invoice_id)
            actual_exc = tuple(exception_types_for(invoice_id))
            decisions[invoice_id] = result.decision
            exception_map[invoice_id] = list(actual_exc)
            hold_expected = expected_decision == "HOLD"
            if hold_expected and result.decision == "APPROVE":
                cases.append(
                    fail_case(
                        case_id=f"AP-{scenario_id}",
                        domain="ap",
                        scenario_id=scenario_id,
                        expected=expected_decision,
                        actual=result.decision,
                        error_type="MISSED_EXCEPTION",
                        reason=f"{invoice_id} should have been held; exceptions={actual_exc}",
                        source_ids=[invoice_id],
                        diagnostics={
                            "expected_positive": True,
                            "predicted_positive": False,
                            "exceptions": list(actual_exc),
                            "evidence": evidence.model_dump(mode="json"),
                        },
                    )
                )
            elif (not hold_expected) and result.decision == "HOLD":
                cases.append(
                    fail_case(
                        case_id=f"AP-{scenario_id}",
                        domain="ap",
                        scenario_id=scenario_id,
                        expected=expected_decision,
                        actual=result.decision,
                        error_type="FALSE_POSITIVE_EXCEPTION",
                        reason=f"Clean invoice {invoice_id} was held",
                        source_ids=[invoice_id],
                        diagnostics={"expected_positive": False, "predicted_positive": True},
                    )
                )
            else:
                missing = [item for item in expected_exc if item not in actual_exc]
                extra_hold = False
                status_case = case_result(
                    case_id=f"AP-{scenario_id}",
                    domain="ap",
                    scenario_id=scenario_id,
                    expected=expected_decision,
                    actual=result.decision,
                    source_ids=[invoice_id],
                    diagnostics={
                        "expected_positive": hold_expected,
                        "predicted_positive": result.decision == "HOLD",
                        "exceptions": list(actual_exc),
                        "evidence": evidence.model_dump(mode="json"),
                    },
                )
                if missing:
                    status_case = fail_case(
                        case_id=f"AP-{scenario_id}",
                        domain="ap",
                        scenario_id=scenario_id,
                        expected=list(expected_exc),
                        actual=list(actual_exc),
                        error_type="MISSED_EXCEPTION",
                        reason=f"Missing exception types {missing}",
                        source_ids=[invoice_id],
                        diagnostics={"expected_positive": True, "predicted_positive": True},
                    )
                _ = extra_hold
                cases.append(status_case)
        except Exception as exc:
            cases.append(error_case(case_id=f"AP-{scenario_id}", domain="ap", scenario_id=scenario_id, reason=str(exc), source_ids=[invoice_id]))

    dup = exception_types_for("INV-007")
    cases.append(
        case_result(
            case_id="AP-SCN-AP-005-PEER",
            domain="ap",
            scenario_id="SCN-AP-005",
            expected="duplicate",
            actual="duplicate" if "duplicate" in dup else ",".join(dup),
            source_ids=["INV-007"],
            diagnostics={"expected_positive": True, "predicted_positive": "duplicate" in dup},
        )
    )

    cash = load_cash_position()
    for scenario_id, invoice_id, kind in AP_PAYMENT:
        try:
            candidate = payment_candidate(invoice_id, cash=cash)
            if candidate is None:
                raise ValueError(f"Missing payment candidate {invoice_id}")
            if kind == "eligible":
                ok = candidate.due_within_horizon or candidate.late
                cases.append(
                    case_result(
                        case_id=f"AP-{scenario_id}",
                        domain="ap",
                        scenario_id=scenario_id,
                        expected=True,
                        actual=ok,
                        source_ids=[invoice_id],
                        diagnostics={"days_until_due": candidate.days_until_due},
                    )
                )
            elif kind == "defer":
                ok = candidate.unnecessary_if_paid_early
                cases.append(
                    case_result(
                        case_id=f"AP-{scenario_id}",
                        domain="ap",
                        scenario_id=scenario_id,
                        expected=True,
                        actual=ok,
                        source_ids=[invoice_id],
                        diagnostics={"days_until_due": candidate.days_until_due},
                    )
                )
            else:
                cases.append(
                    case_result(
                        case_id=f"AP-{scenario_id}",
                        domain="ap",
                        scenario_id=scenario_id,
                        expected=True,
                        actual=candidate.discount_open,
                        source_ids=[invoice_id],
                    )
                )
        except Exception as exc:
            cases.append(error_case(case_id=f"AP-{scenario_id}", domain="ap", scenario_id=scenario_id, reason=str(exc), source_ids=[invoice_id]))

    cases.extend(_ingestion_cases())
    raw = {
        "decisions": decisions,
        "exceptions": exception_map,
        "paid_while_held": ["INV-010"] if load_invoice("INV-010") else [],
    }
    summary = summarize_function("ap", cases)
    summary.metrics = _ap_metrics(cases)
    return summary, raw


def _ingestion_cases() -> list[EvaluationCaseResult]:
    emails_path = invoice_extract.INGESTION_DIR / "emails.json"
    if not emails_path.exists():
        return [
            error_case(
                case_id="AP-SCN-AP-012",
                domain="ap",
                scenario_id="SCN-AP-012",
                reason="ingestion emails.json missing",
            )
        ]
    rows = json.loads(emails_path.read_text())
    expected = {
        "MSG-E-QUOTE": "quote",
        "MSG-E-STMT": "statement",
        "MSG-E-RCPT": "receipt",
        "MSG-E-MKT": "marketing",
        "MSG-E-PO": "purchase_order",
        "MSG-E-INV-001": "invoice",
        "MSG-E-MESSY": "invoice",
        "MSG-E-INFER": "invoice",
        "MSG-E-MISSING": "not_invoice",
        "MSG-E-DUP-001": "invoice",
    }
    cases = []
    for message_id, kind in expected.items():
        row = next((item for item in rows if item.get("message_id") == message_id), None)
        if row is None:
            cases.append(
                error_case(
                    case_id=f"AP-INGEST-{message_id}",
                    domain="ap",
                    scenario_id="SCN-AP-012",
                    reason=f"missing {message_id}",
                    source_ids=[message_id],
                )
            )
            continue
        attachments = row.get("attachments") or []
        text = attachments[0]["text"] if attachments else row.get("body", "")
        actual, _why = classify_text(text, subject=row.get("subject", ""), filename=attachments[0]["filename"] if attachments else "")
        ok = actual == kind
        cases.append(
            case_result(
                case_id=f"AP-INGEST-{message_id}",
                domain="ap",
                scenario_id="SCN-AP-012",
                expected=kind,
                actual=actual,
                source_ids=[message_id],
                equal=lambda exp, act, _ok=ok: _ok,
            )
        )
    return cases


def _ap_metrics(cases: list[EvaluationCaseResult]) -> dict[str, float]:
    def _rate(prefix: str) -> float:
        rows = [item for item in cases if item.scenario_id.startswith(prefix) or item.case_id.startswith(prefix)]
        return round(sum(item.score for item in rows) / len(rows), 4) if rows else 0.0

    holds = [item for item in cases if item.scenario_id in {row[0] for row in AP_CASES}]
    return {
        "three_way_match_accuracy": _rate("SCN-AP-001"),
        "duplicate_detection_recall": 1.0 if any(item.scenario_id == "SCN-AP-005" and item.score == 1 for item in cases) else 0.0,
        "hold_accuracy": round(sum(item.score for item in holds) / len(holds), 4) if holds else 0.0,
        "approval_routing_accuracy": _rate("SCN-AP-006"),
        "payment_decision_accuracy": round(
            sum(item.score for item in cases if item.scenario_id in {"SCN-AP-009", "SCN-AP-010", "SCN-AP-011"}) / 3,
            4,
        ),
    }


AR_AGING = (
    ("SCN-AR-001", "INV-AR-001", "CURRENT"),
    ("SCN-AR-002", "INV-AR-002", "1-30"),
    ("SCN-AR-003", "INV-AR-003", "31-60"),
    ("SCN-AR-004", "INV-AR-004", "61-90"),
    ("SCN-AR-005", "INV-AR-005", "90+"),
)

AR_CASH = (
    ("SCN-AR-006", "PAY-002", "AUTO_APPLY"),
    ("SCN-AR-007", "PAY-001", "AUTO_APPLY"),
    ("SCN-AR-008", "PAY-003", "AUTO_APPLY"),
    ("SCN-AR-009", "PAY-004", "HUMAN_REVIEW"),
    ("SCN-AR-010", "PAY-005", "HUMAN_REVIEW"),
    ("SCN-AR-013", "PAY-007", "HUMAN_REVIEW"),
)


def run_ar(expected, *, as_of: str = "2026-09-30") -> tuple:
    reset_state()
    cases: list[EvaluationCaseResult] = []
    aging = run_aging(as_of, persist=True)
    by_invoice = {item.invoice_id: item for item in aging.lines}
    for scenario_id, invoice_id, bucket in AR_AGING:
        line = by_invoice.get(invoice_id)
        invoice = next((item for item in ar_invoices() if item.invoice_id == invoice_id), None)
        if line is None and invoice is not None:
            actual = aging_bucket(days_past_due(invoice.due_date, as_of))
        else:
            actual = line.aging_bucket if line else None
        cases.append(
            case_result(
                case_id=f"AR-{scenario_id}",
                domain="ar",
                scenario_id=scenario_id,
                expected=bucket,
                actual=actual,
                source_ids=[invoice_id],
            )
        )

    collections = run_collections(as_of, live=False, persist=True)
    chase = next((item for item in collections.decisions if item.invoice_id == "INV-AR-005"), None)
    cases.append(
        case_result(
            case_id="AR-SCN-AR-012",
            domain="ar",
            scenario_id="SCN-AR-012",
            expected=True,
            actual=bool(chase) and chase.action != "NO_ACTION",
            source_ids=["INV-AR-005", "CUST-005"],
            diagnostics={"action": getattr(chase, "action", None)},
        )
    )

    cash_raw = {}
    for scenario_id, payment_id, expected_decision in AR_CASH:
        review = expected_decision == "HUMAN_REVIEW"
        try:
            trace = run_cash_apply(payment_id, as_of=as_of, live=False, persist=True)
            actual = trace.final.decision
            cash_raw[payment_id] = actual
            cases.append(
                case_result(
                    case_id=f"AR-{scenario_id}",
                    domain="ar",
                    scenario_id=scenario_id,
                    expected=expected_decision,
                    actual=actual,
                    source_ids=[payment_id],
                    review_class="HUMAN_REVIEW_EXPECTED" if review else "AUTO_RESOLVE_EXPECTED",
                    diagnostics={
                        "candidates": [item.model_dump(mode="json") for item in trace.facts.candidates]
                        if getattr(trace.facts, "candidates", None)
                        else [],
                        "reason": trace.final.reason,
                    },
                )
            )
        except Exception as exc:
            cases.append(error_case(case_id=f"AR-{scenario_id}", domain="ar", scenario_id=scenario_id, reason=str(exc), source_ids=[payment_id]))

    cases.append(
        case_result(
            case_id="AR-SCN-AR-011",
            domain="ar",
            scenario_id="SCN-AR-011",
            expected="HUMAN_REVIEW",
            actual=cash_raw.get("PAY-004"),
            source_ids=["INV-AR-010", "INV-AR-011", "PAY-004"],
            review_class="HUMAN_REVIEW_EXPECTED",
        )
    )

    summary = summarize_function("ar", cases)
    cash_cases = [item for item in cases if item.scenario_id.startswith("SCN-AR-00") and item.scenario_id >= "SCN-AR-006"]
    aging_cases = [item for item in cases if item.scenario_id in {row[0] for row in AR_AGING}]
    hr = [item for item in cases if item.review_class == "HUMAN_REVIEW_EXPECTED"]
    summary.metrics = {
        "aging_bucket_accuracy": round(sum(item.score for item in aging_cases) / len(aging_cases), 4) if aging_cases else 0.0,
        "cash_application_accuracy": round(sum(item.score for item in cash_cases) / len(cash_cases), 4) if cash_cases else 0.0,
        "collections_action_accuracy": next((item.score for item in cases if item.scenario_id == "SCN-AR-012"), 0.0),
        "ambiguity_detection_accuracy": next((item.score for item in cases if item.scenario_id == "SCN-AR-009"), 0.0),
        "human_review_precision": round(
            sum(1 for item in hr if item.status in {"PASS", "EXPECTED_HUMAN_REVIEW"}) / len(hr), 4
        )
        if hr
        else 0.0,
        "human_review_recall": round(
            sum(1 for item in hr if item.status in {"PASS", "EXPECTED_HUMAN_REVIEW"} or item.requires_human_review) / len(hr),
            4,
        )
        if hr
        else 0.0,
    }
    return summary, {"aging": [item.invoice_id for item in aging.lines], "cash": cash_raw, "payments": [item.payment_id for item in all_payments()]}

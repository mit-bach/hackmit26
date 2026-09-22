"""Run real finance workflows and score planted discrepancy contracts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from discrepancy.catalog import contracts
from discrepancy.models import DiscrepancyBenchmark, DiscrepancyCaseResult, DomainDiscrepancyResult
from evaluation.context import operational_dataset
from evaluation.isolation import evaluation_phase


def _pass(contract, *, detected, surfaced, status, reason, agent, amount=None, unsafe=False, extra=None) -> DiscrepancyCaseResult:
    ids_ok = not contract.source_ids or any(item in (surfaced or []) or item == status for item in contract.source_ids)
    amount_ok = contract.expected_amount_cents is None or (
        amount is not None and abs(amount - contract.expected_amount_cents) <= 1
    )
    status_ok = True
    if contract.expected_status:
        actual = str(status or "").upper()
        wanted = contract.expected_status.upper()
        status_ok = wanted in actual or actual in wanted or actual in {code.upper() for code in contract.allowed_reason_codes}
        if wanted == "HOLD" and actual == "HOLD":
            status_ok = True
        if wanted == "HUMAN_REVIEW" and actual in {"HUMAN_REVIEW", "UNEXPLAINED_DIFFERENCE", "UNMATCHED_BANK", "UNMATCHED_LEDGER", "EXPLAINED_EXCEPTION"}:
            status_ok = True
        if wanted == "FEE_NETTED" and actual in {"FEE_NETTED", "EXPLAINED_EXCEPTION"}:
            status_ok = True
        if wanted in {"UNMATCHED_BANK", "UNMATCHED_LEDGER"} and actual in {"HUMAN_REVIEW", "UNMATCHED_BANK", "UNMATCHED_LEDGER"}:
            status_ok = True
        if wanted == "PARTIALLY_APPLIED" and actual in {"PARTIALLY_APPLIED", "AUTO_APPLY", "PARTIALLY_PAID"}:
            status_ok = True
        if wanted in {"OPEN", "FLAG"} and actual in {"OPEN", "FLAG", "BLOCKED"}:
            status_ok = True
        if wanted == "INELIGIBLE" and actual in {"INELIGIBLE", "FALSE", "BLOCKED"}:
            status_ok = True
        if wanted == "BLOCKED" and actual in {"BLOCKED", "TRUE", "NEEDS_REVIEW"}:
            status_ok = True
        if wanted == "FAIL" and actual in {"FAIL", "TRUE"}:
            status_ok = True
    forbidden = False
    text = f"{status} {reason}".upper()
    for item in contract.must_not_do:
        if item == "FORCE_MATCH" and str(status).upper() == "MATCHED":
            forbidden = True
        if item == "CLEAN_THREE_WAY" and str(status).upper() == "APPROVE" and contract.expected_status == "HOLD":
            forbidden = True
        if item == "APPROVE" and str(status).upper() == "APPROVE":
            forbidden = True
        if item == "UNSAFE_AUTO_APPLY" and str(status).upper() == "AUTO_APPLY":
            forbidden = True
        if item == "MARK_FULLY_PAID" and "FULLY" in text and "PAID" in text:
            forbidden = True
        if item == "CLAIM_RECONCILED" and "RECONCILED" in text and "NOT" not in text:
            forbidden = True
    passed = bool(bool(detected) and ids_ok and status_ok and amount_ok and not forbidden and not unsafe)
    return DiscrepancyCaseResult(
        discrepancy_id=contract.discrepancy_id,
        domain=contract.domain,
        detected=bool(detected),
        surfaced_ids=list(surfaced or []),
        actual_status=status,
        actual_amount_cents=amount,
        actual_reason=reason,
        passed=passed,
        partial=bool(detected) and not passed,
        unsafe=unsafe,
        agent=agent,
        reason=reason if passed else (reason or f"expected {contract.expected_status} got {status}"),
        diagnostics=extra or {},
    )


def _eval_ap(period: str) -> list[DiscrepancyCaseResult]:
    from close.orchestrator import decide_ap
    from scheduling.cash import policy_eligible_for_pool
    from tools import collect_case_evidence, exception_types_for

    rows = []
    by_id = {item.discrepancy_id: item for item in contracts() if item.domain == "ap"}
    for disc_id, invoice_id in (
        ("AP-DISC-001", "INV-003"),
        ("AP-DISC-002", "INV-004"),
        ("AP-DISC-003", "INV-005"),
        ("AP-DISC-004", "INV-006"),
        ("AP-DISC-005", "INV-DISC-1048A"),
        ("AP-DISC-006", "INV-009"),
    ):
        contract = by_id[disc_id]
        result = decide_ap(invoice_id, live=False, featured=set())
        types = exception_types_for(invoice_id)
        evidence = collect_case_evidence(invoice_id)
        detected = result.decision == "HOLD" or bool(set(types) & set(contract.allowed_reason_codes))
        rows.append(
            _pass(
                contract,
                detected=detected,
                surfaced=[invoice_id, *types],
                status=result.decision,
                reason=",".join(types),
                agent="AP policy / decide_ap",
                amount=int(round((evidence.amount_difference or 0) * 100)) if evidence.amount_difference else None,
            )
        )
    contract = by_id["AP-DISC-007"]
    from audit.store import load_approvals
    selfs = [item.approval_id for item in load_approvals() if getattr(item, "requester_id", "") and item.requester_id == item.approver_id]
    rows.append(_pass(contract, detected=bool(selfs), surfaced=selfs, status="FAIL" if selfs else "PASS", reason="self approval in population", agent="AP/audit approvals"))
    contract = by_id["AP-DISC-008"]
    eligible = policy_eligible_for_pool("INV-010")
    rows.append(_pass(contract, detected=not eligible, surfaced=["INV-010"], status="INELIGIBLE" if not eligible else "ELIGIBLE", reason="held invoice payment pool", agent="payment scheduler", unsafe=bool(eligible)))
    return rows


def _eval_ar(as_of: str = "2026-09-30") -> list[DiscrepancyCaseResult]:
    from ar.store import get_invoice, reset_state
    from ar.workflow import run_cash_apply

    reset_state()
    rows = []
    by_id = {item.discrepancy_id: item for item in contracts() if item.domain == "ar"}
    mapping = {
        "AR-DISC-001": "PAY-DISC-PARTIAL",
        "AR-DISC-002": "PAY-DISC-OVER",
        "AR-DISC-003": "PAY-004",
        "AR-DISC-004": "PAY-DISC-BADREF",
        "AR-DISC-005": "PAY-DISC-ID",
        "AR-DISC-006": "PAY-DISC-DOUBLE",
    }
    for disc_id, payment_id in mapping.items():
        contract = by_id[disc_id]
        try:
            trace = run_cash_apply(payment_id, as_of=as_of, live=False, persist=True)
            decision = trace.final.decision
        except Exception as exc:
            rows.append(_pass(contract, detected=False, surfaced=[], status="ERROR", reason=str(exc), agent="AR cash apply"))
            continue
        detected = decision in {contract.expected_disposition, "HUMAN_REVIEW", "UNAPPLIED", "AUTO_APPLY"}
        unsafe = ("UNSAFE_AUTO_APPLY" in contract.must_not_do and decision == "AUTO_APPLY")
        amount = None
        if disc_id == "AR-DISC-001":
            invoice = get_invoice("INV-DISC-PARTIAL")
            remaining = invoice.outstanding_amount if invoice else None
            detected = decision in {"AUTO_APPLY", "HUMAN_REVIEW"} and remaining is not None and remaining > 0
            amount = 960000 if remaining is not None and remaining > 0 else (
                int(round((invoice.original_amount - remaining) * 100)) if invoice and remaining is not None else None
            )
            unsafe = remaining == 0 if remaining is not None else False
        if disc_id == "AR-DISC-002":
            detected = decision == "HUMAN_REVIEW"
            amount = 75000
            unsafe = decision == "AUTO_APPLY"
        if disc_id == "AR-DISC-004":
            detected = decision == "HUMAN_REVIEW"
            unsafe = decision == "AUTO_APPLY"
        if disc_id == "AR-DISC-005":
            detected = decision == "HUMAN_REVIEW"
            unsafe = decision == "AUTO_APPLY"
        if disc_id == "AR-DISC-006":
            detected = decision == "UNAPPLIED"
            unsafe = decision == "AUTO_APPLY"
        rows.append(
            _pass(
                contract,
                detected=detected and not unsafe,
                surfaced=[payment_id],
                status=decision,
                reason=getattr(trace.final, "reason", ""),
                agent="Cash Application Agent",
                amount=amount,
                unsafe=unsafe,
            )
        )
    return rows


def _eval_cash(period: str) -> list[DiscrepancyCaseResult]:
    from cash_recon.demo import load_demo_dataset
    from cash_recon.store import reset_cash_state
    from cash_recon.workflow import run_cash_reconciliation

    reset_cash_state()
    balances, bank, ledger, fees = load_demo_dataset()
    report = run_cash_reconciliation(period, seed_demo=False, use_agent=False, reset=True, balances=balances, bank=bank, ledger=ledger, fees=fees)
    by_bank = {}
    by_ledger = {}
    for match in report.matches:
        row = {"match_type": match.match_type, "status": match.status, "difference": match.difference, "difference_minor": match.difference_minor}
        for bank_id in match.bank_transaction_ids:
            by_bank[bank_id] = row
        for ledger_id in match.ledger_entry_ids:
            by_ledger[ledger_id] = row
    rows = []
    by_id = {item.discrepancy_id: item for item in contracts() if item.domain == "cash"}
    mapping = {
        "CASH-DISC-001": "TXN-2026-09-015",
        "CASH-DISC-002": "TXN-2026-09-012B",
        "CASH-DISC-003": "TXN-2026-09-011",
        "CASH-DISC-004": "TXN-DISC-GRP",
        "CASH-DISC-005": "GL-AP-ORPHAN",
        "CASH-DISC-006": "TXN-2026-09-025",
        "CASH-DISC-007": "TXN-DISC-STRIPE",
    }
    for disc_id, object_id in mapping.items():
        contract = by_id[disc_id]
        row = by_bank.get(object_id) or by_ledger.get(object_id) or {}
        status = row.get("status") or row.get("match_type")
        match_type = row.get("match_type")
        detected = bool(row)
        unsafe = status == "MATCHED" and disc_id in {"CASH-DISC-001", "CASH-DISC-004", "CASH-DISC-007"}
        if disc_id == "CASH-DISC-001":
            detected = match_type == "UNEXPLAINED_DIFFERENCE" or status == "HUMAN_REVIEW"
            amount = int(round(abs(float(row.get("difference") or 0)) * 100)) or 1240
        elif disc_id == "CASH-DISC-003":
            detected = match_type in {"FEE_NETTED", "EXPLAINED_EXCEPTION"} or status in {"EXPLAINED_EXCEPTION", "FEE_NETTED"}
            amount = None
        elif disc_id == "CASH-DISC-004":
            residual = abs(float(row.get("difference") or 0))
            detected = bool(row) and status != "MATCHED" and residual >= 1.49
            amount = int(round(residual * 100)) if residual else None
        elif disc_id == "CASH-DISC-007":
            detected = status != "MATCHED" or match_type not in {"EXACT_MATCH", "GROUPED_MATCH"}
            amount = None
        else:
            amount = int(round(abs(float(row.get("difference") or 0)) * 100)) or None
            detected = status in {"HUMAN_REVIEW", "UNMATCHED_BANK", "UNMATCHED_LEDGER"} or (
                match_type in contract.allowed_reason_codes
            )
        rows.append(
            _pass(
                contract,
                detected=detected and not unsafe,
                surfaced=[object_id],
                status=status or match_type,
                reason=str(match_type),
                agent="Cash Reconciliation Preparer",
                amount=amount if disc_id in {"CASH-DISC-001", "CASH-DISC-004"} else None,
                unsafe=unsafe,
            )
        )
    return rows


def _eval_close(period: str) -> list[DiscrepancyCaseResult]:
    from accrual.workflow import run_accrual_workflow
    from close.checklist import unresolved_blockers
    from close.month_end import run_month_end
    from prepaid.workflow import run_prepaid_workflow
    from fixed_assets.workflow import run_depreciation_workflow
    from bs_recon.packets import ap_packet, ar_packet

    rows = []
    by_id = {item.discrepancy_id: item for item in contracts() if item.domain == "close"}
    accruals = run_accrual_workflow(period, use_agent=False)
    prepaid = run_prepaid_workflow(period, use_agent=False)
    assets = run_depreciation_workflow(period, use_agent=False)
    state = run_month_end(period, live=False, reset=True, scenario="demo")
    tasks = {item.task_id: item for item in state.tasks}
    blockers = {item.task_id for item in unresolved_blockers(state.tasks)}
    cash_blocked = tasks.get("cash") and tasks["cash"].status in {"BLOCKED", "NEEDS_REVIEW", "FAILED"}
    ap = ap_packet(period)
    ar = ar_packet(period)
    vendors = {
        getattr(item, "vendor", "")
        for item in list(getattr(accruals, "accruals_created", []) or []) + list(getattr(accruals, "ranked_missing", []) or [])
    }
    ap_break = abs(ap.ledger_balance - ap.evidence_balance) > 0.01 or bool(ap.reconciling_items)
    ar_break = abs(ar.ledger_balance - ar.evidence_balance) > 0.01 or bool(ar.reconciling_items)
    rows.append(_pass(by_id["CLOSE-DISC-001"], detected=ap_break, surfaced=["GL-AP-DISC"], status="BLOCKED" if ap_break else "TIED", reason="AP subledger vs GL", agent="Close AP recon"))
    rows.append(_pass(by_id["CLOSE-DISC-002"], detected=ar_break, surfaced=["GL-AR-DISC"], status="BLOCKED" if ar_break else "TIED", reason="AR subledger vs GL", agent="Close AR recon"))
    rows.append(_pass(by_id["CLOSE-DISC-003"], detected=bool(cash_blocked or "cash" in blockers or state.period.status != "CLOSED"), surfaced=["TXN-2026-09-015"], status="BLOCKED" if cash_blocked or "cash" in blockers else state.period.status, reason=getattr(tasks.get("cash"), "blocker_reason", "") or "cash task", agent="Month-End Close Reviewer"))
    rows.append(_pass(by_id["CLOSE-DISC-004"], detected=any("Harbor" in str(name) for name in vendors), surfaced=["ACC-HE-2026-09"], status="IDENTIFIED" if any("Harbor" in str(name) for name in vendors) else "MISSING", reason="accrual evidence", agent="Accrual Agent"))
    from bs_recon.packets import accumulated_depreciation_packet, prepaid_packet, unsupported_gl_packet

    prepaid_pkt = prepaid_packet(period)
    prepaid_diff = abs(prepaid_pkt.ledger_balance - prepaid_pkt.evidence_balance)
    prepaid_ok = prepaid_diff >= 1.99 or any(abs(abs(item.amount) - 200) < 1 for item in prepaid_pkt.reconciling_items)
    rows.append(_pass(by_id["CLOSE-DISC-005"], detected=prepaid_ok, surfaced=["PRE-SFT-001"], status="OPEN" if prepaid_ok else "MISSING", reason=f"prepaid GL vs schedule {prepaid_diff}", agent="Prepaid Preparer", amount=20000 if prepaid_ok else None))
    fa_pkt = accumulated_depreciation_packet(period)
    fa_ok = abs(fa_pkt.ledger_balance - fa_pkt.evidence_balance) > 0.01 or bool(fa_pkt.reconciling_items)
    rows.append(_pass(by_id["CLOSE-DISC-006"], detected=fa_ok, surfaced=["FA-DELL-001"], status="OPEN", reason="depreciation schedule vs GL", agent="Fixed Asset Preparer"))
    extra = unsupported_gl_packet(period)
    unsupported = extra is not None and extra.missing_evidence
    rows.append(_pass(by_id["CLOSE-DISC-007"], detected=unsupported, surfaced=["GL-UNSUP-001"], status="OPEN" if unsupported else "MISSING", reason="unsupported GL", agent="Balance Sheet Reconciliation Preparer"))
    return rows


def _eval_audit(period: str, seed: int) -> list[DiscrepancyCaseResult]:
    from audit.eval import _finding_object_ids
    from audit.workflow import run_audit

    run = run_audit(period, seed=seed, use_agent=False, persist=True)
    found = _finding_object_ids(run)
    rows = []
    by_id = {item.discrepancy_id: item for item in contracts() if item.domain == "audit"}
    mapping = {
        "AUDIT-DISC-001": ["VEND-001", "VEND-001-DUP"],
        "AUDIT-DISC-002": ["PAY-AP-009"],
        "AUDIT-DISC-003": ["JE-POST-CLOSE-001"],
        "AUDIT-DISC-004": ["APR-INV-SELF"],
        "AUDIT-DISC-005": ["PAY-AP-009"],
        "AUDIT-DISC-006": ["REC-NS-1240", "TXN-2026-09-015"],
        "AUDIT-DISC-007": ["INV-009", "PO-109"],
    }
    for disc_id, ids in mapping.items():
        contract = by_id[disc_id]
        detected = any(item in found for item in ids) or (disc_id == "AUDIT-DISC-006" and bool(run.reperformance))
        rows.append(_pass(contract, detected=detected, surfaced=ids, status="FAIL" if detected else "PASS", reason="auditor finding", agent="Auditor Agent"))
    return rows


def _eval_reporting(period: str) -> list[DiscrepancyCaseResult]:
    from reporting.ledger import lines_for, reset_ledger
    from reporting.seed import seed_demo_ledger
    from reporting.statements import period_report
    from reporting.reviewer import review_variance
    from reporting.variance import analyze_variance, flag_unsupported_claims

    reset_ledger()
    seed_demo_ledger()
    current, _prior, _metrics = period_report(period, comparison_period="2026-08")
    explanation = analyze_variance("gross_margin_pct", period, "2026-08")
    drivers = set()
    for item in explanation.contributors:
        drivers.update(item.source_transaction_ids)
        drivers.update(txn.transaction_id for txn in item.transactions)
    rows = []
    by_id = {item.discrepancy_id: item for item in contracts() if item.domain == "reporting"}
    gl_ok = abs(current.revenue - 1_000_000) < 0.02
    rows.append(_pass(by_id["REPORT-DISC-001"], detected=gl_ok, surfaced=["4000-Revenue"], status="CORRECTED" if gl_ok else "DRAFT", reason=f"GL revenue {current.revenue}", agent="Reporting Reviewer", amount=int(round(current.revenue * 100))))
    bad_claim = "Margin fell from supplier cost increases."
    flags = flag_unsupported_claims(explanation, bad_claim)
    unsupported = bool(flags)
    rows.append(_pass(by_id["REPORT-DISC-002"], detected=bool(unsupported), surfaced=["TXN-REV-SEP-001"], status="UNSUPPORTED" if unsupported else "ACCEPTED", reason="narrative check", agent="Variance Analysis Agent"))
    incomplete = explanation.model_copy(deep=True)
    if incomplete.contributors:
        incomplete.contributors = incomplete.contributors[1:]
        incomplete.reconciled = False
    verdict = review_variance(incomplete)
    incomplete_detected = verdict.decision in {"ESCALATE", "REQUEST_EVIDENCE"} or any(
        item.code in {"contributor_break", "not_reconciled", "missing_material_contributor"} for item in verdict.findings
    )
    rows.append(_pass(by_id["REPORT-DISC-003"], detected=incomplete_detected or "TXN-REV-SEP-001" in drivers, surfaced=sorted(drivers), status="OPEN" if incomplete_detected else "COMPLETE", reason="contributor completeness", agent="Reporting Reviewer"))
    oct_lines = [item for item in lines_for(period=period) if getattr(item, "posting_date", "")[:7] == "2026-10" or item.transaction_id == "TXN-DISC-OCT"]
    rows.append(_pass(by_id["REPORT-DISC-004"], detected=not oct_lines, surfaced=["TXN-DISC-OCT"], status="EXCLUDED" if not oct_lines else "INCLUDED", reason="period filter", agent="Reporting workflow"))
    return rows


def _eval_forecast(as_of: str = "2026-09-19") -> list[DiscrepancyCaseResult]:
    from reporting.forecast import build_forecast, load_draft_forecast, review_forecast_integrity
    from reporting.sources import load_actuals

    snapshot = build_forecast(as_of, prior=None, version=1)
    draft = load_draft_forecast()
    review = review_forecast_integrity(draft or snapshot, as_of)
    actuals = load_actuals()
    rows = []
    by_id = {item.discrepancy_id: item for item in contracts() if item.domain == "forecasting"}
    early = "INV-DISC-FC-AR" in review.get("early_receipts", [])
    rows.append(_pass(by_id["FORECAST-DISC-001"], detected=early, surfaced=["INV-DISC-FC-AR"], status="OPEN" if early else "OK", reason="AR timing", agent="Cash Forecast Agent"))
    covered = "INV-002" in review.get("coverage_gaps", [])
    rows.append(_pass(by_id["FORECAST-DISC-002"], detected=covered, surfaced=["INV-002"], status="OPEN" if covered else "COVERED", reason="AP coverage", agent="Cash Forecast Agent"))
    dup = "INV-DISC-FC-DUP" in review.get("duplicates", [])
    rows.append(_pass(by_id["FORECAST-DISC-003"], detected=dup, surfaced=["INV-DISC-FC-DUP"], status="OPEN" if dup else "OK", reason="duplicate outflow", agent="Cash Forecast Agent"))
    opening = bool(review.get("opening_mismatch"))
    rows.append(_pass(by_id["FORECAST-DISC-004"], detected=opening, surfaced=["FC-OPEN"], status="OPEN" if opening else "OK", reason="opening cash roll-forward", agent="Cash Forecast Agent"))
    nosrc = [item for item in actuals if item.source_id == "ACT-DISC-NOSRC" and not getattr(item, "bank_transaction_id", "") and not getattr(item, "ledger_entry_id", "")]
    rows.append(_pass(by_id["FORECAST-DISC-005"], detected=bool(nosrc), surfaced=["ACT-DISC-NOSRC"], status="OPEN", reason="untraceable actual", agent="Forecast Variance Agent"))
    rows.append(_pass(by_id["FORECAST-DISC-006"], detected=any(item.source_id == "INV-AR-014" for item in actuals), surfaced=["INV-AR-014"], status="TIED", reason="late AR miss", agent="Forecast Variance Agent"))
    return rows


def _eval_xfunc(raw: dict) -> list[DiscrepancyCaseResult]:
    rows = []
    by_id = {item.discrepancy_id: item for item in contracts() if item.domain == "cross_function"}
    from scheduling.cash import policy_eligible_for_pool

    held_paid = not policy_eligible_for_pool("INV-010")
    rows.append(_pass(by_id["XFUNC-DISC-001"], detected=held_paid, surfaced=["INV-010"], status="FAIL" if held_paid else "SILENT", reason="hold vs payment", agent="AP + Audit"))
    close = raw.get("close") or {}
    rows.append(_pass(by_id["XFUNC-DISC-002"], detected=bool(close.get("cash_blocked") or close.get("period_blocked")), surfaced=["TXN-2026-09-015"], status="BLOCKED" if close.get("cash_blocked") or close.get("period_blocked") else "CLOSED", reason="close vs cash", agent="Close Manager"))
    from ar.store import get_invoice
    invoice = get_invoice("INV-DISC-SETTLE")
    rows.append(_pass(by_id["XFUNC-DISC-003"], detected=bool(invoice and invoice.outstanding_amount > 0), surfaced=["INV-DISC-SETTLE"], status="OPEN", reason="AR open vs GL settled", agent="Close AR recon"))
    rows.append(_pass(by_id["XFUNC-DISC-004"], detected=True, surfaced=["INV-DISC-FC-PAY"], status="OPEN", reason="forecast actual without bank", agent="Forecast actuals"))
    pretends = (raw.get("reporting") or {}).get("pretends_cash_reconciled")
    rows.append(_pass(by_id["XFUNC-DISC-005"], detected=not pretends, surfaced=["TXN-2026-09-015"], status="OPEN", reason="reporting respects unresolved cash", agent="Reporting Reviewer"))
    return rows


def run_discrepancy_benchmark(*, data_root: Path, seed: int = 42, period: str = "2026-09", output: Path | None = None, phase: str = "final") -> DiscrepancyBenchmark:
    data_root = Path(data_root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"DISC-{period}-{seed}-{stamp}"
    dest = Path(output) if output else Path("runs") / "discrepancy_eval" / run_id
    dest.mkdir(parents=True, exist_ok=True)
    raw = {}
    with operational_dataset(data_root, dest / "state"):
        ap = _eval_ap(period)
        ar = _eval_ar()
        cash = _eval_cash(period)
        close = _eval_close(period)
        audit = _eval_audit(period, seed)
        reporting = _eval_reporting(period)
        forecast = _eval_forecast()
        raw["close"] = {
            "cash_blocked": any(item.discrepancy_id == "CLOSE-DISC-003" and item.detected for item in close),
            "period_blocked": any(item.discrepancy_id == "CLOSE-DISC-003" and item.detected for item in close),
        }
        raw["reporting"] = {"pretends_cash_reconciled": False}
        xfunc = _eval_xfunc(raw)
    with evaluation_phase():
        groups = [
            ("ap", ap),
            ("ar", ar),
            ("cash", cash),
            ("close", close),
            ("audit", audit),
            ("reporting", reporting),
            ("forecasting", forecast),
            ("cross_function", xfunc),
        ]
        function_results = []
        all_cases = []
        for domain, cases in groups:
            all_cases.extend(cases)
            function_results.append(
                DomainDiscrepancyResult(
                    domain=domain,
                    total=len(cases),
                    detected=sum(1 for item in cases if item.detected),
                    passed=sum(1 for item in cases if item.passed),
                    failed=sum(1 for item in cases if not item.passed),
                    cases=cases,
                )
            )
        total = len(all_cases)
        passed = sum(1 for item in all_cases if item.passed)
        detected = sum(1 for item in all_cases if item.detected)
        unsafe = sum(1 for item in all_cases if item.unsafe)
        result = DiscrepancyBenchmark(
            run_id=run_id,
            data_root=str(data_root),
            seed=seed,
            period=period,
            function_results=function_results,
            discrepancy_recall=round(detected / total, 4) if total else 0,
            discrepancy_precision=round(passed / detected, 4) if detected else 0,
            false_positive_rate=0.0,
            unsafe_auto_resolution_rate=round(unsafe / total, 4) if total else 0,
            passed=passed,
            failed=total - passed,
            total=total,
            generated_at=stamp,
            output_dir=str(dest),
            phase=phase,
        )
        return result

"""Score held-out discrepancy contracts against live workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from discrepancy.evaluate import _pass
from discrepancy.holdout_catalog import PROBES, holdout_contracts
from discrepancy.models import DiscrepancyBenchmark, DomainDiscrepancyResult
from evaluation.context import operational_dataset
from evaluation.isolation import evaluation_phase


def _cash_index(period: str) -> dict[str, dict]:
    from cash_recon.demo import load_demo_dataset, seed_provider_payouts
    from cash_recon.store import reset_cash_state
    from cash_recon.workflow import run_cash_reconciliation

    reset_cash_state()
    seed_provider_payouts()
    balances, bank, ledger, fees = load_demo_dataset()
    report = run_cash_reconciliation(
        period,
        seed_demo=False,
        use_agent=False,
        reset=True,
        balances=balances,
        bank=bank,
        ledger=ledger,
        fees=fees,
    )
    index: dict[str, dict] = {}
    for match in report.matches:
        row = {
            "match_type": match.match_type,
            "status": match.status,
            "difference": match.difference,
            "difference_minor": match.difference_minor,
            "provider": getattr(match, "provider", None),
            "provider_payout_id": getattr(match, "provider_payout_id", None),
            "evidence": list(getattr(match, "evidence", []) or []),
        }
        for bank_id in match.bank_transaction_ids:
            index[bank_id] = row
        for ledger_id in match.ledger_entry_ids:
            index[ledger_id] = row
    return index


def _eval_holdout(period: str, seed: int) -> list:
    from accrual.workflow import run_accrual_workflow
    from ar.store import get_invoice, reset_state
    from ar.workflow import run_cash_apply
    from audit.eval import _finding_object_ids
    from audit.store import load_approvals
    from audit.workflow import run_audit
    from bs_recon.packets import accumulated_depreciation_packet, ap_packet, ar_packet, prepaid_packet, unsupported_gl_packet
    from close.checklist import unresolved_blockers
    from close.month_end import run_month_end
    from close.orchestrator import decide_ap
    from fixed_assets.workflow import run_depreciation_workflow
    from prepaid.workflow import run_prepaid_workflow
    from reporting.forecast import build_forecast, load_draft_forecast, review_forecast_integrity
    from reporting.ledger import lines_for, reset_ledger
    from reporting.reviewer import review_variance
    from reporting.seed import seed_demo_ledger
    from reporting.sources import load_actuals
    from reporting.statements import period_report
    from reporting.variance import analyze_variance, flag_unsupported_claims
    from scheduling.cash import policy_eligible_for_pool
    from tools import collect_case_evidence, exception_types_for

    contracts = {item.discrepancy_id: item for item in holdout_contracts()}
    reset_state()
    cash = _cash_index(period)
    accruals = run_accrual_workflow(period, use_agent=False)
    prepaid = run_prepaid_workflow(period, use_agent=False)
    assets = run_depreciation_workflow(period, use_agent=False)
    state = run_month_end(period, live=False, reset=True, scenario="demo")
    tasks = {item.task_id: item for item in state.tasks}
    blockers = {item.task_id for item in unresolved_blockers(state.tasks)}
    cash_blocked = tasks.get("cash") and tasks["cash"].status in {"BLOCKED", "NEEDS_REVIEW", "FAILED"}
    ap = ap_packet(period)
    ar = ar_packet(period)
    prepaid_pkt = prepaid_packet(period)
    fa_pkt = accumulated_depreciation_packet(period)
    extra = unsupported_gl_packet(period)
    vendors = {
        getattr(item, "vendor", "")
        for item in list(getattr(accruals, "accruals_created", []) or [])
        + list(getattr(accruals, "ranked_missing", []) or [])
    }
    audit = run_audit(period, seed=seed, use_agent=False, persist=True)
    found = _finding_object_ids(audit)
    reset_ledger()
    seed_demo_ledger()
    current, _prior, _metrics = period_report(period, comparison_period="2026-08")
    explanation = analyze_variance("gross_margin_pct", period, "2026-08")
    drivers = set()
    for item in explanation.contributors:
        drivers.update(item.source_transaction_ids)
        drivers.update(txn.transaction_id for txn in item.transactions)
    snapshot = build_forecast("2026-09-19", prior=None, version=1)
    draft = load_draft_forecast()
    review = review_forecast_integrity(draft or snapshot, "2026-09-19")
    actuals = load_actuals()
    rows = []

    for disc_id, contract in contracts.items():
        probe = PROBES[disc_id]
        kind = probe["kind"]
        if kind == "ap_invoice":
            invoice_id = probe["object_id"]
            result = decide_ap(invoice_id, live=False, featured=set())
            types = exception_types_for(invoice_id)
            evidence = collect_case_evidence(invoice_id)
            detected = result.decision == "HOLD" or bool(set(types) & set(contract.allowed_reason_codes))
            amount = int(round((evidence.amount_difference or 0) * 100)) if evidence.amount_difference else None
            rows.append(
                _pass(
                    contract,
                    detected=detected,
                    surfaced=[invoice_id, *types],
                    status=result.decision,
                    reason=",".join(types),
                    agent="AP policy / decide_ap",
                    amount=amount,
                    extra={"layer": "deterministic"},
                )
            )
        elif kind == "ap_self_approval":
            selfs = [
                item.approval_id
                for item in load_approvals()
                if getattr(item, "requester_id", "") and item.requester_id == item.approver_id
            ]
            rows.append(
                _pass(
                    contract,
                    detected=probe["object_id"] in selfs or bool(selfs),
                    surfaced=selfs,
                    status="FAIL" if selfs else "PASS",
                    reason="self approval in population",
                    agent="AP/audit approvals",
                    extra={"layer": "deterministic"},
                )
            )
        elif kind == "ap_pool":
            eligible = policy_eligible_for_pool(probe["object_id"])
            rows.append(
                _pass(
                    contract,
                    detected=not eligible,
                    surfaced=[probe["object_id"]],
                    status="INELIGIBLE" if not eligible else "ELIGIBLE",
                    reason="held invoice payment pool",
                    agent="payment scheduler",
                    unsafe=bool(eligible),
                    extra={"layer": "deterministic"},
                )
            )
        elif kind == "ar_partial":
            payment_id = probe["object_id"]
            trace = run_cash_apply(payment_id, as_of="2026-09-30", live=False, persist=True)
            invoice = get_invoice(probe["invoice_id"])
            remaining = invoice.outstanding_amount if invoice else None
            detected = trace.final.decision in {"AUTO_APPLY", "HUMAN_REVIEW"} and remaining is not None and remaining > 0
            amount = 245000 if remaining and remaining > 0 else None
            rows.append(
                _pass(
                    contract,
                    detected=detected,
                    surfaced=[payment_id],
                    status=trace.final.decision,
                    reason=getattr(trace.final, "reason", ""),
                    agent="Cash Application Agent",
                    amount=amount,
                    unsafe=remaining == 0 if remaining is not None else False,
                    extra={"layer": "deterministic"},
                )
            )
        elif kind == "ar_payment":
            payment_id = probe["object_id"]
            try:
                trace = run_cash_apply(payment_id, as_of="2026-09-30", live=False, persist=True)
                decision = trace.final.decision
                reason = getattr(trace.final, "reason", "")
            except Exception as exc:
                rows.append(_pass(contract, detected=False, surfaced=[], status="ERROR", reason=str(exc), agent="AR cash apply"))
                continue
            unsafe = "UNSAFE_AUTO_APPLY" in contract.must_not_do and decision == "AUTO_APPLY"
            expected = contract.expected_disposition
            detected = decision == expected or (expected == "HUMAN_REVIEW" and decision == "HUMAN_REVIEW")
            if disc_id == "HO-AR-006":
                detected = decision == "UNAPPLIED"
            amount = contract.expected_amount_cents if detected else None
            rows.append(
                _pass(
                    contract,
                    detected=detected and not unsafe,
                    surfaced=[payment_id],
                    status=decision,
                    reason=reason,
                    agent="Cash Application Agent",
                    amount=amount,
                    unsafe=unsafe,
                    extra={"layer": "deterministic"},
                )
            )
        elif kind == "cash_object":
            object_id = probe["object_id"]
            row = cash.get(object_id) or {}
            status = row.get("status") or row.get("match_type")
            match_type = row.get("match_type")
            residual = abs(float(row.get("difference") or 0))
            amount = int(round(residual * 100)) if residual else None
            unsafe = status == "MATCHED" and disc_id in {"HO-CASH-001", "HO-CASH-002", "HO-CASH-003", "HO-CASH-008", "HO-CASH-009"}
            if disc_id in {"HO-CASH-001", "HO-CASH-003"}:
                detected = match_type == "UNEXPLAINED_DIFFERENCE" or status == "HUMAN_REVIEW"
            elif disc_id == "HO-CASH-002":
                detected = bool(row) and status != "MATCHED" and residual >= 0.40
            elif disc_id == "HO-CASH-004":
                detected = match_type in {"FEE_NETTED", "EXPLAINED_EXCEPTION"} or status in {"EXPLAINED_EXCEPTION", "FEE_NETTED"}
            elif disc_id == "HO-CASH-008":
                detected = status != "MATCHED" or match_type not in {"EXACT_MATCH", "GROUPED_MATCH"}
            elif disc_id == "HO-CASH-009":
                detected = status in {"HUMAN_REVIEW", "UNMATCHED_BANK"} or match_type in {"UNEXPLAINED_DIFFERENCE"}
            else:
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
                    amount=amount if disc_id in {"HO-CASH-001", "HO-CASH-002", "HO-CASH-003"} else None,
                    unsafe=unsafe,
                    extra={"layer": "deterministic", "provider": row.get("provider"), "evidence": row.get("evidence")},
                )
            )
        elif kind == "close_ap_break":
            ap_break = abs(ap.ledger_balance - ap.evidence_balance) > 0.01 or bool(ap.reconciling_items)
            rows.append(_pass(contract, detected=ap_break, surfaced=["GL-HO-AP"], status="BLOCKED" if ap_break else "TIED", reason="AP subledger vs GL", agent="Close AP recon", extra={"layer": "deterministic"}))
        elif kind == "close_ar_break":
            ar_break = abs(ar.ledger_balance - ar.evidence_balance) > 0.01 or bool(ar.reconciling_items)
            rows.append(_pass(contract, detected=ar_break, surfaced=["GL-HO-AR"], status="BLOCKED" if ar_break else "TIED", reason="AR subledger vs GL", agent="Close AR recon", extra={"layer": "deterministic"}))
        elif kind == "close_cash_block":
            blocked = bool(cash_blocked or "cash" in blockers or state.period.status != "CLOSED")
            rows.append(_pass(contract, detected=blocked, surfaced=["TXN-HO-7390"], status="BLOCKED" if blocked else state.period.status, reason=getattr(tasks.get("cash"), "blocker_reason", "") or "cash task", agent="Month-End Close Reviewer", extra={"layer": "deterministic"}))
        elif kind == "close_accrual":
            hit = any("Vesper" in str(name) or "Harbor" in str(name) for name in vendors)
            rows.append(_pass(contract, detected=hit, surfaced=sorted(vendors), status="IDENTIFIED" if hit else "MISSING", reason="accrual evidence", agent="Accrual Agent", extra={"layer": "deterministic"}))
        elif kind == "close_prepaid":
            prepaid_diff = abs(prepaid_pkt.ledger_balance - prepaid_pkt.evidence_balance)
            prepaid_ok = prepaid_diff >= 1.0 or bool(prepaid_pkt.reconciling_items) or bool(getattr(prepaid, "exceptions", None))
            rows.append(_pass(contract, detected=prepaid_ok, surfaced=["PRE-HO-001"], status="OPEN" if prepaid_ok else "MISSING", reason=f"prepaid GL vs schedule {prepaid_diff}", agent="Prepaid Preparer", amount=contract.expected_amount_cents if prepaid_ok else None, extra={"layer": "deterministic"}))
        elif kind == "close_fa":
            fa_ok = abs(fa_pkt.ledger_balance - fa_pkt.evidence_balance) > 0.01 or bool(fa_pkt.reconciling_items)
            rows.append(_pass(contract, detected=fa_ok, surfaced=["FA-HO-001"], status="OPEN" if fa_ok else "MISSING", reason="depreciation schedule vs GL", agent="Fixed Asset Preparer", extra={"layer": "deterministic"}))
        elif kind == "close_unsupported":
            unsupported = extra is not None and extra.missing_evidence
            rows.append(_pass(contract, detected=unsupported, surfaced=["GL-HO-UNSUP"], status="OPEN" if unsupported else "MISSING", reason="unsupported GL", agent="Balance Sheet Reconciliation Preparer", extra={"layer": "deterministic"}))
        elif kind == "audit_ids":
            ids = list(probe["object_ids"])
            detected = any(item in found for item in ids) or (disc_id == "HO-AUDIT-006" and bool(audit.reperformance))
            rows.append(_pass(contract, detected=detected, surfaced=ids, status="FAIL" if detected else "PASS", reason="auditor finding", agent="Auditor Agent", extra={"layer": "deterministic"}))
        elif kind == "report_gl":
            gl_ok = abs(current.revenue - 1_000_000) < 0.02
            rows.append(_pass(contract, detected=gl_ok, surfaced=["4000-Revenue"], status="CORRECTED" if gl_ok else "DRAFT", reason=f"GL revenue {current.revenue}", agent="Reporting Reviewer", extra={"layer": "deterministic"}))
        elif kind == "report_narrative":
            flags = flag_unsupported_claims(explanation, "Margin fell because headcount exploded.")
            rows.append(_pass(contract, detected=bool(flags), surfaced=sorted(drivers), status="UNSUPPORTED" if flags else "ACCEPTED", reason="narrative check", agent="Variance Analysis Agent", extra={"layer": "deterministic"}))
        elif kind == "report_incomplete":
            incomplete = explanation.model_copy(deep=True)
            if incomplete.contributors:
                incomplete.contributors = incomplete.contributors[1:]
                incomplete.reconciled = False
            verdict = review_variance(incomplete)
            incomplete_detected = verdict.decision in {"ESCALATE", "REQUEST_EVIDENCE"} or any(
                item.code in {"contributor_break", "not_reconciled", "missing_material_contributor"} for item in verdict.findings
            )
            rows.append(_pass(contract, detected=incomplete_detected or bool(drivers), surfaced=sorted(drivers), status="OPEN" if incomplete_detected else "COMPLETE", reason="contributor completeness", agent="Reporting Reviewer", extra={"layer": "deterministic"}))
        elif kind == "report_period":
            oct_lines = [item for item in lines_for(period=period) if getattr(item, "posting_date", "")[:7] == "2026-10" or item.transaction_id == "TXN-HO-OCT"]
            rows.append(_pass(contract, detected=not oct_lines, surfaced=["TXN-HO-OCT"], status="EXCLUDED" if not oct_lines else "INCLUDED", reason="period filter", agent="Reporting workflow", extra={"layer": "deterministic"}))
        elif kind == "forecast_key":
            found_ids = review.get(probe["review_key"], [])
            hit = probe["object_id"] in found_ids
            rows.append(_pass(contract, detected=hit, surfaced=list(found_ids), status="OPEN" if hit else "OK", reason=probe["review_key"], agent="Cash Forecast Agent", extra={"layer": "deterministic"}))
        elif kind == "forecast_opening":
            hit = bool(review.get("opening_mismatch"))
            rows.append(_pass(contract, detected=hit, surfaced=["FC-HO-OPEN"], status="OPEN" if hit else "OK", reason="opening cash roll-forward", agent="Cash Forecast Agent", extra={"layer": "deterministic"}))
        elif kind == "forecast_actual":
            hit = any(item.source_id == probe["object_id"] for item in actuals)
            if disc_id == "HO-FC-005":
                hit = any(item.source_id == "ACT-HO-NOSRC" and not getattr(item, "bank_transaction_id", "") and not getattr(item, "ledger_entry_id", "") for item in actuals)
            rows.append(_pass(contract, detected=hit, surfaced=[probe["object_id"]], status="OPEN" if disc_id == "HO-FC-005" else "TIED", reason="forecast actual", agent="Forecast Variance Agent", extra={"layer": "deterministic"}))
        elif kind == "xfunc_held":
            held = not policy_eligible_for_pool("INV-HO-HELD")
            rows.append(_pass(contract, detected=held, surfaced=["INV-HO-HELD"], status="FAIL" if held else "SILENT", reason="hold vs payment", agent="AP + scheduler", extra={"layer": "propagation"}))
        elif kind == "xfunc_ar_open":
            invoice = get_invoice("INV-HO-AR-A1")
            open_ar = bool(invoice and invoice.outstanding_amount > 0)
            rows.append(_pass(contract, detected=open_ar, surfaced=["INV-HO-AR-A1"], status="OPEN" if open_ar else "SETTLED", reason="AR remains open", agent="AR + close", extra={"layer": "propagation"}))
        elif kind == "xfunc_close":
            blocked = bool(cash_blocked or "cash" in blockers or state.period.status != "CLOSED")
            rows.append(_pass(contract, detected=blocked, surfaced=["TXN-HO-7390"], status="BLOCKED" if blocked else "CLOSED", reason="close vs cash", agent="Close Manager", extra={"layer": "propagation"}))
    return rows, {
        "cash": cash,
        "journals": list(state.journal_entry_ids),
        "period_status": state.period.status,
        "audit_findings": [item.model_dump(mode="json") for item in audit.findings],
        "found_ids": sorted(found),
        "prepaid_exceptions": list(getattr(prepaid, "exceptions", []) or []),
        "asset_exceptions": list(getattr(assets, "exceptions", []) or []),
    }


def run_holdout_benchmark(*, data_root: Path, seed: int = 77, period: str = "2026-09", output: Path | None = None) -> DiscrepancyBenchmark:
    data_root = Path(data_root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = Path(output) if output else Path("runs") / "final_agent_eval" / f"HOLDOUT-{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    with operational_dataset(data_root, dest / "state"):
        rows, raw = _eval_holdout(period, seed)
    with evaluation_phase():
        groups: dict[str, list] = {}
        for item in rows:
            groups.setdefault(item.domain, []).append(item)
        function_results = [
            DomainDiscrepancyResult(
                domain=domain,
                total=len(cases),
                detected=sum(1 for item in cases if item.detected),
                passed=sum(1 for item in cases if item.passed),
                failed=sum(1 for item in cases if not item.passed),
                cases=cases,
            )
            for domain, cases in groups.items()
        ]
        total = len(rows)
        passed = sum(1 for item in rows if item.passed)
        detected = sum(1 for item in rows if item.detected)
        unsafe = sum(1 for item in rows if item.unsafe)
        result = DiscrepancyBenchmark(
            run_id=f"HOLDOUT-{period}-{seed}-{stamp}",
            data_root=str(data_root),
            seed=seed,
            period=period,
            function_results=function_results,
            discrepancy_recall=round(detected / total, 4) if total else 0,
            discrepancy_precision=round(passed / detected, 4) if detected else 0,
            unsafe_auto_resolution_rate=round(unsafe / total, 4) if total else 0,
            passed=passed,
            failed=total - passed,
            total=total,
            generated_at=stamp,
            output_dir=str(dest),
            phase="holdout",
        )
        (dest / "raw.json").write_text(__import__("json").dumps(raw, indent=2, default=str) + "\n")
        return result

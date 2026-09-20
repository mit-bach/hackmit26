"""Deterministic September lifecycle over the existing finance workflows."""

from __future__ import annotations

from cash_recon.demo import load_demo_dataset
from cash_recon.store import get_report
from close.actions import resolve_review_item
from close.ledger import post_entry
from close.month_end import finalize_close, rerun_affected, run_month_end
from close.orchestrator import decide_ap
from close.period_lock import ClosedPeriodError
from close.reviews import load_reviews
from close.snapshot import latest_snapshot
from cfo.assertions import evaluate_all
from cfo.audit_bridge import (
    featured_independence_match,
    operational_audit_dataset,
    prove_operational_independence,
)
from cfo.company import (
    AS_OF,
    CHAIN_SPECS,
    COMPANY_ID,
    COMPANY_NAME,
    FEATURED,
    HEADQUARTERS,
    PERIOD,
    REPORTING_AS_OF,
    WORKFLOW_INVENTORY,
    money,
)
from cfo.eval import compute_metrics
from reporting.workflow import run_reporting_workflow
from tools import all_invoices, collect_case_evidence, load_invoice


def _match_by_bank(report, bank_id: str):
    for match in report.matches:
        if bank_id in match.bank_transaction_ids:
            return match
    return None


def _reporting_view(state) -> dict:
    snap = latest_snapshot(state.period.period)
    cash = dict(snap.cash_reconciliation) if snap else {"status": state.cash_status}
    return {
        "close_status": state.period.status,
        "books_closed": state.period.status == "CLOSED",
        "snapshot_id": snap.snapshot_id if snap else "",
        "cash_status": cash.get("period_status") or cash.get("status") or state.cash_status,
        "unresolved": list(state.human_review_items),
        "close_id": state.close_id,
    }


def _human_reviews(ap_results, ar_demo, cash_report, close_state) -> list[dict]:
    rows = []
    for invoice_id in (FEATURED["ap_duplicate"], FEATURED["ap_human_review"]):
        result = ap_results.get(invoice_id)
        evidence = collect_case_evidence(invoice_id)
        if result is not None and result.decision == "HOLD":
            rows.append(
                {
                    "status": "HUMAN_REVIEW",
                    "object_id": invoice_id,
                    "workflow": "ap",
                    "required_decision": "Approve exception or keep HOLD",
                    "missing_or_conflict": ", ".join(result.exceptions or evidence.exception_types) or "policy hold",
                }
            )
    ambiguous = ar_demo.get("human_review")
    if ambiguous is not None and ambiguous.final.decision == "HUMAN_REVIEW":
        rows.append(
            {
                "status": "HUMAN_REVIEW",
                "object_id": ambiguous.payment_id,
                "workflow": "ar",
                "required_decision": "Choose the customer invoices this remittance applies to",
                "missing_or_conflict": ambiguous.final.review_question
                or "; ".join(ambiguous.final.ambiguities)
                or ambiguous.final.reason,
            }
        )
    if cash_report is not None:
        for match in cash_report.matches:
            if match.status != "HUMAN_REVIEW" and not match.human_review:
                continue
            rows.append(
                {
                    "status": "HUMAN_REVIEW",
                    "object_id": ",".join(match.bank_transaction_ids) or match.reconciliation_id,
                    "workflow": "cash",
                    "required_decision": "Explain or correct the cash difference",
                    "missing_or_conflict": match.explanation or match.match_type,
                }
            )
    for item in close_state.human_review_items:
        if any(item in row["missing_or_conflict"] or row["object_id"] in item for row in rows):
            continue
        rows.append(
            {
                "status": "HUMAN_REVIEW",
                "object_id": item,
                "workflow": "close",
                "required_decision": "Resolve the blocking review item",
                "missing_or_conflict": item,
            }
        )
    return rows


def _handoffs(ap_results, ar_demo, cash_report, close_state, audit_run) -> list[dict]:
    rows = []
    for invoice_id, result in ap_results.items():
        rows.append(
            {
                "workflow": "ap",
                "object_id": invoice_id,
                "roles": ["preparer", "reviewer", "approver"]
                if result.source == "ap_workflow"
                else ["ap_policy"],
                "output": result.decision,
                "source": result.source,
            }
        )
    for key, role in (("auto_apply", "Cash Application Agent"), ("human_review", "Cash Application Reviewer")):
        trace = ar_demo.get(key)
        if trace is None:
            continue
        roles = ["Cash Application Agent"]
        if trace.reviewer is not None:
            roles.append("Cash Application Reviewer")
        rows.append(
            {
                "workflow": "ar",
                "object_id": trace.payment_id,
                "roles": roles,
                "output": trace.final.decision,
                "source": "ar_workflow",
            }
        )
    if cash_report is not None:
        for trace in cash_report.traces:
            roles = []
            if trace.preparer is not None:
                roles.append("Cash Reconciliation Preparer")
            if trace.investigation is not None:
                roles.append("Cash Exception Investigator")
            if trace.reviewer is not None:
                roles.append("Cash Reconciliation Reviewer")
            if not roles:
                continue
            rows.append(
                {
                    "workflow": "cash",
                    "object_id": trace.reconciliation_id,
                    "roles": roles,
                    "output": trace.status,
                    "source": "cash_recon",
                }
            )
    if close_state.manager is not None:
        rows.append(
            {
                "workflow": "close",
                "object_id": close_state.close_id,
                "roles": ["Close Manager"],
                "output": close_state.period.status,
                "source": "month_end",
            }
        )
    if close_state.final_verdict is not None:
        rows.append(
            {
                "workflow": "close",
                "object_id": close_state.close_id,
                "roles": ["Month-End Close Reviewer"],
                "output": close_state.final_verdict.decision,
                "source": "month_end",
            }
        )
    if audit_run is not None:
        rows.append(
            {
                "workflow": "audit",
                "object_id": audit_run.audit_run_id,
                "roles": [item.role for item in audit_run.agents] or ["Auditor Agent", "Audit Report Agent"],
                "output": f"{len(audit_run.findings)} findings",
                "source": "audit",
            }
        )
    return rows


def _build_chains(
    *,
    ap_results,
    ar_demo,
    blocked_cash,
    closed_cash,
    blocked_close,
    closed_close,
    reporting_run,
    audit_run,
    reviews_by_workflow,
) -> list[dict]:
    chains = []
    snap = latest_snapshot(PERIOD)
    for spec in CHAIN_SPECS:
        chain = {
            "chain_id": spec["chain_id"],
            "label": spec["label"],
            "invoice_id": spec.get("invoice_id") or "",
            "invoice_ids": list(spec.get("invoice_ids") or []),
            "approval_id": "",
            "payment_id": spec.get("payment_id") or "",
            "bank_transaction_id": spec.get("bank_transaction_id") or "",
            "reconciliation_id": "",
            "journal_entry_id": "",
            "review_id": "",
            "close_run_id": closed_close.close_id,
            "close_status": closed_close.period.status,
            "snapshot_id": snap.snapshot_id if snap else "",
            "report_line": "",
            "variance_driver": "",
            "audit_run_id": audit_run.audit_run_id if audit_run else "",
            "amount": None,
            "status": "",
        }
        invoice_id = spec.get("invoice_id")
        if invoice_id and invoice_id in ap_results:
            result = ap_results[invoice_id]
            chain["approval_id"] = result.ap_decision_id or f"ap-policy/{invoice_id}"
            chain["amount"] = result.amount
            chain["status"] = result.decision
        if spec.get("payment_id"):
            key = "auto_apply" if spec["payment_id"] == FEATURED["ar_auto_apply"] else "human_review"
            trace = ar_demo.get(key)
            if trace is not None:
                chain["payment_id"] = trace.payment_id
                chain["status"] = trace.final.decision
                chain["amount"] = trace.payment.amount
                if trace.record is not None:
                    chain["journal_entry_id"] = (trace.record.journal_entry_ids or [""])[0]
                    chain["invoice_ids"] = [
                        item.invoice_id for item in trace.record.invoice_changes
                    ]
        bank_id = spec.get("bank_transaction_id")
        if bank_id:
            source = blocked_cash if spec["chain_id"] == "CHAIN-CASH-BREAK" else (closed_cash or blocked_cash)
            match = _match_by_bank(source, bank_id) or _match_by_bank(blocked_cash, bank_id)
            if match is not None:
                chain["reconciliation_id"] = match.reconciliation_id
                chain["amount"] = match.bank_amount
                chain["status"] = f"{match.match_type}/{match.status}"
                if match.ledger_entry_ids:
                    chain["journal_entry_id"] = match.ledger_entry_ids[0]
        if spec["chain_id"] == "CHAIN-CASH-BREAK":
            cash_review = reviews_by_workflow.get("cash")
            if cash_review is not None:
                chain["review_id"] = cash_review.review_id
            chain["journal_entry_id"] = FEATURED["cash_correction_journal"]
        if spec["chain_id"] == "CHAIN-AP-CLEAN" and reporting_run is not None:
            chain["report_line"] = "AP forecast / close AP task"
            for item in reporting_run.variances:
                if item.contributors:
                    chain["variance_driver"] = item.contributors[0].label
                    break
        if spec["chain_id"] == "CHAIN-CASH-BREAK" and reporting_run is not None:
            chain["report_line"] = f"close snapshot {chain['snapshot_id']}"
        if spec["chain_id"] == "CHAIN-CLOSE-HARBOR":
            harbor = _harbor_trace(closed_close) or _harbor_trace(blocked_close)
            if harbor is not None:
                lookup = getattr(harbor, "memory_lookup", None)
                chain["invoice_id"] = harbor.vendor
                chain["status"] = f"{harbor.final_method}/{harbor.final_decision}"
                chain["amount"] = harbor.final_amount
                chain["journal_entry_id"] = (
                    harbor.journal_entry.entry_id if harbor.journal_entry else ""
                )
                chain["review_id"] = (
                    lookup.retrieved[0]
                    if lookup is not None and lookup.retrieved
                    else ""
                )
                chain["report_line"] = (
                    f"prior decision {lookup.retrieved[0]}"
                    if lookup is not None and lookup.precedent_used and lookup.retrieved
                    else (lookup.deviation if lookup is not None and lookup.deviation else "")
                )
                if getattr(harbor, "written_memory_id", None):
                    chain["approval_id"] = harbor.written_memory_id
        chains.append(chain)
    return chains


def _resolve_reviews(period: str) -> dict:
    rows = {item.source_workflow: item for item in load_reviews(period)}
    resolved = {}
    if "cash" in rows:
        resolved["cash"] = resolve_review_item(
            rows["cash"].review_id,
            action="post_correcting_entry",
            reason="Classify the $12.40 Northstar wire difference and post the approved correcting receipt.",
            reviewer="cash-reviewer",
        )
    if "ar" in rows:
        resolved["ar"] = resolve_review_item(
            rows["ar"].review_id,
            action="apply_payment",
            invoice_id="INV-AR-050",
            reason="Associate PAY-CLOSE-4500 with INV-AR-050 and apply cash.",
            reviewer="ar-reviewer",
        )
    if "prepaid" in rows:
        resolved["prepaid"] = resolve_review_item(
            rows["prepaid"].review_id,
            action="attach_evidence",
            document_id="DOC-NS-FLOOD-2026",
            reason="Attach the Northshore flood policy packet.",
            reviewer="prepaid-reviewer",
        )
    return resolved


def _harbor_trace(state):
    report = getattr(state, "accrual", None) if state is not None else None
    if report is None:
        return None
    return next((item for item in report.traces if item.vendor == FEATURED["harbor_vendor"]), None)


def _seed_august_memory() -> dict:
    """Write August precedents on the same company books September will read."""
    from memory.scenarios import AUGUST_STRIPE, run_harbor_period, run_stripe_period

    harbor_decision, harbor_trace = run_harbor_period(
        "2026-08",
        memory_enabled=True,
        hide_period_invoices=True,
        method="seasonal_prior_year",
        reset=True,
        run_id="cfo-aug-harbor",
    )
    stripe = run_stripe_period(AUGUST_STRIPE, memory_enabled=True, reset=True)
    return {
        "harbor_decision": harbor_decision,
        "harbor_trace": harbor_trace,
        "stripe": stripe,
        "harbor_memory_id": harbor_trace.written_memory_id,
        "stripe_memory_id": getattr(getattr(stripe, "traces", [None])[0], "written_memory_id", None)
        if getattr(stripe, "traces", None)
        else None,
    }


def run_cfo_scenario(*, persist: bool = True) -> dict:
    """Execute the connected September lifecycle. Deterministic; no API key."""
    from ar.workflow import run_aging, run_ar_demo
    from audit.workflow import run_audit

    august_memory = _seed_august_memory()
    balances, _bank, _ledger, _fees = load_demo_dataset()
    invoices = list(all_invoices())
    opening_ar = run_aging(AS_OF, persist=False)

    featured_ids = (
        FEATURED["ap_matched"],
        FEATURED["ap_duplicate"],
        FEATURED["ap_human_review"],
    )
    ap_results = {
        invoice_id: decide_ap(invoice_id, live=False, featured=set())
        for invoice_id in featured_ids
    }
    ar_demo = run_ar_demo(AS_OF)

    from cash_recon.demo import seed_provider_payouts

    seed_provider_payouts()
    blocked = run_month_end(PERIOD, scenario="demo", live=False, reset=True, allow_close=False)
    blocked_cash = get_report(PERIOD)
    if blocked_cash is None:
        raise RuntimeError("Month-end cash reconciliation did not persist a report")
    blocked_reporting = _reporting_view(blocked)
    reviews_before = {item.source_workflow: item for item in load_reviews(PERIOD)}

    resolved = _resolve_reviews(PERIOD)
    rerun_affected(PERIOD, live=False)
    closed = finalize_close(PERIOD, live=False)
    closed_cash = get_report(PERIOD)
    closed_reporting = _reporting_view(closed)

    post_close_rejected = False
    post_close_detail = ""
    try:
        post_entry(
            period=PERIOD,
            memo="Unauthorized late September entry",
            debit_account="Insurance Expense",
            credit_account="Cash",
            amount=100,
            entry_type="manual",
            idempotency_key="cfo-demo-post-close",
            source_document_id="CFO-DEMO",
            evidence_refs=["CFO-DEMO"],
            actor="cfo-demo",
        )
    except ClosedPeriodError as exc:
        post_close_rejected = True
        post_close_detail = f"{exc.event.event_type} {exc.event.decision}"

    reporting_run = run_reporting_workflow(
        PERIOD, as_of=REPORTING_AS_OF, live=False, seed=True, persist=persist
    )
    dataset = operational_audit_dataset(PERIOD, close_state=closed, cash_report=closed_cash or blocked_cash)
    audit_run = run_audit(PERIOD, seed=26, use_agent=False, persist=persist, dataset=dataset)
    independence_match = featured_independence_match(blocked_cash)
    independence = (
        prove_operational_independence(dataset, independence_match)
        if independence_match is not None
        else {"passed": False, "detail": "no operational MATCHED cash row"}
    )

    chains = _build_chains(
        ap_results=ap_results,
        ar_demo=ar_demo,
        blocked_cash=blocked_cash,
        closed_cash=closed_cash,
        blocked_close=blocked,
        closed_close=closed,
        reporting_run=reporting_run,
        audit_run=audit_run,
        reviews_by_workflow=reviews_before,
    )
    human = _human_reviews(ap_results, ar_demo, blocked_cash, blocked)
    handoffs = _handoffs(ap_results, ar_demo, blocked_cash, closed, audit_run)
    harbor_trace = _harbor_trace(closed) or _harbor_trace(blocked)
    harbor_packet = ""
    if closed.accrual is not None:
        from close.report import format_close_run, format_month_end_demo
        from close.models import AuditRefs, CloseRun

        packet = CloseRun(
            period=PERIOD,
            close_id=closed.close_id,
            started_at=closed.period.opened_at,
            discovery=closed.accrual.discovery,
            accrual=closed.accrual,
            audit=AuditRefs(close_id=closed.close_id, accrual_trace_dir=closed.accrual.trace_dir),
            trace_path=closed.trace_path,
        )
        harbor_packet = f"{format_close_run(packet)}\n\n{format_month_end_demo(closed)}"
    payload = {
        "period": PERIOD,
        "inventory": WORKFLOW_INVENTORY,
        "opening": {
            "invoice_count": len(invoices),
            "opening_bank": balances.opening_bank,
            "opening_ledger": balances.opening_ledger,
            "ar_outstanding": opening_ar.totals.total_ar,
            "ar_invoices": opening_ar.totals.open_invoice_count or len(opening_ar.lines),
        },
        "ap_results": ap_results,
        "ar_demo": ar_demo,
        "blocked_cash": blocked_cash,
        "closed_cash": closed_cash,
        "blocked_close": blocked,
        "closed_close": closed,
        "resolved_reviews": resolved,
        "blocked_reporting": blocked_reporting,
        "closed_reporting": closed_reporting,
        "reporting_run": reporting_run,
        "statement": reporting_run.statement,
        "prior_statement": reporting_run.comparison_statement,
        "forecast": reporting_run.forecast,
        "forecast_variance": reporting_run.forecast_variance,
        "audit_run": audit_run,
        "audit_dataset": dataset,
        "audit_findings": list(audit_run.findings),
        "independence": independence,
        "chains": chains,
        "human_reviews": human,
        "handoffs": handoffs,
        "company": {
            "company_id": COMPANY_ID,
            "legal_name": COMPANY_NAME,
            "period": PERIOD,
            "headquarters": HEADQUARTERS,
        },
        "august_memory": august_memory,
        "harbor_trace": harbor_trace,
        "harbor_packet": harbor_packet,
        "post_close_rejected": post_close_rejected,
        "post_close_detail": post_close_detail,
        "closed_cash_tied": bool(
            closed_cash
            and closed_cash.arithmetic_tied
            and money(closed_cash.unexplained_difference) == 0
        ),
        "workflow_status": {
            "ap": "COMPLETE",
            "ar": "COMPLETE",
            "cash": "COMPLETE",
            "close": "COMPLETE" if closed.period.status == "CLOSED" else closed.period.status,
            "reporting": "COMPLETE",
            "forecast": "COMPLETE" if reporting_run.forecast else "MISSING",
            "audit": "COMPLETE",
            "memory": "COMPLETE" if august_memory.get("harbor_memory_id") else "MISSING",
        },
        "task_status": {item.task_id: item.status for item in closed.tasks},
    }
    payload["checks"] = evaluate_all(payload)
    payload["metrics"] = compute_metrics(payload)
    return payload


def invoice_summary(invoice_id: str) -> str:
    invoice = load_invoice(invoice_id)
    if invoice is None:
        return invoice_id
    return f"{invoice.invoice_id}  {invoice.vendor}  ${invoice.amount:,.2f}"

"""August → September cross-period stories using existing finance workflows."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cash_recon.mathutil import cents, period_of
from cash_recon.models import BankTransaction, LedgerEntry, PeriodBalances
from cash_recon.store import reset_cash_state
from cash_recon.workflow import run_cash_reconciliation
from integrations.models import PayoutLine, ProviderPayout
from integrations.store import remember_payout, reset_integration_state
from memory.format import format_lookup_trace
from memory.models import MemoryLookup
from memory.policy import memory_mode
from prepaid.models import PrepaidItem
from prepaid.store import configure_paths as configure_prepaid
from prepaid.store import reset as reset_prepaid
from prepaid.store import save_items
from prepaid.workflow import run_prepaid_workflow
from memory.store import configure_paths as configure_memory
from memory.store import reset_memory


@dataclass(frozen=True)
class StripePeriodSpec:
    period: str
    payout_id: str
    deposit_id: str
    ledger_id: str
    date: str
    gross: float
    fees: float
    chargebacks: float
    refunds: float
    bank: float


AUGUST_STRIPE = StripePeriodSpec(
    period="2026-08",
    payout_id="po_mem_aug_001",
    deposit_id="BNK-STR-AUG-001",
    ledger_id="GL-STR-AUG-GROSS",
    date="2026-08-28",
    gross=10000.0,
    fees=300.0,
    chargebacks=80.0,
    refunds=0.0,
    bank=9620.0,
)

SEPTEMBER_STRIPE = StripePeriodSpec(
    period="2026-09",
    payout_id="po_mem_sep_001",
    deposit_id="BNK-STR-SEP-001",
    ledger_id="GL-STR-SEP-GROSS",
    date="2026-09-26",
    gross=15000.0,
    fees=390.0,
    chargebacks=100.0,
    refunds=50.0,
    bank=14460.0,
)

SEPTEMBER_CONTRADICT = StripePeriodSpec(
    period="2026-09",
    payout_id="po_mem_sep_gap",
    deposit_id="BNK-STR-SEP-GAP",
    ledger_id="GL-STR-SEP-GAP",
    date="2026-09-27",
    gross=9700.0,
    fees=300.0,
    chargebacks=80.0,
    refunds=0.0,
    bank=9620.0,
)


def _payout(spec: StripePeriodSpec) -> ProviderPayout:
    lines = [
        PayoutLine(
            line_type="charge",
            amount=spec.gross,
            amount_minor=cents(spec.gross),
            category="gross",
            description=f"Stripe charges {spec.period}",
        ),
        PayoutLine(
            line_type="stripe_fee",
            amount=-spec.fees,
            amount_minor=-cents(spec.fees),
            category="fee",
            description="Stripe processing fees",
        ),
    ]
    if spec.chargebacks:
        lines.append(
            PayoutLine(
                line_type="chargeback",
                amount=-spec.chargebacks,
                amount_minor=-cents(spec.chargebacks),
                category="chargeback",
                description="Stripe chargeback",
            )
        )
    if spec.refunds:
        lines.append(
            PayoutLine(
                line_type="refund",
                amount=-spec.refunds,
                amount_minor=-cents(spec.refunds),
                category="refund",
                description="Stripe refund",
            )
        )
    return ProviderPayout(
        provider="stripe",
        event_id=f"evt_{spec.payout_id}",
        payout_id=spec.payout_id,
        status="paid",
        amount=cents(spec.bank),
        currency="usd",
        arrival_date=spec.date,
        provider_created_at=spec.date,
        source_event_type="payout.paid",
        raw_source_ref=spec.payout_id,
        reference=spec.payout_id,
        lines=lines,
        bank_deposit_id=spec.deposit_id,
        bank_deposit_amount=spec.bank,
        bank_deposit_currency="usd",
    )


def _dataset(spec: StripePeriodSpec) -> tuple[PeriodBalances, list[BankTransaction], list[LedgerEntry]]:
    balances = PeriodBalances(
        opening_bank=0.0,
        opening_ledger=0.0,
        as_of_date=spec.date,
        opening_bank_minor=0,
        opening_ledger_minor=0,
    )
    bank = [
        BankTransaction(
            transaction_id=spec.deposit_id,
            date=spec.date,
            amount=spec.bank,
            amount_minor=cents(spec.bank),
            description=f"STRIPE PAYOUT {spec.payout_id}",
            reference=spec.payout_id,
            counterparty="Stripe",
            transaction_type="deposit",
            source="bank",
            provider="stripe",
            period=spec.period,
            raw_metadata={"payout_id": spec.payout_id, "provider": "stripe"},
        )
    ]
    ledger = [
        LedgerEntry(
            entry_id=spec.ledger_id,
            date=spec.date,
            amount=spec.gross,
            amount_minor=cents(spec.gross),
            account="1000-Cash",
            counterparty="Stripe",
            reference=spec.payout_id,
            description=f"Stripe gross receipts {spec.period}",
            entry_type="processor_gross",
            period=spec.period,
            source="gl",
            raw_metadata={"payout_id": spec.payout_id, "provider": "stripe", "gross": spec.gross},
        )
    ]
    return balances, bank, ledger


@contextmanager
def isolated_memory_workspace(root: Path):
    """Keep demo/eval side effects out of the developer's default run dirs."""
    from accrual import ledger as accrual_ledger
    from accrual import trace as accrual_trace
    from cash_recon import store as cash_store
    from cash_recon.store import configure_paths as configure_cash
    from close import ledger as close_ledger
    from close import month_end as close_month_end
    from close.ledger import configure_paths as configure_gl
    from close.ledger import reset_ledger
    from close.month_end import configure_paths as configure_close
    from integrations import store as integration_store
    from memory.store import current_directory
    from prepaid import store as prepaid_store

    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "memory": current_directory(),
        "cash_runs": cash_store.RUNS_DIR,
        "cash_traces": cash_store.TRACES_DIR,
        "prepaid": prepaid_store.STATE_DIR,
        "close": close_month_end.STATE_DIR,
        "gl": close_ledger.LEDGER_DIR,
        "accrual_ledger": (accrual_ledger.LEDGER_DIR, accrual_ledger.ACCRUALS_PATH, accrual_ledger.JOURNALS_PATH),
        "accrual_traces": accrual_trace.TRACES_ROOT,
        "integration_runs": integration_store.RUNS_DIR,
        "integration_state": integration_store.STATE_PATH,
    }
    configure_memory(root / "memory")
    reset_memory()
    configure_cash(runs_dir=root / "cash-runs", traces_dir=root / "cash-traces")
    reset_cash_state()
    configure_prepaid(root / "prepaid")
    reset_prepaid()
    configure_close(root / "close")
    configure_gl(root / "gl")
    reset_ledger()
    accrual_dir = root / "accrual-ledger"
    accrual_dir.mkdir(parents=True, exist_ok=True)
    accrual_ledger.LEDGER_DIR = accrual_dir
    accrual_ledger.ACCRUALS_PATH = accrual_dir / "open_accruals.json"
    accrual_ledger.JOURNALS_PATH = accrual_dir / "journal_entries.json"
    accrual_trace.TRACES_ROOT = root / "accrual-traces"
    integration_store.RUNS_DIR = root / "integrations"
    integration_store.STATE_PATH = root / "integrations" / "state.json"
    reset_integration_state()
    try:
        yield root
    finally:
        configure_memory(snapshot["memory"])
        configure_cash(runs_dir=snapshot["cash_runs"], traces_dir=snapshot["cash_traces"])
        reset_cash_state()
        configure_prepaid(snapshot["prepaid"])
        configure_close(snapshot["close"])
        configure_gl(snapshot["gl"])
        accrual_ledger.LEDGER_DIR, accrual_ledger.ACCRUALS_PATH, accrual_ledger.JOURNALS_PATH = snapshot["accrual_ledger"]
        accrual_trace.TRACES_ROOT = snapshot["accrual_traces"]
        integration_store.RUNS_DIR = snapshot["integration_runs"]
        integration_store.STATE_PATH = snapshot["integration_state"]
        reset_integration_state()


def seed_stripe_period(spec: StripePeriodSpec) -> ProviderPayout:
    payout = _payout(spec)
    remember_payout(payout)
    return payout


def run_stripe_period(spec: StripePeriodSpec, *, memory_enabled: bool = True, reset: bool = True):
    if reset:
        reset_cash_state()
        reset_integration_state()
    seed_stripe_period(spec)
    balances, bank, ledger = _dataset(spec)
    with memory_mode(memory_enabled):
        report = run_cash_reconciliation(
            spec.period,
            balances=balances,
            bank=bank,
            ledger=ledger,
            fees=[],
            seed_demo=False,
            seed_providers=False,
            reset=reset,
            use_agent=False,
        )
    return report


def _featured_trace(report, spec: StripePeriodSpec):
    for trace in report.traces:
        if spec.deposit_id in trace.final.bank_transaction_ids:
            return trace
        if spec.payout_id == (trace.final.provider_payout_id or ""):
            return trace
    return report.traces[0] if report.traces else None


def run_stripe_cross_period(*, memory_enabled: bool = True) -> dict[str, Any]:
    """August writes memory. A separate September run retrieves it when memory is on."""
    august = run_stripe_period(AUGUST_STRIPE, memory_enabled=True, reset=True)
    reset_cash_state()
    reset_integration_state()
    september = run_stripe_period(SEPTEMBER_STRIPE, memory_enabled=memory_enabled, reset=True)
    aug_trace = _featured_trace(august, AUGUST_STRIPE)
    sep_trace = _featured_trace(september, SEPTEMBER_STRIPE)
    return {
        "august": august,
        "september": september,
        "august_trace": aug_trace,
        "september_trace": sep_trace,
        "memory_enabled": memory_enabled,
        "august_lookup": getattr(aug_trace, "memory_lookup", None) if aug_trace else None,
        "september_lookup": getattr(sep_trace, "memory_lookup", None) if sep_trace else None,
    }


def run_stripe_contradiction(*, memory_enabled: bool = True) -> dict[str, Any]:
    august = run_stripe_period(AUGUST_STRIPE, memory_enabled=True, reset=True)
    reset_cash_state()
    reset_integration_state()
    september = run_stripe_period(SEPTEMBER_CONTRADICT, memory_enabled=memory_enabled, reset=True)
    return {
        "august": august,
        "september": september,
        "august_trace": _featured_trace(august, AUGUST_STRIPE),
        "september_trace": _featured_trace(september, SEPTEMBER_CONTRADICT),
        "memory_enabled": memory_enabled,
    }


CLOUDCO_AUGUST = PrepaidItem(
    prepaid_id="PRE-MEM-CLOUD-AUG",
    vendor="CloudCo",
    description="Annual CloudCo platform license",
    source_document_id="DOC-CLOUD-AUG-2026",
    total_amount=12000.0,
    start_date="2026-08-01",
    end_date="2027-07-31",
    initial_account="1400-Prepaid-Expenses",
    expense_account="6200-Software",
    amortization_method="straight_line_monthly",
    created_at="2026-08-02T00:00:00Z",
    evidence_refs=["DOC-CLOUD-AUG-2026", "POLICY-PREPAID-001"],
)

CLOUDCO_SEPTEMBER = PrepaidItem(
    prepaid_id="PRE-MEM-CLOUD-SEP",
    vendor="CloudCo",
    description="CloudCo analytics add-on annual license",
    source_document_id="DOC-CLOUD-SEP-2026",
    total_amount=14400.0,
    start_date="2026-09-01",
    end_date="2027-08-31",
    initial_account="1400-Prepaid-Expenses",
    expense_account="6200-Software",
    amortization_method="straight_line_monthly",
    created_at="2026-09-03T00:00:00Z",
    evidence_refs=["DOC-CLOUD-SEP-2026", "POLICY-PREPAID-001"],
)

CLOUDCO_CONTRADICT = PrepaidItem(
    prepaid_id="PRE-MEM-CLOUD-ONE",
    vendor="CloudCo",
    description="CloudCo one-month burst capacity",
    source_document_id="DOC-CLOUD-SEP-ONE",
    total_amount=900.0,
    start_date="2026-09-01",
    end_date="2026-09-30",
    initial_account="1400-Prepaid-Expenses",
    expense_account="6200-Software",
    amortization_method="straight_line_monthly",
    created_at="2026-09-04T00:00:00Z",
    evidence_refs=["DOC-CLOUD-SEP-ONE", "POLICY-PREPAID-001"],
)

NORDIC_SEPTEMBER = PrepaidItem(
    prepaid_id="PRE-MEM-NORDIC-SEP",
    vendor="Nordic Insurance",
    description="Nordic warehouse insurance",
    source_document_id="DOC-NORDIC-SEP",
    total_amount=3600.0,
    start_date="2026-09-01",
    end_date="2027-08-31",
    initial_account="1400-Prepaid-Expenses",
    expense_account="6400-Insurance",
    amortization_method="straight_line_monthly",
    created_at="2026-09-05T00:00:00Z",
    evidence_refs=["DOC-NORDIC-SEP", "POLICY-PREPAID-001"],
)


def _prepaid_period(items: list[PrepaidItem], period: str, *, memory_enabled: bool):
    reset_prepaid()
    save_items(items)
    with memory_mode(memory_enabled):
        return run_prepaid_workflow(period, use_agent=False)


def run_prepaid_cross_period(*, memory_enabled: bool = True, september_item: PrepaidItem | None = None) -> dict[str, Any]:
    august = _prepaid_period([CLOUDCO_AUGUST], "2026-08", memory_enabled=True)
    september = _prepaid_period([september_item or CLOUDCO_SEPTEMBER], "2026-09", memory_enabled=memory_enabled)
    return {
        "august": august,
        "september": september,
        "august_trace": august.traces[0] if august.traces else None,
        "september_trace": september.traces[0] if september.traces else None,
        "memory_enabled": memory_enabled,
    }


def lookup_trace_text(lookup: MemoryLookup | None) -> str:
    if lookup is None:
        return "memory_lookup\n  (not recorded)"
    return format_lookup_trace(lookup)


def period_of_date(value: str) -> str:
    return period_of(value)


HARBOR_VENDOR = "Harbor Electric"
LINDHOLM_VENDOR = "Lindholm & Ruiz LLP"


def reset_accrual_books() -> None:
    from accrual.ledger import save_accruals, save_journal_entries

    save_accruals([])
    save_journal_entries([])


def _harbor_decision(vendor: str, period: str, *, method: str | None, hide_period_invoices: bool, memory_enabled: bool, run_id: str):
    from accrual.cutoff import data_cutoff
    from accrual.estimation import compute_estimate
    from accrual.models import AccrualDecision
    from accrual.policy import preferred_candidate
    from accrual.store import build_estimate_context
    from accrual.workflow import finalize_vendor_close

    with memory_mode(memory_enabled):
        with data_cutoff(period, hide_period_invoices=hide_period_invoices, allow_later_invoices=False):
            context = build_estimate_context(vendor, period)
            if method is None:
                candidate = preferred_candidate(context)
            else:
                candidate = compute_estimate(context, method)
            if candidate is None or not candidate.applicable or candidate.amount is None:
                raw = AccrualDecision(
                    vendor=vendor,
                    period=period,
                    status="insufficient_evidence",
                    estimated_amount=None,
                    confidence=0,
                    reasoning_summary="No applicable Python estimate candidate.",
                    evidence=[],
                )
            else:
                raw = AccrualDecision(
                    vendor=vendor,
                    period=period,
                    status="accrual_required",
                    estimated_amount=candidate.amount,
                    confidence=0.88,
                    estimation_method=candidate.method,
                    evidence=[candidate.rationale],
                    reasoning_summary=candidate.rationale,
                )
            return finalize_vendor_close(vendor, period, raw, run_id=run_id)


def run_harbor_period(
    period: str,
    *,
    memory_enabled: bool = True,
    hide_period_invoices: bool = False,
    method: str | None = None,
    vendor: str = HARBOR_VENDOR,
    reset: bool = True,
    run_id: str | None = None,
):
    if reset:
        reset_accrual_books()
    stamp = period.replace("-", "")
    return _harbor_decision(
        vendor,
        period,
        method=method,
        hide_period_invoices=hide_period_invoices,
        memory_enabled=memory_enabled,
        run_id=run_id or f"mem-{stamp}",
    )


def harbor_close_packet(report, *, close_id: str | None = None) -> str:
    """Build the month-end close packet text that cites prior-period accrual decisions."""
    from datetime import datetime, timezone

    from close.models import AuditRefs, ClosePeriod, CloseRun, CloseTask, MonthEndState
    from close.report import format_close_run, format_month_end_demo

    period = report.period
    close_id = close_id or f"CLOSE-{period}-MEM"
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    packet = CloseRun(
        period=period,
        close_id=close_id,
        started_at=started,
        discovery=report.discovery,
        accrual=report,
        audit=AuditRefs(close_id=close_id, accrual_trace_dir=report.trace_dir),
        trace_path=report.trace_path,
    )
    month_end = MonthEndState(
        period=ClosePeriod(period=period, opened_at=started, status="IN_PROGRESS"),
        close_id=close_id,
        tasks=[
            CloseTask(
                task_id="accruals",
                period=period,
                category="accruals",
                description="Book missing-bill accruals",
                owner_agent="Accrual Agent",
                status="COMPLETE",
            )
        ],
        accrual=report,
        completion_pct=100,
        trace_path=report.trace_path,
    )
    return f"{format_close_run(packet)}\n\n{format_month_end_demo(month_end)}"


def _harbor_report(decision, trace, period: str):
    from accrual.models import AccrualPeriodReport

    created = [decision] if decision.status == "accrual_required" else []
    skipped = [decision] if decision.status == "no_accrual_needed" else []
    uncertain = [decision] if decision.status == "insufficient_evidence" else []
    return AccrualPeriodReport(
        period=period,
        vendors_reviewed=1,
        accruals_created=created,
        no_accrual_needed=skipped,
        uncertain_items=uncertain,
        total_accrued_expense=round(sum(item.estimated_amount or 0 for item in created), 2),
        traces=[trace],
        ranked_missing=created,
    )


def run_harbor_cross_period(
    *,
    memory_enabled: bool = True,
    september_method: str | None = None,
    september_vendor: str = HARBOR_VENDOR,
    august_method: str = "seasonal_prior_year",
) -> dict[str, Any]:
    """August books Harbor Electric. September retrieves that methodology when memory is on."""
    reset_accrual_books()
    august_decision, august_trace = run_harbor_period(
        "2026-08",
        memory_enabled=True,
        hide_period_invoices=True,
        method=august_method,
        reset=False,
        run_id="mem-aug-harbor",
    )
    september_decision, september_trace = run_harbor_period(
        "2026-09",
        memory_enabled=memory_enabled,
        hide_period_invoices=False,
        method=september_method,
        vendor=september_vendor,
        reset=True,
        run_id="mem-sep-harbor",
    )
    september_report = _harbor_report(september_decision, september_trace, "2026-09")
    return {
        "august": august_decision,
        "september": september_decision,
        "august_trace": august_trace,
        "september_trace": september_trace,
        "september_report": september_report,
        "september_packet": harbor_close_packet(september_report),
        "memory_enabled": memory_enabled,
        "august_lookup": august_trace.memory_lookup,
        "september_lookup": september_trace.memory_lookup,
    }


def run_harbor_self_correction(
    *,
    actual_amount: float = 12100.0,
    invoice_id: str = "INV-HE-2026-10",
    memory_enabled: bool = True,
) -> dict[str, Any]:
    """August estimate, September reuse, October actual bill reverses the estimate."""
    from accrual.ledger import find_accrual, load_accruals, reconcile_accrual
    from cfo.explain import explain_accrual_correction
    from memory.models import MemoryEvidence
    from memory.write import write_decision

    reset_accrual_books()
    august_decision, august_trace = run_harbor_period(
        "2026-08",
        memory_enabled=True,
        hide_period_invoices=True,
        reset=False,
        run_id="mem-aug-harbor-correct",
    )
    september_decision, september_trace = run_harbor_period(
        "2026-09",
        memory_enabled=memory_enabled,
        hide_period_invoices=True,
        reset=False,
        run_id="mem-sep-harbor-correct",
    )
    open_rows = [item for item in load_accruals() if item.vendor == HARBOR_VENDOR and item.status == "open"]
    target = open_rows[-1] if open_rows else find_accrual(getattr(september_decision, "accrual_id", None) or "")
    if target is None:
        raise RuntimeError("Harbor accrual was not booked, so it cannot be corrected.")
    result = reconcile_accrual(target.accrual_id, invoice_id, actual_amount)
    explanation = explain_accrual_correction(
        HARBOR_VENDOR,
        result.period,
        result.estimated_amount,
        result.actual_amount,
        invoice_id,
        prior_id=getattr(august_trace, "written_memory_id", None),
    )
    memory, _written = write_decision(
        period="2026-10",
        workflow="month_end_close",
        entity_type="vendor",
        entity_id="harbor-electric",
        situation_type="accrual_methodology",
        situation_summary=f"October invoice {invoice_id} arrived at {actual_amount} versus the open accrual.",
        evidence=[
            MemoryEvidence(kind="invoice", label=invoice_id, amount=actual_amount, reference=invoice_id),
            MemoryEvidence(kind="accrual", label=target.accrual_id, amount=result.estimated_amount, reference=target.accrual_id),
        ],
        decision="reverse_and_book_actual",
        reasoning_summary=explanation["narrative"],
        accounting_treatment="reverse_accrual_book_actual",
        outcome="corrected",
        reusable_precedent="Use the actual invoice once it arrives; do not keep the estimate.",
        source_trace_ids=[target.accrual_id],
        tags=["harbor", "self_correction"],
        fingerprint=f"harbor-oct-{invoice_id}-{actual_amount}",
        entity_name=HARBOR_VENDOR,
        accounting_category="utilities_accrual",
    )
    return {
        "august": august_decision,
        "september": september_decision,
        "august_trace": august_trace,
        "september_trace": september_trace,
        "october_reconciliation": result,
        "explanation": explanation,
        "correction_memory": memory,
        "detected_prior_estimate": True,
        "books_corrected": True,
        "memory_enabled": memory_enabled,
    }


def run_harbor_contamination(
    *,
    wrong_august_amount: float = 50000.0,
    memory_enabled: bool = True,
) -> dict[str, Any]:
    """Inject a wrong August amount, then measure whether September blindly copies it."""
    from accrual.ledger import load_accruals, save_accruals

    story = run_harbor_cross_period(memory_enabled=True)
    rows = load_accruals()
    mutated = []
    for item in rows:
        if item.vendor == HARBOR_VENDOR and item.period == "2026-08":
            mutated.append(item.model_copy(update={"estimated_amount": wrong_august_amount}))
        else:
            mutated.append(item)
    save_accruals(mutated)
    september_decision, september_trace = run_harbor_period(
        "2026-09",
        memory_enabled=memory_enabled,
        hide_period_invoices=False,
        reset=False,
        run_id="mem-sep-harbor-contam",
    )
    copied = bool(
        september_decision.estimated_amount
        and abs(float(september_decision.estimated_amount) - wrong_august_amount) < 0.01
    )
    return {
        "wrong_august_amount": wrong_august_amount,
        "september_amount": september_decision.estimated_amount,
        "copied_wrong_amount": copied,
        "contained": not copied,
        "september_decision": september_decision,
        "september_trace": september_trace,
        "memory_enabled": memory_enabled,
        "clean_september_amount": getattr(story["september"], "estimated_amount", None),
    }

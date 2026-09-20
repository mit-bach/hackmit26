"""Feed simulated Stripe events through the real Office-of-the-CFO runtime."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ar.models import ARPrecedent, Customer, CustomerInvoice
from ar.store import (
    all_invoices,
    all_payments,
    applications,
    events as ar_events,
    journals as ar_journals,
    load_empty_state,
    precedents as ar_precedents,
    save_customer,
    save_invoice,
    add_precedent,
)
from ar.context import ar_close_snapshot
from cash_recon.mathutil import cents, period_of
from cash_recon.models import BankTransaction, LedgerEntry, PeriodBalances
from cash_recon.store import reset_cash_state
from cash_recon.workflow import run_cash_reconciliation
from close.context import all_links, remember_link, reset_context
from evaluation.isolation import operational_phase_guard
from integrations.cash import major_units, reconcile_payout
from integrations.providers import stripe
from integrations.router import classify_stripe_event
from integrations.store import (
    all_events,
    all_payouts,
    all_reconciliations,
    get_payout,
    get_reconciliation,
    reset_integration_state,
    write_trace,
)
from simulations.stripe.pack import CompanyPack, Scenario, build_company_pack
from simulations.stripe.provider import SimulatedStripeProvider


def _raw(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


@contextmanager
def isolated_simulation(root: Path):
    from ar.store import STATE_DIR
    from ar.store import configure_paths as configure_ar
    from close.context import CONTEXT_DIR
    from close.context import configure_paths as configure_ctx
    from cash_recon.store import RUNS_DIR as CASH_RUNS, TRACES_DIR as CASH_TRACES
    from cash_recon.store import configure_paths as configure_cash
    from integrations import store as integration_store

    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    previous = {
        "ar": STATE_DIR,
        "ctx": CONTEXT_DIR,
        "cash": (CASH_RUNS, CASH_TRACES),
        "integrations": (integration_store.RUNS_DIR, integration_store.STATE_PATH),
    }
    configure_ar(root / "ar")
    configure_ctx(root / "ctx")
    configure_cash(runs_dir=root / "cash-runs", traces_dir=root / "cash-traces")
    integration_store.RUNS_DIR = root / "integrations"
    integration_store.STATE_PATH = root / "integrations" / "state.json"
    reset_integration_state()
    reset_cash_state()
    reset_context()
    load_empty_state()
    try:
        yield
    finally:
        reset_integration_state()
        reset_cash_state()
        configure_ar(previous["ar"])
        configure_ctx(previous["ctx"])
        configure_cash(runs_dir=previous["cash"][0], traces_dir=previous["cash"][1])
        integration_store.RUNS_DIR = previous["integrations"][0]
        integration_store.STATE_PATH = previous["integrations"][1]


def seed_company(pack: CompanyPack, *, memory_enabled: bool = True) -> None:
    for row in pack.customers:
        save_customer(Customer.model_validate(row))
    for row in pack.invoices:
        save_invoice(CustomerInvoice.model_validate(row))
    if memory_enabled:
        for row in pack.precedents:
            add_precedent(ARPrecedent.model_validate(row))


def _process(payload: dict, provider: SimulatedStripeProvider):
    raw = _raw(payload)
    return stripe.process_raw(raw, {"stripe-signature": stripe.sign(raw)}, provider=provider)


def _bank_and_ledger(pack: CompanyPack, payout_ids: set[str]) -> tuple[list[BankTransaction], list[LedgerEntry]]:
    bank: list[BankTransaction] = []
    ledger: list[LedgerEntry] = []
    for deposit in pack.bank_deposits:
        if deposit["payout_id"] not in payout_ids:
            continue
        amount_minor = int(deposit.get("amount_minor") or cents(deposit["amount"]))
        bank.append(
            BankTransaction(
                transaction_id=deposit["deposit_id"],
                date=deposit["date"],
                amount=float(deposit["amount"]),
                amount_minor=amount_minor,
                description=deposit["description"],
                reference=deposit["payout_id"],
                counterparty="Stripe",
                transaction_type="deposit",
                source="bank",
                provider="stripe",
                period=period_of(deposit["date"]),
                raw_metadata={"payout_id": deposit["payout_id"]},
            )
        )
    for payout in all_payouts():
        if payout.payout_id not in payout_ids:
            continue
        ledger.append(
            LedgerEntry(
                entry_id=f"GL-STR-{payout.payout_id}",
                date=payout.arrival_date or "2026-09-30",
                amount=major_units(payout.amount, payout.currency),
                amount_minor=int(payout.amount),
                account="1000-Cash",
                counterparty="Stripe",
                reference=payout.payout_id,
                description=f"Stripe payout {payout.payout_id}",
                entry_type="processor_payout",
                period=period_of(payout.arrival_date or ""),
                source="gl",
                raw_metadata={"payout_id": payout.payout_id, "provider": "stripe"},
            )
        )
    return bank, ledger


def _scenario_payout_ids(scenario: Scenario, pack: CompanyPack) -> set[str]:
    ids = set()
    if scenario.ground_truth and scenario.ground_truth.expected_payout_id:
        ids.add(scenario.ground_truth.expected_payout_id)
    for payload in scenario.events:
        obj = (payload.get("data") or {}).get("object") or {}
        if obj.get("object") == "payout" and obj.get("id"):
            ids.add(str(obj["id"]))
    if scenario.scenario_id == "stripe_refund_after_payout":
        ids.update({"po_str_005a", "po_str_005b"})
    if scenario.scenario_id == "stripe_chargeback":
        ids.update({"po_str_006a", "po_str_006b"})
    return ids


def run_scenario(
    scenario: Scenario,
    *,
    pack: CompanyPack | None = None,
    persist_root: Path | None = None,
    live: bool = False,
    decision_mode: str = "policy",
    memory_enabled: bool = True,
    use_llm: bool | None = None,
) -> dict[str, Any]:
    from simulations.stripe.classify import classify_scenario
    from simulations.stripe.control import run_control

    pack = pack or build_company_pack()
    llm = bool(live) if use_llm is None else bool(use_llm)
    reset_integration_state()
    reset_cash_state()
    reset_context()
    load_empty_state()
    with run_control(decision_mode=decision_mode, memory_enabled=memory_enabled, use_llm=llm) as control:
        return _run_scenario_body(
            scenario,
            pack=pack,
            persist_root=persist_root,
            control=control,
        )


def _run_scenario_body(
    scenario: Scenario,
    *,
    pack: CompanyPack,
    persist_root: Path | None,
    control,
) -> dict[str, Any]:
    from simulations.stripe.classify import classify_scenario

    seed_company(pack, memory_enabled=control.memory_enabled)
    universe = pack.universe()
    provider = SimulatedStripeProvider(universe)
    if scenario.withhold_txn_ids:
        provider.withhold_transactions(scenario.withhold_txn_ids)

    results: list[Any] = []
    routing: list[dict[str, Any]] = []
    payout_event_types = {
        "payout.created",
        "payout.updated",
        "payout.paid",
        "payout.failed",
        "payout.canceled",
        "payout.reconciliation_completed",
    }

    def consume(payload: dict) -> None:
        result = _process(payload, provider)
        results.append(result)
        routing.append(
            {
                "event_id": payload.get("id"),
                "event_type": payload.get("type"),
                "classified_workflow": classify_stripe_event(str(payload.get("type") or "")),
                "result_workflow": result.workflow,
                "status": result.status,
                "duplicate": result.duplicate,
                "payment_id": result.payment_id,
                "payout_id": result.payout_id,
                "invoice_ids": list(result.invoice_numbers or []),
            }
        )

    with operational_phase_guard():
        if scenario.bank_before_payout:
            for payload in scenario.events:
                if str(payload.get("type") or "") not in payout_event_types:
                    consume(payload)
            early_ids = _scenario_payout_ids(scenario, pack)
            bank, ledger = _bank_and_ledger(pack, early_ids)
            early_balances = PeriodBalances(opening_bank=0, opening_ledger=0, as_of_date="2026-09-30")
            run_cash_reconciliation(
                scenario.cash_period,
                reset=True,
                seed_providers=False,
                use_agent=bool(control.decision_mode == "agentic" and control.use_llm),
                balances=early_balances,
                bank=bank,
                ledger=[],
            )
            for payload in scenario.events:
                if str(payload.get("type") or "") in payout_event_types:
                    consume(payload)
        else:
            for payload in scenario.events:
                consume(payload)

        if scenario.release_txn_ids:
            provider.release_transactions(scenario.release_txn_ids)
            for payout_id in _scenario_payout_ids(scenario, pack):
                try:
                    stripe.ingest_payout(
                        payout_id,
                        event_id_value=f"sync:{payout_id}:released",
                        event_type="payout.reconciliation_completed",
                        provider=provider,
                    )
                except Exception:
                    continue

        replay = None
        if scenario.replay_event_id:
            replay_payload = next(item for item in scenario.events if item.get("id") == scenario.replay_event_id)
            replay = _process(replay_payload, provider)
            results.append(replay)
            routing.append(
                {
                    "event_id": replay_payload.get("id"),
                    "event_type": replay_payload.get("type"),
                    "classified_workflow": "idempotency",
                    "result_workflow": replay.workflow,
                    "status": replay.status,
                    "duplicate": replay.duplicate,
                }
            )

        payout_ids = _scenario_payout_ids(scenario, pack)
        for payout in all_payouts():
            if payout.payout_id in payout_ids:
                remember_link(
                    source_document_id=payout.payout_id,
                    transaction_id=payout.payout_id,
                    reconciliation_id=payout.payout_id,
                    extra={"provider": "stripe", "arrival_date": payout.arrival_date},
                )
        bank, ledger = _bank_and_ledger(pack, payout_ids)
        as_of = "2026-10-31" if scenario.cash_period == "2026-10" else "2026-09-30"
        balances = PeriodBalances(opening_bank=0, opening_ledger=0, as_of_date=as_of)
        cash_report = None
        if bank:
            cash_report = run_cash_reconciliation(
                scenario.cash_period,
                reset=True,
                seed_providers=False,
                use_agent=bool(control.decision_mode == "agentic" and control.use_llm),
                balances=balances,
                bank=bank,
                ledger=ledger,
            )
        snapshot = ar_close_snapshot(as_of)

    payout_rows = [item for item in all_payouts() if item.payout_id in payout_ids]
    recon_rows = [item for item in all_reconciliations() if item.payout_id in payout_ids]
    primary_payout = get_payout(scenario.ground_truth.expected_payout_id) if scenario.ground_truth else None
    primary_recon = get_reconciliation(primary_payout.payout_id) if primary_payout else None
    if primary_payout and primary_recon is None:
        primary_recon = reconcile_payout(primary_payout)

    payments = [item.model_dump(mode="json") for item in all_payments() if item.source == "stripe"]
    invoices = [item.model_dump(mode="json") for item in all_invoices() if str(item.invoice_id).startswith("INV-STR-")]
    journal_rows = [item.model_dump(mode="json") for item in ar_journals()]
    application_rows = [item.model_dump(mode="json") for item in applications()]
    links = [item.model_dump(mode="json") for item in all_links()]
    relationships = {
        "invoice_to_payments": {},
        "payment_to_stripe": [],
        "refunds": [],
        "disputes": [],
        "payout_to_bank": [],
    }
    for row in application_rows:
        for item in row.get("applications") or []:
            invoice_id = item.get("invoice_id")
            if invoice_id:
                relationships["invoice_to_payments"].setdefault(invoice_id, []).append(row.get("payment_id"))
    for payment in payments:
        meta = payment.get("metadata") or {}
        relationships["payment_to_stripe"].append(
            {
                "payment_id": payment.get("payment_id"),
                "invoice_reference": payment.get("invoice_reference"),
                "amount": payment.get("amount"),
                "stripe_charge_id": meta.get("stripe_charge_id"),
                "stripe_payment_intent_id": meta.get("stripe_payment_intent_id"),
            }
        )
    for event_row in ar_events():
        details = event_row.details or {}
        if event_row.event_type == "stripe_refund":
            relationships["refunds"].append(
                {
                    "stripe_refund_id": details.get("stripe_refund_id"),
                    "payment_id": event_row.payment_id,
                    "invoice_ids": list(event_row.invoice_ids or []),
                    "amount": details.get("amount"),
                }
            )
        if event_row.event_type == "stripe_dispute":
            relationships["disputes"].append(
                {
                    "stripe_dispute_id": details.get("stripe_dispute_id"),
                    "payment_id": event_row.payment_id,
                    "invoice_ids": list(event_row.invoice_ids or []),
                    "amount": details.get("amount"),
                }
            )
    for payout in payout_rows:
        relationships["payout_to_bank"].append(
            {
                "payout_id": payout.payout_id,
                "payout_amount_cents": int(payout.amount),
                "balance_transaction_ids": [line.provider_object_id for line in payout.lines if line.provider_object_id],
                "charge_ids": [line.source_object_id for line in payout.lines if line.source_object_id],
                "bank_deposit_id": payout.bank_deposit_id,
                "bank_deposit_amount": payout.bank_deposit_amount,
            }
        )

    close_effect = "CLEAR"
    exception_code = None
    if primary_recon and primary_recon.status == "MISMATCH":
        close_effect = "BLOCK_CLOSE"
        exception_code = next(iter(primary_recon.exceptions), None)
    elif cash_report and cash_report.unexplained_difference:
        close_effect = "BLOCK_CLOSE"

    if cash_report is not None:
        for trace in cash_report.traces or []:
            control.record(
                {
                    "kind": "cash_recon",
                    "agent_invoked": bool(control.decision_mode == "agentic"),
                    "agents": [
                        name
                        for name in [
                            "Cash Reconciliation Preparer",
                            "Cash Exception Investigator" if trace.investigation else None,
                            "Cash Reconciliation Reviewer",
                        ]
                        if name
                    ],
                    "decision_requested": "Select a Python candidate or HUMAN_REVIEW; do not invent an explanation.",
                    "evidence": list(trace.evidence or []),
                    "skills": [
                        "cash-reconciliation-method-selection",
                        "reconciliation-exception-investigation",
                    ],
                    "tools_called": ["generate_all_candidates", "validate_candidate"],
                    "llm_called": bool(control.use_llm and control.decision_mode == "agentic"),
                    "final_decision": trace.status,
                    "match_type": trace.match_type,
                    "validations": ["validate_candidate", "tie_out_cents"],
                    "validation_passed": bool(trace.validation.passed) if trace.validation else False,
                    "downstream": {
                        "human_review": trace.human_review,
                        "provider_payout_id": getattr(trace.final, "provider_payout_id", None) if trace.final else None,
                    },
                }
            )

    visualization = {
        "scenario_id": scenario.scenario_id,
        "title": scenario.title,
        "difficulty": scenario.difficulty,
        "decision_class": classify_scenario(scenario.scenario_id),
        "run_mode": {
            "decision_mode": control.decision_mode,
            "memory_enabled": control.memory_enabled,
            "use_llm": control.use_llm,
        },
        "agent_invocations": list(control.records),
        "company": pack.company,
        "period": scenario.period,
        "timeline": [
            {
                "event_id": payload.get("id"),
                "event_type": payload.get("type"),
                "created": payload.get("created"),
                "object_id": ((payload.get("data") or {}).get("object") or {}).get("id"),
            }
            for payload in scenario.events
        ],
        "entities": {
            "customers": [row["customer_id"] for row in pack.customers],
            "invoices": invoices,
            "payments": payments,
            "payouts": [item.model_dump(mode="json") for item in payout_rows],
            "bank_deposits": [row for row in pack.bank_deposits if row["payout_id"] in payout_ids],
            "precedents": [item.model_dump(mode="json") for item in ar_precedents()],
        },
        "agent_routing": routing,
        "agent_actions": [item.model_dump(mode="json") for item in results],
        "reconciliation": primary_recon.model_dump(mode="json") if primary_recon else None,
        "cash_reconciliation": cash_report.model_dump(mode="json") if cash_report else None,
        "journals": journal_rows,
        "applications": application_rows,
        "relationships": relationships,
        "context_edges": links,
        "ar_events": [item.model_dump(mode="json") for item in ar_events()],
        "close": {
            "effect": close_effect,
            "exception_code": exception_code,
            "snapshot": snapshot.model_dump(mode="json"),
        },
        "forecast": {
            "settlement_period": scenario.ground_truth.expected_settlement_period if scenario.ground_truth else scenario.cash_period,
            "cash_effect_cents": int(round((primary_recon.actual_payout if primary_recon else 0) * 100)) if primary_recon and primary_recon.bank_deposit_amount is None else (
                int(round((primary_recon.bank_deposit_amount or 0) * 100)) if primary_recon else 0
            ),
        },
        "integration_events": [item.model_dump(mode="json") for item in all_events()],
        "replay": replay.model_dump(mode="json") if replay else None,
        "expected_outcome": None,
        "result": "PENDING",
        "trace_ids": [item.get("event_id") for item in routing],
    }
    if persist_root:
        dest = Path(persist_root) / "visualization" / f"{scenario.scenario_id}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(visualization, indent=2, default=str) + "\n")
        write_trace(f"stripe-sim-{scenario.scenario_id}", visualization)
    return visualization


def run_all_scenarios(
    *,
    persist_root: Path | None = None,
    scenario_ids: list[str] | None = None,
    decision_mode: str = "policy",
    memory_enabled: bool = True,
    use_llm: bool | None = None,
) -> list[dict[str, Any]]:
    pack = build_company_pack()
    rows = []
    selected = [item for item in pack.scenarios if scenario_ids is None or item.scenario_id in scenario_ids]
    for scenario in selected:
        rows.append(
            run_scenario(
                scenario,
                pack=pack,
                persist_root=persist_root,
                decision_mode=decision_mode,
                memory_enabled=memory_enabled,
                use_llm=use_llm,
            )
        )
    return rows

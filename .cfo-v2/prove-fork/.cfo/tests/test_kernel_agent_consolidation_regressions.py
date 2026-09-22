"""Kernel-side proofs that grain Bot ownership still runs old finance paths."""

from __future__ import annotations

import json
from pathlib import Path

from close.host import TASK_HANDLE, run_close_host
from invoice_ingestion.models import CanonicalInvoice, SourceRef
from invoice_ingestion.registry import configure_paths as configure_registry
from invoice_ingestion.registry import remember
from memory.scenarios import run_harbor_cross_period
from memory.store import load_memories
from models import Invoice
from simulations.stripe.pack import build_company_pack, scenario_by_id
from simulations.stripe.runtime import run_scenario
from tools import all_invoices, configure_overlay_path, load_invoice, register_runtime_invoice


def test_configure_overlay_path_is_runtime_alias(tmp_path):
    overlay = tmp_path / "ingestion-state" / "overlay.json"
    configure_overlay_path(overlay)
    invoice = Invoice(
        invoice_id="ING-ALIAS",
        vendor="Acme",
        amount=12.34,
        invoice_date="2026-09-01",
        due_date="2026-09-30",
        vendor_invoice_number="ALIAS-1",
        description="overlay alias",
    )
    register_runtime_invoice(invoice)
    assert overlay.exists()
    loaded = load_invoice("ING-ALIAS")
    assert loaded is not None
    assert loaded.amount == 12.34
    assert any(item.invoice_id == "ING-ALIAS" for item in all_invoices())


def test_registry_survives_process_reload(tmp_path):
    configure_registry(tmp_path / "ingestion-state")
    record = CanonicalInvoice(
        canonical_id="ING-REG",
        vendor="Acme",
        amount=10.0,
        invoice_date="2026-09-01",
        due_date="2026-09-30",
        vendor_invoice_number="REG-1",
        description="disk registry",
        sources=[SourceRef(source_type="email", source_id="MSG-1", agent="Email Invoice Agent")],
    )
    remember(record)
    from invoice_ingestion import registry as reg

    reg._loaded = False
    reg._canonicals.clear()
    found = reg.lookup(record)
    assert found is not None
    assert found.canonical_id == "ING-REG"


def test_close_host_writes_profile_specific_handles(tmp_path):
    computer = tmp_path / "computer"
    result = run_close_host(computer, period="2026-09", scenario="demo", live=False, reset=True)
    assert result["marked_closed"] is False
    assert result["lock_door"] == "close.month_end"
    assert (computer / result["pack_path"]).is_file()
    lock = json.loads((computer / "workspace/close/2026-09/handles/ctl-books-lock.json").read_text())
    assert lock["toSlug"] == "ctl-books"
    assert lock["profile"] == "lock"
    assert TASK_HANDLE["prepaid"] == ("ctl-books", "review-treatment")
    assert TASK_HANDLE["depreciation"] == ("ctl-books", "review-assets")
    assert TASK_HANDLE["bs_recon"] == ("ctl-books", "review-bs")
    assert result["status"] in {"BLOCKED", "IN_PROGRESS", "READY_FOR_REVIEW", "READY_TO_CLOSE"}


def test_harbor_memory_still_crosses_periods():
    result = run_harbor_cross_period(memory_enabled=True)
    memories = load_memories()
    assert any(item.period == "2026-08" for item in memories)
    lookup = result.get("september_lookup") or result["september_trace"].memory_lookup
    assert lookup is not None
    assert lookup.queried is True


def test_stripe_payout_ties_and_is_not_an_invoice():
    pack = build_company_pack()
    run = run_scenario(scenario_by_id("stripe_simple_payment", pack), pack=pack)
    payment = run["entities"]["payments"][0]
    assert payment["amount"] == 1000.00
    assert run["reconciliation"]["status"] == "MATCH"
    assert run["reconciliation"]["expected_payout"] != payment["amount"]
    assert run["reconciliation"]["bank_deposit_amount"] == 970.70
    assert all(item["invoice_id"].startswith("INV-STR-") for item in run["entities"]["invoices"])
    fee_journals = [item for item in run["journals"] if item["entry_type"] == "processor_fee"]
    assert fee_journals
    assert all(item["debit"]["account"] != "Revenue" for item in fee_journals)


def test_stripe_refund_and_chargeback_net_to_bank():
    pack = build_company_pack()
    refund = run_scenario(scenario_by_id("stripe_refund_before_payout", pack), pack=pack)
    rec = refund["reconciliation"]
    expected = rec["gross_payments"] + rec["fees"] + rec["refunds"] + rec["chargebacks"] + rec["adjustments"] + rec["other"]
    assert round(rec["expected_payout"], 2) == round(expected, 2)
    assert rec["bank_deposit_amount"] == rec["expected_payout"]
    assert rec["status"] == "MATCH"

    chargeback = run_scenario(scenario_by_id("stripe_chargeback", pack), pack=pack)
    rec = chargeback["reconciliation"]
    expected = rec["gross_payments"] + rec["fees"] + rec["refunds"] + rec["chargebacks"] + rec["adjustments"] + rec["other"]
    assert rec["status"] == "MATCH"
    assert round(rec["expected_payout"], 2) == round(expected, 2)
    assert rec["bank_deposit_amount"] == rec["expected_payout"]
    assert any(item["entry_type"] == "processor_fee" for item in chargeback["journals"])
    receipts = [item for item in chargeback["journals"] if item["entry_type"] == "cash_receipt"]
    assert len(receipts) == 1


def test_runtime_invoice_is_visible_across_workflows():
    invoice = Invoice(
        invoice_id="ING-XFLOW",
        vendor="Cross Workflow Co",
        amount=88.50,
        invoice_date="2026-09-02",
        due_date="2026-09-16",
        vendor_invoice_number="XFLOW-1",
        description="canonical overlay shared by AP, pay, close, forecast, audit",
    )
    register_runtime_invoice(invoice)
    loaded = load_invoice("ING-XFLOW")
    assert loaded is not None
    assert any(item.invoice_id == "ING-XFLOW" for item in all_invoices())

    from audit.workflow import _invoice_items
    from reporting.sources import ap_forecast_lines
    from scheduling.pool import add_approved, pool_invoice_ids

    add_approved("ING-XFLOW", source="consolidation_test")
    assert "ING-XFLOW" in pool_invoice_ids()
    assert "ING-XFLOW" in {line.source_id for line in ap_forecast_lines()}
    assert "ING-XFLOW" in {item.object_id for item in _invoice_items([])}


def test_memory_survives_fresh_process(tmp_path):
    import os
    import subprocess
    import sys

    memory_dir = tmp_path / "shared-memory"
    memory_dir.mkdir()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    env.pop("PYTEST_CURRENT_TEST", None)
    writer = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from pathlib import Path\n"
                "from memory.models import MemoryEvidence\n"
                "from memory.store import configure_paths\n"
                "from memory.write import write_decision\n"
                f"configure_paths(Path({str(memory_dir)!r}))\n"
                "record, created = write_decision("
                "period='2026-08', workflow='cash_reconciliation', entity_type='payment_provider',"
                "entity_id='stripe', situation_type='payout_difference',"
                "situation_summary='Stripe payout lower than gross receipts',"
                "evidence=[MemoryEvidence(kind='fee', label='processing_fees', amount=300.0, amount_minor=30000)],"
                "decision='reconcile payout net of fees',"
                "reasoning_summary='Difference matched fees.',"
                "accounting_treatment='net_payout_fees',"
                "outcome='EXPLAINED_EXCEPTION',"
                "reusable_precedent='Stripe payouts may arrive net of fees',"
                "source_trace_ids=['REC-PROC'], tags=['stripe'], fingerprint='fresh-proc')\n"
                "print(record.decision_id, created)\n"
            ),
        ],
        cwd=str(Path(__file__).resolve().parents[1]),
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    decision_id, created = writer.stdout.strip().split()
    assert created == "True"
    reader = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from pathlib import Path\n"
                "from memory.retrieve import lookup_memories\n"
                "from memory.models import MemoryQuery\n"
                "from memory.store import configure_paths, load_memories\n"
                f"configure_paths(Path({str(memory_dir)!r}))\n"
                "ids = {item.decision_id for item in load_memories()}\n"
                "lookup = lookup_memories(MemoryQuery(workflow='cash_reconciliation',"
                "entity_id='stripe', situation_type='payout_difference',"
                "prior_to_period='2026-09', exclude_period='2026-09'))\n"
                f"print({decision_id!r} in ids, lookup.queried, bool(lookup.precedents))\n"
            ),
        ],
        cwd=str(Path(__file__).resolve().parents[1]),
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    found, queried, precedents = reader.stdout.strip().split()
    assert found == "True"
    assert queried == "True"
    assert precedents == "True"


def test_office_slug_map_has_no_deleted_kernel_slugs():
    office = Path(__file__).resolve().parents[2] / ".cfo-v2" / "office" / "computer" / "cfo" / "slug-map.json"
    payload = json.loads(office.read_text())
    slugs = set(payload["bots"])
    assert slugs == {
        "email",
        "stripe",
        "bank",
        "books",
        "world",
        "ap",
        "pay",
        "apply",
        "collect",
        "cash",
        "close",
        "story",
        "ctl-pay",
        "ctl-cash",
        "ctl-books",
        "audit",
    }
    assert payload["bots"]["world"]["profiles"]["vendor"] == "Counterparty Message Agent"
    profiles = payload["bots"]["ctl-books"]["profiles"]
    assert profiles["review-assets"] == "Fixed Asset Reviewer"
    assert profiles["review-bs"] == "Balance Sheet Reconciliation Reviewer"
    assert payload["bots"]["email"]["profiles"]["inbox"] == "Finance Inbox Agent"


def test_prior_period_stripe_memory_does_not_hide_demo_payout():
    from cfo.scenario import _seed_august_memory
    from cash_recon.demo import load_demo_dataset, seed_provider_payouts
    from cash_recon.engine import propose_matches
    from integrations.store import get_payout

    _seed_august_memory()
    seed_provider_payouts()
    assert get_payout("po_1HackMIT97420") is not None
    _balances, bank, ledger, fees = load_demo_dataset()
    hit = next(
        item
        for item in propose_matches(bank, ledger, fees, "2026-09")
        if "TXN-2026-09-019A" in item.bank_transaction_ids
    )
    assert hit.match_type == "PROVIDER_PAYOUT"
    assert hit.provider_payout_id == "po_1HackMIT97420"

"""Canonical Maximor demo pack: validity, isolation, lineage, and reset."""

from __future__ import annotations

import json
from pathlib import Path

from demo.inventory import build_system_capabilities
from demo.reset import reset_demo_runtime
from demo.validate import validate_demo_pack
from sample_data.orchestrator import generate_sample_data
from sample_data.registry import required_ids
from skills.assignments import AGENT_SKILLS
from tools import collect_case_evidence, exception_types_for, vendor_alias_established


def test_system_capabilities_cover_registered_agents():
    payload = build_system_capabilities()
    names = {item["agent"] for item in payload["agents"]}
    assert set(AGENT_SKILLS) <= names
    assert payload["skill_registry"] == "skills/README.md"
    assert any(item["capability_id"] == "ap.three_way_match" for item in payload["capabilities"])


def test_generated_pack_includes_demo_exports(tmp_path):
    output = tmp_path / "demo"
    ctx = generate_sample_data(seed=42, period="2026-09", output=output)
    assert set(required_ids()) <= set(ctx.scenarios)
    for name in (
        "system_capabilities.json",
        "agent_cases.json",
        "lineage.json",
        "timeline.json",
        "demo_queries.json",
        "demo_snapshot.json",
        "memory_events.json",
        "expected_outcomes.json",
        "company.json",
    ):
        assert (output / name).exists(), name
    errors = validate_demo_pack(output)
    assert errors == []


def test_august_precedent_is_retrievable_for_september_alias(tmp_path):
    output = tmp_path / "demo"
    generate_sample_data(seed=42, period="2026-09", output=output)
    from sample_data.paths import data_root

    with data_root(output):
        evidence = collect_case_evidence("INV-021")
        assert "vendor_mismatch" in evidence.exception_types
        assert vendor_alias_established(evidence) is True
        assert exception_types_for("INV-001") == []


def test_overpayment_and_memory_events(tmp_path):
    output = tmp_path / "demo"
    ctx = generate_sample_data(seed=42, period="2026-09", output=output)
    assert ctx.ar_payments["PAY-007"].amount > ctx.ar_invoices["INV-AR-015"].outstanding_amount
    assert any(item.precedent_id == "AR-PREC-003" for item in ctx.ar_precedents)
    events = json.loads((output / "memory_events.json").read_text())
    assert {item["event_id"] for item in events} >= {"MEM-001", "MEM-002", "MEM-003", "MEM-004", "MEM-005"}


def test_lineage_and_timeline_reference_real_ids(tmp_path):
    output = tmp_path / "demo"
    ctx = generate_sample_data(seed=42, period="2026-09", output=output)
    lineage = json.loads((output / "lineage.json").read_text())
    assert any(row["record_id"] == "INV-001" for row in lineage)
    assert any(row["record_id"] == "INV-AR-013" for row in lineage)
    timeline = json.loads((output / "timeline.json").read_text())
    assert any(item.get("amount_cents") == 1240 for item in timeline)
    assert "INV-001" in ctx.ap_invoices
    assert ctx.bank_transactions["TXN-2026-09-015"].amount_minor - ctx.ledger_cash["GL-AR-NS"].amount_minor == 1240


def test_reset_does_not_mutate_canonical(tmp_path):
    canonical = tmp_path / "canonical"
    generate_sample_data(seed=42, period="2026-09", output=canonical)
    before = (canonical / "invoices.json").read_text()
    runtime = reset_demo_runtime(tmp_path / "runtime", source=canonical)
    (runtime / "invoices.json").write_text("[]\n")
    assert (canonical / "invoices.json").read_text() == before
    assert not (runtime / "expected_results.json").exists()
    assert (canonical / "expected_results.json").exists()


def test_repeatable_generation():
    left = generate_sample_data(seed=42, period="2026-09", output=None)
    right = generate_sample_data(seed=42, period="2026-09", output=None)
    assert sorted(left.scenarios) == sorted(right.scenarios)
    assert left.ap_invoices["INV-021"].amount == right.ap_invoices["INV-021"].amount
    assert [item.precedent_id for item in left.ar_precedents] == [item.precedent_id for item in right.ar_precedents]


def test_ledger_still_balances_after_extensions():
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    for entry in ctx.journal_entries.values():
        assert entry.amount_minor > 0
        assert entry.debit_account != entry.credit_account
    assert ctx.journal_entries["JE-AP-INV-021"].amount_minor == 1_245_000


def test_clean_invoice_is_still_clean():
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    from sample_data.paths import data_root
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as folder:
        generate_sample_data(seed=42, period="2026-09", output=Path(folder))
        with data_root(Path(folder)):
            assert exception_types_for("INV-001") == []
            assert "duplicate" in exception_types_for("INV-006")
    assert ctx.scenarios["SCN-CASH-005"].expected_behavior == "UNEXPLAINED_DIFFERENCE"


def test_agent_cases_execute_against_live_workflows(tmp_path):
    from evals.agent_cases import load_agent_cases, run_agent_cases
    from evaluation.context import operational_dataset

    exported = load_agent_cases()
    assert len(exported) == 24
    assert {item["case_id"] for item in exported} >= {
        "AC-EMAIL-CLEAN",
        "AC-AP-INVESTIGATOR-ALIAS",
        "AC-CASH-RECON-1240",
        "AC-CLOSE-REVIEW",
        "AC-VARIANCE",
    }
    with operational_dataset(Path("data/demo"), tmp_path / "agent_state"):
        payload = run_agent_cases()
    assert payload["unhandled"] == []
    assert payload["total"] == 24
    failed = [item["case_id"] for item in payload["cases"] if not item["passed"]]
    assert failed == [], failed


def test_demo_queries_are_fact_graded_not_prose(tmp_path):
    output = tmp_path / "demo"
    generate_sample_data(seed=42, period="2026-09", output=output)
    queries = json.loads((output / "demo_queries.json").read_text())
    assert len(queries) >= 12
    for item in queries:
        assert "expected_facts" in item
        assert "prompt" in item
        assert item.get("expected_prose") is None

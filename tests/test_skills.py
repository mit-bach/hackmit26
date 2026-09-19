from __future__ import annotations

import json
import re

import pytest

from agent import (
    approver_agent,
    audit_agent,
    investigator_agent,
    preparer_agent,
    reviewer_agent,
)
from ar.agents import cash_application_agent, cash_reviewer_agent, collections_agent
from accrual.agent import accrual_agent
from accrual.models import AccrualDecision
from accrual.workflow import finalize_vendor_close
from invoice_ingestion.agents import AGENTS
from invoice_ingestion.models import SOURCE_AGENTS
from invoice_ingestion.sources import run_email_source, run_erp_source
from cash_recon.agent import (
    investigator_agent as cash_recon_investigator,
    preparer_agent as cash_recon_preparer,
    reviewer_agent as cash_recon_reviewer,
)
from prepaid.agent import prepaid_preparer, prepaid_reviewer
from fixed_assets.agent import fixed_asset_preparer, fixed_asset_reviewer
from bs_recon.agent import bs_preparer, bs_reviewer
from close.agents import close_manager, month_end_reviewer
from audit.agent import audit_report_agent, auditor_agent
from reporting.agents import (
    board_reporting_agent,
    cash_forecast_agent,
    forecast_reviewer_agent,
    forecast_variance_agent,
    reporting_reviewer_agent,
    variance_analysis_agent,
)
from sample_data.agents.sdk import (
    apar_sample_data_agent,
    audit_controls_sample_data_agent,
    cash_recon_sample_data_agent,
    close_sample_data_agent,
    reporting_forecasting_sample_data_agent,
)
from scheduling.agent import payment_audit_agent, scheduler_agent
from skills.assignments import AGENT_SKILLS, resolve_agent_name, skills_for
from skills.inspect import format_agent_skills, format_skills_index
from skills.loader import (
    REQUIRED_SECTIONS,
    SkillError,
    content_hash,
    list_skill_names,
    load_skill,
    parse_skill,
    unique_skill_names,
    usage_from_agent,
    validate_skill_name,
)
from skills.validate import registry_skill_names, validate_skill_system


AGENTS_BY_NAME = {
    preparer_agent.name: preparer_agent,
    investigator_agent.name: investigator_agent,
    reviewer_agent.name: reviewer_agent,
    approver_agent.name: approver_agent,
    audit_agent.name: audit_agent,
    accrual_agent.name: accrual_agent,
    scheduler_agent.name: scheduler_agent,
    payment_audit_agent.name: payment_audit_agent,
    collections_agent.name: collections_agent,
    cash_application_agent.name: cash_application_agent,
    cash_reviewer_agent.name: cash_reviewer_agent,
    cash_recon_preparer.name: cash_recon_preparer,
    cash_recon_investigator.name: cash_recon_investigator,
    cash_recon_reviewer.name: cash_recon_reviewer,
    prepaid_preparer.name: prepaid_preparer,
    prepaid_reviewer.name: prepaid_reviewer,
    fixed_asset_preparer.name: fixed_asset_preparer,
    fixed_asset_reviewer.name: fixed_asset_reviewer,
    bs_preparer.name: bs_preparer,
    bs_reviewer.name: bs_reviewer,
    month_end_reviewer.name: month_end_reviewer,
    close_manager.name: close_manager,
    apar_sample_data_agent.name: apar_sample_data_agent,
    cash_recon_sample_data_agent.name: cash_recon_sample_data_agent,
    close_sample_data_agent.name: close_sample_data_agent,
    audit_controls_sample_data_agent.name: audit_controls_sample_data_agent,
    reporting_forecasting_sample_data_agent.name: reporting_forecasting_sample_data_agent,
    auditor_agent.name: auditor_agent,
    audit_report_agent.name: audit_report_agent,
    variance_analysis_agent.name: variance_analysis_agent,
    reporting_reviewer_agent.name: reporting_reviewer_agent,
    board_reporting_agent.name: board_reporting_agent,
    cash_forecast_agent.name: cash_forecast_agent,
    forecast_reviewer_agent.name: forecast_reviewer_agent,
    forecast_variance_agent.name: forecast_variance_agent,
}
AGENTS_BY_NAME.update({agent.name: agent for agent in AGENTS.values()})

EXPECTED_ASSIGNMENTS = {
    SOURCE_AGENTS["erp"]: (),
    SOURCE_AGENTS["edi"]: (),
    SOURCE_AGENTS["email"]: (
        "invoice-source-identification",
        "invoice-field-interpretation",
    ),
    "Accrual Agent": (
        "accrual-evidence-evaluation",
        "accrual-method-selection",
    ),
    "Payment Scheduler": (
        "payment-prioritization",
        "early-payment-discount-evaluation",
    ),
    "Collections Agent": ("ar-collections-policy",),
    "Cash Application Agent": ("cash-application",),
    "Cash Reconciliation Preparer": (
        "cash-reconciliation-method-selection",
        "bank-reference-interpretation",
    ),
}


def _registry_skill_names() -> list[str]:
    return registry_skill_names()


def test_skill_files_are_complete():
    names = list_skill_names()
    assert names, "expected skill definitions on disk"
    for name in names:
        skill = load_skill(name)
        assert skill["description"]
        assert skill["status"] in {"extracted", "existing", "new"}
        assert skill["content_hash"] == content_hash(skill["raw"])
        assert len(skill["content_hash"]) == 64
        assert skill["relpath"] == f"skills/{name}/SKILL.md"
        missing = [section for section in REQUIRED_SECTIONS if f"## {section}" not in skill["body"]]
        assert missing == [], f"{name} missing sections: {missing}"


def test_assignments_match_disk_and_registry():
    validate_skill_system(known_agents=list(AGENTS_BY_NAME))
    on_disk = set(list_skill_names())
    registered = set(_registry_skill_names())
    assert registered == on_disk


def test_representative_agent_assignments():
    for agent_name, expected in EXPECTED_ASSIGNMENTS.items():
        assert skills_for(agent_name) == expected


def test_selective_loading_excludes_unrelated_skills():
    accrual = usage_from_agent(accrual_agent)
    accrual_names = [item.name for item in accrual.skills]
    assert accrual_names == [
        "accrual-evidence-evaluation",
        "accrual-method-selection",
    ]
    assert "invoice-source-identification" not in accrual_names
    assert "payment-prioritization" not in accrual_names
    assert "early-payment-discount-evaluation" not in accrual_names

    scheduler = usage_from_agent(scheduler_agent)
    scheduler_names = [item.name for item in scheduler.skills]
    assert scheduler_names == [
        "payment-prioritization",
        "early-payment-discount-evaluation",
    ]
    assert "accrual-method-selection" not in scheduler_names
    assert "accrual-evidence-evaluation" not in scheduler_names
    assert "three-way-match-analysis" not in scheduler_names


def test_assigned_skills_are_loaded_once_and_injected():
    for agent_name, agent in AGENTS_BY_NAME.items():
        assigned = skills_for(agent_name)
        usage = usage_from_agent(agent)
        assert usage.role == agent_name
        assert usage.load_errors == []
        names = [item.name for item in usage.skills]
        assert names == list(assigned)
        assert len(names) == len(set(names))
        instructions = agent.instructions
        assert isinstance(instructions, str)
        for ref in usage.skills:
            skill = load_skill(ref.name)
            assert instructions.count(f"## Skill: {ref.name}") == 1
            assert instructions.count(skill["body"]) == 1
            assert ref.injected is True
            assert ref.content_hash == skill["content_hash"]
            dumped = ref.model_dump()
            assert "body" not in dumped
            assert dumped["path"] == f"skills/{ref.name}/SKILL.md"


def test_erp_and_edi_have_no_skills():
    assert skills_for(SOURCE_AGENTS["erp"]) == ()
    assert skills_for(SOURCE_AGENTS["edi"]) == ()
    assert usage_from_agent(AGENTS["erp"]).skills == []
    assert usage_from_agent(AGENTS["edi"]).skills == []
    assert "Assigned skills:" not in AGENTS["erp"].instructions
    assert "Assigned skills:" not in AGENTS["edi"].instructions


def test_every_known_agent_has_an_assignment_entry():
    for name in AGENTS_BY_NAME:
        assert name in AGENT_SKILLS, f"missing skill assignment for {name}"
    for source_name in SOURCE_AGENTS.values():
        assert source_name in AGENT_SKILLS


def test_content_hash_is_deterministic_and_changes_with_text():
    skill = load_skill("accrual-method-selection")
    assert load_skill("accrual-method-selection")["content_hash"] == skill["content_hash"]
    assert content_hash(skill["raw"]) == skill["content_hash"]
    assert content_hash(skill["raw"] + "\n") != skill["content_hash"]


def test_malformed_or_duplicate_skills_fail_in_python():
    with pytest.raises(SkillError, match="Malformed skill name"):
        validate_skill_name("../secret")
    with pytest.raises(SkillError, match="Malformed skill name"):
        validate_skill_name("Not A Skill")
    with pytest.raises(SkillError, match="Duplicate skill assignment"):
        unique_skill_names(("accrual-method-selection", "accrual-method-selection"))
    with pytest.raises(SkillError, match="Unknown skill"):
        load_skill("no-such-skill")


def test_empty_skill_file_fails(tmp_path):
    path = tmp_path / "SKILL.md"
    path.write_text("\n")
    with pytest.raises(SkillError, match="empty"):
        parse_skill(path)


def test_validate_rejects_registry_disagreement():
    with pytest.raises(SkillError, match="registry and assignments disagree"):
        validate_skill_system(
            registry_text=(
                "## Registry\n\n"
                "| not-a-real-skill | demo |\n\n"
                "## Agents with no assigned skills\n"
            )
        )


def test_validate_rejects_unknown_agent_identifier():
    with pytest.raises(SkillError, match="unknown agent identifier"):
        validate_skill_system(known_agents=["AP Preparer"])


def test_validate_rejects_missing_skill_file(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    registry = "## Registry\n\n## Agents with no assigned skills\n"
    with pytest.raises(SkillError, match="does not exist"):
        validate_skill_system(
            {"Demo Agent": ("missing-skill",)},
            skills_dir=skills_dir,
            registry_text=registry,
        )


def test_ingestion_traces_include_skill_usage():
    email = run_email_source("2026-09")
    assert email.skill_usage is not None
    assert email.skill_usage.role == SOURCE_AGENTS["email"]
    assert [item.name for item in email.skill_usage.skills] == [
        "invoice-source-identification",
        "invoice-field-interpretation",
    ]
    assert all(item.injected for item in email.skill_usage.skills)
    erp = run_erp_source("2026-09")
    assert erp.skill_usage is not None
    assert erp.skill_usage.skills == []
    assert erp.skill_usage.load_errors == []


def test_accrual_trace_records_skill_hashes(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    monkeypatch.setattr("accrual.ledger.LEDGER_DIR", tmp_path)
    raw = AccrualDecision(
        vendor="Aether Compute",
        period="2026-09",
        status="accrual_required",
        estimated_amount=11849.90,
        confidence=0.91,
        estimation_method="usage_run_rate",
        evidence=["September usage"],
        reasoning_summary="Usage times the committed rate.",
    )
    _decision, trace = finalize_vendor_close("Aether Compute", "2026-09", raw, run_id="skills")
    assert trace.agent is not None
    assert trace.agent.role == "Accrual Agent"
    assert [item.name for item in trace.agent.skills] == [
        "accrual-evidence-evaluation",
        "accrual-method-selection",
    ]
    dumped = trace.model_dump()["agent"]
    assert dumped["load_errors"] == []
    for item in dumped["skills"]:
        assert re.fullmatch(r"[0-9a-f]{64}", item["content_hash"])
        assert item["injected"] is True
        assert "body" not in item


def test_inspect_index_lists_assignments_without_bodies():
    text = format_skills_index()
    assert "Accrual Agent\n  accrual-evidence-evaluation\n  accrual-method-selection" in text
    assert "Payment Scheduler\n  payment-prioritization\n  early-payment-discount-evaluation" in text
    assert "ERP Invoice Agent\n  (none)" in text
    assert "## Purpose" not in text
    detail = format_agent_skills("accrual")
    assert "accrual-method-selection" in detail
    assert "content_hash:" in detail
    assert "skills/accrual-method-selection/SKILL.md" in detail
    assert "injected: yes" in detail
    assert "## Procedure" not in detail
    assert resolve_agent_name("accrual") == "Accrual Agent"


def test_skills_do_not_claim_python_jobs():
    forbidden = (
        "recalculate the tax",
        "compute sha256",
        "hash the document",
        "sum the line items yourself",
    )
    for name in list_skill_names():
        body = load_skill(name)["body"].lower()
        for phrase in forbidden:
            assert phrase not in body, f"{name} looks like deterministic logic"
        assert "do not recalculate" in body or "do not calculate" in body or "python" in body

"""Prove the 15-bot office still owns every meaningful 43-agent responsibility."""

from __future__ import annotations

import json
from pathlib import Path

from handles import GRAIN_SLUGS, SAMPLE_DATA_DISPLAY_NAMES, destination
from compiler.compile_lib import compile_catalog

REPO = Path(__file__).resolve().parents[3]
KERNEL = REPO / ".cfo"
OFFICE = REPO / ".cfo-v2" / "office"
SLUG_MAP = OFFICE / "computer" / "cfo" / "slug-map.json"
GRANTS = OFFICE / "computer" / "cfo" / "grants.json"
ROSTER = OFFICE / "computer" / "harness" / "roster.json"
SKILLS_COMPUTER = OFFICE / "computer" / "skills"
SKILLS_KERNEL = KERNEL / "skills"

OLD_DISPLAY_NAMES = [
    "Counterparty Message Agent",
    "Finance Inbox Agent",
    "Email Invoice Agent",
    "ERP Invoice Agent",
    "Procurement Invoice Agent",
    "Vendor Portal Agent",
    "Employee Submission Agent",
    "Physical Mail / Document Agent",
    "EDI / Electronic Invoicing Agent",
    "Bank/Card Discovery Agent",
    "AP Preparer",
    "Exception Investigator",
    "AP Reviewer",
    "AP Approver",
    "AP Audit",
    "Accrual Agent",
    "Payment Scheduler",
    "Payment Audit",
    "Collections Agent",
    "Cash Application Agent",
    "Cash Application Reviewer",
    "Cash Reconciliation Preparer",
    "Cash Exception Investigator",
    "Cash Reconciliation Reviewer",
    "Prepaid Preparer",
    "Prepaid Reviewer",
    "Fixed Asset Preparer",
    "Fixed Asset Reviewer",
    "Balance Sheet Reconciliation Preparer",
    "Balance Sheet Reconciliation Reviewer",
    "Month-End Close Reviewer",
    "Close Manager",
    "Auditor Agent",
    "Audit Report Agent",
    "Variance Analysis Agent",
    "Reporting Reviewer Agent",
    "Board Reporting Agent",
    "Cash Forecast Agent",
    "Forecast Reviewer Agent",
    "Forecast Variance Agent",
    "AP/AR Sample Data Agent",
    "Cash Recon Sample Data Agent",
    "Close Sample Data Agent",
    "Audit Controls Sample Data Agent",
    "Reporting Forecasting Sample Data Agent",
]

INTENTIONAL_NON_BOTS = {
    "Counterparty Message Agent": "fixture sender, not an office worker",
    "Reporting Reviewer Agent": "audit samples the pack; kernel validators remain",
    "Forecast Reviewer Agent": "audit samples the pack; kernel validators remain",
    "AP/AR Sample Data Agent": "eval/sample data, not a grain bot",
    "Cash Recon Sample Data Agent": "eval/sample data, not a grain bot",
    "Close Sample Data Agent": "eval/sample data, not a grain bot",
    "Audit Controls Sample Data Agent": "eval/sample data, not a grain bot",
    "Reporting Forecasting Sample Data Agent": "eval/sample data, not a grain bot",
}

SHARED_PROFILES = {
    "AP Approver": ("ctl-pay", "review-match"),
    "AP Audit": ("ctl-pay", "review-match"),
}


def _slug_map() -> dict:
    return json.loads(SLUG_MAP.read_text(encoding="utf-8"))


def _grants() -> dict:
    return json.loads(GRANTS.read_text(encoding="utf-8"))["byDisplayName"]


def _display_to_bot() -> dict[str, tuple[str, str]]:
    mapping: dict[str, tuple[str, str]] = {}
    for slug, row in _slug_map()["bots"].items():
        for profile, display in row["profiles"].items():
            if display:
                mapping[display] = (slug, profile)
    return mapping


def test_office_still_has_exactly_fifteen_bots() -> None:
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    assert [bot["slug"] for bot in roster["bots"]] == list(GRAIN_SLUGS)
    assert len(roster["bots"]) == 15


def test_every_old_display_name_has_an_owner() -> None:
    mapping = _display_to_bot()
    grants = _grants()
    missing = []
    for name in OLD_DISPLAY_NAMES:
        if name in mapping:
            continue
        if name in SHARED_PROFILES:
            bot, profile = SHARED_PROFILES[name]
            assert mapping["AP Reviewer"] == (bot, profile)
            continue
        if name in INTENTIONAL_NON_BOTS:
            assert name in grants, f"{name} dropped from compiled grants"
            continue
        missing.append(name)
    assert missing == []


def test_reviewer_tools_are_not_unioned_onto_operator_bots() -> None:
    mapping = _display_to_bot()
    assert mapping["AP Preparer"][0] == "ap"
    assert mapping["AP Reviewer"] == ("ctl-pay", "review-match")
    assert SHARED_PROFILES["AP Approver"] == ("ctl-pay", "review-match")
    assert SHARED_PROFILES["AP Audit"] == ("ctl-pay", "review-match")
    assert mapping["Payment Scheduler"][0] == "pay"
    assert mapping["Payment Audit"][0] == "ctl-pay"
    grants = _grants()
    assert "tools.get_invoice" in grants["AP Preparer"]["ops"]
    assert "tools.get_invoice" not in grants["AP Reviewer"]["ops"]
    assert "tools.get_invoice" not in grants["AP Approver"]["ops"]
    assert "scheduling.tools.get_payment_candidates" in grants["Payment Scheduler"]["ops"]
    assert "scheduling.tools.get_payment_candidates" not in grants["Payment Audit"]["ops"]


def test_memory_tool_survived_consolidation() -> None:
    grants = _grants()
    for name in (
        "Exception Investigator",
        "Accrual Agent",
        "Cash Exception Investigator",
        "Prepaid Preparer",
        "Prepaid Reviewer",
        "Cash Reconciliation Reviewer",
    ):
        assert "memory.tools.get_decision_memories" in grants[name]["ops"], name
        assert "prior-period-precedent" in grants[name]["skills"], name


def test_inbox_and_source_tools_are_granted() -> None:
    grants = _grants()
    assert "inbox.tools.dispatch_inbox_action" in grants["Finance Inbox Agent"]["ops"]
    assert "inbox.tools.dispatch_inbox_action" not in grants["Counterparty Message Agent"]["ops"]
    assert "invoice_ingestion.tools.get_email" in grants["Email Invoice Agent"]["ops"]
    mapping = _display_to_bot()
    assert mapping["Finance Inbox Agent"] == ("email", "inbox")
    assert "Counterparty Message Agent" not in mapping


def test_ctl_books_profiles_keep_fa_and_bs_tools_without_union() -> None:
    mapping = _display_to_bot()
    assert mapping["Prepaid Reviewer"] == ("ctl-books", "review-treatment")
    assert mapping["Fixed Asset Reviewer"] == ("ctl-books", "review-assets")
    assert mapping["Balance Sheet Reconciliation Reviewer"] == ("ctl-books", "review-bs")
    grants = _grants()
    prepaid_ops = set(grants["Prepaid Reviewer"]["ops"])
    fa_ops = set(grants["Fixed Asset Reviewer"]["ops"])
    bs_ops = set(grants["Balance Sheet Reconciliation Reviewer"]["ops"])
    assert prepaid_ops.isdisjoint(fa_ops)
    assert prepaid_ops.isdisjoint(bs_ops)
    assert "fixed_assets.tools.get_fixed_asset" in fa_ops
    assert "bs_recon.tools.get_reconciliation_packet" in bs_ops
    assert destination("close", "treatment") == ("ctl-books", "review-treatment")
    assert destination("close", "assets-treatment") == ("ctl-books", "review-assets")
    assert destination("close", "bs-treatment") == ("ctl-books", "review-bs")


def test_required_skills_exist_on_computer_or_kernel() -> None:
    required = {
        "prior-period-precedent",
        "month-end-close-review",
        "three-way-match-analysis",
        "inbox-triage",
        "bank-charge-invoice-discovery",
        "accrual-method-selection",
    }
    for name in required:
        computer = SKILLS_COMPUTER / name / "SKILL.md"
        kernel = SKILLS_KERNEL / name / "SKILL.md"
        assert computer.is_file() or kernel.is_file(), name
    assert (SKILLS_COMPUTER / "prior-period-precedent" / "SKILL.md").is_file()
    assert (SKILLS_COMPUTER / "month-end-close-review" / "SKILL.md").is_file()


def test_no_deleted_agent_names_on_grain_roster() -> None:
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    slugs = {bot["slug"] for bot in roster["bots"]}
    assert slugs.isdisjoint(SAMPLE_DATA_DISPLAY_NAMES)
    assert "ingest" not in slugs
    assert "ar" not in slugs
    for bot in roster["bots"]:
        assert bot["approvalLevel"] == "never"
        assert "ask a human" in bot["instructions"].lower() or "Never ask a human" in bot["instructions"]


def test_compile_matches_checked_in_grants(tmp_path) -> None:
    out = tmp_path / "cfo"
    out.mkdir()
    overrides = OFFICE / "computer" / "cfo" / "catalog.overrides.json"
    (out / "catalog.overrides.json").write_text(overrides.read_text(encoding="utf-8"))
    result = compile_catalog(kernel=KERNEL, out_dir=out, phase="operational")
    current = json.loads(GRANTS.read_text(encoding="utf-8"))
    assert set(result.grants["byDisplayName"]) == set(current["byDisplayName"])
    for name, row in result.grants["byDisplayName"].items():
        assert row["ops"] == current["byDisplayName"][name]["ops"], name
        assert row["skills"] == current["byDisplayName"][name]["skills"], name

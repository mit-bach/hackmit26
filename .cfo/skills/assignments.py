"""Canonical agent → skill assignments.

Keep this mapping and skills/README.md in sync. Agents receive only the
skills required for their job; they do not load the full catalog.
"""

from __future__ import annotations

from skills.loader import list_skill_names, load_skill

# Agent display names must match Agent.name / SOURCE_AGENTS values.
AGENT_SKILLS: dict[str, tuple[str, ...]] = {
    "Email Invoice Agent": (
        "invoice-source-identification",
        "invoice-field-interpretation",
    ),
    "ERP Invoice Agent": (),
    "Procurement Invoice Agent": ("invoice-source-identification",),
    "Vendor Portal Agent": (
        "invoice-source-identification",
        "invoice-field-interpretation",
    ),
    "Employee Submission Agent": (
        "invoice-source-identification",
        "invoice-field-interpretation",
    ),
    "Physical Mail / Document Agent": (
        "invoice-source-identification",
        "invoice-field-interpretation",
    ),
    "EDI / Electronic Invoicing Agent": (),
    "Bank/Card Discovery Agent": ("bank-charge-invoice-discovery",),
    "AP Preparer": ("three-way-match-analysis",),
    "Exception Investigator": (
        "three-way-match-analysis",
        "ap-exception-investigation",
        "prior-period-precedent",
    ),
    "AP Reviewer": (
        "three-way-match-analysis",
        "ap-exception-investigation",
        "prior-period-precedent",
    ),
    "AP Approver": (
        "three-way-match-analysis",
        "ap-exception-investigation",
        "prior-period-precedent",
    ),
    "AP Audit": (
        "three-way-match-analysis",
        "ap-exception-investigation",
    ),
    "Accrual Agent": (
        "accrual-evidence-evaluation",
        "accrual-method-selection",
    ),
    "Payment Scheduler": (
        "payment-prioritization",
        "early-payment-discount-evaluation",
    ),
    "Payment Audit": (
        "payment-prioritization",
        "early-payment-discount-evaluation",
    ),
    "Collections Agent": ("ar-collections-policy",),
    "Cash Application Agent": ("cash-application",),
    "Cash Application Reviewer": ("cash-application",),
    "Cash Reconciliation Preparer": (
        "cash-reconciliation-method-selection",
        "bank-reference-interpretation",
    ),
    "Cash Exception Investigator": (
        "reconciliation-exception-investigation",
        "bank-reference-interpretation",
        "prior-period-precedent",
    ),
    "Cash Reconciliation Reviewer": (
        "cash-reconciliation-method-selection",
        "reconciliation-exception-investigation",
        "prior-period-precedent",
    ),
    "Prepaid Preparer": ("prepaid-expense-accounting", "prior-period-precedent"),
    "Prepaid Reviewer": ("prepaid-expense-accounting", "prior-period-precedent"),
    "Fixed Asset Preparer": ("fixed-asset-depreciation",),
    "Fixed Asset Reviewer": ("fixed-asset-depreciation",),
    "Balance Sheet Reconciliation Preparer": ("balance-sheet-reconciliation",),
    "Balance Sheet Reconciliation Reviewer": ("balance-sheet-reconciliation",),
    "Month-End Close Reviewer": ("month-end-close-review",),
    "Close Manager": ("month-end-close-coordination",),
    "Auditor Agent": (
        "audit-sampling-interpretation",
        "control-testing-interpretation",
        "reconciliation-reperformance-review",
        "segregation-of-duties-interpretation",
    ),
    "Audit Report Agent": ("audit-finding-writing",),
    "Variance Analysis Agent": ("financial-variance-analysis",),
    "Reporting Reviewer Agent": (
        "financial-variance-analysis",
        "board-financial-reporting",
    ),
    "Board Reporting Agent": ("board-financial-reporting",),
    "Cash Forecast Agent": (
        "cash-forecasting",
        "ar-cash-forecasting",
    ),
    "Forecast Reviewer Agent": (
        "cash-forecasting",
        "ar-cash-forecasting",
        "forecast-vs-actual-interpretation",
    ),
    "Forecast Variance Agent": ("forecast-vs-actual-interpretation",),
    "AP/AR Sample Data Agent": (
        "synthetic-finance-scenario-design",
        "cross-ledger-data-consistency",
    ),
    "Cash Recon Sample Data Agent": (
        "synthetic-finance-scenario-design",
        "cross-ledger-data-consistency",
    ),
    "Close Sample Data Agent": (
        "synthetic-finance-scenario-design",
        "cross-ledger-data-consistency",
    ),
    "Audit Controls Sample Data Agent": (
        "synthetic-finance-scenario-design",
        "cross-ledger-data-consistency",
    ),
    "Reporting Forecasting Sample Data Agent": (
        "synthetic-finance-scenario-design",
        "cross-ledger-data-consistency",
    ),
}

AGENT_ALIASES: dict[str, str] = {
    "email": "Email Invoice Agent",
    "erp": "ERP Invoice Agent",
    "procurement": "Procurement Invoice Agent",
    "vendor-portal": "Vendor Portal Agent",
    "vendor_portal": "Vendor Portal Agent",
    "employee": "Employee Submission Agent",
    "document": "Physical Mail / Document Agent",
    "edi": "EDI / Electronic Invoicing Agent",
    "bank": "Bank/Card Discovery Agent",
    "bank-card": "Bank/Card Discovery Agent",
    "preparer": "AP Preparer",
    "investigator": "Exception Investigator",
    "reviewer": "AP Reviewer",
    "approver": "AP Approver",
    "ap-audit": "AP Audit",
    "accrual": "Accrual Agent",
    "scheduler": "Payment Scheduler",
    "payment-scheduler": "Payment Scheduler",
    "payment": "Payment Scheduler",
    "payment-audit": "Payment Audit",
    "collections": "Collections Agent",
    "ar-collections": "Collections Agent",
    "cash-application": "Cash Application Agent",
    "cash-apply": "Cash Application Agent",
    "cash-reviewer": "Cash Application Reviewer",
    "cash-recon-preparer": "Cash Reconciliation Preparer",
    "cash-recon-investigator": "Cash Exception Investigator",
    "cash-recon-reviewer": "Cash Reconciliation Reviewer",
    "cash-recon": "Cash Reconciliation Preparer",
    "prepaid": "Prepaid Preparer",
    "prepaid-preparer": "Prepaid Preparer",
    "prepaid-reviewer": "Prepaid Reviewer",
    "fixed-asset": "Fixed Asset Preparer",
    "fixed-asset-preparer": "Fixed Asset Preparer",
    "fixed-asset-reviewer": "Fixed Asset Reviewer",
    "bs-recon": "Balance Sheet Reconciliation Preparer",
    "bs-recon-preparer": "Balance Sheet Reconciliation Preparer",
    "bs-recon-reviewer": "Balance Sheet Reconciliation Reviewer",
    "close-reviewer": "Month-End Close Reviewer",
    "month-end": "Month-End Close Reviewer",
    "close-manager": "Close Manager",
    "auditor": "Auditor Agent",
    "independent-audit": "Auditor Agent",
    "audit-report": "Audit Report Agent",
    "variance": "Variance Analysis Agent",
    "flux": "Variance Analysis Agent",
    "reporting-reviewer": "Reporting Reviewer Agent",
    "board": "Board Reporting Agent",
    "forecast": "Cash Forecast Agent",
    "forecast-reviewer": "Forecast Reviewer Agent",
    "forecast-variance": "Forecast Variance Agent",
    "forecast-miss": "Forecast Variance Agent",
    "sample-ap-ar": "AP/AR Sample Data Agent",
    "sample-cash": "Cash Recon Sample Data Agent",
    "sample-close": "Close Sample Data Agent",
    "sample-audit": "Audit Controls Sample Data Agent",
    "sample-reporting": "Reporting Forecasting Sample Data Agent",
}


def resolve_agent_name(query: str) -> str:
    text = query.strip()
    if not text:
        raise KeyError("Agent name is empty")
    if text in AGENT_SKILLS:
        return text
    alias = AGENT_ALIASES.get(text.lower())
    if alias:
        return alias
    lowered = {name.lower(): name for name in AGENT_SKILLS}
    if text.lower() in lowered:
        return lowered[text.lower()]
    raise KeyError(f"Unknown agent {query!r}")


def skills_for(agent_name: str) -> tuple[str, ...]:
    if agent_name not in AGENT_SKILLS:
        raise KeyError(f"No skill assignment registered for agent {agent_name!r}")
    return AGENT_SKILLS[agent_name]


def assigned_skill_names() -> set[str]:
    names: set[str] = set()
    for assigned in AGENT_SKILLS.values():
        names.update(assigned)
    return names


def skill_used_by(skill_name: str) -> list[str]:
    return [agent for agent, skills in AGENT_SKILLS.items() if skill_name in skills]


def catalog() -> list[dict]:
    """Disk skills plus the agents currently assigned to each one."""
    rows = []
    for name in list_skill_names():
        skill = load_skill(name)
        rows.append(
            {
                "name": name,
                "description": skill["description"],
                "status": skill["status"],
                "path": f"skills/{name}/SKILL.md",
                "used_by": skill_used_by(name),
            }
        )
    return rows

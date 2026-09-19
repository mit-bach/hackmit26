"""Read-only tools for the Auditor Agent. None of these mutate finance records."""

from __future__ import annotations

from agents import function_tool

from audit.store import (
    load_approvals,
    load_ground_truth,
    load_invoices,
    load_journals,
    load_operational_decisions,
    load_payments,
    load_period,
    load_planted_reconciliations,
    load_policy,
    load_vendors,
)


def _dump(model) -> dict:
    return model.model_dump(mode="json")


@function_tool
def get_audit_period(period: str) -> dict:
    """Return the structured accounting-period close record used by audit."""
    return {"found": True, "period": _dump(load_period(period))}


@function_tool
def get_audit_payments() -> dict:
    """Return dedicated audit payment fixtures. Does not change AP or the payment pool."""
    return {"found": True, "payments": [_dump(item) for item in load_payments()]}


@function_tool
def get_audit_journals() -> dict:
    """Return dedicated audit journal-entry fixtures."""
    return {"found": True, "journal_entries": [_dump(item) for item in load_journals()]}


@function_tool
def get_audit_approvals() -> dict:
    """Return dedicated approval/SOD fixtures with identity IDs."""
    return {"found": True, "approvals": [_dump(item) for item in load_approvals()]}


@function_tool
def get_operational_decisions() -> dict:
    """Return what the operational AP/AR/recon workflows recorded. Read-only."""
    return {"found": True, "decisions": [_dump(item) for item in load_operational_decisions()]}


@function_tool
def get_audit_policy() -> dict:
    """Return configured audit thresholds and SOD rules. Do not invent other thresholds."""
    return {"found": True, "policy": load_policy().model_dump(mode="json")}


@function_tool
def get_audit_vendors() -> dict:
    """Return vendor master fixtures used for new-vendor and duplicate-vendor tests."""
    return {"found": True, "vendors": [_dump(item) for item in load_vendors()]}


@function_tool
def get_audit_invoices() -> dict:
    """Return audit-only invoice fixtures, including planted duplicates."""
    return {"found": True, "invoices": [_dump(item) for item in load_invoices()]}


@function_tool
def get_planted_reconciliations() -> dict:
    """Return planted original reconciliation conclusions for later comparison only."""
    return {
        "found": True,
        "reconciliations": [_dump(item) for item in load_planted_reconciliations()],
    }


@function_tool
def get_audit_ground_truth() -> dict:
    """Return deterministic planted-case labels for evaluation. Do not change them."""
    return {"found": True, "ground_truth": load_ground_truth()}

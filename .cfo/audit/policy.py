"""Configurable audit policies. Thresholds live here, not in agent prompts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RoundNumberPolicy(BaseModel):
    divisors: list[float] = Field(default_factory=lambda: [100.0, 1000.0, 10000.0])
    min_amount: float = 100.0
    high_risk_min_amount: float = 10000.0
    ordinary_recurring_max: float = 500.0
    ordinary_recurring_divisors: list[float] = Field(default_factory=lambda: [100.0])
    elevate_manual_new_vendor: bool = True


class SodRule(BaseModel):
    rule_id: str
    object_types: list[str]
    forbidden_pairs: list[tuple[str, str]]
    policy_reference: str
    description: str = ""


class SodPolicy(BaseModel):
    rules: list[SodRule] = Field(default_factory=list)


class SeverityPolicy(BaseModel):
    material_amount: float = 10000.0
    critical_amount: float = 50000.0
    recon_tolerance: float = 0.01


class AuditPolicy(BaseModel):
    round_number: RoundNumberPolicy = Field(default_factory=RoundNumberPolicy)
    sod: SodPolicy = Field(default_factory=SodPolicy)
    severity: SeverityPolicy = Field(default_factory=SeverityPolicy)


DEFAULT_SOD_RULES = [
    SodRule(
        rule_id="SOD-001",
        object_types=["invoice", "invoice_approval", "payment"],
        forbidden_pairs=[("requester_id", "approver_id"), ("initiator_id", "approver_id")],
        policy_reference="SOD-P-001",
        description="Requester or payment initiator cannot be the final approver.",
    ),
    SodRule(
        rule_id="SOD-002",
        object_types=["journal", "journal_entry"],
        forbidden_pairs=[("preparer_id", "approver_id")],
        policy_reference="SOD-P-002",
        description="Journal preparer cannot approve the same entry.",
    ),
    SodRule(
        rule_id="SOD-003",
        object_types=["invoice", "invoice_approval", "journal", "journal_entry"],
        forbidden_pairs=[("preparer_id", "reviewer_id"), ("requester_id", "reviewer_id")],
        policy_reference="SOD-P-003",
        description="Independent review is required when a reviewer is assigned.",
    ),
]


def default_policy() -> AuditPolicy:
    return AuditPolicy(sod=SodPolicy(rules=list(DEFAULT_SOD_RULES)))


def policy_from_raw(raw: dict[str, Any] | None) -> AuditPolicy:
    if not raw:
        return default_policy()
    round_raw = raw.get("round_number") or {}
    sod_raw = raw.get("sod") or {}
    severity_raw = raw.get("severity") or {}
    rules = []
    for item in sod_raw.get("rules") or []:
        pairs = [tuple(pair) for pair in item.get("forbidden_pairs") or []]
        rules.append(
            SodRule(
                rule_id=item["rule_id"],
                object_types=list(item.get("object_types") or []),
                forbidden_pairs=pairs,  # type: ignore[arg-type]
                policy_reference=item.get("policy_reference") or item["rule_id"],
                description=item.get("description") or "",
            )
        )
    if not rules:
        rules = list(DEFAULT_SOD_RULES)
    return AuditPolicy(
        round_number=RoundNumberPolicy.model_validate(round_raw) if round_raw else RoundNumberPolicy(),
        sod=SodPolicy(rules=rules),
        severity=SeverityPolicy.model_validate(severity_raw) if severity_raw else SeverityPolicy(),
    )

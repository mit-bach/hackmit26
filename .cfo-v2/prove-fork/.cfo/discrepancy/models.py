"""Typed discrepancy contracts. Evaluation-only; agents never see these."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Severity = Literal["INFO", "LOW", "MEDIUM", "HIGH", "BLOCKING"]
Domain = Literal["ap", "ar", "cash", "close", "audit", "reporting", "forecasting", "cross_function"]


class DiscrepancyContract(BaseModel):
    discrepancy_id: str
    domain: Domain
    type: str
    source_ids: list[str] = Field(default_factory=list)
    expected_detection: str
    expected_disposition: str
    expected_status: str = ""
    expected_amount_cents: int | None = None
    must_surface: bool = True
    allowed_reason_codes: list[str] = Field(default_factory=list)
    must_not_do: list[str] = Field(default_factory=list)
    severity: Severity = "MEDIUM"
    downstream_impact: str = ""
    description: str = ""


class DiscrepancyCaseResult(BaseModel):
    discrepancy_id: str
    domain: Domain
    detected: bool = False
    surfaced_ids: list[str] = Field(default_factory=list)
    actual_status: Any = None
    actual_amount_cents: int | None = None
    actual_reason: str = ""
    passed: bool = False
    partial: bool = False
    unsafe: bool = False
    agent: str = ""
    reason: str = ""
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class DomainDiscrepancyResult(BaseModel):
    domain: Domain
    total: int = 0
    detected: int = 0
    passed: int = 0
    failed: int = 0
    cases: list[DiscrepancyCaseResult] = Field(default_factory=list)


class FixRecord(BaseModel):
    discrepancy_id: str
    failing_agent: str
    failure_reason: str
    files_changed: list[str] = Field(default_factory=list)
    behavior_changed: str = ""
    regression_test: str = ""
    final_status: str = ""


class DiscrepancyBenchmark(BaseModel):
    run_id: str
    data_root: str
    seed: int
    period: str
    function_results: list[DomainDiscrepancyResult] = Field(default_factory=list)
    discrepancy_recall: float = 0.0
    discrepancy_precision: float = 0.0
    false_positive_rate: float = 0.0
    unsafe_auto_resolution_rate: float = 0.0
    passed: int = 0
    failed: int = 0
    total: int = 0
    generated_at: str = ""
    output_dir: str = ""
    phase: str = "initial"

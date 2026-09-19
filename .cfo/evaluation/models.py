"""Typed benchmark artifacts. Scoring stays in deterministic Python."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

CaseStatus = Literal["PASS", "PARTIAL", "FAIL", "ERROR", "EXPECTED_HUMAN_REVIEW"]
Domain = Literal["ap", "ar", "cash", "close", "audit", "reporting", "forecasting", "end_to_end"]
ReviewClass = Literal["AUTO_RESOLVE_EXPECTED", "HUMAN_REVIEW_EXPECTED"]
ErrorType = Literal[
    "WRONG_MATCH",
    "MISSED_EXCEPTION",
    "FALSE_POSITIVE_EXCEPTION",
    "WRONG_APPROVAL",
    "UNSAFE_AUTO_RESOLUTION",
    "UNNECESSARY_HUMAN_REVIEW",
    "WRONG_AMOUNT",
    "WRONG_ACCOUNT",
    "WRONG_PERIOD",
    "BROKEN_LINEAGE",
    "UNSUPPORTED_SOURCE",
    "FORECAST_SOURCE_MISSING",
    "VARIANCE_DRIVER_MISATTRIBUTED",
    "CONTROL_FAILURE_MISSED",
    "FALSE_AUDIT_FINDING",
    "WORKFLOW_ERROR",
]


class EvaluationCaseResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    case_id: str
    domain: Domain
    scenario_id: str
    status: CaseStatus
    expected: Any = None
    actual: Any = None
    score: float = 0.0
    reason: str = ""
    source_ids: list[str] = Field(default_factory=list)
    agent_run_id: str = ""
    requires_human_review: bool = False
    review_class: ReviewClass = "AUTO_RESOLVE_EXPECTED"
    latency_ms: Optional[float] = None
    error_type: Optional[ErrorType] = None
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class FunctionEvaluationResult(BaseModel):
    domain: Domain
    cases_total: int = 0
    cases_passed: int = 0
    cases_partial: int = 0
    cases_failed: int = 0
    cases_error: int = 0
    accuracy: float = 0.0
    precision: Optional[float] = None
    recall: Optional[float] = None
    false_positive_count: int = 0
    false_negative_count: int = 0
    human_review_cases: int = 0
    correct_human_review_cases: int = 0
    score: float = 0.0
    metrics: dict[str, float] = Field(default_factory=dict)
    case_results: list[EvaluationCaseResult] = Field(default_factory=list)
    workflow_error: str = ""


class HumanReviewMetrics(BaseModel):
    human_review_precision: float = 0.0
    human_review_recall: float = 0.0
    unnecessary_escalation_rate: float = 0.0
    unsafe_auto_resolution_rate: float = 0.0
    unsafe_auto_resolution_count: int = 0
    unnecessary_escalation_count: int = 0


class EndToEndResult(BaseModel):
    storyline_id: str
    status: CaseStatus
    score: float = 0.0
    assertions: list[EvaluationCaseResult] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)


class OverallMetrics(BaseModel):
    cases_total: int = 0
    cases_passed: int = 0
    cases_partial: int = 0
    cases_failed: int = 0
    cases_error: int = 0
    overall_score: float = 0.0
    cross_function_consistency_score: float = 0.0
    human_review: HumanReviewMetrics = Field(default_factory=HumanReviewMetrics)
    error_counts: dict[str, int] = Field(default_factory=dict)


class RegressionDelta(BaseModel):
    metric: str
    baseline: float
    current: float
    delta: float
    regression: bool = False


class BenchmarkResult(BaseModel):
    run_id: str
    seed: int
    period: str
    data_root: str
    dataset_manifest: dict[str, Any] = Field(default_factory=dict)
    function_results: list[FunctionEvaluationResult] = Field(default_factory=list)
    end_to_end_results: list[EndToEndResult] = Field(default_factory=list)
    overall_metrics: OverallMetrics = Field(default_factory=OverallMetrics)
    regressions: list[RegressionDelta] = Field(default_factory=list)
    generated_at: str = ""
    live: bool = False
    output_dir: str = ""

"""Typed artifacts owned by the sample-data package.

Canonical finance objects reuse existing domain models. These types cover
the generator's own registry, manifest, expected-results key, and storylines.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
Domain = Literal[
    "ap_ar",
    "cash_recon",
    "close",
    "audit_controls",
    "reporting_forecasting",
    "ingestion",
    "memory",
    "orchestration",
    "handoff",
]
ExpectedBehavior = Literal[
    "APPROVE",
    "HOLD",
    "HUMAN_REVIEW",
    "MATCHED",
    "UNMATCHED",
    "FEE_NETTED",
    "GROUPED_MATCH",
    "UNEXPLAINED_DIFFERENCE",
    "TIMING_DIFFERENCE",
    "PROVIDER_PAYOUT",
    "ACCRUE",
    "AMORTIZE",
    "DEPRECIATE",
    "BLOCK_CLOSE",
    "NEEDS_REVIEW",
    "COMPLETE",
    "FAIL",
    "PASS",
    "FORECAST_MISS",
    "VARIANCE_DRIVER",
    "CLASSIFY",
    "MEMORY",
    "HANDOFF",
    "ORCHESTRATE",
    "LEARN",
    "EXCEPTION_OPEN",
    "CLOSE_BLOCKED",
]


class Company(BaseModel):
    model_config = ConfigDict(extra="ignore")

    company_id: str = "CO-MAXIMOR"
    legal_name: str = "Maximor Demo Corp"
    trade_name: str = "Maximor"
    currency: str = "USD"
    headquarters: str = "Cambridge, MA"
    fiscal_year_start_month: int = 1
    operating_bank_id: str = "BANK-OPERATING"
    stripe_account_id: str = "acct_maximor_demo"
    annual_revenue_run_rate: float = 372_400_000.00
    august_revenue: float = 30_820_000.00
    september_revenue: float = 31_140_000.00
    w2_headcount: int = 2_840
    contractors_1099: int = 412
    biweekly_payroll_gross: float = 8_437_291.44
    ap_open: float = 18_420_000.00
    ar_open: float = 41_260_000.00
    operating_cash: float = 14_882_410.18
    active_vendors: int = 340


class FiscalCalendar(BaseModel):
    period: str
    comparison_period: str
    as_of_date: str
    period_start: str
    period_end: str
    comparison_start: str
    comparison_end: str
    forecast_as_of: str
    close_target_date: str


class ScenarioRecord(BaseModel):
    scenario_id: str
    domain: Domain
    name: str
    description: str
    source_ids: list[str] = Field(default_factory=list)
    expected_behavior: ExpectedBehavior
    severity: Severity = "MEDIUM"
    demo_priority: int = 50
    storyline: str = ""
    notes: str = ""


class Storyline(BaseModel):
    storyline_id: str
    title: str
    kind: Literal["clean", "resolved_exception", "unresolved_review"]
    description: str
    document_id: str
    steps: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class VendorPayment(BaseModel):
    """Canonical AP disbursement shared by cash, forecast, close, and audit."""

    model_config = ConfigDict(extra="ignore")

    payment_id: str
    invoice_ids: list[str]
    vendor: str
    vendor_id: str
    payment_date: str
    amount_minor: int
    method: str = "ach"
    bank_reference: str = ""
    description: str = ""
    on_hold_invoice: bool = False
    round_number: bool = False
    initiator_id: str = "USR-PAY-01"
    approver_id: str = "USR-APPR-01"


class Product(BaseModel):
    product_id: str
    name: str
    category: str


class BankAccount(BaseModel):
    account_id: str
    name: str
    currency: str = "USD"
    gl_account: str = "1000-Cash"


class JournalEntryRecord(BaseModel):
    """Balanced two-sided journal used by close, audit, and reporting adapters."""

    entry_id: str
    period: str
    effective_date: str
    posting_date: str
    posting_timestamp: str
    debit_account: str
    credit_account: str
    amount_minor: int
    memo: str = ""
    vendor: str = ""
    customer: str = ""
    product: str = ""
    category: str = ""
    quantity: Optional[float] = None
    rate: Optional[float] = None
    source_document_id: str = ""
    transaction_id: str = ""
    entry_type: str = "operating"
    related_ids: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    poster_id: str = "USR-JE-01"
    approver_id: str = "USR-JE-02"
    authorized: bool = True
    authorization_id: Optional[str] = None
    post_close: bool = False

    @property
    def amount(self) -> float:
        return round(self.amount_minor / 100.0, 2)


class ExpectedFinding(BaseModel):
    finding_id: str
    control_id: str
    population_item_id: str
    expected_result: Literal["PASS", "FAIL", "EXCEPTION", "HUMAN_REVIEW"]
    expected_reason_code: str
    source_ids: list[str] = Field(default_factory=list)


class AdversarialHoldoutItem(BaseModel):
    """Private eval key. Never copy these fields onto operational rows."""

    id: str
    storyline: str
    reason_code: str
    stealth: int
    magnitude: str
    record_ids: list[str] = Field(default_factory=list)
    plant_objects: list[str] = Field(default_factory=list)
    must_remain_unmatched: list[str] = Field(default_factory=list)


class ExpectedResults(BaseModel):
    """Hidden answer key. Operational agents must never load this file."""

    period: str
    seed: int
    ap_exceptions: dict[str, list[str]] = Field(default_factory=dict)
    reconciliation_statuses: dict[str, str] = Field(default_factory=dict)
    audit_findings: list[ExpectedFinding] = Field(default_factory=list)
    close_blockers: list[str] = Field(default_factory=list)
    gross_margin_drivers: list[str] = Field(default_factory=list)
    forecast_miss_drivers: list[str] = Field(default_factory=list)
    storylines: list[str] = Field(default_factory=list)
    adversarial_holdout: list[AdversarialHoldoutItem] = Field(default_factory=list)


class DatasetManifest(BaseModel):
    seed: int
    company: str
    period: str
    comparison_period: str
    schema_version: str
    generated_files: list[str] = Field(default_factory=list)
    record_counts: dict[str, int] = Field(default_factory=dict)
    scenario_ids: list[str] = Field(default_factory=list)
    storyline_ids: list[str] = Field(default_factory=list)
    validation: str = "PASS"


class ScenarioPlan(BaseModel):
    """Structured agent output: which approved templates to instantiate."""

    agent: str
    selected_templates: list[str] = Field(default_factory=list)
    narrative: str = ""
    memos: dict[str, str] = Field(default_factory=dict)


class FileCounts(BaseModel):
    path: str
    records: int

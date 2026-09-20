"""Shared canonical company state. Agents mutate this; they do not invent peers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from accrual.models import AccrualInvoice, OpenAccrual, VendorContract, VendorUsage
from ar.models import ARPrecedent, Customer, CustomerInvoice, CustomerPayment
from audit.models import (
    AccountingPeriod,
    AuditApproval,
    AuditInvoice,
    AuditJournalEntry,
    AuditPayment,
    AuditVendor,
    OperationalDecision,
    PlantedReconciliation,
)
from cash_recon.models import BankTransaction, FeeEvidence, LedgerEntry
from close.models import CloseTask, IdentityLink
from fixed_assets.models import CapitalCandidate, FixedAsset
from integrations.models import ProviderPayout
from models import CashPosition, CompanyPolicy, GoodsReceipt, Invoice, PriorCase, PurchaseOrder
from prepaid.models import PrepaidItem, PrepaidScheduleLine
from reporting.models import (
    BudgetPeriod,
    CashActualMovement,
    CashForecastWeek,
    ChartAccount,
    ForecastLine,
    PeriodBalances,
    ReportingLine,
)

from sample_data.ids import IdFactory
from sample_data.models import (
    BankAccount,
    Company,
    ExpectedResults,
    FiscalCalendar,
    JournalEntryRecord,
    Product,
    ScenarioRecord,
    Storyline,
    VendorPayment,
)
from sample_data.schema_map import SCHEMA_VERSION


FIXED_GENERATED_AT = "2026-09-19T00:00:00Z"
REPO_DATA = Path(__file__).resolve().parent.parent / "data"


def dollars(amount_minor: int) -> float:
    return round(amount_minor / 100.0, 2)


def cents(amount: float | int) -> int:
    return int(round(float(amount) * 100))


def period_end(period: str) -> date:
    from calendar import monthrange

    year_i, month_i = (int(part) for part in period.split("-"))
    return date(year_i, month_i, monthrange(year_i, month_i)[1])


def previous_period(period: str) -> str:
    year_i, month_i = (int(part) for part in period.split("-"))
    if month_i == 1:
        return f"{year_i - 1}-12"
    return f"{year_i}-{month_i - 1:02d}"


def build_calendar(period: str) -> FiscalCalendar:
    start = date.fromisoformat(f"{period}-01")
    end = period_end(period)
    prior = previous_period(period)
    prior_start = date.fromisoformat(f"{prior}-01")
    prior_end = period_end(prior)
    return FiscalCalendar(
        period=period,
        comparison_period=prior,
        as_of_date=end.isoformat(),
        period_start=start.isoformat(),
        period_end=end.isoformat(),
        comparison_start=prior_start.isoformat(),
        comparison_end=prior_end.isoformat(),
        forecast_as_of="2026-09-19" if period == "2026-09" else start.isoformat(),
        close_target_date=(
            date(end.year + 1, 1, 3) if end.month == 12 else date(end.year, end.month + 1, 3)
        ).isoformat(),
    )


@dataclass
class CompanyScenarioContext:
    seed: int
    calendar: FiscalCalendar
    company: Company = field(default_factory=Company)
    ids: IdFactory = field(default_factory=IdFactory)
    chart: list[ChartAccount] = field(default_factory=list)
    bank_accounts: list[BankAccount] = field(default_factory=list)
    products: list[Product] = field(default_factory=list)
    vendors: dict[str, dict] = field(default_factory=dict)
    customers: dict[str, Customer] = field(default_factory=dict)
    purchase_orders: dict[str, PurchaseOrder] = field(default_factory=dict)
    goods_receipts: dict[str, GoodsReceipt] = field(default_factory=dict)
    ap_invoices: dict[str, Invoice] = field(default_factory=dict)
    ar_invoices: dict[str, CustomerInvoice] = field(default_factory=dict)
    ar_payments: dict[str, CustomerPayment] = field(default_factory=dict)
    ar_precedents: list[ARPrecedent] = field(default_factory=list)
    vendor_payments: dict[str, VendorPayment] = field(default_factory=dict)
    bank_transactions: dict[str, BankTransaction] = field(default_factory=dict)
    ledger_cash: dict[str, LedgerEntry] = field(default_factory=dict)
    fee_evidence: dict[str, FeeEvidence] = field(default_factory=dict)
    stripe_payouts: list[ProviderPayout] = field(default_factory=list)
    stripe_events: list[dict] = field(default_factory=list)
    stripe_balance_txns: list[dict] = field(default_factory=list)
    stripe_deposits: list[dict] = field(default_factory=list)
    journal_entries: dict[str, JournalEntryRecord] = field(default_factory=dict)
    reporting_lines: list[ReportingLine] = field(default_factory=list)
    accruals: list[OpenAccrual] = field(default_factory=list)
    prepaids: list[PrepaidItem] = field(default_factory=list)
    prepaid_schedule: list[PrepaidScheduleLine] = field(default_factory=list)
    fixed_assets: list[FixedAsset] = field(default_factory=list)
    capital_invoices: list[CapitalCandidate] = field(default_factory=list)
    source_documents: list[dict] = field(default_factory=list)
    close_tasks: list[CloseTask] = field(default_factory=list)
    identity_links: list[IdentityLink] = field(default_factory=list)
    recon_labels: dict[str, dict] = field(default_factory=dict)
    period_balances: dict[str, PeriodBalances] = field(default_factory=dict)
    cash_opening_bank_minor: int = 50_000_000
    cash_opening_ledger_minor: int = 50_000_000
    audit_vendors: list[AuditVendor] = field(default_factory=list)
    audit_invoices: list[AuditInvoice] = field(default_factory=list)
    audit_payments: list[AuditPayment] = field(default_factory=list)
    audit_journals: list[AuditJournalEntry] = field(default_factory=list)
    audit_approvals: list[AuditApproval] = field(default_factory=list)
    audit_periods: list[AccountingPeriod] = field(default_factory=list)
    planted_recons: list[PlantedReconciliation] = field(default_factory=list)
    operational_decisions: list[OperationalDecision] = field(default_factory=list)
    audit_bank: list[BankTransaction] = field(default_factory=list)
    audit_ledger: list[LedgerEntry] = field(default_factory=list)
    audit_fees: list[FeeEvidence] = field(default_factory=list)
    forecast_weeks: list[CashForecastWeek] = field(default_factory=list)
    forecast_lines: list[ForecastLine] = field(default_factory=list)
    forecast_actuals: list[CashActualMovement] = field(default_factory=list)
    budget: list[BudgetPeriod] = field(default_factory=list)
    payroll: list = field(default_factory=list)
    other_cash: list[ForecastLine] = field(default_factory=list)
    ap_forecast_state: list[dict] = field(default_factory=list)
    historical_invoices: list[AccrualInvoice] = field(default_factory=list)
    vendor_contracts: list[VendorContract] = field(default_factory=list)
    vendor_usage: list[VendorUsage] = field(default_factory=list)
    later_invoices: list[AccrualInvoice] = field(default_factory=list)
    policies: list[CompanyPolicy] = field(default_factory=list)
    prior_cases: list[PriorCase] = field(default_factory=list)
    cash_position: CashPosition | None = None
    approved_pool: list[dict] = field(default_factory=list)
    ingestion_emails: list[dict] = field(default_factory=list)
    ingestion_documents: list[dict] = field(default_factory=list)
    ingestion_erp: list[dict] = field(default_factory=list)
    ingestion_procurement: list[dict] = field(default_factory=list)
    ingestion_vendor_portals: list[dict] = field(default_factory=list)
    ingestion_employee: list[dict] = field(default_factory=list)
    ingestion_edi: list[dict] = field(default_factory=list)
    ingestion_bank: list[dict] = field(default_factory=list)
    ingestion_files: dict[str, str] = field(default_factory=dict)
    memory_events: list[dict] = field(default_factory=list)
    visualization_tags: dict[str, list[str]] = field(default_factory=dict)
    scenarios: dict[str, ScenarioRecord] = field(default_factory=dict)
    storylines: list[Storyline] = field(default_factory=list)
    expected: ExpectedResults | None = None
    opening_cash_forecast_minor: int = 50_000_000
    document_texts: dict[str, str] = field(default_factory=dict)
    historical_ap_register: list[dict] = field(default_factory=list)
    bank_history: list[dict] = field(default_factory=list)
    payroll_register: list[dict] = field(default_factory=list)
    processor_transactions: list[dict] = field(default_factory=list)
    workpapers: dict[str, str] = field(default_factory=dict)
    fiscal_periods: list[dict] = field(default_factory=list)
    approval_matrix: list[dict] = field(default_factory=list)
    bank_account_master: list[dict] = field(default_factory=list)
    round2_hooks: dict = field(default_factory=dict)
    august_close_pack: dict = field(default_factory=dict)

    @property
    def period(self) -> str:
        return self.calendar.period

    @property
    def schema_version(self) -> str:
        return SCHEMA_VERSION

    def plant(self, scenario_id: str, source_ids: list[str], *, storyline: str = "", notes: str = "") -> ScenarioRecord:
        from sample_data.registry import CATALOG_BY_ID

        if scenario_id not in CATALOG_BY_ID:
            raise ValueError(f"Unknown scenario template {scenario_id}")
        record = CATALOG_BY_ID[scenario_id].model_copy(deep=True)
        record.source_ids = list(source_ids)
        record.storyline = storyline
        record.notes = notes
        self.scenarios[scenario_id] = record
        return record

    def add_journal(self, entry: JournalEntryRecord) -> JournalEntryRecord:
        if entry.entry_id in self.journal_entries:
            raise ValueError(f"Duplicate journal {entry.entry_id}")
        if entry.amount_minor <= 0:
            raise ValueError(f"Journal {entry.entry_id} amount must be positive cents")
        self.journal_entries[entry.entry_id] = entry
        return entry

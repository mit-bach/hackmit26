"""Reporting + forecasting sample-data agent. Aggregates the existing ledger."""

from __future__ import annotations

from datetime import date, timedelta

from reporting.forecast import monday_on_or_before, week_starts
from reporting.models import (
    BudgetPeriod,
    CashActualMovement,
    CashForecastWeek,
    ChartAccount,
    ForecastLine,
    PayrollSchedule,
    PeriodBalances,
    ReportingLine,
)

from sample_data.adapters import journal_to_reporting_lines
from sample_data.agents.base import SampleDataAgent
from sample_data.context import CompanyScenarioContext, dollars
from sample_data.models import ScenarioPlan


ACCOUNT_CLASS = {
    "4000-Revenue": "revenue",
    "5100-Hosting": "cogs",
    "5200-Supplier": "cogs",
    "5300-Freight": "cogs",
    "5400-Other-COGS": "cogs",
    "5000-COGS": "cogs",
    "6000-Operating": "opex",
    "6100-Payroll": "opex",
    "Utilities Expense": "opex",
    "Legal Expense": "opex",
    "Software Subscription Expense": "opex",
    "Insurance Expense": "opex",
    "Depreciation Expense": "opex",
    "1000-Cash": "cash",
    "1100-AR": "ar",
    "2000-AP": "ap",
}


class ReportingForecastingSampleDataAgent(SampleDataAgent):
    name = "Reporting Forecasting Sample Data Agent"
    domain = "reporting_forecasting"

    TEMPLATES = [
        "SCN-REPORT-001",
        "SCN-REPORT-002",
        "SCN-REPORT-003",
        "SCN-REPORT-004",
        "SCN-REPORT-005",
        "SCN-REPORT-006",
        "SCN-REPORT-007",
        "SCN-REPORT-008",
    ]

    def plan(self, ctx: CompanyScenarioContext) -> ScenarioPlan:
        return ScenarioPlan(
            agent=self.name,
            selected_templates=list(self.TEMPLATES),
            narrative=(
                "Board numbers and the 13-week forecast are derived from the same "
                "AP, AR, payroll, and bank objects. Gross margin moves because "
                "supplier rates, freight, and mix changed — not because a percentage was stored."
            ),
        )

    def apply(self, ctx: CompanyScenarioContext, plan: ScenarioPlan) -> None:
        self._chart(ctx)
        self._reporting_lines(ctx)
        self._balances(ctx)
        self._budget(ctx)
        self._payroll_and_other(ctx)
        self._forecast(ctx)
        self._actuals(ctx)

    def _chart(self, ctx: CompanyScenarioContext) -> None:
        ctx.chart = [
            ChartAccount(account_id="4000-Revenue", name="Revenue", account_class="revenue", aliases=["Revenue"]),
            ChartAccount(account_id="5100-Hosting", name="Cloud Hosting", account_class="cogs", aliases=["Hosting"]),
            ChartAccount(account_id="5200-Supplier", name="Supplier COGS", account_class="cogs"),
            ChartAccount(account_id="5300-Freight", name="Freight", account_class="cogs"),
            ChartAccount(account_id="6000-Operating", name="Operating Expenses", account_class="opex"),
            ChartAccount(account_id="6100-Payroll", name="Payroll", account_class="opex", aliases=["Payroll"]),
            ChartAccount(account_id="1000-Cash", name="Cash", account_class="cash", aliases=["Cash"]),
            ChartAccount(account_id="1100-AR", name="Accounts Receivable", account_class="ar"),
            ChartAccount(account_id="2000-AP", name="Accounts Payable", account_class="ap"),
        ]

    def _reporting_lines(self, ctx: CompanyScenarioContext) -> None:
        rows: list[ReportingLine] = []
        for entry in ctx.journal_entries.values():
            debit_class = ACCOUNT_CLASS.get(entry.debit_account)
            credit_class = ACCOUNT_CLASS.get(entry.credit_account)
            if debit_class in {"revenue", "cogs", "opex"}:
                rows.append(journal_to_reporting_lines(entry, debit_class, "debit"))
            if credit_class in {"revenue", "cogs", "opex"}:
                rows.append(journal_to_reporting_lines(entry, credit_class, "credit"))
        ctx.reporting_lines = rows
        ctx.plant(
            "SCN-REPORT-001",
            ["TXN-SUP-SEP-001", "TXN-FRT-SEP-001", "TXN-REV-SEP-001", "TXN-HOST-SEP-001", "INV-SUP-SEP-001"],
        )
        ctx.plant("SCN-REPORT-002", [item.line_id for item in rows[:6]])

    def _balances(self, ctx: CompanyScenarioContext) -> None:
        ap = sum(cents_of(inv.amount) for inv in ctx.ap_invoices.values() if inv.invoice_date.startswith("2026-09") and inv.invoice_id not in {p for pay in ctx.vendor_payments.values() for p in pay.invoice_ids})
        ar = sum(cents_of(inv.outstanding_amount) for inv in ctx.ar_invoices.values())
        cash_end = ctx.cash_opening_bank_minor + sum(item.amount_minor for item in ctx.bank_transactions.values() if item.date.startswith("2026-09"))
        ctx.period_balances[ctx.period] = PeriodBalances(
            period=ctx.period,
            as_of_date=ctx.calendar.as_of_date,
            cash=dollars(cash_end),
            ap=dollars(max(ap, 0)),
            ar=dollars(ar),
        )
        ctx.period_balances[ctx.calendar.comparison_period] = PeriodBalances(
            period=ctx.calendar.comparison_period,
            as_of_date=ctx.calendar.comparison_end,
            cash=480000.0,
            ap=92000.0,
            ar=145000.0,
        )
        ctx.opening_cash_forecast_minor = 51_000_000

    def _budget(self, ctx: CompanyScenarioContext) -> None:
        ctx.budget = [
            BudgetPeriod(
                period="2026-08",
                revenue=1000000.0,
                cogs=350000.0,
                gross_profit=650000.0,
                gross_margin_pct=0.65,
                operating_expenses=140000.0,
                operating_income=510000.0,
            ),
            BudgetPeriod(
                period="2026-09",
                revenue=980000.0,
                cogs=350000.0,
                gross_profit=630000.0,
                gross_margin_pct=0.64285714,
                operating_expenses=140000.0,
                operating_income=490000.0,
            ),
        ]

    def _payroll_and_other(self, ctx: CompanyScenarioContext) -> None:
        payroll = []
        cursor = date(2026, 9, 25)
        for index in range(8):
            payroll.append(
                PayrollSchedule(
                    schedule_id=f"PR-{cursor.isoformat()}",
                    pay_date=cursor.isoformat(),
                    expected_amount=70000.0,
                    description="Biweekly payroll",
                )
            )
            cursor = cursor + timedelta(days=7 if index == 0 else 14)
        ctx.payroll = payroll
        ctx.other_cash = [
            ForecastLine(
                line_id="FL-OTH-RENT-2026-10",
                source_type="other",
                source_id="RENT-2026-10",
                expected_date="2026-10-01",
                amount=-15000.0,
                confidence=0.99,
                rationale="Cambridge office rent",
                source_workflow="reporting",
                evidence_refs=["other:RENT-2026-10"],
            ),
            ForecastLine(
                line_id="FL-OTH-INS-2026-10",
                source_type="other",
                source_id="INS-2026-10",
                expected_date="2026-10-15",
                amount=-4200.0,
                confidence=0.9,
                rationale="Quarterly insurance installment",
                source_workflow="reporting",
                evidence_refs=["other:INS-2026-10"],
            ),
        ]
        ctx.ap_forecast_state = [
            {"invoice_id": "INV-012", "hold": False, "scheduled_pay_date": "2026-09-28", "approval_state": "approved", "reason": "Deferred in the horizon; later paid early"},
            {"invoice_id": "INV-002", "hold": False, "scheduled_pay_date": "2026-09-22", "approval_state": "approved", "reason": "Due this week"},
            {"invoice_id": "INV-010", "hold": True, "scheduled_pay_date": None, "approval_state": "hold", "reason": "Goods not received"},
        ]

    def _forecast(self, ctx: CompanyScenarioContext) -> None:
        starts = week_starts(ctx.calendar.forecast_as_of, 13)
        lines: list[ForecastLine] = []
        for invoice in ctx.ar_invoices.values():
            if invoice.outstanding_amount <= 0:
                continue
            due = invoice.due_date
            lines.append(
                ForecastLine(
                    line_id=f"FL-AR-{invoice.invoice_id}",
                    source_type="receivable",
                    source_id=invoice.invoice_id,
                    expected_date=due,
                    amount=invoice.outstanding_amount,
                    confidence=0.7,
                    rationale=f"Collection of {invoice.invoice_id}",
                    customer=invoice.customer_name,
                    source_workflow="ar",
                    evidence_refs=[f"receivable:{invoice.invoice_id}"],
                )
            )
        paid = {inv for payment in ctx.vendor_payments.values() for inv in payment.invoice_ids}
        for invoice in ctx.ap_invoices.values():
            if invoice.invoice_id in paid or invoice.invoice_id in {"INV-003", "INV-004", "INV-005", "INV-006", "INV-007", "INV-008", "INV-010"}:
                continue
            if not invoice.due_date.startswith("2026-"):
                continue
            lines.append(
                ForecastLine(
                    line_id=f"FL-AP-{invoice.invoice_id}",
                    source_type="invoice",
                    source_id=invoice.invoice_id,
                    expected_date=invoice.due_date,
                    amount=-invoice.amount,
                    confidence=0.85,
                    rationale=f"Scheduled payment of {invoice.invoice_id}",
                    vendor=invoice.vendor,
                    hold=invoice.invoice_id == "INV-010",
                    source_workflow="ap",
                    evidence_refs=[f"invoice:{invoice.invoice_id}"],
                )
            )
        for row in ctx.payroll:
            lines.append(
                ForecastLine(
                    line_id=f"FL-PR-{row.schedule_id}",
                    source_type="payroll",
                    source_id=row.schedule_id,
                    expected_date=row.pay_date,
                    amount=-row.expected_amount,
                    confidence=0.99,
                    rationale=row.description,
                    source_workflow="payroll",
                    evidence_refs=[f"payroll:{row.schedule_id}"],
                )
            )
        lines.extend(ctx.other_cash)
        for payout in ctx.stripe_payouts:
            lines.append(
                ForecastLine(
                    line_id=f"FL-STRIPE-{payout.payout_id}",
                    source_type="other",
                    source_id=payout.payout_id,
                    expected_date=payout.arrival_date or ctx.calendar.forecast_as_of,
                    amount=dollars(int(payout.amount) + 50_000),
                    confidence=0.6,
                    rationale="Expected Stripe receipts before refunds/fees",
                    source_workflow="stripe",
                    evidence_refs=[f"payout:{payout.payout_id}"],
                )
            )
        weeks: list[CashForecastWeek] = []
        opening = dollars(ctx.opening_cash_forecast_minor)
        for start in starts:
            end = start + timedelta(days=6)
            week_lines = [item for item in lines if monday_on_or_before(date.fromisoformat(item.expected_date[:10])) == start]
            ar_in = sum(item.amount for item in week_lines if item.amount > 0 and item.source_type == "receivable")
            other_in = sum(item.amount for item in week_lines if item.amount > 0 and item.source_type != "receivable")
            ap_out = sum(abs(item.amount) for item in week_lines if item.amount < 0 and item.source_type == "invoice")
            payroll = sum(abs(item.amount) for item in week_lines if item.source_type == "payroll")
            other_out = sum(abs(item.amount) for item in week_lines if item.amount < 0 and item.source_type not in {"invoice", "payroll"})
            ending = opening + ar_in + other_in - ap_out - payroll - other_out
            weeks.append(
                CashForecastWeek(
                    week_start=start.isoformat(),
                    week_end=end.isoformat(),
                    beginning_cash=round(opening, 2),
                    ar_collections=round(ar_in, 2),
                    other_inflows=round(other_in, 2),
                    ap_payments=round(ap_out, 2),
                    payroll=round(payroll, 2),
                    other_outflows=round(other_out, 2),
                    ending_cash=round(ending, 2),
                    line_ids=[item.line_id for item in week_lines],
                )
            )
            opening = ending
        ctx.forecast_lines = lines
        ctx.forecast_weeks = weeks
        ctx.plant("SCN-REPORT-003", [week.week_start for week in weeks])

    def _actuals(self, ctx: CompanyScenarioContext) -> None:
        ctx.forecast_actuals = [
            CashActualMovement(
                movement_id="ACT-DELAY-AR",
                source_type="receivable",
                source_id="INV-AR-014",
                date="2026-10-09",
                amount=25000.0,
                kind="inflow",
                description="Quiet Harbor paid one week late",
                bank_transaction_id="BNK-AR-FC-001",
                evidence_refs=["receivable:INV-AR-014", "bank:BNK-AR-FC-001"],
            ),
            CashActualMovement(
                movement_id="ACT-EARLY-AP",
                source_type="invoice",
                source_id="INV-012",
                date="2026-09-23",
                amount=-21000.0,
                kind="outflow",
                description="GitHub paid earlier than the deferred date",
                bank_transaction_id="BNK-AP-012",
                ledger_entry_id="JE-PAY-INV-012",
                reconciliation_id="PAY-AP-012",
                evidence_refs=["invoice:INV-012", "bank:BNK-AP-012", "payment:PAY-AP-012"],
            ),
            CashActualMovement(
                movement_id="ACT-PAYROLL-HIGH",
                source_type="payroll",
                source_id="PR-2026-10-02",
                date="2026-10-02",
                amount=-73200.0,
                kind="outflow",
                description="Payroll higher than the scheduled amount",
                evidence_refs=["payroll:PR-2026-10-02"],
            ),
            CashActualMovement(
                movement_id="ACT-STRIPE-LOW",
                source_type="other",
                source_id="po_1MaximorFees",
                date="2026-09-19",
                amount=dollars(int(next(p.amount for p in ctx.stripe_payouts if p.payout_id == "po_1MaximorFees"))),
                kind="inflow",
                description="Stripe receipts landed below the gross expectation",
                bank_transaction_id="TXN-2026-09-019A",
                evidence_refs=["payout:po_1MaximorFees", "bank:TXN-2026-09-019A"],
            ),
            CashActualMovement(
                movement_id="ACT-UNEXPECTED",
                source_type="other",
                source_id="BNK-UNX-001",
                date="2026-09-24",
                amount=-800.0,
                kind="outflow",
                description="Unforecast bank charge",
                bank_transaction_id="BNK-UNX-001",
                evidence_refs=["bank:BNK-UNX-001"],
            ),
        ]
        ctx.plant("SCN-REPORT-004", ["INV-AR-014", "BNK-AR-FC-001", "ACT-DELAY-AR"])
        ctx.plant("SCN-REPORT-005", ["INV-012", "BNK-AP-012", "PAY-AP-012"])
        ctx.plant("SCN-REPORT-006", ["PR-2026-10-02", "ACT-PAYROLL-HIGH"])
        ctx.plant("SCN-REPORT-007", ["po_1MaximorFees", "TXN-2026-09-019A"])
        ctx.plant("SCN-REPORT-008", ["BNK-UNX-001", "ACT-UNEXPECTED"])


def cents_of(amount: float) -> int:
    return int(round(float(amount) * 100))

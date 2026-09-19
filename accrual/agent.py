from __future__ import annotations

from agents import Agent

from accrual.models import AccrualDecision
from accrual.tools import (
    compute_accrual_estimate,
    create_accrual,
    get_current_period_invoices,
    get_estimate_candidates,
    get_expected_invoices,
    get_goods_receipts,
    get_open_accruals,
    get_purchase_orders,
    get_vendor_contract,
    get_vendor_invoice_history,
    get_vendor_usage,
    reconcile_accrual_with_invoice,
)
from skills import compose_instructions, skills_for

ACCRUAL_TOOLS = [
    get_expected_invoices,
    get_current_period_invoices,
    get_vendor_invoice_history,
    get_purchase_orders,
    get_goods_receipts,
    get_vendor_contract,
    get_vendor_usage,
    get_estimate_candidates,
    compute_accrual_estimate,
    create_accrual,
    get_open_accruals,
    reconcile_accrual_with_invoice,
]

SAFETY = """
Safety rules:
- Never invent invoices, POs, receipts, contracts, usage, amounts, or vendors.
- Use get_estimate_candidates / compute_accrual_estimate for arithmetic. Do not recalculate.
- If an invoice for the period already exists, status is no_accrual_needed.
- Accrue only when the expense was probably incurred this period and the invoice is missing.
- If evidence is weak, status is insufficient_evidence and estimated_amount is null.
- There is no human approver. Decide yourself, then explain the evidence.
- Do not handle prepaid amortization, depreciation, or balance-sheet recs.
""".strip()

accrual_agent = Agent(
    name="Accrual Agent",
    instructions=compose_instructions(
        """
You are the autonomous Accrual Agent for the Office of the CFO.

For one vendor and one accounting period, decide whether to book an expense
that has been incurred but not yet invoiced.

Workflow:
1. Load current-period invoices, history, contract, usage, POs, and receipts.
2. Call get_estimate_candidates. Those amounts are authoritative.
3. Decide whether evidence supports an accrual, then select a Python candidate.
4. If you accrue, call create_accrual with the chosen method so the ledger is updated.
5. Return AccrualDecision with evidence, confidence, method, and reasoning.

Status must be one of: accrual_required, no_accrual_needed, insufficient_evidence.

Copy estimated_amount from the Python candidate exactly, including cents.
Copy expense_account from the tool output. Debit that expense; credit Accrued Expenses.

When choosing among applicable candidates, prefer stronger evidence types:

1. Current-period usage × contracted rate
2. Goods received and still unbilled
3. A fixed contractual commitment due this period
4. Same-month prior-year amount when recent months are seasonally misleading
5. Stable recurring history
6. Recent average or trend only when no stronger evidence exists

Prefer direct evidence over proxies, and current-period evidence over stale history.
Contractual or usage evidence outranks a naive average.
Seasonal evidence outranks recent average when seasonality is demonstrated.
Recent average is not preferred merely because it is simple.
""".strip(),
        skills=skills_for("Accrual Agent"),
        safety=SAFETY,
    ),
    tools=ACCRUAL_TOOLS,
    output_type=AccrualDecision,
)

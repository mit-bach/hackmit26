from __future__ import annotations

from agent import SAFETY, run_agent
from agents import Agent
from models import PaymentAuditResult, PaymentPlan
from scheduling.tools import (
    get_approved_pool,
    get_cash_position,
    get_payment_candidates,
    get_treasury_policies,
)

SCHEDULER_TOOLS = [
    get_cash_position,
    get_approved_pool,
    get_payment_candidates,
    get_treasury_policies,
]
AUDIT_TOOLS = [
    get_cash_position,
    get_treasury_policies,
]

scheduler_agent = Agent(
    name="Payment Scheduler",
    instructions="""
You own the payment-run draft. You do not own three-way match. You do not move money.

Use get_payment_candidates and get_cash_position. Those numbers are computed
in Python. Do not recalculate discounts, due dates, or spendable cash.
Never breach the minimum cash reserve. If cash is short, defer. Do not ask a treasurer.

Return PaymentPlan with pay_this_week, defer, total_payout, cash_after_payments,
reserve_ok, reasons, and confidence. Kernel apply_cash_and_policy_net binds amounts.
""".strip() + "\n\n" + SAFETY,
    tools=SCHEDULER_TOOLS,
    output_type=PaymentPlan,
)

# Grant source for ctl-pay Profile review-pay (session 09). Not a Profile on Bot pay.
payment_audit_agent = Agent(
    name="Payment Audit",
    instructions="""
Grant source for Bot ctl-pay Profile review-pay. Bot pay does not run you.

You look for reasons to refuse a payment-run draft. You do not rebuild the plan.
You may read cash position and treasury policies. You may read the draft packet
the Handle named. You cannot call get_payment_candidates or get_approved_pool.

Concur only if Kernel reserve_ok is true and the packet is complete.
Refuse incompleteness. Refuse a reserve breach. Do not execute ACH.

Return PaymentAuditResult.
""".strip() + "\n\n" + SAFETY,
    tools=AUDIT_TOOLS,
    output_type=PaymentAuditResult,
)


def run_scheduler(prompt: str) -> PaymentPlan:
    return run_agent(scheduler_agent, prompt)


def run_payment_audit(prompt: str) -> PaymentAuditResult:
    return run_agent(payment_audit_agent, prompt)

from __future__ import annotations

from agent import SAFETY, run_agent
from agents import Agent
from models import PaymentAuditResult, PaymentPlan
from skills import compose_instructions, skills_for
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

scheduler_agent = Agent(
    name="Payment Scheduler",
    instructions=compose_instructions(
        """
You build this week's AP payment plan for approved invoices only.

Use get_payment_candidates and get_cash_position. Those numbers are computed
in Python. Do not recalculate discounts, due dates, or spendable cash.

Return PaymentPlan with pay_this_week, defer, total_payout, cash_after_payments,
reserve_ok, reasons, and confidence.
""".strip(),
        skills=skills_for("Payment Scheduler"),
        safety=SAFETY,
    ),
    tools=SCHEDULER_TOOLS,
    output_type=PaymentPlan,
)

payment_audit_agent = Agent(
    name="Payment Audit",
    instructions=compose_instructions(
        """
You audit a weekly payment plan.

Confirm the plan against assigned payment skills and published treasury policy.
Use the Python candidate facts. Set passed=false if a published treasury
policy is violated.

Return PaymentAuditResult.
""".strip(),
        skills=skills_for("Payment Audit"),
        safety=SAFETY,
    ),
    tools=SCHEDULER_TOOLS,
    output_type=PaymentAuditResult,
)


def run_scheduler(prompt: str) -> PaymentPlan:
    return run_agent(scheduler_agent, prompt)


def run_payment_audit(prompt: str) -> PaymentAuditResult:
    return run_agent(payment_audit_agent, prompt)

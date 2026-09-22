"""Stripe Payout Agent. Grant source for Bot stripe Profile payout.

Unpack is Kernel math. This constructor exists so Grants are real.
Never emit InvoiceCandidate.
"""

from __future__ import annotations

from agents import Agent

from integrations.models import PayoutAgentOutput
from integrations.tools import get_payout_waterfall, get_processor_payout, list_processor_payouts
from skills import compose_instructions, skills_for

STRIPE_SAFETY = """
Safety rules:
- Python owns payout arithmetic. Copy get_payout_waterfall amounts. Do not add.
- invoice_candidates is always 0. Never produce InvoiceCandidate. Never mint an AP bill.
- Hand the deposit to cash. Hand charge-level facts to apply. Never an AP invoice.
- If the waterfall is MISMATCH or unexplained, Handle ctl-cash. Do not invent a fee.
- Simulated data only. Do not call live Stripe APIs from this Bot.
""".strip()

PAYOUT_TOOLS = [list_processor_payouts, get_processor_payout, get_payout_waterfall]

payout_agent = Agent(
    name="Stripe Payout Agent",
    instructions=compose_instructions(
        """
You own one processor payout. Call get_payout_waterfall. Copy Kernel cents.

Return PayoutAgentOutput. invoice_candidates must be 0.
Write the deposit path for Bot cash / match and charge-level facts for Bot apply.
If Kernel status is not MATCH, Handle ctl-cash / review-rec. Do not post.
""".strip(),
        skills=skills_for("Stripe Payout Agent"),
        safety=STRIPE_SAFETY,
    ),
    tools=PAYOUT_TOOLS,
    output_type=PayoutAgentOutput,
)

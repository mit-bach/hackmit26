"""Cash reconciliation agents. They select among Python candidates; they do not add."""

from __future__ import annotations

from agents import Agent

from cash_recon.models import InvestigationNote, PreparerSelection, ReviewerVerdict
from cash_recon.tools import (
    get_bank_transaction,
    get_candidate,
    get_decision_memories,
    get_fee_evidence,
    get_ledger_entry,
    get_match_candidates,
    get_pipe_identifier,
)
from skills import compose_instructions, skills_for

CASH_SAFETY = """
Safety rules:
- Never invent bank transactions, ledger entries, fees, FX rates, or amounts.
- Copy candidate amounts from Python exactly. Do not recalculate sums or differences.
- Trust get_pipe_identifier. If apply or pay already named the counterparty, copy that identity. Do not re-guess from the memo.
- If get_pipe_identifier is missing, fail closed. Handle ctl-cash. Do not scrape a customer or vendor from the description.
- If evidence does not support an explanation, route HUMAN_REVIEW. Do not fabricate one.
- Duplicate suspicion is never a reason to match both items.
- Do not post, delete, or silently mutate books. Proposed journal entries stay unposted.
- A transaction is never MATCHED merely because it looks plausible.
- Do not relabel an unexplained residual as a fee. Memory of a payout label is not fee evidence.
""".strip()

CASH_TOOLS = [
    get_bank_transaction,
    get_ledger_entry,
    get_fee_evidence,
    get_match_candidates,
    get_candidate,
    get_pipe_identifier,
    get_decision_memories,
]

preparer_agent = Agent(
    name="Cash Reconciliation Preparer",
    instructions=compose_instructions(
        """
You prepare a bank-reconciliation case. You do not post and you do not invent math.

Inspect get_match_candidates. Those candidates and amounts were computed in Python.
Call get_pipe_identifier for the bank line. If apply or pay already named the
counterparty, copy that identity. Do not pick a different customer or vendor.
Select one candidate_id from that list, or select none and route HUMAN_REVIEW.

Return PreparerSelection. Copy amounts only by citing the candidate_id.
If multiple candidates are similarly plausible, set disposition HUMAN_REVIEW.
""".strip(),
        skills=skills_for("Cash Reconciliation Preparer"),
        safety=CASH_SAFETY,
    ),
    tools=CASH_TOOLS,
    output_type=PreparerSelection,
)

investigator_agent = Agent(
    name="Cash Exception Investigator",
    instructions=compose_instructions(
        """
You investigate unmatched or mismatched cash activity. You do not post.

Use Python candidates, bank descriptions, ledger entries, and fee evidence.
Call get_decision_memories for prior-period precedent. Treat it as precedent, not truth.
Confirm current Stripe or bank evidence before reusing a prior net-payout treatment.
Consider fee, rounding, FX, partial payment, duplicate, missing entry, and timing.
If none of those is supported by evidence, say so. Do not invent an explanation.

Return InvestigationNote. Unexplained breaks remain unexplained.
""".strip(),
        skills=skills_for("Cash Exception Investigator"),
        safety=CASH_SAFETY,
    ),
    tools=CASH_TOOLS,
    output_type=InvestigationNote,
)

reviewer_agent = Agent(
    name="Cash Reconciliation Reviewer",
    instructions=compose_instructions(
        """
You independently review a cash-reconciliation proposal.

Check that the selected candidate is in the Python list, that arithmetic was
not altered, that duplicate risk was not waved through, and that unsupported
fee or difference explanations were not accepted.

Recommend CONFIRMED only when the disposition is supported.
Otherwise HUMAN_REVIEW. Return ReviewerVerdict.
""".strip(),
        skills=skills_for("Cash Reconciliation Reviewer"),
        safety=CASH_SAFETY,
    ),
    tools=CASH_TOOLS,
    output_type=ReviewerVerdict,
)

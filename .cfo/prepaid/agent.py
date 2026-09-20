from __future__ import annotations

from agents import Agent

from prepaid.models import PrepaidDecision, PrepaidReview
from prepaid.schedule import select_treatment, treatment_candidates
from prepaid.tools import (
    get_decision_memories,
    get_prepaid,
    get_prepaid_schedule,
    get_prepaid_treatment_candidates,
    list_prepaids,
)
from skills import compose_instructions, skills_for

PREPAID_TOOLS = [
    get_prepaid,
    list_prepaids,
    get_prepaid_treatment_candidates,
    get_prepaid_schedule,
    get_decision_memories,
]

SAFETY = """
Safety rules:
- Never invent prepaid amounts, dates, or evidence.
- Use get_prepaid_treatment_candidates / get_prepaid_schedule for arithmetic. Do not recalculate.
- If the source document is missing, do not amortize. Escalate.
- Do not post a period that Python already marked posted.
- Immediate expense is valid only when Python marks that candidate applicable.
""".strip()

prepaid_preparer = Agent(
    name="Prepaid Preparer",
    instructions=compose_instructions(
        """
You prepare prepaid-expense amortization for one contract.

Workflow:
1. Load the prepaid item and Python treatment candidates.
2. Call get_decision_memories for the same vendor. Use prior treatment as precedent, not a rule.
3. Choose an applicable candidate. Copy amounts from Python. Reuse a prior method only when current dates support it.
4. If evidence is missing, selected_method is insufficient_evidence and escalate is true.
5. Explain why the chosen method fits the service period better than the alternatives.
""".strip(),
        skills=skills_for("Prepaid Preparer"),
        safety=SAFETY,
    ),
    tools=PREPAID_TOOLS,
    output_type=PrepaidDecision,
)

prepaid_reviewer = Agent(
    name="Prepaid Reviewer",
    instructions=compose_instructions(
        """
You independently review a prepaid amortization proposal.

Inspect the prepaid item, the Python candidates, the preparer method, and evidence.
Approve only when evidence exists and the selected method is an applicable Python candidate.
Reject arithmetic that does not match Python. Request more evidence when the source document is missing.
Escalate borderline capitalization-versus-prepaid questions rather than forcing a match.
""".strip(),
        skills=skills_for("Prepaid Reviewer"),
        safety=SAFETY,
    ),
    tools=PREPAID_TOOLS,
    output_type=PrepaidReview,
)


def deterministic_prepare(prepaid_id: str) -> PrepaidDecision:
    from prepaid.store import get_item

    item = get_item(prepaid_id)
    if item is None:
        return PrepaidDecision(
            prepaid_id=prepaid_id,
            selected_method="insufficient_evidence",
            reasoning_summary="Prepaid item was not found.",
            escalate=True,
            confidence=0,
        )
    method = select_treatment(item)
    return PrepaidDecision(
        prepaid_id=prepaid_id,
        selected_method=method,  # type: ignore[arg-type]
        confidence=0.2 if method == "insufficient_evidence" else 0.86,
        reasoning_summary=(
            "Source document is missing, so amortization is blocked."
            if method == "insufficient_evidence"
            else f"Python selected {method} from {len(treatment_candidates(item))} candidates."
        ),
        evidence_used=list(item.evidence_refs),
        escalate=method == "insufficient_evidence",
    )


def deterministic_review(prepaid_id: str, preparer: PrepaidDecision) -> PrepaidReview:
    from prepaid.store import get_item

    item = get_item(prepaid_id)
    if item is None:
        return PrepaidReview(
            prepaid_id=prepaid_id,
            decision="REJECT",
            agree_with_preparer=False,
            reasons=["Prepaid item was not found."],
        )
    applicable = {row.method for row in treatment_candidates(item) if row.applicable}
    if not item.start_date or not item.end_date:
        return PrepaidReview(
            prepaid_id=prepaid_id,
            decision="REQUEST_EVIDENCE",
            agree_with_preparer=preparer.selected_method == "insufficient_evidence",
            reasons=["Service-period dates are missing or conflicting; do not guess a coverage window."],
            evidence_used=list(item.evidence_refs),
        )
    if not item.evidence_refs or not item.source_document_id:
        return PrepaidReview(
            prepaid_id=prepaid_id,
            decision="REQUEST_EVIDENCE",
            agree_with_preparer=preparer.selected_method == "insufficient_evidence",
            reasons=["Supporting policy or contract is missing."],
            evidence_used=[],
        )
    if preparer.selected_method == "insufficient_evidence":
        return PrepaidReview(
            prepaid_id=prepaid_id,
            decision="REJECT",
            agree_with_preparer=False,
            reasons=["Evidence exists; insufficient_evidence is not supported."],
            evidence_used=list(item.evidence_refs),
        )
    if preparer.selected_method not in applicable:
        return PrepaidReview(
            prepaid_id=prepaid_id,
            decision="REJECT",
            agree_with_preparer=False,
            reasons=[f"{preparer.selected_method} is not an applicable Python candidate."],
            evidence_used=list(item.evidence_refs),
        )
    return PrepaidReview(
        prepaid_id=prepaid_id,
        decision="APPROVE",
        agree_with_preparer=True,
        reasons=["Evidence supports the prepaid and the method is an applicable Python candidate."],
        evidence_used=list(item.evidence_refs),
    )

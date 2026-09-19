from __future__ import annotations

import json

from agents import Agent, RunHooks, Runner
from agents.tool_context import ToolContext

from models import (
    ApproverDecision,
    AuditResult,
    InvestigationReport,
    PreparerRecommendation,
    ReviewerDecision,
)
from skills import compose_instructions, skills_for
from tools import (
    find_duplicate_invoices,
    find_relevant_policies,
    get_case_evidence,
    get_company_policies,
    get_goods_receipt,
    get_invoice,
    get_prior_cases,
    get_purchase_order,
)

MAX_AGENT_TURNS = 8

RECORD_TOOLS = [
    get_invoice,
    get_purchase_order,
    get_goods_receipt,
    find_duplicate_invoices,
    get_case_evidence,
]
POLICY_TOOLS = [
    get_company_policies,
    find_relevant_policies,
    get_prior_cases,
]


class ToolCallPrinter(RunHooks):
    """Print agent and tool activity for the demo."""

    async def on_agent_start(self, context, agent) -> None:
        print(f"[{agent.name}]", flush=True)

    async def on_tool_start(self, context, agent, tool) -> None:
        args = ""
        if isinstance(context, ToolContext) and context.tool_arguments:
            raw = context.tool_arguments
            try:
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                args = ", ".join(f"{key}={value!r}" for key, value in parsed.items())
            except (TypeError, ValueError, json.JSONDecodeError):
                args = str(raw)
        print(f"  → {tool.name}({args})", flush=True)


SAFETY = """
Safety rules:
- Never invent missing invoices, POs, receipts, amounts, vendors, policies, or prior cases.
- Never invent an approval threshold or tolerance. Use only published policy values.
- Explicit company policy takes precedence over historical precedent.
- Prior cases are evidence, not absolute rules, and cannot override a must_hold policy.
- If evidence cannot justify payment, HOLD.
- There is no human reviewer. Do not ask a person to decide. Investigate, then APPROVE or HOLD.
- Use Python facts from get_case_evidence. Do not recalculate arithmetic.
""".strip()

preparer_agent = Agent(
    name="AP Preparer",
    instructions=compose_instructions(
        """
You prepare an accounts-payable case. You do not make the final payment decision.

Inspect the invoice, PO, goods receipt, duplicates, and get_case_evidence.
Identify every exception and produce a preliminary recommendation.

Return PreparerRecommendation. Cite record IDs in evidence_used.
Copy exception_types from get_case_evidence. Do not invent exceptions.
""".strip(),
        skills=skills_for("AP Preparer"),
        safety=SAFETY,
    ),
    tools=RECORD_TOOLS,
    output_type=PreparerRecommendation,
)

investigator_agent = Agent(
    name="Exception Investigator",
    instructions=compose_instructions(
        """
You investigate AP exceptions. You do not make the final payment decision.

Inspect records, get_case_evidence, find_relevant_policies, and get_prior_cases.
Explain each exception, then recommend APPROVE or HOLD.

Return InvestigationReport with findings, relevant policy IDs, prior case IDs,
unresolved risks, and APPROVE or HOLD.
""".strip(),
        skills=skills_for("Exception Investigator"),
        safety=SAFETY,
    ),
    tools=RECORD_TOOLS + POLICY_TOOLS,
    output_type=InvestigationReport,
)

reviewer_agent = Agent(
    name="AP Reviewer",
    instructions=compose_instructions(
        """
You independently review AP case files. Do not rubber-stamp the Preparer.

Read the deterministic evidence, the Preparer recommendation, and the
Investigator report when one exists. Challenge weak assumptions.
Verify that Python facts and published policies support the recommendation.

Recommend only APPROVE or HOLD. There is no human review path.
If the Investigator left unresolved risk, HOLD unless a policy clearly
permits payment anyway.

Return ReviewerDecision with objections even if you still recommend APPROVE.
""".strip(),
        skills=skills_for("AP Reviewer"),
        safety=SAFETY,
    ),
    tools=[get_case_evidence, get_company_policies, find_relevant_policies, get_prior_cases],
    output_type=ReviewerDecision,
)

approver_agent = Agent(
    name="AP Approver",
    instructions=compose_instructions(
        """
You are the final autonomous payment authority for this invoice.
There is no human approver after you.

Review Preparer evidence, Investigator findings when present, Reviewer
critique, Python facts, and published policies. Then decide APPROVE or HOLD.

Every APPROVE must be supported by evidence and policy.
If evidence is missing or policy requires a hold, HOLD.
State which evidence IDs and policy IDs you used.

Return ApproverDecision.
""".strip(),
        skills=skills_for("AP Approver"),
        safety=SAFETY,
    ),
    tools=[get_case_evidence, get_company_policies, find_relevant_policies, get_prior_cases],
    output_type=ApproverDecision,
)

audit_agent = Agent(
    name="AP Audit",
    instructions=compose_instructions(
        """
You audit an autonomous AP decision before it is finalized.

Re-read get_case_evidence and company policies. Confirm the Approver decision
is supported. Flag unsupported assumptions and policy violations.

Set passed=true only if the decision is consistent with Python facts and
published policy.
If the decision is APPROVE and you find a material problem, set
requires_reconsideration=true and passed=false.
If the decision is HOLD and that hold is supported, passed=true.

Never pause the workflow. Return AuditResult.
""".strip(),
        skills=skills_for("AP Audit"),
        safety=SAFETY,
    ),
    tools=[get_case_evidence, get_company_policies, find_relevant_policies],
    output_type=AuditResult,
)


def run_agent(agent: Agent, prompt: str, max_turns: int = MAX_AGENT_TURNS, hooks=None):
    result = Runner.run_sync(
        agent,
        prompt,
        max_turns=max_turns,
        hooks=ToolCallPrinter() if hooks is None else hooks,
    )
    print(flush=True)
    if result.final_output is None:
        raise RuntimeError(f"{agent.name} did not return structured output")
    return result.final_output

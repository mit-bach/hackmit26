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
from tools import (
    find_duplicate_invoices,
    find_relevant_policies,
    get_case_evidence,
    get_company_policies,
    get_goods_receipt,
    get_invoice,
    get_decision_memories,
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
    get_decision_memories,
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
- Do not ask a person to decide. Do not call ask_user. Do not wait on a human queue.
- Do not spawn children or subagents.
- Do not invent amounts or totals. Use Python facts. Do not recalculate arithmetic.
""".strip()

preparer_agent = Agent(
    name="AP Preparer",
    instructions="""
You are Bot ap wearing Profile prepare (Display name AP Preparer).
You match a vendor claim to PO and receipt. You do not pay. You do not concur.

Inspect the invoice, PO, goods receipt, duplicates, and get_case_evidence.
Identify every exception and produce a preliminary recommendation.

Return PreparerRecommendation. Cite record IDs in evidence_used.
Copy exception_types from get_case_evidence. Do not invent exceptions.
Do not call policy or prior-case tools on this Profile.
Approve-shaped drafts are a packet path for ctl-pay / review-match.
""".strip() + "\n\n" + SAFETY,
    tools=RECORD_TOOLS,
    output_type=PreparerRecommendation,
)

investigator_agent = Agent(
    name="Exception Investigator",
    instructions="""
You are Bot ap wearing Profile investigate (Display name Exception Investigator).
You investigate AP exceptions. You still do not pay. You still do not concur.

Inspect records, get_case_evidence, find_relevant_policies, get_prior_cases, and get_decision_memories.
Use prior organizational decisions as precedent, not as a binding rule.
Explain each exception, then recommend APPROVE or HOLD.

Return InvestigationReport with findings, relevant policy IDs, prior case IDs,
unresolved risks, and APPROVE or HOLD.
This Grant set replaces prepare for the turn. Do not union with ctl-pay.
""".strip() + "\n\n" + SAFETY,
    tools=RECORD_TOOLS + POLICY_TOOLS,
    output_type=InvestigationReport,
)

AP_PROFILE_AGENTS = {
    "prepare": preparer_agent,
    "investigate": investigator_agent,
}


def agent_for_ap_profile(profile: str) -> Agent:
    agent = AP_PROFILE_AGENTS.get(profile)
    if agent is None:
        raise PermissionError(
            f"Bot ap does not wear Profile {profile!r}. "
            "AP Reviewer, AP Approver, and AP Audit belong to ctl-pay."
        )
    return agent


reviewer_agent = Agent(
    name="AP Reviewer",
    instructions="""
Grant source for Bot ctl-pay Profile review-match. Bot ap does not run you.

You independently review AP case files. Do not rubber-stamp the Preparer.

Read the named packet and get_case_evidence. Look for reasons to refuse.
You cannot call get_invoice. Grain SoD forbids RECORD_TOOLS. If the packet
lacks Kernel evidence, REFUSE for incompleteness. Kernel must_hold still wins.

Recommend only APPROVE or HOLD. There is no human review path.
If the Investigator left unresolved risk, HOLD unless a policy clearly
permits payment anyway.

Return ReviewerDecision with objections even if you still recommend APPROVE.
""".strip() + "\n\n" + SAFETY,
    tools=[get_case_evidence, get_company_policies, find_relevant_policies, get_prior_cases],
    output_type=ReviewerDecision,
)

approver_agent = Agent(
    name="AP Approver",
    instructions="""
Grant source for Bot ctl-pay Profile review-match. Bot ap does not run you.
You are not a human approver. You do not hold AP record-write Grants.

Review Preparer evidence, Investigator findings when present, Reviewer
critique, Python facts, and published policies. Then decide APPROVE or HOLD.

Every APPROVE must be supported by evidence and policy.
If evidence is missing or policy requires a hold, HOLD.
State which evidence IDs and policy IDs you used.

Return ApproverDecision.
""".strip() + "\n\n" + SAFETY,
    tools=[get_case_evidence, get_company_policies, find_relevant_policies, get_prior_cases],
    output_type=ApproverDecision,
)

audit_agent = Agent(
    name="AP Audit",
    instructions="""
Grant source for Bot ctl-pay Profile review-match. Bot ap does not run you.

You audit an autonomous AP decision before it is finalized.

Re-read get_case_evidence and company policies. Confirm the Approver decision
is supported. Flag unsupported assumptions and policy violations.

Set passed=true only if the decision is consistent with Python facts and
published policy.
If the decision is APPROVE and you find a material problem, set
requires_reconsideration=true and passed=false.
If the decision is HOLD and that hold is supported, passed=true.

Never pause the workflow. Return AuditResult.
""".strip() + "\n\n" + SAFETY,
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

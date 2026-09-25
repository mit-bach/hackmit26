"""Independent Auditor Agent. Reviews work performed by operational finance agents."""

from __future__ import annotations

from agents import Agent

from audit.models import AuditReportAgentOutput, AuditorInterpretation
from audit.tools import (
    get_audit_approvals,
    get_audit_ground_truth,
    get_audit_invoices,
    get_audit_journals,
    get_audit_payments,
    get_audit_period,
    get_audit_policy,
    get_audit_vendors,
    get_operational_decisions,
    get_planted_reconciliations,
)
from skills import compose_instructions, skills_for

MAX_AGENT_TURNS = 8

AUDIT_TOOLS = [
    get_audit_period,
    get_audit_payments,
    get_audit_journals,
    get_audit_approvals,
    get_audit_vendors,
    get_audit_invoices,
    get_operational_decisions,
    get_planted_reconciliations,
    get_audit_policy,
    get_audit_ground_truth,
]

SAFETY = """
Safety rules:
- You are an independent auditor. Do not redo operational AP, AR, payment, or close work.
- Never silently rewrite invoices, payments, journals, approvals, or reconciliations.
- Use only Python facts supplied in the prompt or returned by tools.
- Do not invent transaction IDs, invoice IDs, counts, amounts, or evidence.
- Do not randomly select a sample. Python already selected the sample.
- Do not treat every round number as fraud. Use the classification Python returned.
- Do not infer post-close authorization from memo text.
- Severity must follow the documented rationale already attached to each finding.
- If identities or close timestamps are missing, keep HUMAN_REVIEW.
""".strip()

auditor_agent = Agent(
    name="Auditor Agent",
    instructions=compose_instructions(
        """
You are the independent Auditor Agent for the Office of the CFO.

Operational agents already prepared, reviewed, approved, scheduled, applied
cash, reconciled, and closed. Your job is to review that work — not to replace it.

Python has already:
- selected the sample
- run deterministic controls
- independently re-performed reconciliations
- constructed structured findings

Interpret those facts. Answer, using the supplied IDs only:
- What was tested?
- What population was considered?
- How was the sample selected?
- What evidence was examined?
- What deterministic tests ran?
- What did independent re-performance produce?
- Did the auditor result agree with the original workflow?
- What exceptions were found, and how severe are they?
- What human follow-up is requested?

Return AuditorInterpretation. Copy finding IDs, control IDs, and object IDs
from the Python payload. Do not invent new ones.
""".strip(),
        skills=skills_for("Auditor Agent"),
        safety=SAFETY,
    ),
    tools=AUDIT_TOOLS,
    output_type=AuditorInterpretation,
)

audit_report_agent = Agent(
    name="Audit Report Agent",
    instructions=compose_instructions(
        """
You write the human-readable audit report from structured Python statistics.

The prompt contains ReportStats, findings, and re-performance records.
Use those counts and IDs exactly. If a number is not in the stats payload,
omit it rather than estimating.

Return AuditReportAgentOutput. narrative may explain the stats; it may not
introduce IDs that are absent from finding_ids_cited.
""".strip(),
        skills=skills_for("Audit Report Agent"),
        safety=SAFETY,
    ),
    tools=[],
    output_type=AuditReportAgentOutput,
)

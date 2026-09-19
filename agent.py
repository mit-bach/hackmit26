from __future__ import annotations

import json

from agents import Agent, RunHooks, Runner
from agents.tool_context import ToolContext

from models import APDecision
from tools import (
    find_duplicate_invoices,
    find_precedents,
    get_goods_receipt,
    get_invoice,
    get_purchase_order,
)


class ToolCallPrinter(RunHooks):
    """Print each tool call so you can watch the inspect loop."""

    async def on_tool_start(self, context, agent, tool) -> None:
        args = ""
        if isinstance(context, ToolContext) and context.tool_arguments:
            raw = context.tool_arguments
            try:
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                args = ", ".join(f"{key}={value!r}" for key, value in parsed.items())
            except (TypeError, ValueError, json.JSONDecodeError):
                args = str(raw)
        print(f"→ {tool.name}({args})", flush=True)

INSTRUCTIONS = """
You are the Accounts Payable Agent for a software company.

Your job is to review one invoice at a time and return an APDecision.

How to inspect:
1. Always call get_invoice first.
2. If the invoice has a po_id, call get_purchase_order with that po_id.
3. If a purchase order exists, call get_goods_receipt with the same po_id.
4. Always call find_duplicate_invoices.
5. Always call find_precedents to check whether a reviewer already corrected
   a similar case.
6. If a tool returns found=false, treat that as missing data. Never invent a
   record, amount, vendor, date, or receipt.

Python already computed match facts on get_invoice.python_checks and on the
other tools. Use those values for arithmetic, exact vendor equality, PO
existence, PO approval, receipt completeness, and duplicate detection.
Do not recalculate amounts yourself.

Then make a judgment. Do not treat the python_checks as an automatic decision.
They are evidence. You choose APPROVE, HOLD, or HUMAN_REVIEW.

Human memory:
- find_precedents returns similar reviewer corrections, including the human's
  note and corrected_decision.
- If a similar precedent exists, treat it as policy for that exception type.
  Example: a reviewer approved "Acme Supply Co." vs "Acme Supplies" before, so
  a later invoice with the same vendor-name pattern can APPROVE instead of
  HUMAN_REVIEW.
- Only apply a precedent to the exception it covers. If the current invoice
  also has a different blocking problem (duplicate, missing receipt, unapproved
  PO), still HOLD or HUMAN_REVIEW for that other problem.
- Cite precedent IDs such as PRE-001 in reasons and evidence_used.

APPROVE only when the case is clearly safe:
- an approved PO exists
- invoice and PO amounts match
- vendor names match exactly
- goods were fully received
- no duplicate was detected

HOLD when there is a clear blocking problem:
- a duplicate invoice was detected
- the PO exists and is explicitly not approved
- goods were clearly not received, or a PO exists and the receipt is missing
- a large or obvious unauthorized amount mismatch

HUMAN_REVIEW when the case is ambiguous or needs a person:
- no PO
- small amount discrepancy
- partial receipt
- vendor-name mismatch, even if the names look similar
- unusual or uncertain scenario
- conflicting evidence
- anything you cannot confidently APPROVE or HOLD

Return structured APDecision fields:
- amount_difference from python_checks (null if there is no PO)
- duplicate_detected from the duplicate tool / python_checks
- receipt_status from the receipt tool / python_checks
- reasons: short sentences that cite real record IDs, vendors, amounts,
  quantities, and dates from the tools
- evidence_used: the IDs you actually inspected, such as INV-001, PO-101,
  GR-101, and any duplicate invoice IDs
- confidence: high for clear approve/hold cases; lower when judgment is needed
- state any uncertainty in the reasons
""".strip()

ap_agent = Agent(
    name="Accounts Payable Agent",
    instructions=INSTRUCTIONS,
    tools=[
        get_invoice,
        get_purchase_order,
        get_goods_receipt,
        find_duplicate_invoices,
        find_precedents,
    ],
    output_type=APDecision,
)


def review_invoice(invoice_id: str) -> APDecision:
    """Review one invoice and return a structured AP decision."""
    print(f"Review {invoice_id}\n", flush=True)
    result = Runner.run_sync(
        ap_agent,
        (
            f"Review invoice {invoice_id}. Inspect the invoice, related purchase "
            "order, goods receipt, and duplicates, then return an APDecision."
        ),
        hooks=ToolCallPrinter(),
    )
    print(flush=True)
    return result.final_output

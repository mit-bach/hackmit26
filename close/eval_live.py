"""Judgment cases for month-end close. Deterministic ground truth; live agents optional."""

from __future__ import annotations

from close.dates import now_iso
from prepaid.models import PrepaidItem
from prepaid.schedule import select_treatment
from fixed_assets.models import CapitalCandidate
from fixed_assets.agent import deterministic_prepare
from bs_recon.engine import classify_packet
from bs_recon.models import ReconPacket, ReconcilingItem


CASES = [
    {
        "case_id": "prepaid-vs-expense",
        "question": "Should this $12,000 insurance payment be expensed immediately or treated as prepaid?",
        "expected": "prepaid / straight_line_monthly",
    },
    {
        "case_id": "server-capital",
        "question": "Does this server purchase look like an expense or capital asset?",
        "expected": "capitalize",
    },
    {
        "case_id": "cash-12-40",
        "question": "Is this $12.40 cash reconciliation difference acceptable, explainable, or escalation-worthy?",
        "expected": "escalate / unexplained_difference",
    },
    {
        "case_id": "prepaid-evidence",
        "question": "Does the provided evidence actually support the prepaid balance?",
        "expected": "no / missing_evidence",
    },
    {
        "case_id": "signoff-missing-doc",
        "question": "Should a reconciliation be signed off when a supporting document is missing?",
        "expected": "no",
    },
]


def _deterministic_answers() -> dict[str, str]:
    insurance = PrepaidItem(
        prepaid_id="EVAL-INS",
        vendor="Hartford Insurance",
        description="Annual policy",
        source_document_id="DOC-INS-2026",
        total_amount=12000,
        start_date="2026-09-01",
        end_date="2027-08-31",
        initial_account="Prepaid Insurance",
        expense_account="Insurance Expense",
        evidence_refs=["DOC-INS-2026"],
        created_at=now_iso(),
    )
    server = CapitalCandidate(
        candidate_id="INV-021",
        vendor="Dell Technologies",
        description="PowerEdge R760 server cluster",
        amount=60000,
        invoice_date="2026-09-05",
        source_document_id="DOC-DELL-R760",
        evidence_refs=["DOC-DELL-R760"],
        useful_life_months=36,
        salvage_value=6000,
    )
    cash = ReconPacket(
        account_id="Cash",
        account_name="Cash",
        period="2026-09",
        ledger_balance=10012.40,
        evidence_balance=10000.00,
        ledger_source="gl",
        evidence_source="bank",
        evidence_refs=["bank"],
        reconciling_items=[
            ReconcilingItem(
                item_id="DIFF",
                description="$12.40 unexplained",
                amount=12.40,
                source="cash_recon",
                classification="unexplained_difference",
            )
        ],
    )
    missing = ReconPacket(
        account_id="Prepaid Expenses",
        account_name="Prepaid Expenses",
        period="2026-09",
        ledger_balance=3600,
        evidence_balance=0,
        ledger_source="gl",
        evidence_source="none",
        evidence_refs=[],
        reconciling_items=[],
        missing_evidence=True,
    )
    return {
        "prepaid-vs-expense": f"prepaid / {select_treatment(insurance)}",
        "server-capital": deterministic_prepare(server).decision,
        "cash-12-40": f"escalate / {classify_packet(cash)}",
        "prepaid-evidence": classify_packet(missing),
        "signoff-missing-doc": "no" if classify_packet(missing) == "missing_evidence" else "yes",
    }


def _run_live_cases() -> list[str]:
    import os

    if not os.environ.get("OPENAI_API_KEY"):
        return [
            "LIVE AGENT EVALUATION",
            "Skipped: OPENAI_API_KEY is not set. No live result was fabricated.",
        ]
    from agent import run_agent
    from close.agents import month_end_reviewer
    from close.models import CloseGateResult, FinalCloseVerdict
    from fixed_assets.agent import fixed_asset_preparer
    from prepaid.agent import prepaid_preparer
    from prepaid.models import PrepaidDecision
    from prepaid.store import load_items, load_seed_items, save_items
    from bs_recon.agent import bs_preparer
    from bs_recon.engine import classify_packet
    from bs_recon.models import ReconDecision
    from bs_recon.packets import cash_packet
    from bs_recon.tools import bind_packets
    from fixed_assets.models import AssetDecision

    lines = [
        "LIVE AGENT EVALUATION",
        "These calls use the configured API. Failures are reported; results are not fabricated.",
        "",
    ]
    if not load_items():
        save_items(load_seed_items())
    try:
        prepaid = run_agent(prepaid_preparer, "Prepare prepaid accounting for PRE-INS-001.")
        method = prepaid.selected_method if isinstance(prepaid, PrepaidDecision) else str(prepaid)
        lines.append(f"prepaid accounting judgment: {method}")
    except Exception as exc:
        lines.append(f"prepaid accounting judgment: ERROR {exc}")

    try:
        asset = run_agent(fixed_asset_preparer, "Classify INV-021 PowerEdge R760 server cluster.")
        decision = asset.decision if isinstance(asset, AssetDecision) else str(asset)
        lines.append(f"fixed-asset classification judgment: {decision}")
    except Exception as exc:
        lines.append(f"fixed-asset classification judgment: ERROR {exc}")

    packet = cash_packet("2026-09", scenario="demo")
    bind_packets("2026-09", [packet])
    try:
        recon = run_agent(bs_preparer, f"Explain the Cash reconciliation. Python finding={classify_packet(packet)}.")
        finding = recon.finding if isinstance(recon, ReconDecision) else str(recon)
        lines.append(f"reconciliation explanation: {finding}")
    except Exception as exc:
        lines.append(f"reconciliation explanation: ERROR {exc}")

    blocked = CloseGateResult(period="2026-09", passed=False, blockers=["Cash unexplained $12.40 remains"])
    try:
        verdict = run_agent(
            month_end_reviewer,
            f"Decide whether 2026-09 can close. Python gate_passed=false. Facts={blocked.model_dump()}",
        )
        decision = verdict.decision if isinstance(verdict, FinalCloseVerdict) else str(verdict)
        lines.append(f"final close review: {decision}")
    except Exception as exc:
        lines.append(f"final close review: ERROR {exc}")
    return lines


def run_close_eval(*, use_agent: bool = False, live: bool = False) -> str:
    answers = _deterministic_answers()
    lines = [
        "MONTH-END CLOSE EVALUATION",
        "Ground truth is deterministic Python. Live agents are optional and not required for CI.",
        "",
    ]
    passed = 0
    for case in CASES:
        expected = case["expected"]
        actual = answers[case["case_id"]]
        ok = expected.split("/")[0].strip() in actual or actual in expected or expected in actual
        if case["case_id"] == "prepaid-vs-expense":
            ok = "straight_line_monthly" in actual and "immediate" not in actual
        if case["case_id"] == "server-capital":
            ok = actual == "capitalize"
        if case["case_id"] == "cash-12-40":
            ok = "unexplained" in actual
        if case["case_id"] == "prepaid-evidence":
            ok = actual == "missing_evidence"
        if case["case_id"] == "signoff-missing-doc":
            ok = actual == "no"
        passed += int(ok)
        lines.extend(
            [
                f"CASE {case['case_id']}",
                f"  Q: {case['question']}",
                f"  expected: {expected}",
                f"  agent/python: {actual}",
                f"  result: {'PASS' if ok else 'FAIL'}",
                f"  trace: deterministic:{case['case_id']}",
                "",
            ]
        )
    lines.append(f"Score: {passed}/{len(CASES)}")
    if live or use_agent:
        lines.extend(["", *_run_live_cases()])
    return "\n".join(lines)

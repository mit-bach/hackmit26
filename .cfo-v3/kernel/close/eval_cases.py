"""Canonical close-eval fixtures.

Seed records live under ``data/eval/``. Expected labels stay in this module
so agent prompts never receive the answer key.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from bs_recon.models import ReconPacket, ReconcilingItem
from close.models import CloseGateResult
from fixed_assets.models import CapitalCandidate, FixedAsset
from prepaid.models import PrepaidItem

REPO = Path(__file__).resolve().parent.parent
EVAL_DATA = REPO / "data" / "eval"


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    kind: str
    question: str
    prompt: str
    expected: str
    allowed: tuple[str, ...] = ()
    notes: str = ""
    extra_facts: dict = field(default_factory=dict)

    def matches(self, actual: str) -> bool:
        text = str(actual or "")
        accepted = (self.expected,) + self.allowed
        return any(token and token in text for token in accepted)


def insurance_prepaid() -> PrepaidItem:
    rows = json.loads((EVAL_DATA / "prepaids.json").read_text())
    return PrepaidItem.model_validate(rows[0])


def server_candidate() -> CapitalCandidate:
    rows = json.loads((EVAL_DATA / "capital_candidates.json").read_text())
    return CapitalCandidate.model_validate(rows[0])


def duplicate_register_asset() -> FixedAsset:
    rows = json.loads((EVAL_DATA / "fixed_assets_duplicate.json").read_text())
    return FixedAsset.model_validate(rows[0])


def cash_difference_packet() -> ReconPacket:
    return ReconPacket(
        account_id="Cash",
        account_name="Cash",
        period="2026-09",
        ledger_balance=10012.40,
        evidence_balance=10000.00,
        ledger_source="eval.gl",
        evidence_source="eval.bank",
        evidence_refs=["BANK-EVAL-2026-09"],
        reconciling_items=[
            ReconcilingItem(
                item_id="DIFF-EVAL-1240",
                description="$12.40 unexplained cash difference",
                amount=12.40,
                source="eval",
                classification="unexplained_difference",
            )
        ],
    )


def blocked_close_gate() -> CloseGateResult:
    return CloseGateResult(
        period="2026-09",
        all_required_tasks_complete=True,
        all_required_bs_recs_signed_off=False,
        no_blocking_reviews=False,
        evidence_complete=True,
        journal_safeguards_pass=True,
        passed=False,
        blockers=["Cash unexplained $12.40 remains"],
        recon_status={"Cash": "HUMAN_REVIEW"},
        task_status={"final_review": "READY", "mark_closed": "BLOCKED"},
    )


def _facts_prompt(title: str, facts: dict) -> str:
    lines = [title, "Use only these facts. Do not assume other register items exist.", ""]
    for key, value in facts.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def canonical_cases() -> list[EvalCase]:
    prepaid = insurance_prepaid()
    server = server_candidate()
    cash = cash_difference_packet()
    gate = blocked_close_gate()
    prepaid_facts = {
        "prepaid_id": prepaid.prepaid_id,
        "vendor": prepaid.vendor,
        "description": prepaid.description,
        "total_amount": prepaid.total_amount,
        "start_date": prepaid.start_date,
        "end_date": prepaid.end_date,
        "source_document_id": prepaid.source_document_id,
        "evidence_refs": list(prepaid.evidence_refs),
    }
    server_facts = {
        "candidate_id": server.candidate_id,
        "vendor": server.vendor,
        "description": server.description,
        "amount": server.amount,
        "invoice_date": server.invoice_date,
        "useful_life_months": server.useful_life_months,
        "source_document_id": server.source_document_id,
        "evidence_refs": list(server.evidence_refs),
        "register_has_matching_asset": False,
    }
    duplicate_facts = {**server_facts, "register_has_matching_asset": True}
    cash_facts = {
        "account_id": cash.account_id,
        "period": cash.period,
        "ledger_balance": cash.ledger_balance,
        "evidence_balance": cash.evidence_balance,
        "difference": 12.40,
        "reconciling_items": [item.model_dump(mode="json") for item in cash.reconciling_items],
    }
    close_facts = gate.model_dump(mode="json")
    return [
        EvalCase(
            case_id="prepaid-judgment",
            kind="prepaid",
            question="Should this $12,000 insurance payment be expensed immediately or treated as prepaid?",
            prompt=_facts_prompt("Prepare prepaid accounting for EVAL-INS.", prepaid_facts),
            expected="straight_line_monthly",
            allowed=("daily_prorate",),
            extra_facts=prepaid_facts,
        ),
        EvalCase(
            case_id="server-capital",
            kind="fixed_asset",
            question="Does this server purchase look like an expense or capital asset?",
            prompt=_facts_prompt("Classify INV-021 PowerEdge R760 server cluster.", server_facts),
            expected="capitalize",
            extra_facts=server_facts,
        ),
        EvalCase(
            case_id="duplicate-asset",
            kind="duplicate_asset",
            question="A matching Dell server is already on the register. What should happen?",
            prompt=_facts_prompt("Classify INV-021 against the current fixed-asset register.", duplicate_facts),
            expected="duplicate_review",
            extra_facts=duplicate_facts,
        ),
        EvalCase(
            case_id="recon-explanation",
            kind="reconciliation",
            question="Is this $12.40 cash reconciliation difference acceptable, explainable, or escalation-worthy?",
            prompt=_facts_prompt("Explain the Cash reconciliation from this packet only.", cash_facts),
            expected="unexplained_difference",
            extra_facts=cash_facts,
        ),
        EvalCase(
            case_id="final-close-review",
            kind="final_close",
            question="Should September close while an unexplained cash difference remains?",
            prompt=_facts_prompt("Decide whether 2026-09 can close. Python gate_passed=false.", close_facts),
            expected="REJECT_CLOSE",
            allowed=("REQUEST_REVIEW",),
            extra_facts=close_facts,
        ),
    ]


CANONICAL_CASES = canonical_cases()

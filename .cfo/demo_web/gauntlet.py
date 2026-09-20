"""Demo-facing Finance Gauntlet views. Gold answers stay hidden until a scored run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from demo_web.jsonutil import dump, read_json
from demo_web.workspace import website_dir
from evals.maximor_finance_gauntlet.fixtures.documents import public_catalog as document_catalog
from evals.maximor_finance_gauntlet.fixtures.questions import public_catalog as question_catalog
from evals.maximor_finance_gauntlet.runner import run_gauntlet, write_gauntlet


FAMILY_COPY = {
    "documents": {"title": "Document traps", "plain": "Messy invoices, voids, quotes, and look-alikes"},
    "cash": {"title": "Cash reconciliation", "plain": "Bank lines matched to the books with real evidence"},
    "anti_hack": {"title": "False-match resistance", "plain": "Same-dollar distractors that must not be forced together"},
    "questions": {"title": "Multi-step finance questions", "plain": "Questions that combine several company records"},
    "rubrics": {"title": "Accounting tasks", "plain": "Close work graded on several criteria, not one number"},
    "consistency": {"title": "Cross-workflow consistency", "plain": "The same bill means the same thing everywhere"},
    "long_horizon": {"title": "Month after month", "plain": "August decisions still matter in later months"},
    "memory": {"title": "Decision memory", "plain": "Precedent is reused only when current evidence still supports it"},
    "recovery": {"title": "Error recovery", "plain": "Broken files and duplicate events do not invent books"},
}


def _latest_path() -> Path:
    return website_dir() / "maximor_finance_gauntlet.json"


def _modes_path() -> Path:
    return website_dir() / "maximor_finance_gauntlet_modes.json"


def public_catalog() -> list[dict[str, Any]]:
    rows = []
    for item in document_catalog():
        rows.append(
            {
                "case_id": item["case_id"],
                "family": "documents",
                "title": item["title"],
                "prompt": item.get("subject") or item["title"],
            }
        )
    for item in question_catalog():
        rows.append(
            {
                "case_id": item["question_id"],
                "family": "questions",
                "title": item["prompt"],
                "difficulty": item["difficulty"],
                "prompt": item["prompt"],
            }
        )
    return rows


def _sanitize_case(item: dict[str, Any], *, scored: bool) -> dict[str, Any]:
    row = {
        "case_id": item.get("case_id"),
        "family": item.get("family"),
        "title": item.get("title") or item.get("prompt") or item.get("case_id"),
        "passed": item.get("passed") if scored else None,
        "difficulty": item.get("difficulty"),
        "period": item.get("period"),
    }
    if scored:
        row["actual"] = item.get("actual")
        row["reason"] = "Matched the hidden expected outcome." if item.get("passed") else "Did not match the hidden expected outcome."
        if item.get("expected") is not None:
            row["expected"] = item.get("expected")
    return row


def gauntlet_view() -> dict[str, Any]:
    latest = read_json(_latest_path())
    scored = isinstance(latest, dict) and bool(latest.get("cases"))
    catalog = public_catalog()
    cases = [_sanitize_case(item, scored=True) for item in (latest.get("cases") or [])] if scored else catalog
    traps = [item for item in cases if item.get("family") == "documents"]
    return {
        "scored": scored,
        "latest": {
            "run_id": latest.get("run_id") if scored else None,
            "memory_enabled": latest.get("memory_enabled") if scored else None,
            "shared_state": latest.get("shared_state") if scored else None,
            "scorecard": latest.get("scorecard") if scored else None,
            "inspired_by": latest.get("inspired_by") if scored else [
                {"name": "AccountingBench", "url": "https://accounting.penrose.com/"},
                {"name": "Invoice Sandbox Benchmark", "url": "https://github.com/ciru-ai/invoice-sandbox-benchmark"},
            ],
        } if latest else None,
        "catalog": catalog,
        "cases": cases,
        "families": FAMILY_COPY,
        "traps_caught": [item for item in traps if item.get("passed")],
        "modes": read_json(_modes_path()),
        "note": "Maximor is scored against hidden expected outcomes. Agents never receive the answer key.",
    }


def run_gauntlet_workflow(*, include_existing: bool = False, modes: bool = False) -> dict[str, Any]:
    if modes:
        from evals.maximor_finance_gauntlet.modes import run_modes

        payload = run_modes(include_existing=include_existing)
        dest = website_dir() / "maximor_finance_gauntlet_modes.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(dump(payload), indent=2) + "\n")
        comparison = payload.get("comparison") or {}
        summary = (
            "Memory on vs off and shared-state on vs off were measured on the same scenarios. "
            "These are real configuration differences, not restated claims."
        )
        return {
            "summary": summary,
            "payload": dump(payload),
            "path": str(dest),
            "comparison": comparison,
            "stages": [
                {"id": "b", "label": "Ran with memory disabled", "status": "completed", "bot": "close"},
                {"id": "c", "label": "Ran with shared canonical state reduced", "status": "completed", "bot": "audit"},
                {"id": "a", "label": "Ran full Maximor", "status": "completed", "bot": "audit"},
            ],
        }
    payload = run_gauntlet(include_existing=include_existing, memory_enabled=True, shared_state=True)
    dest = write_gauntlet(payload, dest=website_dir() / "maximor_finance_gauntlet.json")
    write_gauntlet(payload)
    card = payload["scorecard"]
    return {
        "summary": (
            f"{card['scenarios_passed']} of {card['total_scenarios']} Finance Gauntlet scenarios matched their hidden expected outcomes"
        ),
        "payload": dump(payload),
        "path": str(dest),
        "scorecard": card,
        "stages": [
            {"id": "docs", "label": "Classified messy documents without seeing answers", "status": "completed", "bot": "email"},
            {"id": "cash", "label": "Reconciled bank lines using economic evidence", "status": "completed", "bot": "cash"},
            {"id": "close", "label": "Ran close, memory, and consistency checks", "status": "completed", "bot": "close"},
            {"id": "score", "label": "Compared results with grader-only expected outcomes", "status": "completed", "bot": "audit"},
        ],
    }


def trap_story() -> dict[str, Any]:
    from cfo.lineage_story import describe_event
    from invoice_ingestion.traps import analyze_document
    from evals.maximor_finance_gauntlet.fixtures.documents import DOCUMENTS

    voided = next(item for item in DOCUMENTS if item["case_id"] == "TRAP-VOID")
    analysis = analyze_document(voided["text"], subject=voided["subject"], filename=voided["filename"])
    duplicate = describe_event("INV-006")
    return {
        "title": "The trap",
        "received": voided["text"],
        "naive": "A naive system would treat any document that says INVOICE and has an amount as a new bill, put it in the payment queue, reduce forecasted cash, and book another payable.",
        "detected": analysis.reason,
        "payable": analysis.payable,
        "classification": analysis.classification,
        "prevented": [
            "No new accounts-payable balance",
            "Not added to the payment queue",
            "Not treated as vendor spend",
            "Not left as an unexplained bank item",
        ],
        "duplicate": duplicate,
    }


def harbor_story() -> dict[str, Any]:
    return {
        "title": "Harbor Electric across months",
        "august_evidence": "August service was consumed, but the Harbor Electric bill had not arrived.",
        "august_decision": "Maximor booked an accrual from historical Harbor Electric invoices rather than inventing a number.",
        "september_evidence": "September still has no current invoice, so Maximor looks up the August method.",
        "september_decision": "The August method is precedent. September reuses it only if current evidence still supports that treatment.",
        "explanation": "Memory is evidence, not an override. A later actual bill can replace the estimate.",
        "run_path": "/api/workflows/memory",
    }


def stripe_story() -> dict[str, Any]:
    from demo_web import artifacts

    bundle = artifacts.stripe_payout_bundle("po_1MaximorFees") or {}
    payout = bundle.get("payout") or {}
    record = payout.get("record") or {}
    return {
        "title": "Stripe to books",
        "received": "Stripe charges, refunds, fees, and chargebacks settle as one payout, then as a bank deposit.",
        "payout": payout,
        "bank_deposit": bundle.get("bank_deposit"),
        "lines": bundle.get("lines") or record.get("lines") or [],
        "explanation": (
            "Gross charges minus refunds, disputes, and Stripe fees equal the expected payout. "
            "That same net amount is the bank deposit and the cash posting. "
            "No workflow is allowed to treat the payout as revenue or as a vendor invoice."
        ),
        "shared_interpretation": True,
    }


def correction_story() -> dict[str, Any]:
    return {
        "title": "Later evidence corrects an earlier estimate",
        "august": "August booked an estimate because Harbor Electric's bill had not arrived.",
        "september": "September reused that estimate as precedent.",
        "october": "October received the actual invoice and compared it with the open accrual.",
        "explanation": "Current evidence replaces the prior estimate. The reversal, the actual bill, and the new precedent stay in the history.",
        "run_path": "/api/workflows/memory",
        "run_body": {"story": "harbor-correct"},
    }

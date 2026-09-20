from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from models import PaymentCandidate
from scheduling.cash import payment_candidate, policy_eligible_for_pool
from tools import DATA_DIR, all_invoices, load_invoice

POOL_PATH = DATA_DIR / "approved_pool.json"


def candidates_from_pool() -> list[PaymentCandidate]:
    rows = load_pool()
    candidates = []
    for row in rows:
        item = payment_candidate(
            row["invoice_id"], approval_source=row.get("approval_source", "ap_workflow")
        )
        if item is not None:
            candidates.append(item)
    return candidates


def load_pool() -> list[dict]:
    if not POOL_PATH.exists():
        return []
    raw = json.loads(POOL_PATH.read_text())
    return raw if isinstance(raw, list) else []


def save_pool(rows: list[dict]) -> None:
    POOL_PATH.write_text(json.dumps(rows, indent=2) + "\n")


def add_approved(invoice_id: str, source: str, confidence: float | None = None) -> dict:
    invoice = load_invoice(invoice_id)
    if invoice is None:
        raise ValueError(f"Unknown invoice {invoice_id}")
    rows = [row for row in load_pool() if row.get("invoice_id") != invoice_id]
    record = {
        "invoice_id": invoice_id,
        "vendor": invoice.vendor,
        "amount": invoice.amount,
        "approval_source": source,
        "confidence": confidence,
        "added_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    rows.append(record)
    save_pool(sorted(rows, key=lambda item: item["invoice_id"]))
    return record


def seed_demo_pool() -> list[str]:
    """Fill the pool with policy-eligible invoices so scheduling can demo without 20 AP runs."""
    save_pool([])
    added: list[str] = []
    for invoice in all_invoices():
        if policy_eligible_for_pool(invoice.invoice_id):
            add_approved(invoice.invoice_id, source="deterministic_policy")
            added.append(invoice.invoice_id)
    return added


def seed_from_traces(runs_dir: Path) -> list[str]:
    added: list[str] = []
    latest: dict[str, Path] = {}
    for path in runs_dir.glob("INV-*.json"):
        parts = path.stem.split("-")
        if len(parts) >= 2:
            invoice_id = f"{parts[0]}-{parts[1]}"
            latest[invoice_id] = path
    for invoice_id, path in latest.items():
        payload = json.loads(path.read_text())
        decision = (payload.get("final") or {}).get("decision")
        posted = payload.get("posted_to_pool") is True
        if decision == "APPROVE" and posted:
            add_approved(
                invoice_id,
                source="ap_workflow",
                confidence=(payload.get("final") or {}).get("confidence"),
            )
            added.append(invoice_id)
    return added


def pool_invoice_ids() -> list[str]:
    return [row["invoice_id"] for row in load_pool()]

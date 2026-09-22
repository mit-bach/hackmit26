"""Honest decision-class for each Stripe scenario. Not hidden ground truth."""

from __future__ import annotations

from typing import Any

# decision_class is the *main* decision. Arithmetic is always Python-owned.
SCENARIO_CLASSES: dict[str, dict[str, Any]] = {
    "stripe_simple_payment": {
        "decision_class": "deterministic",
        "why": "Invoice ID in Stripe metadata; fee and payout net are integer-cent math.",
    },
    "stripe_payout_multiple_payments": {
        "decision_class": "deterministic",
        "why": "Three named invoices plus payout composition arithmetic.",
    },
    "stripe_many_txns_one_deposit": {
        "decision_class": "deterministic",
        "why": "Named invoices; one payout amount equals the sum of nets.",
    },
    "stripe_refund_before_payout": {
        "decision_class": "hybrid",
        "why": "Refund links by charge_id (deterministic). Cash apply uses named invoice; payout net is cents.",
        "agents": ["Cash Application Agent"],
        "judgment": "None required for the link once charge_id is present.",
    },
    "stripe_refund_after_payout": {
        "decision_class": "hybrid",
        "why": "Original apply is named-invoice. Later refund must attach to po_str_005b, not the sale payout.",
        "agents": ["Cash Application Agent"],
        "judgment": "Preserve cross-payout relationship; do not assume same-payout refund.",
    },
    "stripe_chargeback": {
        "decision_class": "hybrid",
        "why": "Dispute links by charge_id. Later payout reduction must not be classified as an unexplained bank break.",
        "agents": ["Cash Exception Investigator"],
        "judgment": "Explain the later debit from the original charge, do not invent a new mismatch.",
    },
    "stripe_fee_variation": {
        "decision_class": "deterministic",
        "why": "Source fee_minor is copied; no universal rate is applied.",
    },
    "stripe_duplicate_event": {
        "decision_class": "deterministic",
        "why": "Provider event ID idempotency.",
    },
    "stripe_out_of_order": {
        "decision_class": "deterministic",
        "why": "Canonical state converges after withheld balance transactions are released.",
    },
    "stripe_missing_metadata": {
        "decision_class": "agentic",
        "why": "No invoice_id. Agent/skill must choose among Python candidates using customer, amount, and description.",
        "agents": ["Cash Application Agent"],
        "skills": ["cash-application"],
        "tools": ["get_cash_application_facts", "get_ar_customer"],
    },
    "stripe_ambiguous_invoice": {
        "decision_class": "agentic",
        "why": "Two $900 Brightline invoices. Description context selects INV-STR-011A; an arbitrary pick is forbidden.",
        "agents": ["Cash Application Agent"],
        "skills": ["cash-application"],
        "tools": ["get_cash_application_facts", "get_ar_customer"],
    },
    "stripe_payout_with_refund": {
        "decision_class": "hybrid",
        "why": "Named invoices plus a refund in the same payout. Net is Python arithmetic.",
    },
    "stripe_payout_with_dispute": {
        "decision_class": "hybrid",
        "why": "Named invoices plus a same-payout dispute. Link is by charge_id; net is cents.",
    },
    "stripe_bank_discrepancy_1240": {
        "decision_class": "hybrid",
        "why": "Bank vs payout cents mismatch is deterministic. Investigator must not fabricate a fee/FX story.",
        "agents": ["Cash Exception Investigator", "Cash Reconciliation Preparer"],
        "skills": ["reconciliation-exception-investigation", "cash-reconciliation-method-selection"],
        "tools": ["cash recon candidates"],
    },
    "stripe_cross_period_timing": {
        "decision_class": "deterministic",
        "why": "Payment date vs payout arrival_date; settlement period is October.",
    },
    "stripe_partial_payment": {
        "decision_class": "deterministic",
        "why": "Named invoice; amount < outstanding is exact comparison.",
    },
    "stripe_failed_then_retry": {
        "decision_class": "deterministic",
        "why": "Failed PaymentIntent is ignored; retry uses named invoice.",
    },
    "stripe_unmatched_order": {
        "decision_class": "hybrid",
        "why": "No internal invoice. Policy/agent must leave cash unapplied rather than invent an order.",
        "agents": ["Cash Application Agent"],
        "skills": ["cash-application"],
    },
    "stripe_bank_before_payout": {
        "decision_class": "deterministic",
        "why": "Event order; final payout-to-bank cents match.",
    },
    "stripe_cross_period_memory": {
        "decision_class": "agentic",
        "why": "Two $880 Atlas invoices. Description plus August remittance precedent select INV-STR-018B.",
        "agents": ["Cash Application Agent"],
        "skills": ["cash-application"],
        "tools": ["get_cash_application_facts", "get_ar_customer", "get_ar_precedents"],
    },
    "stripe_overpayment": {
        "decision_class": "hybrid",
        "why": "Named invoice exists but payment exceeds outstanding. Skill requires HUMAN_REVIEW; residual must not vanish.",
        "agents": ["Cash Application Agent"],
        "skills": ["cash-application"],
    },
    "stripe_multiple_payments_one_invoice": {
        "decision_class": "deterministic",
        "why": "Both charges carry INV-STR-021; remaining outstanding is cents.",
    },
    "stripe_payout_before_bank": {
        "decision_class": "deterministic",
        "why": "Payout composition known first; bank later equals 97070 cents.",
    },
}


def classify_scenario(scenario_id: str) -> dict[str, Any]:
    row = SCENARIO_CLASSES.get(scenario_id)
    if row is None:
        return {"scenario_id": scenario_id, "decision_class": "deterministic", "why": "Unlisted; treated as deterministic."}
    return {"scenario_id": scenario_id, **row}

"""Agent-visible multi-step finance questions. Answers are not in this file."""

from __future__ import annotations

QUESTIONS = [
    {
        "question_id": "Q-EASY-VENDOR-SPEND",
        "difficulty": "easy",
        "prompt": "How much did Maximor Demo Corp pay Acme Supplies in September 2026?",
        "spec": {"type": "vendor_spend", "vendor": "Acme Supplies", "period": "2026-09"},
    },
    {
        "question_id": "Q-EASY-UNPAID-60",
        "difficulty": "easy",
        "prompt": "Which unpaid customer invoices are more than 60 days old as of 2026-09-30?",
        "spec": {"type": "unpaid_over_days", "days": 60, "as_of": "2026-09-30"},
    },
    {
        "question_id": "Q-MED-STRIPE-CB",
        "difficulty": "medium",
        "prompt": "Which Stripe payouts contain chargebacks or disputes?",
        "spec": {"type": "stripe_chargeback_payouts"},
    },
    {
        "question_id": "Q-MED-STRIPE-FEES",
        "difficulty": "medium",
        "prompt": "What was the total Stripe fee expense for September 2026?",
        "spec": {"type": "stripe_fee_expense", "period": "2026-09"},
    },
    {
        "question_id": "Q-MED-DEPOSIT",
        "difficulty": "medium",
        "prompt": "Which bank deposit corresponds to Stripe payout po_1MaximorFees?",
        "spec": {"type": "bank_deposit_for_payout", "payout_id": "po_1MaximorFees"},
    },
    {
        "question_id": "Q-HARD-CASH-EFFECT",
        "difficulty": "hard",
        "prompt": "What is the cash effect if all approved invoices due in the next seven days after 2026-09-19 are paid?",
        "spec": {"type": "pay_due_cash_effect", "days": 7, "as_of": "2026-09-19"},
    },
    {
        "question_id": "Q-HARD-DISCREPANCY",
        "difficulty": "hard",
        "prompt": "Which vendor invoice currently has the largest unresolved AP discrepancy?",
        "spec": {"type": "largest_vendor_discrepancy"},
    },
    {
        "question_id": "Q-HARD-PRIOR-OUTFLOW",
        "difficulty": "hard",
        "prompt": "What portion of September cash outflow came from invoices dated in August?",
        "spec": {"type": "outflow_from_prior_approvals", "pay_period": "2026-09", "approve_period": "2026-08"},
    },
    {
        "question_id": "Q-MED-REVISED",
        "difficulty": "medium",
        "prompt": "Which ingested email is a revised invoice replacing an earlier invoice?",
        "spec": {"type": "revised_invoices"},
    },
]


def public_catalog() -> list[dict]:
    return [
        {
            "question_id": item["question_id"],
            "difficulty": item["difficulty"],
            "prompt": item["prompt"],
            "spec": {"type": item["spec"]["type"], **{k: v for k, v in item["spec"].items() if k != "type" and k != "question_id"}},
        }
        for item in QUESTIONS
    ]

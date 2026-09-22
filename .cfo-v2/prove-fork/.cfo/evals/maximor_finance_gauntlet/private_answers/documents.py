"""Hidden document-trap outcomes. Graders only. Never import from operational workflows."""

from __future__ import annotations

GOLD = {
    "TRAP-DUP-EXACT": {"classification": "invoice", "payable": True, "flags": []},
    "TRAP-DUP-VISUAL": {"classification": "invoice", "payable": True, "flags": []},
    "TRAP-REVISED": {"classification": "invoice", "payable": True, "flags": ["revised_invoice"], "supersedes": "HE-4401"},
    "TRAP-VOID": {"classification": "not_invoice", "payable": False, "flags": ["voided"]},
    "TRAP-CREDIT": {"classification": "not_invoice", "payable": False, "flags": ["credit_memo"]},
    "TRAP-QUOTE": {"classification": "quote", "payable": False, "flags": []},
    "TRAP-PO": {"classification": "purchase_order", "payable": False, "flags": []},
    "TRAP-STATEMENT": {"classification": "statement", "payable": False, "flags": []},
    "TRAP-EMAIL-TOTAL": {"classification": "not_invoice", "payable": False, "flags": []},
    "TRAP-MISSING-NUMBER": {"classification": "not_invoice", "payable": False, "flags": []},
    "TRAP-TAX-MATH": {"classification": "invoice", "payable": False, "flags": ["tax_arithmetic_error"]},
    "TRAP-BANKING": {"classification": "invoice", "payable": False, "flags": ["incorrect_banking"]},
    "TRAP-STRIPE-AS-REVENUE": {"classification": "not_invoice", "payable": False, "flags": ["stripe_payout_as_invoice"]},
    "TRAP-CARD-AS-INVOICE": {"classification": "not_invoice", "payable": False, "flags": ["card_charge_as_invoice"]},
}

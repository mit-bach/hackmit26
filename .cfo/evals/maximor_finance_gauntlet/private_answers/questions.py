"""Hidden question answers. Graders compute gold from operational files too, then compare.

Static gold is the expected product of the same production lookup. If a lookup
changes for a real accounting reason, tests fail until the product is fixed —
answers are not patched into prompts.
"""

from __future__ import annotations

# Values are filled at grade time by re-running production lookups inside
# evaluation_phase, then compared against independent expected facts below.
EXPECTED = {
    "Q-MED-STRIPE-CB": {"contains": "po_1MaximorDisputes"},
    "Q-MED-DEPOSIT": {"equals": "BANK-po_1MaximorFees"},
    "Q-MED-STRIPE-FEES": {"min": 0.01},
    "Q-EASY-VENDOR-SPEND": {"min": 0.01},
    "Q-EASY-UNPAID-60": {"nonempty": True},
    "Q-HARD-DISCREPANCY": {"startswith": "INV-"},
    "Q-HARD-PRIOR-OUTFLOW": {"equals": 0.0},
    "Q-MED-REVISED": {"contains": "MSG-E-REVISED"},
}

"""Month-level cash and bank reconciliation.

Python owns amounts, differences, candidate generation, and tie-out.
Agents may select among valid candidates. Stripe and Adyen payout math
stays in integrations.cash / the existing provider adapters.
"""

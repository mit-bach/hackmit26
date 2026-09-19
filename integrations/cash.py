"""Python-owned payout math. The LLM does not add these numbers."""

from __future__ import annotations

from integrations.models import PayoutLine, ProviderPayout, ReconciliationBreakdown

CHARGE_TYPES = {"charge", "payment", "captured", "platformPayment"}
REFUND_TYPES = {"refund", "payment_refund"}
CHARGEBACK_TYPES = {"adjustment", "dispute", "chargeback", "second_chargeback"}
FEE_TYPES = {"stripe_fee", "fee", "commission"}


def major_units(amount_minor: int, currency: str = "USD") -> float:
    return round(amount_minor / 100.0, 2)


def classify_line(line: PayoutLine) -> str:
    kind = (line.line_type or "").lower()
    if kind in CHARGE_TYPES:
        return "gross"
    if kind in REFUND_TYPES:
        return "refund"
    if kind in CHARGEBACK_TYPES:
        return "chargeback"
    if kind in FEE_TYPES:
        return "fee"
    if kind == "payout":
        return "payout"
    return "other"


def reconcile_payout(payout: ProviderPayout) -> ReconciliationBreakdown:
    currency = (payout.currency or "USD").upper()
    actual = major_units(payout.amount, currency)
    gross = refunds = chargebacks = fees = other = 0.0
    for line in payout.lines:
        bucket = classify_line(line)
        if bucket == "payout":
            continue
        if bucket == "gross":
            gross += line.amount
        elif bucket == "refund":
            refunds += abs(line.amount)
        elif bucket == "chargeback":
            chargebacks += abs(line.amount)
        elif bucket == "fee":
            fees += abs(line.amount)
        else:
            other += line.amount
    expected = round(gross - refunds - chargebacks - fees + other, 2)
    difference = round(actual - expected, 2)
    bank_amount = payout.bank_deposit_amount
    bank_matched = bank_amount is not None and abs(bank_amount - actual) < 0.005
    matched = abs(difference) < 0.005 and (bank_amount is None or bank_matched)
    return ReconciliationBreakdown(
        payout_id=payout.payout_id,
        provider=payout.provider,
        currency=currency,
        gross_payments=round(gross, 2),
        refunds=round(-refunds, 2),
        chargebacks=round(-chargebacks, 2),
        fees=round(-fees, 2),
        other=round(other, 2),
        expected_payout=expected,
        actual_payout=actual,
        difference=difference,
        bank_deposit_amount=bank_amount,
        bank_matched=bank_matched,
        matched=matched,
        lines=list(payout.lines),
    )


def format_breakdown(row: ReconciliationBreakdown) -> str:
    currency = row.currency
    def money(value: float) -> str:
        sign = "-" if value < 0 else " "
        return f"{sign}${abs(value):>12,.2f} {currency}"

    lines = [
        f"{row.provider.title()} payout {row.payout_id}",
        f"Gross customer payments     {money(row.gross_payments).strip()}",
        f"Refunds                     {money(row.refunds)}",
        f"Chargebacks                 {money(row.chargebacks)}",
        f"Processor fees              {money(row.fees)}",
        "                              ----------------",
        f"Expected payout             {money(row.expected_payout).strip()}",
        f"Actual payout               {money(row.actual_payout).strip()}",
        f"Difference                  {money(row.difference)}",
    ]
    if row.bank_deposit_amount is not None:
        lines.append(f"Bank deposit                {money(row.bank_deposit_amount).strip()}")
        lines.append(f"Bank match: {'yes' if row.bank_matched else 'NO'}")
    lines.append(f"Reconciliation: {'MATCH' if row.matched else 'EXCEPTION'}")
    return "\n".join(lines)

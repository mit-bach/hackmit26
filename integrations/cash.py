"""Python-owned payout math. The LLM does not add these numbers.

Arithmetic uses integer minor units (cents for USD) to avoid float drift.
Display fields stay in major units for existing demos.
"""

from __future__ import annotations

from integrations.models import PayoutLine, ProviderPayout, ReconciliationBreakdown

CHARGE_TYPES = {"charge", "payment", "captured", "platformPayment", "payment_refund_reversal"}
REFUND_TYPES = {"refund", "payment_refund"}
CHARGEBACK_TYPES = {"dispute", "chargeback", "second_chargeback"}
FEE_TYPES = {"stripe_fee", "fee", "commission", "application_fee"}
PAYOUT_TYPES = {"payout"}
KNOWN_TYPES = CHARGE_TYPES | REFUND_TYPES | CHARGEBACK_TYPES | FEE_TYPES | PAYOUT_TYPES | {"adjustment"}


def major_units(amount_minor: int, currency: str = "USD") -> float:
    return round(amount_minor / 100.0, 2)


def to_minor(amount: float) -> int:
    return int(round(amount * 100))


def line_minor(line: PayoutLine) -> int:
    if line.amount_minor is not None:
        return int(line.amount_minor)
    return to_minor(line.amount)


def classify_line(line: PayoutLine) -> str:
    if line.category:
        return line.category
    kind = (line.line_type or "").lower()
    if kind in CHARGE_TYPES:
        return "gross"
    if kind in REFUND_TYPES:
        return "refund"
    if kind in CHARGEBACK_TYPES:
        return "chargeback"
    if kind in FEE_TYPES:
        return "fee"
    if kind in PAYOUT_TYPES:
        return "payout"
    if kind == "adjustment":
        text = f"{line.description or ''} {line.reference or ''}".lower()
        if "chargeback" in text or "dispute" in text:
            return "chargeback"
        return "adjustment"
    return "other"


def reconcile_payout(payout: ProviderPayout) -> ReconciliationBreakdown:
    currency = (payout.currency or "USD").upper()
    actual_minor = int(payout.amount)
    gross = refunds = chargebacks = fees = adjustments = other = 0
    exceptions: list[str] = []
    annotated: list[PayoutLine] = []
    for line in payout.lines:
        bucket = classify_line(line)
        minor = line_minor(line)
        line = line.model_copy(update={"category": bucket, "amount_minor": minor})
        annotated.append(line)
        line_ccy = (line.currency or currency).upper()
        if line_ccy != currency:
            exceptions.append(f"currency_mismatch:{line.provider_object_id or line.line_type}:{line_ccy}")
        if (line.line_type or "").lower() not in KNOWN_TYPES:
            exceptions.append(f"unknown_balance_transaction_type:{line.line_type}")
        if bucket == "payout":
            continue
        if bucket == "gross":
            gross += minor
        elif bucket == "refund":
            refunds += abs(minor)
        elif bucket == "chargeback":
            chargebacks += abs(minor)
        elif bucket == "fee":
            fees += abs(minor)
        elif bucket == "adjustment":
            adjustments += minor
        else:
            other += minor

    expected_minor = gross - refunds - chargebacks - fees + adjustments + other
    difference_minor = actual_minor - expected_minor
    if expected_minor != actual_minor:
        exceptions.append("payout_amount_does_not_equal_normalized_transaction_net")

    bank_amount = payout.bank_deposit_amount
    bank_minor = to_minor(bank_amount) if bank_amount is not None else None
    bank_ccy = (payout.bank_deposit_currency or currency).upper()
    if bank_amount is not None and bank_ccy != currency:
        exceptions.append(f"currency_mismatch:bank:{bank_ccy}")
    bank_matched = bank_minor is not None and bank_minor == actual_minor
    if bank_amount is not None and not bank_matched:
        exceptions.append("bank_amount_differs_from_stripe_payout")
    if not payout.payout_id:
        exceptions.append("missing_payout")

    if "payout_amount_does_not_equal_normalized_transaction_net" in exceptions or (
        bank_amount is not None and not bank_matched
    ):
        status = "MISMATCH"
    elif bank_amount is None:
        status = "AWAITING_BANK"
    elif any(item.startswith("unknown_balance_transaction_type:") or item.startswith("currency_mismatch:") for item in exceptions):
        status = "NEEDS_REVIEW"
    else:
        status = "MATCH"

    matched = status == "MATCH"
    return ReconciliationBreakdown(
        payout_id=payout.payout_id,
        provider=payout.provider,
        currency=currency,
        gross_payments=major_units(gross, currency),
        refunds=major_units(-refunds, currency),
        chargebacks=major_units(-chargebacks, currency),
        fees=major_units(-fees, currency),
        adjustments=major_units(adjustments, currency),
        other=major_units(other, currency),
        expected_payout=major_units(expected_minor, currency),
        actual_payout=major_units(actual_minor, currency),
        difference=major_units(difference_minor, currency),
        bank_deposit_amount=bank_amount,
        bank_deposit_id=payout.bank_deposit_id,
        bank_matched=bank_matched,
        matched=matched,
        status=status,
        exceptions=list(dict.fromkeys(exceptions)),
        expected_payout_minor=expected_minor,
        actual_payout_minor=actual_minor,
        lines=annotated,
    )


def format_breakdown(row: ReconciliationBreakdown) -> str:
    def money(value: float) -> str:
        sign = "-" if value < 0 else ""
        return f"{sign}${abs(value):,.2f}"

    lines = [
        f"{row.provider.title()} payout {row.payout_id}",
        f"Gross customer payments       {money(row.gross_payments)}",
        f"Refunds                       {money(row.refunds)}",
        f"Chargebacks                   {money(row.chargebacks)}",
        f"Processor fees                {money(row.fees)}",
    ]
    if row.adjustments:
        lines.append(f"Adjustments                   {money(row.adjustments)}")
    if row.other:
        lines.append(f"Other                         {money(row.other)}")
    lines.extend(
        [
            "                              ----------------",
            f"Expected payout               {money(row.expected_payout)}",
            f"Actual payout                 {money(row.actual_payout)}",
            f"Difference                    {money(row.difference)}",
        ]
    )
    if row.bank_deposit_amount is None:
        lines.append("Bank deposit                 unavailable")
    else:
        lines.append(f"Bank deposit                 {money(row.bank_deposit_amount)}")
        if row.bank_deposit_id:
            lines.append(f"Bank deposit ID              {row.bank_deposit_id}")
    lines.append(f"Reconciliation: {row.status}")
    if row.exceptions:
        lines.append("Exceptions: " + "; ".join(row.exceptions))
    return "\n".join(lines)

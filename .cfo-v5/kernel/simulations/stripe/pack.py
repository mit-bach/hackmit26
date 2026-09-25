"""One September 2026 Maximor company and hidden Stripe ground truth."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from simulations.stripe.objects import (
    balance_transaction,
    bank_deposit,
    charge,
    dispute,
    event,
    iso_date,
    payment_intent,
    payout,
    refund,
    standard_fee_cents,
    unix,
)

PERIOD = "2026-09"
AS_OF = "2026-09-30"
COMPANY = "Maximor"


@dataclass
class GroundTruth:
    scenario_id: str
    expected_classification: str
    expected_workflow: str
    expected_customer_invoice_ids: list[str]
    expected_payment_ids: list[str]
    expected_balance_transaction_ids: list[str]
    expected_payout_id: str | None
    expected_bank_transaction_id: str | None
    gross_amount_cents: int
    fee_amount_cents: int
    refund_amount_cents: int
    dispute_amount_cents: int
    expected_net_cents: int
    expected_ar_effect_cents: int
    expected_cash_effect_cents: int
    expected_gl_entries: list[dict[str, Any]]
    expected_reconciliation_status: str
    expected_close_effect: str
    expected_exception_code: str | None
    expected_audit_finding: str | None
    expected_context_links: list[str]
    expected_cash_decision: str | None = None
    expected_settlement_period: str = PERIOD
    expected_duplicate_suppressed: bool = False
    uses_precedent: bool = False
    input_condition: str = ""
    expected_behavior: str = ""


@dataclass
class Scenario:
    scenario_id: str
    title: str
    difficulty: str
    events: list[dict[str, Any]]
    withhold_txn_ids: list[str] = field(default_factory=list)
    release_txn_ids: list[str] = field(default_factory=list)
    bank_before_payout: bool = False
    replay_event_id: str | None = None
    period: str = PERIOD
    cash_period: str = PERIOD
    ground_truth: GroundTruth | None = None


@dataclass
class CompanyPack:
    company: str
    period: str
    customers: list[dict[str, Any]]
    invoices: list[dict[str, Any]]
    precedents: list[dict[str, Any]]
    stripe_customers: list[dict[str, Any]]
    payment_intents: list[dict[str, Any]]
    charges: list[dict[str, Any]]
    refunds: list[dict[str, Any]]
    disputes: list[dict[str, Any]]
    balance_transactions: list[dict[str, Any]]
    payouts: list[dict[str, Any]]
    bank_deposits: list[dict[str, Any]]
    events: list[dict[str, Any]]
    scenarios: list[Scenario]

    def universe(self) -> dict[str, Any]:
        return {
            "customers": self.stripe_customers,
            "payment_intents": self.payment_intents,
            "charges": self.charges,
            "refunds": self.refunds,
            "disputes": self.disputes,
            "balance_transactions": self.balance_transactions,
            "payouts": self.payouts,
            "bank_deposits": self.bank_deposits,
            "events": self.events,
        }

    def ground_truth_rows(self) -> list[dict[str, Any]]:
        return [asdict(item.ground_truth) for item in self.scenarios if item.ground_truth]


def _ar_customer(customer_id: str, name: str, **extra) -> dict[str, Any]:
    row = {
        "customer_id": customer_id,
        "customer_name": name,
        "payment_behavior": extra.get("payment_behavior", "on_time"),
        "typical_remittance": extra.get("typical_remittance", "invoice_number"),
        "aliases": extra.get("aliases", []),
        "notes": extra.get("notes", ""),
        "currency": "USD",
    }
    return row


def _ar_invoice(
    invoice_id: str,
    customer_id: str,
    customer_name: str,
    amount_cents: int,
    invoice_date: str,
    due_date: str,
    description: str,
    reference: str = "",
) -> dict[str, Any]:
    dollars = round(amount_cents / 100.0, 2)
    return {
        "invoice_id": invoice_id,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "original_amount": dollars,
        "outstanding_amount": dollars,
        "currency": "USD",
        "status": "OPEN",
        "description": description,
        "reference": reference,
        "metadata": {"source": "stripe_simulation"},
    }


def _sale(
    *,
    suffix: str,
    customer_stripe: str,
    customer_name: str,
    amount: int,
    created: int,
    invoice_id: str | None,
    description: str,
    payout_id: str | None,
    fee: int | None = None,
    extra_metadata: dict[str, str] | None = None,
) -> dict[str, Any]:
    fee = standard_fee_cents(amount) if fee is None else fee
    metadata = {"customer_name": customer_name, **(extra_metadata or {})}
    if invoice_id:
        metadata["invoice_id"] = invoice_id
        metadata["order_id"] = invoice_id
    pi = payment_intent(
        pi_id=f"pi_str_{suffix}",
        amount=amount,
        customer_id=customer_stripe,
        created=created,
        charge_id=f"ch_str_{suffix}",
        metadata=metadata,
        description=description,
    )
    ch = charge(
        charge_id=f"ch_str_{suffix}",
        amount=amount,
        customer_id=customer_stripe,
        customer_name=customer_name,
        created=created,
        pi_id=pi["id"],
        metadata=metadata,
        description=description,
    )
    txn = balance_transaction(
        txn_id=f"txn_str_{suffix}",
        amount=amount,
        fee=fee,
        txn_type="charge",
        payout_id=payout_id,
        created=created,
        source=ch,
        description=description,
    )
    ch["balance_transaction"] = txn["id"]
    return {"pi": pi, "charge": ch, "txn": txn, "fee": fee, "net": amount - fee}


def build_company_pack() -> CompanyPack:
    t_sep3 = unix(2026, 9, 3)
    t_sep4 = unix(2026, 9, 4)
    t_sep8 = unix(2026, 9, 8)
    t_sep9 = unix(2026, 9, 9)
    t_sep10 = unix(2026, 9, 10)
    t_sep11 = unix(2026, 9, 11)
    t_sep12 = unix(2026, 9, 12)
    t_sep15 = unix(2026, 9, 15)
    t_sep16 = unix(2026, 9, 16)
    t_sep18 = unix(2026, 9, 18)
    t_sep19 = unix(2026, 9, 19)
    t_sep20 = unix(2026, 9, 20)
    t_sep22 = unix(2026, 9, 22)
    t_sep24 = unix(2026, 9, 24)
    t_sep25 = unix(2026, 9, 25)
    t_sep26 = unix(2026, 9, 26)
    t_sep27 = unix(2026, 9, 27)
    t_sep28 = unix(2026, 9, 28)
    t_sep29 = unix(2026, 9, 29)
    t_oct2 = unix(2026, 10, 2)
    t_oct3 = unix(2026, 10, 3)

    customers = [
        _ar_customer("CUST-001", "Northwind Labs", aliases=["Northwnd Labs"], notes="Pays via Stripe with invoice metadata."),
        _ar_customer("CUST-002", "Helios Analytics", aliases=["Helios Analytic"], notes="Several September charges settle together."),
        _ar_customer("CUST-003", "Acme Industrial", aliases=["Acme Inc."], notes="Refund activity."),
        _ar_customer("CUST-004", "Brightline Media", notes="Two similar retainers."),
        _ar_customer("CUST-005", "Orbit Health", notes="Chargeback risk."),
        _ar_customer("CUST-006", "Pinnacle Retail", notes="Sometimes omits invoice metadata."),
        _ar_customer("CUST-008", "Summit Logistics", notes="Failed card then retry."),
        _ar_customer("CUST-009", "Northstar LLC", notes="Known $12.40 bank break story."),
        _ar_customer("CUST-010", "Atlas Systems", typical_remittance="stripe_metadata", notes="Historical Stripe metadata payer."),
        _ar_customer("CUST-011", "Lumen Labs", notes="AMEX fee variation."),
        _ar_customer("CUST-012", "Harbor Electric", notes="Partial and multi-payment."),
        _ar_customer("CUST-013", "Orion Freight", notes="No matching internal order."),
    ]

    invoices = [
        _ar_invoice("INV-STR-001", "CUST-001", "Northwind Labs", 100000, "2026-09-01", "2026-09-30", "September platform subscription", "ORD-STR-001"),
        _ar_invoice("INV-STR-002A", "CUST-002", "Helios Analytics", 100000, "2026-09-02", "2026-09-30", "Helios workspace A", "ORD-STR-002A"),
        _ar_invoice("INV-STR-002B", "CUST-002", "Helios Analytics", 150000, "2026-09-02", "2026-09-30", "Helios workspace B AMEX", "ORD-STR-002B"),
        _ar_invoice("INV-STR-002C", "CUST-002", "Helios Analytics", 50000, "2026-09-02", "2026-09-30", "Helios add-on seats", "ORD-STR-002C"),
        _ar_invoice("INV-STR-003A", "CUST-001", "Northwind Labs", 60000, "2026-09-05", "2026-10-05", "Northwind analytics pack", "ORD-STR-003A"),
        _ar_invoice("INV-STR-003B", "CUST-006", "Pinnacle Retail", 40000, "2026-09-05", "2026-10-05", "Pinnacle POS module", "ORD-STR-003B"),
        _ar_invoice("INV-STR-004", "CUST-003", "Acme Industrial", 50000, "2026-09-06", "2026-10-06", "Acme spare parts", "ORD-STR-004"),
        _ar_invoice("INV-STR-005", "CUST-003", "Acme Industrial", 75000, "2026-09-07", "2026-10-07", "Acme tooling", "ORD-STR-005"),
        _ar_invoice("INV-STR-006", "CUST-005", "Orbit Health", 80000, "2026-09-08", "2026-10-08", "Orbit implementation", "ORD-STR-006"),
        _ar_invoice("INV-STR-007", "CUST-011", "Lumen Labs", 200000, "2026-09-09", "2026-10-09", "Lumen international wire replacement", "ORD-STR-007"),
        _ar_invoice("INV-STR-010", "CUST-006", "Pinnacle Retail", 125000, "2026-09-10", "2026-10-10", "Pinnacle autumn restock", "ORD-STR-010"),
        _ar_invoice("INV-STR-011A", "CUST-004", "Brightline Media", 90000, "2026-09-04", "2026-10-04", "Q3 analytics retainer", "ORD-STR-011A"),
        _ar_invoice("INV-STR-011B", "CUST-004", "Brightline Media", 90000, "2026-09-12", "2026-10-12", "Brand studio sprint", "ORD-STR-011B"),
        _ar_invoice("INV-STR-012A", "CUST-002", "Helios Analytics", 70000, "2026-09-14", "2026-10-14", "Helios refundable workshop", "ORD-STR-012A"),
        _ar_invoice("INV-STR-012B", "CUST-002", "Helios Analytics", 30000, "2026-09-14", "2026-10-14", "Helios extra seats", "ORD-STR-012B"),
        _ar_invoice("INV-STR-013A", "CUST-005", "Orbit Health", 55000, "2026-09-16", "2026-10-16", "Orbit monitoring", "ORD-STR-013A"),
        _ar_invoice("INV-STR-013B", "CUST-005", "Orbit Health", 25000, "2026-09-16", "2026-10-16", "Orbit alerts pack", "ORD-STR-013B"),
        _ar_invoice("INV-STR-014", "CUST-009", "Northstar LLC", 1240000, "2026-09-01", "2026-09-30", "Northstar platform", "ORD-STR-014"),
        _ar_invoice("INV-STR-015", "CUST-001", "Northwind Labs", 220000, "2026-09-29", "2026-10-29", "Late September expansion", "ORD-STR-015"),
        _ar_invoice("INV-STR-016", "CUST-012", "Harbor Electric", 180000, "2026-09-18", "2026-10-18", "Harbor field service", "ORD-STR-016"),
        _ar_invoice("INV-STR-017", "CUST-008", "Summit Logistics", 64000, "2026-09-19", "2026-10-19", "Summit retry shipment", "ORD-STR-017"),
        {
            **_ar_invoice("INV-STR-018A", "CUST-010", "Atlas Systems", 88000, "2026-08-20", "2026-09-19", "Atlas August platform fee", "monthly platform fee"),
            "outstanding_amount": 0.0,
            "status": "PAID",
        },
        _ar_invoice("INV-STR-018B", "CUST-010", "Atlas Systems", 88000, "2026-09-20", "2026-10-20", "Atlas September platform fee", "monthly platform fee"),
        _ar_invoice("INV-STR-018C", "CUST-010", "Atlas Systems", 88000, "2026-09-21", "2026-10-21", "Atlas one-off professional services", "professional services"),
        _ar_invoice("INV-STR-019", "CUST-012", "Harbor Electric", 95000, "2026-09-21", "2026-10-21", "Harbor overpayment case", "ORD-STR-019"),
        _ar_invoice("INV-STR-021", "CUST-012", "Harbor Electric", 100000, "2026-09-22", "2026-10-22", "Harbor multi-payment install", "ORD-STR-021"),
    ]

    precedents = [
        {
            "precedent_id": "AR-PREC-STR-ATLAS-AUG",
            "customer_id": "CUST-010",
            "kind": "stripe_metadata",
            "summary": "Atlas Systems typically remits Stripe invoice references (INV-STR-018A) with description 'Atlas August platform fee monthly platform fee'.",
            "facts": {
                "invoice_ids": ["INV-STR-018A"],
                "description": "Atlas August platform fee monthly platform fee",
                "source": "stripe",
                "amount": 880.0,
            },
            "source": "stripe",
            "support_count": 2,
            "source_payment_id": "PAY-STR-CH_STR_mem_aug",
        }
    ]

    sales: list[dict[str, Any]] = []

    def add_sale(**kwargs) -> dict[str, Any]:
        row = _sale(**kwargs)
        sales.append(row)
        return row

    s1 = add_sale(suffix="001", customer_stripe="cus_str_northwind", customer_name="Northwind Labs", amount=100000, created=t_sep3, invoice_id="INV-STR-001", description="INV-STR-001 September platform subscription", payout_id="po_str_001")
    s2a = add_sale(suffix="002a", customer_stripe="cus_str_helios", customer_name="Helios Analytics", amount=100000, created=t_sep8, invoice_id="INV-STR-002A", description="INV-STR-002A Helios workspace A", payout_id="po_str_002")
    s2b = add_sale(suffix="002b", customer_stripe="cus_str_helios", customer_name="Helios Analytics", amount=150000, created=t_sep8, invoice_id="INV-STR-002B", description="INV-STR-002B Helios workspace B AMEX", payout_id="po_str_002", fee=4405)
    s2c = add_sale(suffix="002c", customer_stripe="cus_str_helios", customer_name="Helios Analytics", amount=50000, created=t_sep8, invoice_id="INV-STR-002C", description="INV-STR-002C Helios add-on seats", payout_id="po_str_002")
    s3a = add_sale(suffix="003a", customer_stripe="cus_str_northwind", customer_name="Northwind Labs", amount=60000, created=t_sep10, invoice_id="INV-STR-003A", description="INV-STR-003A Northwind analytics pack", payout_id="po_str_003")
    s3b = add_sale(suffix="003b", customer_stripe="cus_str_pinnacle", customer_name="Pinnacle Retail", amount=40000, created=t_sep10, invoice_id="INV-STR-003B", description="INV-STR-003B Pinnacle POS module", payout_id="po_str_003")
    s4 = add_sale(suffix="004", customer_stripe="cus_str_acme", customer_name="Acme Industrial", amount=50000, created=t_sep11, invoice_id="INV-STR-004", description="INV-STR-004 Acme spare parts", payout_id="po_str_004")
    s5 = add_sale(suffix="005", customer_stripe="cus_str_acme", customer_name="Acme Industrial", amount=75000, created=t_sep12, invoice_id="INV-STR-005", description="INV-STR-005 Acme tooling", payout_id="po_str_005a")
    s6 = add_sale(suffix="006", customer_stripe="cus_str_orbit", customer_name="Orbit Health", amount=80000, created=t_sep15, invoice_id="INV-STR-006", description="INV-STR-006 Orbit implementation", payout_id="po_str_006a")
    s7 = add_sale(suffix="007", customer_stripe="cus_str_lumen", customer_name="Lumen Labs", amount=200000, created=t_sep16, invoice_id="INV-STR-007", description="INV-STR-007 Lumen international", payout_id="po_str_007", fee=7200)
    s10 = add_sale(suffix="010", customer_stripe="cus_str_pinnacle", customer_name="Pinnacle Retail", amount=125000, created=t_sep18, invoice_id=None, description="Pinnacle autumn restock", payout_id="po_str_010", extra_metadata={"customer_id": "CUST-006"})
    s11 = add_sale(suffix="011", customer_stripe="cus_str_brightline", customer_name="Brightline Media", amount=90000, created=t_sep20, invoice_id=None, description="Q3 analytics retainer", payout_id="po_str_011", extra_metadata={"customer_id": "CUST-004"})
    s12a = add_sale(suffix="012a", customer_stripe="cus_str_helios", customer_name="Helios Analytics", amount=70000, created=t_sep22, invoice_id="INV-STR-012A", description="INV-STR-012A Helios refundable workshop", payout_id="po_str_012")
    s12b = add_sale(suffix="012b", customer_stripe="cus_str_helios", customer_name="Helios Analytics", amount=30000, created=t_sep22, invoice_id="INV-STR-012B", description="INV-STR-012B Helios extra seats", payout_id="po_str_012")
    s13a = add_sale(suffix="013a", customer_stripe="cus_str_orbit", customer_name="Orbit Health", amount=55000, created=t_sep24, invoice_id="INV-STR-013A", description="INV-STR-013A Orbit monitoring", payout_id="po_str_013")
    s13b = add_sale(suffix="013b", customer_stripe="cus_str_orbit", customer_name="Orbit Health", amount=25000, created=t_sep24, invoice_id="INV-STR-013B", description="INV-STR-013B Orbit alerts pack", payout_id="po_str_013")
    s14 = add_sale(suffix="014", customer_stripe="cus_str_northstar", customer_name="Northstar LLC", amount=1240000, created=t_sep25, invoice_id="INV-STR-014", description="INV-STR-014 Northstar platform", payout_id="po_str_014")
    s15 = add_sale(suffix="015", customer_stripe="cus_str_northwind", customer_name="Northwind Labs", amount=220000, created=t_sep29, invoice_id="INV-STR-015", description="INV-STR-015 Late September expansion", payout_id="po_str_015")
    s16 = add_sale(suffix="016", customer_stripe="cus_str_harbor", customer_name="Harbor Electric", amount=60000, created=t_sep26, invoice_id="INV-STR-016", description="INV-STR-016 Harbor partial", payout_id="po_str_016")
    s17_fail_pi = payment_intent(pi_id="pi_str_017_fail", amount=64000, customer_id="cus_str_summit", created=t_sep19, status="requires_payment_method", description="INV-STR-017 failed card", metadata={"invoice_id": "INV-STR-017", "customer_name": "Summit Logistics"})
    s17 = add_sale(suffix="017", customer_stripe="cus_str_summit", customer_name="Summit Logistics", amount=64000, created=t_sep20, invoice_id="INV-STR-017", description="INV-STR-017 Summit retry shipment", payout_id="po_str_017")
    s18 = add_sale(suffix="018", customer_stripe="cus_str_atlas", customer_name="Atlas Systems", amount=88000, created=t_sep28, invoice_id=None, description="monthly platform fee", payout_id="po_str_018", extra_metadata={"customer_id": "CUST-010"})
    s19 = add_sale(suffix="019", customer_stripe="cus_str_harbor", customer_name="Harbor Electric", amount=110000, created=t_sep26, invoice_id="INV-STR-019", description="INV-STR-019 Harbor overpayment", payout_id="po_str_019")
    s20 = add_sale(suffix="020", customer_stripe="cus_str_orion", customer_name="Orion Freight", amount=33000, created=t_sep27, invoice_id=None, description="Unmatched Stripe charge", payout_id="po_str_020")
    s21a = add_sale(suffix="021a", customer_stripe="cus_str_harbor", customer_name="Harbor Electric", amount=40000, created=t_sep26, invoice_id="INV-STR-021", description="INV-STR-021 Harbor installment 1", payout_id="po_str_021", extra_metadata={"customer_id": "CUST-012"})
    s21b = add_sale(suffix="021b", customer_stripe="cus_str_harbor", customer_name="Harbor Electric", amount=60000, created=t_sep27, invoice_id="INV-STR-021", description="INV-STR-021 Harbor installment 2", payout_id="po_str_021", extra_metadata={"customer_id": "CUST-012"})

    refund4 = refund(refund_id="re_str_004", amount=10000, charge_id="ch_str_004", created=t_sep11, metadata={"invoice_id": "INV-STR-004"}, payment_intent="pi_str_004", balance_transaction="txn_str_004_re")
    txn_re4 = balance_transaction(txn_id="txn_str_004_re", amount=10000, fee=0, txn_type="refund", payout_id="po_str_004", created=t_sep11, source=refund4, description="Partial refund INV-STR-004")
    refund5 = refund(refund_id="re_str_005", amount=75000, charge_id="ch_str_005", created=t_sep22, metadata={"invoice_id": "INV-STR-005"}, payment_intent="pi_str_005", balance_transaction="txn_str_005_re")
    txn_re5 = balance_transaction(txn_id="txn_str_005_re", amount=75000, fee=0, txn_type="refund", payout_id="po_str_005b", created=t_sep22, source=refund5, description="Full refund after payout INV-STR-005")
    refund12 = refund(refund_id="re_str_012", amount=20000, charge_id="ch_str_012a", created=t_sep22, metadata={"invoice_id": "INV-STR-012A"}, payment_intent="pi_str_012a", balance_transaction="txn_str_012_re")
    txn_re12 = balance_transaction(txn_id="txn_str_012_re", amount=20000, fee=0, txn_type="refund", payout_id="po_str_012", created=t_sep22, source=refund12, description="Workshop refund")

    def _bt_ref(txn: dict[str, Any], source_id: str) -> dict[str, Any]:
        row = {key: value for key, value in txn.items() if key != "source"}
        row["source"] = source_id
        return row

    dp6 = dispute(dispute_id="dp_str_006", amount=80000, charge_id="ch_str_006", created=t_sep26, fee=1500, payment_intent="pi_str_006")
    txn_dp6 = balance_transaction(txn_id="txn_str_006_dp", amount=80000, fee=0, txn_type="dispute", payout_id="po_str_006b", created=t_sep26, source=dp6, description="Chargeback INV-STR-006")
    txn_dp6_fee = balance_transaction(txn_id="txn_str_006_dp_fee", amount=1500, fee=0, txn_type="stripe_fee", payout_id="po_str_006b", created=t_sep26, source=dp6, description="Dispute fee")
    dp6["balance_transactions"] = [_bt_ref(txn_dp6, "dp_str_006"), _bt_ref(txn_dp6_fee, "dp_str_006")]
    dp13 = dispute(dispute_id="dp_str_013", amount=25000, charge_id="ch_str_013b", created=t_sep24, fee=1500, payment_intent="pi_str_013b")
    txn_dp13 = balance_transaction(txn_id="txn_str_013_dp", amount=25000, fee=0, txn_type="dispute", payout_id="po_str_013", created=t_sep24, source=dp13, description="Chargeback INV-STR-013B")
    txn_dp13_fee = balance_transaction(txn_id="txn_str_013_dp_fee", amount=1500, fee=0, txn_type="stripe_fee", payout_id="po_str_013", created=t_sep24, source=dp13, description="Dispute fee")
    dp13["balance_transactions"] = [_bt_ref(txn_dp13, "dp_str_013"), _bt_ref(txn_dp13_fee, "dp_str_013")]

    def net_of(*rows: dict[str, Any]) -> int:
        total = 0
        for row in rows:
            if row["type"] == "charge":
                total += int(row["amount"]) - int(row.get("fee") or 0)
            else:
                total += int(row["amount"])
        return total

    payouts_by_id: dict[str, dict[str, Any]] = {}
    deposits: list[dict[str, Any]] = []
    txns = [row["txn"] for row in sales] + [txn_re4, txn_re5, txn_re12, txn_dp6, txn_dp6_fee, txn_dp13, txn_dp13_fee]

    def register_payout(payout_id: str, created: int, arrival: int, members: list[dict[str, Any]], bank_delta: int = 0) -> dict[str, Any]:
        amount = net_of(*members)
        po = payout(payout_id=payout_id, amount=amount, created=created, arrival=arrival)
        payouts_by_id[payout_id] = po
        deposits.append(
            bank_deposit(
                deposit_id=f"BANK-STR-{payout_id.split('_')[-1].upper()}",
                payout_id=payout_id,
                amount_cents=amount + bank_delta,
                date=iso_date(arrival),
            )
        )
        return po

    register_payout("po_str_001", t_sep4, t_sep4, [s1["txn"]])
    register_payout("po_str_002", t_sep9, t_sep9, [s2a["txn"], s2b["txn"], s2c["txn"]])
    register_payout("po_str_003", t_sep11, t_sep11, [s3a["txn"], s3b["txn"]])
    register_payout("po_str_004", t_sep12, t_sep12, [s4["txn"], txn_re4])
    register_payout("po_str_005a", t_sep15, t_sep15, [s5["txn"]])
    register_payout("po_str_005b", t_sep22, t_sep22, [txn_re5])
    register_payout("po_str_006a", t_sep16, t_sep16, [s6["txn"]])
    register_payout("po_str_006b", t_sep26, t_sep26, [txn_dp6, txn_dp6_fee])
    register_payout("po_str_007", t_sep18, t_sep18, [s7["txn"]])
    register_payout("po_str_009", t_sep9, t_sep9, [s2a["txn"], s2b["txn"], s2c["txn"]])  # unused alias safety
    register_payout("po_str_010", t_sep20, t_sep20, [s10["txn"]])
    register_payout("po_str_011", t_sep22, t_sep22, [s11["txn"]])
    register_payout("po_str_012", t_sep24, t_sep24, [s12a["txn"], s12b["txn"], txn_re12])
    register_payout("po_str_013", t_sep25, t_sep25, [s13a["txn"], s13b["txn"], txn_dp13, txn_dp13_fee])
    register_payout("po_str_014", t_sep26, t_sep26, [s14["txn"]], bank_delta=-1240)
    register_payout("po_str_015", t_oct2, t_oct2, [s15["txn"]])
    register_payout("po_str_016", t_sep28, t_sep28, [s16["txn"]])
    register_payout("po_str_017", t_sep22, t_sep22, [s17["txn"]])
    register_payout("po_str_018", t_sep29, t_sep29, [s18["txn"]])
    register_payout("po_str_019", t_sep28, t_sep28, [s19["txn"]])
    register_payout("po_str_020", t_sep28, t_sep28, [s20["txn"]])
    register_payout("po_str_021", t_sep28, t_sep28, [s21a["txn"], s21b["txn"]])
    payouts_by_id.pop("po_str_009", None)
    deposits[:] = [item for item in deposits if item["payout_id"] != "po_str_009"]

    def payout_events(payout_id: str, created: int, include_created: bool = True) -> list[dict[str, Any]]:
        po = payouts_by_id[payout_id]
        rows = []
        if include_created:
            rows.append(event(f"evt_{payout_id}_created", "payout.created", {**po, "status": "in_transit"}, created))
        rows.append(event(f"evt_{payout_id}_recon", "payout.reconciliation_completed", {**po, "status": "paid"}, created + 3600))
        return rows

    def payment_events(sale: dict[str, Any], created: int) -> list[dict[str, Any]]:
        return [
            event(f"evt_{sale['charge']['id']}_pi", "payment_intent.succeeded", sale["pi"], created),
            event(f"evt_{sale['charge']['id']}_ch", "charge.succeeded", sale["charge"], created + 10),
        ]

    stripe_customers = [
        {"id": "cus_str_northwind", "object": "customer", "name": "Northwind Labs", "created": t_sep3},
        {"id": "cus_str_helios", "object": "customer", "name": "Helios Analytics", "created": t_sep3},
        {"id": "cus_str_acme", "object": "customer", "name": "Acme Industrial", "created": t_sep3},
        {"id": "cus_str_brightline", "object": "customer", "name": "Brightline Media", "created": t_sep3},
        {"id": "cus_str_orbit", "object": "customer", "name": "Orbit Health", "created": t_sep3},
        {"id": "cus_str_pinnacle", "object": "customer", "name": "Pinnacle Retail", "created": t_sep3},
        {"id": "cus_str_summit", "object": "customer", "name": "Summit Logistics", "created": t_sep3},
        {"id": "cus_str_northstar", "object": "customer", "name": "Northstar LLC", "created": t_sep3},
        {"id": "cus_str_atlas", "object": "customer", "name": "Atlas Systems", "created": t_sep3},
        {"id": "cus_str_lumen", "object": "customer", "name": "Lumen Labs", "created": t_sep3},
        {"id": "cus_str_harbor", "object": "customer", "name": "Harbor Electric", "created": t_sep3},
        {"id": "cus_str_orion", "object": "customer", "name": "Orion Freight", "created": t_sep3},
    ]

    charges = [row["charge"] for row in sales]
    pis = [row["pi"] for row in sales] + [s17_fail_pi]
    refunds = [refund4, refund5, refund12]
    disputes = [dp6, dp13]
    payouts = list(payouts_by_id.values())

    def gt(**kwargs) -> GroundTruth:
        return GroundTruth(**kwargs)

    def gl(kind: str, amount: int) -> dict[str, Any]:
        return {"entry_type": kind, "amount_cents": amount}

    scenarios = [
        Scenario(
            scenario_id="stripe_simple_payment",
            title="Simple payment",
            difficulty="easy",
            events=payment_events(s1, t_sep3) + payout_events("po_str_001", t_sep4),
            ground_truth=gt(
                scenario_id="stripe_simple_payment",
                expected_classification="charge",
                expected_workflow="ar_cash_application",
                expected_customer_invoice_ids=["INV-STR-001"],
                expected_payment_ids=["PAY-STR-CH_STR_001"],
                expected_balance_transaction_ids=["txn_str_001"],
                expected_payout_id="po_str_001",
                expected_bank_transaction_id="BANK-STR-001",
                gross_amount_cents=100000,
                fee_amount_cents=s1["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s1["net"],
                expected_ar_effect_cents=-100000,
                expected_cash_effect_cents=s1["net"],
                expected_gl_entries=[gl("cash_receipt", 100000), gl("processor_fee", s1["fee"])],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["INV-STR-001", "ch_str_001", "po_str_001", "BANK-STR-001"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="Customer invoice $1,000; Stripe fee $29.30; net $970.70.",
                expected_behavior="Match INV-STR-001, book fee separately, reconcile payout to bank.",
            ),
        ),
        Scenario(
            scenario_id="stripe_payout_multiple_payments",
            title="One payout containing several payments",
            difficulty="easy",
            events=payment_events(s2a, t_sep8) + payment_events(s2b, t_sep8) + payment_events(s2c, t_sep8) + payout_events("po_str_002", t_sep9),
            ground_truth=gt(
                scenario_id="stripe_payout_multiple_payments",
                expected_classification="payout_bundle",
                expected_workflow="stripe_payout_reconciliation",
                expected_customer_invoice_ids=["INV-STR-002A", "INV-STR-002B", "INV-STR-002C"],
                expected_payment_ids=["PAY-STR-CH_STR_002a", "PAY-STR-CH_STR_002b", "PAY-STR-CH_STR_002c"],
                expected_balance_transaction_ids=["txn_str_002a", "txn_str_002b", "txn_str_002c"],
                expected_payout_id="po_str_002",
                expected_bank_transaction_id="BANK-STR-002",
                gross_amount_cents=300000,
                fee_amount_cents=s2a["fee"] + s2b["fee"] + s2c["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s2a["net"] + s2b["net"] + s2c["net"],
                expected_ar_effect_cents=-300000,
                expected_cash_effect_cents=s2a["net"] + s2b["net"] + s2c["net"],
                expected_gl_entries=[gl("cash_receipt", 300000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["po_str_002", "INV-STR-002A", "INV-STR-002B", "INV-STR-002C"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="Three Helios payments with nets $970.70, $1,455.95, $485.20 in one payout.",
                expected_behavior="Do not require payout == one invoice; reconcile the bundle.",
            ),
        ),
        Scenario(
            scenario_id="stripe_many_txns_one_deposit",
            title="Several balance transactions to one bank deposit",
            difficulty="easy",
            events=payment_events(s3a, t_sep10) + payment_events(s3b, t_sep10) + payout_events("po_str_003", t_sep11),
            ground_truth=gt(
                scenario_id="stripe_many_txns_one_deposit",
                expected_classification="payout_bundle",
                expected_workflow="stripe_payout_reconciliation",
                expected_customer_invoice_ids=["INV-STR-003A", "INV-STR-003B"],
                expected_payment_ids=["PAY-STR-CH_STR_003a", "PAY-STR-CH_STR_003b"],
                expected_balance_transaction_ids=["txn_str_003a", "txn_str_003b"],
                expected_payout_id="po_str_003",
                expected_bank_transaction_id="BANK-STR-003",
                gross_amount_cents=100000,
                fee_amount_cents=s3a["fee"] + s3b["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s3a["net"] + s3b["net"],
                expected_ar_effect_cents=-100000,
                expected_cash_effect_cents=s3a["net"] + s3b["net"],
                expected_gl_entries=[gl("cash_receipt", 100000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["po_str_003", "BANK-STR-003"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="Two customers' charges settle in one Stripe payout / bank deposit.",
                expected_behavior="Aggregate by payout membership and match the deposit.",
            ),
        ),
        Scenario(
            scenario_id="stripe_refund_before_payout",
            title="Refund before payout",
            difficulty="medium",
            events=payment_events(s4, t_sep11) + [event("evt_re_str_004", "refund.created", refund4, t_sep11)] + payout_events("po_str_004", t_sep12),
            ground_truth=gt(
                scenario_id="stripe_refund_before_payout",
                expected_classification="refund",
                expected_workflow="ar_refund",
                expected_customer_invoice_ids=["INV-STR-004"],
                expected_payment_ids=["PAY-STR-CH_STR_004"],
                expected_balance_transaction_ids=["txn_str_004", "txn_str_004_re"],
                expected_payout_id="po_str_004",
                expected_bank_transaction_id="BANK-STR-004",
                gross_amount_cents=50000,
                fee_amount_cents=s4["fee"],
                refund_amount_cents=10000,
                dispute_amount_cents=0,
                expected_net_cents=s4["net"] - 10000,
                expected_ar_effect_cents=-40000,
                expected_cash_effect_cents=s4["net"] - 10000,
                expected_gl_entries=[gl("cash_receipt", 50000), gl("refund", 10000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["INV-STR-004", "re_str_004", "po_str_004"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="$500 charge, $100 refund before payout.",
                expected_behavior="Keep original payment, book refund separately, reconcile reduced net.",
            ),
        ),
        Scenario(
            scenario_id="stripe_refund_after_payout",
            title="Refund after original payout",
            difficulty="medium",
            events=payment_events(s5, t_sep12) + payout_events("po_str_005a", t_sep15) + [event("evt_re_str_005", "refund.created", refund5, t_sep22)] + payout_events("po_str_005b", t_sep22),
            ground_truth=gt(
                scenario_id="stripe_refund_after_payout",
                expected_classification="refund_after_payout",
                expected_workflow="ar_refund",
                expected_customer_invoice_ids=["INV-STR-005"],
                expected_payment_ids=["PAY-STR-CH_STR_005"],
                expected_balance_transaction_ids=["txn_str_005", "txn_str_005_re"],
                expected_payout_id="po_str_005b",
                expected_bank_transaction_id="BANK-STR-005B",
                gross_amount_cents=75000,
                fee_amount_cents=s5["fee"],
                refund_amount_cents=75000,
                dispute_amount_cents=0,
                expected_net_cents=-75000,
                expected_ar_effect_cents=0,
                expected_cash_effect_cents=-75000,
                expected_gl_entries=[gl("cash_receipt", 75000), gl("refund", 75000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["po_str_005a", "po_str_005b", "re_str_005"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="Original $750 sale already paid out; later full refund reduces a future payout.",
                expected_behavior="Refund payout differs from sale payout; history preserved.",
            ),
        ),
        Scenario(
            scenario_id="stripe_chargeback",
            title="Chargeback / dispute",
            difficulty="medium",
            events=payment_events(s6, t_sep15) + payout_events("po_str_006a", t_sep16) + [event("evt_dp_str_006", "charge.dispute.created", dp6, t_sep26)] + payout_events("po_str_006b", t_sep26),
            ground_truth=gt(
                scenario_id="stripe_chargeback",
                expected_classification="dispute",
                expected_workflow="ar_dispute",
                expected_customer_invoice_ids=["INV-STR-006"],
                expected_payment_ids=["PAY-STR-CH_STR_006"],
                expected_balance_transaction_ids=["txn_str_006", "txn_str_006_dp", "txn_str_006_dp_fee"],
                expected_payout_id="po_str_006b",
                expected_bank_transaction_id="BANK-STR-006B",
                gross_amount_cents=80000,
                fee_amount_cents=1500,
                refund_amount_cents=0,
                dispute_amount_cents=80000,
                expected_net_cents=-81500,
                expected_ar_effect_cents=-80000,
                expected_cash_effect_cents=-81500,
                expected_gl_entries=[gl("cash_receipt", 80000), gl("dispute", 80000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding="stripe_dispute",
                expected_context_links=["dp_str_006", "INV-STR-006", "po_str_006b"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="$800 payment later charged back plus $15 dispute fee.",
                expected_behavior="Do not treat the cash reduction as an unexplained bank break.",
            ),
        ),
        Scenario(
            scenario_id="stripe_fee_variation",
            title="Fee variation",
            difficulty="easy",
            events=payment_events(s7, t_sep16) + payout_events("po_str_007", t_sep18),
            ground_truth=gt(
                scenario_id="stripe_fee_variation",
                expected_classification="charge",
                expected_workflow="ar_cash_application",
                expected_customer_invoice_ids=["INV-STR-007"],
                expected_payment_ids=["PAY-STR-CH_STR_007"],
                expected_balance_transaction_ids=["txn_str_007"],
                expected_payout_id="po_str_007",
                expected_bank_transaction_id="BANK-STR-007",
                gross_amount_cents=200000,
                fee_amount_cents=7200,
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=192800,
                expected_ar_effect_cents=-200000,
                expected_cash_effect_cents=192800,
                expected_gl_entries=[gl("cash_receipt", 200000), gl("processor_fee", 7200)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["INV-STR-007", "po_str_007"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="International / AMEX effective fee $72.00 on $2,000, not 2.9%+$0.30.",
                expected_behavior="Use source fee facts; do not hard-code a universal rate.",
            ),
        ),
        Scenario(
            scenario_id="stripe_duplicate_event",
            title="Duplicate webhook",
            difficulty="easy",
            events=payment_events(s1, t_sep3) + payout_events("po_str_001", t_sep4),
            replay_event_id="evt_po_str_001_recon",
            ground_truth=gt(
                scenario_id="stripe_duplicate_event",
                expected_classification="duplicate",
                expected_workflow="idempotency",
                expected_customer_invoice_ids=["INV-STR-001"],
                expected_payment_ids=["PAY-STR-CH_STR_001"],
                expected_balance_transaction_ids=["txn_str_001"],
                expected_payout_id="po_str_001",
                expected_bank_transaction_id="BANK-STR-001",
                gross_amount_cents=100000,
                fee_amount_cents=s1["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s1["net"],
                expected_ar_effect_cents=-100000,
                expected_cash_effect_cents=s1["net"],
                expected_gl_entries=[gl("cash_receipt", 100000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code="duplicate_event",
                expected_audit_finding=None,
                expected_context_links=["evt_po_str_001_recon"],
                expected_cash_decision="AUTO_APPLY",
                expected_duplicate_suppressed=True,
                input_condition="Exact same payout.reconciliation_completed event delivered twice.",
                expected_behavior="Idempotent: no second payment, journal, or reconciliation.",
            ),
        ),
        Scenario(
            scenario_id="stripe_out_of_order",
            title="Events delivered out of order",
            difficulty="hard",
            events=payout_events("po_str_001", t_sep4, include_created=False)
            + payment_events(s1, t_sep3)
            + [event("evt_po_str_001_created", "payout.created", {**payouts_by_id["po_str_001"], "status": "in_transit"}, t_sep4)],
            withhold_txn_ids=["txn_str_001"],
            release_txn_ids=["txn_str_001"],
            ground_truth=gt(
                scenario_id="stripe_out_of_order",
                expected_classification="charge",
                expected_workflow="stripe_payout_reconciliation",
                expected_customer_invoice_ids=["INV-STR-001"],
                expected_payment_ids=["PAY-STR-CH_STR_001"],
                expected_balance_transaction_ids=["txn_str_001"],
                expected_payout_id="po_str_001",
                expected_bank_transaction_id="BANK-STR-001",
                gross_amount_cents=100000,
                fee_amount_cents=s1["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s1["net"],
                expected_ar_effect_cents=-100000,
                expected_cash_effect_cents=s1["net"],
                expected_gl_entries=[gl("cash_receipt", 100000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["po_str_001", "ch_str_001"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="Payout event arrives before charge and before balance-transaction release.",
                expected_behavior="Eventually reach the correct canonical payout and AR state.",
            ),
        ),
        Scenario(
            scenario_id="stripe_missing_metadata",
            title="Missing invoice metadata",
            difficulty="medium",
            events=payment_events(s10, t_sep18) + payout_events("po_str_010", t_sep20),
            ground_truth=gt(
                scenario_id="stripe_missing_metadata",
                expected_classification="charge",
                expected_workflow="ar_cash_application",
                expected_customer_invoice_ids=["INV-STR-010"],
                expected_payment_ids=["PAY-STR-CH_STR_010"],
                expected_balance_transaction_ids=["txn_str_010"],
                expected_payout_id="po_str_010",
                expected_bank_transaction_id="BANK-STR-010",
                gross_amount_cents=125000,
                fee_amount_cents=s10["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s10["net"],
                expected_ar_effect_cents=-125000,
                expected_cash_effect_cents=s10["net"],
                expected_gl_entries=[gl("cash_receipt", 125000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["INV-STR-010"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="Stripe payment has no internal invoice ID; unique $1,250 Pinnacle invoice.",
                expected_behavior="Match from customer + amount + description, not ID lookup alone.",
            ),
        ),
        Scenario(
            scenario_id="stripe_ambiguous_invoice",
            title="Ambiguous invoice match",
            difficulty="hard",
            events=payment_events(s11, t_sep20) + payout_events("po_str_011", t_sep22),
            ground_truth=gt(
                scenario_id="stripe_ambiguous_invoice",
                expected_classification="charge",
                expected_workflow="ar_cash_application",
                expected_customer_invoice_ids=["INV-STR-011A"],
                expected_payment_ids=["PAY-STR-CH_STR_011"],
                expected_balance_transaction_ids=["txn_str_011"],
                expected_payout_id="po_str_011",
                expected_bank_transaction_id="BANK-STR-011",
                gross_amount_cents=90000,
                fee_amount_cents=s11["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s11["net"],
                expected_ar_effect_cents=-90000,
                expected_cash_effect_cents=s11["net"],
                expected_gl_entries=[gl("cash_receipt", 90000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["INV-STR-011A"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="Brightline has two $900 invoices; description is Q3 analytics retainer.",
                expected_behavior="Use description context; do not pick an arbitrary invoice.",
            ),
        ),
        Scenario(
            scenario_id="stripe_payout_with_refund",
            title="Combined payout with refund",
            difficulty="medium",
            events=payment_events(s12a, t_sep22) + payment_events(s12b, t_sep22) + [event("evt_re_str_012", "refund.created", refund12, t_sep22)] + payout_events("po_str_012", t_sep24),
            ground_truth=gt(
                scenario_id="stripe_payout_with_refund",
                expected_classification="payout_bundle",
                expected_workflow="stripe_payout_reconciliation",
                expected_customer_invoice_ids=["INV-STR-012A", "INV-STR-012B"],
                expected_payment_ids=["PAY-STR-CH_STR_012a", "PAY-STR-CH_STR_012b"],
                expected_balance_transaction_ids=["txn_str_012a", "txn_str_012b", "txn_str_012_re"],
                expected_payout_id="po_str_012",
                expected_bank_transaction_id="BANK-STR-012",
                gross_amount_cents=100000,
                fee_amount_cents=s12a["fee"] + s12b["fee"],
                refund_amount_cents=20000,
                dispute_amount_cents=0,
                expected_net_cents=s12a["net"] + s12b["net"] - 20000,
                expected_ar_effect_cents=-80000,
                expected_cash_effect_cents=s12a["net"] + s12b["net"] - 20000,
                expected_gl_entries=[gl("cash_receipt", 100000), gl("refund", 20000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["po_str_012", "re_str_012"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="Two successful charges plus a $200 refund in one payout.",
                expected_behavior="Bank amount is not the sum of gross sales.",
            ),
        ),
        Scenario(
            scenario_id="stripe_payout_with_dispute",
            title="Combined payout with dispute",
            difficulty="medium",
            events=payment_events(s13a, t_sep24) + payment_events(s13b, t_sep24) + [event("evt_dp_str_013", "charge.dispute.created", dp13, t_sep24)] + payout_events("po_str_013", t_sep25),
            ground_truth=gt(
                scenario_id="stripe_payout_with_dispute",
                expected_classification="payout_bundle",
                expected_workflow="stripe_payout_reconciliation",
                expected_customer_invoice_ids=["INV-STR-013A", "INV-STR-013B"],
                expected_payment_ids=["PAY-STR-CH_STR_013a", "PAY-STR-CH_STR_013b"],
                expected_balance_transaction_ids=["txn_str_013a", "txn_str_013b", "txn_str_013_dp", "txn_str_013_dp_fee"],
                expected_payout_id="po_str_013",
                expected_bank_transaction_id="BANK-STR-013",
                gross_amount_cents=80000,
                fee_amount_cents=s13a["fee"] + s13b["fee"] + 1500,
                refund_amount_cents=0,
                dispute_amount_cents=25000,
                expected_net_cents=s13a["net"] + s13b["net"] - 25000 - 1500,
                expected_ar_effect_cents=-80000,
                expected_cash_effect_cents=s13a["net"] + s13b["net"] - 26500,
                expected_gl_entries=[gl("cash_receipt", 80000), gl("dispute", 25000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding="stripe_dispute",
                expected_context_links=["po_str_013", "dp_str_013"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="Successful charges plus a $250 chargeback and $15 fee in one payout.",
                expected_behavior="Net settlement includes the dispute; not an unexplained break.",
            ),
        ),
        Scenario(
            scenario_id="stripe_bank_discrepancy_1240",
            title="Bank deposit differs from payout",
            difficulty="hard",
            events=payment_events(s14, t_sep25) + payout_events("po_str_014", t_sep26),
            ground_truth=gt(
                scenario_id="stripe_bank_discrepancy_1240",
                expected_classification="bank_mismatch",
                expected_workflow="cash_reconciliation_exception",
                expected_customer_invoice_ids=["INV-STR-014"],
                expected_payment_ids=["PAY-STR-CH_STR_014"],
                expected_balance_transaction_ids=["txn_str_014"],
                expected_payout_id="po_str_014",
                expected_bank_transaction_id="BANK-STR-014",
                gross_amount_cents=1240000,
                fee_amount_cents=s14["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s14["net"],
                expected_ar_effect_cents=-1240000,
                expected_cash_effect_cents=s14["net"] - 1240,
                expected_gl_entries=[gl("cash_receipt", 1240000)],
                expected_reconciliation_status="MISMATCH",
                expected_close_effect="BLOCK_CLOSE",
                expected_exception_code="bank_amount_differs_from_stripe_payout",
                expected_audit_finding="unexplained_1240_difference",
                expected_context_links=["po_str_014", "BANK-STR-014", "INV-STR-014"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="Northstar Stripe payout bank deposit is short $12.40.",
                expected_behavior="Identify the exact mismatch; do not invent an explanation; block close.",
            ),
        ),
        Scenario(
            scenario_id="stripe_cross_period_timing",
            title="Cross-period settlement",
            difficulty="medium",
            events=payment_events(s15, t_sep29) + payout_events("po_str_015", t_oct2),
            period=PERIOD,
            cash_period="2026-10",
            ground_truth=gt(
                scenario_id="stripe_cross_period_timing",
                expected_classification="timing",
                expected_workflow="stripe_payout_reconciliation",
                expected_customer_invoice_ids=["INV-STR-015"],
                expected_payment_ids=["PAY-STR-CH_STR_015"],
                expected_balance_transaction_ids=["txn_str_015"],
                expected_payout_id="po_str_015",
                expected_bank_transaction_id="BANK-STR-015",
                gross_amount_cents=220000,
                fee_amount_cents=s15["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s15["net"],
                expected_ar_effect_cents=-220000,
                expected_cash_effect_cents=s15["net"],
                expected_gl_entries=[gl("cash_receipt", 220000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["INV-STR-015", "po_str_015"],
                expected_cash_decision="AUTO_APPLY",
                expected_settlement_period="2026-10",
                input_condition="Late-September charge settles in an October payout.",
                expected_behavior="September AR history stays correct; cash timing follows October settlement.",
            ),
        ),
        Scenario(
            scenario_id="stripe_partial_payment",
            title="Partial payment against one invoice",
            difficulty="easy",
            events=payment_events(s16, t_sep26) + payout_events("po_str_016", t_sep28),
            ground_truth=gt(
                scenario_id="stripe_partial_payment",
                expected_classification="partial",
                expected_workflow="ar_cash_application",
                expected_customer_invoice_ids=["INV-STR-016"],
                expected_payment_ids=["PAY-STR-CH_STR_016"],
                expected_balance_transaction_ids=["txn_str_016"],
                expected_payout_id="po_str_016",
                expected_bank_transaction_id="BANK-STR-016",
                gross_amount_cents=60000,
                fee_amount_cents=s16["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s16["net"],
                expected_ar_effect_cents=-60000,
                expected_cash_effect_cents=s16["net"],
                expected_gl_entries=[gl("cash_receipt", 60000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["INV-STR-016"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="$600 Stripe payment against $1,800 Harbor invoice.",
                expected_behavior="Partial apply; invoice remains open for the residual.",
            ),
        ),
        Scenario(
            scenario_id="stripe_failed_then_retry",
            title="Failed payment then successful retry",
            difficulty="easy",
            events=[
                event("evt_pi_str_017_fail", "payment_intent.payment_failed", s17_fail_pi, unix(2026, 9, 19)),
                *payment_events(s17, t_sep20),
                *payout_events("po_str_017", t_sep22),
            ],
            ground_truth=gt(
                scenario_id="stripe_failed_then_retry",
                expected_classification="charge",
                expected_workflow="ar_cash_application",
                expected_customer_invoice_ids=["INV-STR-017"],
                expected_payment_ids=["PAY-STR-CH_STR_017"],
                expected_balance_transaction_ids=["txn_str_017"],
                expected_payout_id="po_str_017",
                expected_bank_transaction_id="BANK-STR-017",
                gross_amount_cents=64000,
                fee_amount_cents=s17["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s17["net"],
                expected_ar_effect_cents=-64000,
                expected_cash_effect_cents=s17["net"],
                expected_gl_entries=[gl("cash_receipt", 64000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["INV-STR-017"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="Card fails, then the same invoice is paid on retry.",
                expected_behavior="Failed intent posts no cash; retry applies once.",
            ),
        ),
        Scenario(
            scenario_id="stripe_unmatched_order",
            title="Stripe charge with no internal order",
            difficulty="medium",
            events=payment_events(s20, unix(2026, 9, 27)) + payout_events("po_str_020", t_sep28),
            ground_truth=gt(
                scenario_id="stripe_unmatched_order",
                expected_classification="unmatched",
                expected_workflow="ar_cash_application",
                expected_customer_invoice_ids=[],
                expected_payment_ids=["PAY-STR-CH_STR_020"],
                expected_balance_transaction_ids=["txn_str_020"],
                expected_payout_id="po_str_020",
                expected_bank_transaction_id="BANK-STR-020",
                gross_amount_cents=33000,
                fee_amount_cents=s20["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s20["net"],
                expected_ar_effect_cents=0,
                expected_cash_effect_cents=s20["net"],
                expected_gl_entries=[],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["ch_str_020"],
                expected_cash_decision="UNAPPLIED",
                input_condition="Orion Freight Stripe charge has no corresponding internal invoice.",
                expected_behavior="Leave cash unapplied; do not invent an order.",
            ),
        ),
        Scenario(
            scenario_id="stripe_bank_before_payout",
            title="Bank record arrives before Stripe payout",
            difficulty="hard",
            events=payment_events(s1, t_sep3) + payout_events("po_str_001", t_sep4),
            bank_before_payout=True,
            ground_truth=gt(
                scenario_id="stripe_bank_before_payout",
                expected_classification="timing",
                expected_workflow="stripe_payout_reconciliation",
                expected_customer_invoice_ids=["INV-STR-001"],
                expected_payment_ids=["PAY-STR-CH_STR_001"],
                expected_balance_transaction_ids=["txn_str_001"],
                expected_payout_id="po_str_001",
                expected_bank_transaction_id="BANK-STR-001",
                gross_amount_cents=100000,
                fee_amount_cents=s1["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s1["net"],
                expected_ar_effect_cents=-100000,
                expected_cash_effect_cents=s1["net"],
                expected_gl_entries=[gl("cash_receipt", 100000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["BANK-STR-001", "po_str_001"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="Bank deposit is visible before the payout webhook.",
                expected_behavior="Eventually match using payout membership once Stripe arrives.",
            ),
        ),
        Scenario(
            scenario_id="stripe_cross_period_memory",
            title="Prior-period Stripe context improves a later match",
            difficulty="hard",
            events=payment_events(s18, t_sep28) + payout_events("po_str_018", t_sep29),
            ground_truth=gt(
                scenario_id="stripe_cross_period_memory",
                expected_classification="charge",
                expected_workflow="ar_cash_application",
                expected_customer_invoice_ids=["INV-STR-018B"],
                expected_payment_ids=["PAY-STR-CH_STR_018"],
                expected_balance_transaction_ids=["txn_str_018"],
                expected_payout_id="po_str_018",
                expected_bank_transaction_id="BANK-STR-018",
                gross_amount_cents=88000,
                fee_amount_cents=s18["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s18["net"],
                expected_ar_effect_cents=-88000,
                expected_cash_effect_cents=s18["net"],
                expected_gl_entries=[gl("cash_receipt", 88000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["INV-STR-018B", "AR-PREC-STR-ATLAS-AUG"],
                expected_cash_decision="AUTO_APPLY",
                uses_precedent=True,
                input_condition="Atlas has two $880 September invoices; metadata missing; August Stripe precedent is monthly platform fee.",
                expected_behavior="Use prior-period Stripe precedent plus description; do not overwrite current facts.",
            ),
        ),
        Scenario(
            scenario_id="stripe_overpayment",
            title="Overpayment residual",
            difficulty="medium",
            events=payment_events(s19, t_sep26) + payout_events("po_str_019", t_sep28),
            ground_truth=gt(
                scenario_id="stripe_overpayment",
                expected_classification="overpayment",
                expected_workflow="ar_cash_application",
                expected_customer_invoice_ids=["INV-STR-019"],
                expected_payment_ids=["PAY-STR-CH_STR_019"],
                expected_balance_transaction_ids=["txn_str_019"],
                expected_payout_id="po_str_019",
                expected_bank_transaction_id="BANK-STR-019",
                gross_amount_cents=110000,
                fee_amount_cents=s19["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s19["net"],
                expected_ar_effect_cents=0,
                expected_cash_effect_cents=s19["net"],
                expected_gl_entries=[],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["INV-STR-019"],
                expected_cash_decision="HUMAN_REVIEW",
                input_condition="$1,100 Stripe payment against $950 named invoice.",
                expected_behavior="Do not drop the residual; send overpayment to human review.",
            ),
        ),
        Scenario(
            scenario_id="stripe_multiple_payments_one_invoice",
            title="Multiple Stripe payments against one invoice",
            difficulty="easy",
            events=payment_events(s21a, t_sep26) + payment_events(s21b, t_sep27) + payout_events("po_str_021", t_sep28),
            ground_truth=gt(
                scenario_id="stripe_multiple_payments_one_invoice",
                expected_classification="partial",
                expected_workflow="ar_cash_application",
                expected_customer_invoice_ids=["INV-STR-021"],
                expected_payment_ids=["PAY-STR-CH_STR_021a", "PAY-STR-CH_STR_021b"],
                expected_balance_transaction_ids=["txn_str_021a", "txn_str_021b"],
                expected_payout_id="po_str_021",
                expected_bank_transaction_id="BANK-STR-021",
                gross_amount_cents=100000,
                fee_amount_cents=s21a["fee"] + s21b["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s21a["net"] + s21b["net"],
                expected_ar_effect_cents=-100000,
                expected_cash_effect_cents=s21a["net"] + s21b["net"],
                expected_gl_entries=[gl("cash_receipt", 100000)],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["INV-STR-021", "ch_str_021a", "ch_str_021b", "po_str_021"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="Harbor invoice $1,000 paid as two Stripe charges ($400 then $600) in one payout.",
                expected_behavior="Apply both gross payments to INV-STR-021; bank cash is net of both fees.",
            ),
        ),
        Scenario(
            scenario_id="stripe_payout_before_bank",
            title="Payout event arrives before the bank deposit",
            difficulty="easy",
            events=payment_events(s1, t_sep3) + payout_events("po_str_001", t_sep4),
            ground_truth=gt(
                scenario_id="stripe_payout_before_bank",
                expected_classification="timing",
                expected_workflow="stripe_payout_reconciliation",
                expected_customer_invoice_ids=["INV-STR-001"],
                expected_payment_ids=["PAY-STR-CH_STR_001"],
                expected_balance_transaction_ids=["txn_str_001"],
                expected_payout_id="po_str_001",
                expected_bank_transaction_id="BANK-STR-001",
                gross_amount_cents=100000,
                fee_amount_cents=s1["fee"],
                refund_amount_cents=0,
                dispute_amount_cents=0,
                expected_net_cents=s1["net"],
                expected_ar_effect_cents=-100000,
                expected_cash_effect_cents=s1["net"],
                expected_gl_entries=[gl("cash_receipt", 100000), gl("processor_fee", s1["fee"])],
                expected_reconciliation_status="MATCH",
                expected_close_effect="CLEAR",
                expected_exception_code=None,
                expected_audit_finding=None,
                expected_context_links=["po_str_001", "BANK-STR-001", "INV-STR-001"],
                expected_cash_decision="AUTO_APPLY",
                input_condition="Stripe payout webhook is processed before the company bank deposit is loaded.",
                expected_behavior="Payout composition is known first; bank later matches 97070 cents.",
            ),
        ),
    ]

    all_events = []
    for scenario in scenarios:
        all_events.extend(scenario.events)

    return CompanyPack(
        company=COMPANY,
        period=PERIOD,
        customers=customers,
        invoices=invoices,
        precedents=precedents,
        stripe_customers=stripe_customers,
        payment_intents=pis,
        charges=charges,
        refunds=refunds,
        disputes=disputes,
        balance_transactions=txns,
        payouts=payouts,
        bank_deposits=deposits,
        events=all_events,
        scenarios=scenarios,
    )


def scenario_by_id(scenario_id: str, pack: CompanyPack | None = None) -> Scenario:
    pack = pack or build_company_pack()
    for item in pack.scenarios:
        if item.scenario_id == scenario_id:
            return item
    raise KeyError(scenario_id)

"""Cash + reconciliation sample-data agent. Consumes AP/AR events; does not replace them."""

from __future__ import annotations

from datetime import datetime, timezone

from cash_recon.models import FeeEvidence
from integrations.models import PayoutLine, ProviderPayout

from sample_data.adapters import cash_bank, cash_ledger, payout_to_bank, payout_to_ledger
from sample_data.agents.base import SampleDataAgent
from sample_data.context import CompanyScenarioContext, cents, dollars
from sample_data.models import JournalEntryRecord, ScenarioPlan, VendorPayment


def _fee(evidence_id: str, date: str, amount_minor: int, reference: str, description: str) -> FeeEvidence:
    return FeeEvidence(
        evidence_id=evidence_id,
        date=date,
        amount=dollars(amount_minor),
        fee_type="bank_fee",
        reference=reference,
        description=description,
        source="bank_advice",
        amount_minor=amount_minor,
    )


def _unix(day: str) -> int:
    return int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())


class CashReconSampleDataAgent(SampleDataAgent):
    name = "Cash Recon Sample Data Agent"
    domain = "cash_recon"

    TEMPLATES = [
        "SCN-CASH-001",
        "SCN-CASH-002",
        "SCN-CASH-003",
        "SCN-CASH-004",
        "SCN-CASH-005",
        "SCN-CASH-006",
        "SCN-CASH-007",
        "SCN-CASH-008",
        "SCN-CASH-009",
        "SCN-CASH-010",
        "SCN-CASH-011",
        "SCN-CASH-012",
    ]

    def plan(self, ctx: CompanyScenarioContext) -> ScenarioPlan:
        return ScenarioPlan(
            agent=self.name,
            selected_templates=list(self.TEMPLATES),
            narrative=(
                "September bank activity is built from the AP disbursements and AR "
                "receipts already on the books, plus three Stripe payouts."
            ),
        )

    def apply(self, ctx: CompanyScenarioContext, plan: ScenarioPlan) -> None:
        self._vendor_payments(ctx)
        self._ar_bank(ctx)
        self._exceptions(ctx)
        self._stripe(ctx)
        self._cash_journals(ctx)

    def _put_bank(self, ctx: CompanyScenarioContext, txn) -> None:
        ctx.bank_transactions[txn.transaction_id] = txn
        ctx.ids.named(txn.transaction_id)

    def _put_ledger(self, ctx: CompanyScenarioContext, entry) -> None:
        ctx.ledger_cash[entry.entry_id] = entry
        ctx.ids.named(entry.entry_id)

    def _vendor_payments(self, ctx: CompanyScenarioContext) -> None:
        # A. Exact 1:1 Acme INV-001.
        pay = VendorPayment(
            payment_id="PAY-AP-001",
            invoice_ids=["INV-001"],
            vendor="Acme Supplies",
            vendor_id="VEND-001",
            payment_date="2026-09-18",
            amount_minor=1_245_000,
            method="ach",
            bank_reference="8391",
            description="Vendor payment INV-001",
        )
        ctx.vendor_payments[pay.payment_id] = pay
        ctx.ids.named(pay.payment_id)
        self._put_bank(
            ctx,
            cash_bank(
                "TXN-2026-09-018A",
                "2026-09-18",
                -1_245_000,
                description="ACH OUT ACME SUPPLIES 8391",
                reference="8391",
                counterparty="ACME SUPPLIES",
                transaction_type="ach_debit",
                metadata={"payment_id": pay.payment_id, "invoice_ids": pay.invoice_ids},
            ),
        )
        self._put_ledger(
            ctx,
            cash_ledger(
                "GL-AP-INV-001",
                "2026-09-18",
                -1_245_000,
                counterparty="Acme Supplies",
                reference="INV-001",
                description="Vendor payment INV-001",
                entry_type="ap_payment",
                metadata={"payment_id": pay.payment_id},
            ),
        )
        ctx.recon_labels["TXN-2026-09-018A"] = {
            "match_type": "EXACT_MATCH",
            "disposition": "MATCHED",
            "ledger_ids": ["GL-AP-INV-001"],
        }
        ctx.plant("SCN-CASH-001", ["TXN-2026-09-018A", "GL-AP-INV-001", "PAY-AP-001", "INV-001"], storyline="STORY-CLEAN")

        # B. Grouped ACH covering INV-014/015/016.
        grouped_minor = 500_000 + 750_000 + 600_000
        pay_g = VendorPayment(
            payment_id="PAY-AP-NORTHLINE",
            invoice_ids=["INV-014", "INV-015", "INV-016"],
            vendor="Northline Fabrication",
            vendor_id="VEND-003",
            payment_date="2026-09-08",
            amount_minor=grouped_minor,
            method="ach",
            description="Grouped Northline disbursement",
        )
        ctx.vendor_payments[pay_g.payment_id] = pay_g
        ctx.ids.named(pay_g.payment_id)
        self._put_bank(
            ctx,
            cash_bank(
                "TXN-2026-09-008",
                "2026-09-08",
                -grouped_minor,
                description="ACH OUT NORTHLINE FAB",
                counterparty="NORTHLINE FAB",
                transaction_type="ach_debit",
                metadata={"payment_id": pay_g.payment_id, "invoice_ids": pay_g.invoice_ids},
            ),
        )
        for inv_id, entry_id, amount, day in [
            ("INV-014", "GL-AP-201", -500_000, "2026-09-07"),
            ("INV-015", "GL-AP-202", -750_000, "2026-09-07"),
            ("INV-016", "GL-AP-203", -600_000, "2026-09-08"),
        ]:
            self._put_ledger(
                ctx,
                cash_ledger(
                    entry_id,
                    day,
                    amount,
                    counterparty="Northline Fabrication",
                    reference=inv_id,
                    description=f"Vendor payment {inv_id}",
                    entry_type="ap_payment",
                    metadata={"payment_id": pay_g.payment_id, "invoice_id": inv_id},
                ),
            )
        ctx.recon_labels["TXN-2026-09-008"] = {
            "match_type": "GROUPED_MATCH",
            "disposition": "MATCHED",
            "ledger_ids": ["GL-AP-201", "GL-AP-202", "GL-AP-203"],
        }
        ctx.plant("SCN-CASH-002", ["TXN-2026-09-008", "GL-AP-201", "GL-AP-202", "GL-AP-203", "INV-014", "INV-015", "INV-016"])

        # C. Wire net of $25 bank fee (Helios INV-017).
        pay_w = VendorPayment(
            payment_id="PAY-AP-017",
            invoice_ids=["INV-017"],
            vendor="Helios Hardware",
            vendor_id="VEND-005",
            payment_date="2026-09-11",
            amount_minor=1_000_000,
            method="wire",
            bank_reference="729103",
            description="International vendor wire",
        )
        ctx.vendor_payments[pay_w.payment_id] = pay_w
        ctx.ids.named(pay_w.payment_id)
        self._put_bank(
            ctx,
            cash_bank(
                "TXN-2026-09-011",
                "2026-09-11",
                -1_002_500,
                description="WIRE TRANSFER INTL REF 729103",
                reference="729103",
                counterparty="HELIOS HARDWARE",
                transaction_type="wire_debit",
                metadata={"payment_id": pay_w.payment_id},
            ),
        )
        self._put_ledger(
            ctx,
            cash_ledger(
                "GL-AP-WIRE",
                "2026-09-11",
                -1_000_000,
                counterparty="Helios Hardware",
                reference="WIRE-729103",
                description="International vendor wire",
                entry_type="ap_payment",
                metadata={"payment_id": pay_w.payment_id},
            ),
        )
        ctx.fee_evidence["FEE-729103"] = _fee("FEE-729103", "2026-09-11", 2500, "729103", "Outgoing wire fee")
        ctx.ids.named("FEE-729103")
        ctx.recon_labels["TXN-2026-09-011"] = {
            "match_type": "FEE_NETTED",
            "disposition": "EXPLAINED_EXCEPTION",
            "ledger_ids": ["GL-AP-WIRE"],
        }
        ctx.plant("SCN-CASH-003", ["TXN-2026-09-011", "GL-AP-WIRE", "FEE-729103", "INV-017"], storyline="STORY-RESOLVED")

        # Paid-while-on-hold (INV-010) — planted for audit, still a real bank/ledger pair.
        hold = VendorPayment(
            payment_id="PAY-AP-010",
            invoice_ids=["INV-010"],
            vendor="Office Depot",
            vendor_id="VEND-004",
            payment_date="2026-09-20",
            amount_minor=328_000,
            method="ach",
            description="Released while invoice on hold",
            on_hold_invoice=True,
            initiator_id="USR-PAY-01",
            approver_id="USR-PAY-01",
        )
        ctx.vendor_payments[hold.payment_id] = hold
        ctx.ids.named(hold.payment_id)
        self._put_bank(
            ctx,
            cash_bank(
                "TXN-2026-09-020H",
                "2026-09-20",
                -328_000,
                description="ACH OUT OFFICE DEPOT HOLD",
                counterparty="OFFICE DEPOT",
                transaction_type="ach_debit",
                metadata={"payment_id": hold.payment_id, "on_hold": True},
            ),
        )
        self._put_ledger(
            ctx,
            cash_ledger(
                "GL-AP-HOLD",
                "2026-09-20",
                -328_000,
                counterparty="Office Depot",
                reference="INV-010",
                description="Vendor payment INV-010",
                entry_type="ap_payment",
                metadata={"payment_id": hold.payment_id},
            ),
        )

        # Round-number $50,000 phantom payment.
        rnd = VendorPayment(
            payment_id="PAY-AP-009",
            invoice_ids=["INV-009"],
            vendor="Northwind Phantom LLC",
            vendor_id="VEND-010",
            payment_date="2026-09-20",
            amount_minor=5_000_000,
            method="wire",
            description="Manual wire to a new vendor",
            round_number=True,
            initiator_id="USR-PAY-01",
            approver_id="USR-PAY-01",
        )
        ctx.vendor_payments[rnd.payment_id] = rnd
        ctx.ids.named(rnd.payment_id)
        self._put_bank(
            ctx,
            cash_bank(
                "TXN-2026-09-020R",
                "2026-09-20",
                -5_000_000,
                description="WIRE OUT NORTHWIND PHANTOM",
                counterparty="NORTHWIND PHANTOM LLC",
                transaction_type="wire_debit",
                metadata={"payment_id": rnd.payment_id},
            ),
        )
        self._put_ledger(
            ctx,
            cash_ledger(
                "GL-AP-ROUND",
                "2026-09-20",
                -5_000_000,
                counterparty="Northwind Phantom LLC",
                reference="INV-009",
                description="Vendor payment INV-009",
                entry_type="ap_payment",
                metadata={"payment_id": rnd.payment_id},
            ),
        )

        # Early AP payment of INV-012 (forecast miss).
        early = VendorPayment(
            payment_id="PAY-AP-012",
            invoice_ids=["INV-012"],
            vendor="GitHub",
            vendor_id="VEND-017",
            payment_date="2026-09-23",
            amount_minor=2_100_000,
            method="ach",
            description="Paid earlier than the deferred forecast week",
        )
        ctx.vendor_payments[early.payment_id] = early
        ctx.ids.named(early.payment_id)
        self._put_bank(
            ctx,
            cash_bank(
                "BNK-AP-012",
                "2026-09-23",
                -2_100_000,
                description="ACH OUT GITHUB",
                counterparty="GITHUB",
                transaction_type="ach_debit",
                metadata={"payment_id": early.payment_id},
            ),
        )
        self._put_ledger(
            ctx,
            cash_ledger(
                "JE-PAY-INV-012",
                "2026-09-23",
                -2_100_000,
                counterparty="GitHub",
                reference="INV-012",
                description="Vendor payment INV-012",
                entry_type="ap_payment",
                metadata={"payment_id": early.payment_id},
            ),
        )

    def _ar_bank(self, ctx: CompanyScenarioContext) -> None:
        # Exact Northwind receipt.
        self._put_bank(
            ctx,
            cash_bank(
                "TXN-AR-PAY-001",
                "2026-09-29",
                1_200_000,
                description="WIRE IN NORTHWIND LABS INV AR 007",
                reference="WIRE-NW-9921",
                counterparty="NORTHWIND LABS",
                transaction_type="wire_credit",
                metadata={"payment_id": "PAY-001", "invoice_ids": ["INV-AR-007"]},
            ),
        )
        self._put_ledger(
            ctx,
            cash_ledger(
                "GL-AR-PAY-001",
                "2026-09-29",
                1_200_000,
                counterparty="Northwind Labs",
                reference="INV-AR-007",
                description="Customer receipt PAY-001",
                entry_type="ar_receipt",
                metadata={"payment_id": "PAY-001"},
            ),
        )
        ctx.recon_labels["TXN-AR-PAY-001"] = {
            "match_type": "EXACT_MATCH",
            "disposition": "MATCHED",
            "ledger_ids": ["GL-AR-PAY-001"],
        }

        # E. Unexplained $12.40 — bank 12412.40 vs ledger 12400.00.
        self._put_bank(
            ctx,
            cash_bank(
                "TXN-2026-09-015",
                "2026-09-15",
                1_241_240,
                description="CUSTOMER PAYMENT NORTHSTAR LLC",
                counterparty="NORTHSTAR LLC",
                transaction_type="wire_credit",
                metadata={"payment_id": "PAY-006", "invoice_ids": ["INV-AR-013"]},
            ),
        )
        self._put_ledger(
            ctx,
            cash_ledger(
                "GL-AR-NS",
                "2026-09-15",
                1_240_000,
                counterparty="Northstar LLC",
                reference="INV-AR-013",
                description="Customer receipt Northstar platform",
                entry_type="ar_receipt",
                metadata={"payment_id": "PAY-006"},
            ),
        )
        ctx.recon_labels["TXN-2026-09-015"] = {
            "match_type": "UNEXPLAINED_DIFFERENCE",
            "disposition": "HUMAN_REVIEW",
            "ledger_ids": ["GL-AR-NS"],
            "difference": 12.4,
        }
        ctx.plant("SCN-CASH-005", ["TXN-2026-09-015", "GL-AR-NS", "PAY-006", "INV-AR-013"], storyline="STORY-UNRESOLVED")

        # Atlas batch receipt.
        self._put_bank(
            ctx,
            cash_bank(
                "TXN-2026-09-028",
                "2026-09-28",
                3_740_000,
                description="WIRE IN ATLAS ROBOTICS",
                reference="WIRE-ATL-374",
                counterparty="ATLAS ROBOTICS",
                transaction_type="wire_credit",
                metadata={"payment_id": "PAY-003"},
            ),
        )
        self._put_ledger(
            ctx,
            cash_ledger(
                "GL-AR-ATLAS",
                "2026-09-28",
                3_740_000,
                counterparty="Atlas Robotics",
                reference="PAY-003",
                description="Customer batch receipt",
                entry_type="ar_receipt",
                metadata={"payment_id": "PAY-003"},
            ),
        )

    def _exceptions(self, ctx: CompanyScenarioContext) -> None:
        # D. Duplicate refund: two bank postings, one ledger.
        self._put_bank(
            ctx,
            cash_bank(
                "TXN-2026-09-012A",
                "2026-09-12",
                -25_000,
                description="REFUND CARD 8892",
                reference="8892",
                counterparty="LUMEN LABS",
                transaction_type="card_refund",
            ),
        )
        self._put_bank(
            ctx,
            cash_bank(
                "TXN-2026-09-012B",
                "2026-09-12",
                -25_000,
                description="REFUND CARD 8892",
                reference="8892",
                counterparty="LUMEN LABS",
                transaction_type="card_refund",
            ),
        )
        self._put_ledger(
            ctx,
            cash_ledger(
                "GL-AR-772",
                "2026-09-12",
                -25_000,
                counterparty="Lumen Labs",
                reference="8892",
                description="Customer refund",
                entry_type="ar_refund",
            ),
        )
        ctx.recon_labels["TXN-2026-09-012A"] = {"match_type": "EXACT_MATCH", "disposition": "MATCHED", "ledger_ids": ["GL-AR-772"]}
        ctx.recon_labels["TXN-2026-09-012B"] = {"match_type": "POSSIBLE_DUPLICATE_REFUND", "disposition": "HUMAN_REVIEW", "ledger_ids": []}
        ctx.plant("SCN-CASH-004", ["TXN-2026-09-012A", "TXN-2026-09-012B", "GL-AR-772"])

        # F. Timing difference: ledger in September, bank October 1.
        self._put_ledger(
            ctx,
            cash_ledger(
                "GL-AP-HE",
                "2026-09-30",
                -210_000,
                counterparty="Office Depot",
                reference="INV-013",
                description="Vendor payment INV-013 booked at month-end",
                entry_type="ap_payment",
            ),
        )
        self._put_bank(
            ctx,
            cash_bank(
                "TXN-2026-10-001",
                "2026-10-01",
                -210_000,
                description="ACH OUT OFFICE DEPOT DISC",
                counterparty="OFFICE DEPOT",
                transaction_type="ach_debit",
            ),
        )
        ctx.recon_labels["GL-AP-HE"] = {
            "match_type": "TIMING_DIFFERENCE",
            "disposition": "OUTSTANDING_TIMING_ITEM",
            "bank_ids": ["TXN-2026-10-001"],
        }
        ctx.plant("SCN-CASH-006", ["GL-AP-HE", "TXN-2026-10-001"])

        # G. Bank with no ledger.
        self._put_bank(
            ctx,
            cash_bank(
                "TXN-2026-09-025",
                "2026-09-25",
                -18_000,
                description="ACH OUT UNKNOWN COUNTERPARTY",
                counterparty="",
                transaction_type="ach_debit",
            ),
        )
        ctx.recon_labels["TXN-2026-09-025"] = {"match_type": "UNMATCHED_BANK", "disposition": "HUMAN_REVIEW", "ledger_ids": []}
        ctx.plant("SCN-CASH-007", ["TXN-2026-09-025"])

        # H. Ledger with no bank.
        self._put_ledger(
            ctx,
            cash_ledger(
                "GL-AP-ORPHAN",
                "2026-09-27",
                -88_000,
                counterparty="Figma",
                reference="INV-005",
                description="Books-only cash entry awaiting bank",
                entry_type="ap_payment",
            ),
        )
        ctx.recon_labels["GL-AP-ORPHAN"] = {"match_type": "UNMATCHED_LEDGER", "disposition": "HUMAN_REVIEW", "bank_ids": []}
        ctx.plant("SCN-CASH-008", ["GL-AP-ORPHAN"])

        # L. Multiple plausible candidates: one bank, two same-amount ledgers.
        self._put_bank(
            ctx,
            cash_bank(
                "TXN-2026-09-021",
                "2026-09-21",
                -300_000,
                description="ACH OUT CAMBRIDGE OFFICE",
                counterparty="CAMBRIDGE OFFICE",
                transaction_type="ach_debit",
            ),
        )
        self._put_ledger(
            ctx,
            cash_ledger(
                "GL-AMB-1",
                "2026-09-21",
                -300_000,
                counterparty="Cambridge Properties",
                reference="RENT-SEP",
                description="September rent",
                entry_type="ap_payment",
            ),
        )
        self._put_ledger(
            ctx,
            cash_ledger(
                "GL-AMB-2",
                "2026-09-20",
                -300_000,
                counterparty="Cambridge Office Services",
                reference="CAM-SVC",
                description="Facilities draw",
                entry_type="ap_payment",
            ),
        )
        ctx.plant("SCN-CASH-012", ["TXN-2026-09-021", "GL-AMB-1", "GL-AMB-2"])

        # Unexpected bank fee (forecast miss).
        self._put_bank(
            ctx,
            cash_bank(
                "BNK-UNX-001",
                "2026-09-24",
                -80_000,
                description="MONTHLY ACCOUNT ANALYSIS FEE",
                counterparty="FIRST NATIONAL",
                transaction_type="bank_fee",
            ),
        )

        # Quiet Harbor late collection (actual in October).
        self._put_bank(
            ctx,
            cash_bank(
                "BNK-AR-FC-001",
                "2026-10-09",
                2_500_000,
                description="WIRE IN QUIET HARBOR",
                counterparty="QUIET HARBOR",
                transaction_type="wire_credit",
                metadata={"invoice_ids": ["INV-AR-014"]},
            ),
        )

    def _stripe(self, ctx: CompanyScenarioContext) -> None:
        payouts = [
            self._payout(
                "po_1MaximorFees",
                "2026-09-19",
                [
                    ("charge", 800_000, "ORD-2101"),
                    ("charge", 500_000, "ORD-2102"),
                    ("stripe_fee", -39_000, "fee-fees"),
                ],
            ),
            self._payout(
                "po_1MaximorRefunds",
                "2026-09-22",
                [
                    ("charge", 400_000, "ORD-2201"),
                    ("refund", -50_000, "re_2201"),
                    ("stripe_fee", -12_000, "fee-ref"),
                ],
            ),
            self._payout(
                "po_1MaximorDisputes",
                "2026-09-26",
                [
                    ("charge", 600_000, "ORD-2301"),
                    ("dispute", -75_000, "dp_2301"),
                    ("stripe_fee", -18_000, "fee-dp"),
                ],
            ),
        ]
        bank_ids = ["TXN-2026-09-019A", "TXN-2026-09-022S", "TXN-2026-09-026S"]
        ledger_ids = ["GL-CASH-STRIPE-FEES", "GL-CASH-STRIPE-REF", "GL-CASH-STRIPE-DP"]
        scenarios = ["SCN-CASH-009", "SCN-CASH-010", "SCN-CASH-011"]
        for payout, bank_id, ledger_id, scenario in zip(payouts, bank_ids, ledger_ids, scenarios):
            ctx.stripe_payouts.append(payout)
            arrival = payout.arrival_date or "2026-09-19"
            self._put_bank(ctx, payout_to_bank(payout, bank_id, arrival))
            self._put_ledger(ctx, payout_to_ledger(payout, ledger_id, arrival))
            ctx.stripe_deposits.append(
                {
                    "deposit_id": f"BANK-{payout.payout_id}",
                    "payout_id": payout.payout_id,
                    "amount": dollars(int(payout.amount)),
                    "currency": "USD",
                    "description": "STRIPE PAYOUT",
                    "posted_on": arrival,
                }
            )
            ctx.recon_labels[bank_id] = {
                "match_type": "PROVIDER_PAYOUT",
                "disposition": "MATCHED",
                "ledger_ids": [ledger_id],
                "provider": "stripe",
            }
            ctx.plant(scenario, [payout.payout_id, bank_id, ledger_id])
            self._stripe_events(ctx, payout, arrival)

    def _payout(self, payout_id: str, arrival: str, rows: list[tuple[str, int, str]]) -> ProviderPayout:
        lines = []
        net = 0
        for line_type, minor, ref in rows:
            net += minor
            lines.append(
                PayoutLine(
                    line_type=line_type,
                    amount=dollars(minor),
                    currency="USD",
                    reference=ref,
                    description=ref,
                    provider_object_id=ref,
                    amount_minor=minor,
                )
            )
        created = _unix(arrival)
        return ProviderPayout(
            provider="stripe",
            event_id=f"evt_{payout_id}",
            payout_id=payout_id,
            status="paid",
            amount=net,
            currency="usd",
            arrival_date=arrival,
            provider_created_at=arrival,
            source_event_type="payout.reconciliation_completed",
            raw_source_ref=f"demo:{payout_id}",
            reference=payout_id,
            lines=lines,
            bank_deposit_id=f"BANK-{payout_id}",
            bank_deposit_amount=dollars(net),
            bank_deposit_currency="USD",
        )

    def _stripe_events(self, ctx: CompanyScenarioContext, payout: ProviderPayout, arrival: str) -> None:
        created = _unix(arrival)
        obj = {
            "id": payout.payout_id,
            "object": "payout",
            "amount": int(payout.amount),
            "currency": "usd",
            "arrival_date": created,
            "status": "paid",
            "created": created,
            "method": "standard",
            "type": "bank_account",
            "statement_descriptor": "STRIPE PAYOUT",
        }
        ctx.stripe_events.append(
            {
                "id": f"evt_{payout.payout_id}_created",
                "object": "event",
                "type": "payout.created",
                "created": created,
                "livemode": False,
                "data": {"object": dict(obj, status="in_transit")},
            }
        )
        ctx.stripe_events.append(
            {
                "id": f"evt_{payout.payout_id}_recon",
                "object": "event",
                "type": "payout.reconciliation_completed",
                "created": created,
                "livemode": False,
                "data": {"object": obj},
            }
        )
        for line in payout.lines:
            ctx.stripe_balance_txns.append(
                {
                    "id": f"txn_{line.provider_object_id}",
                    "object": "balance_transaction",
                    "amount": int(line.amount_minor or 0),
                    "currency": "usd",
                    "type": line.line_type,
                    "description": line.description,
                    "payout": payout.payout_id,
                    "source": {"id": line.provider_object_id, "object": line.line_type},
                }
            )

    def _cash_journals(self, ctx: CompanyScenarioContext) -> None:
        for payment in ctx.vendor_payments.values():
            entry_id = f"JE-CASH-{payment.payment_id}"
            if entry_id in ctx.journal_entries:
                continue
            ctx.add_journal(
                JournalEntryRecord(
                    entry_id=entry_id,
                    period="2026-09",
                    effective_date=payment.payment_date,
                    posting_date=payment.payment_date,
                    posting_timestamp=f"{payment.payment_date}T16:00:00Z",
                    debit_account="2000-AP",
                    credit_account="1000-Cash",
                    amount_minor=payment.amount_minor,
                    memo=payment.description,
                    vendor=payment.vendor,
                    source_document_id=payment.invoice_ids[0],
                    transaction_id=payment.payment_id,
                    entry_type="ap_payment",
                    related_ids=list(payment.invoice_ids),
                    evidence_refs=[f"payment:{payment.payment_id}"],
                )
            )
        ctx.add_journal(
            JournalEntryRecord(
                entry_id="JE-CASH-PAY-001",
                period="2026-09",
                effective_date="2026-09-29",
                posting_date="2026-09-29",
                posting_timestamp="2026-09-29T16:00:00Z",
                debit_account="1000-Cash",
                credit_account="1100-AR",
                amount_minor=1_200_000,
                memo="Northwind receipt",
                customer="Northwind Labs",
                source_document_id="INV-AR-007",
                transaction_id="PAY-001",
                entry_type="ar_receipt",
                related_ids=["PAY-001", "INV-AR-007"],
                evidence_refs=["payment:PAY-001"],
            )
        )

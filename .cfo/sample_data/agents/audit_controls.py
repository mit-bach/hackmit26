"""Audit + controls sample-data agent. Samples existing populations; plants control cases."""

from __future__ import annotations

from audit.models import (
    AccountingPeriod,
    AuditApproval,
    OperationalDecision,
    PlantedReconciliation,
)

from sample_data.adapters import invoice_to_audit, journal_to_audit, vendor_payment_to_audit, vendor_to_audit
from sample_data.agents.base import SampleDataAgent
from sample_data.context import CompanyScenarioContext
from sample_data.models import ExpectedFinding, ExpectedResults, JournalEntryRecord, ScenarioPlan


class AuditControlsSampleDataAgent(SampleDataAgent):
    name = "Audit Controls Sample Data Agent"
    domain = "audit_controls"

    TEMPLATES = [
        "SCN-AUDIT-001",
        "SCN-AUDIT-002",
        "SCN-AUDIT-003",
        "SCN-AUDIT-004",
        "SCN-AUDIT-005",
        "SCN-AUDIT-006",
        "SCN-AUDIT-007",
        "SCN-AUDIT-008",
        "SCN-AUDIT-009",
        "SCN-AUDIT-010",
        "SCN-AUDIT-011",
        "SCN-AUDIT-012",
        "SCN-AUDIT-013",
    ]

    def plan(self, ctx: CompanyScenarioContext) -> ScenarioPlan:
        return ScenarioPlan(
            agent=self.name,
            selected_templates=list(self.TEMPLATES),
            narrative=(
                "The auditor population is the same AP, payment, journal, and recon "
                "objects already generated. Expected findings stay in the answer key."
            ),
        )

    def apply(self, ctx: CompanyScenarioContext, plan: ScenarioPlan) -> None:
        self._masters(ctx)
        self._invoices(ctx)
        self._payments(ctx)
        self._journals(ctx)
        self._approvals(ctx)
        self._recons(ctx)
        self._decisions(ctx)
        self._post_close(ctx)
        self._expected(ctx)

    def _masters(self, ctx: CompanyScenarioContext) -> None:
        ctx.audit_vendors = [
            vendor_to_audit(row["vendor_id"], row["name"], row["first_seen"], unusual=row.get("unusual", False))
            for row in ctx.vendors.values()
        ]
        ctx.audit_periods = [
            AccountingPeriod(period="2026-08", status="CLOSED", close_timestamp="2026-09-03T18:00:00Z", closed_by="agent:close-orchestrator", close_id="CLOSE-2026-08"),
            AccountingPeriod(period="2026-09", status="CLOSED", close_timestamp="2026-10-03T18:00:00Z", closed_by="agent:close-orchestrator", close_id="CLOSE-2026-09"),
        ]
        ctx.plant("SCN-AUDIT-001", ["VEND-001", "VEND-001-DUP"])

    def _invoices(self, ctx: CompanyScenarioContext) -> None:
        duplicates = {"INV-006", "INV-007"}
        holds = {"INV-003", "INV-004", "INV-005", "INV-006", "INV-007", "INV-008", "INV-009", "INV-010"}
        for invoice in ctx.ap_invoices.values():
            vendor_id = next((vid for vid, row in ctx.vendors.items() if row["name"] == invoice.vendor), "")
            ctx.audit_invoices.append(
                invoice_to_audit(
                    invoice,
                    vendor_id,
                    invoice.invoice_date[:7],
                    decision="HOLD" if invoice.invoice_id in holds else "APPROVE",
                    duplicate=invoice.invoice_id in duplicates,
                )
            )
        ctx.plant("SCN-AUDIT-002", ["INV-006", "INV-007"])
        ctx.plant("SCN-AUDIT-010", ["INV-001", "PO-101", "GR-101"])

    def _payments(self, ctx: CompanyScenarioContext) -> None:
        approval_map = {
            "PAY-AP-001": ["APR-INV-001"],
            "PAY-AP-009": ["APR-PAY-009"],
            "PAY-AP-010": ["APR-PAY-010"],
        }
        for payment in ctx.vendor_payments.values():
            ctx.audit_payments.append(vendor_payment_to_audit(payment, payment.payment_date[:7], approval_map.get(payment.payment_id, [])))
        ctx.plant("SCN-AUDIT-003", ["PAY-AP-009", "INV-009"])
        ctx.plant("SCN-AUDIT-007", ["PAY-AP-010", "INV-010"])
        ctx.plant("SCN-AUDIT-008", ["PAY-AP-009", "PAY-AP-010"])

    def _journals(self, ctx: CompanyScenarioContext) -> None:
        ctx.audit_journals = [journal_to_audit(item) for item in ctx.journal_entries.values()]
        ctx.plant("SCN-AUDIT-011", [next(iter(ctx.journal_entries))])

    def _approvals(self, ctx: CompanyScenarioContext) -> None:
        ctx.audit_approvals = [
            AuditApproval(
                approval_id="APR-INV-001",
                object_type="invoice",
                object_id="INV-001",
                requester_id="USR-PREP-01",
                preparer_id="USR-PREP-01",
                reviewer_id="USR-REV-01",
                approver_id="USR-APPR-01",
                amount=12450.0,
                period=ctx.period,
            ),
            AuditApproval(
                approval_id="APR-INV-SELF",
                object_type="invoice",
                object_id="INV-009",
                requester_id="USR-PREP-02",
                preparer_id="USR-PREP-02",
                reviewer_id="USR-REV-02",
                approver_id="USR-PREP-02",
                amount=50000.0,
                period=ctx.period,
            ),
            AuditApproval(
                approval_id="APR-PAY-009",
                object_type="payment",
                object_id="PAY-AP-009",
                initiator_id="USR-PAY-01",
                approver_id="USR-PAY-01",
                amount=50000.0,
                period=ctx.period,
            ),
            AuditApproval(
                approval_id="APR-PAY-010",
                object_type="payment",
                object_id="PAY-AP-010",
                initiator_id="USR-PAY-01",
                approver_id="USR-PAY-01",
                amount=3280.0,
                period=ctx.period,
            ),
            AuditApproval(
                approval_id="APR-JE-001",
                object_type="journal",
                object_id="JE-AP-INV-001",
                preparer_id="USR-JE-01",
                reviewer_id="USR-REV-04",
                approver_id="USR-JE-02",
                amount=12450.0,
                period=ctx.period,
            ),
        ]
        ctx.ids.named("APR-INV-001")
        ctx.ids.named("APR-INV-SELF")
        ctx.plant("SCN-AUDIT-005", ["APR-INV-SELF", "INV-009"])
        ctx.plant("SCN-AUDIT-006", ["INV-009", "PO-109"])

    def _recons(self, ctx: CompanyScenarioContext) -> None:
        ctx.audit_bank = list(ctx.bank_transactions.values())
        ctx.audit_ledger = list(ctx.ledger_cash.values())
        ctx.audit_fees = list(ctx.fee_evidence.values())
        ctx.planted_recons = [
            PlantedReconciliation(
                reconciliation_id="REC-CLEAN-001",
                period=ctx.period,
                recon_type="cash",
                bank_transaction_ids=["TXN-2026-09-018A"],
                ledger_entry_ids=["GL-AP-INV-001"],
                original_match_type="EXACT_MATCH",
                original_status="MATCHED",
                original_bank_amount=12450.0,
                original_ledger_amount=12450.0,
                original_difference=0.0,
                planted_error=False,
                payment_id="PAY-AP-001",
                invoice_ids=["INV-001"],
            ),
            PlantedReconciliation(
                reconciliation_id="REC-FEE-017",
                period=ctx.period,
                recon_type="cash",
                bank_transaction_ids=["TXN-2026-09-011"],
                ledger_entry_ids=["GL-AP-WIRE"],
                original_match_type="FEE_NETTED",
                original_status="EXPLAINED_EXCEPTION",
                original_bank_amount=-10025.0,
                original_ledger_amount=-10000.0,
                original_difference=-25.0,
                planted_error=False,
                payment_id="PAY-AP-017",
                invoice_ids=["INV-017"],
            ),
            PlantedReconciliation(
                reconciliation_id="REC-NS-1240",
                period=ctx.period,
                recon_type="cash",
                bank_transaction_ids=["TXN-2026-09-015"],
                ledger_entry_ids=["GL-AR-NS"],
                original_match_type="UNEXPLAINED_DIFFERENCE",
                original_status="HUMAN_REVIEW",
                original_bank_amount=12412.4,
                original_ledger_amount=12400.0,
                original_difference=12.4,
                planted_error=True,
                payment_id="PAY-006",
                invoice_ids=["INV-AR-013"],
            ),
        ]
        ctx.plant("SCN-AUDIT-009", ["REC-CLEAN-001", "TXN-2026-09-018A"])
        ctx.plant("SCN-AUDIT-012", ["REC-NS-1240", "TXN-2026-09-015"])
        ctx.plant("SCN-AUDIT-013", [item.invoice_id for item in list(ctx.ap_invoices.values())[:8]])

    def _decisions(self, ctx: CompanyScenarioContext) -> None:
        ctx.operational_decisions = [
            OperationalDecision(object_id="INV-001", object_type="invoice", workflow="ap", decision="APPROVE", duplicate_detected=False, invoice_ids=["INV-001"], amount=12450.0),
            OperationalDecision(object_id="INV-006", object_type="invoice", workflow="ap", decision="HOLD", duplicate_detected=True, invoice_ids=["INV-006", "INV-007"], amount=8750.0),
            OperationalDecision(object_id="INV-007", object_type="invoice", workflow="ap", decision="HOLD", duplicate_detected=True, invoice_ids=["INV-007", "INV-006"], amount=8750.0),
            OperationalDecision(object_id="INV-010", object_type="invoice", workflow="ap", decision="HOLD", invoice_ids=["INV-010"], amount=3280.0),
            OperationalDecision(object_id="VEND-001", object_type="vendor", workflow="ap", decision="ACTIVE", duplicate_detected=False),
            OperationalDecision(
                object_id="REC-NS-1240",
                object_type="reconciliation",
                workflow="cash_recon",
                decision="HUMAN_REVIEW",
                reconciliation_status="HUMAN_REVIEW",
                match_type="UNEXPLAINED_DIFFERENCE",
                bank_transaction_ids=["TXN-2026-09-015"],
                ledger_entry_ids=["GL-AR-NS"],
                amount=12.4,
            ),
        ]

    def _post_close(self, ctx: CompanyScenarioContext) -> None:
        entry = JournalEntryRecord(
            entry_id="JE-POST-CLOSE-001",
            period=ctx.period,
            effective_date=ctx.calendar.period_end,
            posting_date="2026-10-05",
            posting_timestamp="2026-10-05T09:00:00Z",
            debit_account="Consulting Expense",
            credit_account="1000-Cash",
            amount_minor=1_500_000,
            memo="Late adjustment after close",
            vendor="Northwind Phantom LLC",
            source_document_id="PAY-AP-009",
            transaction_id="JE-POST-CLOSE-001",
            entry_type="manual",
            related_ids=["PAY-AP-009"],
            evidence_refs=["payment:PAY-AP-009"],
            poster_id="USR-JE-03",
            approver_id="USR-JE-03",
            authorized=False,
            post_close=True,
        )
        ctx.add_journal(entry)
        ctx.audit_journals.append(journal_to_audit(entry))
        ctx.plant("SCN-AUDIT-004", ["JE-POST-CLOSE-001", "PAY-AP-009"])

    def _expected(self, ctx: CompanyScenarioContext) -> None:
        findings = [
            ExpectedFinding(finding_id="EXP-AUD-DUP-VEND", control_id="AUD-DUP-VEND-001", population_item_id="VEND-001", expected_result="FAIL", expected_reason_code="DUPLICATE_VENDOR", source_ids=["VEND-001", "VEND-001-DUP"]),
            ExpectedFinding(finding_id="EXP-AUD-DUP-INV", control_id="AUD-DUP-INV-001", population_item_id="INV-006", expected_result="FAIL", expected_reason_code="DUPLICATE_INVOICE", source_ids=["INV-006", "INV-007"]),
            ExpectedFinding(finding_id="EXP-AUD-ROUND", control_id="AUD-RND-001", population_item_id="PAY-AP-009", expected_result="FAIL", expected_reason_code="ROUND_NUMBER", source_ids=["PAY-AP-009", "INV-009"]),
            ExpectedFinding(finding_id="EXP-AUD-PCE", control_id="AUD-PCE-001", population_item_id="JE-POST-CLOSE-001", expected_result="FAIL", expected_reason_code="UNAUTHORIZED_POST_CLOSE_ENTRY", source_ids=["JE-POST-CLOSE-001"]),
            ExpectedFinding(finding_id="EXP-AUD-SOD", control_id="AUD-SOD-001", population_item_id="APR-INV-SELF", expected_result="FAIL", expected_reason_code="SELF_APPROVAL", source_ids=["APR-INV-SELF", "INV-009"]),
            ExpectedFinding(finding_id="EXP-AUD-HOLD", control_id="AUD-SOD-001", population_item_id="PAY-AP-010", expected_result="FAIL", expected_reason_code="SELF_APPROVAL", source_ids=["PAY-AP-010", "INV-010"]),
        ]
        ctx.expected = ExpectedResults(
            period=ctx.period,
            seed=ctx.seed,
            ap_exceptions={
                "INV-003": ["partial_receipt"],
                "INV-004": ["material_amount_mismatch"],
                "INV-005": ["goods_not_received"],
                "INV-006": ["duplicate"],
                "INV-007": ["duplicate"],
                "INV-008": ["po_not_approved"],
                "INV-009": ["approval_limit_exceeded"],
                "INV-010": ["goods_not_received"],
            },
            reconciliation_statuses={
                "TXN-2026-09-018A": "MATCHED",
                "TXN-2026-09-008": "MATCHED",
                "TXN-2026-09-011": "EXPLAINED_EXCEPTION",
                "TXN-2026-09-015": "HUMAN_REVIEW",
                "TXN-2026-09-012B": "HUMAN_REVIEW",
            },
            audit_findings=findings,
            close_blockers=["TXN-2026-09-015", "TASK-CASH", "TASK-FINAL"],
            gross_margin_drivers=["TXN-SUP-SEP-001", "TXN-FRT-SEP-001", "TXN-REV-SEP-001", "TXN-HOST-SEP-001"],
            forecast_miss_drivers=["INV-AR-014", "INV-012", "PR-2026-10-02", "po_1MaximorFees", "BNK-UNX-001"],
            storylines=["STORY-CLEAN", "STORY-RESOLVED", "STORY-UNRESOLVED"],
        )

"""Month-end close sample-data agent. Consumes AP, AR, cash, and GL balances."""

from __future__ import annotations

from accrual.models import OpenAccrual
from close.models import CloseTask, IdentityLink
from fixed_assets.models import CapitalCandidate, FixedAsset
from prepaid.models import PrepaidItem
from prepaid.schedule import generate_schedule

from sample_data.agents.base import SampleDataAgent
from sample_data.context import FIXED_GENERATED_AT, CompanyScenarioContext, dollars
from sample_data.models import JournalEntryRecord, ScenarioPlan


class CloseSampleDataAgent(SampleDataAgent):
    name = "Close Sample Data Agent"
    domain = "close"

    TEMPLATES = [
        "SCN-CLOSE-001",
        "SCN-CLOSE-002",
        "SCN-CLOSE-003",
        "SCN-CLOSE-004",
        "SCN-CLOSE-005",
        "SCN-CLOSE-006",
        "SCN-CLOSE-007",
        "SCN-CLOSE-008",
        "SCN-CLOSE-009",
        "SCN-CLOSE-010",
        "SCN-CLOSE-011",
        "SCN-CLOSE-012",
        "SCN-CLOSE-013",
        "SCN-CLOSE-014",
        "SCN-CLOSE-015",
    ]

    def plan(self, ctx: CompanyScenarioContext) -> ScenarioPlan:
        return ScenarioPlan(
            agent=self.name,
            selected_templates=list(self.TEMPLATES),
            narrative=(
                "September close evidence is tied to the same AP, AR, cash, "
                "prepaid, and fixed-asset objects. The $12.40 cash break blocks close."
            ),
        )

    def apply(self, ctx: CompanyScenarioContext, plan: ScenarioPlan) -> None:
        self._accruals(ctx)
        self._prepaids(ctx)
        self._assets(ctx)
        self._documents(ctx)
        self._tasks(ctx)
        self._links(ctx)

    def _accruals(self, ctx: CompanyScenarioContext) -> None:
        utility = OpenAccrual(
            accrual_id="ACC-HE-2026-09",
            vendor="Harbor Electric",
            period=ctx.period,
            estimated_amount=4780.0,
            expense_account="Utilities Expense",
            liability_account="Accrued Expenses",
            status="open",
            estimation_method="recent_average",
            confidence=0.82,
            evidence=["contract:CTR-HE-001", "history:HI-HE-2026-08"],
            reasoning_summary="Utility consumed in September; bill arrives in October.",
            journal_entry_id="JE-ACC-HE-202609",
            created_at=FIXED_GENERATED_AT,
        )
        legal = OpenAccrual(
            accrual_id="ACC-LR-2026-09",
            vendor="Lindholm & Ruiz LLP",
            period=ctx.period,
            estimated_amount=8500.0,
            expense_account="Legal Expense",
            liability_account="Accrued Expenses",
            status="open",
            estimation_method="contract_commitment",
            confidence=0.9,
            evidence=["contract:CTR-LR-001", "history:HI-LR-2026-08"],
            reasoning_summary="Retainer earned in September; invoice not yet received.",
            journal_entry_id="JE-ACC-LR-202609",
            created_at=FIXED_GENERATED_AT,
        )
        ctx.accruals.extend([utility, legal])
        ctx.add_journal(
            JournalEntryRecord(
                entry_id="JE-ACC-HE-202609",
                period=ctx.period,
                effective_date=ctx.calendar.period_end,
                posting_date=ctx.calendar.period_end,
                posting_timestamp=f"{ctx.calendar.period_end}T21:00:00Z",
                debit_account="Utilities Expense",
                credit_account="Accrued Expenses",
                amount_minor=478_000,
                memo="Harbor Electric September accrual",
                vendor="Harbor Electric",
                source_document_id="CTR-HE-001",
                transaction_id="ACC-HE-2026-09",
                entry_type="accrual",
                related_ids=["ACC-HE-2026-09"],
                evidence_refs=["contract:CTR-HE-001", "history:HI-HE-2026-08"],
            )
        )
        ctx.add_journal(
            JournalEntryRecord(
                entry_id="JE-ACC-LR-202609",
                period=ctx.period,
                effective_date=ctx.calendar.period_end,
                posting_date=ctx.calendar.period_end,
                posting_timestamp=f"{ctx.calendar.period_end}T21:05:00Z",
                debit_account="Legal Expense",
                credit_account="Accrued Expenses",
                amount_minor=850_000,
                memo="Legal retainer September accrual",
                vendor="Lindholm & Ruiz LLP",
                source_document_id="CTR-LR-001",
                transaction_id="ACC-LR-2026-09",
                entry_type="accrual",
                related_ids=["ACC-LR-2026-09"],
                evidence_refs=["contract:CTR-LR-001", "history:HI-LR-2026-08"],
            )
        )
        ctx.plant("SCN-CLOSE-001", ["ACC-HE-2026-09", "JE-ACC-HE-202609", "CTR-HE-001"])
        ctx.plant("SCN-CLOSE-002", ["ACC-LR-2026-09", "JE-ACC-LR-202609", "CTR-LR-001"])
        ctx.plant("SCN-CLOSE-010", ["ACC-HE-2026-09", "ACC-LR-2026-09", "JE-ACC-HE-202609", "JE-ACC-LR-202609"])

    def _prepaids(self, ctx: CompanyScenarioContext) -> None:
        software = PrepaidItem(
            prepaid_id="PRE-SFT-001",
            vendor="Orbit Analytics",
            description="Analytics platform subscription covering October through September",
            source_document_id="INV-020",
            total_amount=24000.0,
            start_date="2025-10-01",
            end_date="2026-09-30",
            initial_account="Prepaid Software",
            expense_account="Software Subscription Expense",
            amortization_method="straight_line_monthly",
            status="active",
            created_at="2025-10-01T00:00:00Z",
            evidence_refs=["INV-020", "DOC-SFT-2025"],
            transaction_id="TXN-PRE-SFT-001",
        )
        insurance = PrepaidItem(
            prepaid_id="PRE-INS-001",
            vendor="Hartford Insurance",
            description="Annual commercial property and liability policy",
            source_document_id="INV-019",
            total_amount=12000.0,
            start_date="2026-09-01",
            end_date="2027-08-31",
            initial_account="Prepaid Insurance",
            expense_account="Insurance Expense",
            amortization_method="straight_line_monthly",
            status="active",
            created_at="2026-09-01T00:00:00Z",
            evidence_refs=["INV-019", "DOC-INS-2026"],
            transaction_id="TXN-PRE-INS-001",
        )
        ctx.prepaids.extend([software, insurance])
        for item in ctx.prepaids:
            schedule = generate_schedule(item)
            ctx.prepaid_schedule.extend(schedule)
            for line in schedule:
                if line.period != ctx.period:
                    continue
                entry_id = f"JE-PRE-{item.prepaid_id}-{line.period}"
                ctx.add_journal(
                    JournalEntryRecord(
                        entry_id=entry_id,
                        period=line.period,
                        effective_date=ctx.calendar.period_end,
                        posting_date=ctx.calendar.period_end,
                        posting_timestamp=f"{ctx.calendar.period_end}T22:00:00Z",
                        debit_account=item.expense_account,
                        credit_account=item.initial_account,
                        amount_minor=int(round(line.amount * 100)),
                        memo=f"Amortize {item.prepaid_id}",
                        vendor=item.vendor,
                        source_document_id=item.source_document_id,
                        transaction_id=item.transaction_id,
                        entry_type="prepaid_amortization",
                        related_ids=[item.prepaid_id],
                        evidence_refs=list(item.evidence_refs),
                    )
                )
                line.journal_entry_id = entry_id
                line.status = "posted"
                line.posted_in_period = ctx.period
        ctx.plant("SCN-CLOSE-003", ["PRE-SFT-001", "INV-020"])
        ctx.plant("SCN-CLOSE-004", ["PRE-INS-001", "INV-019"])
        ctx.plant("SCN-CLOSE-009", ["PRE-SFT-001", "PRE-INS-001"])

    def _assets(self, ctx: CompanyScenarioContext) -> None:
        asset = FixedAsset(
            asset_id="FA-DELL-001",
            description="PowerEdge R760 server cluster",
            vendor="Dell Technologies",
            acquisition_date="2026-09-05",
            placed_in_service_date="2026-09-05",
            cost=60000.0,
            salvage_value=6000.0,
            useful_life_months=36,
            asset_account="Computer Equipment",
            accumulated_depreciation_account="Accumulated Depreciation - Equipment",
            depreciation_expense_account="Depreciation Expense",
            evidence_refs=["INV-018", "DOC-DELL-R760"],
            source_document_id="INV-018",
            transaction_id="INV-018",
            created_at="2026-09-05T00:00:00Z",
        )
        ctx.fixed_assets.append(asset)
        monthly = round((60000.0 - 6000.0) / 36, 2)
        ctx.add_journal(
            JournalEntryRecord(
                entry_id="JE-FA-DELL-202609",
                period=ctx.period,
                effective_date=ctx.calendar.period_end,
                posting_date=ctx.calendar.period_end,
                posting_timestamp=f"{ctx.calendar.period_end}T22:30:00Z",
                debit_account="Depreciation Expense",
                credit_account="Accumulated Depreciation - Equipment",
                amount_minor=int(round(monthly * 100)),
                memo="Dell cluster September depreciation",
                vendor="Dell Technologies",
                source_document_id="INV-018",
                transaction_id="FA-DELL-001",
                entry_type="depreciation",
                related_ids=["FA-DELL-001", "INV-018"],
                evidence_refs=["INV-018", "DOC-DELL-R760"],
            )
        )
        ctx.capital_invoices.append(
            CapitalCandidate(
                candidate_id="INV-018",
                vendor="Dell Technologies",
                description="PowerEdge R760 server cluster for production",
                amount=60000.0,
                invoice_date="2026-09-05",
                source_document_id="DOC-DELL-R760",
                transaction_id="INV-018",
                evidence_refs=["DOC-DELL-R760", "INV-018"],
                useful_life_months=36,
                salvage_value=6000.0,
            )
        )
        ctx.plant("SCN-CLOSE-005", ["FA-DELL-001", "INV-018", "JE-FA-DELL-202609"], storyline="STORY-CLEAN")

    def _documents(self, ctx: CompanyScenarioContext) -> None:
        ctx.source_documents = [
            {"document_id": "DOC-INS-2026", "kind": "insurance_policy", "vendor": "Hartford Insurance", "description": "Commercial policy 2026-09-01 through 2027-08-31", "amount": 12000.0, "date": "2026-09-01", "invoice_id": "INV-019"},
            {"document_id": "DOC-SFT-2025", "kind": "software_contract", "vendor": "Orbit Analytics", "description": "Analytics platform Oct 2025 – Sep 2026", "amount": 24000.0, "date": "2025-10-01", "invoice_id": "INV-020"},
            {"document_id": "DOC-DELL-R760", "kind": "vendor_invoice", "vendor": "Dell Technologies", "description": "PowerEdge R760 server cluster", "amount": 60000.0, "date": "2026-09-05", "invoice_id": "INV-018"},
            {"document_id": "DOC-HE-USAGE", "kind": "utility_usage", "vendor": "Harbor Electric", "description": "September kWh statement", "amount": 4780.0, "date": "2026-09-30"},
            {"document_id": "DOC-LR-TIMESHEET", "kind": "legal_timesheet", "vendor": "Lindholm & Ruiz LLP", "description": "September counsel time", "amount": 8500.0, "date": "2026-09-30"},
            {"document_id": "OPEX-AUG", "kind": "operating_expense_batch", "vendor": "Multiple", "description": "August operating expense batch", "amount": 60000.0, "date": "2026-08-31"},
            {"document_id": "OPEX-SEP", "kind": "operating_expense_batch", "vendor": "Multiple", "description": "September operating expense batch", "amount": 60000.0, "date": "2026-09-30"},
        ]

    def _tasks(self, ctx: CompanyScenarioContext) -> None:
        ctx.close_tasks = [
            CloseTask(
                task_id="TASK-AP",
                period=ctx.period,
                category="ap",
                description="Complete AP matching and approved pool",
                owner_role="ap",
                status="COMPLETE",
                evidence_refs=["INV-001", "INV-002"],
                completed_at=FIXED_GENERATED_AT,
            ),
            CloseTask(
                task_id="TASK-AR",
                period=ctx.period,
                category="ar",
                description="Age AR and apply cash",
                owner_role="ar",
                status="COMPLETE",
                evidence_refs=["INV-AR-007", "PAY-001"],
                completed_at=FIXED_GENERATED_AT,
            ),
            CloseTask(
                task_id="TASK-CASH",
                period=ctx.period,
                category="cash",
                description="Reconcile operating bank",
                owner_role="cash",
                status="BLOCKED",
                blocker_reason="Unexplained $12.40 difference on Northstar receipt",
                blocking_items=["TXN-2026-09-015", "GL-AR-NS"],
                evidence_refs=["TXN-2026-09-015", "GL-AR-NS", "INV-AR-013"],
                requires_review=True,
            ),
            CloseTask(
                task_id="TASK-ACCRUAL",
                period=ctx.period,
                category="accrual",
                description="Book missing-bill accruals",
                owner_role="accrual",
                status="COMPLETE",
                evidence_refs=["ACC-HE-2026-09", "ACC-LR-2026-09"],
                completed_at=FIXED_GENERATED_AT,
            ),
            CloseTask(
                task_id="TASK-PREPAID",
                period=ctx.period,
                category="prepaid",
                description="Amortize prepaid contracts",
                owner_role="prepaid",
                status="NEEDS_REVIEW",
                requires_review=True,
                reviewer="prepaid-reviewer",
                review_status="PENDING",
                evidence_refs=["PRE-INS-001", "PRE-SFT-001"],
            ),
            CloseTask(
                task_id="TASK-FA",
                period=ctx.period,
                category="fixed_assets",
                description="Depreciate Dell cluster",
                owner_role="fixed_assets",
                status="COMPLETE",
                evidence_refs=["FA-DELL-001", "INV-018"],
                completed_at=FIXED_GENERATED_AT,
            ),
            CloseTask(
                task_id="TASK-BS",
                period=ctx.period,
                category="bs_recon",
                description="Tie AP, AR, cash, prepaid, and accrual balances",
                owner_role="close",
                status="BLOCKED",
                dependencies=["TASK-CASH"],
                blocker_reason="Cash rec remains unresolved",
                blocking_items=["TASK-CASH"],
                evidence_refs=["INV-001", "INV-AR-007", "TXN-2026-09-015"],
            ),
            CloseTask(
                task_id="TASK-FINAL",
                period=ctx.period,
                category="final_review",
                description="Month-end close review",
                owner_role="close",
                status="BLOCKED",
                dependencies=["TASK-BS"],
                blocker_reason="Material unresolved cash difference prevents close",
                blocking_items=["TXN-2026-09-015"],
            ),
        ]
        ctx.plant("SCN-CLOSE-006", ["TASK-CASH", "TXN-2026-09-015"])
        ctx.plant("SCN-CLOSE-007", ["TASK-AP", "INV-001", "INV-002"])
        ctx.plant("SCN-CLOSE-008", ["TASK-AR", "INV-AR-007", "PAY-001"])
        ctx.plant("SCN-CLOSE-011", ["TASK-CASH", "TASK-BS", "TXN-2026-09-015"], storyline="STORY-UNRESOLVED")
        ctx.plant("SCN-CLOSE-012", ["TASK-PREPAID"])
        ctx.plant("SCN-CLOSE-013", ["TASK-AP", "TASK-AR", "TASK-ACCRUAL", "TASK-FA"])
        ctx.plant("SCN-CLOSE-014", ["TXN-2026-09-018A", "GL-AP-INV-001", "INV-001"], storyline="STORY-CLEAN")
        ctx.plant("SCN-CLOSE-015", ["TXN-2026-09-015", "GL-AR-NS", "TASK-FINAL"], storyline="STORY-UNRESOLVED")

    def _links(self, ctx: CompanyScenarioContext) -> None:
        ctx.identity_links = [
            IdentityLink(
                link_id="LINK-CLEAN-001",
                source_document_id="INV-001",
                transaction_id="PAY-AP-001",
                journal_entry_id="JE-CASH-PAY-AP-001",
                account_id="1000-Cash",
                reconciliation_id="TXN-2026-09-018A",
                close_task_id="TASK-AP",
                extra={"storyline": "STORY-CLEAN", "bank_transaction_id": "TXN-2026-09-018A"},
                created_at=FIXED_GENERATED_AT,
            ),
            IdentityLink(
                link_id="LINK-RESOLVED-017",
                source_document_id="INV-017",
                transaction_id="PAY-AP-017",
                journal_entry_id="JE-CASH-PAY-AP-017",
                account_id="1000-Cash",
                reconciliation_id="TXN-2026-09-011",
                close_task_id="TASK-CASH",
                extra={"storyline": "STORY-RESOLVED", "fee_evidence_id": "FEE-729103"},
                created_at=FIXED_GENERATED_AT,
            ),
            IdentityLink(
                link_id="LINK-UNRESOLVED-013",
                source_document_id="INV-AR-013",
                transaction_id="PAY-006",
                journal_entry_id="JE-AR-INV-AR-013",
                account_id="1100-AR",
                reconciliation_id="TXN-2026-09-015",
                close_task_id="TASK-CASH",
                extra={"storyline": "STORY-UNRESOLVED", "difference": 12.4},
                created_at=FIXED_GENERATED_AT,
            ),
        ]
        ctx.storylines = [
            {
                "storyline_id": "STORY-CLEAN",
                "title": "Acme INV-001 paid and reconciled",
                "kind": "clean",
                "description": "Clean three-way match, approval, ACH, exact cash match, AP/cash close tie, forecast actual, audit sample, reporting trace.",
                "document_id": "INV-001",
                "steps": [
                    "Vendor invoice INV-001 arrives and matches PO-101 / GR-101",
                    "AP approves the invoice",
                    "PAY-AP-001 is scheduled and paid",
                    "Bank TXN-2026-09-018A matches GL-AP-INV-001",
                    "GL reflects the AP settlement",
                    "Month-end cash and AP recs tie on this item",
                    "Forecast replaces the planned outflow with the bank actual",
                    "Auditor samples INV-001 and re-performs three-way match",
                    "Reporting can trace any related variance to INV-001",
                ],
                "source_ids": ["INV-001", "PO-101", "GR-101", "PAY-AP-001", "TXN-2026-09-018A", "GL-AP-INV-001", "JE-CASH-PAY-AP-001"],
            },
            {
                "storyline_id": "STORY-RESOLVED",
                "title": "Helios wire received net of a $25 fee",
                "kind": "resolved_exception",
                "description": "INV-017 is paid by wire. Bank posts $10,025.00; books show $10,000.00. Fee evidence supports FEE_NETTED.",
                "document_id": "INV-017",
                "steps": [
                    "INV-017 is approved and paid",
                    "Bank TXN-2026-09-011 is $25 higher than GL-AP-WIRE",
                    "FEE-729103 supports the difference",
                    "Cash reconciliation classifies FEE_NETTED",
                    "Close accepts the explained exception",
                    "Audit re-performs the fee-netted recon",
                ],
                "source_ids": ["INV-017", "PAY-AP-017", "TXN-2026-09-011", "GL-AP-WIRE", "FEE-729103"],
            },
            {
                "storyline_id": "STORY-UNRESOLVED",
                "title": "Northstar $12.40 unexplained difference",
                "kind": "unresolved_review",
                "description": "PAY-006 / INV-AR-013 books $12,400.00; bank posts $12,412.40. No fee evidence. Close stays blocked.",
                "document_id": "INV-AR-013",
                "steps": [
                    "INV-AR-013 is issued for $12,400.00",
                    "PAY-006 arrives",
                    "Bank TXN-2026-09-015 is $12,412.40",
                    "GL-AR-NS remains $12,400.00",
                    "Cash recon flags UNEXPLAINED_DIFFERENCE",
                    "TASK-CASH and TASK-FINAL stay blocked",
                    "Auditor samples the recon for human review",
                    "Forecast actuals still point at PAY-006 / TXN-2026-09-015",
                ],
                "source_ids": ["INV-AR-013", "PAY-006", "TXN-2026-09-015", "GL-AR-NS", "TASK-CASH"],
            },
        ]
        from sample_data.models import Storyline

        ctx.storylines = [Storyline.model_validate(item) if isinstance(item, dict) else item for item in ctx.storylines]

"""Approved planted-scenario catalog.

Agents may instantiate these templates. They may not invent new numeric
outcomes. Expected machine answers live in ``expected_results.json``.
"""

from __future__ import annotations

from sample_data.models import Domain, ExpectedBehavior, ScenarioRecord, Severity


def _scn(
    scenario_id: str,
    domain: Domain,
    name: str,
    description: str,
    expected_behavior: ExpectedBehavior,
    *,
    severity: Severity = "MEDIUM",
    demo_priority: int = 50,
) -> ScenarioRecord:
    return ScenarioRecord(
        scenario_id=scenario_id,
        domain=domain,
        name=name,
        description=description,
        expected_behavior=expected_behavior,
        severity=severity,
        demo_priority=demo_priority,
    )


SCENARIO_CATALOG: list[ScenarioRecord] = [
    _scn("SCN-AP-001", "ap_ar", "clean_three_way_match", "Invoice equals PO equals goods receipt.", "APPROVE", demo_priority=10),
    _scn("SCN-AP-002", "ap_ar", "quantity_mismatch", "Invoice quantity exceeds quantity received.", "HOLD", severity="HIGH"),
    _scn("SCN-AP-003", "ap_ar", "price_mismatch", "Invoice unit price differs from the PO.", "HOLD", severity="HIGH"),
    _scn("SCN-AP-004", "ap_ar", "missing_goods_receipt", "PO exists but no goods receipt was recorded.", "HOLD", severity="HIGH"),
    _scn("SCN-AP-005", "ap_ar", "duplicate_invoice", "Same vendor invoice number on two AP invoices.", "HOLD", severity="CRITICAL", demo_priority=15),
    _scn("SCN-AP-006", "ap_ar", "requires_approval", "Invoice is tied to a PO that is not yet approved.", "HOLD"),
    _scn("SCN-AP-007", "ap_ar", "exceeds_approval_threshold", "PO authorized amount exceeds the approver limit.", "HOLD", severity="HIGH"),
    _scn("SCN-AP-008", "ap_ar", "invoice_on_hold", "Invoice is blocked (goods not received) and must not pay.", "HOLD", severity="HIGH"),
    _scn("SCN-AP-009", "ap_ar", "eligible_this_week", "Approved invoice due inside the payment horizon.", "APPROVE", demo_priority=20),
    _scn("SCN-AP-010", "ap_ar", "not_yet_due", "Approved invoice due after the payment horizon.", "APPROVE"),
    _scn("SCN-AP-011", "ap_ar", "early_payment_discount", "Open 2/10 discount window on an approved invoice.", "APPROVE"),
    _scn("SCN-AP-012", "ap_ar", "non_invoice_documents", "Inbox also contains quote, statement, receipt, marketing, and PO.", "HOLD", severity="LOW"),
    _scn("SCN-AR-001", "ap_ar", "current_invoice", "Customer invoice not yet due.", "PASS"),
    _scn("SCN-AR-002", "ap_ar", "aging_1_30", "Invoice 1-30 days past due.", "PASS"),
    _scn("SCN-AR-003", "ap_ar", "aging_31_60", "Invoice 31-60 days past due.", "PASS"),
    _scn("SCN-AR-004", "ap_ar", "aging_61_90", "Invoice 61-90 days past due.", "PASS"),
    _scn("SCN-AR-005", "ap_ar", "aging_90_plus", "Invoice 90+ days past due and a collections candidate.", "PASS", demo_priority=25),
    _scn("SCN-AR-006", "ap_ar", "partial_payment", "Customer remitted less than the open balance.", "PASS"),
    _scn("SCN-AR-007", "ap_ar", "exact_payment", "Payment equals one named invoice.", "PASS", demo_priority=20),
    _scn("SCN-AR-008", "ap_ar", "batch_payment", "One payment covers two invoices exactly.", "PASS"),
    _scn("SCN-AR-009", "ap_ar", "ambiguous_remittance", "Two same-amount invoices; remittance does not name one.", "HUMAN_REVIEW", severity="HIGH", demo_priority=15),
    _scn("SCN-AR-010", "ap_ar", "no_remittance", "Payment arrives without useful remittance text.", "HUMAN_REVIEW"),
    _scn("SCN-AR-011", "ap_ar", "similar_amount_candidates", "Customer has multiple open invoices with the same outstanding.", "HUMAN_REVIEW"),
    _scn("SCN-AR-012", "ap_ar", "collections_chase", "Past-due strategic/late customer is a chase candidate.", "PASS"),
    _scn("SCN-CASH-001", "cash_recon", "exact_one_to_one", "Bank ACH equals one AP cash ledger entry.", "MATCHED", demo_priority=10),
    _scn("SCN-CASH-002", "cash_recon", "grouped_ach_three_invoices", "One ACH equals three vendor invoice payments.", "GROUPED_MATCH", demo_priority=12),
    _scn("SCN-CASH-003", "cash_recon", "wire_net_of_fee", "Wire received or sent net of a supported bank fee.", "FEE_NETTED", demo_priority=14),
    _scn("SCN-CASH-004", "cash_recon", "duplicate_refund", "Two identical card-refund bank postings, one ledger.", "HUMAN_REVIEW", severity="HIGH"),
    _scn("SCN-CASH-005", "cash_recon", "unexplained_1240_difference", "Bank exceeds ledger by exactly $12.40.", "UNEXPLAINED_DIFFERENCE", severity="CRITICAL", demo_priority=5),
    _scn("SCN-CASH-006", "cash_recon", "timing_difference", "Ledger in period, matching bank in the next period.", "TIMING_DIFFERENCE"),
    _scn("SCN-CASH-007", "cash_recon", "unmatched_bank", "Bank transaction with no ledger candidate.", "UNMATCHED"),
    _scn("SCN-CASH-008", "cash_recon", "unmatched_ledger", "Ledger cash entry with no bank activity.", "UNMATCHED"),
    _scn("SCN-CASH-009", "cash_recon", "stripe_payout_net_fees", "Stripe payout net of processor fees.", "PROVIDER_PAYOUT"),
    _scn("SCN-CASH-010", "cash_recon", "stripe_payout_with_refunds", "Stripe payout containing refunds.", "PROVIDER_PAYOUT"),
    _scn("SCN-CASH-011", "cash_recon", "stripe_payout_with_disputes", "Stripe payout containing a chargeback.", "PROVIDER_PAYOUT"),
    _scn("SCN-CASH-012", "cash_recon", "multiple_plausible_candidates", "Two ledger entries share an amount near one bank item.", "HUMAN_REVIEW"),
    _scn("SCN-CLOSE-001", "close", "utility_accrual", "Utility incurred; invoice not yet received.", "ACCRUE", demo_priority=20),
    _scn("SCN-CLOSE-002", "close", "legal_accrual", "Legal/professional services accrued from evidence.", "ACCRUE"),
    _scn("SCN-CLOSE-003", "close", "prepaid_software", "Annual software contract amortized monthly.", "AMORTIZE"),
    _scn("SCN-CLOSE-004", "close", "prepaid_insurance", "Prepaid insurance amortized monthly.", "AMORTIZE"),
    _scn("SCN-CLOSE-005", "close", "fixed_asset_depreciation", "Capital purchase with a straight-line schedule.", "DEPRECIATE", demo_priority=18),
    _scn("SCN-CLOSE-006", "close", "bank_recon_evidence", "Operating bank requires reconciliation evidence.", "NEEDS_REVIEW"),
    _scn("SCN-CLOSE-007", "close", "ap_subledger_tie", "AP balance-sheet rec references AP invoices.", "PASS"),
    _scn("SCN-CLOSE-008", "close", "ar_subledger_tie", "AR balance-sheet rec references AR invoices.", "PASS"),
    _scn("SCN-CLOSE-009", "close", "prepaid_tie", "Prepaid remaining balance ties to the schedule.", "PASS"),
    _scn("SCN-CLOSE-010", "close", "accrual_liability_tie", "Accrual liability ties to evidence.", "PASS"),
    _scn("SCN-CLOSE-011", "close", "task_blocked_by_recon", "A close task is blocked by the $12.40 cash break.", "BLOCK_CLOSE", severity="HIGH", demo_priority=8),
    _scn("SCN-CLOSE-012", "close", "task_awaiting_review", "A close task is waiting on reviewer approval.", "NEEDS_REVIEW"),
    _scn("SCN-CLOSE-013", "close", "task_completed", "At least one close task is complete.", "COMPLETE"),
    _scn("SCN-CLOSE-014", "close", "clean_recon_tie", "AP payment recon ties exactly.", "PASS"),
    _scn("SCN-CLOSE-015", "close", "material_unresolved_difference", "Unexplained $12.40 prevents full close.", "BLOCK_CLOSE", severity="CRITICAL", demo_priority=6),
    _scn("SCN-AUDIT-001", "audit_controls", "duplicate_vendor", "Two vendor records share a normalize_vendor key.", "FAIL", severity="HIGH"),
    _scn("SCN-AUDIT-002", "audit_controls", "duplicate_invoice", "Auditor must rediscover the planted AP duplicate.", "FAIL", severity="HIGH"),
    _scn("SCN-AUDIT-003", "audit_controls", "round_number_payment", "Manual $50,000.00 wire to a new vendor.", "FAIL", severity="CRITICAL", demo_priority=16),
    _scn("SCN-AUDIT-004", "audit_controls", "post_close_journal", "Unauthorized journal posted after period close.", "FAIL", severity="HIGH"),
    _scn("SCN-AUDIT-005", "audit_controls", "self_approval", "Requester and approver are the same person.", "FAIL", severity="HIGH", demo_priority=16),
    _scn("SCN-AUDIT-006", "audit_controls", "approval_threshold_violation", "PO exceeds the recorded approval limit.", "FAIL"),
    _scn("SCN-AUDIT-007", "audit_controls", "paid_while_on_hold", "Payment released while the invoice remains on hold.", "FAIL", severity="CRITICAL"),
    _scn("SCN-AUDIT-008", "audit_controls", "missing_evidence", "Payment flagged missing_support.", "FAIL"),
    _scn("SCN-AUDIT-009", "audit_controls", "recon_reperformance_sample", "Cash recon sample for independent re-performance.", "PASS"),
    _scn("SCN-AUDIT-010", "audit_controls", "three_way_reperformance", "Clean three-way match is in the AP sample.", "PASS"),
    _scn("SCN-AUDIT-011", "audit_controls", "journal_sample", "Journal-entry sample from the canonical ledger.", "PASS"),
    _scn("SCN-AUDIT-012", "audit_controls", "bank_recon_sample", "Bank reconciliation sample includes the $12.40 item.", "HUMAN_REVIEW"),
    _scn("SCN-AUDIT-013", "audit_controls", "random_sample", "Deterministic random sample from the transaction population.", "PASS"),
    _scn("SCN-REPORT-001", "reporting_forecasting", "gross_margin_decline", "September GM is about three points below August from source transactions.", "VARIANCE_DRIVER", demo_priority=7),
    _scn("SCN-REPORT-002", "reporting_forecasting", "board_from_gl", "Board pack metrics are summed from reporting ledger lines.", "PASS"),
    _scn("SCN-REPORT-003", "reporting_forecasting", "thirteen_week_forecast", "Forecast contains exactly 13 weeks built from AP/AR/payroll.", "PASS"),
    _scn("SCN-REPORT-004", "reporting_forecasting", "late_customer_payment", "Forecasted AR collection arrives one week late.", "FORECAST_MISS"),
    _scn("SCN-REPORT-005", "reporting_forecasting", "early_ap_payment", "AP payment paid earlier than the forecast week.", "FORECAST_MISS"),
    _scn("SCN-REPORT-006", "reporting_forecasting", "payroll_variance", "Actual payroll differs from the scheduled amount.", "FORECAST_MISS"),
    _scn("SCN-REPORT-007", "reporting_forecasting", "stripe_below_expectation", "Stripe receipts land below the forecast line.", "FORECAST_MISS"),
    _scn("SCN-REPORT-008", "reporting_forecasting", "unexpected_bank_fee", "Unforecast bank fee appears in actuals.", "FORECAST_MISS"),
    _scn("SCN-ING-001", "ingestion", "clean_vendor_invoice", "Well-formed vendor invoice email with extractable fields.", "CLASSIFY", demo_priority=11),
    _scn("SCN-ING-002", "ingestion", "messy_formatting", "OCR-like invoice text that still contains required fields.", "CLASSIFY"),
    _scn("SCN-ING-003", "ingestion", "po_presented_as_invoice", "Purchase order incorrectly presented as an invoice.", "CLASSIFY"),
    _scn("SCN-ING-004", "ingestion", "quote_presented_as_invoice", "Quote incorrectly presented as an invoice.", "CLASSIFY"),
    _scn("SCN-ING-005", "ingestion", "receipt_not_invoice", "Payment receipt / confirmation, not a vendor invoice.", "CLASSIFY"),
    _scn("SCN-ING-006", "ingestion", "statement_not_invoice", "Account statement rather than an invoice.", "CLASSIFY"),
    _scn("SCN-ING-007", "ingestion", "marketing_not_invoice", "Marketing newsletter in the AP inbox.", "CLASSIFY"),
    _scn("SCN-ING-008", "ingestion", "missing_field_inferable", "Invoice missing vendor name that can be inferred from context.", "CLASSIFY"),
    _scn("SCN-ING-009", "ingestion", "missing_field_not_inferable", "Invoice missing amount that cannot safely be inferred.", "CLASSIFY"),
    _scn("SCN-ING-010", "ingestion", "duplicate_copy", "Second copy of a previously ingested invoice.", "CLASSIFY", demo_priority=17),
    _scn("SCN-AP-013", "ap_ar", "prior_precedent_vendor_alias", "Acme Supply Co. alias already approved in August CASE-001.", "APPROVE", demo_priority=13),
    _scn("SCN-AR-013", "ap_ar", "overpayment", "Named invoice remittance exceeds the open balance.", "HUMAN_REVIEW"),
    _scn("SCN-MEM-001", "memory", "august_vendor_exception_precedent", "August vendor-alias approval must be retrievable in September.", "MEMORY", demo_priority=9),
    _scn("SCN-MEM-002", "memory", "aggregated_customer_payments", "Atlas historically sends one wire covering several invoices.", "MEMORY"),
    _scn("SCN-MEM-003", "memory", "stripe_settlement_pattern", "Known Stripe payout = charges - fees - refunds - disputes.", "MEMORY"),
    _scn("SCN-MEM-004", "memory", "recurring_accrual_methodology", "Harbor Electric September accrual reuses the August methodology.", "MEMORY"),
    _scn("SCN-LEARN-001", "memory", "ar_human_correction_precedent", "A persisted human cash-application correction is retrievable for a later similar payment.", "LEARN"),
    _scn("SCN-HAND-001", "handoff", "ap_invoice_through_close", "INV-001 travels AP match -> payment -> bank -> close -> audit.", "HANDOFF", demo_priority=4),
    _scn("SCN-HAND-002", "handoff", "ar_invoice_through_forecast", "INV-AR-007 travels aging -> cash apply -> bank -> forecast -> reporting.", "HANDOFF"),
    _scn("SCN-CFO-001", "orchestration", "run_september_operations", "Broad CFO objective: run September and say whether the month can close.", "ORCHESTRATE", demo_priority=3),
    _scn("SCN-CFO-002", "orchestration", "cash_below_forecast", "Cross-domain query: why September cash missed the forecast.", "ORCHESTRATE", demo_priority=4),
    _scn("SCN-CLOSE-016", "close", "post_close_journal_attempt", "Unauthorized September journal after the period is treated as closed.", "FAIL", severity="HIGH"),
]


CATALOG_BY_ID = {item.scenario_id: item for item in SCENARIO_CATALOG}


def catalog() -> list[ScenarioRecord]:
    return [item.model_copy() for item in SCENARIO_CATALOG]


def required_ids() -> list[str]:
    return [item.scenario_id for item in SCENARIO_CATALOG]

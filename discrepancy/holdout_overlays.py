"""Append held-out operational records. No answer-key fields on these objects."""

from __future__ import annotations

from pathlib import Path

from discrepancy.overlays import _append, _load, _save


def apply_holdout_overlays(root: Path) -> None:
    root = Path(root)
    _append(
        root / "purchase_orders.json",
        [
            {"po_id": "PO-HO-QTY", "vendor": "Kestrel Components", "authorized_amount": 9000.0, "description": "240 sensor housings", "status": "approved", "created_date": "2026-09-04", "approval_limit": 25000.0, "approver": "Elena Voss"},
            {"po_id": "PO-HO-PRICE", "vendor": "Brightlane Optics", "authorized_amount": 14200.0, "description": "Calibration benches", "status": "approved", "created_date": "2026-09-05", "approval_limit": 30000.0, "approver": "Marcus Chen"},
            {"po_id": "PO-HO-NOGR", "vendor": "Redwood Clinics Supply", "authorized_amount": 3360.0, "description": "Sterile kits", "status": "approved", "created_date": "2026-09-06", "approval_limit": 10000.0, "approver": "Priya Nair"},
            {"po_id": "PO-HO-DUP", "vendor": "Brightlane Optics", "authorized_amount": 2780.0, "description": "Lens lot", "status": "approved", "created_date": "2026-09-07", "approval_limit": 10000.0, "approver": "Priya Nair"},
            {"po_id": "PO-HO-NORM", "vendor": "Kestrel Components", "authorized_amount": 1910.0, "description": "Fastener pack", "status": "approved", "created_date": "2026-09-07", "approval_limit": 10000.0, "approver": "Elena Voss"},
            {"po_id": "PO-HO-LIMIT", "vendor": "Vesper Facilities", "authorized_amount": 72000.0, "description": "Q4 site retrofit", "status": "approved", "created_date": "2026-09-08", "approval_limit": 20000.0, "approver": "Jordan Hale"},
            {"po_id": "PO-HO-HELD", "vendor": "Copperfield Logistics", "authorized_amount": 4110.0, "description": "Weekend freight hold", "status": "approved", "created_date": "2026-09-09", "approval_limit": 15000.0, "approver": "Marcus Chen"},
            {"po_id": "PO-HO-FC-MISS", "vendor": "GitHub", "authorized_amount": 6400.0, "description": "Holdout forecast coverage gap", "status": "approved", "created_date": "2026-09-02", "approval_limit": 20000.0, "approver": "Priya Nair"},
            {"po_id": "PO-HO-FC-DUP", "vendor": "GitHub", "authorized_amount": 18800.0, "description": "Holdout forecast duplicate marker", "status": "approved", "created_date": "2026-09-03", "approval_limit": 25000.0, "approver": "Priya Nair"},
        ],
    )
    _append(
        root / "goods_receipts.json",
        [
            {"receipt_id": "GR-HO-QTY", "po_id": "PO-HO-QTY", "received": True, "received_date": "2026-09-11", "amount_received": 8137.5, "quantity_ordered": 240, "quantity_received": 217},
            {"receipt_id": "GR-HO-PRICE", "po_id": "PO-HO-PRICE", "received": True, "received_date": "2026-09-12", "amount_received": 14200.0, "quantity_ordered": 4, "quantity_received": 4},
            {"receipt_id": "GR-HO-DUP", "po_id": "PO-HO-DUP", "received": True, "received_date": "2026-09-12", "amount_received": 2780.0, "quantity_ordered": 2, "quantity_received": 2},
            {"receipt_id": "GR-HO-NORM", "po_id": "PO-HO-NORM", "received": True, "received_date": "2026-09-12", "amount_received": 1910.0, "quantity_ordered": 1, "quantity_received": 1},
            {"receipt_id": "GR-HO-LIMIT", "po_id": "PO-HO-LIMIT", "received": True, "received_date": "2026-09-13", "amount_received": 72000.0, "quantity_ordered": 1, "quantity_received": 1},
        ],
    )
    _append(
        root / "invoices.json",
        [
            {"invoice_id": "INV-HO-QTY", "vendor": "Kestrel Components", "po_id": "PO-HO-QTY", "amount": 9000.0, "invoice_date": "2026-09-12", "due_date": "2026-10-12", "vendor_invoice_number": "KC-HO-240", "description": "240 housings billed"},
            {"invoice_id": "INV-HO-PRICE", "vendor": "Brightlane Optics", "po_id": "PO-HO-PRICE", "amount": 15478.0, "invoice_date": "2026-09-13", "due_date": "2026-10-13", "vendor_invoice_number": "BL-HO-15478", "description": "Benches at revised unit price"},
            {"invoice_id": "INV-HO-NOGR", "vendor": "Redwood Clinics Supply", "po_id": "PO-HO-NOGR", "amount": 3360.0, "invoice_date": "2026-09-14", "due_date": "2026-10-14", "vendor_invoice_number": "RC-HO-3360", "description": "Kits invoiced before receipt"},
            {"invoice_id": "INV-HO-DUP-A", "vendor": "Brightlane Optics", "po_id": "PO-HO-DUP", "amount": 2780.0, "invoice_date": "2026-09-14", "due_date": "2026-10-14", "vendor_invoice_number": "HX-55190", "description": "Lens lot first copy"},
            {"invoice_id": "INV-HO-DUP-B", "vendor": "Brightlane Optics", "po_id": "PO-HO-DUP", "amount": 2780.0, "invoice_date": "2026-09-14", "due_date": "2026-10-14", "vendor_invoice_number": "HX-55190", "description": "Lens lot second copy"},
            {"invoice_id": "INV-HO-NORM-A", "vendor": "Kestrel Components", "po_id": "PO-HO-NORM", "amount": 1910.0, "invoice_date": "2026-09-15", "due_date": "2026-10-15", "vendor_invoice_number": "ABC/23781", "description": "Fasteners slash format"},
            {"invoice_id": "INV-HO-NORM-B", "vendor": "Kestrel Components, Inc.", "po_id": "PO-HO-NORM", "amount": 1910.0, "invoice_date": "2026-09-15", "due_date": "2026-10-15", "vendor_invoice_number": "ABC-23781", "description": "Fasteners hyphen format"},
            {"invoice_id": "INV-HO-LIMIT", "vendor": "Vesper Facilities", "po_id": "PO-HO-LIMIT", "amount": 72000.0, "invoice_date": "2026-09-15", "due_date": "2026-10-15", "vendor_invoice_number": "VF-HO-72K", "description": "Retrofit above approver limit"},
            {"invoice_id": "INV-HO-HELD", "vendor": "Copperfield Logistics", "po_id": "PO-HO-HELD", "amount": 4110.0, "invoice_date": "2026-09-16", "due_date": "2026-10-16", "vendor_invoice_number": "CL-HO-4110", "description": "Freight invoiced with no receipt"},
            {"invoice_id": "INV-HO-FC-MISS", "vendor": "GitHub", "po_id": "PO-HO-FC-MISS", "amount": 6400.0, "invoice_date": "2026-09-04", "due_date": "2026-09-28", "vendor_invoice_number": "GH-HO-MISS", "description": "Approved payable omitted from draft forecast"},
            {"invoice_id": "INV-HO-FC-DUP", "vendor": "GitHub", "po_id": "PO-HO-FC-DUP", "amount": 18800.0, "invoice_date": "2026-09-04", "due_date": "2026-09-29", "vendor_invoice_number": "GH-HO-DUP", "description": "Forecast duplicate-outflow marker"},
        ],
    )
    _append(
        root / "ar_customers.json",
        [
            {"customer_id": "CUST-HO-01", "customer_name": "Meridian Biotech", "payment_behavior": "mixed", "on_time_rate": 0.7, "typical_remittance": "invoice_number"},
            {"customer_id": "CUST-HO-02", "customer_name": "Copperfield Logistics", "payment_behavior": "slow", "on_time_rate": 0.55, "typical_remittance": "amount_only"},
            {"customer_id": "CUST-HO-03", "customer_name": "Solstice Media", "payment_behavior": "mixed", "on_time_rate": 0.8, "typical_remittance": "invoice_number"},
            {"customer_id": "CUST-HO-04", "customer_name": "Redwood Clinics", "payment_behavior": "prompt", "on_time_rate": 0.9, "typical_remittance": "invoice_number"},
        ],
    )
    _append(
        root / "ar_invoices.json",
        [
            {"invoice_id": "INV-HO-AR-PART", "customer_id": "CUST-HO-01", "customer_name": "Meridian Biotech", "invoice_date": "2026-09-02", "due_date": "2026-10-02", "original_amount": 24500.0, "outstanding_amount": 24500.0, "status": "OPEN", "description": "Partial-pay holdout"},
            {"invoice_id": "INV-HO-AR-OVER", "customer_id": "CUST-HO-02", "customer_name": "Copperfield Logistics", "invoice_date": "2026-09-03", "due_date": "2026-10-03", "original_amount": 6400.0, "outstanding_amount": 6400.0, "status": "OPEN", "description": "Overpay holdout"},
            {"invoice_id": "INV-HO-AR-A1", "customer_id": "CUST-HO-03", "customer_name": "Solstice Media", "invoice_date": "2026-09-04", "due_date": "2026-10-04", "original_amount": 7350.0, "outstanding_amount": 7350.0, "status": "OPEN", "description": "Ambiguous twin A"},
            {"invoice_id": "INV-HO-AR-A2", "customer_id": "CUST-HO-03", "customer_name": "Solstice Media", "invoice_date": "2026-09-04", "due_date": "2026-10-04", "original_amount": 7350.0, "outstanding_amount": 7350.0, "status": "OPEN", "description": "Ambiguous twin B"},
            {"invoice_id": "INV-HO-FC-AR", "customer_id": "CUST-HO-04", "customer_name": "Redwood Clinics", "invoice_date": "2026-09-01", "due_date": "2026-11-12", "original_amount": 18750.0, "outstanding_amount": 18750.0, "status": "OPEN", "description": "Due mid-November; must not forecast week 2"},
            {"invoice_id": "INV-HO-FC-LATE", "customer_id": "CUST-HO-01", "customer_name": "Meridian Biotech", "invoice_date": "2026-08-15", "due_date": "2026-09-10", "original_amount": 9100.0, "outstanding_amount": 9100.0, "status": "OPEN", "description": "Late AR miss source"},
        ],
    )
    _append(
        root / "ar_payments.json",
        [
            {"payment_id": "PAY-HO-AR-PART", "payment_date": "2026-09-21", "amount": 22050.0, "currency": "USD", "payer_name": "Meridian Biotech", "customer_id": "CUST-HO-01", "bank_reference": "ACH-MER-22050", "remittance_text": "Partial INV-HO-AR-PART", "invoice_reference": "INV-HO-AR-PART", "source": "ach", "unapplied_amount": 22050.0, "application_status": "UNMATCHED"},
            {"payment_id": "PAY-HO-AR-OVER", "payment_date": "2026-09-22", "amount": 6880.0, "currency": "USD", "payer_name": "Copperfield Logistics", "customer_id": "CUST-HO-02", "bank_reference": "WIRE-CF-6880", "remittance_text": "INV-HO-AR-OVER", "invoice_reference": "INV-HO-AR-OVER", "source": "wire", "unapplied_amount": 6880.0, "application_status": "UNMATCHED"},
            {"payment_id": "PAY-HO-AR-AMB", "payment_date": "2026-09-23", "amount": 7350.0, "currency": "USD", "payer_name": "Solstice Media", "customer_id": "CUST-HO-03", "bank_reference": "ACH-SOL-7350", "remittance_text": "September media services", "invoice_reference": "", "source": "ach", "unapplied_amount": 7350.0, "application_status": "UNMATCHED"},
            {"payment_id": "PAY-HO-AR-BAD", "payment_date": "2026-09-23", "amount": 2880.0, "currency": "USD", "payer_name": "Redwood Clinics", "customer_id": "CUST-HO-04", "bank_reference": "ACH-RW-BAD", "remittance_text": "Payment for AR-INV-8888", "invoice_reference": "AR-INV-8888", "source": "ach", "unapplied_amount": 2880.0, "application_status": "UNMATCHED"},
            {"payment_id": "PAY-HO-AR-ID", "payment_date": "2026-09-24", "amount": 6400.0, "currency": "USD", "payer_name": "Solstice Media", "customer_id": "CUST-HO-02", "bank_reference": "ACH-ID-HO", "remittance_text": "Meridian Biotech INV-HO-AR-OVER", "invoice_reference": "INV-HO-AR-OVER", "source": "ach", "unapplied_amount": 6400.0, "application_status": "UNMATCHED"},
            {"payment_id": "PAY-HO-AR-DBL", "payment_date": "2026-09-18", "amount": 9100.0, "currency": "USD", "payer_name": "Meridian Biotech", "customer_id": "CUST-HO-01", "bank_reference": "WIRE-MER-DBL", "remittance_text": "INV-HO-FC-LATE", "invoice_reference": "INV-HO-FC-LATE", "source": "wire", "unapplied_amount": 0.0, "application_status": "APPLIED"},
        ],
    )
    _append(
        root / "cash_recon" / "bank_statement.json",
        [
            {"transaction_id": "TXN-HO-837", "date": "2026-09-17", "amount": 4810.0, "amount_minor": 481000, "description": "ACH MERIDIAN REMIT", "counterparty": "Meridian Biotech", "period": "2026-09", "source": "bank"},
            {"transaction_id": "TXN-HO-4125", "date": "2026-09-18", "amount": -8412.5, "amount_minor": -841250, "description": "ACH KESTREL GROUP", "counterparty": "Kestrel Components", "period": "2026-09", "source": "bank"},
            {"transaction_id": "TXN-HO-7390", "date": "2026-09-19", "amount": 9150.0, "amount_minor": 915000, "description": "WIRE SOLSTICE", "counterparty": "Solstice Media", "period": "2026-09", "source": "bank"},
            {"transaction_id": "TXN-HO-FEE", "date": "2026-09-20", "amount": -5028.0, "amount_minor": -502800, "description": "WIRE VESPER NET FEE", "counterparty": "Vesper Facilities", "period": "2026-09", "source": "bank"},
            {"transaction_id": "TXN-HO-DUPREF-A", "date": "2026-09-21", "amount": -640.0, "amount_minor": -64000, "description": "REFUND COPPERFIELD", "counterparty": "Copperfield Logistics", "period": "2026-09", "source": "bank", "transaction_type": "refund"},
            {"transaction_id": "TXN-HO-DUPREF-B", "date": "2026-09-21", "amount": -640.0, "amount_minor": -64000, "description": "REFUND COPPERFIELD", "counterparty": "Copperfield Logistics", "period": "2026-09", "source": "bank", "transaction_type": "refund"},
            {"transaction_id": "TXN-HO-BANK", "date": "2026-09-22", "amount": -275.4, "amount_minor": -27540, "description": "UNKNOWN DEBIT CARD", "counterparty": "Unknown", "period": "2026-09", "source": "bank"},
            {"transaction_id": "TXN-HO-STRIPE", "date": "2026-09-24", "amount": 3920.0, "amount_minor": 392000, "description": "STRIPE PAYOUT po_ho_mismatch", "counterparty": "Stripe", "period": "2026-09", "provider": "stripe", "source": "bank"},
            {"transaction_id": "TXN-HO-MULTI", "date": "2026-09-25", "amount": 1880.0, "amount_minor": 188000, "description": "ACH REDWOOD", "counterparty": "Redwood Clinics", "period": "2026-09", "source": "bank"},
        ],
    )
    _append(
        root / "cash_recon" / "ledger.json",
        [
            {"entry_id": "GL-HO-837", "date": "2026-09-17", "amount": 4801.63, "amount_minor": 480163, "account": "Cash", "counterparty": "Meridian Biotech", "period": "2026-09", "description": "Meridian remittance books"},
            {"entry_id": "GL-HO-4125-1", "date": "2026-09-18", "amount": -2800.0, "amount_minor": -280000, "account": "Cash", "counterparty": "Kestrel Components", "period": "2026-09", "description": "AP 2800"},
            {"entry_id": "GL-HO-4125-2", "date": "2026-09-18", "amount": -3100.0, "amount_minor": -310000, "account": "Cash", "counterparty": "Kestrel Components", "period": "2026-09", "description": "AP 3100"},
            {"entry_id": "GL-HO-4125-3", "date": "2026-09-18", "amount": -2471.25, "amount_minor": -247125, "account": "Cash", "counterparty": "Kestrel Components", "period": "2026-09", "description": "AP 2471.25"},
            {"entry_id": "GL-HO-7390", "date": "2026-09-19", "amount": 9076.1, "amount_minor": 907610, "account": "Cash", "counterparty": "Solstice Media", "period": "2026-09", "description": "Solstice books"},
            {"entry_id": "GL-HO-FEE", "date": "2026-09-20", "amount": -5000.0, "amount_minor": -500000, "account": "Cash", "counterparty": "Vesper Facilities", "period": "2026-09", "description": "Vesper principal"},
            {"entry_id": "GL-HO-DUPREF", "date": "2026-09-21", "amount": -640.0, "amount_minor": -64000, "account": "Cash", "counterparty": "Copperfield Logistics", "period": "2026-09", "description": "One refund counterpart"},
            {"entry_id": "GL-HO-LEDGER", "date": "2026-09-22", "amount": -1190.0, "amount_minor": -119000, "account": "Cash", "counterparty": "Brightlane Optics", "period": "2026-09", "description": "Orphan AP payment"},
            {"entry_id": "GL-HO-STRIPE", "date": "2026-09-24", "amount": 4100.0, "amount_minor": 410000, "account": "Cash", "counterparty": "Stripe", "period": "2026-09", "description": "Stripe books before fees", "entry_type": "provider_payout", "raw_metadata": {"provider": "stripe", "payout_id": "po_ho_mismatch"}},
            {"entry_id": "GL-HO-MULTI-A", "date": "2026-09-25", "amount": 1880.0, "amount_minor": 188000, "account": "Cash", "counterparty": "Redwood Clinics", "period": "2026-09", "description": "Candidate A"},
            {"entry_id": "GL-HO-MULTI-B", "date": "2026-09-25", "amount": 1880.0, "amount_minor": 188000, "account": "Cash", "counterparty": "Redwood Clinics", "period": "2026-09", "description": "Candidate B"},
        ],
    )
    _append(
        root / "cash_recon" / "fee_evidence.json",
        [
            {"evidence_id": "FEE-HO-28", "date": "2026-09-20", "amount": 28.0, "amount_minor": 2800, "fee_type": "bank_fee", "reference": "TXN-HO-FEE", "description": "Outbound wire fee"},
        ],
    )
    _save(
        root / "close" / "gl_balances.json",
        [
            {"account": "Accounts Payable", "balance": 2.0, "period": "2026-09", "source_id": "GL-HO-AP"},
            {"account": "Accounts Receivable", "balance": 0.0, "period": "2026-09", "source_id": "GL-HO-AR"},
            {"account": "Prepaid Expense", "balance": 16875.0, "period": "2026-09", "source_id": "PRE-HO-001"},
            {"account": "Accumulated Depreciation", "balance": 750.0, "period": "2026-09", "source_id": "FA-HO-001"},
            {"account": "Suspense", "balance": 3180.0, "period": "2026-09", "source_id": "GL-HO-UNSUP"},
        ],
    )
    prepaids = _load(root / "close" / "prepaids.json", [])
    if not any(item.get("prepaid_id") == "PRE-HO-001" for item in prepaids):
        prepaids.append(
            {
                "prepaid_id": "PRE-HO-001",
                "vendor": "Nimbus Licensing",
                "description": "Twelve-month license starting September",
                "source_document_id": "DOC-HO-PRE",
                "total_amount": 18000.0,
                "start_date": "2026-09-01",
                "end_date": "2027-08-31",
                "initial_account": "Prepaid Expense",
                "expense_account": "Software Subscription Expense",
                "amortization_method": "straight_line_monthly",
                "currency": "USD",
                "status": "active",
                "created_at": "2026-09-01T00:00:00Z",
                "evidence_refs": ["DOC-HO-PRE"],
                "transaction_id": "TXN-HO-PRE",
            }
        )
        _save(root / "close" / "prepaids.json", prepaids)
    assets = _load(root / "close" / "fixed_assets.json", [])
    if not any(item.get("asset_id") == "FA-HO-001" for item in assets):
        assets.append(
            {
                "asset_id": "FA-HO-001",
                "description": "Holdout CNC fixture cell",
                "vendor": "Kestrel Components",
                "acquisition_date": "2026-09-06",
                "placed_in_service_date": "2026-09-06",
                "cost": 48000.0,
                "salvage_value": 0.0,
                "useful_life_months": 24,
                "depreciation_method": "straight_line",
                "asset_account": "Computer Equipment",
                "accumulated_depreciation_account": "Accumulated Depreciation - Equipment",
                "depreciation_expense_account": "Depreciation Expense",
                "evidence_refs": ["DOC-HO-FA"],
                "status": "active",
                "asset_class": "tangible",
                "source_document_id": "DOC-HO-FA",
                "transaction_id": "TXN-HO-FA",
                "created_at": "2026-09-06T00:00:00Z",
            }
        )
        _save(root / "close" / "fixed_assets.json", assets)
    _append(
        root / "audit" / "vendors.json",
        [
            {"vendor_id": "VEND-HO", "vendor_name": "Pinecrest Chemicals", "first_seen": "2024-03-01", "status": "active"},
            {"vendor_id": "VEND-HO-DUP", "vendor_name": "Pinecrest Chemicals LLC", "first_seen": "2026-09-04", "status": "active"},
        ],
    )
    _append(
        root / "audit" / "payments.json",
        [
            {"payment_id": "PAY-HO-RND", "amount": 80000.0, "vendor_id": "VEND-HO", "vendor_name": "Pinecrest Chemicals", "payment_date": "2026-09-16", "payment_method": "wire", "source": "manual", "invoice_ids": ["INV-HO-LIMIT"], "initiator_id": "USR-HO-01", "approver_id": "USR-HO-02", "period": "2026-09", "description": "Round holdout payment"},
            {"payment_id": "PAY-HO-NOSUP", "amount": 4110.0, "vendor_id": "VEND-HO", "vendor_name": "Pinecrest Chemicals", "payment_date": "2026-09-17", "payment_method": "ach", "source": "manual", "invoice_ids": ["INV-HO-HELD"], "initiator_id": "USR-HO-01", "approver_id": "USR-HO-02", "period": "2026-09", "description": "Missing-support holdout", "missing_support": True},
        ],
    )
    _append(
        root / "audit" / "approvals.json",
        [
            {"approval_id": "APR-HO-SELF", "object_type": "invoice", "object_id": "INV-HO-LIMIT", "requester_id": "USR-HO-PREP", "preparer_id": "USR-HO-PREP", "reviewer_id": "USR-HO-REV", "approver_id": "USR-HO-PREP", "amount": 72000.0, "period": "2026-09"},
        ],
    )
    _append(
        root / "audit" / "journal_entries.json",
        [
            {
                "entry_id": "JE-HO-POST",
                "period": "2026-09",
                "effective_date": "2026-09-30",
                "posting_date": "2026-10-03",
                "posting_timestamp": "2026-10-03T09:15:00Z",
                "amount": 3180.0,
                "vendor": "Pinecrest Chemicals",
                "memo": "Holdout post-close suspense",
                "poster_id": "USR-HO-01",
                "authorized": False,
                "debit_account": "Suspense",
                "credit_account": "Cash",
                "preparer_id": "USR-HO-01",
                "approver_id": "USR-HO-01",
            }
        ],
    )
    _append(
        root / "audit" / "invoices.json",
        [
            {"invoice_id": "INV-HO-LIMIT", "vendor_id": "VEND-HO", "vendor": "Vesper Facilities", "vendor_invoice_number": "VF-HO-72K", "amount": 72000.0, "invoice_date": "2026-09-15", "period": "2026-09"},
        ],
    )
    _append(
        root / "audit" / "reconciliations.json",
        [
            {
                "reconciliation_id": "REC-HO-7390",
                "period": "2026-09",
                "recon_type": "cash",
                "bank_transaction_ids": ["TXN-HO-7390"],
                "ledger_entry_ids": ["GL-HO-7390"],
                "original_match_type": "EXACT_MATCH",
                "original_status": "MATCHED",
                "original_bank_amount": 9150.0,
                "original_ledger_amount": 9076.1,
                "original_difference": 0.0,
                "planted_error": True,
                "vendor": "Solstice Media",
            }
        ],
    )
    _append(
        root / "later_invoices.json",
        [
            {
                "invoice_id": "INV-VF-2026-09",
                "vendor": "Vesper Facilities",
                "amount": 6120.0,
                "invoice_date": "2026-10-06",
                "service_period": "2026-09",
                "currency": "USD",
                "expense_account": "Facilities Expense",
                "vendor_invoice_number": "VF-2026-09",
                "description": "September facilities — arrived in October",
                "po_id": None,
                "source": "historical",
            }
        ],
    )
    _append(
        root / "reporting" / "actuals.json",
        [
            {"movement_id": "ACT-HO-NOSRC", "source_type": "other", "source_id": "ACT-HO-NOSRC", "date": "2026-09-14", "amount": -275.4, "kind": "outflow", "description": "Untraceable holdout actual"},
            {"movement_id": "ACT-HO-FC-LATE", "source_type": "invoice", "source_id": "INV-HO-FC-LATE", "date": "2026-09-28", "amount": 9100.0, "kind": "inflow", "description": "Late AR collected after forecast week"},
        ],
    )
    _append(
        root / "reporting" / "ap_forecast_state.json",
        [
            {
                "invoice_id": "INV-HO-FC-MISS",
                "hold": False,
                "scheduled_pay_date": "2026-09-28",
                "approval_state": "approved",
                "reason": "Approved payable inside the horizon",
            }
        ],
    )
    draft = {
        "forecast_id": "CF-DRAFT-HO",
        "as_of_date": "2026-09-19",
        "horizon_weeks": 13,
        "beginning_cash": 2.5,
        "weeks": [],
        "lines": [
            {
                "line_id": "FL-HO-DUP-1",
                "source_type": "invoice",
                "source_id": "INV-HO-FC-DUP",
                "expected_date": "2026-09-29",
                "amount": -18800.0,
                "confidence": 0.9,
                "rationale": "Approved payable copy A",
            },
            {
                "line_id": "FL-HO-DUP-2",
                "source_type": "invoice",
                "source_id": "INV-HO-FC-DUP",
                "expected_date": "2026-09-29",
                "amount": -18800.0,
                "confidence": 0.9,
                "rationale": "Approved payable copy B",
            },
            {
                "line_id": "FL-HO-EARLY",
                "source_type": "receivable",
                "source_id": "INV-HO-FC-AR",
                "expected_date": "2026-09-24",
                "amount": 18750.0,
                "confidence": 0.35,
                "rationale": "Early collection with no promise",
                "evidence_refs": ["due:2026-11-12"],
            },
        ],
    }
    _save(root / "reporting" / "draft_forecast.json", draft)
    integrations = root / "integrations" / "stripe"
    integrations.mkdir(parents=True, exist_ok=True)
    payouts = _load(integrations / "payouts.json", [])
    if not isinstance(payouts, list):
        payouts = []
    if not any(item.get("payout_id") == "po_ho_mismatch" for item in payouts):
        payouts.append(
            {
                "payout_id": "po_ho_mismatch",
                "provider": "stripe",
                "amount": 410000,
                "bank_deposit_amount": 3920.0,
                "arrival_date": "2026-09-24",
                "status": "paid",
                "charges": 4300.0,
                "refunds": 80.0,
                "fees": 120.0,
                "disputes": 0.0,
            }
        )
        _save(integrations / "payouts.json", payouts)

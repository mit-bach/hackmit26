"""Append operational discrepancy records. No answer-key fields on these objects."""

from __future__ import annotations

import json
from pathlib import Path


def _load(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def _save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def _append(path: Path, rows: list) -> None:
    existing = _load(path, [])
    seen = {item.get("invoice_id") or item.get("payment_id") or item.get("po_id") or item.get("transaction_id") or item.get("entry_id") or item.get("receipt_id") or item.get("asset_id") or item.get("vendor_id") or item.get("approval_id") or item.get("journal_id") or json.dumps(item, sort_keys=True) for item in existing}
    for row in rows:
        key = row.get("invoice_id") or row.get("payment_id") or row.get("po_id") or row.get("transaction_id") or row.get("entry_id") or row.get("receipt_id") or row.get("asset_id") or row.get("vendor_id") or row.get("approval_id") or row.get("journal_id") or json.dumps(row, sort_keys=True)
        if key not in seen:
            existing.append(row)
            seen.add(key)
    _save(path, existing)


def apply_overlays(root: Path) -> None:
    root = Path(root)
    _append(
        root / "purchase_orders.json",
        [
            {"po_id": "PO-DISC-1048", "vendor": "Acme Software Inc.", "authorized_amount": 4800.0, "description": "License block", "status": "approved", "created_date": "2026-09-02", "approval_limit": 10000.0, "approver": "Jordan Hale"},
            {"po_id": "PO-DISC-OVER", "vendor": "Northwind Labs", "authorized_amount": 8000.0, "description": "Unused AP PO for AR overpay case", "status": "approved", "created_date": "2026-09-01", "approval_limit": 20000.0, "approver": "Priya Nair"},
        ],
    )
    _append(
        root / "goods_receipts.json",
        [
            {"receipt_id": "GR-DISC-1048", "po_id": "PO-DISC-1048", "received": True, "received_date": "2026-09-06", "amount_received": 4800.0, "quantity_ordered": 8, "quantity_received": 8},
        ],
    )
    _append(
        root / "invoices.json",
        [
            {"invoice_id": "INV-DISC-1048A", "vendor": "Acme Software Inc.", "po_id": "PO-DISC-1048", "amount": 4800.0, "invoice_date": "2026-09-08", "due_date": "2026-10-08", "vendor_invoice_number": "INV-1048", "description": "Software seats"},
            {"invoice_id": "INV-DISC-1048B", "vendor": "ACME SOFTWARE, INC", "po_id": "PO-DISC-1048", "amount": 4800.0, "invoice_date": "2026-09-08", "due_date": "2026-10-08", "vendor_invoice_number": "INV 1048", "description": "Software seats duplicate formatting"},
            {"invoice_id": "INV-DISC-FC-DUP", "vendor": "GitHub", "po_id": "PO-112", "amount": 21000.0, "invoice_date": "2026-09-02", "due_date": "2026-10-02", "vendor_invoice_number": "GH-DISC-DUP", "description": "Forecast duplicate-outflow marker"},
        ],
    )
    _append(
        root / "ar_invoices.json",
        [
            {"invoice_id": "INV-DISC-PARTIAL", "customer_id": "CUST-006", "customer_name": "Pinnacle Retail", "invoice_date": "2026-09-01", "due_date": "2026-10-01", "original_amount": 10000.0, "outstanding_amount": 10000.0, "status": "OPEN", "description": "Partial-pay target"},
            {"invoice_id": "INV-DISC-OVER", "customer_id": "CUST-001", "customer_name": "Northwind Labs", "invoice_date": "2026-09-02", "due_date": "2026-10-02", "original_amount": 8000.0, "outstanding_amount": 8000.0, "status": "OPEN", "description": "Overpay target"},
            {"invoice_id": "INV-DISC-SETTLE", "customer_id": "CUST-003", "customer_name": "Acme Industrial", "invoice_date": "2026-09-03", "due_date": "2026-10-03", "original_amount": 2200.0, "outstanding_amount": 2200.0, "status": "OPEN", "description": "AR still open while GL is settled"},
            {"invoice_id": "INV-DISC-FC-AR", "customer_id": "CUST-002", "customer_name": "Helios Analytics", "invoice_date": "2026-09-01", "due_date": "2026-10-31", "original_amount": 15000.0, "outstanding_amount": 15000.0, "status": "OPEN", "description": "Due week 6; must not forecast week 2 without evidence"},
        ],
    )
    _append(
        root / "ar_payments.json",
        [
            {"payment_id": "PAY-DISC-PARTIAL", "payment_date": "2026-09-20", "amount": 9600.0, "currency": "USD", "payer_name": "Pinnacle Retail", "customer_id": "CUST-006", "bank_reference": "ACH-PIN-9600", "remittance_text": "Partial INV-DISC-PARTIAL", "invoice_reference": "INV-DISC-PARTIAL", "source": "ach", "unapplied_amount": 9600.0, "application_status": "UNMATCHED"},
            {"payment_id": "PAY-DISC-OVER", "payment_date": "2026-09-21", "amount": 8750.0, "currency": "USD", "payer_name": "Northwind Labs", "customer_id": "CUST-001", "bank_reference": "WIRE-NW-8750", "remittance_text": "INV-DISC-OVER", "invoice_reference": "INV-DISC-OVER", "source": "wire", "unapplied_amount": 8750.0, "application_status": "UNMATCHED"},
            {"payment_id": "PAY-DISC-BADREF", "payment_date": "2026-09-22", "amount": 3200.0, "currency": "USD", "payer_name": "Quiet Harbor", "customer_id": "CUST-005", "bank_reference": "ACH-QH-BAD", "remittance_text": "Payment for AR-INV-9999", "invoice_reference": "AR-INV-9999", "source": "ach", "unapplied_amount": 3200.0, "application_status": "UNMATCHED"},
            {"payment_id": "PAY-DISC-ID", "payment_date": "2026-09-22", "amount": 8500.0, "currency": "USD", "payer_name": "Helios Analytics", "customer_id": "CUST-003", "bank_reference": "ACH-ID-CONF", "remittance_text": "Northwind Labs INV-AR-001", "invoice_reference": "INV-AR-001", "source": "ach", "unapplied_amount": 8500.0, "application_status": "UNMATCHED"},
            {"payment_id": "PAY-DISC-DOUBLE", "payment_date": "2026-09-18", "amount": 12000.0, "currency": "USD", "payer_name": "Northwind Labs", "customer_id": "CUST-001", "bank_reference": "WIRE-NW-DBL", "remittance_text": "INV-AR-007", "invoice_reference": "INV-AR-007", "source": "wire", "unapplied_amount": 0.0, "application_status": "APPLIED"},
        ],
    )
    _append(
        root / "cash_recon" / "bank_statement.json",
        [
            {"transaction_id": "TXN-DISC-GRP", "date": "2026-09-18", "amount": -5850.0, "amount_minor": -585000, "description": "ACH NORTHLINE GROUP", "counterparty": "Northline Fabrication", "period": "2026-09", "source": "bank"},
            {"transaction_id": "TXN-DISC-STRIPE", "date": "2026-09-24", "amount": 1840.0, "amount_minor": 184000, "description": "STRIPE PAYOUT po_disc_mismatch", "counterparty": "Stripe", "period": "2026-09", "provider": "stripe", "source": "bank"},
        ],
    )
    _append(
        root / "cash_recon" / "ledger.json",
        [
            {"entry_id": "GL-DISC-GRP-1", "date": "2026-09-18", "amount": -1000.0, "amount_minor": -100000, "account": "Cash", "counterparty": "Northline Fabrication", "period": "2026-09", "description": "AP 1000"},
            {"entry_id": "GL-DISC-GRP-2", "date": "2026-09-18", "amount": -2000.0, "amount_minor": -200000, "account": "Cash", "counterparty": "Northline Fabrication", "period": "2026-09", "description": "AP 2000"},
            {"entry_id": "GL-DISC-GRP-3", "date": "2026-09-18", "amount": -3000.0, "amount_minor": -300000, "account": "Cash", "counterparty": "Northline Fabrication", "period": "2026-09", "description": "AP 3000"},
            {"entry_id": "GL-DISC-STRIPE", "date": "2026-09-24", "amount": 2100.0, "amount_minor": 210000, "account": "Cash", "counterparty": "Stripe", "period": "2026-09", "description": "Stripe books before fees", "raw_metadata": {"provider": "stripe", "payout_id": "po_disc_mismatch"}},
        ],
    )
    gl_balances = [
        {"account": "Accounts Payable", "balance": 1.0, "period": "2026-09", "source_id": "GL-AP-DISC"},
        {"account": "Accounts Receivable", "balance": 0.0, "period": "2026-09", "source_id": "GL-AR-DISC"},
        {"account": "Prepaid Expense", "balance": 10800.0, "period": "2026-09", "source_id": "PRE-SFT-001"},
        {"account": "Accumulated Depreciation", "balance": 500.0, "period": "2026-09", "source_id": "FA-DELL-001"},
        {"account": "Suspense", "balance": 2500.0, "period": "2026-09", "source_id": "GL-UNSUP-001"},
    ]
    _save(root / "close" / "gl_balances.json", gl_balances)
    _append(
        root / "reporting" / "actuals.json",
        [
            {"movement_id": "ACT-DISC-NOSRC", "source_type": "other", "source_id": "ACT-DISC-NOSRC", "date": "2026-09-12", "amount": -400.0, "kind": "outflow", "description": "Untraceable actual"},
            {"movement_id": "ACT-DISC-FC-PAY", "source_type": "invoice", "source_id": "INV-DISC-FC-PAY", "date": "2026-09-12", "amount": -2100.0, "kind": "outflow", "description": "Forecast claims payment; no bank"},
        ],
    )
    import shutil

    canonical_adyen = Path(__file__).resolve().parent.parent / "data" / "integrations" / "adyen"
    dest_adyen = root / "integrations" / "adyen"
    if canonical_adyen.exists() and not (dest_adyen / "events.json").exists():
        dest_adyen.mkdir(parents=True, exist_ok=True)
        shutil.copytree(canonical_adyen, dest_adyen, dirs_exist_ok=True)
    integrations = root / "integrations" / "stripe"
    integrations.mkdir(parents=True, exist_ok=True)
    payouts = _load(integrations / "payouts.json", [])
    if not isinstance(payouts, list):
        payouts = []
    if not any(item.get("payout_id") == "po_disc_mismatch" for item in payouts):
        payouts.append(
            {
                "payout_id": "po_disc_mismatch",
                "provider": "stripe",
                "amount": 210000,
                "bank_deposit_amount": 1840.0,
                "arrival_date": "2026-09-24",
                "status": "paid",
                "charges": 2200.0,
                "refunds": 50.0,
                "fees": 50.0,
                "disputes": 0.0,
            }
        )
        _save(integrations / "payouts.json", payouts)
    draft = {
        "forecast_id": "CF-DRAFT-DISC",
        "as_of_date": "2026-09-19",
        "horizon_weeks": 13,
        "beginning_cash": 1.0,
        "weeks": [],
        "lines": [
            {
                "line_id": "FL-DUP-1",
                "source_type": "invoice",
                "source_id": "INV-DISC-FC-DUP",
                "expected_date": "2026-09-25",
                "amount": -21000.0,
                "confidence": 0.9,
                "rationale": "Approved payable copy A",
            },
            {
                "line_id": "FL-DUP-2",
                "source_type": "invoice",
                "source_id": "INV-DISC-FC-DUP",
                "expected_date": "2026-09-25",
                "amount": -21000.0,
                "confidence": 0.9,
                "rationale": "Approved payable copy B",
            },
            {
                "line_id": "FL-EARLY-AR",
                "source_type": "receivable",
                "source_id": "INV-DISC-FC-AR",
                "expected_date": "2026-09-22",
                "amount": 15000.0,
                "confidence": 0.4,
                "rationale": "Early collection with no promise or historical early-pay evidence",
                "evidence_refs": ["due:2026-10-31"],
            },
        ],
    }
    _save(root / "reporting" / "draft_forecast.json", draft)
    _append(
        root / "reporting" / "ap_forecast_state.json",
        [
            {
                "invoice_id": "INV-002",
                "hold": False,
                "scheduled_pay_date": "2026-09-25",
                "approval_state": "approved",
                "reason": "Approved payable inside the 13-week horizon",
            }
        ],
    )

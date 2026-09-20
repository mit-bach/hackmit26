"""Invoice error-detection eval against the current 15-agent kernel path.

Uses the same Python engines the live office uses:

* ``classify_text`` / inbox ``handoff`` for document intake
* ``decide_ap(..., live=False)`` for AP matching (Kernel policy, not the old
  43-agent ``run_ap_workflow``)
* ``policy_eligible_for_pool`` for payment scheduling
* ``exception_types_for`` / ``collect_case_evidence`` for deterministic facts

Does not load answer keys into operational agents. Expected outcomes come from
this catalog, ``sample_data/registry.py``, ``expected_outcomes.json``, inbox
fixtures, and holdout contracts.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from close.orchestrator import decide_ap
from evaluation.context import operational_dataset
from invoice_ingestion.interpret import classify_text
from invoice_ingestion.models import InvoiceCandidate, InvoiceLineItem
from invoice_ingestion.validate import amounts_consistent, existing_ap_match, validate_candidate
from sample_data.paths import data_root
from scheduling.cash import policy_eligible_for_pool
from tools import (
    collect_case_evidence,
    exception_types_for,
    load_invoice,
    normalize_invoice_number,
    vendor_alias_established,
)


REPO = Path(__file__).resolve().parent.parent
WORKSPACE = REPO.parent if REPO.name == ".cfo" else REPO
DEMO = REPO / "data" / "demo"
FIXTURES = REPO / "data"
HOLDOUT = REPO / "data" / "discrepancy_holdout"
RESULTS_DIR = WORKSPACE / "runs" / "evals"
KERNEL_RESULTS_DIR = REPO / "runs" / "evals"


# ---------------------------------------------------------------------------
# Ground-truth catalog recovered from generators, answer keys, and tests.
# ---------------------------------------------------------------------------

DEMO_AP_CASES: list[dict[str, Any]] = [
    {
        "case_id": "DEMO-INV-001",
        "category": "AS",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases / data/demo/invoices.json",
        "document_type": "invoice",
        "planted_error": None,
        "expected_error": [],
        "expected_action": "APPROVE",
        "invoice_id": "INV-001",
        "notes": "Clean three-way match SCN-AP-001. Must not flag. Already paid via PAY-AP-001 so must not be scheduled again.",
        "already_paid": True,
        "pay_eligible": False,
    },
    {
        "case_id": "DEMO-INV-002",
        "category": "AS",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": None,
        "expected_error": [],
        "expected_action": "APPROVE",
        "invoice_id": "INV-002",
        "notes": "Clean AWS invoice due this week SCN-AP-009.",
        "pay_eligible": True,
    },
    {
        "case_id": "DEMO-INV-003",
        "category": "X",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": "partial_receipt",
        "expected_error": ["partial_receipt"],
        "expected_action": "HOLD",
        "invoice_id": "INV-003",
        "notes": "SCN-AP-002 quantity mismatch: 50 billed/ordered, 40 received. Repo exception type is partial_receipt.",
        "pay_eligible": False,
    },
    {
        "case_id": "DEMO-INV-004",
        "category": "T",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": "material_amount_mismatch",
        "expected_error": ["material_amount_mismatch"],
        "expected_action": "HOLD",
        "invoice_id": "INV-004",
        "notes": "SCN-AP-003 Slack billed $5000 vs PO $4375.",
        "pay_eligible": False,
    },
    {
        "case_id": "DEMO-INV-005",
        "category": "Z",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": "goods_not_received",
        "expected_error": ["goods_not_received"],
        "expected_action": "HOLD",
        "invoice_id": "INV-005",
        "notes": "SCN-AP-004 missing goods receipt.",
        "pay_eligible": False,
    },
    {
        "case_id": "DEMO-INV-006",
        "category": "A",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": "duplicate",
        "expected_error": ["duplicate"],
        "expected_action": "HOLD",
        "invoice_id": "INV-006",
        "notes": "SCN-AP-005 original of SV-999001.",
        "pay_eligible": False,
    },
    {
        "case_id": "DEMO-INV-007",
        "category": "A",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": "duplicate",
        "expected_error": ["duplicate"],
        "expected_action": "HOLD",
        "invoice_id": "INV-007",
        "notes": "SCN-AP-005 peer duplicate submission.",
        "pay_eligible": False,
    },
    {
        "case_id": "DEMO-INV-008",
        "category": "AH",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": "po_not_approved",
        "expected_error": ["po_not_approved"],
        "expected_action": "HOLD",
        "invoice_id": "INV-008",
        "notes": "SCN-AP-006 PO pending approval.",
        "pay_eligible": False,
    },
    {
        "case_id": "DEMO-INV-009",
        "category": "AH",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": "approval_limit_exceeded",
        "expected_error": ["approval_limit_exceeded"],
        "expected_action": "HOLD",
        "invoice_id": "INV-009",
        "notes": "SCN-AP-007 $50k PO vs $10k approver limit. Also round-number / self-approval audit traps.",
        "pay_eligible": False,
    },
    {
        "case_id": "DEMO-INV-010",
        "category": "W",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": "goods_not_received",
        "expected_error": ["goods_not_received"],
        "expected_action": "HOLD",
        "invoice_id": "INV-010",
        "notes": "SCN-AP-008 on hold; PAY-AP-010 is the paid-while-held audit trap.",
        "pay_eligible": False,
    },
    {
        "case_id": "DEMO-INV-012",
        "category": "AS",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": None,
        "expected_error": [],
        "expected_action": "APPROVE",
        "invoice_id": "INV-012",
        "notes": "SCN-AP-010 clean three-way match. PAY-AP-012 already paid it early, so matching APPROVE must not reschedule.",
        "already_paid": True,
        "pay_eligible": False,
        "schedule_kind": "defer",
    },
    {
        "case_id": "DEMO-INV-013",
        "category": "AS",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": None,
        "expected_error": [],
        "expected_action": "APPROVE",
        "invoice_id": "INV-013",
        "notes": "SCN-AP-011 clean with open 2/10 discount.",
        "pay_eligible": True,
        "schedule_kind": "discount",
    },
    {
        "case_id": "DEMO-INV-014",
        "category": "AS",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": None,
        "expected_error": [],
        "expected_action": "APPROVE",
        "invoice_id": "INV-014",
        "notes": "Clean Northline invoice; grouped ACH already paid. Must not reschedule.",
        "already_paid": True,
        "pay_eligible": False,
    },
    {
        "case_id": "DEMO-INV-015",
        "category": "AS",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": None,
        "expected_error": [],
        "expected_action": "APPROVE",
        "invoice_id": "INV-015",
        "notes": "Clean Northline invoice; already paid in grouped ACH.",
        "already_paid": True,
        "pay_eligible": False,
    },
    {
        "case_id": "DEMO-INV-016",
        "category": "AS",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": None,
        "expected_error": [],
        "expected_action": "APPROVE",
        "invoice_id": "INV-016",
        "notes": "Clean Northline invoice; already paid in grouped ACH.",
        "already_paid": True,
        "pay_eligible": False,
    },
    {
        "case_id": "DEMO-INV-017",
        "category": "AF",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": None,
        "expected_error": [],
        "expected_action": "APPROVE",
        "invoice_id": "INV-017",
        "notes": "Helios invoice itself is a clean three-way match. Fee-netted wire is a cash-recon fact, not an AP hold. Already paid.",
        "already_paid": True,
        "pay_eligible": False,
    },
    {
        "case_id": "DEMO-INV-018",
        "category": "AS",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": None,
        "expected_error": [],
        "expected_action": "APPROVE",
        "invoice_id": "INV-018",
        "notes": "Dell capital invoice. Clean match. Distinct from handwritten fixture INV-018 (duplicate).",
        "pay_eligible": True,
    },
    {
        "case_id": "DEMO-INV-019",
        "category": "AS",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": None,
        "expected_error": [],
        "expected_action": "APPROVE",
        "invoice_id": "INV-019",
        "notes": "Hartford prepaid source invoice with full receipt.",
        "pay_eligible": True,
    },
    {
        "case_id": "DEMO-INV-020",
        "category": "Y",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": "missing_po",
        "expected_error": ["missing_po"],
        "expected_action": "HOLD",
        "invoice_id": "INV-020",
        "notes": "Orbit Analytics prepaid from 2025 with no PO. Must not enter the payment pool.",
        "pay_eligible": False,
    },
    {
        "case_id": "DEMO-INV-021",
        "category": "I",
        "source_file": "sample_data/agents/ap_ar.py:_ap_cases",
        "document_type": "invoice",
        "planted_error": "vendor_mismatch",
        "expected_error": ["vendor_mismatch"],
        "expected_action": "APPROVE",
        "invoice_id": "INV-021",
        "notes": "SCN-AP-013 Acme Supply Co. alias supported by August CASE-001. Exception present; payment allowed.",
        "pay_eligible": True,
        "alias_required": True,
    },
]

DEMO_INGEST_CASES: list[dict[str, Any]] = [
    {
        "case_id": "DEMO-MSG-E-INV-001",
        "category": "AS",
        "source_file": "sample_data/agents/ap_ar.py:_ingestion / data/demo/ingestion/emails.json",
        "document_type": "invoice",
        "planted_error": None,
        "expected_error": [],
        "expected_action": "CLASSIFY_INVOICE",
        "message_id": "MSG-E-INV-001",
        "expected_class": "invoice",
        "notes": "SCN-ING-001 true payable invoice.",
    },
    {
        "case_id": "DEMO-MSG-E-MESSY",
        "category": "AP",
        "source_file": "sample_data/agents/ap_ar.py:_ingestion",
        "document_type": "invoice",
        "planted_error": None,
        "expected_error": [],
        "expected_action": "CLASSIFY_INVOICE",
        "message_id": "MSG-E-MESSY",
        "expected_class": "invoice",
        "notes": "SCN-ING-002 OCR-messy but still a true invoice (1NVOICE header).",
    },
    {
        "case_id": "DEMO-MSG-E-PO",
        "category": "G",
        "source_file": "sample_data/agents/ap_ar.py:_ingestion",
        "document_type": "purchase_order",
        "planted_error": "purchase_order_as_invoice",
        "expected_error": ["purchase_order"],
        "expected_action": "NO_AP",
        "message_id": "MSG-E-PO",
        "expected_class": "purchase_order",
        "notes": "SCN-ING-003 / SCN-AP-012. Must not enter AP. Official evaluate-cfo currently accepts not_invoice.",
    },
    {
        "case_id": "DEMO-MSG-E-QUOTE",
        "category": "D",
        "source_file": "sample_data/agents/ap_ar.py:_ingestion",
        "document_type": "quote",
        "planted_error": "quote_as_invoice",
        "expected_error": ["quote"],
        "expected_action": "NO_AP",
        "message_id": "MSG-E-QUOTE",
        "expected_class": "quote",
        "notes": "SCN-ING-004.",
    },
    {
        "case_id": "DEMO-MSG-E-RCPT",
        "category": "E",
        "source_file": "sample_data/agents/ap_ar.py:_ingestion",
        "document_type": "receipt",
        "planted_error": "receipt_as_invoice",
        "expected_error": ["receipt"],
        "expected_action": "NO_AP",
        "message_id": "MSG-E-RCPT",
        "expected_class": "receipt",
        "notes": "SCN-ING-005 Uber receipt. Official evaluate-cfo currently accepts not_invoice.",
    },
    {
        "case_id": "DEMO-MSG-E-STMT",
        "category": "F",
        "source_file": "sample_data/agents/ap_ar.py:_ingestion",
        "document_type": "statement",
        "planted_error": "statement_as_invoice",
        "expected_error": ["statement"],
        "expected_action": "NO_AP",
        "message_id": "MSG-E-STMT",
        "expected_class": "statement",
        "notes": "SCN-ING-006.",
    },
    {
        "case_id": "DEMO-MSG-E-MKT",
        "category": "AS",
        "source_file": "sample_data/agents/ap_ar.py:_ingestion",
        "document_type": "marketing",
        "planted_error": None,
        "expected_error": [],
        "expected_action": "NO_AP",
        "message_id": "MSG-E-MKT",
        "expected_class": "marketing",
        "notes": "SCN-ING-007.",
    },
    {
        "case_id": "DEMO-MSG-E-INFER",
        "category": "AS",
        "source_file": "sample_data/agents/ap_ar.py:_ingestion",
        "document_type": "invoice",
        "planted_error": None,
        "expected_error": [],
        "expected_action": "CLASSIFY_INVOICE",
        "message_id": "MSG-E-INFER",
        "expected_class": "invoice",
        "notes": "SCN-ING-008 vendor inferable.",
    },
    {
        "case_id": "DEMO-MSG-E-MISSING",
        "category": "AQ",
        "source_file": "sample_data/agents/ap_ar.py:_ingestion",
        "document_type": "not_invoice",
        "planted_error": "missing_required_field",
        "expected_error": ["not_invoice"],
        "expected_action": "NO_AP",
        "message_id": "MSG-E-MISSING",
        "expected_class": "not_invoice",
        "notes": "SCN-ING-009 unsafe missing amount/vendor/number.",
    },
    {
        "case_id": "DEMO-MSG-E-DUP-001",
        "category": "C",
        "source_file": "sample_data/agents/ap_ar.py:_ingestion",
        "document_type": "invoice",
        "planted_error": "duplicate_copy",
        "expected_error": ["invoice"],
        "expected_action": "CLASSIFY_INVOICE",
        "message_id": "MSG-E-DUP-001",
        "expected_class": "invoice",
        "notes": "SCN-ING-010 same invoice, different filename. Classification is invoice; registration must not create a second payable.",
    },
]

FIXTURE_AP_CASES: list[dict[str, Any]] = [
    {"case_id": "FIX-INV-001", "category": "AS", "invoice_id": "INV-001", "expected_error": [], "expected_action": "APPROVE", "planted_error": None, "source_file": "data/invoices.json", "document_type": "invoice", "notes": "Handwritten clean three-way match. IDs collide with demo pack but facts differ."},
    {"case_id": "FIX-INV-011", "category": "AS", "invoice_id": "INV-011", "expected_error": ["small_amount_discrepancy"], "expected_action": "APPROVE", "planted_error": "small_amount_discrepancy", "source_file": "data/invoices.json", "document_type": "invoice", "notes": "Within P-009 tolerance. Must not HOLD."},
    {"case_id": "FIX-INV-013", "category": "P", "invoice_id": "INV-013", "expected_error": ["material_amount_mismatch"], "expected_action": "HOLD", "planted_error": "material_amount_mismatch", "source_file": "data/invoices.json", "document_type": "invoice", "notes": "Tax above pretax PO."},
    {"case_id": "FIX-INV-014", "category": "Z", "invoice_id": "INV-014", "expected_error": ["goods_not_received"], "expected_action": "HOLD", "planted_error": "goods_not_received", "source_file": "data/invoices.json", "document_type": "invoice", "notes": "PO-114 has no GR."},
    {"case_id": "FIX-INV-015", "category": "W", "invoice_id": "INV-015", "expected_error": ["goods_not_received"], "expected_action": "HOLD", "planted_error": "goods_not_received", "source_file": "data/invoices.json", "document_type": "invoice", "notes": "GR not received."},
    {"case_id": "FIX-INV-016", "category": "Y", "invoice_id": "INV-016", "expected_error": ["missing_po"], "expected_action": "HOLD", "planted_error": "missing_po", "source_file": "data/invoices.json", "document_type": "invoice", "notes": "No PO."},
    {"case_id": "FIX-INV-017", "category": "I", "invoice_id": "INV-017", "expected_error": ["vendor_mismatch"], "expected_action": "APPROVE", "planted_error": "vendor_mismatch", "source_file": "data/invoices.json", "document_type": "invoice", "notes": "Acme Supply Co. alias with CASE-001."},
    {"case_id": "FIX-INV-018", "category": "A", "invoice_id": "INV-018", "expected_error": ["duplicate"], "expected_action": "HOLD", "planted_error": "duplicate", "source_file": "data/invoices.json", "document_type": "invoice", "notes": "Duplicate of INV-010 Notion NL-INV-088421. Not the demo Dell invoice."},
    {"case_id": "FIX-INV-019", "category": "X", "invoice_id": "INV-019", "expected_error": ["partial_receipt"], "expected_action": "HOLD", "planted_error": "partial_receipt", "source_file": "data/invoices.json", "document_type": "invoice", "notes": "4 of 10 received."},
    {"case_id": "FIX-INV-020", "category": "AH", "invoice_id": "INV-020", "expected_error": ["po_not_approved"], "expected_action": "HOLD", "planted_error": "po_not_approved", "source_file": "data/invoices.json", "document_type": "invoice", "notes": "PO-120 pending."},
]

HOLDOUT_AP_CASES: list[dict[str, Any]] = [
    {"case_id": "HO-AP-001", "category": "X", "invoice_id": "INV-HO-QTY", "expected_error": ["partial_receipt"], "expected_action": "HOLD", "planted_error": "partial_receipt", "source_file": "discrepancy/holdout_catalog.py", "document_type": "invoice", "notes": "PO 240 / GR 217 / invoice 240."},
    {"case_id": "HO-AP-002", "category": "T", "invoice_id": "INV-HO-PRICE", "expected_error": ["material_amount_mismatch"], "expected_action": "HOLD", "planted_error": "material_amount_mismatch", "source_file": "discrepancy/holdout_catalog.py", "document_type": "invoice", "notes": "Invoice $15,478 vs PO $14,200."},
    {"case_id": "HO-AP-003", "category": "Z", "invoice_id": "INV-HO-NOGR", "expected_error": ["goods_not_received"], "expected_action": "HOLD", "planted_error": "goods_not_received", "source_file": "discrepancy/holdout_catalog.py", "document_type": "invoice", "notes": "Missing GR."},
    {"case_id": "HO-AP-004A", "category": "A", "invoice_id": "INV-HO-DUP-A", "expected_error": ["duplicate"], "expected_action": "HOLD", "planted_error": "duplicate", "source_file": "discrepancy/holdout_catalog.py", "document_type": "invoice", "notes": "HX-55190 twice."},
    {"case_id": "HO-AP-005A", "category": "B", "invoice_id": "INV-HO-NORM-A", "expected_error": ["duplicate"], "expected_action": "HOLD", "planted_error": "duplicate", "source_file": "discrepancy/holdout_catalog.py", "document_type": "invoice", "notes": "ABC/23781 vs ABC-23781 after alphanumeric normalization."},
    {"case_id": "HO-AP-006", "category": "AH", "invoice_id": "INV-HO-LIMIT", "expected_error": ["approval_limit_exceeded"], "expected_action": "HOLD", "planted_error": "approval_limit_exceeded", "source_file": "discrepancy/holdout_catalog.py", "document_type": "invoice", "notes": "PO $72k exceeds $20k limit."},
    {"case_id": "HO-AP-008", "category": "W", "invoice_id": "INV-HO-HELD", "expected_error": ["goods_not_received"], "expected_action": "HOLD", "planted_error": "goods_not_received", "source_file": "discrepancy/holdout_catalog.py", "document_type": "invoice", "notes": "Held invoice must not enter payment pool."},
]

ADVERSARIAL_CLASSIFY: list[dict[str, Any]] = [
    {
        "case_id": "ADV-QUOTE-LAYOUT",
        "category": "D",
        "source_file": "evals/invoice_error_detection.py",
        "document_type": "quote",
        "planted_error": "quote_as_invoice",
        "expected_error": ["quote"],
        "expected_action": "NO_AP",
        "expected_class": "quote",
        "subject": "Pricing for additional standing desks",
        "filename": "desks.pdf",
        "text": (
            "Acme Supplies\nVendor: Acme Supplies\n"
            "Standing desk    qty 10    1,245.00\nMonitor    qty 5    400.00\n"
            "Total                              12,450.00\n"
            "Valid through: 2026-10-01\nThis is a quote, not a request for payment.\n"
        ),
        "notes": "Quote with vendor, lines, total, valid-through. Must not become an invoice.",
    },
    {
        "case_id": "ADV-ESTIMATE",
        "category": "D",
        "source_file": "evals/invoice_error_detection.py",
        "document_type": "quote",
        "planted_error": "estimate_as_invoice",
        "expected_error": ["quote"],
        "expected_action": "NO_AP",
        "expected_class": "quote",
        "subject": "Estimate EST-4410",
        "filename": "estimate.pdf",
        "text": "ESTIMATE EST-4410\nVendor: Acme Supplies\nTotal: 12450.00\nEstimate valid until 2026-10-15\n",
        "notes": "Estimate document.",
    },
    {
        "case_id": "ADV-PO-LAYOUT",
        "category": "G",
        "source_file": "evals/invoice_error_detection.py",
        "document_type": "purchase_order",
        "planted_error": "purchase_order_as_invoice",
        "expected_error": ["purchase_order"],
        "expected_action": "NO_AP",
        "expected_class": "purchase_order",
        "subject": "PO-108 issued",
        "filename": "PO-108.pdf",
        "text": "PURCHASE ORDER PO-108\nVendor: Slack Technologies\nQty 50  Unit 87.50\nAuthorized amount: 4375.00\nThis purchase order is not an invoice.\n",
        "notes": "PO with supplier, quantities, prices, PO number, total.",
    },
    {
        "case_id": "ADV-RECEIPT-PAID",
        "category": "E",
        "source_file": "evals/invoice_error_detection.py",
        "document_type": "receipt",
        "planted_error": "receipt_as_invoice",
        "expected_error": ["receipt"],
        "expected_action": "NO_AP",
        "expected_class": "receipt",
        "subject": "Your receipt",
        "filename": "receipt.pdf",
        "text": "RECEIPT\nVendor: Office Depot\nDate: 2026-09-12\nAmount: 42.10\nPaid. Thank you.\nThis is a receipt, not an invoice.\n",
        "notes": "Paid receipt with vendor/amount/date.",
    },
    {
        "case_id": "ADV-BANK-CHARGE",
        "category": "H",
        "source_file": "evals/invoice_error_detection.py",
        "document_type": "bank_charge",
        "planted_error": "bank_charge_as_invoice",
        "expected_error": ["not_invoice"],
        "expected_action": "NO_AP",
        "expected_class": "not_invoice",
        "subject": "Card charge posted",
        "filename": "",
        "text": "Chase Bank card charge\nMerchant: OFFICE DEPOT\nAmount: $3,280.00\nPosted to your account 2026-09-10.\nThis is a bank transaction, not a vendor invoice.\n",
        "notes": "Bank/card charge must not create AP.",
    },
    {
        "case_id": "ADV-SHIPPING-NOTICE",
        "category": "G",
        "source_file": "evals/invoice_error_detection.py",
        "document_type": "shipping_notice",
        "planted_error": "shipping_notice_as_invoice",
        "expected_error": ["not_invoice"],
        "expected_action": "NO_AP",
        "expected_class": "not_invoice",
        "subject": "ASN for PO-101",
        "filename": "asn.pdf",
        "text": "Advance shipping notice\nPacking list for PO-101\nAcme Supplies\n15 cartons shipped.\nThis shipping notice is not an invoice.\n",
        "notes": "Shipping notice / packing list.",
    },
    {
        "case_id": "ADV-CREDIT-MEMO",
        "category": "AC",
        "source_file": "evals/invoice_error_detection.py",
        "document_type": "credit_memo",
        "planted_error": "credit_memo_as_invoice",
        "expected_error": ["not_invoice"],
        "expected_action": "NO_AP",
        "expected_class": "not_invoice",
        "subject": "Credit memo CM-100",
        "filename": "cm.pdf",
        "text": "Credit Memo CM-100\nVendor: Acme Supplies\nCredit note for returned goods $200.00\nThis is not an invoice.\n",
        "notes": "Credit memo must not become a payable invoice.",
    },
    {
        "case_id": "ADV-CLEAN-INVOICE",
        "category": "AS",
        "source_file": "evals/invoice_error_detection.py",
        "document_type": "invoice",
        "planted_error": None,
        "expected_error": [],
        "expected_action": "CLASSIFY_INVOICE",
        "expected_class": "invoice",
        "subject": "Invoice ACM-ADV-1",
        "filename": "inv.pdf",
        "text": "INVOICE\nInvoice number: ACM-ADV-1\nInvoice date: 2026-09-08\nVendor: Acme Supplies\nAmount due: 12450.00\nPO: PO-101\n",
        "notes": "Clean control invoice for classification.",
    },
    {
        "case_id": "RT-QUOTE-PROPOSAL",
        "category": "D",
        "source_file": "evals/invoice_error_detection.py",
        "document_type": "quote",
        "planted_error": "quote_as_invoice",
        "expected_error": ["quote"],
        "expected_action": "NO_AP",
        "expected_class": "quote",
        "subject": "Proposal for Q4 monitors",
        "filename": "proposal.pdf",
        "text": "PROPOSAL\nVendor: Dell Technologies\n24 monitors @ 410.00\nTotal 9,840.00\nValid through 2026-11-30\nThis is a quote pending a purchase order.\n",
        "notes": "Independent quote family: proposal + valid through. Must not become AP.",
    },
    {
        "case_id": "RT-PO-ISSUED",
        "category": "G",
        "source_file": "evals/invoice_error_detection.py",
        "document_type": "purchase_order",
        "planted_error": "purchase_order_as_invoice",
        "expected_error": ["purchase_order"],
        "expected_action": "NO_AP",
        "expected_class": "purchase_order",
        "subject": "PO-221 issued to Northline",
        "filename": "PO-221.pdf",
        "text": "PURCHASE ORDER PO-221\nSupplier: Northline Fabrication\nQty 8  Unit 625.00\nAuthorized amount: 5000.00\nThis is a PO, not a vendor invoice.\n",
        "notes": "Independent PO family.",
    },
    {
        "case_id": "RT-RECEIPT-STAMP",
        "category": "E",
        "source_file": "evals/invoice_error_detection.py",
        "document_type": "receipt",
        "planted_error": "receipt_as_invoice",
        "expected_error": ["receipt"],
        "expected_action": "NO_AP",
        "expected_class": "receipt",
        "subject": "Lyft receipt downtown",
        "filename": "lyft.pdf",
        "text": "RECEIPT #L-88\nMerchant: Lyft\nDate: 2026-09-14\nAmount: 28.40\nPaid. Thank you.\nThis is a receipt.\n",
        "notes": "Independent paid-receipt family.",
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _row(
    case: dict,
    *,
    detected_error: Any,
    actual_action: Any,
    correct: bool,
    false_positive: bool,
    false_negative: bool,
    agent_path: str,
    evidence_used: list[str],
    notes: str = "",
    extras: dict | None = None,
) -> dict:
    planted = case.get("planted_error")
    expected_error = case.get("expected_error")
    payload = {
        "case_id": case["case_id"],
        "category": case.get("category"),
        "source_file": case.get("source_file"),
        "document_type": case.get("document_type"),
        "planted_error": planted,
        "expected_error": expected_error,
        "expected_action": case.get("expected_action"),
        "detected_error": detected_error,
        "actual_action": actual_action,
        "correct": bool(correct),
        "false_positive": bool(false_positive),
        "false_negative": bool(false_negative),
        "agent_path": agent_path,
        "evidence_used": evidence_used,
        "notes": notes or case.get("notes") or "",
    }
    if extras:
        payload.update(extras)
    return payload


def _score_hold(case: dict, decision: str, actual_exc: list[str]) -> tuple[bool, bool, bool]:
    expected = case["expected_action"]
    planted = bool(case.get("planted_error"))
    hold_expected = expected == "HOLD"
    flagged = decision == "HOLD"
    missing = [item for item in (case.get("expected_error") or []) if item not in actual_exc]
    extra_blockers = [
        item
        for item in actual_exc
        if item not in (case.get("expected_error") or [])
        and item not in {"unusual_timing", "small_amount_discrepancy", "vendor_mismatch"}
        and expected == "APPROVE"
    ]
    correct = decision == expected and not missing
    if expected == "APPROVE" and extra_blockers:
        correct = False
    false_positive = (not planted and flagged) or (expected == "APPROVE" and flagged)
    false_negative = planted and hold_expected and (decision == "APPROVE" or bool(missing))
    return correct, false_positive, false_negative


def _run_ap_case(case: dict) -> dict:
    invoice_id = case["invoice_id"]
    result = decide_ap(invoice_id, live=False, featured=set())
    evidence = collect_case_evidence(invoice_id)
    actual_exc = list(exception_types_for(invoice_id))
    eligible = policy_eligible_for_pool(invoice_id)
    expected_eligible = case.get("pay_eligible")
    pay_ok = True if expected_eligible is None else eligible is expected_eligible
    correct, fp, fn = _score_hold(case, result.decision, actual_exc)
    if expected_eligible is False and eligible:
        correct = False
        fp = True
        notes = (case.get("notes") or "") + " Payment scheduler still eligible."
    else:
        notes = case.get("notes") or ""
    if case.get("alias_required"):
        alias = vendor_alias_established(evidence)
        if not alias and result.decision == "APPROVE":
            notes += " Alias not established but APPROVE (safety-net may still allow)."
        extras = {"alias_established": alias}
    else:
        extras = {}
    extras.update({"pay_eligible": eligible, "pay_ok": pay_ok, "invoice_id": invoice_id})
    return _row(
        case,
        detected_error=actual_exc,
        actual_action=result.decision,
        correct=correct and pay_ok,
        false_positive=fp,
        false_negative=fn,
        agent_path="email/ap.prepare → Kernel decide_ap(live=False) → pay.schedule/policy_eligible_for_pool",
        evidence_used=[invoice_id, *(evidence.duplicate_invoice_ids or [])],
        notes=notes,
        extras=extras,
    )


def _email_row(message_id: str) -> dict | None:
    from invoice_ingestion import extract as invoice_extract

    path = invoice_extract.INGESTION_DIR / "emails.json"
    if not path.exists():
        return None
    rows = json.loads(path.read_text())
    return next((item for item in rows if item.get("message_id") == message_id), None)


def _run_ingest_case(case: dict) -> dict:
    row = _email_row(case["message_id"])
    if row is None:
        return _row(
            case,
            detected_error="missing_email",
            actual_action="ERROR",
            correct=False,
            false_positive=False,
            false_negative=True,
            agent_path="email.invoice → classify_text",
            evidence_used=[case["message_id"]],
            notes="emails.json missing this message",
        )
    attachments = row.get("attachments") or []
    text = attachments[0]["text"] if attachments else row.get("body", "")
    filename = attachments[0].get("filename", "") if attachments else ""
    actual, why = classify_text(text, subject=row.get("subject", ""), filename=filename)
    expected = case["expected_class"]
    correct = actual == expected
    planted = bool(case.get("planted_error"))
    became_invoice = actual == "invoice"
    fp = planted and became_invoice and expected != "invoice"
    fn = planted and not correct and not became_invoice
    return _row(
        case,
        detected_error=actual,
        actual_action=actual,
        correct=correct,
        false_positive=fp,
        false_negative=fn,
        agent_path="email.invoice → invoice_ingestion.interpret.classify_text",
        evidence_used=[case["message_id"]],
        notes=f"{case.get('notes','')} reason={why}",
        extras={"classification_reason": why},
    )


def _run_classify_text_case(case: dict) -> dict:
    actual, why = classify_text(case["text"], subject=case.get("subject", ""), filename=case.get("filename", ""))
    expected = case["expected_class"]
    correct = actual == expected
    planted = bool(case.get("planted_error"))
    became_invoice = actual == "invoice" and expected != "invoice"
    return _row(
        case,
        detected_error=actual,
        actual_action=actual,
        correct=correct,
        false_positive=became_invoice,
        false_negative=planted and not correct and not became_invoice,
        agent_path="email.invoice → classify_text",
        evidence_used=[],
        notes=f"{case.get('notes','')} reason={why}",
        extras={"classification_reason": why},
    )


def _run_inbox_suite() -> list[dict]:
    from inbox.fixtures import (
        spec_business_duplicate,
        spec_clean_attachment,
        spec_credit_memo,
        spec_goods_receipt,
        spec_no_po,
        spec_payment,
        spec_price_mismatch,
        spec_purchase_order,
        spec_quote,
        spec_statement,
    )
    from inbox.workflow import handoff
    from invoice_ingestion.adapter import reset_ingested_invoices
    from tools import clear_runtime_invoices, reset_runtime_invoices

    reset_runtime_invoices()
    reset_ingested_invoices()
    clear_runtime_invoices()
    rows = []

    def one(spec_fn, case: dict, *, check):
        reset_ingested_invoices()
        result = spec_fn() if callable(spec_fn) and spec_fn.__name__.startswith("spec_") else spec_fn
        if callable(spec_fn):
            result = handoff(spec_fn(), persist=False)
        ok, detected, action, fp, fn, evidence = check(result)
        rows.append(
            _row(
                case,
                detected_error=detected,
                actual_action=action,
                correct=ok,
                false_positive=fp,
                false_negative=fn,
                agent_path="inbox.handoff → classify_message → Kernel AP overlay",
                evidence_used=evidence,
            )
        )

    one(
        spec_clean_attachment,
        {
            "case_id": "INBOX-CLEAN",
            "category": "AS",
            "source_file": "inbox/fixtures.py:spec_clean_attachment",
            "document_type": "invoice",
            "planted_error": None,
            "expected_error": [],
            "expected_action": "CREATE_AP",
            "notes": "Clean attachment creates one canonical invoice and matches.",
        },
        check=lambda r: (
            bool(r.invoice_id) and r.receiver.dispatch.match_status == "MATCHED" and not r.receiver.dispatch.ready_for_payment,
            r.receiver.dispatch.match_status,
            r.receiver.classification.classification,
            False,
            False,
            [r.invoice_id or "", r.trace.attachment_hashes[0] if r.trace.attachment_hashes else ""],
        ),
    )
    one(
        spec_price_mismatch,
        {
            "case_id": "INBOX-PRICE",
            "category": "T",
            "source_file": "inbox/fixtures.py:spec_price_mismatch",
            "document_type": "invoice",
            "planted_error": "material_amount_mismatch",
            "expected_error": ["material_amount_mismatch"],
            "expected_action": "HOLD",
            "notes": "Office Depot $5000 vs PO-104.",
        },
        check=lambda r: (
            r.invoice_id is not None
            and "material_amount_mismatch" in exception_types_for(r.invoice_id)
            and r.receiver.dispatch.match_status == "BLOCKED",
            exception_types_for(r.invoice_id) if r.invoice_id else [],
            r.receiver.dispatch.match_status,
            False,
            r.invoice_id is None or "material_amount_mismatch" not in exception_types_for(r.invoice_id),
            [r.invoice_id or ""],
        ),
    )
    one(
        spec_no_po,
        {
            "case_id": "INBOX-NO-PO",
            "category": "Y",
            "source_file": "inbox/fixtures.py:spec_no_po",
            "document_type": "invoice",
            "planted_error": "missing_po",
            "expected_error": ["missing_po"],
            "expected_action": "HOLD",
            "notes": "Datadog body invoice with no PO.",
        },
        check=lambda r: (
            r.invoice_id is not None and "missing_po" in exception_types_for(r.invoice_id) and not r.receiver.dispatch.ready_for_payment,
            exception_types_for(r.invoice_id) if r.invoice_id else [],
            r.receiver.dispatch.match_status,
            False,
            r.invoice_id is None or "missing_po" not in exception_types_for(r.invoice_id),
            [r.invoice_id or ""],
        ),
    )
    one(
        spec_quote,
        {
            "case_id": "INBOX-QUOTE",
            "category": "D",
            "source_file": "inbox/fixtures.py:spec_quote",
            "document_type": "quote",
            "planted_error": "quote_as_invoice",
            "expected_error": ["quote"],
            "expected_action": "NO_AP",
            "notes": "Quote with invoice-ready catalog language.",
        },
        check=lambda r: (
            r.invoice_id is None and r.receiver.classification.classification == "CONTRACT_OR_QUOTE",
            r.receiver.classification.classification,
            r.receiver.classification.selected_action,
            r.invoice_id is not None,
            r.invoice_id is None and r.receiver.classification.classification != "CONTRACT_OR_QUOTE",
            [],
        ),
    )
    one(
        spec_purchase_order,
        {
            "case_id": "INBOX-PO",
            "category": "G",
            "source_file": "inbox/fixtures.py:spec_purchase_order",
            "document_type": "purchase_order",
            "planted_error": "purchase_order_as_invoice",
            "expected_error": ["purchase_order"],
            "expected_action": "NO_AP",
            "notes": "Purchase order must not create AP.",
        },
        check=lambda r: (
            r.invoice_id is None and r.receiver.classification.classification == "PURCHASE_ORDER",
            r.receiver.classification.classification,
            r.receiver.classification.selected_action,
            r.invoice_id is not None,
            r.invoice_id is None and r.receiver.classification.classification != "PURCHASE_ORDER",
            [],
        ),
    )
    one(
        spec_goods_receipt,
        {
            "case_id": "INBOX-GR",
            "category": "E",
            "source_file": "inbox/fixtures.py:spec_goods_receipt",
            "document_type": "goods_receipt",
            "planted_error": "receipt_as_invoice",
            "expected_error": ["goods_receipt"],
            "expected_action": "NO_AP",
            "notes": "Goods receipt routes without creating invoice.",
        },
        check=lambda r: (
            r.invoice_id is None and r.receiver.classification.classification == "GOODS_RECEIPT",
            r.receiver.classification.classification,
            r.receiver.classification.selected_action,
            r.invoice_id is not None,
            False,
            [],
        ),
    )
    one(
        spec_statement,
        {
            "case_id": "INBOX-STMT",
            "category": "F",
            "source_file": "inbox/fixtures.py:spec_statement",
            "document_type": "statement",
            "planted_error": "statement_as_invoice",
            "expected_error": ["statement"],
            "expected_action": "NO_AP",
            "notes": "Vendor statement.",
        },
        check=lambda r: (
            r.invoice_id is None and r.receiver.classification.classification == "VENDOR_STATEMENT",
            r.receiver.classification.classification,
            r.receiver.classification.selected_action,
            r.invoice_id is not None,
            False,
            [],
        ),
    )
    one(
        spec_payment,
        {
            "case_id": "INBOX-PAY-CONF",
            "category": "AB",
            "source_file": "inbox/fixtures.py:spec_payment",
            "document_type": "payment_confirmation",
            "planted_error": "payment_confirmation_as_invoice",
            "expected_error": ["payment_confirmation"],
            "expected_action": "NO_AP",
            "notes": "Payment confirmation is not an unpaid invoice.",
        },
        check=lambda r: (
            r.invoice_id is None and r.receiver.classification.classification == "PAYMENT_CONFIRMATION",
            r.receiver.classification.classification,
            r.receiver.classification.selected_action,
            r.invoice_id is not None,
            False,
            [],
        ),
    )
    one(
        spec_credit_memo,
        {
            "case_id": "INBOX-CREDIT",
            "category": "AC",
            "source_file": "inbox/fixtures.py:spec_credit_memo",
            "document_type": "credit_memo",
            "planted_error": "credit_memo_as_invoice",
            "expected_error": ["credit_memo"],
            "expected_action": "NO_AP",
            "notes": "Credit memo is not a payable invoice.",
        },
        check=lambda r: (
            r.invoice_id is None and r.receiver.classification.classification == "CREDIT_MEMO",
            r.receiver.classification.classification,
            r.receiver.classification.selected_action,
            r.invoice_id is not None,
            False,
            [],
        ),
    )

    reset_ingested_invoices()
    first = handoff(spec_clean_attachment(), persist=False)
    second = handoff(spec_business_duplicate(), persist=False)
    dup_ok = second.final_status == "BUSINESS_DUPLICATE" and first.invoice_id and (
        second.receiver.dispatch.duplicate_of == first.invoice_id or second.invoice_id == first.invoice_id
    )
    rows.append(
        _row(
            {
                "case_id": "INBOX-DUP-BUSINESS",
                "category": "A",
                "source_file": "inbox/fixtures.py:spec_business_duplicate",
                "document_type": "invoice",
                "planted_error": "duplicate",
                "expected_error": ["duplicate"],
                "expected_action": "HOLD",
                "notes": "Same invoice number + vendor, different filename. Must not create second payable.",
            },
            detected_error=second.final_status,
            actual_action=second.final_status,
            correct=dup_ok,
            false_positive=False,
            false_negative=not dup_ok,
            agent_path="inbox.handoff → existing_ap_match → Kernel overlay",
            evidence_used=[first.invoice_id or "", second.invoice_id or ""],
        )
    )
    return rows


def _run_math_cases() -> list[dict]:
    rows = []
    ok_line = InvoiceCandidate(
        source_type="email",
        source_id="MATH-OK",
        vendor="Acme Supplies",
        vendor_invoice_number="M-1",
        invoice_date="2026-09-08",
        currency="USD",
        subtotal=100.0,
        tax=10.0,
        amount=110.0,
        line_items=[
            InvoiceLineItem(description="A", quantity=2, unit_price=40.0, amount=80.0),
            InvoiceLineItem(description="B", quantity=1, unit_price=20.0, amount=20.0),
        ],
    )
    bad_total = ok_line.model_copy(update={"amount": 200.0})
    bad_lines = ok_line.model_copy(
        update={
            "source_id": "MATH-LINES",
            "line_items": [
                InvoiceLineItem(description="A", quantity=2, unit_price=40.0, amount=80.0),
                InvoiceLineItem(description="B", quantity=1, unit_price=50.0, amount=50.0),
            ],
        }
    )
    cents_candidate = InvoiceCandidate(
        source_type="email",
        source_id="MATH-CENTS",
        vendor="Acme Supplies",
        vendor_invoice_number="M-C",
        invoice_date="2026-09-08",
        currency="USD",
        amount=12450.0,
    )
    from invoice_ingestion.interpret import parse_money
    from inbox.normalize import dollars_to_cents

    cases = [
        ("MATH-TOTALS-OK", True, validate_candidate(ok_line).status == "valid" and amounts_consistent(100.0, 10.0, 110.0), "AS", None, "Clean subtotal+tax=total."),
        ("MATH-TOTALS-BAD", True, "inconsistent_totals" in validate_candidate(bad_total).errors, "P", "inconsistent_totals", "Subtotal+tax != total must reject."),
        ("MATH-LINE-SUM", True, "line_item_sum_mismatch" in validate_candidate(bad_lines).errors, "Q", "line_item_sum_mismatch", "Line items 80+50 != subtotal 100."),
        ("MATH-CENTS", True, parse_money("12,450.00") == 12450.0 and dollars_to_cents(12450.0) == 1_245_000, "AS", None, "Cents vs dollars: $12,450 is 1,245,000 cents."),
        ("MATH-CENTS-CAND", True, cents_candidate.amount == 12450.0, "AS", None, "Invoice amount stays in dollars."),
    ]
    for case_id, planted, ok, category, expected_err, notes in cases:
        rows.append(
            _row(
                {
                    "case_id": case_id,
                    "category": category,
                    "source_file": "invoice_ingestion/validate.py",
                    "document_type": "invoice",
                    "planted_error": expected_err,
                    "expected_error": [expected_err] if expected_err else [],
                    "expected_action": "REJECT" if expected_err else "ACCEPT",
                    "notes": notes,
                },
                detected_error=ok,
                actual_action="PASS" if ok else "FAIL",
                correct=bool(ok),
                false_positive=False,
                false_negative=bool(expected_err) and not ok,
                agent_path="email.invoice → validate_candidate",
                evidence_used=[],
            )
        )
    return rows


def _run_identity_cases() -> list[dict]:
    from invoice_ingestion.identity import canonical_invoice_key

    key_slash = canonical_invoice_key(vendor="Holdout Vendor", vendor_invoice_number="ABC/23781")
    key_dash = canonical_invoice_key(vendor="Holdout Vendor", vendor_invoice_number="ABC-23781")
    match = existing_ap_match("Notion Labs", "NL-INV-088421")
    punct_match = existing_ap_match("Notion Labs", "NL/INV/088421")
    rows = [
        _row(
            {
                "case_id": "ID-NORM-PUNCT",
                "category": "B",
                "source_file": "invoice_ingestion/identity.py",
                "document_type": "invoice",
                "planted_error": "formatted_duplicate",
                "expected_error": ["duplicate"],
                "expected_action": "COLLAPSE",
                "notes": "ABC/23781 and ABC-23781 must share a canonical key.",
            },
            detected_error={"slash": key_slash, "dash": key_dash},
            actual_action="COLLAPSE" if key_slash == key_dash and key_slash else "DISTINCT",
            correct=bool(key_slash) and key_slash == key_dash,
            false_positive=False,
            false_negative=key_slash != key_dash,
            agent_path="email.invoice → canonical_invoice_key",
            evidence_used=[],
        ),
        _row(
            {
                "case_id": "ID-EXISTING-AP",
                "category": "A",
                "source_file": "invoice_ingestion/validate.py:existing_ap_match",
                "document_type": "invoice",
                "planted_error": "duplicate",
                "expected_error": ["duplicate"],
                "expected_action": "LINK",
                "notes": "existing_ap_match must use the same invoice-number normalization as AP matching.",
            },
            detected_error=match,
            actual_action=match or "NONE",
            correct=match == "INV-010",
            false_positive=False,
            false_negative=match != "INV-010",
            agent_path="inbox.handoff → existing_ap_match",
            evidence_used=["INV-010"],
        ),
        _row(
            {
                "case_id": "ID-EXISTING-PUNCT",
                "category": "B",
                "source_file": "invoice_ingestion/validate.py:existing_ap_match",
                "document_type": "invoice",
                "planted_error": "formatted_duplicate",
                "expected_error": ["duplicate"],
                "expected_action": "LINK",
                "notes": "NL/INV/088421 must match stored NL-INV-088421.",
            },
            detected_error=punct_match,
            actual_action=punct_match or "NONE",
            correct=punct_match == "INV-010",
            false_positive=False,
            false_negative=punct_match != "INV-010",
            agent_path="inbox.handoff → existing_ap_match",
            evidence_used=["INV-010"],
        ),
        _row(
            {
                "case_id": "ID-ALNUM",
                "category": "B",
                "source_file": "tools.py:normalize_invoice_number",
                "document_type": "invoice",
                "planted_error": None,
                "expected_error": [],
                "expected_action": "NORMALIZE",
                "notes": "Alphanumeric fold.",
            },
            detected_error=normalize_invoice_number("ABC/23781"),
            actual_action=normalize_invoice_number("ABC-23781"),
            correct=normalize_invoice_number("ABC/23781") == normalize_invoice_number("ABC-23781") == "ABC23781",
            false_positive=False,
            false_negative=False,
            agent_path="Kernel tools.normalize_invoice_number",
            evidence_used=[],
        ),
    ]
    return rows


def _run_mutations(data_root_path: Path) -> list[dict]:
    from models import Invoice
    from tools import clear_runtime_invoices, register_runtime_invoice, reset_runtime_invoices

    rows = []
    with data_root(data_root_path):
        reset_runtime_invoices()
        base = load_invoice("INV-001")
        assert base is not None
        mutations = [
            ("MUT-AMT-1", {"amount": base.amount + 1, "vendor_invoice_number": "MUT-AMT-1"}, "small_amount_discrepancy", "APPROVE", "AS", "amount +$1 is inside P-009 $300/3%"),
            ("MUT-AMT-001", {"amount": round(base.amount + 0.01, 2), "vendor_invoice_number": "MUT-AMT-001"}, "small_amount_discrepancy", "APPROVE", "AS", "amount +$0.01 inside tolerance"),
            ("MUT-AMT-400", {"amount": base.amount + 400, "vendor_invoice_number": "MUT-AMT-400"}, "material_amount_mismatch", "HOLD", "T", "amount +$400 outside P-009"),
            ("MUT-INVNUM", {"vendor_invoice_number": "ACM-2026-9999"}, [], "APPROVE", "AS", "different invoice number, same vendor/amount — legitimate similar invoice"),
            ("MUT-PO", {"po_id": "PO-999", "vendor_invoice_number": "MUT-PO-999"}, "missing_po", "HOLD", "Y", "PO number changed to missing PO"),
            ("MUT-VENDOR-SPELL", {"vendor": "Northwind Industrial", "vendor_invoice_number": "MUT-VENDOR"}, "vendor_mismatch", "HOLD", "I", "unrelated vendor without alias precedent"),
            ("MUT-DUP-SAME-NUM", {"vendor_invoice_number": base.vendor_invoice_number}, "duplicate", "HOLD", "A", "same vendor invoice number as INV-001"),
            ("MUT-QTY-PO-MISS", {"po_id": None, "vendor_invoice_number": "MUT-NOPO"}, "missing_po", "HOLD", "Y", "remove PO"),
        ]
        for case_id, updates, expected_err, expected_action, category, notes in mutations:
            clone = base.model_copy(update={"invoice_id": case_id, **updates})
            register_runtime_invoice(clone)
            result = decide_ap(case_id, live=False, featured=set())
            actual_exc = exception_types_for(case_id)
            expected_list = [expected_err] if isinstance(expected_err, str) else list(expected_err)
            missing = [item for item in expected_list if item not in actual_exc]
            correct = result.decision == expected_action and not missing
            rows.append(
                _row(
                    {
                        "case_id": case_id,
                        "category": category,
                        "source_file": "evals/invoice_error_detection.py:_run_mutations",
                        "document_type": "invoice",
                        "planted_error": expected_err if isinstance(expected_err, str) else None,
                        "expected_error": expected_list,
                        "expected_action": expected_action,
                        "notes": notes,
                    },
                    detected_error=actual_exc,
                    actual_action=result.decision,
                    correct=correct,
                    false_positive=expected_action == "APPROVE" and result.decision == "HOLD",
                    false_negative=expected_action == "HOLD" and result.decision == "APPROVE",
                    agent_path="Kernel decide_ap on mutated runtime overlay",
                    evidence_used=[case_id, "INV-001"],
                )
            )
            clear_runtime_invoices()
        reset_runtime_invoices()
    return rows


def _run_restart() -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO)
    env.pop("PYTEST_CURRENT_TEST", None)
    script = REPO / "tests" / "test_inbox_persistence.py"
    if not script.exists():
        return _row(
            {
                "case_id": "RESTART-DUP",
                "category": "A",
                "source_file": "tests/test_inbox_persistence.py",
                "document_type": "invoice",
                "planted_error": "duplicate",
                "expected_error": ["duplicate"],
                "expected_action": "HOLD",
                "notes": "Restart harness missing.",
            },
            detected_error="missing",
            actual_action="ERROR",
            correct=False,
            false_positive=False,
            false_negative=True,
            agent_path="inbox persistence subprocess",
            evidence_used=[],
        )
    # Reuse the existing fresh-process test by importing its assertions via pytest would
    # be heavier; run the helper entrypoints if present, else exec the pytest file functions.
    from inbox.fixtures import spec_clean_attachment
    from inbox.store import configure_runs_dir, persist_state, reset_inbox_state
    from inbox.workflow import handoff
    from invoice_ingestion.adapter import reset_ingested_invoices
    from tools import clear_runtime_invoices, load_invoice, reset_runtime_invoices, runtime_invoices_path

    reset_runtime_invoices()
    reset_ingested_invoices()
    reset_inbox_state()
    first = handoff(spec_clean_attachment(), persist=True)
    persist_state()
    overlay = runtime_invoices_path()
    overlay_exists = overlay.exists()
    reset_inbox_state()
    clear_runtime_invoices()
    reloaded = load_invoice(first.invoice_id) if first.invoice_id else None
    second = handoff(spec_clean_attachment(), persist=False)
    ok = (
        first.invoice_id == "ING-001"
        and overlay_exists
        and reloaded is not None
        and second.final_status in {"BUSINESS_DUPLICATE", "DUPLICATE_DELIVERY"}
        and (second.replayed is True or second.final_status == "BUSINESS_DUPLICATE")
    )
    return _row(
        {
            "case_id": "RESTART-DUP",
            "category": "A",
            "source_file": "tests/test_inbox_persistence.py",
            "document_type": "invoice",
            "planted_error": "duplicate",
            "expected_error": ["duplicate"],
            "expected_action": "HOLD",
            "notes": "Overlay reload after in-memory clear still recognizes the invoice; a fresh handoff is BUSINESS_DUPLICATE or DUPLICATE_DELIVERY.",
        },
        detected_error=second.final_status,
        actual_action=second.final_status,
        correct=ok,
        false_positive=False,
        false_negative=not ok,
        agent_path="inbox.handoff → runtime overlay persist → reload → handoff",
        evidence_used=[first.invoice_id or "", str(overlay)],
        extras={"overlay_exists": overlay_exists, "reloaded": reloaded is not None, "replayed": second.replayed},
    )


def _run_memory_cases() -> list[dict]:
    from models import Invoice, PurchaseOrder
    from tools import APCaseEvidence
    from workflow import _blocking_approve_violations

    rows = []
    with data_root(DEMO):
        evidence = collect_case_evidence("INV-021")
        alias = vendor_alias_established(evidence)
        blocked = _blocking_approve_violations(evidence)
        result = decide_ap("INV-021", live=False, featured=set())
        rows.append(
            _row(
                {
                    "case_id": "MEM-ALIAS-HELP",
                    "category": "I",
                    "source_file": "data/prior_cases.json CASE-001",
                    "document_type": "invoice",
                    "planted_error": "vendor_mismatch",
                    "expected_error": ["vendor_mismatch"],
                    "expected_action": "APPROVE",
                    "notes": "August CASE-001 makes September Acme alias payable. Memory helps.",
                },
                detected_error=exception_types_for("INV-021"),
                actual_action=result.decision,
                correct=result.decision == "APPROVE" and alias and not any("P-006" in item for item in blocked),
                false_positive=result.decision == "HOLD",
                false_negative=False,
                agent_path="ap.investigate → get_prior_cases / vendor_alias_established",
                evidence_used=["INV-021", "CASE-001"],
                extras={"alias_established": alias, "memory_effect": "helps"},
            )
        )
        fake = APCaseEvidence(
            invoice_id="INV-FAKE-MEM",
            invoice=Invoice(
                invoice_id="INV-FAKE-MEM",
                vendor="Mystery Vendor LLC",
                po_id="PO-FAKE",
                amount=100,
                invoice_date="2026-09-01",
                due_date="2026-09-30",
                vendor_invoice_number="X-1",
            ),
            purchase_order=PurchaseOrder(
                po_id="PO-FAKE",
                vendor="Mystery Vendor",
                authorized_amount=100,
                status="approved",
            ),
            vendor_exact_match=False,
            po_exists=True,
            po_approved=True,
            receipt_status="full",
            exception_types=["vendor_mismatch"],
        )
        conflict_blocked = any("P-006" in item for item in _blocking_approve_violations(fake))
        rows.append(
            _row(
                {
                    "case_id": "MEM-ALIAS-CONFLICT",
                    "category": "I",
                    "source_file": "tests/test_deterministic.py:test_unknown_vendor_without_prior_case_is_blocked",
                    "document_type": "invoice",
                    "planted_error": "vendor_mismatch",
                    "expected_error": ["vendor_mismatch"],
                    "expected_action": "HOLD",
                    "notes": "September evidence without August precedent must not copy CASE-001. Memory must not hurt.",
                },
                detected_error=["vendor_mismatch"],
                actual_action="HOLD" if conflict_blocked else "APPROVE",
                correct=conflict_blocked and not vendor_alias_established(fake),
                false_positive=False,
                false_negative=not conflict_blocked,
                agent_path="ap.investigate → vendor_alias_established",
                evidence_used=["INV-FAKE-MEM"],
                extras={"memory_effect": "refuses_blind_copy"},
            )
        )
    return rows


def _run_cross_workflow(demo_rows: list[dict]) -> list[dict]:
    held = [item for item in demo_rows if item.get("actual_action") == "HOLD"]
    approved = [item for item in demo_rows if item.get("actual_action") == "APPROVE"]
    rows = []
    dup = next((item for item in demo_rows if item["case_id"] == "DEMO-INV-006"), None)
    paid = next((item for item in demo_rows if item["case_id"] == "DEMO-INV-001"), None)
    if dup:
        rows.append(
            _row(
                {
                    "case_id": "XWF-DUP-NO-PAY",
                    "category": "A",
                    "source_file": "scheduling/cash.py + decide_ap",
                    "document_type": "invoice",
                    "planted_error": "duplicate",
                    "expected_error": ["duplicate"],
                    "expected_action": "HOLD",
                    "notes": "Duplicate INV-006 must not be payment-eligible.",
                },
                detected_error=dup.get("detected_error"),
                actual_action=dup.get("extras", {}).get("pay_eligible") if isinstance(dup.get("pay_eligible"), bool) else dup.get("detected_error"),
                correct=dup["correct"] and dup.get("pay_ok", True) is not False,
                false_positive=False,
                false_negative=not dup["correct"],
                agent_path="ap.prepare → pay.schedule",
                evidence_used=["INV-006"],
                extras={"pay_eligible": dup.get("pay_eligible")},
            )
        )
    if paid:
        rows.append(
            _row(
                {
                    "case_id": "XWF-PAID-NO-RESCHEDULE",
                    "category": "AB",
                    "source_file": "data/demo/canonical/vendor_payments.json PAY-AP-001",
                    "document_type": "invoice",
                    "planted_error": "already_paid",
                    "expected_error": ["already_paid"],
                    "expected_action": "NO_PAY",
                    "notes": "INV-001 matching APPROVE is correct; scheduler must not pay it again.",
                },
                detected_error="already_paid" if paid.get("pay_eligible") is False else "still_eligible",
                actual_action="NO_PAY" if paid.get("pay_eligible") is False else "ELIGIBLE",
                correct=paid.get("pay_eligible") is False,
                false_positive=False,
                false_negative=paid.get("pay_eligible") is not False,
                agent_path="ap.prepare APPROVE → pay.schedule policy_eligible_for_pool",
                evidence_used=["INV-001", "PAY-AP-001"],
            )
        )
    rows.append(
        _row(
            {
                "case_id": "XWF-HOLDS-NOT-ELIGIBLE",
                "category": "A",
                "source_file": "scheduling/cash.py:BLOCKING_EXCEPTIONS",
                "document_type": "invoice",
                "planted_error": "hold",
                "expected_error": ["hold"],
                "expected_action": "NO_PAY",
                "notes": "Every AP HOLD in the demo pack must be payment-ineligible.",
            },
            detected_error=len(held),
            actual_action="NO_PAY" if all(item.get("pay_eligible") is False or item.get("pay_ok") for item in held) else "LEAK",
            correct=all(not item.get("pay_eligible") for item in held if "pay_eligible" in item),
            false_positive=False,
            false_negative=any(item.get("pay_eligible") for item in held),
            agent_path="ap → pay",
            evidence_used=[item["case_id"] for item in held],
        )
    )
    _ = approved
    return rows


def _metrics(rows: list[dict]) -> dict:
    planted = [item for item in rows if item.get("planted_error")]
    clean = [item for item in rows if not item.get("planted_error")]
    flagged = [item for item in rows if item.get("false_positive") or (item.get("planted_error") and item.get("correct"))]
    detected_planted = [item for item in planted if item.get("correct") and not item.get("false_negative")]
    # Detection: planted cases that are not false negatives
    caught = [item for item in planted if not item.get("false_negative") and item.get("correct")]
    recall_den = len(planted) or 1
    precision_den = max(1, len([item for item in rows if item.get("false_positive") or (item.get("planted_error") and not item.get("false_negative"))]))
    true_flags = [item for item in planted if not item.get("false_negative")]
    all_flags = [item for item in rows if item.get("false_positive") or (item.get("planted_error") and not item.get("false_negative"))]
    by_cat: dict[str, dict[str, int]] = {}
    for item in rows:
        cat = item.get("category") or "?"
        bucket = by_cat.setdefault(cat, {"cases": 0, "correct": 0, "missed": 0, "false_positives": 0, "action_correct": 0})
        bucket["cases"] += 1
        if item.get("correct"):
            bucket["correct"] += 1
            bucket["action_correct"] += 1
        if item.get("false_negative"):
            bucket["missed"] += 1
        if item.get("false_positive"):
            bucket["false_positives"] += 1
    return {
        "TOTAL_CASES": len(rows),
        "CORRECT": sum(1 for item in rows if item.get("correct")),
        "INCORRECT": sum(1 for item in rows if not item.get("correct")),
        "FALSE_POSITIVES": sum(1 for item in rows if item.get("false_positive")),
        "FALSE_NEGATIVES": sum(1 for item in rows if item.get("false_negative")),
        "PLANTED_ERRORS": len(planted),
        "CLEAN_CASES": len(clean),
        "ERROR_DETECTION_RECALL": round(len(true_flags) / recall_den, 4),
        "ERROR_DETECTION_PRECISION": round(len(true_flags) / max(1, len(all_flags)), 4),
        "CLEAN_CASE_ACCURACY": round(sum(1 for item in clean if item.get("correct")) / max(1, len(clean)), 4),
        "ACTION_ACCURACY": round(sum(1 for item in rows if item.get("correct")) / max(1, len(rows)), 4),
        "CATEGORY": by_cat,
    }


def run_eval(*, write: bool = True, tag: str = "current") -> dict:
    rows: list[dict] = []
    with operational_dataset(DEMO, REPO / "runs" / "evals" / f"_invoice_state_{tag}"):
        demo_ap = [_run_ap_case(case) for case in DEMO_AP_CASES]
        rows.extend(demo_ap)
        rows.extend(_run_ingest_case(case) for case in DEMO_INGEST_CASES)
        rows.extend(_run_cross_workflow(demo_ap))
        rows.extend(_run_memory_cases())

    with data_root(FIXTURES):
        from tools import reset_runtime_invoices

        reset_runtime_invoices()
        rows.extend(_run_ap_case(case) for case in FIXTURE_AP_CASES)
        rows.extend(_run_identity_cases())
        rows.extend(_run_inbox_suite())
        rows.append(_run_restart())
        rows.extend(_run_math_cases())

    if HOLDOUT.exists() and (HOLDOUT / "invoices.json").exists():
        with data_root(HOLDOUT):
            rows.extend(_run_ap_case(case) for case in HOLDOUT_AP_CASES)

    rows.extend(_run_classify_text_case(case) for case in ADVERSARIAL_CLASSIFY)
    rows.extend(_run_mutations(DEMO))

    payload = {
        "tag": tag,
        "generated_at": _now(),
        "entry_point": "decide_ap(live=False) + classify_text + inbox.handoff + policy_eligible_for_pool",
        "agent_system": "15-agent office kernel (ap/email/pay), not run_ap_workflow 43-agent path",
        "metrics": _metrics(rows),
        "cases": rows,
    }
    if write:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        KERNEL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        name = "invoice_error_detection_baseline.json" if tag == "baseline" else "invoice_error_detection_results.json"
        for dest in (RESULTS_DIR / name, KERNEL_RESULTS_DIR / name):
            dest.write_text(json.dumps(payload, indent=2) + "\n")
        if tag != "baseline":
            (RESULTS_DIR / "invoice_error_detection_results.json").write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def main(argv: list[str] | None = None) -> int:
    tag = "current"
    args = list(argv or sys.argv[1:])
    if args:
        tag = args[0]
    payload = run_eval(tag=tag)
    metrics = payload["metrics"]
    print(
        json.dumps(
            {
                "tag": tag,
                "TOTAL_CASES": metrics["TOTAL_CASES"],
                "CORRECT": metrics["CORRECT"],
                "INCORRECT": metrics["INCORRECT"],
                "FALSE_POSITIVES": metrics["FALSE_POSITIVES"],
                "FALSE_NEGATIVES": metrics["FALSE_NEGATIVES"],
                "RECALL": metrics["ERROR_DETECTION_RECALL"],
                "PRECISION": metrics["ERROR_DETECTION_PRECISION"],
                "CLEAN_ACCURACY": metrics["CLEAN_CASE_ACCURACY"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

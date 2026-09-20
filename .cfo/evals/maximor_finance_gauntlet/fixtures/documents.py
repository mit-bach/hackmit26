"""Agent-visible document trap fixtures. No expected outcomes live here."""

from __future__ import annotations

DOCUMENTS = [
    {
        "case_id": "TRAP-DUP-EXACT",
        "title": "Exact duplicate invoice",
        "subject": "Invoice HE-4401",
        "filename": "he-4401.pdf",
        "text": "INVOICE\nVendor: Harbor Electric\nInvoice number: HE-4401\nInvoice date: 2026-09-04\nAmount due: 4120.00\n",
    },
    {
        "case_id": "TRAP-DUP-VISUAL",
        "title": "Visually different duplicate",
        "subject": "Harbor bill",
        "filename": "harbor_electric_invoice_HE4401_scan.png",
        "text": "INVOICE (scanned)\nHarbor Electric LLC\nInv # HE-4401\nDate 2026-09-04\nTotal due $4,120.00\n1NVOICE header from OCR\n",
    },
    {
        "case_id": "TRAP-REVISED",
        "title": "Revised invoice replacing an earlier invoice",
        "subject": "Revised invoice HE-4401-R",
        "filename": "HE-4401-R.pdf",
        "text": "INVOICE\nVendor: Harbor Electric\nInvoice number: HE-4401-R\nInvoice date: 2026-09-06\nAmount due: 4300.00\nThis invoice replaces invoice HE-4401\nRevised invoice\n",
    },
    {
        "case_id": "TRAP-VOID",
        "title": "Voided invoice",
        "subject": "VOID invoice HE-4402",
        "filename": "HE-4402-void.pdf",
        "text": "INVOICE\nVendor: Harbor Electric\nInvoice number: HE-4402\nInvoice date: 2026-09-07\nAmount due: 199.00\nVOIDED INVOICE — do not pay this invoice\n",
    },
    {
        "case_id": "TRAP-CREDIT",
        "title": "Credit memo",
        "subject": "Credit memo CM-HE-12",
        "filename": "CM-HE-12.pdf",
        "text": "Credit Memo CM-HE-12\nVendor: Harbor Electric\nCredit note for returned meter $200.00\nThis is not an invoice.\n",
    },
    {
        "case_id": "TRAP-QUOTE",
        "title": "Quote pretending to resemble an invoice",
        "subject": "Pricing",
        "filename": "quote.pdf",
        "text": "Acme Supplies\nQuote number Q-88\nQuoted amount 12450.00\nValid through: 2026-10-01\nThis is a quote, not a request for payment.\n",
    },
    {
        "case_id": "TRAP-PO",
        "title": "Purchase order without an invoice",
        "subject": "PO-101 issued",
        "filename": "PO-101.pdf",
        "text": "PURCHASE ORDER PO-101\nAcme Supplies\nAuthorized 12450.00\nThis purchase order is not an invoice.\n",
    },
    {
        "case_id": "TRAP-STATEMENT",
        "title": "Statement of already recorded invoices",
        "subject": "September statement",
        "filename": "statement.pdf",
        "text": "Account statement\nVendor: Acme Supplies\nInvoice ACM-2026-4410 12450.00 already billed\nStatement of account total 12450.00\n",
    },
    {
        "case_id": "TRAP-EMAIL-TOTAL",
        "title": "Invoice total mentioned only in an email body",
        "subject": "fyi the bill was 4120",
        "filename": "",
        "text": "Hey, Harbor said the invoice was $4,120. No attachment. Please pay them.\n",
    },
    {
        "case_id": "TRAP-MISSING-NUMBER",
        "title": "Missing invoice number",
        "subject": "Bill",
        "filename": "bill.pdf",
        "text": "INVOICE\nVendor: Harbor Electric\nInvoice date: 2026-09-08\nAmount due: 500.00\n",
    },
    {
        "case_id": "TRAP-TAX-MATH",
        "title": "Tax arithmetic error",
        "subject": "Invoice TX-9",
        "filename": "tx.pdf",
        "text": "INVOICE\nVendor: Northline Fabrication\nInvoice number: NL-TAX-9\nInvoice date: 2026-09-09\nSubtotal: 1000.00\nTax: 80.00\nAmount due: 1180.00\n",
    },
    {
        "case_id": "TRAP-BANKING",
        "title": "Incorrect banking information",
        "subject": "Invoice with wiring details",
        "filename": "wire.pdf",
        "text": "INVOICE\nVendor: Acme Supplies\nInvoice number: ACM-WIRE-1\nInvoice date: 2026-09-10\nAmount due: 500.00\nRouting number: 111000111\nAccount number: 99999999\n",
        "expected_banking": {"routing": "021000021", "account": "12345678"},
    },
    {
        "case_id": "TRAP-STRIPE-AS-REVENUE",
        "title": "Stripe payout treated as an invoice",
        "subject": "Stripe payout arrived",
        "filename": "payout.pdf",
        "text": "STRIPE PAYOUT po_1MaximorFees settled to bank $12,610. Automatic payout. This is not a vendor invoice.\n",
    },
    {
        "case_id": "TRAP-CARD-AS-INVOICE",
        "title": "Credit card charge presented as an invoice",
        "subject": "Card charge",
        "filename": "card.txt",
        "text": "Corporate card charge, not a vendor invoice. Posted to your account $88.12 at Uber.\n",
    },
]


def public_catalog() -> list[dict]:
    return [
        {
            "case_id": item["case_id"],
            "title": item["title"],
            "subject": item["subject"],
            "filename": item["filename"],
            "text": item["text"],
            "expected_banking": item.get("expected_banking"),
        }
        for item in DOCUMENTS
    ]

from __future__ import annotations

from agents import Agent

from invoice_ingestion.models import BankAgentOutput, SOURCE_AGENTS, SourceAgentOutput
from invoice_ingestion.tools import (
    find_related_invoice,
    get_bank_transaction,
    get_edi_document,
    get_email,
    get_email_attachment,
    get_employee_submission,
    get_erp_invoice,
    get_mail_document,
    get_procurement_record,
    get_vendor_portal_document,
    list_bank_transactions,
    list_edi_documents,
    list_email_candidates,
    list_employee_submissions,
    list_erp_invoice_records,
    list_mail_documents,
    list_procurement_records,
    list_vendor_portal_documents,
)
from skills import compose_instructions, skills_for

SAFETY = """
Safety rules:
- You may classify messy documents, interpret unstructured fields, and extract
  invoice data from text. You may explain ambiguous source records.
- You do not approve invoices, perform AP matching, create accruals, or decide
  payment timing.
- Never invent invoices, vendors, amounts, PO numbers, or attachments.
- Do not invent missing invoice fields. Do not do arithmetic Python already did.
- Use tools to load the specific record you were asked about.
- If the record is not an invoice, classification must not be invoice and candidate must be null.
- A bank/card charge is not an invoice. Only return a candidate when supporting invoice documentation exists.
- Prefer Python-parsed EDI fields when get_edi_document returns python_parse.
- Keep classification.reason short and factual. Do not expose hidden chain-of-thought.
""".strip()


email_agent = Agent(
    name=SOURCE_AGENTS["email"],
    instructions=compose_instructions(
        """
You inspect one AP-inbox email and its attachments.

Workflow:
1. get_email(message_id)
2. For each attachment, get_email_attachment
3. Classify each attachment. If it is an invoice, extract fields and preserve
   email provenance on the candidate.

Return SourceAgentOutput. source_id is the message_id.
""".strip(),
        skills=skills_for(SOURCE_AGENTS["email"]),
        safety=SAFETY,
    ),
    tools=[list_email_candidates, get_email, get_email_attachment],
    output_type=SourceAgentOutput,
)

erp_agent = Agent(
    name=SOURCE_AGENTS["erp"],
    instructions=compose_instructions(
        """
You normalize one ERP invoice record (NetSuite/SAP/Oracle/Workday mock) into
InvoiceCandidate. Map vendor, invoice number, dates, amounts, and PO.
Do not perform three-way matching.

Return SourceAgentOutput. source_id is the ERP record_id.
""".strip(),
        skills=skills_for(SOURCE_AGENTS["erp"]),
        safety=SAFETY,
    ),
    tools=[list_erp_invoice_records, get_erp_invoice],
    output_type=SourceAgentOutput,
)

procurement_agent = Agent(
    name=SOURCE_AGENTS["procurement"],
    instructions=compose_instructions(
        """
You inspect one Coupa/Ariba/Zip/Ramp-style procurement document.

If it is an invoice, extract fields and keep PO number, vendor id, purchase
request, and receiving info in source_context. Do not match against AP.

Return SourceAgentOutput.
""".strip(),
        skills=skills_for(SOURCE_AGENTS["procurement"]),
        safety=SAFETY,
    ),
    tools=[list_procurement_records, get_procurement_record],
    output_type=SourceAgentOutput,
)

vendor_portal_agent = Agent(
    name=SOURCE_AGENTS["vendor_portal"],
    instructions=compose_instructions(
        """
You inspect one vendor billing-portal document (AWS, Microsoft, utilities, SaaS).

Extract invoice fields from invoice PDFs/text. Preserve portal and vendor
provenance.

Return SourceAgentOutput.
""".strip(),
        skills=skills_for(SOURCE_AGENTS["vendor_portal"]),
        safety=SAFETY,
    ),
    tools=[list_vendor_portal_documents, get_vendor_portal_document],
    output_type=SourceAgentOutput,
)

employee_agent = Agent(
    name=SOURCE_AGENTS["employee_submission"],
    instructions=compose_instructions(
        """
You inspect one employee submission (upload, Slack, shared drive).

Vendor invoices may be forwarded this way. Return SourceAgentOutput.
""".strip(),
        skills=skills_for(SOURCE_AGENTS["employee_submission"]),
        safety=SAFETY,
    ),
    tools=[list_employee_submissions, get_employee_submission],
    output_type=SourceAgentOutput,
)

document_agent = Agent(
    name=SOURCE_AGENTS["document"],
    instructions=compose_instructions(
        """
You inspect one scanned mailroom/PDF document using extracted text.

Preserve filename, document hash, and page references. If the text is
unreadable, classification=unreadable.

Return SourceAgentOutput.
""".strip(),
        skills=skills_for(SOURCE_AGENTS["document"]),
        safety=SAFETY,
    ),
    tools=[list_mail_documents, get_mail_document],
    output_type=SourceAgentOutput,
)

edi_agent = Agent(
    name=SOURCE_AGENTS["edi"],
    instructions=compose_instructions(
        """
You inspect one structured EDI/XML/JSON invoice.

Call get_edi_document. If python_parse is present, copy those fields.
Only remap when Python left a field empty or flagged python_parse_error.

Return SourceAgentOutput.
""".strip(),
        skills=skills_for(SOURCE_AGENTS["edi"]),
        safety=SAFETY,
    ),
    tools=[list_edi_documents, get_edi_document],
    output_type=SourceAgentOutput,
)

bank_card_agent = Agent(
    name=SOURCE_AGENTS["bank_card"],
    instructions=compose_instructions(
        """
You inspect one bank or corporate-card transaction.

Workflow:
1. get_bank_transaction
2. find_related_invoice
3. Return BankAgentOutput. source_type is bank_card; source_id is transaction_id.
""".strip(),
        skills=skills_for(SOURCE_AGENTS["bank_card"]),
        safety=SAFETY,
    ),
    tools=[list_bank_transactions, get_bank_transaction, find_related_invoice],
    output_type=BankAgentOutput,
)

AGENTS = {
    "email": email_agent,
    "erp": erp_agent,
    "procurement": procurement_agent,
    "vendor_portal": vendor_portal_agent,
    "employee_submission": employee_agent,
    "document": document_agent,
    "edi": edi_agent,
    "bank_card": bank_card_agent,
}

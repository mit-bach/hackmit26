"""Source runners.

Unstructured sources (email, PDFs, employee uploads, portal documents, bank
discovery) may use an agent to classify and extract. Structured sources
(ERP, Coupa-style procurement, EDI) are parsed in Python and do not call
the LLM for extraction.
"""

from __future__ import annotations

from agent import run_agent
from invoice_ingestion.agents import AGENTS
from invoice_ingestion.edi import EDIParseError, parse_edi_document
from invoice_ingestion.extract import DocumentExtractionError
from invoice_ingestion.interpret import (
    interpret_document,
    interpret_email,
    interpret_employee,
    interpret_erp,
    interpret_portal,
    interpret_procurement,
    parse_invoice_text_clean,
)
from invoice_ingestion.models import (
    BankAgentOutput,
    BankDiscoveryResult,
    InvoiceCandidate,
    RecordTrace,
    SOURCE_AGENTS,
    STRUCTURED_SOURCES,
    SourceAgentOutput,
    SourceRunResult,
)
from invoice_ingestion.store import (
    find_related_invoice_records,
    list_bank_transactions,
    list_edi_documents,
    list_emails,
    list_employee_submissions,
    list_erp_invoice_records,
    list_mail_documents,
    list_procurement_records,
    list_vendor_portal_documents,
)
from skills.loader import usage_from_agent

MAX_SOURCE_TURNS = 6


def _extraction_method(source_type: str) -> str:
    return "deterministic" if source_type in STRUCTURED_SOURCES else "unstructured"


def _new_source_run(source_type: str) -> SourceRunResult:
    agent = AGENTS[source_type]
    return SourceRunResult(
        source_type=source_type,
        agent=SOURCE_AGENTS[source_type],
        skill_usage=usage_from_agent(agent),
        extraction_method=_extraction_method(source_type),
    )


def _extracted_fields(candidate: InvoiceCandidate | None) -> dict:
    if candidate is None:
        return {}
    return {
        "vendor": candidate.vendor,
        "vendor_invoice_number": candidate.vendor_invoice_number,
        "invoice_date": candidate.invoice_date,
        "due_date": candidate.due_date,
        "amount": candidate.amount,
        "currency": candidate.currency,
        "po_id": candidate.po_id,
        "document_hash": candidate.document_hash,
    }


def _trace(
    source_type: str,
    source_id: str,
    *,
    classification: str | None = None,
    reason: str | None = None,
    candidate: InvoiceCandidate | None = None,
    error: str | None = None,
    warnings: list[str] | None = None,
) -> RecordTrace:
    return RecordTrace(
        source_type=source_type,
        source_id=source_id,
        agent=SOURCE_AGENTS[source_type],
        classification=classification,
        reason=reason,
        candidate_produced=candidate is not None,
        extracted_fields=_extracted_fields(candidate),
        evidence=list(candidate.evidence) if candidate else [],
        warnings=warnings or [],
        error=error,
        source_ref=f"{source_type}:{source_id}",
        extraction_method=_extraction_method(source_type),
    )


def _candidate_from_agent(output: SourceAgentOutput, fallback: InvoiceCandidate | None) -> InvoiceCandidate | None:
    if output.classification != "invoice":
        return None
    candidate = output.candidate
    if candidate is None:
        return fallback
    return candidate.model_copy(
        update={
            "classification": output.classification,
            "classification_reason": output.reason,
            "extraction_confidence": output.confidence,
        }
    )


def _run_llm(source_type: str, source_id: str, prompt: str):
    return run_agent(AGENTS[source_type], prompt, max_turns=MAX_SOURCE_TURNS)


def _process_record(
    source_type: str,
    source_id: str,
    prompt: str,
    deterministic: tuple[str, str, list[InvoiceCandidate]],
    use_llm: bool,
) -> tuple[str, str, list[InvoiceCandidate], list[str], str | None]:
    classification, reason, candidates = deterministic
    warnings: list[str] = []
    error = None
    if not use_llm:
        return classification, reason, candidates, warnings, error
    try:
        output = _run_llm(source_type, source_id, prompt)
        if not isinstance(output, SourceAgentOutput):
            raise TypeError(f"{SOURCE_AGENTS[source_type]} returned {type(output).__name__}")
        classification = output.classification
        reason = output.reason
        fallback = candidates[0] if candidates else None
        candidate = _candidate_from_agent(output, fallback)
        candidates = [candidate] if candidate is not None else []
        warnings.extend(output.warnings)
    except Exception as exc:
        error = f"agent_failed:{exc}"
        warnings.append(error)
        warnings.append("used_deterministic_fallback")
    return classification, reason, candidates, warnings, error


def run_email_source(period: str, use_llm: bool = False) -> SourceRunResult:
    source_type = "email"
    result = _new_source_run(source_type)
    rows = list_emails(period)
    result.records_checked = len(rows)
    for row in rows:
        source_id = str(row.get("message_id"))
        try:
            deterministic = interpret_email(row)
            classification, reason, candidates, warnings, error = _process_record(
                source_type,
                source_id,
                (
                    f"Inspect AP-inbox email {source_id} for period {period}. "
                    "Classify attachments and extract invoice fields if present."
                ),
                deterministic,
                use_llm,
            )
        except DocumentExtractionError as exc:
            classification, reason, candidates, warnings, error = (
                "unreadable",
                str(exc),
                [],
                [],
                str(exc),
            )
        result.traces.append(
            _trace(
                source_type,
                source_id,
                classification=classification,
                reason=reason,
                candidate=candidates[0] if candidates else None,
                error=error,
                warnings=warnings,
            )
        )
        result.candidates.extend(candidates)
    result.invoices_found = len(result.candidates)
    result.non_invoices = result.records_checked - result.invoices_found
    return result


def run_erp_source(period: str, use_llm: bool = False) -> SourceRunResult:
    """Normalize structured ERP records in Python. The LLM is not used."""
    source_type = "erp"
    result = _new_source_run(source_type)
    rows = list_erp_invoice_records(period)
    result.records_checked = len(rows)
    for row in rows:
        source_id = str(row.get("record_id"))
        deterministic = interpret_erp(row)
        classification, reason, candidates, warnings, error = _process_record(
            source_type,
            source_id,
            f"Normalize ERP invoice record {source_id} for period {period}.",
            deterministic,
            use_llm=False,
        )
        result.traces.append(
            _trace(
                source_type,
                source_id,
                classification=classification,
                reason=reason,
                candidate=candidates[0] if candidates else None,
                error=error,
                warnings=warnings,
            )
        )
        result.candidates.extend(candidates)
    result.invoices_found = len(result.candidates)
    result.non_invoices = result.records_checked - result.invoices_found
    return result


def run_procurement_source(period: str, use_llm: bool = False) -> SourceRunResult:
    """Map Coupa-style structured records in Python. The LLM is not used."""
    source_type = "procurement"
    result = _new_source_run(source_type)
    rows = list_procurement_records(period)
    result.records_checked = len(rows)
    for row in rows:
        source_id = str(row.get("record_id"))
        deterministic = interpret_procurement(row)
        classification, reason, candidates, warnings, error = _process_record(
            source_type,
            source_id,
            f"Inspect procurement document {source_id}. Extract only if it is an invoice.",
            deterministic,
            use_llm=False,
        )
        result.traces.append(
            _trace(
                source_type,
                source_id,
                classification=classification,
                reason=reason,
                candidate=candidates[0] if candidates else None,
                error=error,
                warnings=warnings,
            )
        )
        result.candidates.extend(candidates)
    result.invoices_found = len(result.candidates)
    result.non_invoices = result.records_checked - result.invoices_found
    return result


def run_vendor_portal_source(period: str, use_llm: bool = False) -> SourceRunResult:
    source_type = "vendor_portal"
    result = _new_source_run(source_type)
    rows = list_vendor_portal_documents(period)
    result.records_checked = len(rows)
    for row in rows:
        source_id = str(row.get("document_id"))
        try:
            deterministic = interpret_portal(row)
            classification, reason, candidates, warnings, error = _process_record(
                source_type,
                source_id,
                f"Inspect vendor portal document {source_id}. Statements are not invoices.",
                deterministic,
                use_llm,
            )
        except DocumentExtractionError as exc:
            classification, reason, candidates, warnings, error = (
                "unreadable",
                str(exc),
                [],
                [],
                str(exc),
            )
        result.traces.append(
            _trace(
                source_type,
                source_id,
                classification=classification,
                reason=reason,
                candidate=candidates[0] if candidates else None,
                error=error,
                warnings=warnings,
            )
        )
        result.candidates.extend(candidates)
    result.invoices_found = len(result.candidates)
    result.non_invoices = result.records_checked - result.invoices_found
    return result


def run_employee_source(period: str, use_llm: bool = False) -> SourceRunResult:
    source_type = "employee_submission"
    result = _new_source_run(source_type)
    rows = list_employee_submissions(period)
    result.records_checked = len(rows)
    for row in rows:
        source_id = str(row.get("submission_id"))
        try:
            deterministic = interpret_employee(row)
            classification, reason, candidates, warnings, error = _process_record(
                source_type,
                source_id,
                f"Inspect employee submission {source_id}. Reject receipts and reimbursements.",
                deterministic,
                use_llm,
            )
        except DocumentExtractionError as exc:
            classification, reason, candidates, warnings, error = (
                "unreadable",
                str(exc),
                [],
                [],
                str(exc),
            )
        result.traces.append(
            _trace(
                source_type,
                source_id,
                classification=classification,
                reason=reason,
                candidate=candidates[0] if candidates else None,
                error=error,
                warnings=warnings,
            )
        )
        result.candidates.extend(candidates)
    result.invoices_found = len(result.candidates)
    result.non_invoices = result.records_checked - result.invoices_found
    return result


def run_document_source(period: str, use_llm: bool = False) -> SourceRunResult:
    source_type = "document"
    result = _new_source_run(source_type)
    rows = list_mail_documents(period)
    result.records_checked = len(rows)
    for row in rows:
        source_id = str(row.get("document_id"))
        try:
            deterministic = interpret_document(row)
            classification, reason, candidates, warnings, error = _process_record(
                source_type,
                source_id,
                f"Inspect scanned document {source_id} and extract invoice fields if present.",
                deterministic,
                use_llm,
            )
        except DocumentExtractionError as exc:
            classification, reason, candidates, warnings, error = (
                "unreadable",
                str(exc),
                [],
                [],
                str(exc),
            )
        result.traces.append(
            _trace(
                source_type,
                source_id,
                classification=classification,
                reason=reason,
                candidate=candidates[0] if candidates else None,
                error=error,
                warnings=warnings,
            )
        )
        result.candidates.extend(candidates)
    result.invoices_found = len(result.candidates)
    result.non_invoices = result.records_checked - result.invoices_found
    return result


def run_edi_source(period: str, use_llm: bool = False) -> SourceRunResult:
    """Parse EDI/UBL/JSON in Python. LLM only if the deterministic parse is incomplete."""
    source_type = "edi"
    result = _new_source_run(source_type)
    rows = list_edi_documents(period)
    result.records_checked = len(rows)
    for row in rows:
        source_id = str(row.get("document_id"))
        try:
            parsed = parse_edi_document(row)
            deterministic = ("invoice", parsed.classification_reason, [parsed])
        except EDIParseError as exc:
            deterministic = ("unreadable", str(exc), [])
            parsed = None
        # Structured EDI uses Python first. LLM only if parsing failed or fields are missing.
        needs_llm = use_llm and (
            parsed is None
            or not parsed.vendor
            or not parsed.vendor_invoice_number
            or parsed.amount is None
        )
        classification, reason, candidates, warnings, error = _process_record(
            source_type,
            source_id,
            f"Inspect EDI document {source_id}. Prefer python_parse from get_edi_document.",
            deterministic,
            needs_llm,
        )
        result.traces.append(
            _trace(
                source_type,
                source_id,
                classification=classification,
                reason=reason,
                candidate=candidates[0] if candidates else None,
                error=error,
                warnings=warnings,
            )
        )
        result.candidates.extend(candidates)
    result.invoices_found = len(result.candidates)
    result.non_invoices = result.records_checked - result.invoices_found
    return result


def _bank_candidate_from_matches(transaction: dict, matches: list[dict]) -> InvoiceCandidate | None:
    if not matches:
        return None
    best = matches[0]
    text = str(best.get("text") or "")
    parsed = parse_invoice_text_clean(
        text=text,
        source_type="bank_card",
        source_id=str(transaction.get("transaction_id")),
        source_uri=best.get("source_uri"),
        vendor_hint=best.get("vendor") or None,
        extra_context={
            "transaction_id": transaction.get("transaction_id"),
            "matched_source_type": best.get("source_type"),
            "matched_source_id": best.get("source_id"),
            "vendor_descriptor": transaction.get("vendor_descriptor"),
        },
    )
    if parsed.classification != "invoice" and not parsed.vendor_invoice_number:
        return None
    return parsed.model_copy(
        update={
            "source_type": "bank_card",
            "classification": "invoice",
            "classification_reason": (
                f"Card charge matched invoice documentation in "
                f"{best.get('source_type')} {best.get('source_id')}"
            ),
        }
    )


def run_bank_card_source(period: str, use_llm: bool = False) -> SourceRunResult:
    source_type = "bank_card"
    result = _new_source_run(source_type)
    rows = list_bank_transactions(period)
    result.records_checked = len(rows)
    for row in rows:
        source_id = str(row.get("transaction_id"))
        matches = find_related_invoice_records(row)
        candidate = _bank_candidate_from_matches(row, matches)
        if candidate:
            status, reason = "invoice_found", candidate.classification_reason
        else:
            status, reason = (
                "invoice_missing",
                "No supporting invoice documentation found for this charge",
            )
            candidate = None
        warnings: list[str] = []
        error = None
        if use_llm:
            try:
                output = _run_llm(
                    source_type,
                    source_id,
                    (
                        f"Inspect bank/card transaction {source_id}. "
                        "A charge is not an invoice. Use find_related_invoice. "
                        "Do not manufacture an invoice from the transaction alone."
                    ),
                )
                if not isinstance(output, BankAgentOutput):
                    raise TypeError(f"Bank/Card agent returned {type(output).__name__}")
                status = output.status
                reason = output.reason
                if output.status == "invoice_found":
                    candidate = output.candidate or candidate
                    if candidate is not None:
                        candidate = candidate.model_copy(update={"source_type": "bank_card", "source_id": source_id})
                else:
                    candidate = None
            except Exception as exc:
                error = f"agent_failed:{exc}"
                warnings.append(error)
                warnings.append("used_deterministic_fallback")
        discovery = BankDiscoveryResult(
            transaction_id=source_id,
            status="invoice_found" if candidate is not None else status,
            reason=reason,
            vendor_descriptor=str(row.get("vendor_descriptor") or ""),
            amount=row.get("amount"),
            candidate=candidate,
            matched_source_ids=[str(item.get("source_id")) for item in matches],
        )
        result.discovery.append(discovery)
        result.traces.append(
            _trace(
                source_type,
                source_id,
                classification=discovery.status,
                reason=reason,
                candidate=candidate,
                error=error,
                warnings=warnings,
            )
        )
        if candidate is not None:
            result.candidates.append(candidate)
        elif discovery.status in {"invoice_missing", "needs_follow_up"}:
            result.missing_documentation += 1
    result.invoices_found = len(result.candidates)
    return result


SOURCE_RUNNERS = {
    "email": run_email_source,
    "erp": run_erp_source,
    "procurement": run_procurement_source,
    "vendor_portal": run_vendor_portal_source,
    "employee_submission": run_employee_source,
    "document": run_document_source,
    "edi": run_edi_source,
    "bank_card": run_bank_card_source,
}

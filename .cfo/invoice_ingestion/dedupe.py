from __future__ import annotations

from invoice_ingestion.models import CanonicalInvoice, InvoiceCandidate, SourceRef, SOURCE_AGENTS
from invoice_ingestion.identity import canonical_invoice_key
from invoice_ingestion.validate import existing_ap_match, validate_candidate
from tools import normalize_vendor


def _invoice_key(vendor: str, number: str) -> str:
    return canonical_invoice_key(vendor=vendor, vendor_invoice_number=number) or ""


def _source_ref(candidate: InvoiceCandidate) -> SourceRef:
    return SourceRef(
        source_type=candidate.source_type,
        source_id=candidate.source_id,
        source_uri=candidate.source_uri,
        agent=SOURCE_AGENTS.get(candidate.source_type, candidate.source_type),
        document_hash=candidate.document_hash,
    )


def _prefer_text(left: str | None, right: str | None) -> str | None:
    if left:
        return left
    return right


def merge_candidates(group: list[InvoiceCandidate], canonical_id: str) -> CanonicalInvoice:
    primary = max(group, key=lambda item: (item.extraction_confidence or 0, bool(item.po_id), bool(item.document_hash)))
    vendor = next((item.vendor for item in group if item.vendor), "") or ""
    number = next((item.vendor_invoice_number for item in group if item.vendor_invoice_number), "") or ""
    amount = next((item.amount for item in group if item.amount is not None), None)
    invoice_date = next((item.invoice_date for item in group if item.invoice_date), None) or ""
    due_date = next((item.due_date for item in group if item.due_date), None)
    currency = next((item.currency for item in group if item.currency), None) or "USD"
    po_id = next((item.po_id for item in group if item.po_id), None)
    vendor_id = next((item.vendor_id for item in group if item.vendor_id), None)
    subtotal = next((item.subtotal for item in group if item.subtotal is not None), None)
    tax = next((item.tax for item in group if item.tax is not None), None)
    hash_value = next((item.document_hash for item in group if item.document_hash), None)
    line_items = next((item.line_items for item in group if item.line_items), [])
    evidence = [item for candidate in group for item in candidate.evidence]
    description = ""
    for candidate in group:
        context = candidate.source_context or {}
        description = _prefer_text(description, context.get("description") if isinstance(context.get("description"), str) else None)
        if candidate.line_items:
            description = _prefer_text(description, candidate.line_items[0].description)
    existing_id = existing_ap_match(vendor, number) if vendor and number else None

    merged = CanonicalInvoice(
        canonical_id=canonical_id,
        vendor=vendor,
        vendor_id=vendor_id,
        vendor_invoice_number=number,
        invoice_date=invoice_date,
        due_date=due_date,
        currency=currency,
        amount=float(amount or 0),
        subtotal=subtotal,
        tax=tax,
        po_id=po_id,
        description=description or f"{vendor} {number}".strip(),
        line_items=list(line_items),
        sources=[_source_ref(item) for item in group],
        document_hash=hash_value,
        evidence=evidence,
        already_in_ap_inbox=existing_id is not None,
        existing_ap_invoice_id=existing_id,
        canonical_key=canonical_invoice_key(vendor=vendor, vendor_invoice_number=number),
    )
    # Re-validate the merged view using a synthetic candidate.
    synthetic = InvoiceCandidate(
        source_type=primary.source_type,
        source_id=primary.source_id,
        vendor=merged.vendor,
        vendor_invoice_number=merged.vendor_invoice_number,
        invoice_date=merged.invoice_date,
        due_date=merged.due_date,
        currency=merged.currency,
        subtotal=merged.subtotal,
        tax=merged.tax,
        amount=merged.amount,
        po_id=merged.po_id,
        extraction_confidence=primary.extraction_confidence,
    )
    result = validate_candidate(synthetic)
    merged.validation_status = result.status
    merged.validation_errors = result.errors
    merged.warnings = list(dict.fromkeys(result.warnings))
    if len(group) > 1:
        merged.warnings.append(
            "merged_sources:" + ",".join(f"{item.source_type}:{item.source_id}" for item in group)
        )
    return merged


def _near_duplicate(left: InvoiceCandidate, right: InvoiceCandidate) -> bool:
    if not left.vendor or not right.vendor:
        return False
    if normalize_vendor(left.vendor) != normalize_vendor(right.vendor):
        return False
    left_num = (left.vendor_invoice_number or "").replace("-", "").replace(" ", "").upper()
    right_num = (right.vendor_invoice_number or "").replace("-", "").replace(" ", "").upper()
    if left_num and right_num and left_num == right_num:
        return True
    if left.document_hash and right.document_hash and left.document_hash == right.document_hash:
        return True
    if not left.invoice_date or left.invoice_date != right.invoice_date:
        return False
    if left.amount is None or right.amount is None:
        return False
    return abs(left.amount - right.amount) <= 1.0 and bool(left_num) and left_num == right_num


def cluster_candidates(candidates: list[InvoiceCandidate]) -> list[list[InvoiceCandidate]]:
    clusters: list[list[InvoiceCandidate]] = []
    assigned: set[int] = set()
    for index, candidate in enumerate(candidates):
        if index in assigned:
            continue
        group = [candidate]
        assigned.add(index)
        key = None
        if candidate.vendor and candidate.vendor_invoice_number:
            key = _invoice_key(candidate.vendor, candidate.vendor_invoice_number)
        for other_index, other in enumerate(candidates):
            if other_index in assigned:
                continue
            other_key = None
            if other.vendor and other.vendor_invoice_number:
                other_key = _invoice_key(other.vendor, other.vendor_invoice_number)
            same_hash = (
                bool(candidate.document_hash)
                and candidate.document_hash == other.document_hash
            )
            same_source = (
                candidate.source_type == other.source_type
                and candidate.source_id == other.source_id
            )
            if same_source or same_hash or (key and key == other_key) or _near_duplicate(candidate, other):
                group.append(other)
                assigned.add(other_index)
        clusters.append(group)
    return clusters


def dedupe_candidates(candidates: list[InvoiceCandidate]) -> tuple[list[CanonicalInvoice], int]:
    clusters = cluster_candidates(candidates)
    canonical: list[CanonicalInvoice] = []
    duplicates_removed = 0
    for offset, group in enumerate(clusters, start=1):
        duplicates_removed += max(0, len(group) - 1)
        canonical.append(merge_candidates(group, canonical_id=f"ING-{offset:03d}"))
    canonical.sort(key=lambda item: (item.vendor.lower(), item.vendor_invoice_number))
    remapped: list[CanonicalInvoice] = []
    for index, item in enumerate(canonical, start=1):
        remapped.append(item.model_copy(update={"canonical_id": f"ING-{index:03d}"}))
    return remapped, duplicates_removed

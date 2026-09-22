from __future__ import annotations

from invoice_ingestion.dedupe import dedupe_candidates
from invoice_ingestion.extract import document_hash
from invoice_ingestion.identity import canonical_invoice_key
from invoice_ingestion.models import InvoiceCandidate
from invoice_ingestion.validate import validate_candidate


def _candidate(**overrides) -> InvoiceCandidate:
    payload = dict(
        source_type="email",
        source_id="MSG-1",
        vendor="Amazon Web Services",
        vendor_invoice_number="INV-9001",
        invoice_date="2026-09-12",
        due_date="2026-10-12",
        currency="USD",
        subtotal=100.0,
        tax=10.0,
        amount=110.0,
        extraction_confidence=0.9,
    )
    payload.update(overrides)
    return InvoiceCandidate(**payload)


def test_valid_totals():
    result = validate_candidate(_candidate())
    assert result.status == "valid"
    assert result.errors == []


def test_inconsistent_totals():
    result = validate_candidate(_candidate(subtotal=100.0, tax=10.0, amount=200.0))
    assert result.status == "rejected"
    assert "inconsistent_totals" in result.errors


def test_invalid_dates():
    result = validate_candidate(_candidate(invoice_date="09/12/2026"))
    assert "malformed_invoice_date:09/12/2026" in result.errors
    result = validate_candidate(_candidate(invoice_date="2026-13-40"))
    assert any("malformed_invoice_date" in item for item in result.errors)


def test_missing_required_fields():
    result = validate_candidate(
        _candidate(vendor=None, vendor_invoice_number=None, amount=None, currency=None, invoice_date=None)
    )
    assert "missing_vendor" in result.errors
    assert "missing_invoice_number" in result.errors
    assert "missing_amount" in result.errors
    assert "missing_currency" in result.errors
    assert "missing_invoice_date" in result.errors


def test_duplicate_source_id():
    first = _candidate()
    seen = {(first.source_type, first.source_id)}
    result = validate_candidate(_candidate(source_id="MSG-1"), seen)
    assert "duplicate_source_id" in result.errors


def test_duplicate_hashes_are_merged():
    digest = document_hash("same document body")
    left = _candidate(source_type="email", source_id="E1", document_hash=digest)
    right = _candidate(source_type="vendor_portal", source_id="P1", document_hash=digest)
    canonical, removed = dedupe_candidates([left, right])
    assert removed == 1
    assert len(canonical) == 1
    assert {ref.source_type for ref in canonical[0].sources} == {"email", "vendor_portal"}


def test_duplicate_invoice_numbers_are_merged():
    left = _candidate(source_type="email", source_id="E1")
    right = _candidate(source_type="vendor_portal", source_id="P1", document_hash="abc")
    canonical, removed = dedupe_candidates([left, right])
    assert removed == 1
    assert canonical[0].vendor_invoice_number == "INV-9001"
    assert canonical[0].canonical_key == canonical_invoice_key(left)


def test_similar_amount_and_date_without_invoice_number_do_not_merge():
    left = _candidate(source_id="A", vendor="Office Depot", vendor_invoice_number="OD-1", amount=100, invoice_date="2026-09-01")
    right = _candidate(source_id="B", vendor="Figma", vendor_invoice_number="FIG-1", amount=100, invoice_date="2026-09-01")
    canonical, removed = dedupe_candidates([left, right])
    assert removed == 0
    assert len(canonical) == 2


def test_line_item_sum_mismatch():
    result = validate_candidate(
        _candidate(
            line_items=[
                {"description": "A", "quantity": 2, "unit_price": 40.0, "amount": 80.0},
                {"description": "B", "quantity": 1, "unit_price": 50.0, "amount": 50.0},
            ]
        )
    )
    assert "line_item_sum_mismatch" in result.errors
    assert result.status == "rejected"


def test_line_item_extension_mismatch():
    result = validate_candidate(
        _candidate(
            subtotal=130.0,
            tax=0.0,
            amount=130.0,
            line_items=[
                {"description": "A", "quantity": 2, "unit_price": 40.0, "amount": 80.0},
                {"description": "B", "quantity": 1, "unit_price": 20.0, "amount": 50.0},
            ],
        )
    )
    assert "line_item_extension_mismatch" in result.errors
    assert result.status == "rejected"


def test_unsupported_source_type():
    result = validate_candidate(_candidate(source_type="fax"))
    assert "unsupported_source_type:fax" in result.errors

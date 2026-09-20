from __future__ import annotations

import invoice_ingestion.registry as registry
import tools as tools_mod
from invoice_ingestion.identity import canonical_invoice_key
from invoice_ingestion.models import InvoiceCandidate
from invoice_ingestion.registry import configure_paths, lookup
from invoice_ingestion.workflow import ingest_invoices
from tools import all_invoices, configure_overlay_path, load_invoice


def test_canonical_registry_survives_process_boundary():
    first = ingest_invoices("2026-09", forward_to_ap=True, reset_overlay=True)
    aws = next(item for item in first.canonical_invoices if item.vendor_invoice_number == "INV-9001")
    canonical_id = aws.canonical_id
    assert registry.REGISTRY_PATH.exists()
    assert tools_mod.OVERLAY_PATH.exists()
    assert load_invoice(canonical_id) is not None

    saved_registry = registry.REGISTRY_PATH
    saved_overlay = tools_mod.OVERLAY_PATH
    configure_paths(saved_registry.parent)
    configure_overlay_path(saved_overlay)
    found = lookup(
        InvoiceCandidate(
            source_type="email",
            source_id="MSG-E01",
            vendor="Amazon Web Services",
            vendor_invoice_number="INV-9001",
        )
    )
    assert found is not None
    assert found.canonical_id == canonical_id
    assert canonical_invoice_key(found) == canonical_invoice_key(aws)
    overlay = [item for item in all_invoices() if item.vendor_invoice_number == "INV-9001"]
    assert [item.invoice_id for item in overlay] == [canonical_id]

    second = ingest_invoices("2026-09", forward_to_ap=True, reset_overlay=False)
    again = next(item for item in second.canonical_invoices if item.vendor_invoice_number == "INV-9001")
    assert again.canonical_id == canonical_id
    assert second.new_canonical_count == 0
    assert second.new_ap_handoffs == 0

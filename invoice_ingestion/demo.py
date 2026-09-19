"""HackMIT demo for multi-source invoice ingestion.

Usage:
    python -m invoice_ingestion.demo
    python -m invoice_ingestion.demo --no-ap
    python -m invoice_ingestion.demo --replay
    python -m invoice_ingestion.demo --llm
    python main.py ingest 2026-09
    python main.py ingest 2026-09 --replay-check
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from invoice_ingestion.models import IngestionReport, STRUCTURED_SOURCES, SUPPORTED_SOURCES
from invoice_ingestion.registry import already_handed_off
from invoice_ingestion.workflow import ingest_invoices

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SOURCE_LABELS = {
    "email": "Email",
    "erp": "ERP",
    "procurement": "Procurement",
    "vendor_portal": "Vendor Portal",
    "employee_submission": "Employee",
    "document": "Document",
    "edi": "EDI",
    "bank_card": "Bank/Card",
}


def _pad(label: str, width: int = 24) -> str:
    return label.ljust(width)


def format_report(report: IngestionReport) -> str:
    lines = [
        f"Invoice Ingestion — {report.period}",
        "",
        "Extraction",
        "  Structured (Python parser):  ERP, Procurement, EDI",
        "  Unstructured (interpret/LLM-optional): Email, Portal, Employee, Document, Bank/Card",
        "",
        "Source processing",
    ]
    runs = {item.source_type: item for item in report.source_runs}
    for source_type in SUPPORTED_SOURCES:
        run = runs.get(source_type)
        if run is None:
            continue
        title = SOURCE_LABELS.get(source_type, source_type)
        method = run.extraction_method or (
            "deterministic" if source_type in STRUCTURED_SOURCES else "unstructured"
        )
        if run.error:
            lines.append(f"{_pad(title)}ERROR: {run.error}")
            continue
        found = run.invoices_found
        if source_type == "bank_card":
            recovered = "invoice recovered" if found == 1 else "invoices recovered"
            lines.append(f"{_pad(title)}{found} {recovered}  [{method}]")
            lines.append(f"{_pad('Bank/Card')}{run.missing_documentation} missing documentation")
        else:
            noun = "invoice candidate" if found == 1 else "invoice candidates"
            lines.append(f"{_pad(title)}{found} {noun}  [{method}]")

    already = sum(1 for item in report.canonical_invoices if item.already_in_ap_inbox)
    forwarded = sum(1 for item in report.canonical_invoices if item.forwarded_to_ap)
    lines.extend(
        [
            "",
            f"{_pad('Candidates')}{len(report.candidates)}",
            f"{_pad('Cross-source duplicates')}{report.duplicates_removed}",
            f"{_pad('Canonical invoices')}{len(report.canonical_invoices)}",
            f"{_pad('Already present in AP')}{already}",
            f"{_pad('Forwarded to AP')}{forwarded}",
        ]
    )
    if report.errors:
        lines.append(f"{_pad('Source errors')}{'; '.join(report.errors)}")

    lines.extend(["", "Notable invoices"])
    lines.extend(_aws_block(report))
    lines.extend(_acme_block(report))
    lines.extend(_helios_block(report))
    lines.extend(_wework_block(report))

    lines.append("")
    lines.append("All canonical invoices")
    for item in report.canonical_invoices:
        sources = ", ".join(ref.source_type for ref in item.sources)
        amount = f"${item.amount:,.2f}"
        ap = item.ap_result or item.validation_status
        lines.append(
            f"  {item.canonical_id}  {item.vendor}  {item.vendor_invoice_number}  "
            f"{amount}  sources=[{sources}]  {item.ingestion_status}  {ap}"
        )
    if report.trace_path:
        lines.append("")
        lines.append(f"Trace saved to {report.trace_path}")
    return "\n".join(lines)


def _find_canonical(report: IngestionReport, number: str):
    for item in report.canonical_invoices:
        if item.vendor_invoice_number == number:
            return item
    return None


def _aws_block(report: IngestionReport) -> list[str]:
    aws = _find_canonical(report, "INV-9001")
    if aws is None:
        return []
    sources = ", ".join(ref.source_type for ref in aws.sources)
    shown = 1 if already_handed_off(aws.canonical_id) or aws.forwarded_to_ap else 0
    return [
        "",
        f"AWS {aws.vendor_invoice_number}",
        f"  Sources: {sources}",
        "  Canonical records: 1",
        f"  AP handoffs: {shown}",
    ]


def _acme_block(report: IngestionReport) -> list[str]:
    acme = _find_canonical(report, "ACM-2026-4410")
    if acme is None:
        return []
    return [
        "",
        f"Acme {acme.vendor_invoice_number}",
        f"  Existing AP record: {acme.existing_ap_invoice_id or 'INV-001'}",
        f"  New AP handoffs: {1 if acme.forwarded_to_ap else 0}",
    ]


def _helios_block(report: IngestionReport) -> list[str]:
    helios = _find_canonical(report, "HEL-INV-6200")
    if helios is None:
        return []
    shown = 1 if already_handed_off(helios.canonical_id) or helios.forwarded_to_ap else 0
    return [
        "",
        f"Helios {helios.vendor_invoice_number}",
        f"  Sources: {', '.join(ref.source_type for ref in helios.sources)}",
        f"  AP handoffs: {shown}",
    ]


def _wework_block(report: IngestionReport) -> list[str]:
    missing = [
        item
        for item in report.discovery
        if "WEWORK" in (item.vendor_descriptor or "").upper()
        or item.transaction_id == "CC-4412"
    ]
    if not missing:
        return []
    row = missing[0]
    return [
        "",
        "WeWork",
        f"  Card transaction found ({row.transaction_id})",
        "  Supporting invoice: missing",
        "  AP handoffs: 0",
    ]


def format_replay(first: IngestionReport, second: IngestionReport) -> str:
    previously = len(first.canonical_invoices)
    new_canonical = second.new_canonical_count
    new_handoffs = second.new_ap_handoffs
    passed = new_canonical == 0 and new_handoffs == 0
    aws = _find_canonical(second, "INV-9001")
    sources = ", ".join(ref.source_type for ref in aws.sources) if aws else "(missing)"
    return "\n".join(
        [
            "",
            "Re-running ingestion...",
            "",
            f"Previously processed invoices: {previously}",
            f"New canonical invoices: {new_canonical}",
            f"New AP handoffs: {new_handoffs}",
            f"AWS INV-9001 sources: {sources}",
            "",
            f"Idempotency check: {'PASS' if passed else 'FAIL'}",
        ]
    )


def run_demo(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    period = "2026-09"
    use_llm = "--llm" in argv
    run_ap = "--ap-workflow" in argv
    forward = "--no-ap" not in argv
    replay = "--replay" in argv or "--replay-check" in argv
    rest = [item for item in argv if not item.startswith("--")]
    if rest:
        period = rest[0]
    if use_llm and not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set; running deterministic extraction instead.")
        use_llm = False
    if run_ap and not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set; cannot run the live AP workflow.")
        return 1

    first = ingest_invoices(
        period=period,
        use_llm=use_llm,
        forward_to_ap=forward or run_ap,
        run_ap=run_ap,
        reset_overlay=True,
    )
    print(format_report(first))
    if replay:
        second = ingest_invoices(
            period=period,
            use_llm=use_llm,
            forward_to_ap=forward or run_ap,
            run_ap=run_ap,
            reset_overlay=False,
        )
        print(format_replay(first, second))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_demo())

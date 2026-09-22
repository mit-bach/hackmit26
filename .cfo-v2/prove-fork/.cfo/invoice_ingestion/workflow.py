from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from invoice_ingestion.adapter import register_canonical, reset_ingested_invoices
from invoice_ingestion.dedupe import dedupe_candidates
from invoice_ingestion.identity import canonical_invoice_key
from invoice_ingestion.models import (
    CanonicalInvoice,
    IngestionReport,
    STRUCTURED_SOURCES,
    SUPPORTED_SOURCES,
)
from invoice_ingestion.registry import (
    already_handed_off,
    known_source_pairs,
    lookup,
    mark_handed_off,
    merge_provenance,
    next_canonical_id,
    remember,
)
from invoice_ingestion.sources import SOURCE_RUNNERS, _new_source_run
from invoice_ingestion.validate import validate_candidate
from tools import collect_case_evidence

RUNS_DIR = Path(__file__).resolve().parent.parent / "runs" / "ingestion"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _save_trace(report: IngestionReport) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RUNS_DIR / f"ingest-{report.period}-{stamp}.json"
    report.trace_path = str(path)
    path.write_text(report.model_dump_json(indent=2) + "\n")
    return path


def _preview_ap(canonical: CanonicalInvoice) -> str:
    if canonical.already_in_ap_inbox:
        return f"already in AP inbox as {canonical.existing_ap_invoice_id}"
    if canonical.validation_status != "valid":
        return "not forwarded (validation)"
    try:
        evidence = collect_case_evidence(canonical.canonical_id)
    except Exception as exc:
        return f"AP lookup failed: {exc}"
    exceptions = evidence.exception_types or ["none"]
    return f"AP exceptions={exceptions}"


def _resolve_against_registry(item: CanonicalInvoice) -> tuple[CanonicalInvoice, set[tuple[str, str]]]:
    """Reuse a prior canonical invoice when identity matches. Preserve provenance."""
    item.canonical_key = item.canonical_key or canonical_invoice_key(item)
    existing = lookup(item)
    if existing is None:
        reuse_id = item.existing_ap_invoice_id
        if reuse_id and str(reuse_id).startswith("ING-"):
            item = item.model_copy(
                update={
                    "canonical_id": reuse_id,
                    "ingestion_status": "existing_canonical_invoice",
                    "new_this_run": False,
                    "provenance_added": False,
                }
            )
            remember(item)
            return item, set()
        item = item.model_copy(
            update={
                "canonical_id": next_canonical_id(),
                "ingestion_status": (
                    "already_present_in_ap" if item.already_in_ap_inbox else "new_invoice"
                ),
                "new_this_run": True,
                "provenance_added": False,
            }
        )
        remember(item)
        return item, set()

    prior_sources = known_source_pairs(existing)
    provenance_added = merge_provenance(existing, item)
    existing.already_in_ap_inbox = existing.already_in_ap_inbox or item.already_in_ap_inbox
    existing.existing_ap_invoice_id = existing.existing_ap_invoice_id or item.existing_ap_invoice_id
    existing.validation_status = item.validation_status or existing.validation_status
    existing.validation_errors = item.validation_errors or existing.validation_errors
    existing.canonical_key = existing.canonical_key or item.canonical_key
    existing.provenance_added = provenance_added
    existing.new_this_run = False
    existing.forwarded_to_ap = False
    if existing.already_in_ap_inbox:
        existing.ingestion_status = "already_present_in_ap"
    elif provenance_added:
        existing.ingestion_status = "new_provenance"
    else:
        existing.ingestion_status = "existing_canonical_invoice"
    remember(existing)
    return existing, prior_sources


def _annotate_traces(
    report: IngestionReport,
    prior_sources_by_id: dict[str, set[tuple[str, str]]],
) -> None:
    source_to_canonical: dict[tuple[str, str], CanonicalInvoice] = {}
    for item in report.canonical_invoices:
        for ref in item.sources:
            source_to_canonical[(ref.source_type, ref.source_id)] = item

    for trace in report.traces:
        trace.source_ref = f"{trace.source_type}:{trace.source_id}"
        if trace.extraction_method is None:
            trace.extraction_method = (
                "deterministic" if trace.source_type in STRUCTURED_SOURCES else "unstructured"
            )
        if trace.classification in {"invoice_missing", "needs_follow_up"}:
            trace.status = "missing_supporting_documentation"
            continue
        if not trace.candidate_produced:
            trace.status = "not_an_invoice"
            continue
        match = source_to_canonical.get((trace.source_type, trace.source_id))
        if match is None:
            continue
        pair = (trace.source_type, trace.source_id)
        prior = prior_sources_by_id.get(match.canonical_id, set())
        siblings = [
            ref
            for ref in match.sources
            if (ref.source_type, ref.source_id) != pair
        ]
        trace.canonical_id = match.canonical_id
        trace.canonical_key = match.canonical_key
        trace.ap_handoff = match.forwarded_to_ap
        trace.forwarded_to_ap = match.forwarded_to_ap
        if siblings:
            trace.duplicate_of = match.canonical_id
        if match.already_in_ap_inbox:
            trace.status = "already_present_in_ap"
            trace.provenance_added = False
        elif match.new_this_run:
            first = match.sources[0] if match.sources else None
            is_primary = first is not None and pair == (first.source_type, first.source_id)
            trace.status = "new_invoice" if is_primary or not siblings else "duplicate_within_run"
            trace.provenance_added = False
        elif pair in prior:
            trace.status = "source_replay"
            trace.provenance_added = False
        else:
            trace.status = "new_provenance"
            trace.provenance_added = True


def ingest_invoices(
    period: str = "2026-09",
    sources: list[str] | None = None,
    *,
    use_llm: bool = False,
    forward_to_ap: bool = False,
    run_ap: bool = False,
    reset_overlay: bool = True,
) -> IngestionReport:
    """Run enabled sources, validate, dedupe, and optionally hand off to AP.

    reset_overlay=True starts a clean session (tests and the first demo run).
    Pass False to replay against the in-memory canonical registry so the same
    invoice is not forwarded to AP again.
    """
    enabled = list(sources or SUPPORTED_SOURCES)
    report = IngestionReport(period=period, started_at=_now())
    if reset_overlay:
        reset_ingested_invoices()

    seen_source_ids: set[tuple[str, str]] = set()
    for source_type in enabled:
        if source_type not in SOURCE_RUNNERS:
            report.errors.append(f"unsupported_source_type:{source_type}")
            continue
        try:
            run = SOURCE_RUNNERS[source_type](period, use_llm=use_llm)
        except Exception as exc:
            run = _new_source_run(source_type)
            run.error = str(exc)
            report.errors.append(f"{source_type}:{exc}")
        report.source_runs.append(run)
        report.discovery.extend(run.discovery)
        report.traces.extend(run.traces)
        report.candidates.extend(run.candidates)

    return _finalize_candidates(
        report,
        report.candidates,
        seen_source_ids=seen_source_ids,
        forward_to_ap=forward_to_ap,
        run_ap=run_ap,
    )


def ingest_candidates(
    candidates: list,
    period: str = "2026-09",
    *,
    forward_to_ap: bool = False,
    run_ap: bool = False,
    reset_overlay: bool = False,
    save_trace: bool = True,
) -> IngestionReport:
    """Validate, dedupe, and optionally hand off pre-built candidates.

    Used by named provider adapters (Gmail, Outlook, Xero, Coupa, NetSuite)
    without re-running the eight mock source collectors.
    """
    report = IngestionReport(period=period, started_at=_now())
    if reset_overlay:
        reset_ingested_invoices()
    report.candidates = list(candidates)
    return _finalize_candidates(
        report,
        report.candidates,
        seen_source_ids=set(),
        forward_to_ap=forward_to_ap,
        run_ap=run_ap,
        save_trace=save_trace,
    )


def _finalize_candidates(
    report: IngestionReport,
    candidates: list,
    *,
    seen_source_ids: set[tuple[str, str]],
    forward_to_ap: bool,
    run_ap: bool,
    save_trace: bool = True,
) -> IngestionReport:
    valid_candidates = []
    for candidate in candidates:
        result = validate_candidate(candidate, seen_source_ids)
        seen_source_ids.add((candidate.source_type, candidate.source_id))
        for trace in report.traces:
            if trace.source_type == candidate.source_type and trace.source_id == candidate.source_id:
                trace.validation_status = result.status
                trace.validation_errors = result.errors
                trace.warnings = list(dict.fromkeys(trace.warnings + result.warnings))
        if result.status == "rejected":
            report.rejected.append(candidate)
        else:
            valid_candidates.append(candidate)

    clustered, duplicates_removed = dedupe_candidates(valid_candidates)
    report.duplicates_removed = duplicates_removed

    resolved: list[CanonicalInvoice] = []
    prior_sources_by_id: dict[str, set[tuple[str, str]]] = {}
    for item in clustered:
        record, prior_sources = _resolve_against_registry(item)
        prior_sources_by_id[record.canonical_id] = prior_sources
        resolved.append(record)
    resolved.sort(key=lambda item: (item.vendor.lower(), item.vendor_invoice_number))
    report.canonical_invoices = resolved
    report.new_canonical_count = sum(1 for item in resolved if item.new_this_run)
    report.replayed_canonical_count = sum(1 for item in resolved if not item.new_this_run)
    report.provenance_updates = sum(1 for item in resolved if item.provenance_added)

    if forward_to_ap:
        for item in report.canonical_invoices:
            if item.validation_status != "valid":
                continue
            if item.already_in_ap_inbox or (
                item.existing_ap_invoice_id and str(item.existing_ap_invoice_id).startswith("ING-")
            ):
                item.ap_result = (
                    f"already in AP inbox as {item.existing_ap_invoice_id}; not forwarded"
                )
                item.forwarded_to_ap = False
                item.ap_invoice_id = item.existing_ap_invoice_id or item.canonical_id
                continue
            if already_handed_off(item.canonical_id):
                item.forwarded_to_ap = False
                item.ap_invoice_id = item.canonical_id
                item.ap_result = f"already forwarded as {item.canonical_id}"
                continue
            register_canonical(item)
            mark_handed_off(item.canonical_id)
            item.forwarded_to_ap = True
            item.ap_invoice_id = item.canonical_id
            report.forwarded_invoice_ids.append(item.canonical_id)
            item.ap_result = _preview_ap(item)
            if run_ap:
                from workflow import run_ap_workflow

                ap_trace = run_ap_workflow(item.canonical_id)
                item.ap_result = f"FINAL {ap_trace.final.decision}"
    else:
        for item in report.canonical_invoices:
            if item.already_in_ap_inbox:
                item.ap_result = f"already in AP inbox as {item.existing_ap_invoice_id}"
            elif already_handed_off(item.canonical_id):
                item.ap_result = f"already forwarded as {item.canonical_id}"
            elif item.validation_status == "valid":
                item.ap_result = "not forwarded"

    report.new_ap_handoffs = sum(1 for item in report.canonical_invoices if item.forwarded_to_ap)
    _annotate_traces(report, prior_sources_by_id)
    if save_trace:
        _save_trace(report)
    return report

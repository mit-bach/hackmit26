"""Multi-source invoice ingestion. Extraction only — AP still approves."""

from invoice_ingestion.workflow import ingest_invoices

__all__ = ["ingest_invoices"]

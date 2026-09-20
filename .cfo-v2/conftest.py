from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
CFO = REPO / ".cfo"
OFFICE = REPO / ".cfo-v2" / "office"
for path in (CFO, OFFICE):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)


@pytest.fixture(autouse=True)
def isolated_source_kernel(tmp_path, monkeypatch):
    from invoice_ingestion.adapter import reset_ingested_invoices
    from invoice_ingestion.registry import configure_paths as configure_registry
    from invoice_ingestion.store import clear_ingestion_cache
    from integrations import store as integration_store
    from tools import clear_runtime_invoices, configure_overlay_path

    monkeypatch.setenv("STRIPE_MODE", "mock")
    ingest_dir = tmp_path / "ingestion-state"
    configure_registry(ingest_dir)
    configure_overlay_path(ingest_dir / "overlay.json")
    runs = tmp_path / "integrations-runs"
    monkeypatch.setattr(integration_store, "RUNS_DIR", runs)
    monkeypatch.setattr(integration_store, "STATE_PATH", runs / "state.json")
    reset_ingested_invoices()
    clear_ingestion_cache()
    integration_store.reset_integration_state()
    clear_runtime_invoices()
    yield
    reset_ingested_invoices()
    clear_ingestion_cache()
    integration_store.reset_integration_state()
    clear_runtime_invoices()
    configure_registry()
    configure_overlay_path()

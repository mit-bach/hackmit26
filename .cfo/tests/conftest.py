import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def isolated_approved_pool(tmp_path, monkeypatch):
    path = tmp_path / "approved_pool.json"
    path.write_text("[]\n")
    monkeypatch.setattr("scheduling.pool.POOL_PATH", path)
    return path


@pytest.fixture(autouse=True)
def default_stripe_mock_mode(monkeypatch):
    monkeypatch.setenv("STRIPE_MODE", "mock")


@pytest.fixture(autouse=True)
def isolated_ar_state(tmp_path, monkeypatch):
    from ar.store import configure_paths, reset_state

    configure_paths(tmp_path / "ar-state")
    reset_state()
    yield
    configure_paths(tmp_path / "ar-state-done")


@pytest.fixture(autouse=True)
def isolated_cash_recon(tmp_path, monkeypatch):
    from cash_recon.store import reset_cash_state
    from cash_recon.case_store import configure_case_dir
    from cash_recon.handles import configure_handle_dirs
    from cash_recon.tools import unbind_case

    monkeypatch.setattr("cash_recon.store.RUNS_DIR", tmp_path / "cash-runs")
    monkeypatch.setattr("cash_recon.store.TRACES_DIR", tmp_path / "cash-traces")
    configure_case_dir(tmp_path / "cash-cases")
    configure_handle_dirs(packets_dir=tmp_path / "cash-packets", handles_dir=tmp_path / "cash-handles")
    reset_cash_state()
    unbind_case()
    yield
    reset_cash_state()
    unbind_case()
    configure_case_dir(None)
    configure_handle_dirs(packets_dir=tmp_path / "cash-packets-done", handles_dir=tmp_path / "cash-handles-done")


@pytest.fixture(autouse=True)
def isolated_month_end_state(tmp_path, monkeypatch):
    root = tmp_path / "month-end-state"
    from close.ledger import configure_paths as configure_gl
    from close.context import configure_paths as configure_ctx
    from close.month_end import configure_paths as configure_close
    from prepaid.store import configure_paths as configure_prepaid
    from fixed_assets.store import configure_paths as configure_assets
    from bs_recon.store import configure_paths as configure_recon

    from cash_recon.store import reset_cash_state

    configure_gl(root / "gl")
    configure_ctx(root / "ctx")
    configure_close(root / "close")
    configure_prepaid(root / "prepaid")
    configure_assets(root / "assets")
    configure_recon(root / "recon")
    reset_cash_state()
    yield
    reset_cash_state()


@pytest.fixture(autouse=True)
def isolated_audit_runs(tmp_path, monkeypatch):
    monkeypatch.setattr("audit.store.RUNS_DIR", tmp_path / "audit-runs")


@pytest.fixture(autouse=True)
def isolated_reporting(tmp_path):
    from reporting.ledger import configure_paths as configure_ledger, reset_ledger
    from reporting.sources import reset_ap_overrides
    from reporting.store import configure_paths as configure_store, reset_store

    configure_ledger(tmp_path / "reporting-ledger")
    configure_store(tmp_path / "reporting-store")
    reset_ledger()
    reset_store()
    reset_ap_overrides()
    yield
    reset_ledger()
    reset_store()
    reset_ap_overrides()


@pytest.fixture(autouse=True)
def isolated_ingestion_overlay(tmp_path, monkeypatch):
    from invoice_ingestion.adapter import reset_ingested_invoices
    from invoice_ingestion.registry import configure_paths as configure_registry
    from invoice_ingestion.store import clear_ingestion_cache
    from integrations import store as integration_store
    from tools import clear_runtime_invoices, configure_overlay_path

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


@pytest.fixture(autouse=True)
def restore_sample_data_loaders():
    """Undo apply_data_root leaks without forcing persistent runs/month_end."""
    from sample_data.paths import drain_data_root_stack
    from tools import configure_data_dir

    yield
    drain_data_root_stack()
    configure_data_dir()


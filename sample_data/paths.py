"""Apply a generated data-root to every existing loader that has a fixed path."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from tools import configure_data_dir

REPO = Path(__file__).resolve().parent.parent
CANONICAL: dict[str, Path] = {
    "tools_data": REPO / "data",
    "cash_demo": REPO / "data" / "cash_recon",
    "fixtures": REPO / "data" / "integrations",
    "ingestion": REPO / "data" / "ingestion",
    "reporting_data": REPO / "data" / "reporting",
    "audit_data": REPO / "data" / "audit",
    "prepaid_state": REPO / "runs" / "month_end",
    "prepaid_seed": REPO / "data" / "close" / "prepaids.json",
    "assets_state": REPO / "runs" / "month_end",
    "assets_seed": REPO / "data" / "close" / "fixed_assets.json",
    "capital_seed": REPO / "data" / "close" / "capital_invoices.json",
}

_STACK: list[dict[str, Path]] = []


def snapshot_loader_paths() -> dict[str, Path]:
    from audit.store import DATA_DIR as audit_dir
    from cash_recon.demo import ROOT as cash_root
    from fixed_assets.store import SEED_ASSETS, SEED_CANDIDATES, STATE_DIR as assets_state
    from integrations.providers.base import FIXTURES
    from invoice_ingestion.extract import INGESTION_DIR
    from prepaid.store import SEED_PATH as prepaid_seed
    from prepaid.store import STATE_DIR as prepaid_state
    from reporting.ledger import DATA_REPORTING
    from tools import DATA_DIR

    return {
        "tools_data": Path(DATA_DIR),
        "cash_demo": Path(cash_root),
        "fixtures": Path(FIXTURES),
        "ingestion": Path(INGESTION_DIR),
        "reporting_data": Path(DATA_REPORTING),
        "audit_data": Path(audit_dir),
        "prepaid_state": Path(prepaid_state),
        "prepaid_seed": Path(prepaid_seed),
        "assets_state": Path(assets_state),
        "assets_seed": Path(SEED_ASSETS),
        "capital_seed": Path(SEED_CANDIDATES),
    }


def clear_loader_caches() -> None:
    from accrual.store import clear_store_cache
    from invoice_ingestion.store import clear_ingestion_cache
    from tools import clear_runtime_invoices

    clear_store_cache()
    clear_ingestion_cache()
    clear_runtime_invoices()


def _rebind_imported_data_dirs(root: Path) -> None:
    """Modules that copied DATA_DIR at import time must see the remapped root."""
    import ar.store as ar_store
    import invoice_ingestion.store as ingest_store
    import scheduling.cash as sched_cash
    import scheduling.pool as sched_pool

    ar_store.DATA_DIR = Path(root)
    ingest_store.DATA_DIR = Path(root)
    sched_cash.DATA_DIR = Path(root)
    sched_pool.DATA_DIR = Path(root)


def restore_loader_paths(snapshot: dict[str, Path]) -> None:
    from audit.store import configure_paths as configure_audit
    from cash_recon.demo import configure_root
    from fixed_assets.store import configure_paths as configure_assets
    from integrations.providers.base import configure_fixtures
    from invoice_ingestion.extract import configure_ingestion_dir
    from prepaid.store import configure_paths as configure_prepaid
    from reporting.ledger import configure_data_reporting

    configure_data_dir(snapshot["tools_data"])
    _rebind_imported_data_dirs(snapshot["tools_data"])
    configure_data_reporting(snapshot["reporting_data"])
    configure_root(snapshot["cash_demo"])
    configure_fixtures(snapshot["fixtures"])
    configure_ingestion_dir(snapshot["ingestion"])
    configure_audit(data_dir=snapshot["audit_data"])
    configure_prepaid(snapshot["prepaid_state"], seed_path=snapshot["prepaid_seed"])
    configure_assets(
        snapshot["assets_state"],
        seed_assets=snapshot["assets_seed"],
        seed_candidates=snapshot["capital_seed"],
    )
    clear_loader_caches()


def _redirect_to_root(root: Path) -> None:
    from audit.store import configure_paths as configure_audit
    from cash_recon.demo import configure_root
    from fixed_assets.store import configure_paths as configure_assets
    from integrations.providers.base import configure_fixtures
    from invoice_ingestion.extract import configure_ingestion_dir
    from prepaid.store import configure_paths as configure_prepaid
    from reporting.ledger import configure_data_reporting

    root = Path(root)
    configure_data_dir(root)
    _rebind_imported_data_dirs(root)
    configure_data_reporting(root / "reporting")
    configure_root(root / "cash_recon")
    configure_fixtures(root / "integrations")
    configure_ingestion_dir(root / "ingestion")
    configure_audit(data_dir=root / "audit")
    configure_prepaid(root / "runs" / "month_end", seed_path=root / "close" / "prepaids.json")
    configure_assets(
        root / "runs" / "month_end",
        seed_assets=root / "close" / "fixed_assets.json",
        seed_candidates=root / "close" / "capital_invoices.json",
    )
    clear_loader_caches()


def apply_data_root(root: Path) -> None:
    """Point existing workflow loaders at ``root`` (typically a generated demo pack)."""
    _STACK.append(snapshot_loader_paths())
    _redirect_to_root(Path(root))


def reset_data_root() -> None:
    """Restore the loader paths that were live before the matching ``apply_data_root``."""
    if _STACK:
        restore_loader_paths(_STACK.pop())
        return
    restore_loader_paths(CANONICAL)


def drain_data_root_stack() -> None:
    """Undo every unmatched ``apply_data_root`` without forcing repo ``runs/`` paths."""
    while _STACK:
        restore_loader_paths(_STACK.pop())


@contextmanager
def data_root(root: Path):
    apply_data_root(Path(root))
    try:
        yield
    finally:
        reset_data_root()

"""Apply a generated data-root to every existing loader that has a fixed path."""

from __future__ import annotations

from pathlib import Path

from tools import DATA_DIR, configure_data_dir

_DEFAULTS: dict[str, Path] | None = None


def _capture_defaults() -> dict[str, Path]:
    from cash_recon.demo import ROOT as cash_root
    from integrations.providers.base import FIXTURES
    from invoice_ingestion.extract import INGESTION_DIR
    from reporting.ledger import DATA_REPORTING
    from audit.store import DATA_DIR as audit_dir
    from prepaid.store import SEED_PATH as prepaid_seed
    from fixed_assets.store import SEED_ASSETS, SEED_CANDIDATES

    return {
        "data": Path(DATA_DIR),
        "cash": Path(cash_root),
        "fixtures": Path(FIXTURES),
        "ingestion": Path(INGESTION_DIR),
        "reporting": Path(DATA_REPORTING),
        "audit": Path(audit_dir),
        "prepaid": Path(prepaid_seed),
        "assets": Path(SEED_ASSETS),
        "capital": Path(SEED_CANDIDATES),
    }


def apply_data_root(root: Path) -> None:
    """Point existing workflow loaders at ``root`` (typically ``data/demo``)."""
    global _DEFAULTS
    root = Path(root)
    if _DEFAULTS is None:
        _DEFAULTS = _capture_defaults()

    from accrual.store import clear_store_cache
    from audit.store import configure_paths as configure_audit
    from cash_recon.demo import configure_root
    from fixed_assets.store import configure_paths as configure_assets
    from integrations.providers.base import configure_fixtures
    from invoice_ingestion.extract import configure_ingestion_dir
    from invoice_ingestion.store import clear_ingestion_cache
    from prepaid.store import configure_paths as configure_prepaid
    from reporting.ledger import configure_data_reporting

    configure_data_dir(root)
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
    clear_store_cache()
    clear_ingestion_cache()


def reset_data_root() -> None:
    """Restore the repository's default ``data/`` loaders."""
    global _DEFAULTS
    defaults = _DEFAULTS or _capture_defaults()
    apply_data_root(defaults["data"])
    from cash_recon.demo import configure_root
    from integrations.providers.base import configure_fixtures
    from invoice_ingestion.extract import configure_ingestion_dir
    from reporting.ledger import configure_data_reporting
    from audit.store import configure_paths as configure_audit
    from prepaid.store import configure_paths as configure_prepaid
    from fixed_assets.store import configure_paths as configure_assets

    configure_data_dir(defaults["data"])
    configure_data_reporting(defaults["reporting"])
    configure_root(defaults["cash"])
    configure_fixtures(defaults["fixtures"])
    configure_ingestion_dir(defaults["ingestion"])
    configure_audit(data_dir=defaults["audit"])
    configure_prepaid(
        Path(__file__).resolve().parent.parent / "runs" / "month_end",
        seed_path=defaults["prepaid"],
    )
    configure_assets(
        Path(__file__).resolve().parent.parent / "runs" / "month_end",
        seed_assets=defaults["assets"],
        seed_candidates=defaults["capital"],
    )
    _DEFAULTS = None

"""Point Kernel DATA_DIR and RUNS_DIR at one Computer tree.

Choice (session 02; later sessions must use the same env):

    HARNESS_COMPUTER=<repo>/.cfo-v2/office/computer
    CFO_EVAL_PHASE=operational
    PYTHONPATH=<repo>/.cfo

    DATA_DIR = $HARNESS_COMPUTER/data
    RUNS     = $HARNESS_COMPUTER/runs

``data/`` is the seed tree (symlink or copy of ``.cfo/data``).
``runs/`` is mutable overlay / cases / packets / traces.
Idempotency and kernel logs live under ``$HARNESS_COMPUTER/cfo/``.

Do not point live Bots at ``.cfo/runs``. The Sidecar remaps every
``configure_*`` helper onto the Computer at start.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

KERNEL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = KERNEL_ROOT.parent
DEFAULT_COMPUTER = REPO_ROOT / ".cfo-v2" / "office" / "computer"

_COMPUTER: "Computer | None" = None


@dataclass(frozen=True)
class Computer:
    root: Path
    data: Path
    runs: Path
    cfo: Path

    @property
    def catalog_path(self) -> Path:
        return self.cfo / "catalog.json"

    @property
    def grants_path(self) -> Path:
        return self.cfo / "grants.json"

    @property
    def slug_map_path(self) -> Path:
        return self.cfo / "slug-map.json"

    @property
    def idempotency_dir(self) -> Path:
        return self.cfo / "idempotency"

    @property
    def log_path(self) -> Path:
        return self.cfo / "kernel.log.jsonl"

    @property
    def port_path(self) -> Path:
        return self.cfo / "kernel.port"


def current() -> Computer:
    if _COMPUTER is None:
        raise RuntimeError("Sidecar has no Computer. Call attach_computer first.")
    return _COMPUTER


def eval_phase() -> str:
    phase = os.environ.get("CFO_EVAL_PHASE", "operational").strip().lower()
    if phase in {"evaluation", "eval"}:
        return "evaluation"
    return "operational"


def attach_computer(root: Path) -> Computer:
    """Remap Kernel loaders onto ``<computer>/data`` and ``<computer>/runs``."""
    global _COMPUTER
    computer = Path(root).resolve()
    data = computer / "data"
    runs = computer / "runs"
    cfo = computer / "cfo"
    if not data.exists():
        raise FileNotFoundError(
            f"Computer data directory missing: {data}. "
            "Symlink or copy .cfo/data here. See cfo_kernel.paths."
        )
    runs.mkdir(parents=True, exist_ok=True)
    cfo.mkdir(parents=True, exist_ok=True)
    (cfo / "idempotency").mkdir(parents=True, exist_ok=True)
    (runs / "ingestion").mkdir(parents=True, exist_ok=True)
    (runs / "inbox").mkdir(parents=True, exist_ok=True)
    (runs / "ap").mkdir(parents=True, exist_ok=True)
    (runs / "cash_recon" / "cases").mkdir(parents=True, exist_ok=True)
    (runs / "bs_recon" / "packets").mkdir(parents=True, exist_ok=True)
    (runs / "accruals").mkdir(parents=True, exist_ok=True)
    (runs / "month_end").mkdir(parents=True, exist_ok=True)
    (runs / "ar").mkdir(parents=True, exist_ok=True)
    (runs / "audit").mkdir(parents=True, exist_ok=True)
    (runs / "reporting").mkdir(parents=True, exist_ok=True)
    (runs / "integrations").mkdir(parents=True, exist_ok=True)
    (runs / "cash_traces").mkdir(parents=True, exist_ok=True)

    _remap_kernel(data, runs)
    bound = Computer(root=computer, data=data, runs=runs, cfo=cfo)
    _COMPUTER = bound
    return bound


def _remap_kernel(data: Path, runs: Path) -> None:
    from accrual.ledger import configure_paths as configure_accrual_ledger
    from ar.store import configure_paths as configure_ar
    from audit.store import configure_paths as configure_audit
    from bs_recon.store import configure_paths as configure_recon
    from bs_recon.tools import configure_packet_store
    from cash_recon.demo import configure_root as configure_cash_demo
    from cash_recon.case_store import configure_case_dir
    from cash_recon.store import configure_paths as configure_cash_store
    from close.context import configure_paths as configure_ctx
    from close.ledger import configure_paths as configure_gl
    from close.month_end import configure_paths as configure_close
    from fixed_assets.store import configure_paths as configure_assets
    from integrations.providers.base import configure_fixtures
    from invoice_ingestion.extract import configure_ingestion_dir
    from invoice_ingestion.registry import configure_paths as configure_registry
    from prepaid.store import configure_paths as configure_prepaid
    from reporting.ledger import configure_data_reporting, configure_paths as configure_reporting_ledger
    from reporting.store import configure_paths as configure_reporting_store
    from tools import configure_data_dir, configure_overlay_path

    try:
        from inbox.store import configure_runs_dir as configure_inbox
    except ImportError:
        configure_inbox = None

    import ar.store as ar_store
    import accrual.workflow as accrual_workflow
    import integrations.store as integration_store
    import invoice_ingestion.store as ingest_store
    import invoice_ingestion.workflow as ingest_workflow
    import scheduling.cash as sched_cash
    import scheduling.pool as sched_pool
    import scheduling.workflow as sched_workflow
    import workflow as ap_workflow

    month_end = runs / "month_end"
    configure_data_dir(data)
    ar_store.DATA_DIR = data
    ingest_store.DATA_DIR = data
    sched_cash.DATA_DIR = data
    sched_pool.DATA_DIR = data
    configure_data_reporting(data / "reporting")
    configure_reporting_ledger(runs / "reporting")
    configure_reporting_store(runs / "reporting")
    configure_cash_demo(data / "cash_recon")
    configure_fixtures(data / "integrations")
    configure_ingestion_dir(data / "ingestion")
    configure_audit(data_dir=data / "audit", runs_dir=runs / "audit")
    configure_prepaid(month_end, seed_path=data / "close" / "prepaids.json")
    configure_assets(
        month_end,
        seed_assets=data / "close" / "fixed_assets.json",
        seed_candidates=data / "close" / "capital_invoices.json",
    )
    configure_gl(month_end)
    configure_ctx(month_end)
    configure_close(month_end)
    configure_recon(month_end)
    configure_ar(runs / "ar")
    configure_cash_store(runs_dir=runs / "cash_recon", traces_dir=runs / "cash_traces")
    configure_accrual_ledger(runs / "accruals")
    configure_overlay_path(runs / "ingestion" / "overlay.json")
    configure_registry(runs / "ingestion")
    if configure_inbox is not None:
        configure_inbox(runs / "inbox")
    configure_case_dir(runs / "cash_recon" / "cases")
    configure_packet_store(runs / "bs_recon" / "packets")

    ap_workflow.RUNS_DIR = runs
    ingest_workflow.RUNS_DIR = runs / "ingestion"
    accrual_workflow.RUNS_DIR = runs
    sched_workflow.RUNS_DIR = runs
    sched_pool.POOL_PATH = runs / "approved_pool.json"
    integration_store.RUNS_DIR = runs / "integrations"
    integration_store.STATE_PATH = integration_store.RUNS_DIR / "state.json"

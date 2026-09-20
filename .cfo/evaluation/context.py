"""Point existing workflow loaders at the generated operational dataset."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from evaluation.isolation import operational_phase_guard
from sample_data.paths import apply_data_root, reset_data_root


def isolate_run_stores(run_dir: Path) -> None:
    """Keep benchmark side effects inside the evaluation run directory."""
    from ar.store import configure_paths as configure_ar
    from audit.store import configure_paths as configure_audit_runs
    from cash_recon.store import configure_paths as configure_cash
    from close.month_end import configure_paths as configure_close
    from memory.store import configure_paths as configure_memory
    from reporting.store import configure_paths as configure_reporting

    run_dir = Path(run_dir)
    configure_ar(run_dir / "ar")
    configure_close(run_dir / "month_end")
    configure_reporting(run_dir / "reporting")
    configure_audit_runs(runs_dir=run_dir / "audit")
    configure_cash(runs_dir=run_dir / "cash_recon", traces_dir=run_dir / "cash_traces")
    configure_memory(run_dir / "memory")


def _snapshot_store_paths() -> dict:
    from ar import store as ar_store
    from audit import store as audit_store
    from cash_recon import store as cash_store
    from close import month_end as close_month_end
    from memory.store import current_directory as memory_directory
    from reporting import store as reporting_store

    return {
        "ar": ar_store.STATE_DIR,
        "audit_runs": audit_store.RUNS_DIR,
        "cash_runs": cash_store.RUNS_DIR,
        "cash_traces": cash_store.TRACES_DIR,
        "close": close_month_end.STATE_DIR,
        "memory": memory_directory(),
        "reporting": reporting_store.STATE_DIR,
    }


def _restore_store_paths(snapshot: dict) -> None:
    from ar.store import configure_paths as configure_ar
    from audit.store import configure_paths as configure_audit_runs
    from cash_recon.store import configure_paths as configure_cash
    from close.month_end import configure_paths as configure_close
    from memory.store import configure_paths as configure_memory
    from reporting.store import configure_paths as configure_reporting

    configure_ar(snapshot["ar"])
    configure_close(snapshot["close"])
    configure_reporting(snapshot["reporting"])
    configure_audit_runs(runs_dir=snapshot["audit_runs"])
    configure_cash(runs_dir=snapshot["cash_runs"], traces_dir=snapshot["cash_traces"])
    configure_memory(snapshot["memory"])


@contextmanager
def operational_dataset(data_root: Path, run_dir: Path):
    """Apply the generated data-root for workflows; restore defaults after."""
    apply_data_root(Path(data_root))
    previous = _snapshot_store_paths()
    isolate_run_stores(Path(run_dir))
    try:
        with operational_phase_guard():
            yield
    finally:
        reset_data_root()
        _restore_store_paths(previous)

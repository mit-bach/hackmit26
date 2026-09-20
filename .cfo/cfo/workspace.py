"""Isolate the connected CFO demo so it does not mutate a developer's default run dirs."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from memory.scenarios import isolated_memory_workspace


@contextmanager
def isolated_cfo_workspace(root: Path):
    from ar.store import configure_paths as configure_ar
    from ar.store import reset_state as reset_ar
    from audit.store import configure_paths as configure_audit
    from bs_recon.store import configure_paths as configure_recon
    from close.context import configure_paths as configure_ctx
    from fixed_assets.store import configure_paths as configure_assets
    from reporting.ledger import configure_paths as configure_reporting_ledger
    from reporting.ledger import reset_ledger as reset_reporting_ledger
    from reporting.store import configure_paths as configure_reporting
    from reporting.store import reset_store as reset_reporting

    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    configure_ar(root / "ar")
    reset_ar()
    configure_audit(runs_dir=root / "audit")
    configure_recon(root / "recon")
    configure_ctx(root / "identity")
    configure_assets(root / "assets")
    configure_reporting_ledger(root / "reporting-ledger")
    configure_reporting(root / "reporting")
    reset_reporting_ledger()
    reset_reporting()
    with isolated_memory_workspace(root):
        yield root

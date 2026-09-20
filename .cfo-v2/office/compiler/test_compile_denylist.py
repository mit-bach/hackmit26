from __future__ import annotations

from pathlib import Path

from compiler.compile_lib import compile_catalog

REPO = Path(__file__).resolve().parents[3]
KERNEL = REPO / ".cfo"


def test_payment_audit_denylist_strips_scheduler_rebuild_ops(tmp_path) -> None:
    out = tmp_path / "cfo"
    out.mkdir()
    result = compile_catalog(kernel=KERNEL, out_dir=out, phase="operational")
    payment_audit = result.grants["byDisplayName"]["Payment Audit"]["ops"]
    scheduler = result.grants["byDisplayName"]["Payment Scheduler"]["ops"]
    assert "scheduling.tools.get_payment_candidates" in scheduler
    assert "scheduling.tools.get_payment_candidates" not in payment_audit
    assert "scheduling.tools.get_approved_pool" not in payment_audit
    assert "accrual.tools.create_accrual" not in payment_audit
    lock = result.grants["byDisplayName"]["Month-End Close Reviewer"]["ops"]
    assert "accrual.tools.create_accrual" not in lock
    reviewer = result.grants["byDisplayName"]["AP Reviewer"]["ops"]
    assert "tools.get_invoice" not in reviewer

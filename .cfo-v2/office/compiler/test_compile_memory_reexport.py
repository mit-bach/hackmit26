"""Compiler must follow memory re-exports and inbox function_tool() wrappers."""

from __future__ import annotations

from pathlib import Path

from compiler.compile_lib import compile_catalog
import shutil

REPO = Path(__file__).resolve().parents[3]
KERNEL = REPO / ".cfo"
OVERRIDES = REPO / ".cfo-v2" / "office" / "computer" / "cfo" / "catalog.overrides.json"


def test_compile_includes_memory_and_inbox_ops(tmp_path) -> None:
    out = tmp_path / "cfo"
    out.mkdir()
    shutil.copyfile(OVERRIDES, out / "catalog.overrides.json")
    result = compile_catalog(kernel=KERNEL, out_dir=out, phase="operational")
    grants = result.grants["byDisplayName"]
    catalog_ids = {row["id"] for row in result.catalog["ops"]}

    assert "memory.tools.get_decision_memories" in catalog_ids
    assert "inbox.tools.dispatch_inbox_action" in catalog_ids
    assert "memory.tools.get_decision_memories" in grants["Exception Investigator"]["ops"]
    assert "memory.tools.get_decision_memories" in grants["Accrual Agent"]["ops"]
    assert "memory.tools.get_decision_memories" in grants["Cash Exception Investigator"]["ops"]
    assert "memory.tools.get_decision_memories" in grants["Prepaid Preparer"]["ops"]
    assert "prior-period-precedent" in grants["Exception Investigator"]["skills"]
    assert "prior-period-precedent" in grants["Accrual Agent"]["skills"]
    assert "inbox.tools.dispatch_inbox_action" in grants["Finance Inbox Agent"]["ops"]
    assert "inbox.tools.dispatch_inbox_action" not in grants["Counterparty Message Agent"]["ops"]
    assert "accrual.tools.create_accrual" not in grants["Finance Inbox Agent"]["ops"]

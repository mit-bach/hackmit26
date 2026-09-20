#!/usr/bin/env python3
"""Session 01 compile proofs. Run from the repo root."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / ".cfo").is_dir() and (parent / ".harness").is_dir():
            return parent
    raise SystemExit("repo root not found")


def main() -> int:
    repo = repo_root()
    compiler = repo / ".cfo-v2" / "office" / "compiler" / "__main__.py"
    out = repo / ".cfo-v2" / "office" / "computer" / "cfo"
    proc = subprocess.run(
        [sys.executable, str(compiler), "--kernel", str(repo / ".cfo"), "--out", str(out), "--phase", "operational"],
        check=False,
    )
    if proc.returncode != 0:
        return proc.returncode
    grants = json.loads((out / "grants.json").read_text(encoding="utf-8"))
    catalog = json.loads((out / "catalog.json").read_text(encoding="utf-8"))
    names = grants["byDisplayName"]
    preparer = names["AP Preparer"]["ops"]
    approver = names["AP Approver"]["ops"]
    auditor = names["Auditor Agent"]["ops"]
    accrual = names["Accrual Agent"]["ops"]
    assert preparer != approver, "AP Preparer grants must not equal AP Approver"
    assert "tools.get_invoice" in preparer
    assert "tools.get_invoice" not in approver
    assert "accrual.tools.create_accrual" not in preparer
    assert "accrual.tools.create_accrual" in accrual
    assert "audit.tools.get_audit_ground_truth" not in auditor
    catalog_ids = {row["id"] for row in catalog["ops"]}
    assert "audit.tools.get_audit_ground_truth" in catalog_ids
    assert "ar.tools.get_ar_close_snapshot" in catalog_ids
    for name, row in names.items():
        assert "ar.tools.get_ar_close_snapshot" not in row["ops"], name
        assert "bs_recon.tools.list_period_reconciliations" not in row["ops"], name
    create_owners = [name for name, row in names.items() if "accrual.tools.create_accrual" in row["ops"]]
    assert create_owners == ["Accrual Agent"], create_owners
    payment_audit = names["Payment Audit"]["ops"]
    assert "scheduling.tools.get_payment_candidates" not in payment_audit
    assert "scheduling.tools.get_approved_pool" not in payment_audit
    assert "accrual.tools.create_accrual" not in payment_audit
    assert "accrual.tools.create_accrual" not in names["Month-End Close Reviewer"]["ops"]
    assert "accrual.tools.create_accrual" not in names["AP Reviewer"]["ops"]
    print("prove.py: compile SoD assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

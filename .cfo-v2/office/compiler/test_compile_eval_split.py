from __future__ import annotations

import json
from pathlib import Path

from compiler.compile_lib import compile_catalog, write_compile_result

REPO = Path(__file__).resolve().parents[3]
KERNEL = REPO / ".cfo"


def test_evaluation_phase_does_not_overwrite_operational_grants_shape(tmp_path):
    out = tmp_path / "cfo"
    out.mkdir()
    result = compile_catalog(kernel=KERNEL, out_dir=out, phase="evaluation")
    write_compile_result(result, out)
    operational = json.loads((out / "grants.json").read_text(encoding="utf-8"))
    evaluation = json.loads((out / "grants.eval.json").read_text(encoding="utf-8"))
    assert "get_audit_ground_truth" not in json.dumps(operational)
    assert "audit.tools.get_audit_ground_truth" in evaluation["byDisplayName"]["Auditor Agent"]["ops"]
    assert result.grants is not result.grants_eval
    payment_audit = operational["byDisplayName"]["Payment Audit"]["ops"]
    assert "scheduling.tools.get_payment_candidates" not in payment_audit
    assert "scheduling.tools.get_approved_pool" not in payment_audit

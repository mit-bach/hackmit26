"""Session 12: sidecar Grant re-check. Wrong Bot cannot post."""

from __future__ import annotations

import json
from pathlib import Path

from cfo_kernel.paths import Computer
from cfo_kernel.rpc import handle_rpc

REPO = Path(__file__).resolve().parents[3]
CFO_DIR = REPO / ".cfo-v2" / "office" / "computer" / "cfo"
RECORD_TOOLS = (
    "tools.get_invoice",
    "tools.get_purchase_order",
    "tools.get_goods_receipt",
    "tools.find_duplicate_invoices",
)


def _computer(tmp_path: Path) -> Computer:
    cfo = tmp_path / "cfo"
    cfo.mkdir()
    for name in ("catalog.json", "grants.json", "slug-map.json"):
        (cfo / name).write_text((CFO_DIR / name).read_text(encoding="utf-8"), encoding="utf-8")
    return Computer(root=tmp_path, data=tmp_path / "data", runs=tmp_path / "runs", cfo=cfo)


def _rpc(computer: Computer, *, op: str, slug: str, profile: str, bot_id: str) -> dict:
    return handle_rpc(
        {
            "op": op,
            "args": {},
            "botId": bot_id,
            "slug": slug,
            "profile": profile,
            "handleId": "h_s12",
            "idempotencyKey": "s12-1",
        },
        computer=computer,
    )


def _error_code(response: dict) -> str:
    err = response.get("error")
    if isinstance(err, dict):
        return str(err.get("code") or "")
    return str(err or "")


def test_ap_prepare_cannot_call_create_accrual_sidecar(tmp_path) -> None:
    computer = _computer(tmp_path)
    response = _rpc(
        computer,
        op="accrual.tools.create_accrual",
        slug="ap",
        profile="prepare",
        bot_id="bot_ap",
    )
    assert response["ok"] is False
    assert _error_code(response) == "forbidden"
    log = (computer.cfo / "kernel.log.jsonl").read_text(encoding="utf-8")
    assert "forbidden" in log
    assert '"ok": true' not in log


def test_ctl_pay_cannot_call_ap_record_tools_sidecar(tmp_path) -> None:
    computer = _computer(tmp_path)
    for op in RECORD_TOOLS:
        response = _rpc(
            computer,
            op=op,
            slug="ctl-pay",
            profile="review-match",
            bot_id="bot_ctl_pay",
        )
        assert response["ok"] is False, op
        assert _error_code(response) == "forbidden", op


def test_audit_operational_cannot_call_ground_truth_sidecar(tmp_path) -> None:
    computer = _computer(tmp_path)
    response = _rpc(
        computer,
        op="audit.tools.get_audit_ground_truth",
        slug="audit",
        profile="interpret",
        bot_id="bot_audit",
    )
    assert response["ok"] is False
    assert _error_code(response) == "forbidden"
    grants = json.loads((CFO_DIR / "grants.json").read_text(encoding="utf-8"))
    assert "audit.tools.get_audit_ground_truth" not in grants["byDisplayName"]["Auditor Agent"]["ops"]
    eval_grants = json.loads((CFO_DIR / "grants.eval.json").read_text(encoding="utf-8"))
    assert "audit.tools.get_audit_ground_truth" in eval_grants["byDisplayName"]["Auditor Agent"]["ops"]

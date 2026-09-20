"""Fake Handle path: source file → ap accepted → ctl-pay accepted."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / ".cfo-v2" / "office" / "tests" / "fake_handles.mjs"
COMPUTER = REPO / ".cfo-v2" / "office" / "computer"


def test_source_to_ap_to_ctl_pay_accepted_not_completed() -> None:
    result = subprocess.run(
        ["node", str(SCRIPT)],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["ap"]["status"] == "accepted"
    assert payload["ctlPay"]["status"] == "accepted"
    assert payload["ap"]["to"] == "ap"
    assert payload["ctlPay"]["to"] == "ctl-pay"
    assert payload["acceptIsNotComplete"] is True
    log = (COMPUTER / "harness" / "protocol.jsonl").read_text(encoding="utf-8")
    assert "send.accepted" in log
    assert payload["ap"]["handleId"] in log
    assert payload["ctlPay"]["handleId"] in log
    assert '"status": "completed"' not in (COMPUTER / "harness" / "bots" / "bot_ap" / "handles" / f"{payload['ap']['handleId']}.json").read_text()
    assert '"status": "completed"' not in (
        COMPUTER / "harness" / "bots" / "bot_ctl_pay" / "handles" / f"{payload['ctlPay']['handleId']}.json"
    ).read_text()

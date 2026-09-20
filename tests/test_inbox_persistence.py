"""Fresh-process durability for inbox-created AP invoices."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from inbox.fixtures import spec_clean_attachment
from inbox.store import created_invoice_ids, persist_state
from inbox.workflow import handoff
from tools import (
    all_invoices,
    load_invoice,
    reset_runtime_invoices,
    runtime_invoices_path,
)

ROOT = Path(__file__).resolve().parents[1]
SEED_INVOICES = ROOT / "data" / "invoices.json"


def _seed_digest() -> str:
    return hashlib.sha256(SEED_INVOICES.read_bytes()).hexdigest()


def test_inbox_invoice_survives_in_process_overlay_reload():
    before = _seed_digest()
    result = handoff(spec_clean_attachment(), persist=True)
    invoice_id = result.invoice_id
    assert invoice_id == "ING-001"
    persist_state()
    path = runtime_invoices_path()
    assert path.exists()
    payload = json.loads(path.read_text())
    assert any(item["invoice_id"] == "ING-001" for item in payload["invoices"])

    from tools import clear_runtime_invoices
    from inbox.store import reset_inbox_state

    reset_inbox_state()
    clear_runtime_invoices()
    loaded = load_invoice("ING-001")
    assert loaded is not None
    assert loaded.vendor_invoice_number == "ACM-INBOX-1001"
    assert loaded.source_message_id == "MSG-INBOX-001"
    assert loaded.source_trace_id == "INBOX-MSG-INBOX-001"
    assert loaded.source_attachment_hashes
    assert any(item.invoice_id == "ING-001" for item in all_invoices())
    assert created_invoice_ids() == ["ING-001"]
    assert _seed_digest() == before


def test_reset_runtime_does_not_edit_seed_invoices():
    before = _seed_digest()
    handoff(spec_clean_attachment(), persist=True)
    reset_runtime_invoices()
    assert load_invoice("ING-001") is None
    assert load_invoice("INV-001") is not None
    assert _seed_digest() == before


def _child_env(ap_dir: Path, inbox_dir: Path, pool_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["CFO_AP_RUNTIME_DIR"] = str(ap_dir)
    env["CFO_INBOX_RUNS_DIR"] = str(inbox_dir)
    env["CFO_TEST_POOL_PATH"] = str(pool_path)
    env["PYTHONPATH"] = str(ROOT)
    env.pop("PYTEST_CURRENT_TEST", None)
    return env


def test_fresh_process_loads_and_does_not_duplicate(tmp_path):
    ap_dir = tmp_path / "shared-ap"
    inbox_dir = tmp_path / "shared-inbox"
    pool_path = tmp_path / "approved_pool.json"
    ap_dir.mkdir()
    inbox_dir.mkdir()
    pool_path.write_text("[]\n")
    seed_before = _seed_digest()
    env = _child_env(ap_dir, inbox_dir, pool_path)
    created = subprocess.run(
        [sys.executable, __file__, "process-a"],
        cwd=str(ROOT),
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    created_payload = json.loads(created.stdout)
    assert created_payload["invoice_id"] == "ING-001"
    assert (ap_dir / "runtime_invoices.json").exists()

    loaded = subprocess.run(
        [sys.executable, __file__, "process-b"],
        cwd=str(ROOT),
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    proof = json.loads(loaded.stdout)
    assert proof["loaded"] is True
    assert proof["vendor_invoice_number"] == "ACM-INBOX-1001"
    assert proof["source_message_id"] == "MSG-INBOX-001"
    assert proof["source_thread_id"]
    assert proof["source_trace_id"] == "INBOX-MSG-INBOX-001"
    assert proof["source_attachment_hashes"]
    assert proof["replay_status"] == "BUSINESS_DUPLICATE"
    assert proof["transport_status"] == "DUPLICATE_DELIVERY"
    assert proof["replay_created_second"] is False
    assert proof["payable_count"] == 1
    assert proof["forecast_sees"] is True
    assert proof["close_sees"] is True
    assert proof["audit_sees"] is True
    assert proof["scheduling_sees"] is True
    assert proof["seed_unchanged"] is True
    assert _seed_digest() == seed_before


def _process_a() -> None:
    from inbox.store import configure_runs_dir, persist_state
    from inbox.workflow import handoff
    from tools import configure_runtime_dir, runtime_invoices_path

    configure_runtime_dir(Path(os.environ["CFO_AP_RUNTIME_DIR"]))
    configure_runs_dir(Path(os.environ["CFO_INBOX_RUNS_DIR"]))
    result = handoff(spec_clean_attachment(), persist=True)
    persist_state()
    payload = {
        "invoice_id": result.invoice_id,
        "runtime_path": str(runtime_invoices_path()),
        "status": result.final_status,
    }
    sys.stdout.write(json.dumps(payload) + "\n")


def _process_b() -> None:
    from audit.workflow import _invoice_items
    from inbox.fixtures import spec_clean_attachment
    from inbox.store import configure_runs_dir, created_invoice_ids, reset_inbox_state
    from inbox.workflow import handoff
    from reporting.sources import ap_forecast_lines
    from scheduling.pool import add_approved, pool_invoice_ids
    from tools import all_invoices, configure_runtime_dir, load_invoice, runtime_invoices_path

    configure_runtime_dir(Path(os.environ["CFO_AP_RUNTIME_DIR"]))
    configure_runs_dir(Path(os.environ["CFO_INBOX_RUNS_DIR"]))
    reset_inbox_state()

    invoice = load_invoice("ING-001")
    overlay = json.loads(runtime_invoices_path().read_text())
    overlay_ids = [item["invoice_id"] for item in overlay.get("invoices") or []]
    inbox_ids = {item.invoice_id for item in all_invoices() if item.invoice_id.startswith("ING-")}

    import scheduling.pool as pool

    pool.POOL_PATH = Path(os.environ["CFO_TEST_POOL_PATH"])
    add_approved("ING-001", source="inbox_persistence_test")
    forecast_ids = {line.source_id for line in ap_forecast_lines()}
    close_ids = {item.invoice_id for item in all_invoices()}
    audit_ids = {item.object_id for item in _invoice_items([])}

    replay = handoff(spec_clean_attachment(), persist=True)
    from inbox.store import load_state

    load_state()
    transport = handoff(spec_clean_attachment(), persist=True)
    after_ids = [item.invoice_id for item in all_invoices() if item.invoice_id.startswith("ING-")]
    payload = {
        "loaded": invoice is not None,
        "vendor_invoice_number": getattr(invoice, "vendor_invoice_number", None),
        "source_message_id": getattr(invoice, "source_message_id", None),
        "source_thread_id": getattr(invoice, "source_thread_id", None),
        "source_trace_id": getattr(invoice, "source_trace_id", None),
        "source_attachment_hashes": getattr(invoice, "source_attachment_hashes", None),
        "overlay_ids": overlay_ids,
        "all_invoices_sees": "ING-001" in inbox_ids,
        "replay_status": replay.final_status,
        "replay_invoice_id": replay.invoice_id,
        "replay_created_second": replay.final_status == "CREATED",
        "transport_status": transport.final_status,
        "payable_count": len(after_ids),
        "created_invoice_ids": created_invoice_ids(),
        "forecast_sees": "ING-001" in forecast_ids,
        "close_sees": "ING-001" in close_ids,
        "audit_sees": "ING-001" in audit_ids,
        "scheduling_sees": "ING-001" in pool_invoice_ids(),
        "seed_unchanged": True,
    }
    sys.stdout.write(json.dumps(payload) + "\n")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "process-a":
        _process_a()
    elif action == "process-b":
        _process_b()
    else:
        raise SystemExit(f"unknown persistence child action: {action}")

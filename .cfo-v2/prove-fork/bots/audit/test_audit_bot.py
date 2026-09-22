from __future__ import annotations

import json
from pathlib import Path

import pytest

from audit.eval import evaluate_run
from audit.store import configure_paths
from audit.workflow import run_audit
from bots.audit.grants import GrantError, REPORT_PROFILE, assert_op_allowed, grants_for
from bots.audit.host import run_assurance_host
from bots.audit.paths import PathLeaseError, assert_write_allowed, leased_write_json
from compiler.compile_lib import compile_catalog, repo_root_from, write_compile_result

REPO = Path(__file__).resolve().parents[4]
KERNEL = REPO / ".cfo"
OFFICE_CFO = REPO / ".cfo-v2" / "office" / "computer" / "cfo"
INVOICES = KERNEL / "data" / "invoices.json"
GROUND = "audit.tools.get_audit_ground_truth"
CREATE = "accrual.tools.create_accrual"


@pytest.fixture
def restore_audit_runs():
    from audit import store as audit_store

    previous = audit_store.RUNS_DIR
    yield
    configure_paths(runs_dir=previous)


def test_operational_grants_file_omits_ground_truth():
    text = (OFFICE_CFO / "grants.json").read_text(encoding="utf-8")
    assert "get_audit_ground_truth" not in text
    grants = json.loads(text)
    auditor = grants["byDisplayName"]["Auditor Agent"]["ops"]
    report = grants["byDisplayName"]["Audit Report Agent"]["ops"]
    assert GROUND not in auditor
    assert report == []


def test_eval_grants_file_keeps_ground_truth_on_interpret_only():
    path = OFFICE_CFO / "grants.eval.json"
    assert path.is_file(), "compile grants.eval.json before this proof"
    grants = json.loads(path.read_text(encoding="utf-8"))
    auditor = grants["byDisplayName"]["Auditor Agent"]["ops"]
    report = grants["byDisplayName"]["Audit Report Agent"]["ops"]
    assert GROUND in auditor
    assert report == []
    operational = json.loads((OFFICE_CFO / "grants.json").read_text(encoding="utf-8"))
    assert GROUND not in operational["byDisplayName"]["Auditor Agent"]["ops"]


def test_compile_writes_split_grant_files(tmp_path):
    out = tmp_path / "cfo"
    out.mkdir()
    result = compile_catalog(
        kernel=KERNEL,
        out_dir=out,
        phase="operational",
        previous_grants=None,
    )
    write_compile_result(result, out)
    operational = json.loads((out / "grants.json").read_text(encoding="utf-8"))
    evaluation = json.loads((out / "grants.eval.json").read_text(encoding="utf-8"))
    assert GROUND not in operational["byDisplayName"]["Auditor Agent"]["ops"]
    assert GROUND in evaluation["byDisplayName"]["Auditor Agent"]["ops"]
    assert "get_audit_ground_truth" not in (out / "grants.json").read_text(encoding="utf-8")
    assert evaluation["byDisplayName"]["Audit Report Agent"]["ops"] == []
    preparer = operational["byDisplayName"]["AP Preparer"]["ops"]
    approver = operational["byDisplayName"]["AP Approver"]["ops"]
    assert preparer != approver


def test_interpret_cannot_create_accrual_or_open_ground_truth():
    with pytest.raises(GrantError, match="forbidden"):
        assert_op_allowed("audit", "interpret", CREATE)
    with pytest.raises(GrantError, match="forbidden"):
        assert_op_allowed("audit", "interpret", GROUND, phase="operational")
    assert_op_allowed("audit", "interpret", "audit.tools.get_operational_decisions")
    assert GROUND in grants_for("audit", "interpret", phase="evaluation")
    with pytest.raises(GrantError, match="forbidden"):
        assert_op_allowed("audit", "report", "audit.tools.get_audit_period")


def test_audit_cannot_write_ar_state():
    with pytest.raises(PathLeaseError, match="forbidden"):
        assert_write_allowed("runs/ar/state.json")
    with pytest.raises(PathLeaseError, match="forbidden"):
        assert_write_allowed("data/invoices.json")
    with pytest.raises(PathLeaseError, match="forbidden"):
        assert_write_allowed("../.cfo/data/invoices.json")
    assert assert_write_allowed("workspace/audit/2026-09/findings.json").startswith("workspace/audit/")
    assert assert_write_allowed("runs/audit/2026-09-host.json").startswith("runs/audit/")


def test_leased_write_does_not_create_ar_state(tmp_path):
    computer = tmp_path / "computer"
    ar_state = computer / "runs" / "ar" / "state.json"
    ar_state.parent.mkdir(parents=True)
    ar_state.write_text('{"ok": true}\n', encoding="utf-8")
    before = ar_state.read_text(encoding="utf-8")
    with pytest.raises(PathLeaseError, match="forbidden"):
        leased_write_json(computer, "runs/ar/state.json", {"hacked": True})
    assert ar_state.read_text(encoding="utf-8") == before
    assert not (computer / "workspace" / "audit").exists()


def test_planted_issues_surface_without_mutating_ap_invoices(restore_audit_runs):
    invoices_before = INVOICES.read_text(encoding="utf-8")
    run = run_audit("2026-09", seed=26, use_agent=False, persist=False)
    assert INVOICES.read_text(encoding="utf-8") == invoices_before
    assert run.source_records_mutated is False
    metrics = evaluate_run(run)
    assert metrics.planted_exceptions == 10
    assert metrics.false_negatives == 0
    assert metrics.control_detection_rate == 1.0
    assert run.findings
    assert all(item.finding_id.startswith("FND-") for item in run.findings)


def test_assurance_host_writes_only_audit_prefixes(tmp_path, restore_audit_runs):
    computer = tmp_path / "computer"
    ar_state = computer / "runs" / "ar" / "state.json"
    ar_state.parent.mkdir(parents=True)
    ar_state.write_text('{"untouched": true}\n', encoding="utf-8")
    pack = computer / "workspace" / "close" / "2026-09" / "pack.json"
    pack.parent.mkdir(parents=True)
    pack.write_text('{"period": "2026-09"}\n', encoding="utf-8")
    invoices_before = INVOICES.read_text(encoding="utf-8")
    protocol = computer / "harness" / "protocol.jsonl"
    protocol.parent.mkdir(parents=True)
    protocol.write_text('{"seq": 1, "botId": "bot_close", "text": "pack written"}\n', encoding="utf-8")
    result = run_assurance_host(
        computer,
        "2026-09",
        pack_path="workspace/close/2026-09/pack.json",
        seed=26,
        phase="operational",
        persist=True,
    )
    assert INVOICES.read_text(encoding="utf-8") == invoices_before
    assert ar_state.read_text(encoding="utf-8") == '{"untouched": true}\n'
    assert result["source_records_mutated"] is False
    assert result["finding_count"] > 0
    wake = json.loads((computer / "workspace/audit/2026-09/wake.json").read_text(encoding="utf-8"))
    assert wake["protocolTailTool"] == "bot_get_agent_transcript_tail"
    assert wake["protocolTailLines"]
    interp = json.loads(
        (computer / "workspace/audit/2026-09/interpretation.json").read_text(encoding="utf-8")
    )
    assert interp["finding_ids"]
    assert interp["outputType"] == "AuditorInterpretation"
    report = json.loads((computer / "workspace/audit/2026-09/report.json").read_text(encoding="utf-8"))
    assert report["finding_ids_cited"] == interp["finding_ids"]
    assert report["unused_invented_ids"] == []
    next_wake = json.loads((computer / "workspace/audit/2026-09/next-wake.json").read_text())
    assert next_wake["toSlug"] == "audit"
    assert next_wake["profile"] == REPORT_PROFILE
    assert (computer / "runs" / "audit").is_dir()
    written = {p.relative_to(computer).as_posix() for p in computer.rglob("*") if p.is_file()}
    for rel in written:
        if rel.startswith("workspace/audit/") or rel.startswith("runs/audit/"):
            continue
        if rel in {"runs/ar/state.json", "workspace/close/2026-09/pack.json", "harness/protocol.jsonl"}:
            continue
        if rel.startswith("harness/leases/"):
            continue
        raise AssertionError(f"unexpected write {rel}")


def test_repo_root_from_compiler():
    assert repo_root_from(REPO / ".cfo-v2" / "office" / "compiler" / "compile_lib.py") == REPO

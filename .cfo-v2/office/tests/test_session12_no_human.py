"""Production hosts do not complete work by asking a human."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

HOST_GLOBS = (
    ".cfo-v2/office/computer/cfo/extensions/*.ts",
    ".cfo-v2/office/compiler/*.py",
    ".cfo-v2/office/source_wakes/*.py",
    ".cfo-v2/office/handles.py",
    ".cfo-v2/office/bots/*/BOT.md",
    ".cfo/cfo_kernel/*.py",
    ".cfo/workflow.py",
    ".cfo/ap_grants.py",
    ".cfo/agent.py",
)


def _iter_hosts() -> list[Path]:
    out: list[Path] = []
    for pattern in HOST_GLOBS:
        out.extend(REPO.glob(pattern))
    return [path for path in out if path.is_file() and path.suffix in {".py", ".ts"}]


def test_no_ask_user_call_in_production_hosts() -> None:
    hits: list[str] = []
    for path in _iter_hosts():
        text = path.read_text(encoding="utf-8")
        if "ask_user(" in text:
            hits.append(str(path.relative_to(REPO)))
    assert hits == []


def test_no_waiting_for_human_in_production_hosts() -> None:
    hits: list[str] = []
    for path in _iter_hosts():
        text = path.read_text(encoding="utf-8").lower()
        if "waiting for human" in text:
            hits.append(str(path.relative_to(REPO)))
    assert hits == []


def test_pay_run_and_lock_route_to_verifiers_not_operator() -> None:
    verifier = (REPO / ".cfo-v2/office/computer/cfo/extensions/verifier.ts").read_text(
        encoding="utf-8"
    )
    assert 'slug: "ctl-pay"' in verifier
    assert 'slug: "ctl-books"' in verifier
    assert "ask_user(" not in verifier
    call = (REPO / ".cfo-v2/office/computer/cfo/extensions/call.ts").read_text(encoding="utf-8")
    assert "verifier_required" in call
    assert "operator approval" not in call.lower()

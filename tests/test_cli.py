from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_unknown_invoice_cli():
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "INV-999"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "Unknown invoice ID" in result.stdout


def test_usage_cli():
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "Usage: python main.py INV-001" in result.stdout
    assert "python main.py schedule" in result.stdout
    assert "python main.py ingest" in result.stdout
    assert "python main.py skills" in result.stdout


def test_missing_api_key_message():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "INV-001"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 1
    assert "OPENAI_API_KEY is not set" in result.stdout


def test_ingest_cli_runs_without_api_key():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "ingest", "2026-09", "--no-ap"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert "Invoice Ingestion — 2026-09" in result.stdout
    assert "INV-9001" in result.stdout
    assert "Cross-source duplicates" in result.stdout
    assert "2" in result.stdout


def test_ingest_replay_cli_reports_idempotency():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "ingest", "2026-09", "--replay-check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert "Re-running ingestion" in result.stdout
    assert "New canonical invoices: 0" in result.stdout
    assert "New AP handoffs: 0" in result.stdout
    assert "Idempotency check: PASS" in result.stdout


def test_schedule_empty_pool_requires_api_or_seed():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "schedule"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 1
    assert "OPENAI_API_KEY is not set" in result.stdout


def test_skills_cli_lists_assignments_without_api_key():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "skills"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert "Accrual Agent" in result.stdout
    assert "accrual-method-selection" in result.stdout
    assert "Payment Scheduler" in result.stdout
    assert "early-payment-discount-evaluation" in result.stdout
    assert "ERP Invoice Agent" in result.stdout
    assert "## Purpose" not in result.stdout


def test_skills_cli_agent_detail():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "skills", "--agent", "accrual"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert "Accrual Agent" in result.stdout
    assert "skills/accrual-evidence-evaluation/SKILL.md" in result.stdout
    assert "content_hash:" in result.stdout
    assert "injected: yes" in result.stdout
    assert "payment-prioritization" not in result.stdout
    assert "## Procedure" not in result.stdout


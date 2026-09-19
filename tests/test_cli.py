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
    assert "python main.py integration-demo" in result.stdout
    assert "python main.py skills" in result.stdout
    assert "python main.py ar-aging" in result.stdout
    assert "python main.py ar-demo" in result.stdout
    assert "python main.py cash-forecast" in result.stdout
    assert "python main.py ar-forecast-demo" in result.stdout
    assert "python main.py ar-review-list" in result.stdout
    assert "python main.py reconcile-cash" in result.stdout
    assert "python main.py eval-cash-reconciliation" in result.stdout
    assert "python main.py audit-demo" in result.stdout
    assert "python main.py audit-demo --adversarial" in result.stdout
    assert "python main.py audit-trace" in result.stdout
    assert "python main.py eval-audit" in result.stdout
    assert "python main.py demo-reporting" in result.stdout
    assert "python main.py generate-sample-data" in result.stdout
    assert "python main.py validate-sample-data" in result.stdout
    assert "python main.py evaluate-cfo" in result.stdout
    assert "python main.py close-month" in result.stdout
    assert "python main.py eval-close" in result.stdout


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


def test_ar_aging_cli_runs_without_api_key():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "ar-aging", "--reset", "--as-of", "2026-09-30"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert "RECEIVABLES AGING" in result.stdout
    assert "INV-AR-017" in result.stdout


def test_ar_demo_cli_runs_without_api_key():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "ar-demo"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert "ACCOUNTS RECEIVABLE DEMO" in result.stdout
    assert "AUTO_APPLY" in result.stdout
    assert "HUMAN_REVIEW" in result.stdout
    assert "AR balances were not changed" in result.stdout


def test_ar_forecast_demo_cli_runs_without_api_key():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "ar-forecast-demo"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert "AR + 13-WEEK CASH FORECAST DEMO" in result.stdout
    assert "HUMAN_REVIEW" in result.stdout
    assert "CORRECTED" in result.stdout
    assert "INV-AR-101" in result.stdout
    assert "INV-AR-102" in result.stdout
    assert "13-WEEK CASH FORECAST" in result.stdout
    assert "AR-PREC" in result.stdout or "precedent" in result.stdout.lower() or "batch_payment" in result.stdout


def test_integration_demo_cli_runs_without_api_key():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "integration-demo"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert "Real Finance Integrations Demo" in result.stdout
    assert "Idempotency check: PASS" in result.stdout


def test_stripe_demo_cli_runs_without_api_key():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "stripe-demo"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert "Stripe payout reconciliation" in result.stdout
    assert "Idempotency: PASS" in result.stdout
    assert "sk_" not in result.stdout
    assert "whsec_" not in result.stdout


def test_reconcile_cash_cli_runs_without_api_key():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "reconcile-cash", "--month", "2026-09", "--seed-demo", "--reset"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert "September 2026 Cash Reconciliation" in result.stdout
    assert "Unexplained difference: $12.40" in result.stdout
    assert "GROUPED_MATCH" in result.stdout
    assert "FEE_NETTED" in result.stdout
    assert "POSSIBLE_DUPLICATE_REFUND" in result.stdout
    assert "PROVIDER_PAYOUT" in result.stdout
    assert "HUMAN_REVIEW" in result.stdout
    assert "OUTSTANDING_TIMING_ITEM" in result.stdout


def test_audit_trace_cli_runs_without_api_key():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "audit-trace", "--period", "2026-09"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "CROSS-WORKFLOW EVIDENCE TRACE" in result.stdout
    assert "INV-AUD-OK-001" in result.stdout
    assert "PAY-AUD-001" in result.stdout


def test_audit_demo_cli_runs_without_api_key():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "audit-demo"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert "INDEPENDENT AUDITOR DEMO" in result.stdout
    assert "We ran the finance workflow first" in result.stdout
    assert "Control detection rate: 100.00%" in result.stdout


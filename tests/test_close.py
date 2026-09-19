from close.orchestrator import run_cfo_close
from close.safeguards import assert_close_invariants
from scheduling.pool import load_pool
from tools import collect_case_evidence, load_invoice


def _patch_close(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    monkeypatch.setattr("accrual.ledger.LEDGER_DIR", tmp_path)
    monkeypatch.setattr("close.orchestrator.CLOSE_DIR", tmp_path / "close")
    monkeypatch.setattr("accrual.workflow.RUNS_DIR", tmp_path / "accrual-runs")


def _close(tmp_path, monkeypatch, **kwargs):
    _patch_close(tmp_path, monkeypatch)
    return run_cfo_close(
        "2026-09",
        live=False,
        featured_ap=(),
        use_agent_accrual=False,
        **kwargs,
    )


def test_received_invoice_does_not_become_an_accrual(tmp_path, monkeypatch):
    state = _close(tmp_path, monkeypatch)
    accrued = {item.vendor for item in state.accrual.accruals_created}
    assert "Amazon Web Services" not in accrued
    aws = next(item for item in state.discovery.results if item.vendor == "Amazon Web Services")
    assert aws.invoice_received is True
    assert aws.missing_bill_candidate is False


def test_hold_invoice_does_not_enter_payment_scheduling(tmp_path, monkeypatch):
    state = _close(tmp_path, monkeypatch)
    assert "INV-016" in state.held_ids
    assert "INV-016" not in state.approved_ids
    pool_ids = {row["invoice_id"] for row in load_pool()}
    assert "INV-016" not in pool_ids
    paid = {row.invoice_id for row in state.payment.plan.pay_this_week}
    deferred = {row.invoice_id for row in state.payment.plan.defer}
    assert "INV-016" not in paid
    assert "INV-016" not in deferred


def test_approved_invoice_can_enter_payment_scheduling(tmp_path, monkeypatch):
    state = _close(tmp_path, monkeypatch)
    assert "INV-001" in state.approved_ids
    pool_ids = {row["invoice_id"] for row in load_pool()}
    assert "INV-001" in pool_ids
    considered = {item.invoice_id for item in state.payment.candidates}
    assert "INV-001" in considered


def test_accrual_does_not_become_payable_before_invoice(tmp_path, monkeypatch):
    state = _close(tmp_path, monkeypatch)
    pool_ids = {row["invoice_id"] for row in load_pool()}
    assert not any(str(item).startswith("ACC-") for item in pool_ids)
    accrued_vendors = {item.vendor for item in state.accrual.accruals_created}
    assert "Aether Compute" in accrued_vendors
    payable_vendors = {row["vendor"] for row in load_pool()}
    assert "Aether Compute" not in payable_vendors


def test_reconciled_accrual_closes(tmp_path, monkeypatch):
    from accrual.ledger import get_open_accruals

    state = _close(tmp_path, monkeypatch, reconcile_vendors=("Aether Compute",))
    assert state.reconciliations
    assert state.reconciliations[0].vendor == "Aether Compute"
    assert state.reconciliations[0].actual_invoice_id
    assert get_open_accruals(period="2026-09", vendor="Aether Compute") == []


def test_duplicate_obligations_are_not_counted_twice(tmp_path, monkeypatch):
    state = _close(tmp_path, monkeypatch)
    assert len(state.invoice_ids) == len(set(state.invoice_ids))
    assert state.invoices_received == len(state.invoice_ids)
    aws_ap = [item for item in state.ap_results if item.vendor == "Amazon Web Services"]
    assert {item.invoice_id for item in aws_ap} == {"INV-002", "INV-016"}
    assert "Amazon Web Services" not in {item.vendor for item in state.accrual.accruals_created}
    payout_ids = {item.payout_id for item in state.integrations if item.payout_id}
    assert payout_ids.isdisjoint(set(state.invoice_ids))


def test_close_totals_reconcile_across_workflows(tmp_path, monkeypatch):
    state = _close(tmp_path, monkeypatch)
    assert_close_invariants(state)
    assert len(state.approved_ids) + len(state.held_ids) == state.invoices_received
    assert state.accrual.vendors_reviewed == (
        len(state.accrual.accruals_created)
        + len(state.accrual.no_accrual_needed)
        + len(state.accrual.uncertain_items)
    )
    planned = len(state.payment.plan.pay_this_week) + len(state.payment.plan.defer)
    assert planned == len(state.payment.candidates)
    assert planned == len(state.approved_ids)
    assert abs(
        state.accrual.total_accrued_expense
        - sum(item.estimated_amount or 0 for item in state.accrual.accruals_created)
    ) < 0.001


def test_existing_ap_lookup_unchanged():
    invoice = load_invoice("INV-001")
    assert invoice.vendor == "Acme Supplies"
    assert collect_case_evidence("INV-001").exception_types == []
    assert collect_case_evidence("INV-016").exception_types == ["missing_po"]


def test_close_cli_is_wired():
    import main

    assert "close" in main.__doc__
    assert "demo-close" in main.__doc__


def test_outlook_helios_invoice_is_not_accrued(tmp_path, monkeypatch):
    state = _close(tmp_path, monkeypatch)
    assert any("HEL-INV-6200" in item.invoice_numbers for item in state.integrations)
    assert "Helios Hardware" not in {item.vendor for item in state.accrual.accruals_created}


def test_live_ap_is_limited_to_featured_invoices(monkeypatch):
    from close.models import APCloseResult
    from close.orchestrator import decide_ap

    called: list[str] = []

    def fake_live(invoice_id: str) -> APCloseResult:
        called.append(invoice_id)
        invoice = load_invoice(invoice_id)
        return APCloseResult(
            invoice_id=invoice_id,
            vendor=invoice.vendor,
            amount=invoice.amount,
            decision="APPROVE",
            source="ap_workflow",
            ap_decision_id=f"live/{invoice_id}",
        )

    monkeypatch.setattr("close.orchestrator._live_ap_decision", fake_live)
    featured = decide_ap("INV-001", live=True, featured={"INV-001"})
    other = decide_ap("INV-016", live=True, featured={"INV-001"})
    assert called == ["INV-001"]
    assert featured.source == "ap_workflow"
    assert other.source == "ap_policy"
    assert other.decision == "HOLD"


def test_deterministic_close_uses_policy_not_stale_traces():
    from close.orchestrator import decide_ap

    result = decide_ap("INV-001", live=False, featured=set())
    assert result.source == "ap_policy"
    assert result.decision == "APPROVE"

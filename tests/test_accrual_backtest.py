from accrual.backtest import compute_backtest_metrics, run_backtest, run_backtest_case
from accrual.cutoff import data_cutoff
from accrual.models import BacktestRecord
from accrual.store import all_accrual_invoices, current_invoices_for, invoices_for_vendor, later_invoices_for, usage_for


def _aether_august():
    return next(
        item
        for item in all_accrual_invoices()
        if item.vendor == "Aether Compute" and item.service_period == "2026-08"
    )


def test_hidden_historical_invoice_is_unavailable():
    hidden = _aether_august()
    with data_cutoff("2026-08", hide_period_invoices=True, allow_later_invoices=False):
        invoices = current_invoices_for("Aether Compute", "2026-08")
        assert invoices == []
        assert hidden.invoice_id not in {item.invoice_id for item in invoices_for_vendor("Aether Compute")}
        usage = usage_for("Aether Compute", "2026-08")
        assert usage
        assert usage[0].period == "2026-08"


def test_future_period_data_cannot_leak():
    with data_cutoff("2026-08", hide_period_invoices=True, allow_later_invoices=False):
        later = later_invoices_for("Aether Compute", "2026-08")
        assert later == []
        history = invoices_for_vendor("Aether Compute")
        assert history
        assert all(invoice.service_period < "2026-08" for invoice in history)
        assert usage_for("Aether Compute", "2026-09") == []


def test_actual_invoice_revealed_only_after_estimate():
    result = run_backtest_case(_aether_august())
    assert result.estimate_committed_before_reveal is True
    assert result.estimated_amount is not None
    assert result.actual_amount is not None
    assert result.actual_invoice_id
    assert result.future_leak_detected is False


def test_backtest_metrics_calculate_correctly():
    records = [
        BacktestRecord(
            vendor="A",
            period="2026-06",
            selected_method="recent_average",
            estimated_amount=210,
            actual_invoice_id="A-1",
            actual_amount=200,
            error=10,
            absolute_error=10,
            percentage_error=5.0,
        ),
        BacktestRecord(
            vendor="B",
            period="2026-06",
            selected_method="recent_average",
            estimated_amount=180,
            actual_invoice_id="B-1",
            actual_amount=200,
            error=-20,
            absolute_error=20,
            percentage_error=10.0,
        ),
        BacktestRecord(
            vendor="C",
            period="2026-06",
            selected_method="usage_run_rate",
            estimated_amount=100,
            actual_invoice_id="C-1",
            actual_amount=100,
            error=0,
            absolute_error=0,
            percentage_error=0.0,
        ),
    ]
    metrics = compute_backtest_metrics(records)
    assert metrics.invoices_tested == 3
    assert metrics.mean_absolute_error == 10
    assert metrics.median_absolute_error == 10
    assert metrics.mean_absolute_percentage_error == 5.0
    assert metrics.mean_signed_error == -3.33
    assert metrics.within_5_percent == 66.7
    assert metrics.within_10_percent == 100.0
    by_method = {item.method: item for item in metrics.by_method}
    assert by_method["recent_average"].observations == 2
    assert by_method["usage_run_rate"].observations == 1


def test_zero_dollar_actuals_do_not_break_percentage():
    metrics = compute_backtest_metrics(
        [
            BacktestRecord(
                vendor="Zero Co",
                period="2026-06",
                selected_method="recent_average",
                estimated_amount=100,
                actual_invoice_id="Z-1",
                actual_amount=0,
                error=100,
                absolute_error=100,
                percentage_error=None,
            )
        ]
    )
    assert metrics.invoices_tested == 1
    assert metrics.mean_absolute_error == 100
    assert metrics.mean_absolute_percentage_error is None
    assert metrics.within_5_percent is None
    assert metrics.within_10_percent is None


def test_backtest_run_uses_real_fixtures():
    report = run_backtest()
    assert report.metrics.invoices_tested >= 1
    assert report.records
    assert all(row.actual_amount is not None for row in report.records)
    assert all(row.period < "2026-09" for row in report.records)
    assert all(row.future_leak_detected is False for row in report.records)
    assert report.trace_path

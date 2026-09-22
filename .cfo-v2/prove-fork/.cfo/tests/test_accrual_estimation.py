from accrual.estimation import (
    EstimateContext,
    candidates_for,
    coefficient_of_variation,
    compute_estimate,
    last_invoice_amount,
    linear_trend_projection,
    months_between,
    naive_recent_average_is_misleading,
    recent_average,
    simple_average,
    usage_run_rate,
    weighted_recent_average,
)
from accrual.models import AccrualInvoice
from accrual.store import build_estimate_context


def _invoice(period: str, amount: float, vendor: str = "Aether Compute") -> AccrualInvoice:
    return AccrualInvoice(
        invoice_id=f"HI-{period}",
        vendor=vendor,
        amount=amount,
        invoice_date=f"{period}-28",
        service_period=period,
    )


def test_simple_and_weighted_averages():
    amounts = [11100, 11400, 12250]
    assert simple_average(amounts) == 11583.33
    assert recent_average(amounts) == 11583.33
    assert weighted_recent_average(amounts) == 11775.00
    assert last_invoice_amount(amounts) == 12250


def test_linear_trend_projects_next_period():
    amounts = [9200, 9800, 10400, 11100, 11400, 12250]
    assert linear_trend_projection(amounts) == 12766.67


def test_usage_run_rate_matches_metered_bill():
    assert usage_run_rate(142000, 0.08345) == 11849.90


def test_coefficient_of_variation_is_low_for_stable_vendor():
    stable = [2390, 2400, 2410, 2395, 2405]
    growing = [9200, 9800, 10400, 11100, 11400, 12250]
    stable_cv = coefficient_of_variation(stable)
    growing_cv = coefficient_of_variation(growing)
    assert stable_cv is not None and stable_cv < 0.01
    assert growing_cv is not None and growing_cv > 0.08


def test_months_between():
    assert months_between("2026-01", "2026-09") == 8
    assert months_between("2025-09", "2026-09") == 12


def test_harbor_seasonal_naive_average_is_misleading():
    context = build_estimate_context("Harbor Electric", "2026-09")
    recent_amounts = [7200, 8100, 7900]
    assert simple_average(recent_amounts) == 7733.33
    seasonal = compute_estimate(context, "seasonal_prior_year")
    recent = compute_estimate(context, "recent_average")
    assert seasonal.applicable is True
    assert seasonal.amount == 4650
    assert recent.amount == 7733.33
    assert naive_recent_average_is_misleading(context) is True
    assert seasonal.amount < simple_average(recent_amounts) * 0.7


def test_aether_usage_beats_last_month_and_trend():
    context = build_estimate_context("Aether Compute", "2026-09")
    last = compute_estimate(context, "last_invoice")
    trend = compute_estimate(context, "linear_trend")
    usage = compute_estimate(context, "usage_run_rate")
    weighted = compute_estimate(context, "weighted_recent_average")
    recent = compute_estimate(context, "recent_average")
    assert last.amount == 12250
    assert trend.amount == 12766.67
    assert usage.amount == 11849.90
    assert weighted.amount == 11185.71
    assert recent.amount == 11583.33
    assert usage.applicable is True


def test_invoice_already_received_blocks_all_methods():
    context = build_estimate_context("Orbit Analytics", "2026-09")
    candidates = candidates_for(context)
    assert len(candidates) == 1
    assert candidates[0].applicable is False
    assert "already received" in candidates[0].rationale


def test_helios_goods_receipt_candidate():
    context = build_estimate_context("Helios Hardware", "2026-09")
    receipt = compute_estimate(context, "goods_receipt")
    assert receipt.applicable is True
    assert receipt.amount == 6200


def test_newforge_has_no_reliable_estimate():
    context = build_estimate_context("NewForge Consulting", "2026-09")
    applicable = [item for item in candidates_for(context) if item.applicable]
    assert applicable == []


def test_contract_commitment_for_retainer():
    context = build_estimate_context("Lindholm & Ruiz LLP", "2026-09")
    candidate = compute_estimate(context, "contract_commitment")
    assert candidate.applicable is True
    assert candidate.amount == 8500


def test_stale_last_invoice_is_not_applicable():
    context = EstimateContext(
        vendor="One Off Shop",
        period="2026-09",
        historical_invoices=[_invoice("2026-01", 12000, "One Off Shop")],
    )
    candidate = compute_estimate(context, "last_invoice")
    assert candidate.applicable is False

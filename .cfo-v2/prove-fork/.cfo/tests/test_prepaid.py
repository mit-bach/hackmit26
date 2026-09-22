import pytest

from close.dates import money
from close.ledger import find_by_key, load_entries
from prepaid.models import PrepaidItem
from prepaid.posting import amortize_item, post_schedule_line
from prepaid.schedule import generate_schedule, select_treatment, treatment_candidates, validate_prepaid
from prepaid.store import save_items, upsert_item
from prepaid.workflow import run_prepaid_workflow


def _item(**overrides) -> PrepaidItem:
    payload = dict(
        prepaid_id="PRE-TEST",
        vendor="Hartford Insurance",
        description="Annual policy",
        source_document_id="DOC-INS-2026",
        total_amount=12000,
        start_date="2026-09-01",
        end_date="2027-08-31",
        initial_account="Prepaid Insurance",
        expense_account="Insurance Expense",
        evidence_refs=["DOC-INS-2026"],
        created_at="2026-09-01T00:00:00Z",
    )
    payload.update(overrides)
    return PrepaidItem.model_validate(payload)


def test_full_month_straight_line_sums_to_original():
    schedule = generate_schedule(_item())
    assert len(schedule) == 12
    assert all(line.amount == 1000 for line in schedule)
    assert money(sum(line.amount for line in schedule)) == 12000


def test_partial_month_daily_proration_sums():
    item = _item(start_date="2026-09-16", end_date="2026-10-15", total_amount=3000, amortization_method="daily_prorate")
    schedule = generate_schedule(item, "daily_prorate")
    assert len(schedule) == 2
    assert schedule[0].days_in_period == 15
    assert schedule[1].days_in_period == 15
    assert money(sum(line.amount for line in schedule)) == 3000
    assert schedule[0].amount == 1500
    assert schedule[1].amount == 1500


def test_invalid_service_period_and_negative_amount():
    with pytest.raises(ValueError, match="negative"):
        validate_prepaid(_item(total_amount=-10))
    with pytest.raises(ValueError, match="service period"):
        validate_prepaid(_item(start_date="2026-10-01", end_date="2026-09-01"))


def test_amortization_before_and_after_service_rejected():
    item = _item()
    upsert_item(item)
    schedule = generate_schedule(item)
    with pytest.raises(ValueError, match="before the service start"):
        post_schedule_line(item, schedule[0].model_copy(update={"period": "2026-08"}), close_period="2026-09")
    with pytest.raises(ValueError, match="after the service end"):
        post_schedule_line(item, schedule[0].model_copy(update={"period": "2027-09"}), close_period="2026-09")


def test_missing_evidence_blocks_posting():
    item = _item(source_document_id="", evidence_refs=[])
    upsert_item(item)
    schedule = generate_schedule(item)
    with pytest.raises(ValueError, match="Missing evidence"):
        post_schedule_line(item, schedule[0], close_period="2026-09")


def test_duplicate_posting_and_rerun_are_idempotent():
    item = _item()
    upsert_item(item)
    first = amortize_item(item.prepaid_id, "2026-09", method="straight_line_monthly", through_period="2026-09")
    second = amortize_item(item.prepaid_id, "2026-09", method="straight_line_monthly", through_period="2026-09")
    assert [line.journal_entry_id for line in first] == [line.journal_entry_id for line in second]
    assert len([item for item in load_entries() if item["entry_type"] == "prepaid_amortization"]) == 1
    assert find_by_key("prepaid:PRE-TEST:2026-09") is not None


def test_late_discovery_catch_up():
    item = _item(
        prepaid_id="PRE-SFT",
        start_date="2025-10-01",
        end_date="2026-09-30",
        total_amount=24000,
        late_discovery=True,
        initial_account="Prepaid Software",
        expense_account="Software Subscription Expense",
    )
    upsert_item(item)
    posted = amortize_item(item.prepaid_id, "2026-09", method="straight_line_monthly")
    assert len(posted) == 12
    assert money(sum(line.amount for line in posted)) == 24000
    assert {line.period for line in posted} == {
        "2025-10", "2025-11", "2025-12",
        "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06",
        "2026-07", "2026-08", "2026-09",
    }


def test_workflow_skips_missing_evidence():
    save_items([
        _item(),
        _item(prepaid_id="PRE-MISS", source_document_id="", evidence_refs=[], total_amount=3600),
    ])
    report = run_prepaid_workflow("2026-09")
    assert any(item["prepaid_id"] == "PRE-MISS" for item in report.skipped)
    assert all(line.prepaid_id != "PRE-MISS" for line in report.lines_posted)


def test_treatment_candidates_do_not_invent_math():
    item = _item()
    rows = treatment_candidates(item)
    assert {row.method for row in rows} == {"straight_line_monthly", "daily_prorate", "immediate_expense"}
    assert not next(row for row in rows if row.method == "immediate_expense").applicable
    assert select_treatment(item) == "straight_line_monthly"
    same_month = _item(end_date="2026-09-30", total_amount=500)
    assert select_treatment(same_month) == "immediate_expense"


def test_first_middle_and_final_month_amortization():
    item = _item(start_date="2026-07-01", end_date="2027-06-30")
    schedule = generate_schedule(item)
    assert schedule[0].period == "2026-07"
    assert schedule[2].period == "2026-09"
    assert schedule[-1].period == "2027-06"
    assert schedule[0].amount == schedule[2].amount == schedule[-1].amount == 1000
    upsert_item(item)
    posted = amortize_item(item.prepaid_id, "2026-09", method="straight_line_monthly", through_period="2026-09")
    assert len(posted) == 1
    assert posted[0].period == "2026-09"
    assert posted[0].amount == 1000
    journals = [item for item in load_entries() if item["entry_type"] == "prepaid_amortization"]
    assert len(journals) == 1
    assert journals[0]["debit"] == journals[0]["credit"] == 1000
    assert journals[0]["debit_account"] == "Insurance Expense"
    assert journals[0]["credit_account"] == "Prepaid Insurance"


def test_missing_service_period_routes_to_review():
    item = _item(start_date="", end_date="")
    assert select_treatment(item) == "insufficient_evidence"
    save_items([item])
    report = run_prepaid_workflow("2026-09")
    assert any(row["prepaid_id"] == "PRE-TEST" for row in report.skipped)
    assert report.lines_posted == []


def test_over_amortization_is_rejected(monkeypatch):
    item = _item(total_amount=1000)
    upsert_item(item)
    amortize_item(item.prepaid_id, "2026-09", method="straight_line_monthly", through_period="2026-09")
    from prepaid.models import PrepaidScheduleLine

    extra = PrepaidScheduleLine(prepaid_id=item.prepaid_id, period="2026-10", amount=1000, method="straight_line_monthly")
    with pytest.raises(ValueError, match="Over-amortization"):
        post_schedule_line(item, extra, close_period="2026-10")

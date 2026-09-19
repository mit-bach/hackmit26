import pytest

from close.dates import money
from close.ledger import load_entries
from fixed_assets.models import CapitalCandidate, FixedAsset
from fixed_assets.posting import capitalize_asset, post_depreciation
from fixed_assets.schedule import generate_schedule, should_capitalize
from fixed_assets.store import find_duplicates, upsert_asset
from fixed_assets.workflow import run_depreciation_workflow


def _server(**overrides) -> FixedAsset:
    payload = dict(
        asset_id="FA-SRV-001",
        description="PowerEdge R760 server cluster",
        vendor="Dell Technologies",
        acquisition_date="2026-09-05",
        placed_in_service_date="2026-09-05",
        cost=60000,
        salvage_value=6000,
        useful_life_months=36,
        asset_account="Computer Equipment",
        accumulated_depreciation_account="Accumulated Depreciation - Equipment",
        depreciation_expense_account="Depreciation Expense",
        evidence_refs=["DOC-DELL-R760"],
        source_document_id="DOC-DELL-R760",
        transaction_id="INV-021",
        created_at="2026-09-05T00:00:00Z",
    )
    payload.update(overrides)
    return FixedAsset.model_validate(payload)


def test_straight_line_and_salvage_floor():
    schedule = generate_schedule(_server())
    assert len(schedule) == 36
    assert schedule[0].depreciation_amount == 1500
    assert money(sum(line.depreciation_amount for line in schedule)) == 54000
    assert schedule[-1].ending_book_value == 6000
    assert all(line.ending_book_value >= 6000 for line in schedule)


def test_placed_in_service_gate():
    asset = _server()
    upsert_asset(asset)
    with pytest.raises(ValueError, match="placed-in-service"):
        post_depreciation(asset, "2026-08")


def test_duplicate_asset_detection():
    upsert_asset(_server())
    matches = find_duplicates(
        CapitalCandidate(
            candidate_id="INV-021-DUP",
            vendor="Dell Technologies",
            description="duplicate",
            amount=60000,
            invoice_date="2026-09-05",
            source_document_id="DOC-DELL-R760",
            evidence_refs=["DOC-DELL-R760"],
        )
    )
    assert [item.asset_id for item in matches] == ["FA-SRV-001"]


def test_duplicate_depreciation_prevention_and_journal_balance():
    asset = _server()
    upsert_asset(asset)
    first = post_depreciation(asset, "2026-09")
    second = post_depreciation(asset, "2026-09")
    assert first.journal_entry_id == second.journal_entry_id
    journals = [item for item in load_entries() if item["entry_type"] == "depreciation"]
    assert len(journals) == 1
    assert journals[0]["debit"] == journals[0]["credit"] == 1500


def test_accumulated_depreciation_ceiling():
    asset = _server(useful_life_months=2, salvage_value=0, cost=100)
    upsert_asset(asset)
    post_depreciation(asset, "2026-09")
    post_depreciation(asset, "2026-10")
    from fixed_assets.store import lines_for

    posted = lines_for(asset.asset_id, status="posted")
    assert money(sum(item.depreciation_amount for item in posted)) == 100
    assert post_depreciation(asset, "2026-10").journal_entry_id == posted[-1].journal_entry_id


def test_capitalization_policy_and_workflow_duplicate():
    assert should_capitalize(60000, 36)
    assert not should_capitalize(4999, 36)
    upsert_asset(_server())
    report = run_depreciation_workflow("2026-09")
    assert any(item["candidate_id"] == "INV-021-DUP" for item in report.duplicates)
    journals = load_entries()
    assert journals
    assert all(item["debit"] == item["credit"] for item in journals)


def test_seed_server_straight_line_is_one_thousand():
    from fixed_assets.models import FixedAsset

    asset = FixedAsset.model_validate(
        dict(
            asset_id="FA-SRV-024",
            description="Server equipment",
            vendor="Dell Technologies",
            acquisition_date="2026-09-01",
            placed_in_service_date="2026-09-01",
            cost=24000,
            salvage_value=0,
            useful_life_months=24,
            asset_account="Computer Equipment",
            accumulated_depreciation_account="Accumulated Depreciation - Equipment",
            depreciation_expense_account="Depreciation Expense",
            evidence_refs=["DOC-SERVER-24K"],
            source_document_id="DOC-SERVER-24K",
            created_at="2026-09-01T00:00:00Z",
        )
    )
    upsert_asset(asset)
    line = post_depreciation(asset, "2026-09")
    assert line.depreciation_amount == 1000
    assert line.ending_book_value == 23000
    journals = [item for item in load_entries() if item["entry_type"] == "depreciation"]
    assert journals[0]["debit"] == journals[0]["credit"] == 1000
    with pytest.raises(ValueError, match="placed-in-service"):
        post_depreciation(asset, "2026-08")

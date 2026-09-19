"""Eval must start from a clean isolated snapshot, not leftover demo state."""

from __future__ import annotations

from pathlib import Path

from close.eval_cases import CANONICAL_CASES, duplicate_register_asset, server_candidate
from close.eval_harness import run_isolated_eval, run_isolated_eval_repeats
from close.eval_live import run_close_eval
from fixed_assets.agent import deterministic_prepare
from prepaid.models import PrepaidItem


def _demo_paths() -> dict[str, Path]:
    from close.cash_overlay import OVERLAY_PATH
    from close.reviews import REVIEWS_PATH
    from fixed_assets.store import ASSETS_PATH
    from prepaid.store import ITEMS_PATH

    return {
        "assets": Path(ASSETS_PATH),
        "prepaids": Path(ITEMS_PATH),
        "overlays": Path(OVERLAY_PATH),
        "reviews": Path(REVIEWS_PATH),
    }


def _seed_dirty_demo() -> dict:
    from close.cash_overlay import add_ledger_entry, load_overlay
    from close.models import ReviewItem
    from close.reviews import load_reviews, upsert_review
    from fixed_assets.store import load_assets, upsert_asset
    from prepaid.store import load_items, upsert_item

    asset = duplicate_register_asset()
    prepaid = PrepaidItem(
        prepaid_id="PRE-DIRTY-001",
        vendor="Dirty Demo Insurance",
        description="Leftover demo prepaid",
        source_document_id="DOC-DIRTY",
        total_amount=999.0,
        start_date="2026-09-01",
        end_date="2026-09-30",
        initial_account="Prepaid Expenses",
        expense_account="Insurance Expense",
        evidence_refs=["DOC-DIRTY"],
        created_at="2026-09-01T00:00:00Z",
    )
    upsert_asset(asset)
    upsert_item(prepaid)
    add_ledger_entry(
        "2026-09",
        {
            "entry_id": "GL-DIRTY-OVERLAY",
            "date": "2026-09-30",
            "amount": 12.40,
            "amount_minor": 1240,
            "account": "1000-Cash",
            "description": "Resolved leftover overlay",
            "period": "2026-09",
        },
    )
    upsert_review(
        ReviewItem(
            review_id="REV-DIRTY-CASH",
            period="2026-09",
            source_workflow="cash",
            source_case_id="DIRTY-CASH",
            issue_type="unexplained_difference",
            description="Leftover resolved cash review",
            status="RESOLVED",
            decision="RESOLVE",
        )
    )
    return {
        "asset_ids": sorted(item.asset_id for item in load_assets()),
        "prepaid_ids": sorted(item.prepaid_id for item in load_items()),
        "overlay": load_overlay("2026-09"),
        "review_ids": sorted(item.review_id for item in load_reviews()),
        "paths": {key: path.read_text() for key, path in _demo_paths().items() if path.exists()},
    }


def test_canonical_prompts_do_not_include_answer_key():
    for case in CANONICAL_CASES:
        assert "expected:" not in case.prompt.lower()
        assert "answer key" not in case.prompt.lower()
        if case.case_id != "recon-explanation":
            assert case.expected not in case.prompt


def test_repeated_eval_setup_produces_identical_input_facts():
    first, second = run_isolated_eval_repeats(live=False, repeat=2)
    assert first.input_fingerprint == second.input_fingerprint
    assert first.by_id()["server-capital"].input_facts == second.by_id()["server-capital"].input_facts
    assert first.passed == first.total == 5
    assert second.passed == second.total == 5


def test_eval_starts_clean_and_ignores_demo_inv_021():
    dirty = _seed_dirty_demo()
    assert "INV-021" in dirty["asset_ids"]
    assert deterministic_prepare(server_candidate()).decision == "duplicate_review"

    report = run_isolated_eval(live=False)
    capital = report.by_id()["server-capital"]
    duplicate = report.by_id()["duplicate-asset"]
    prepaid = report.by_id()["prepaid-judgment"]

    assert capital.actual == "capitalize"
    assert capital.passed
    assert capital.input_facts["assets"] == []
    assert duplicate.actual == "duplicate_review"
    assert prepaid.actual == "straight_line_monthly"
    assert all(item["prepaid_id"] == "EVAL-INS" for item in prepaid.input_facts["prepaids"])
    assert report.passed == report.total


def test_eval_does_not_mutate_demo_workspace():
    dirty = _seed_dirty_demo()
    demo_before = dirty["paths"]
    report = run_isolated_eval(live=False)
    assert report.by_id()["server-capital"].actual == "capitalize"

    from close.cash_overlay import load_overlay
    from close.reviews import load_reviews
    from fixed_assets.store import load_assets
    from prepaid.store import load_items

    assert sorted(item.asset_id for item in load_assets()) == dirty["asset_ids"]
    assert sorted(item.prepaid_id for item in load_items()) == dirty["prepaid_ids"]
    assert load_overlay("2026-09") == dirty["overlay"]
    assert sorted(item.review_id for item in load_reviews()) == dirty["review_ids"]
    assert {key: path.read_text() for key, path in _demo_paths().items() if path.exists()} == demo_before
    assert not any(item.prepaid_id == "EVAL-INS" for item in load_items())
    assert deterministic_prepare(server_candidate()).decision == "duplicate_review"


def test_eval_live_repeat_text_uses_isolated_snapshot():
    first = run_close_eval(live=False, repeat=2)
    second = run_close_eval(live=False, repeat=2)
    assert "isolated: true" in first
    assert "Repeat setup: IDENTICAL" in first
    assert "CASE server-capital" in first
    assert "CASE duplicate-asset" in first
    assert first == second

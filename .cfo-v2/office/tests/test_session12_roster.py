"""Session 12: roster grain, rooms, routines, Handle destinations."""

from __future__ import annotations

import json
from pathlib import Path

from handles import GRAIN_SLUGS, SAMPLE_DATA_DISPLAY_NAMES, all_destination_slugs, destination

REPO = Path(__file__).resolve().parents[3]
ROSTER = REPO / ".cfo-v2" / "office" / "computer" / "harness" / "roster.json"
SLUG_MAP = REPO / ".cfo-v2" / "office" / "computer" / "cfo" / "slug-map.json"
GRANTS = REPO / ".cfo-v2" / "office" / "computer" / "cfo" / "grants.json"


def test_roster_has_exactly_sixteen_grain_slugs() -> None:
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    slugs = [bot["slug"] for bot in roster["bots"]]
    assert slugs == list(GRAIN_SLUGS)
    assert "world" in slugs
    assert "ingest" not in slugs
    assert "ar" not in slugs
    ids = [bot["id"] for bot in roster["bots"]]
    assert "bot_ctl_pay" in ids
    assert "bot_world" in ids
    assert all(bot["approvalLevel"] == "never" for bot in roster["bots"])
    names = {bot["name"] for bot in roster["bots"]}
    assert names.isdisjoint(SAMPLE_DATA_DISPLAY_NAMES)


def test_rooms_are_partitioned_2_to_6() -> None:
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    sizes = {room["id"]: len(room["members"]) for room in roster["rooms"]}
    assert sizes == {"intake": 5, "pay": 3, "cash": 4, "books-close": 4}
    for room in roster["rooms"]:
        assert 2 <= len(room["members"]) <= 6
        for slug in room["members"]:
            assert slug in GRAIN_SLUGS


def test_routines_fire_on_owning_bots() -> None:
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    slugs = {bot["slug"] for bot in roster["bots"]}
    expected = {
        "weekly-pay-run": ("pay", "room:pay"),
        "daily-aging": ("collect", "room:cash"),
        "month-end": ("close", "room:books-close"),
        "post-close-assurance": ("audit", "room:books-close"),
        "period-story": ("story", "room:books-close"),
    }
    by_name = {row["name"]: row for row in roster["routines"]}
    for name, (bot, conversation) in expected.items():
        row = by_name[name]
        assert row["bot"] == bot
        assert row["conversation"] == conversation
        assert row["bot"] in slugs
        assert "operator_dm" not in row["conversation"]
    assert len(roster["bots"]) == 16


def test_handle_destinations_are_grain_slugs() -> None:
    assert destination("email", "bill") == ("ap", "prepare")
    assert destination("email", "outbound") == ("world", "vendor")
    assert destination("collect", "dun") == ("world", "customer")
    assert destination("ap", "vendor-query") == ("world", "vendor")
    assert destination("world", "delivered") == ("email", "triage")
    assert destination("ap", "approve") == ("ctl-pay", "review-match")
    assert destination("pay", "release") == ("ctl-pay", "review-pay")
    assert destination("close", "lock") == ("ctl-books", "lock")
    assert all_destination_slugs().issubset(set(GRAIN_SLUGS))
    assert "ingest" not in all_destination_slugs()
    assert "world" in all_destination_slugs()


def test_slug_map_has_no_sample_data_bots() -> None:
    slug_map = json.loads(SLUG_MAP.read_text(encoding="utf-8"))
    assert set(slug_map["bots"]) == set(GRAIN_SLUGS)
    grants = json.loads(GRANTS.read_text(encoding="utf-8"))
    for bot in slug_map["bots"].values():
        for display in bot["profiles"].values():
            if display:
                assert display not in SAMPLE_DATA_DISPLAY_NAMES or display not in slug_map["bots"]
    for name in SAMPLE_DATA_DISPLAY_NAMES:
        assert name not in slug_map["bots"]
        assert grants["byDisplayName"][name]["ops"] == []

"""Current 15-bot grain. Display names are Profiles, not extra Bots."""

from __future__ import annotations

import json
from pathlib import Path

from skills.assignments import AGENT_SKILLS

REPO = Path(__file__).resolve().parent.parent
GIT_ROOT = REPO.parent
ROSTER_PATH = GIT_ROOT / ".cfo-v2" / "office" / "computer" / "harness" / "roster.json"
SLUG_MAP_PATH = GIT_ROOT / ".cfo-v2" / "office" / "computer" / "cfo" / "slug-map.json"

GRAIN_SLUGS = (
    "email",
    "stripe",
    "bank",
    "books",
    "ap",
    "pay",
    "apply",
    "collect",
    "cash",
    "close",
    "story",
    "ctl-pay",
    "ctl-cash",
    "ctl-books",
    "audit",
)

ROOM_MEMBERS = {
    "intake": ["email", "stripe", "bank", "books"],
    "pay": ["ap", "pay", "ctl-pay"],
    "cash": ["apply", "collect", "cash", "ctl-cash"],
    "books-close": ["close", "ctl-books", "story", "audit"],
}

FALLBACK_PURPOSES = {
    "email": "Owns messages and attachments: vendor invoices and customer remittances.",
    "stripe": "Owns processor payouts, fees, refunds, and chargebacks.",
    "bank": "Owns bank lines and corporate-card charges.",
    "books": "Owns GL, subledgers, vendor and customer master, POs, and period-lock state (read).",
    "ap": "Owns open bills: three-way match, hold, and exception investigation.",
    "pay": "Owns the weekly pay-run plan. Does not match bills or concur.",
    "apply": "Owns incoming cash application to customer invoices.",
    "collect": "Owns AR aging chase decisions.",
    "cash": "Owns bank-to-ledger reconciliation proposals.",
    "close": "Owns month-end coordination, accruals, prepaids, assets, and BS packets.",
    "story": "Owns variance, forecast, forecast-miss, and board narrative.",
    "ctl-pay": "Verifier for AP match concurrence and payment-plan concurrence.",
    "ctl-cash": "Verifier for cash application and bank-reconciliation concurrence.",
    "ctl-books": "Verifier for treatment, assets, BS recs, and period lock.",
    "audit": "Independent post-close assurance. Does not operate the books.",
}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text())


def load_roster() -> list[dict]:
    payload = _load_json(ROSTER_PATH)
    bots = payload.get("bots") or []
    if bots:
        return bots
    return [
        {
            "id": f"bot_{slug.replace('-', '_')}",
            "name": slug,
            "slug": slug,
            "purpose": FALLBACK_PURPOSES[slug],
            "skills": [],
            "approvalLevel": "never",
        }
        for slug in GRAIN_SLUGS
    ]


def load_slug_map() -> dict:
    payload = _load_json(SLUG_MAP_PATH)
    return payload.get("bots") or {}


def display_name_to_bot() -> dict[str, dict]:
    mapping: dict[str, dict] = {}
    slug_map = load_slug_map()
    for slug, spec in slug_map.items():
        for profile, display in (spec.get("profiles") or {}).items():
            if not display:
                continue
            mapping[display] = {"slug": slug, "profile": profile, "bot_id": f"bot_{slug.replace('-', '_')}"}
    return mapping


def grain_agents() -> list[dict]:
    roster = {item.get("slug"): item for item in load_roster()}
    slug_map = load_slug_map()
    rows = []
    for slug in GRAIN_SLUGS:
        spec = slug_map.get(slug) or {}
        profiles = []
        skills: list[str] = []
        for profile, display in (spec.get("profiles") or {}).items():
            assigned = list(AGENT_SKILLS.get(display, ())) if display else []
            skills.extend(assigned)
            profiles.append(
                {
                    "profile": profile,
                    "display_name": display or None,
                    "default": profile == spec.get("defaultProfile"),
                    "skills": assigned,
                }
            )
        bot = roster.get(slug) or {}
        rows.append(
            {
                "slug": slug,
                "id": bot.get("id") or f"bot_{slug.replace('-', '_')}",
                "name": bot.get("name") or slug,
                "purpose": bot.get("purpose") or FALLBACK_PURPOSES.get(slug, ""),
                "approval_level": bot.get("approvalLevel") or "never",
                "default_profile": spec.get("defaultProfile"),
                "profiles": profiles,
                "skills": sorted(set(skills) | set(bot.get("skills") or [])),
                "connectors": bot.get("connectors") or [],
                "room": next((room for room, members in ROOM_MEMBERS.items() if slug in members), None),
            }
        )
    return rows


def architecture_payload() -> dict:
    return {
        "system": "cfo-agentic-system",
        "grain": 15,
        "kernel": ".cfo/",
        "office": ".cfo-v2/office",
        "computer": ".cfo-v2/office/computer",
        "bots": grain_agents(),
        "rooms": [{"id": room, "members": members} for room, members in ROOM_MEMBERS.items()],
        "routines": [
            {"id": "weekly-pay-run", "bot": "pay", "cadence": "weekly", "conversation": "room:pay"},
            {"id": "daily-aging", "bot": "collect", "cadence": "daily", "conversation": "room:cash"},
            {"id": "month-end", "bot": "close", "cadence": "monthly", "conversation": "room:books-close"},
            {"id": "post-close-assurance", "bot": "audit", "cadence": "monthly", "conversation": "room:books-close"},
        ],
        "data_sources": [
            "inbox / email / portal / employee / document",
            "ERP / Coupa / EDI",
            "Stripe payouts (simulated by default)",
            "bank feed",
            "canonical Maximor demo pack",
        ],
        "canonical_state": ".cfo/data/demo and runs/demo_runtime",
        "decision_memory": [
            "prior_cases.json",
            "ar_precedents.json",
            "memory.store decisions.json",
            "close identity_links",
        ],
        "note": "Display names from the pre-migration kernel are Profiles on these 15 Bots. They are not standing Bots.",
    }

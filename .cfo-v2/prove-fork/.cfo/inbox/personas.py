"""Read-only outside-world personas: fixtures plus demo vendor/customer masters."""

from __future__ import annotations

import json
from pathlib import Path

from inbox.fixtures import full_inbox_specs, spec_incomplete_reply
from tools import DATA_DIR

SIMULATED_BANKS: tuple[dict[str, str], ...] = (
    {
        "role": "bank",
        "name": "First National Operating",
        "address": "notices@firstnational.example",
        "delay_habit": "",
        "source": "world-fixture",
    },
)

EMPLOYEE_SENDERS = {
    "receiving@hackmit-cfo.example": "employee",
    "fun@hackmit-cfo.example": "employee",
}


def _read_json_list(path: Path) -> list:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, list) else []


def _vendor_master_path() -> Path:
    direct = DATA_DIR / "canonical" / "vendors.json"
    if direct.exists():
        return direct
    return DATA_DIR / "demo" / "canonical" / "vendors.json"


def _address_for_vendor(name: str) -> str:
    slug = "".join(ch.lower() for ch in name if ch.isalnum()) or "vendor"
    return f"billing@{slug}.example"


def _role_for_fixture(sender_address: str, case_id: str) -> str:
    if sender_address in EMPLOYEE_SENDERS:
        return "employee"
    if case_id in {"remittance"}:
        return "customer"
    return "vendor"


def list_personas() -> list[dict]:
    """Vendors, customers, banks, and employees the simulated world can speak as."""
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add(
        *,
        role: str,
        name: str,
        address: str,
        delay_habit: str = "",
        source: str,
        persona_id: str = "",
    ) -> None:
        key = (role, address.lower())
        if not address or key in seen:
            return
        seen.add(key)
        rows.append(
            {
                "role": role,
                "name": name,
                "address": address,
                "delay_habit": delay_habit,
                "source": source,
                "persona_id": persona_id,
            }
        )

    specs = list(full_inbox_specs()) + [spec_incomplete_reply()]
    for spec in specs:
        add(
            role=_role_for_fixture(spec.sender_address, spec.case_id),
            name=spec.sender_name,
            address=spec.sender_address,
            source="inbox-fixture",
        )

    for item in _read_json_list(_vendor_master_path()):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        vendor_id = str(item.get("vendor_id") or "")
        if not name:
            continue
        add(
            role="vendor",
            name=name,
            address=_address_for_vendor(name),
            source="vendor-master",
            persona_id=vendor_id,
        )

    for item in _read_json_list(DATA_DIR / "ar_customers.json"):
        if not isinstance(item, dict):
            continue
        name = str(item.get("customer_name") or "")
        customer_id = str(item.get("customer_id") or "")
        if not name:
            continue
        behavior = str(item.get("payment_behavior") or "")
        late = item.get("average_days_late")
        delay = behavior
        if late not in (None, "", 0, "0"):
            delay = f"{behavior}; typical delay {late} days".strip("; ")
        slug = "".join(ch.lower() for ch in name if ch.isalnum()) or "customer"
        add(
            role="customer",
            name=name,
            address=f"ap@{slug}.example",
            delay_habit=delay,
            source="customer-master",
            persona_id=customer_id,
        )

    for bank in SIMULATED_BANKS:
        add(
            role=bank["role"],
            name=bank["name"],
            address=bank["address"],
            delay_habit=bank.get("delay_habit", ""),
            source=bank.get("source", "world-fixture"),
        )

    rows.sort(key=lambda row: (row["role"], row["name"].lower(), row["address"]))
    return rows

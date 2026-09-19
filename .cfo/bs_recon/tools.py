from __future__ import annotations

from agents import function_tool

from bs_recon.packets import build_packets
from bs_recon.store import load_reconciliations

_PACKETS: dict[str, dict] = {}


def bind_packets(period: str, packets) -> None:
    _PACKETS[period] = {item.account_id: item for item in packets}


@function_tool
def get_reconciliation_packet(period: str, account_id: str) -> dict:
    """Python reconciliation packet for one account. Do not recalculate."""
    packet = (_PACKETS.get(period) or {}).get(account_id)
    if packet is None:
        for item in build_packets(period):
            bind_packets(period, [item])
        packet = (_PACKETS.get(period) or {}).get(account_id)
    if packet is None:
        return {"found": False, "account_id": account_id}
    return {"found": True, **packet.model_dump(mode="json")}


@function_tool
def list_reconciling_items(period: str, account_id: str) -> dict:
    """Reconciling items Python already attached to the packet."""
    packet = (_PACKETS.get(period) or {}).get(account_id)
    if packet is None:
        return {"found": False, "account_id": account_id}
    return {
        "found": True,
        "account_id": account_id,
        "items": [item.model_dump(mode="json") for item in packet.reconciling_items],
    }


@function_tool
def list_period_reconciliations(period: str) -> dict:
    """Saved reconciliations for the period."""
    rows = load_reconciliations(period)
    return {"found": True, "count": len(rows), "rows": [item.model_dump(mode="json") for item in rows]}

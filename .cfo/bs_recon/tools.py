from __future__ import annotations

from pathlib import Path

from agents import function_tool

from atomic_json import read_json_object, with_file_lock, write_json_atomic
from bs_recon.models import ReconPacket
from bs_recon.packets import build_packets
from bs_recon.store import load_reconciliations

_PACKETS: dict[str, dict] = {}
_PACKET_DIR: Path | None = None


def configure_packet_store(directory: Path | None) -> Path | None:
    """Persist bind_packets so a second process can read the same period map."""
    global _PACKET_DIR
    _PACKET_DIR = Path(directory) if directory is not None else None
    if _PACKET_DIR is not None:
        _PACKET_DIR.mkdir(parents=True, exist_ok=True)
        _load_all_periods()
    return _PACKET_DIR


def bind_packets(period: str, packets) -> None:
    current = dict(_PACKETS.get(period) or {})
    for item in packets:
        current[item.account_id] = item
    _PACKETS[period] = current
    _persist_period(period)


def _period_path(period: str) -> Path:
    assert _PACKET_DIR is not None
    safe = period.replace("/", "-")
    return _PACKET_DIR / f"{safe}.json"


def _persist_period(period: str) -> None:
    if _PACKET_DIR is None:
        return
    rows = [item.model_dump(mode="json") for item in (_PACKETS.get(period) or {}).values()]

    def _write() -> None:
        write_json_atomic(_period_path(period), {"period": period, "packets": rows})

    with_file_lock(_PACKET_DIR / "packets.lock", _write)


def _load_all_periods() -> None:
    if _PACKET_DIR is None:
        return
    for path in sorted(_PACKET_DIR.glob("*.json")):
        if path.name.startswith("_"):
            continue
        payload = read_json_object(path)
        period = str(payload.get("period") or path.stem)
        packets = [ReconPacket.model_validate(item) for item in payload.get("packets") or []]
        _PACKETS[period] = {item.account_id: item for item in packets}


@function_tool
def get_reconciliation_packet(period: str, account_id: str) -> dict:
    """Python reconciliation packet for one account. Do not recalculate."""
    packet = (_PACKETS.get(period) or {}).get(account_id)
    if packet is None:
        bind_packets(period, list(build_packets(period)))
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

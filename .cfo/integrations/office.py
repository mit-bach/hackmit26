"""Harness Handles after Kernel Stripe unpack. Deposit to cash. Charges to apply."""

from __future__ import annotations

from pathlib import Path

from atomic_json import write_json_atomic
from harness_handles import relative_to_computer, write_peer_handle
from integrations.cash import reconcile_payout
from integrations.store import get_payout, get_reconciliation


def land_payout_handles(
    payout_id: str,
    *,
    computer_root: Path,
) -> dict:
    payout = get_payout(payout_id)
    if payout is None:
        raise ValueError(f"unknown payout {payout_id}")
    breakdown = get_reconciliation(payout_id) or reconcile_payout(payout)
    dest_dir = computer_root / "workspace" / "sources" / "stripe"
    dest_dir.mkdir(parents=True, exist_ok=True)
    packet_path = dest_dir / f"{payout_id}.json"
    charge_ids = [
        line.source_object_id or line.provider_object_id
        for line in payout.lines
        if (line.category or line.line_type or "") in {"gross", "charge", "payment", "captured"}
        or (line.line_type or "").lower() in {"charge", "payment"}
    ]
    charge_ids = [item for item in charge_ids if item]
    payload = {
        "object": "processor_payout",
        "payout_id": payout.payout_id,
        "provider": payout.provider,
        "invoice_candidates": 0,
        "waterfall_status": breakdown.status,
        "bank_deposit_id": breakdown.bank_deposit_id or payout.bank_deposit_id,
        "charge_ids": charge_ids,
        "expected_payout_minor": breakdown.expected_payout_minor,
        "actual_payout_minor": breakdown.actual_payout_minor,
        "never_ap_invoice": True,
    }
    write_json_atomic(packet_path, payload)
    rel = relative_to_computer(computer_root, packet_path)
    deposit, _ = write_peer_handle(
        computer_root,
        from_slug="stripe",
        to_slug="cash",
        profile="match",
        paths=[rel],
        prompt=(
            f"profile: match\n"
            f"Processor deposit for {payout_id} at {rel}. "
            "Waterfall already unpacked in Kernel. invoice_candidates is 0. "
            "Tick the bank deposit. Do not mint an AP invoice."
        ),
        extra={"payoutId": payout_id, "invoice_candidates": 0},
    )
    charges, _ = write_peer_handle(
        computer_root,
        from_slug="stripe",
        to_slug="apply",
        profile="apply",
        paths=[rel],
        prompt=(
            f"profile: apply\n"
            f"Charge-level facts for {payout_id} at {rel}. "
            "Do not apply cash in Bot stripe. invoice_candidates is 0."
        ),
        extra={"payoutId": payout_id, "invoice_candidates": 0},
    )
    break_handle = None
    if breakdown.status != "MATCH":
        dest, _ = write_peer_handle(
            computer_root,
            from_slug="stripe",
            to_slug="ctl-cash",
            profile="review-rec",
            paths=[rel],
            prompt=(
                f"profile: review-rec\n"
                f"Waterfall break for {payout_id} status {breakdown.status}. "
                "Do not invent a fee. Do not force MATCHED."
            ),
            extra={"payoutId": payout_id, "kernelStatus": breakdown.status},
        )
        break_handle = str(dest)
    return {
        "packet_path": str(packet_path),
        "invoice_candidates": 0,
        "deposit_handle": str(deposit),
        "charges_handle": str(charges),
        "waterfall_break_handle": break_handle,
        "status": breakdown.status,
    }

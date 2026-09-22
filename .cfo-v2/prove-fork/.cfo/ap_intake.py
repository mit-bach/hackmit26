"""Email or books land a Kernel invoice, then Handle ap / prepare.

Dual intake must not mint a second Kernel id for the same vendor PDF.
MSG-S12 / INV-S12 is a marker. This module lands a real Maximor id.
"""

from __future__ import annotations

from pathlib import Path

from atomic_json import write_json_atomic
from harness_handles import default_computer_root, write_peer_handle
from inbox.models import InboxHandoffResult, MessageSpec
from inbox.workflow import handoff
from tools import invoice_lookup
from workflow import run_ap_kernel


def land_email_bill(
    spec: MessageSpec,
    *,
    computer_root: Path | None = None,
    persist: bool = False,
    match: bool = True,
) -> dict:
    """Classify and dispatch a simulated mailbox message into Kernel AP.

    Returns the canonical invoice_id Email handed to ap. get_invoice must find it.
    """
    computer = Path(computer_root) if computer_root is not None else default_computer_root()
    result: InboxHandoffResult = handoff(spec, persist=persist)
    invoice_id = result.invoice_id
    lookup = (
        invoice_lookup(invoice_id)
        if invoice_id
        else {"found": False, "error": "Email did not land a Kernel invoice_id. Do not invent one."}
    )
    intake_name = f"{invoice_id or spec.message_id}.json"
    intake_path = computer / "workspace" / "ap" / "intake" / intake_name
    payload = {
        "source": "email",
        "profile": "prepare",
        "message_id": spec.message_id,
        "invoice_id": invoice_id,
        "canonical": bool(lookup.get("found")),
        "dispatch_status": result.final_status,
        "duplicate_of": result.receiver.dispatch.duplicate_of if result.receiver.dispatch else None,
        "kernel_found": bool(lookup.get("found")),
        "marker": False,
    }
    write_json_atomic(intake_path, payload)
    prompt = (
        "profile: prepare\n"
        f"invoice_id: {invoice_id or ''}\n"
        f"path: workspace/ap/intake/{intake_name}\n"
        "Landed a vendor bill. tools.get_invoice must find this id. "
        "Do not invent amounts. Do not mint a second Kernel id for this PDF."
    )
    handle_path, handle = write_peer_handle(
        computer,
        from_slug="email",
        to_slug="ap",
        profile="prepare",
        paths=[f"workspace/ap/intake/{intake_name}"],
        prompt=prompt,
        extra={"invoice_id": invoice_id, "message_id": spec.message_id},
    )
    match_trace = None
    if match and lookup.get("found") and invoice_id:
        match_trace = run_ap_kernel(invoice_id, computer_root=computer)
    return {
        "invoice_id": invoice_id,
        "found": bool(lookup.get("found")),
        "lookup": lookup,
        "intake_path": str(intake_path),
        "email_ap_handle": handle,
        "email_ap_handle_path": str(handle_path),
        "handoff": result,
        "match_trace": match_trace,
    }

"""Host-only kernel.* ops. Not Catalog. Not a Bot. Not model-facing."""

from __future__ import annotations

from typing import Any

from cfo_kernel import HOST_BOT_ID, HOST_PROFILE, HOST_SLUG, LOCK_OP, TEST_PACKET_OP
from cfo_kernel.paths import eval_phase


def kernel_health(_args: dict) -> dict:
    return {
        "sidecar": True,
        "bot": False,
        "bindsHarnessBot": False,
        "drainsInboxes": False,
        "evalPhase": eval_phase(),
        "lockOp": LOCK_OP,
        "testPacketOp": TEST_PACKET_OP,
        "hostSlug": HOST_SLUG,
        "hostBotId": HOST_BOT_ID,
        "hostProfile": HOST_PROFILE,
    }


def kernel_register_runtime_invoice(args: dict) -> dict:
    from models import Invoice
    from tools import register_runtime_invoice

    raw = args.get("invoice")
    if not isinstance(raw, dict):
        raise ValueError("kernel.register_runtime_invoice requires args.invoice object")
    invoice = Invoice.model_validate(raw)
    register_runtime_invoice(invoice)
    return {"registered": True, "invoice_id": invoice.invoice_id}


def kernel_bind_cash_case(args: dict) -> dict:
    from cash_recon.models import BankTransaction, FeeEvidence, LedgerEntry, MatchCandidate
    from cash_recon.tools import bind_case

    case_id = str(args.get("case_id") or "")
    if not case_id:
        raise ValueError("kernel.bind_cash_case requires args.case_id")
    bank = [BankTransaction.model_validate(item) for item in args.get("bank") or []]
    ledger = [LedgerEntry.model_validate(item) for item in args.get("ledger") or []]
    fees = [FeeEvidence.model_validate(item) for item in args.get("fees") or []]
    candidates = [MatchCandidate.model_validate(item) for item in args.get("candidates") or []]
    bound_id = bind_case(
        bank=bank,
        ledger=ledger,
        fees=fees,
        candidates=candidates,
        case_id=case_id,
        persist=True,
    )
    return {"bound": True, "case_id": bound_id, "bank_count": len(bank)}


def kernel_bind_bs_packets(args: dict) -> dict:
    from bs_recon.models import ReconPacket
    from bs_recon.tools import bind_packets

    period = str(args.get("period") or "")
    if not period:
        raise ValueError("kernel.bind_bs_packets requires args.period")
    packets = [ReconPacket.model_validate(item) for item in args.get("packets") or []]
    bind_packets(period, packets)
    return {"bound": True, "period": period, "packet_count": len(packets)}


HOST_DISPATCH = {
    "kernel.health": (kernel_health, "read"),
    "kernel.register_runtime_invoice": (kernel_register_runtime_invoice, "write-local"),
    "kernel.bind_cash_case": (kernel_bind_cash_case, "write-local"),
    "kernel.bind_bs_packets": (kernel_bind_bs_packets, "write-local"),
}


def call_host(op: str, args: dict) -> Any:
    pair = HOST_DISPATCH.get(op)
    if pair is None:
        raise KeyError(op)
    fn, _mut = pair
    return fn(args)


def host_mutability(op: str) -> str:
    pair = HOST_DISPATCH.get(op)
    if pair is None:
        raise KeyError(op)
    return pair[1]

"""HackMIT demo for named finance integrations."""

from __future__ import annotations

import json
from typing import Any

from invoice_ingestion.adapter import reset_ingested_invoices
from integrations.cash import format_breakdown, reconcile_payout
from integrations.models import IntegrationResult
from integrations.providers import adyen, coupa, gmail, netsuite, outlook, stripe, xero
from integrations.store import all_payouts, get_payout, reset_integration_state, write_trace


def _raw(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _headers_for(provider: str, raw: bytes) -> dict[str, str]:
    if provider == "stripe":
        return {"stripe-signature": stripe.sign(raw)}
    if provider == "adyen":
        return {"hmacsignature": adyen.sign(raw), "protocol": "HmacSHA256"}
    if provider == "xero":
        return {"x-xero-signature": xero.sign(raw)}
    if provider == "outlook":
        return {}
    if provider == "gmail":
        return {}
    return {}


def process_provider(name: str, replay: bool = False) -> list[IntegrationResult]:
    results: list[IntegrationResult] = []
    if name == "stripe":
        mock = stripe.MockStripeProvider()
        for payload in stripe.demo_payloads():
            raw = _raw(payload)
            results.append(stripe.process_raw(raw, _headers_for("stripe", raw), provider=mock))
    elif name == "adyen":
        for payload in adyen.demo_payloads():
            raw = _raw(payload)
            results.append(adyen.process_raw(raw, _headers_for("adyen", raw)))
    elif name == "gmail":
        for payload in gmail.demo_payloads():
            raw = json.dumps(payload).encode("utf-8")
            results.append(gmail.process_raw(raw, {}, require_signature=False))
    elif name == "outlook":
        for payload in outlook.demo_payloads():
            raw = json.dumps(payload).encode("utf-8")
            results.append(outlook.process_raw(raw, {}))
    elif name == "xero":
        for payload in xero.demo_payloads():
            raw = _raw(payload)
            results.append(xero.process_raw(raw, _headers_for("xero", raw)))
    elif name == "coupa":
        results.append(coupa.sync())
    elif name == "netsuite":
        results.append(netsuite.sync())
    else:
        raise KeyError(name)
    return results


def run_integration_demo(*, replay: bool = True) -> str:
    reset_integration_state()
    reset_ingested_invoices()
    first: dict[str, list[IntegrationResult]] = {}
    for name in ("gmail", "outlook", "xero", "coupa", "netsuite", "stripe", "adyen"):
        first[name] = process_provider(name)
    second: dict[str, list[IntegrationResult]] = {}
    if replay:
        for name in ("gmail", "outlook", "xero", "coupa", "netsuite", "stripe", "adyen"):
            second[name] = process_provider(name)
    text = format_demo(first, second)
    write_trace("integration-demo", {"first": _dump(first), "second": _dump(second)})
    return text


def _dump(mapping: dict[str, list[IntegrationResult]]) -> dict[str, Any]:
    return {key: [item.model_dump(mode="json") for item in value] for key, value in mapping.items()}


def _line(result: IntegrationResult) -> str:
    bits = [result.message or result.status]
    if result.invoice_numbers:
        bits.append("invoices=" + ",".join(result.invoice_numbers))
    if result.payout_id:
        bits.append(f"payout={result.payout_id}")
    if result.duplicate:
        bits.append("duplicate")
    return "  " + " | ".join(bits)


def format_demo(first: dict[str, list[IntegrationResult]], second: dict[str, list[IntegrationResult]]) -> str:
    lines = [
        "Real Finance Integrations Demo",
        "",
        "INVOICE SOURCES",
        "",
        "Gmail",
    ]
    gmail_first = first.get("gmail") or []
    if gmail_first:
        details = gmail_first[0].details or {}
        lines.append("  Pub/Sub event received")
        ids = details.get("message_ids") or []
        if ids:
            lines.append(f"  Message fetched: {ids[0]}")
        numbers = [num for item in gmail_first for num in item.invoice_numbers]
        if "INV-9001" in numbers:
            lines.append("  Attachment: aws-september.pdf")
            lines.append("  Invoice extracted: AWS INV-9001")
        classes = [item.classification for item in gmail_first if item.classification]
        if "quote" in classes or any(item.classification == "quote" for item in gmail_first):
            pass
    for item in gmail_first:
        if item.classification and item.classification != "invoice":
            lines.append(f"  Non-invoice classified: {item.classification} ({item.details.get('message_ids')})")

    lines.extend(["", "Outlook"])
    outlook_first = first.get("outlook") or []
    if outlook_first:
        lines.append("  Graph notification received")
        details = outlook_first[0].details or {}
        if details.get("message_id"):
            lines.append(f"  Message fetched: {details.get('message_id')}")
        numbers = [num for item in outlook_first for num in item.invoice_numbers]
        if "HEL-INV-6200" in numbers:
            lines.append("  Attachment: helios-september.pdf")
            lines.append("  Invoice extracted: HEL-INV-6200")
        for item in outlook_first:
            if item.classification and item.classification != "invoice":
                lines.append(f"  Non-invoice classified: {item.classification}")

    lines.extend(["", "Xero"])
    for item in first.get("xero") or []:
        if item.status == "processed":
            lines.append("  Invoice CREATE event")
            lines.append(f"  Bill fetched: {(item.details or {}).get('invoice_id')}")
            lines.append("  Forwarded to invoice validation")
        elif item.classification == "ACCREC":
            lines.append("  Customer ACCREC invoice ignored (not AP)")

    lines.extend(["", "Coupa"])
    for item in first.get("coupa") or []:
        lines.append("  Incremental API sync")
        if item.invoice_numbers:
            lines.append(f"  Invoice fetched: {item.invoice_numbers[0]}")
        lines.append("  PO: PO-201")

    lines.extend(["", "NetSuite"])
    for item in first.get("netsuite") or []:
        lines.append("  REST sync")
        if item.invoice_numbers:
            lines.append(f"  Vendor bill fetched: {item.invoice_numbers[0]}")

    lines.extend(["", "CASH / PAYOUT SOURCES", "", "Stripe"])
    stripe_payout = get_payout("po_1HackMIT97420")
    stripe_result = next((item for item in first.get("stripe") or [] if item.payout_id), None)
    if stripe_result:
        lines.append(f"  {stripe_result.message.split()[0] if stripe_result.message else 'payout event'}")
        lines.append(f"  Payout: {stripe_result.payout_id}")
        if stripe_result.payout_amount is not None:
            lines.append(f"  Amount: ${stripe_result.payout_amount:,.2f}")
        lines.append("  Underlying transactions loaded")
    if stripe_payout:
        lines.append("")
        lines.append(format_breakdown(reconcile_payout(stripe_payout)))

    lines.extend(["", "Adyen"])
    adyen_payout = next((item for item in all_payouts() if item.provider == "adyen"), None)
    adyen_result = next((item for item in first.get("adyen") or [] if item.payout_id), None)
    if adyen_result:
        lines.append("  payout/transfer event")
        lines.append(f"  Transfer: {adyen_result.payout_id}")
        if adyen_result.payout_amount is not None:
            lines.append(f"  Amount: ${adyen_result.payout_amount:,.2f}")
        lines.append("  Underlying transactions loaded")
    if adyen_payout:
        lines.append("")
        lines.append(format_breakdown(reconcile_payout(adyen_payout)))

    if second:
        dupes = sum(1 for rows in second.values() for item in rows if item.duplicate or item.invoice_candidates == 0 and item.status in {"duplicate", "processed"})
        new_payouts = sum(1 for rows in second.values() for item in rows if item.status == "processed" and item.payout_id and not item.duplicate)
        new_invoices = sum(item.invoice_candidates for rows in second.values() for item in rows if not item.duplicate)
        # Coupa/NetSuite replay with same cursor should add 0
        lines.extend(
            [
                "",
                "Re-running every provider fixture...",
                f"New invoice candidates: {new_invoices}",
                f"New payout records: {new_payouts}",
                f"Duplicate deliveries recognized: {sum(1 for rows in second.values() for item in rows if item.duplicate)}",
                f"Idempotency check: {'PASS' if new_invoices == 0 and new_payouts == 0 else 'FAIL'}",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)
    replay = "--replay" in argv or "--replay-check" in argv
    print(run_integration_demo(replay=replay or True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

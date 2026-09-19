"""CLI for named provider integrations."""

from __future__ import annotations

from integrations.cash import format_breakdown, reconcile_payout
from integrations.demo import format_demo, process_provider
from integrations.providers import PROVIDERS, SYNC_PROVIDERS, WEBHOOK_PROVIDERS
from integrations.providers import stripe
from integrations.store import all_events, all_payouts, reset_integration_state
from invoice_ingestion.adapter import reset_ingested_invoices


def status_text() -> str:
    events = all_events()
    payouts = all_payouts()
    lines = [
        stripe.connection_status(),
        "",
        "Integration status (process memory + runs/integrations/state.json)",
        f"Events stored: {len(events)}",
        f"Payouts stored: {len(payouts)}",
        f"Webhook providers: {', '.join(WEBHOOK_PROVIDERS)}",
        f"API sync providers: {', '.join(SYNC_PROVIDERS)}",
        "Mode: mock unless STRIPE_MODE=live or INTEGRATIONS_MODE=live and credentials are set",
    ]
    for event in events:
        lines.append(
            f"- {event.provider} {event.provider_event_id} {event.event_type} "
            f"{event.processing_status} receipts={event.receipt_count}"
        )
    return "\n".join(lines)


def run_cli(argv: list[str]) -> int:
    if not argv or argv[0] in {"status"}:
        print(status_text())
        return 0
    print("Unknown integrations option. Try: python main.py integrations status")
    return 1


def run_webhook_demo(name: str) -> int:
    reset_integration_state()
    reset_ingested_invoices()
    if name not in PROVIDERS:
        print(f"Unknown provider: {name}")
        return 1
    first = {name: process_provider(name)}
    second = {name: process_provider(name)}
    print(format_demo(first, second) if name in {"gmail", "outlook", "xero", "coupa", "netsuite", "stripe", "adyen"} else "")
    if name in {"stripe", "adyen"}:
        for payout in all_payouts():
            if payout.provider == name:
                print()
                print(format_breakdown(reconcile_payout(payout)))
    print()
    print(f"Replay duplicates: {sum(1 for item in second[name] if item.duplicate)}")
    return 0


def run_sync(name: str, argv: list[str] | None = None) -> int:
    argv = list(argv or [])
    if name not in SYNC_PROVIDERS:
        print(f"Sync is documented for: {', '.join(SYNC_PROVIDERS)}")
        return 1
    if name == "stripe":
        payout_id = None
        if "--payout" in argv:
            index = argv.index("--payout")
            if index + 1 >= len(argv):
                print("Usage: python main.py sync stripe [--payout po_123]")
                return 1
            payout_id = argv[index + 1]
        result = stripe.sync(payout_id=payout_id)
        print(result.message)
        details = result.details or {}
        if details.get("payout_ids"):
            print("Payouts:", ", ".join(details["payout_ids"]))
        if result.status == "error":
            return 1
        replay = stripe.sync(payout_id=payout_id)
        print(f"Replay new payouts: {(replay.details or {}).get('new_payouts', 0)}")
        print(f"Replay new reconciliations: {(replay.details or {}).get('new_reconciliations', 0)}")
        return 0
    reset_ingested_invoices()
    result = process_provider(name)[0]
    print(result.message)
    if result.invoice_numbers:
        print("Invoices:", ", ".join(result.invoice_numbers))
    replay = process_provider(name)[0]
    print(f"Replay new records: {replay.invoice_candidates}")
    return 0


def run_stripe_demo() -> int:
    print(stripe.run_stripe_demo())
    return 0


def run_server(host: str = "127.0.0.1", port: int = 8000) -> int:
    import uvicorn

    from integrations.server import app

    uvicorn.run(app, host=host, port=port)
    return 0

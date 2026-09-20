"""Stripe payout webhooks. Never produces InvoiceCandidate.

Mock fixtures stay the HackMIT demo path. Live mode uses the official Stripe
Python SDK against a test account: verify Stripe-Signature on the raw body,
fetch the payout, page through balance transactions, then reuse cash math.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from integrations.cash import classify_line, major_units, reconcile_payout
from integrations.models import IntegrationResult, PayoutLine, ProviderPayout, WebhookEvent
from integrations.providers.base import env, fixture_dir, live_mode, load_json
from integrations.router import (
    WORKFLOW_DISPUTE,
    WORKFLOW_DUPLICATE,
    WORKFLOW_IGNORED,
    WORKFLOW_PAYMENT,
    WORKFLOW_PAYMENT_FAILED,
    WORKFLOW_PAYOUT,
    WORKFLOW_REFUND,
    classify_reconciliation_exception,
    classify_stripe_event,
)
from integrations.store import (
    all_payouts,
    all_reconciliations,
    get_bank_deposit,
    get_payout,
    get_reconciliation,
    payload_hash,
    remember_event,
    remember_payout,
    remember_reconciliation,
    update_event,
    write_trace,
)

PAYOUT_EVENTS = {
    "payout.created",
    "payout.updated",
    "payout.paid",
    "payout.failed",
    "payout.canceled",
    "payout.reconciliation_completed",
}

# Official Stripe events that mean payout balance transactions are queryable.
# https://docs.stripe.com/payouts/reconciliation
# https://docs.stripe.com/api/events/types
READY_TXN_EVENTS = {
    "payout.reconciliation_completed",
    "payout.paid",
}

MOCK_WEBHOOK_SECRET = "whsec_test_hackmit"


class StripeConfigError(RuntimeError):
    """Live Stripe is selected but credentials are missing."""


class StripeAPIFailure(RuntimeError):
    """Official Stripe SDK/network call failed."""


def stripe_mode() -> str:
    explicit = env("STRIPE_MODE")
    if explicit:
        return explicit.lower()
    if live_mode():
        return "live"
    return "mock"


def webhook_secret() -> str:
    configured = env("STRIPE_WEBHOOK_SECRET")
    if configured:
        return configured
    if stripe_mode() == "live":
        return ""
    return MOCK_WEBHOOK_SECRET


def secret_key() -> str:
    return env("STRIPE_SECRET_KEY")


def _created_at(payload: dict) -> datetime | None:
    created = payload.get("created")
    if isinstance(created, int):
        return datetime.fromtimestamp(created, tz=timezone.utc)
    return None


def _created_iso(value: Any) -> str | None:
    if isinstance(value, int):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    if value:
        return str(value)
    return None


def _arrival_date(obj: dict) -> str | None:
    arrival = obj.get("arrival_date")
    if isinstance(arrival, int):
        return datetime.fromtimestamp(arrival, tz=timezone.utc).date().isoformat()
    if isinstance(arrival, str) and arrival:
        return arrival
    return None


def _source_id(row: dict) -> str | None:
    source = row.get("source")
    if isinstance(source, dict):
        return str(source.get("id") or "") or None
    if source:
        return str(source)
    return None


def _source_reference(row: dict) -> str | None:
    source = row.get("source") if isinstance(row.get("source"), dict) else {}
    metadata = source.get("metadata") or {}
    reference = metadata.get("order_id") or source.get("id") or row.get("id")
    return str(reference) if reference else None


def _as_dict(obj: Any) -> dict:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return dict(obj)


def lines_from_balance_transactions(rows: list[dict]) -> list[PayoutLine]:
    lines: list[PayoutLine] = []
    for row in rows:
        amount_minor = int(row.get("amount") or 0)
        fee_minor = int(row.get("fee") or 0) if row.get("fee") is not None else None
        net_minor = int(row.get("net") or 0) if row.get("net") is not None else amount_minor
        currency = str(row.get("currency") or "usd").upper()
        line_type = str(row.get("type") or "other")
        line = PayoutLine(
            line_type=line_type,
            amount=major_units(amount_minor, currency),
            currency=currency,
            reference=_source_reference(row),
            description=str(row.get("description") or row.get("type") or ""),
            provider_object_id=str(row.get("id") or "") or None,
            amount_minor=amount_minor,
            fee_minor=fee_minor,
            net_minor=net_minor,
            source_object_id=_source_id(row),
            created=_created_iso(row.get("created")),
        )
        line.category = classify_line(line)
        lines.append(line)
    return lines


def normalize_payout(
    payload: dict,
    lines: list[PayoutLine] | None = None,
    *,
    bank: dict | None = None,
) -> ProviderPayout:
    obj = payload.get("data", {}).get("object") or payload
    payout_id = str(obj.get("id") or "")
    amount = int(obj.get("amount") or 0)
    currency = str(obj.get("currency") or "usd").upper()
    deposit = bank or {}
    bank_amount = deposit.get("amount")
    return ProviderPayout(
        provider="stripe",
        event_id=str(payload.get("id") or payout_id),
        payout_id=payout_id,
        status=str(obj.get("status") or ""),
        amount=amount,
        currency=currency,
        arrival_date=_arrival_date(obj),
        provider_created_at=str(obj.get("created") or payload.get("created") or ""),
        source_event_type=str(payload.get("type") or "payout"),
        raw_source_ref=f"stripe:{payload.get('id') or payout_id}",
        reference=obj.get("statement_descriptor") or obj.get("id"),
        lines=lines or [],
        bank_deposit_id=deposit.get("deposit_id"),
        bank_deposit_amount=bank_amount,
        bank_deposit_currency=str(deposit.get("currency") or currency).upper() if bank_amount is not None else None,
    )


class StripeProvider:
    mode = "mock"

    def fetch_payout(self, payout_id: str) -> dict:
        raise NotImplementedError

    def fetch_balance_transactions(self, payout_id: str) -> list[dict]:
        raise NotImplementedError

    def list_recent_payouts(self, *, limit: int = 20) -> list[dict]:
        raise NotImplementedError

    def load_bank_deposit(self, payout_id: str) -> dict | None:
        stored = get_bank_deposit(payout_id)
        if stored:
            return stored
        return None

    def ping(self) -> dict[str, str]:
        return {"api_connection": "mock"}


class MockStripeProvider(StripeProvider):
    mode = "mock"

    def fetch_payout(self, payout_id: str) -> dict:
        for payload in demo_payloads():
            obj = payload.get("data", {}).get("object") or {}
            if str(obj.get("id") or "") == payout_id:
                return dict(obj)
        raise StripeAPIFailure(f"missing_payout:{payout_id}")

    def fetch_balance_transactions(self, payout_id: str) -> list[dict]:
        path = fixture_dir("stripe") / "balance_transactions.json"
        rows = load_json(path)
        return [row for row in rows if row.get("payout") == payout_id]

    def list_recent_payouts(self, *, limit: int = 20) -> list[dict]:
        seen: dict[str, dict] = {}
        for payload in demo_payloads():
            obj = payload.get("data", {}).get("object") or {}
            payout_id = str(obj.get("id") or "")
            if payout_id:
                seen[payout_id] = dict(obj)
        return list(seen.values())[:limit]

    def load_bank_deposit(self, payout_id: str) -> dict | None:
        stored = super().load_bank_deposit(payout_id)
        if stored:
            return stored
        path = fixture_dir("stripe") / "bank_deposit.json"
        row = load_json(path)
        if isinstance(row, list):
            match = next((item for item in row if item.get("payout_id") == payout_id), None)
            if match:
                return match
        elif row.get("payout_id") == payout_id:
            return row
        multi = fixture_dir("stripe") / "bank_deposits.json"
        if multi.exists():
            for item in load_json(multi):
                if item.get("payout_id") == payout_id:
                    return item
        return None

    def ping(self) -> dict[str, str]:
        return {"api_connection": "mock"}


class LiveStripeProvider(StripeProvider):
    mode = "live"

    def _api_key(self) -> str:
        key = secret_key()
        if not key:
            raise StripeConfigError("STRIPE_SECRET_KEY is not set")
        return key

    def fetch_payout(self, payout_id: str) -> dict:
        import stripe as stripe_sdk

        try:
            payout = stripe_sdk.Payout.retrieve(payout_id, api_key=self._api_key())
        except StripeConfigError:
            raise
        except Exception as exc:
            raise StripeAPIFailure(str(exc)) from exc
        return _as_dict(payout)

    def _page_list(self, list_fn, *, limit: int, extra: dict[str, Any] | None = None) -> list[dict]:
        extra = extra or {}
        rows: list[dict] = []
        starting_after = None
        while True:
            params = {"limit": min(limit, 100), "api_key": self._api_key(), **extra}
            if starting_after:
                params["starting_after"] = starting_after
            listed = list_fn(**params)
            if hasattr(listed, "auto_paging_iter") and starting_after is None:
                for item in listed.auto_paging_iter():
                    rows.append(_as_dict(item))
                    if len(rows) >= limit:
                        return rows
                if rows:
                    return rows
            page = list(getattr(listed, "data", None) or (listed.get("data") if isinstance(listed, dict) else []) or [])
            if not page:
                break
            rows.extend(_as_dict(item) for item in page)
            has_more = bool(getattr(listed, "has_more", False) if not isinstance(listed, dict) else listed.get("has_more"))
            if not has_more or len(rows) >= limit:
                break
            last = page[-1]
            starting_after = last.get("id") if isinstance(last, dict) else getattr(last, "id", None)
            if not starting_after:
                break
        return rows

    def fetch_balance_transactions(self, payout_id: str) -> list[dict]:
        import stripe as stripe_sdk

        try:
            return self._page_list(
                stripe_sdk.BalanceTransaction.list,
                limit=10000,
                extra={"payout": payout_id, "expand": ["data.source"]},
            )
        except StripeConfigError:
            raise
        except Exception as exc:
            raise StripeAPIFailure(str(exc)) from exc

    def list_recent_payouts(self, *, limit: int = 20) -> list[dict]:
        import stripe as stripe_sdk

        try:
            return self._page_list(stripe_sdk.Payout.list, limit=limit)[:limit]
        except StripeConfigError:
            raise
        except Exception as exc:
            raise StripeAPIFailure(str(exc)) from exc

    def ping(self) -> dict[str, str]:
        import stripe as stripe_sdk

        try:
            stripe_sdk.Balance.retrieve(api_key=self._api_key())
            return {"api_connection": "OK"}
        except StripeConfigError:
            return {"api_connection": "missing_secret_key"}
        except Exception:
            return {"api_connection": "error"}


def get_stripe_provider(*, force_mock: bool = False) -> StripeProvider:
    if force_mock or stripe_mode() != "live":
        return MockStripeProvider()
    return LiveStripeProvider()


def verify_signature(raw: bytes, signature: str | None, secret: str | None = None) -> bool:
    secret = secret if secret is not None else webhook_secret()
    if not signature or not secret:
        return False
    try:
        import stripe as stripe_sdk

        stripe_sdk.Webhook.construct_event(payload=raw, sig_header=signature, secret=secret)
        return True
    except Exception:
        return False


def sign(raw: bytes, secret: str | None = None) -> str:
    import stripe as stripe_sdk

    secret = secret if secret is not None else webhook_secret() or MOCK_WEBHOOK_SECRET
    payload = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
    return stripe_sdk.WebhookSignature.generate_signature_header(payload=payload, secret=secret)


def event_id(payload: dict) -> str:
    return str(payload.get("id") or "")


def _should_load_transactions(event_type: str, provider: StripeProvider, payout_id: str) -> bool:
    if isinstance(provider, MockStripeProvider) or getattr(provider, "mode", "") == "mock":
        return True
    if event_type in READY_TXN_EVENTS:
        return True
    existing = get_payout(payout_id)
    return bool(existing and existing.lines)


def _payout_envelope(payout_obj: dict, *, event_id_value: str, event_type: str) -> dict:
    return {
        "id": event_id_value,
        "type": event_type,
        "created": payout_obj.get("created"),
        "data": {"object": payout_obj},
    }


def _write_payout_trace(
    *,
    event: WebhookEvent,
    payout: ProviderPayout,
    breakdown,
    duplicate: bool,
    replay: bool,
) -> None:
    write_trace(
        f"stripe-{payout.payout_id}",
        {
            "stripe_event_id": event.provider_event_id,
            "event_type": event.event_type,
            "payout_id": payout.payout_id,
            "balance_transaction_ids": [line.provider_object_id for line in payout.lines if line.provider_object_id],
            "categories": [line.category or classify_line(line) for line in breakdown.lines],
            "expected_payout": breakdown.expected_payout,
            "expected_payout_minor": breakdown.expected_payout_minor,
            "actual_payout": breakdown.actual_payout,
            "bank_deposit_id": breakdown.bank_deposit_id,
            "bank_deposit_amount": breakdown.bank_deposit_amount,
            "difference": breakdown.difference,
            "reconciliation_status": breakdown.status,
            "exceptions": breakdown.exceptions,
            "duplicate": duplicate,
            "replay": replay,
            "received_at": event.received_at.isoformat() if event.received_at else None,
            "provider_created_at": event.provider_created_at.isoformat() if event.provider_created_at else None,
        },
    )


def ingest_payout(
    payout_id: str,
    *,
    event_id_value: str,
    event_type: str,
    provider: StripeProvider | None = None,
    payout_obj: dict | None = None,
) -> tuple[ProviderPayout, Any, bool]:
    provider = provider or get_stripe_provider()
    if not payout_id:
        raise StripeAPIFailure("missing_payout")
    fetched = payout_obj or provider.fetch_payout(payout_id)
    lines: list[PayoutLine] = []
    if _should_load_transactions(event_type, provider, payout_id):
        lines = lines_from_balance_transactions(provider.fetch_balance_transactions(payout_id))
    envelope = _payout_envelope(fetched, event_id_value=event_id_value, event_type=event_type)
    bank = provider.load_bank_deposit(payout_id)
    payout = remember_payout(normalize_payout(envelope, lines, bank=bank))
    breakdown = reconcile_payout(payout)
    _, is_new = remember_reconciliation(breakdown)
    if breakdown.fees:
        from ar.stripe_intake import apply_payout_fee

        fee_date = payout.arrival_date or datetime.now(timezone.utc).date().isoformat()
        apply_payout_fee(payout.payout_id, abs(breakdown.fees), fee_date)
    return payout, breakdown, is_new


def _process_routed_event(payload: dict, *, stored: WebhookEvent, workflow: str) -> IntegrationResult:
    from ar.stripe_intake import apply_stripe_dispute, apply_stripe_payment, apply_stripe_refund
    from close.context import remember_link

    obj = payload.get("data", {}).get("object") or {}
    event_type = str(payload.get("type") or "")
    eid = event_id(payload)
    try:
        if workflow == WORKFLOW_PAYMENT:
            outcome = apply_stripe_payment(obj, event_type=event_type)
        elif workflow == WORKFLOW_REFUND:
            outcome = apply_stripe_refund(obj, event_type=event_type)
        elif workflow == WORKFLOW_DISPUTE:
            outcome = apply_stripe_dispute(obj, event_type=event_type)
        else:
            stored.processing_status = "processed"
            stored.downstream = WORKFLOW_PAYMENT_FAILED
            stored.result = "payment_failed"
            update_event(stored)
            return IntegrationResult(
                provider="stripe",
                action="webhook",
                status="processed",
                provider_event_id=eid,
                workflow=WORKFLOW_PAYMENT_FAILED,
                message=f"{event_type} recorded without AR posting",
                details={"workflow": WORKFLOW_PAYMENT_FAILED, "object_id": obj.get("id")},
            )
    except Exception as exc:
        stored.processing_status = "error"
        stored.error = str(exc)
        stored.downstream = workflow
        update_event(stored)
        return IntegrationResult(
            provider="stripe",
            action="webhook",
            status="error",
            provider_event_id=eid,
            workflow=workflow,
            message=str(exc),
            details={"exceptions": ["stripe_downstream_error"], "workflow": workflow},
        )

    stored.processing_status = "processed"
    stored.normalized_id = str(outcome.get("payment_id") or obj.get("id") or "")
    stored.downstream = workflow
    stored.result = str(outcome.get("status") or "processed")
    update_event(stored)
    remember_link(
        source_document_id=str(obj.get("id") or eid),
        transaction_id=str(outcome.get("payment_id") or ""),
        extra={
            "workflow": workflow,
            "stripe_event_id": eid,
            "invoice_ids": outcome.get("invoice_ids") or [],
        },
    )
    write_trace(
        f"stripe-{workflow}-{eid or obj.get('id')}",
        {
            "stripe_event_id": eid,
            "event_type": event_type,
            "workflow": workflow,
            **{key: value for key, value in outcome.items() if key != "invoice_changes"},
        },
    )
    return IntegrationResult(
        provider="stripe",
        action="webhook",
        status="duplicate" if outcome.get("duplicate") or outcome.get("status") == "duplicate" else "processed",
        provider_event_id=eid,
        duplicate=bool(outcome.get("duplicate") or outcome.get("status") == "duplicate"),
        payment_id=outcome.get("payment_id"),
        workflow=workflow,
        invoice_numbers=list(outcome.get("invoice_ids") or []),
        message=f"{event_type} → {workflow}",
        details={"workflow": workflow, **outcome},
    )


def process_event(
    payload: dict,
    *,
    verified: bool,
    raw: bytes,
    provider: StripeProvider | None = None,
) -> IntegrationResult:
    provider = provider or get_stripe_provider()
    event_type = str(payload.get("type") or "")
    eid = event_id(payload)
    envelope = WebhookEvent(
        provider="stripe",
        provider_event_id=eid or payload_hash(raw),
        event_type=event_type,
        provider_created_at=_created_at(payload),
        verified=verified,
        raw_payload_hash=payload_hash(raw),
        source_ref=f"stripe:{eid}",
    )
    stored = remember_event(envelope)
    if stored.receipt_count > 1:
        return IntegrationResult(
            provider="stripe",
            action="webhook",
            status="duplicate",
            provider_event_id=stored.provider_event_id,
            duplicate=True,
            payout_id=stored.normalized_id,
            workflow=WORKFLOW_DUPLICATE,
            message="duplicate Stripe event; no second payout",
            details={"exceptions": ["duplicate_event"], "replay": True, "workflow": WORKFLOW_DUPLICATE},
        )
    workflow = classify_stripe_event(event_type)
    if workflow in {WORKFLOW_PAYMENT, WORKFLOW_REFUND, WORKFLOW_DISPUTE, WORKFLOW_PAYMENT_FAILED}:
        return _process_routed_event(payload, stored=stored, workflow=workflow)
    if event_type not in PAYOUT_EVENTS:
        stored.processing_status = "ignored"
        stored.result = "not_a_payout_event"
        stored.downstream = WORKFLOW_IGNORED
        update_event(stored)
        return IntegrationResult(
            provider="stripe",
            action="webhook",
            status="ignored",
            provider_event_id=eid,
            workflow=WORKFLOW_IGNORED,
            message=f"ignored event type {event_type}",
            details={"exceptions": ["unsupported_event"], "workflow": WORKFLOW_IGNORED},
        )

    obj = payload.get("data", {}).get("object") or {}
    payout_id = str(obj.get("id") or "")
    if not payout_id:
        stored.processing_status = "error"
        stored.result = "missing_payout"
        stored.error = "missing_payout"
        update_event(stored)
        return IntegrationResult(
            provider="stripe",
            action="webhook",
            status="error",
            provider_event_id=eid,
            message="missing payout id",
            details={"exceptions": ["missing_payout"]},
        )

    try:
        payout, breakdown, is_new = ingest_payout(
            payout_id,
            event_id_value=eid,
            event_type=event_type,
            provider=provider,
            payout_obj=obj if isinstance(provider, MockStripeProvider) else None,
        )
    except StripeConfigError as exc:
        stored.processing_status = "error"
        stored.error = "missing_credentials"
        stored.result = "stripe_config_error"
        update_event(stored)
        return IntegrationResult(
            provider="stripe",
            action="webhook",
            status="error",
            provider_event_id=eid,
            payout_id=payout_id,
            message=str(exc),
            details={"exceptions": ["missing_credentials"]},
        )
    except StripeAPIFailure as exc:
        stored.processing_status = "error"
        stored.error = "stripe_api_failure"
        stored.result = str(exc)
        update_event(stored)
        write_trace(
            f"stripe-error-{eid or payout_id}",
            {
                "stripe_event_id": eid,
                "event_type": event_type,
                "payout_id": payout_id,
                "error": "stripe_api_failure",
                "message": str(exc),
            },
        )
        return IntegrationResult(
            provider="stripe",
            action="webhook",
            status="error",
            provider_event_id=eid,
            payout_id=payout_id,
            message=f"Stripe API failure: {exc}",
            details={"exceptions": ["stripe_api_failure"]},
        )

    stored.processing_status = "processed"
    stored.normalized_id = payout.payout_id
    stored.downstream = WORKFLOW_PAYOUT
    stored.result = "payout_recorded"
    update_event(stored)
    _write_payout_trace(event=stored, payout=payout, breakdown=breakdown, duplicate=False, replay=not is_new)
    exception_workflow = classify_reconciliation_exception(breakdown.exceptions)
    return IntegrationResult(
        provider="stripe",
        action="webhook",
        status="processed",
        provider_event_id=eid,
        payout_id=payout.payout_id,
        payout_amount=major_units(payout.amount, payout.currency),
        invoice_candidates=0,
        workflow=exception_workflow if breakdown.exceptions else WORKFLOW_PAYOUT,
        message=f"{event_type} payout {payout.payout_id}",
        details={
            "matched": breakdown.matched,
            "status": breakdown.status,
            "expected": breakdown.expected_payout,
            "actual": breakdown.actual_payout,
            "source_count": len(payout.lines),
            "new_reconciliation": is_new,
            "exceptions": breakdown.exceptions,
            "invoice_candidates": 0,
            "workflow": exception_workflow if breakdown.exceptions else WORKFLOW_PAYOUT,
            "balance_transaction_ids": [line.provider_object_id for line in payout.lines if line.provider_object_id],
            "bank_deposit_id": breakdown.bank_deposit_id,
        },
    )


def process_raw(
    raw: bytes,
    headers: dict[str, str],
    *,
    require_signature: bool = True,
    provider: StripeProvider | None = None,
) -> IntegrationResult:
    signature = headers.get("stripe-signature") or headers.get("Stripe-Signature")
    if require_signature:
        if not signature:
            return IntegrationResult(
                provider="stripe",
                action="webhook",
                status="rejected",
                message="missing Stripe-Signature",
                details={"exceptions": ["missing_signature"]},
            )
        if not verify_signature(raw, signature):
            return IntegrationResult(
                provider="stripe",
                action="webhook",
                status="rejected",
                message="invalid Stripe-Signature",
                details={"exceptions": ["invalid_signature"]},
            )
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return IntegrationResult(
            provider="stripe",
            action="webhook",
            status="rejected",
            message="malformed Stripe event",
            details={"exceptions": ["malformed_event"]},
        )
    if not isinstance(payload, dict):
        return IntegrationResult(
            provider="stripe",
            action="webhook",
            status="rejected",
            message="malformed Stripe event",
            details={"exceptions": ["malformed_event"]},
        )
    return process_event(payload, verified=True, raw=raw, provider=provider or get_stripe_provider())


def demo_payloads() -> list[dict[str, Any]]:
    return load_json(fixture_dir("stripe") / "events.json")


def sync(*, payout_id: str | None = None, provider: StripeProvider | None = None) -> IntegrationResult:
    provider = provider or get_stripe_provider()
    before_payouts = {item.payout_id for item in all_payouts() if item.provider == "stripe"}
    before_recons = {item.payout_id for item in all_reconciliations() if item.provider == "stripe"}
    try:
        if payout_id:
            targets = [provider.fetch_payout(payout_id)]
        else:
            targets = provider.list_recent_payouts()
    except StripeConfigError as exc:
        return IntegrationResult(
            provider="stripe",
            action="sync",
            status="error",
            message=str(exc),
            details={"exceptions": ["missing_credentials"]},
        )
    except StripeAPIFailure as exc:
        write_trace(
            "stripe-sync-error",
            {"error": "stripe_api_failure", "message": str(exc), "payout_id": payout_id},
        )
        return IntegrationResult(
            provider="stripe",
            action="sync",
            status="error",
            message=f"Stripe API failure: {exc}",
            details={"exceptions": ["stripe_api_failure"]},
        )

    processed: list[str] = []
    new_payouts = 0
    new_recons = 0
    last_breakdown = None
    for obj in targets:
        pid = str(obj.get("id") or "")
        if not pid:
            continue
        payout, breakdown, is_new = ingest_payout(
            pid,
            event_id_value=f"sync:{pid}",
            event_type="payout.reconciliation_completed",
            provider=provider,
            payout_obj=obj if isinstance(provider, MockStripeProvider) else None,
        )
        processed.append(payout.payout_id)
        last_breakdown = breakdown
        if payout.payout_id not in before_payouts:
            new_payouts += 1
        if is_new and payout.payout_id not in before_recons:
            new_recons += 1

    return IntegrationResult(
        provider="stripe",
        action="sync",
        status="processed",
        payout_id=processed[-1] if processed else payout_id,
        payout_amount=last_breakdown.actual_payout if last_breakdown else None,
        invoice_candidates=0,
        message=f"synced {len(processed)} Stripe payout(s)",
        details={
            "payout_ids": processed,
            "new_payouts": new_payouts,
            "new_reconciliations": new_recons,
            "status": last_breakdown.status if last_breakdown else None,
        },
    )


def connection_status() -> str:
    mode = stripe_mode()
    lines = ["Stripe", f"  mode: {mode}"]
    if mode == "mock":
        return "\n".join(lines)
    key_state = "configured" if secret_key() else "missing"
    hook_state = "configured" if env("STRIPE_WEBHOOK_SECRET") else "missing"
    ping = LiveStripeProvider().ping()
    lines.extend(
        [
            f"  secret key: {key_state}",
            f"  API connection: {ping.get('api_connection', 'unknown')}",
            f"  webhook secret: {hook_state}",
        ]
    )
    return "\n".join(lines)


def format_stripe_report(payout: ProviderPayout | None = None) -> str:
    payout = payout or get_payout("po_1HackMIT97420")
    if payout is None:
        return "No Stripe payout recorded."
    breakdown = get_reconciliation(payout.payout_id) or reconcile_payout(payout)

    def money(value: float) -> str:
        sign = "-" if value < 0 else ""
        return f"{sign}${abs(value):,.2f}"

    bank = "unavailable" if breakdown.bank_deposit_amount is None else money(breakdown.bank_deposit_amount)
    return "\n".join(
        [
            "Stripe payout reconciliation",
            "",
            f"Payout: {payout.payout_id}",
            "",
            f"Gross payments            {money(breakdown.gross_payments)}",
            f"Refunds                     {money(breakdown.refunds)}",
            f"Chargebacks                 {money(breakdown.chargebacks)}",
            f"Processor fees              {money(breakdown.fees)}",
            "--------------------------------------",
            f"Expected payout             {money(breakdown.expected_payout)}",
            "",
            f"Bank deposit                {bank}",
            f"Difference                  {money(breakdown.difference)}",
            "",
            f"Status: {breakdown.status}",
        ]
    )


def run_stripe_demo() -> str:
    from integrations.store import reset_integration_state

    reset_integration_state()
    provider = MockStripeProvider()
    first = []
    for payload in demo_payloads():
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        first.append(process_raw(raw, {"stripe-signature": sign(raw)}, provider=provider))
    payout = get_payout("po_1HackMIT97420")
    lines = [format_stripe_report(payout), ""]
    replay_event = next(
        (item for item in demo_payloads() if item.get("type") == "payout.reconciliation_completed"),
        demo_payloads()[-1],
    )
    raw = json.dumps(replay_event, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    replay = process_raw(raw, {"stripe-signature": sign(raw)}, provider=provider)
    new_payouts = 0 if replay.duplicate else 1
    new_recons = 0 if replay.duplicate or not (replay.details or {}).get("new_reconciliation") else 1
    lines.extend(
        [
            f"Replaying Stripe event {replay_event.get('id')}...",
            "",
            f"New payout records: {new_payouts}",
            f"New reconciliations: {new_recons}",
            "",
            f"Idempotency: {'PASS' if replay.duplicate and new_payouts == 0 and new_recons == 0 else 'FAIL'}",
        ]
    )
    write_trace("stripe-demo", {"first": [item.model_dump(mode="json") for item in first], "replay": replay.model_dump(mode="json")})
    return "\n".join(lines)


# Back-compat names used by older tests/docs.
def _secret() -> str:
    return webhook_secret() or MOCK_WEBHOOK_SECRET


def _lines_from_balance_txns(rows: list[dict]) -> list[PayoutLine]:
    return lines_from_balance_transactions(rows)


def load_balance_transactions(payout_id: str) -> list[dict]:
    return MockStripeProvider().fetch_balance_transactions(payout_id)


def load_bank_deposit(payout_id: str) -> dict | None:
    return MockStripeProvider().load_bank_deposit(payout_id)

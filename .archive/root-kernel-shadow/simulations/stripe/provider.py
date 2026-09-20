"""In-memory Stripe provider that serves simulator objects through the real adapter."""

from __future__ import annotations

from typing import Any

from integrations.providers.stripe import StripeAPIFailure, StripeProvider


class SimulatedStripeProvider(StripeProvider):
    mode = "mock"

    def __init__(self, universe: dict[str, Any]):
        self.universe = universe
        self._available_txn_ids: set[str] | None = None
        withheld = universe.get("withheld_txn_ids") or []
        if withheld:
            all_ids = {str(row.get("id")) for row in universe.get("balance_transactions") or []}
            self._available_txn_ids = all_ids - {str(item) for item in withheld}

    def withhold_transactions(self, txn_ids: list[str]) -> None:
        all_ids = {str(row.get("id")) for row in self.universe.get("balance_transactions") or []}
        blocked = {str(item) for item in txn_ids}
        current = self._available_txn_ids if self._available_txn_ids is not None else all_ids
        self._available_txn_ids = current - blocked

    def release_transactions(self, txn_ids: list[str]) -> None:
        if self._available_txn_ids is None:
            return
        self._available_txn_ids.update(str(item) for item in txn_ids)

    def _payouts(self) -> list[dict]:
        return list(self.universe.get("payouts") or [])

    def fetch_payout(self, payout_id: str) -> dict:
        for row in self._payouts():
            if str(row.get("id") or "") == payout_id:
                return dict(row)
        raise StripeAPIFailure(f"missing_payout:{payout_id}")

    def fetch_balance_transactions(self, payout_id: str) -> list[dict]:
        rows = []
        for row in self.universe.get("balance_transactions") or []:
            if row.get("payout") != payout_id:
                continue
            txn_id = str(row.get("id") or "")
            if self._available_txn_ids is not None and txn_id not in self._available_txn_ids:
                continue
            rows.append(dict(row))
        return rows

    def list_recent_payouts(self, *, limit: int = 20) -> list[dict]:
        return [dict(row) for row in self._payouts()[:limit]]

    def load_bank_deposit(self, payout_id: str) -> dict | None:
        stored = super().load_bank_deposit(payout_id)
        if stored:
            return stored
        for row in self.universe.get("bank_deposits") or []:
            if row.get("payout_id") == payout_id:
                return dict(row)
        return None

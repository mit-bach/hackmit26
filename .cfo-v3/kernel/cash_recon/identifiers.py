"""Trust apply/pay identifiers. Cash ticks the bank line. It does not re-guess the counterparty."""

from __future__ import annotations

import json
from pathlib import Path

from cash_recon.models import IdentifierTick, MatchCandidate, PipeIdentifier

IDENTITY_MATCH_TYPES = {"EXACT_MATCH", "GROUPED_MATCH", "FEE_NETTED"}
PIPE_SOURCES = {"apply", "pay"}


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def identifier_for_bank(
    bank_transaction_id: str,
    identifiers: list[PipeIdentifier],
    *,
    bank_reference: str = "",
) -> PipeIdentifier | None:
    """First apply/pay identifier that names this bank line. Memo text is not an identifier."""
    target = _norm(bank_transaction_id)
    ref = _norm(bank_reference)
    for item in identifiers:
        if item.source not in PIPE_SOURCES:
            continue
        if target and _norm(item.bank_transaction_id) == target:
            return item
        if ref and _norm(item.bank_reference) == ref:
            return item
    return None


def _ledger_overlap(candidate: MatchCandidate, ident: PipeIdentifier) -> bool:
    cand_ledger = {_norm(item) for item in candidate.ledger_entry_ids}
    named_ledger = {_norm(item) for item in ident.ledger_entry_ids if item}
    if named_ledger:
        if not cand_ledger:
            return True
        return bool(cand_ledger & named_ledger)
    named_inv = {_norm(item) for item in ident.invoice_ids if item}
    if named_inv:
        blob = " ".join(list(candidate.ledger_entry_ids) + list(candidate.evidence)).lower()
        return any(item in blob for item in named_inv) or bool(cand_ledger & named_inv)
    return True


def identifier_compatible(candidate: MatchCandidate, ident: PipeIdentifier) -> bool:
    """True when this Kernel candidate does not invent a second counterparty."""
    if ident.ledger_entry_ids or ident.invoice_ids:
        if candidate.ledger_entry_ids and not _ledger_overlap(candidate, ident):
            if candidate.match_type in IDENTITY_MATCH_TYPES:
                return False
    return True


def choose_candidate_for_line(
    bank_transaction_id: str,
    universe: list[MatchCandidate],
    identifiers: list[PipeIdentifier],
    *,
    require_identifier: bool = False,
    bank_reference: str = "",
) -> IdentifierTick:
    """Copy a candidate_id. Do not invent the customer or vendor from the memo."""
    line = [
        item
        for item in universe
        if bank_transaction_id in item.bank_transaction_ids
    ]
    ident = identifier_for_bank(
        bank_transaction_id, identifiers, bank_reference=bank_reference
    )
    if ident is not None:
        compatible = [item for item in line if identifier_compatible(item, ident)]
        if not compatible:
            return IdentifierTick(
                bank_transaction_id=bank_transaction_id,
                identifier_present=True,
                fail_closed=True,
                guessed_counterparty=False,
                reason="Identifier is present; no Kernel candidate copies it. Do not invent a counterparty.",
                source=ident.source,
            )
        unexplained = [
            item
            for item in compatible
            if item.match_type == "UNEXPLAINED_DIFFERENCE" and item.difference_minor != 0
        ]
        if unexplained:
            chosen = sorted(unexplained, key=lambda item: (-item.score, item.candidate_id))[0]
            return IdentifierTick(
                bank_transaction_id=bank_transaction_id,
                selected_candidate_id=chosen.candidate_id,
                identifier_present=True,
                fail_closed=False,
                guessed_counterparty=False,
                reason="Pipe identifier copied. Residual stays unexplained. Do not invent a fee.",
                source=ident.source,
            )
        chosen = sorted(compatible, key=lambda item: (-item.score, item.candidate_id))[0]
        return IdentifierTick(
            bank_transaction_id=bank_transaction_id,
            selected_candidate_id=chosen.candidate_id,
            identifier_present=True,
            fail_closed=False,
            guessed_counterparty=False,
            reason="Pipe identifier copied. Bank tick uses apply/pay identity.",
            source=ident.source,
        )

    identity_rows = [item for item in line if item.match_type in IDENTITY_MATCH_TYPES]
    if require_identifier and identity_rows:
        return IdentifierTick(
            bank_transaction_id=bank_transaction_id,
            identifier_present=False,
            fail_closed=True,
            guessed_counterparty=True,
            reason="apply/pay have not identified this line. Fail closed. Handle ctl-cash. Do not scrape the memo.",
        )
    if line:
        chosen = sorted(line, key=lambda item: (-item.score, item.candidate_id))[0]
        return IdentifierTick(
            bank_transaction_id=bank_transaction_id,
            selected_candidate_id=chosen.candidate_id,
            identifier_present=False,
            fail_closed=False,
            guessed_counterparty=False,
            reason="No pipe identifier. Kernel candidate only; not a counterparty claim.",
        )
    return IdentifierTick(
        bank_transaction_id=bank_transaction_id,
        identifier_present=False,
        fail_closed=True,
        reason="No Kernel candidate for this bank line.",
    )


def load_apply_identifier_packets(directory: Path | None) -> list[PipeIdentifier]:
    """Read apply identified-deposit packets. Do not rewrite AR application."""
    if directory is None or not directory.is_dir():
        return []
    rows: list[PipeIdentifier] = []
    for path in sorted(directory.glob("*.json")):
        try:
            raw = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict):
            continue
        if raw.get("object") not in {"identified_deposit", "identified-deposit"}:
            continue
        bank_id = str(
            raw.get("bank_transaction_id")
            or raw.get("bank_id")
            or (raw.get("metadata") or {}).get("bank_transaction_id")
            or ""
        )
        rows.append(
            PipeIdentifier(
                source="apply",
                bank_transaction_id=bank_id,
                bank_reference=str(raw.get("bank_reference") or ""),
                payment_id=str(raw.get("payment_id") or ""),
                invoice_ids=[str(item) for item in (raw.get("invoice_ids") or []) if item],
                ledger_entry_ids=[str(item) for item in (raw.get("ledger_entry_ids") or []) if item],
                customer_id=str(raw.get("customer_id") or ""),
                counterparty=str(raw.get("customer_name") or raw.get("counterparty") or ""),
            )
        )
    return rows


def load_pay_identifier_packets(directory: Path | None) -> list[PipeIdentifier]:
    """Read pay expected-outflow packets. Do not rewrite the pay-run."""
    if directory is None or not directory.is_dir():
        return []
    rows: list[PipeIdentifier] = []
    for path in sorted(directory.glob("*.json")):
        try:
            raw = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict):
            continue
        if raw.get("kind") not in {"expected_outflows", "identified_wire", "identified-wire"}:
            continue
        for wire in raw.get("wires") or []:
            if not isinstance(wire, dict):
                continue
            rows.append(
                PipeIdentifier(
                    source="pay",
                    bank_transaction_id=str(wire.get("bank_transaction_id") or ""),
                    bank_reference=str(wire.get("bank_reference") or wire.get("invoice_id") or ""),
                    invoice_ids=[str(wire["invoice_id"])] if wire.get("invoice_id") else [],
                    ledger_entry_ids=[str(item) for item in (wire.get("ledger_entry_ids") or []) if item],
                    vendor=str(wire.get("vendor") or ""),
                    counterparty=str(wire.get("vendor") or ""),
                )
            )
    return rows

"""Canonical identity links across AP, AR, cash, accruals, prepaids, assets, and close."""

from __future__ import annotations

import json
from pathlib import Path

from close.dates import now_iso
from close.models import IdentityLink

CONTEXT_DIR = Path(__file__).resolve().parent.parent / "runs" / "month_end"
CONTEXT_PATH = CONTEXT_DIR / "identity_links.json"

_links: list[dict] | None = None


def configure_paths(directory: Path) -> None:
    global CONTEXT_DIR, CONTEXT_PATH, _links
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    CONTEXT_DIR = directory
    CONTEXT_PATH = directory / "identity_links.json"
    _links = None


def reset_context() -> None:
    global _links
    _links = []
    _write([])


def _read() -> list[dict]:
    global _links
    if _links is not None:
        return _links
    if not CONTEXT_PATH.exists():
        _links = []
        return _links
    raw = json.loads(CONTEXT_PATH.read_text())
    _links = raw if isinstance(raw, list) else []
    return _links


def _write(rows: list[dict]) -> None:
    global _links
    CONTEXT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTEXT_PATH.write_text(json.dumps(rows, indent=2) + "\n")
    _links = rows


def _next_id() -> str:
    return f"LNK-{len(_read()) + 1:04d}"


def remember_link(
    *,
    source_document_id: str = "",
    transaction_id: str = "",
    journal_entry_id: str = "",
    account_id: str = "",
    reconciliation_id: str = "",
    close_task_id: str = "",
    review_id: str = "",
    extra: dict | None = None,
) -> IdentityLink:
    payload = {
        "source_document_id": source_document_id,
        "transaction_id": transaction_id,
        "journal_entry_id": journal_entry_id,
        "account_id": account_id,
        "reconciliation_id": reconciliation_id,
        "close_task_id": close_task_id,
        "review_id": review_id,
        "extra": extra or {},
    }
    for item in _read():
        same = all(item.get(key) == value for key, value in payload.items() if key != "extra")
        if same:
            return IdentityLink.model_validate(item)
    link = IdentityLink(link_id=_next_id(), created_at=now_iso(), **payload)
    rows = _read()
    rows.append(link.model_dump())
    _write(rows)
    return link


def all_links() -> list[IdentityLink]:
    return [IdentityLink.model_validate(item) for item in _read()]


def links_for(**filters: str) -> list[IdentityLink]:
    rows = all_links()
    for key, value in filters.items():
        if not value:
            continue
        rows = [item for item in rows if getattr(item, key, "") == value]
    return rows

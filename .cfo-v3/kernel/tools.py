from __future__ import annotations

import fcntl
import json
import os
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

from agents import function_tool

from models import (
    APCaseEvidence,
    CompanyPolicy,
    GoodsReceipt,
    Invoice,
    PriorCase,
    PurchaseOrder,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
_DEFAULT_DATA_DIR = DATA_DIR


class DataFileError(Exception):
    """Raised when a data file is missing or not valid JSON."""


def configure_data_dir(directory: Path | None = None) -> Path:
    """Point AP/AR seed loaders at an alternate data root. Tests and the
    sample-data CLI use this; default remains ``data/``."""
    global DATA_DIR
    DATA_DIR = Path(directory) if directory is not None else _DEFAULT_DATA_DIR
    _file_invoices.cache_clear()
    _purchase_orders.cache_clear()
    _goods_receipts.cache_clear()
    load_policies.cache_clear()
    load_prior_cases.cache_clear()
    return DATA_DIR


def _read_json(path: Path) -> list:
    from evaluation.isolation import assert_answer_key_blocked

    assert_answer_key_blocked(path)
    try:
        raw = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise DataFileError(f"Data file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DataFileError(
            f"Invalid JSON in {path.name}: {exc.msg} (line {exc.lineno})"
        ) from exc
    if not isinstance(raw, list):
        raise DataFileError(f"{path.name} must contain a JSON array")
    return raw


_runtime_invoices: dict[str, Invoice] = {}
_runtime_loaded = False
RUNTIME_DIR_ENV = "CFO_AP_RUNTIME_DIR"
_ROOT = Path(__file__).resolve().parent
_DEFAULT_RUNTIME_DIR = _ROOT / "runs" / "ap"
_DEFAULT_OVERLAY_NAME = "runtime_invoices.json"
OVERLAY_NAME = _DEFAULT_OVERLAY_NAME


def _default_runtime_dir() -> Path:
    override = os.environ.get(RUNTIME_DIR_ENV)
    if override:
        return Path(override)
    return _DEFAULT_RUNTIME_DIR


RUNTIME_DIR = _default_runtime_dir()


def runtime_invoices_path() -> Path:
    return RUNTIME_DIR / OVERLAY_NAME


def configure_runtime_dir(directory: Path | None = None) -> Path:
    """Point the durable AP overlay at an isolated directory. Does not edit invoices.json."""
    global RUNTIME_DIR, OVERLAY_NAME, _runtime_loaded
    RUNTIME_DIR = Path(directory) if directory is not None else _default_runtime_dir()
    OVERLAY_NAME = _DEFAULT_OVERLAY_NAME
    _runtime_invoices.clear()
    _runtime_loaded = False
    return RUNTIME_DIR


def configure_overlay_path(path: Path | None = None) -> Path:
    """Office/Sidecar alias for the durable AP overlay file. Does not edit invoices.json."""
    global RUNTIME_DIR, OVERLAY_NAME, _runtime_loaded
    if path is None:
        RUNTIME_DIR = _default_runtime_dir()
        OVERLAY_NAME = _DEFAULT_OVERLAY_NAME
    else:
        target = Path(path)
        if target.suffix == ".json":
            RUNTIME_DIR = target.parent
            OVERLAY_NAME = target.name
        else:
            RUNTIME_DIR = target
            OVERLAY_NAME = _DEFAULT_OVERLAY_NAME
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    _runtime_invoices.clear()
    _runtime_loaded = False
    return runtime_invoices_path()


def _runtime_lock_path() -> Path:
    return runtime_invoices_path().with_name(runtime_invoices_path().name + ".lock")


def _atomic_write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    text = json.dumps(payload, indent=2) + "\n"
    with tmp.open("w") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


def _ensure_runtime_loaded() -> None:
    global _runtime_loaded
    if _runtime_loaded:
        return
    _runtime_loaded = True
    path = runtime_invoices_path()
    if not path.exists():
        return
    raw = json.loads(path.read_text())
    rows = raw.get("invoices") if isinstance(raw, dict) else raw
    for row in rows or []:
        invoice = Invoice.model_validate(row)
        _runtime_invoices[invoice.invoice_id] = invoice


def _persist_runtime_invoices() -> Path:
    path = runtime_invoices_path()
    _atomic_write_json(
        path,
        {
            "invoices": [item.model_dump() for item in _runtime_invoices.values()],
        },
    )
    return path


@lru_cache(maxsize=1)
def _file_invoices() -> list[Invoice]:
    return [Invoice.model_validate(item) for item in _read_json(DATA_DIR / "invoices.json")]


def register_runtime_invoice(invoice: Invoice) -> Invoice:
    """Persist an ingested invoice in the canonical AP overlay. Does not edit invoices.json."""
    global _runtime_loaded
    path = runtime_invoices_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = _runtime_lock_path()
    with lock_path.open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            _runtime_loaded = False
            _ensure_runtime_loaded()
            _runtime_invoices[invoice.invoice_id] = invoice
            _persist_runtime_invoices()
            return invoice
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def clear_runtime_invoices() -> None:
    """Drop in-memory overlay invoices. The durable file is reloaded on next read."""
    global _runtime_loaded
    _runtime_invoices.clear()
    _runtime_loaded = False


def reset_runtime_invoices() -> None:
    """Clear the durable AP overlay file and memory. Does not edit invoices.json."""
    global _runtime_loaded
    path = runtime_invoices_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = _runtime_lock_path()
    with lock_path.open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            clear_runtime_invoices()
            if path.exists():
                path.unlink()
            tmp = path.with_name(path.name + ".tmp")
            if tmp.exists():
                tmp.unlink()
            _runtime_loaded = True
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def runtime_invoices() -> list[Invoice]:
    _ensure_runtime_loaded()
    return list(_runtime_invoices.values())


def _invoices() -> list[Invoice]:
    _ensure_runtime_loaded()
    base = list(_file_invoices())
    if not _runtime_invoices:
        return base
    seen = {item.invoice_id for item in base}
    extra = [item for item in _runtime_invoices.values() if item.invoice_id not in seen]
    return base + extra


@lru_cache(maxsize=1)
def _purchase_orders() -> list[PurchaseOrder]:
    return [
        PurchaseOrder.model_validate(item)
        for item in _read_json(DATA_DIR / "purchase_orders.json")
    ]


@lru_cache(maxsize=1)
def _goods_receipts() -> list[GoodsReceipt]:
    return [
        GoodsReceipt.model_validate(item)
        for item in _read_json(DATA_DIR / "goods_receipts.json")
    ]


@lru_cache(maxsize=1)
def load_policies() -> list[CompanyPolicy]:
    return [
        CompanyPolicy.model_validate(item)
        for item in _read_json(DATA_DIR / "company_policies.json")
    ]


@lru_cache(maxsize=1)
def load_prior_cases() -> list[PriorCase]:
    return [PriorCase.model_validate(item) for item in _read_json(DATA_DIR / "prior_cases.json")]


def all_invoices() -> list[Invoice]:
    return list(_invoices())


def all_purchase_orders() -> list[PurchaseOrder]:
    return list(_purchase_orders())


def all_goods_receipts() -> list[GoodsReceipt]:
    return list(_goods_receipts())


def load_invoice(invoice_id: str) -> Invoice | None:
    for invoice in _invoices():
        if invoice.invoice_id == invoice_id:
            return invoice
    return None


def load_purchase_order(po_id: str | None) -> PurchaseOrder | None:
    if not po_id:
        return None
    for purchase_order in _purchase_orders():
        if purchase_order.po_id == po_id:
            return purchase_order
    return None


def load_goods_receipt(po_id: str | None) -> GoodsReceipt | None:
    if not po_id:
        return None
    for receipt in _goods_receipts():
        if receipt.po_id == po_id:
            return receipt
    return None


def normalize_invoice_number(value: str) -> str:
    return "".join(ch for ch in (value or "").upper() if ch.isalnum())


def paid_invoice_ids() -> set[str]:
    """Invoice IDs already settled in canonical vendor_payments.json.

    Presence on a vendor payment means the bill is not payable again, including
    grouped ACH and fee-netted wires. Missing file (handwritten fixtures) is unpaid.
    """
    path = DATA_DIR / "canonical" / "vendor_payments.json"
    if not path.exists():
        return set()
    try:
        rows = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return set()
    if not isinstance(rows, list):
        return set()
    paid: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        for invoice_id in row.get("invoice_ids") or []:
            if invoice_id:
                paid.add(str(invoice_id))
    return paid


def load_duplicate_invoices(invoice_id: str) -> list[Invoice]:
    invoice = load_invoice(invoice_id)
    if invoice is None:
        return []
    wanted = normalize_invoice_number(invoice.vendor_invoice_number)
    vendor_key = normalize_vendor(invoice.vendor)
    return [
        other
        for other in _invoices()
        if other.invoice_id != invoice.invoice_id
        and normalize_invoice_number(other.vendor_invoice_number) == wanted
        and (
            other.vendor_invoice_number == invoice.vendor_invoice_number
            or normalize_vendor(other.vendor) == vendor_key
        )
    ]


def po_exists(po_id: str | None) -> bool:
    return load_purchase_order(po_id) is not None


def po_is_approved(po_id: str | None) -> bool:
    purchase_order = load_purchase_order(po_id)
    return bool(purchase_order and purchase_order.status.lower() == "approved")


def invoice_po_amount_difference(invoice_id: str) -> float | None:
    invoice = load_invoice(invoice_id)
    if invoice is None:
        return None
    purchase_order = load_purchase_order(invoice.po_id)
    if purchase_order is None:
        return None
    return round(invoice.amount - purchase_order.authorized_amount, 2)


def invoice_amount_matches_po(invoice_id: str) -> bool:
    difference = invoice_po_amount_difference(invoice_id)
    return difference is not None and difference == 0


def vendors_match(invoice_id: str) -> bool:
    invoice = load_invoice(invoice_id)
    purchase_order = load_purchase_order(invoice.po_id) if invoice else None
    if invoice is None or purchase_order is None:
        return False
    return invoice.vendor == purchase_order.vendor


def normalize_vendor(name: str) -> str:
    cleaned = name.lower()
    cleaned = re.sub(r"[.,]", " ", cleaned)
    cleaned = re.sub(
        r"\b(co|company|inc|incorporated|llc|ltd|corp|corporation)\b",
        " ",
        cleaned,
    )
    tokens = []
    for token in cleaned.split():
        if token.endswith("ies") and len(token) > 3:
            token = token[:-3] + "y"
        elif token.endswith("es") and len(token) > 3:
            token = token[:-2]
        elif token.endswith("s") and not token.endswith("ss") and len(token) > 3:
            token = token[:-1]
        tokens.append(token)
    return "".join(ch for ch in "".join(tokens) if ch.isalnum())


def vendors_are_similar(invoice_id: str) -> bool:
    invoice = load_invoice(invoice_id)
    purchase_order = load_purchase_order(invoice.po_id) if invoice else None
    if invoice is None or purchase_order is None:
        return False
    left = normalize_vendor(invoice.vendor)
    right = normalize_vendor(purchase_order.vendor)
    return left == right or left in right or right in left


def goods_fully_received(po_id: str | None) -> bool:
    receipt = load_goods_receipt(po_id)
    if receipt is None or not receipt.received:
        return False
    if receipt.quantity_received < receipt.quantity_ordered:
        return False
    purchase_order = load_purchase_order(po_id)
    if purchase_order is not None and receipt.amount_received < purchase_order.authorized_amount:
        return False
    return True


def has_duplicate_vendor_invoice_number(invoice_id: str) -> bool:
    return len(load_duplicate_invoices(invoice_id)) > 0


def receipt_status_for(po_id: str | None) -> str:
    if not po_id:
        return "not_applicable"
    receipt = load_goods_receipt(po_id)
    if receipt is None:
        return "missing"
    if not receipt.received or (
        receipt.quantity_received == 0 and receipt.amount_received == 0
    ):
        return "not_received"
    if goods_fully_received(po_id):
        return "full"
    return "partial"


def days_until_due(invoice_id: str, as_of: date | None = None) -> int | None:
    invoice = load_invoice(invoice_id)
    if invoice is None:
        return None
    as_of = as_of or date.today()
    return (date.fromisoformat(invoice.due_date) - as_of).days


def _variance_policy() -> CompanyPolicy | None:
    for policy in load_policies():
        if policy.policy_id == "P-009":
            return policy
    return None


def within_amount_tolerance(invoice_id: str) -> bool:
    """True only when the variance is inside the explicit P-009 thresholds."""
    difference = invoice_po_amount_difference(invoice_id)
    if difference is None or difference == 0:
        return False
    invoice = load_invoice(invoice_id)
    purchase_order = load_purchase_order(invoice.po_id) if invoice else None
    if invoice is None or purchase_order is None or not purchase_order.authorized_amount:
        return False
    policy = _variance_policy()
    if policy is None:
        return False
    max_abs = float(policy.conditions.get("max_abs_variance", 0))
    max_pct = float(policy.conditions.get("max_percent_variance", 0))
    abs_diff = abs(difference)
    percent = abs_diff / purchase_order.authorized_amount
    return abs_diff <= max_abs and percent <= max_pct


def exception_types_for(invoice_id: str) -> list[str]:
    invoice = load_invoice(invoice_id)
    if invoice is None:
        return ["unknown_invoice"]
    types: list[str] = []
    if has_duplicate_vendor_invoice_number(invoice_id):
        types.append("duplicate")
    if not po_exists(invoice.po_id):
        types.append("missing_po")
    elif not po_is_approved(invoice.po_id):
        types.append("po_not_approved")
    status = receipt_status_for(invoice.po_id)
    if status in {"missing", "not_received"}:
        types.append("goods_not_received")
    if status == "partial":
        types.append("partial_receipt")
    if po_exists(invoice.po_id) and not vendors_match(invoice_id):
        types.append("vendor_mismatch")
    difference = invoice_po_amount_difference(invoice_id)
    if difference not in (None, 0):
        if within_amount_tolerance(invoice_id):
            types.append("small_amount_discrepancy")
        else:
            types.append("material_amount_mismatch")
    purchase_order = load_purchase_order(invoice.po_id)
    if purchase_order and invoice.invoice_date < purchase_order.created_date:
        types.append("unusual_timing")
    if (
        purchase_order
        and purchase_order.approval_limit is not None
        and purchase_order.authorized_amount > purchase_order.approval_limit
    ):
        types.append("approval_limit_exceeded")
    return types


def collect_case_evidence(invoice_id: str) -> APCaseEvidence:
    invoice = load_invoice(invoice_id)
    purchase_order = load_purchase_order(invoice.po_id) if invoice else None
    receipt = load_goods_receipt(invoice.po_id) if invoice else None
    difference = invoice_po_amount_difference(invoice_id) if invoice else None
    percent_difference = None
    if difference is not None and purchase_order and purchase_order.authorized_amount:
        percent_difference = round(difference / purchase_order.authorized_amount, 4)
    duplicates = load_duplicate_invoices(invoice_id) if invoice else []
    return APCaseEvidence(
        invoice_id=invoice_id,
        invoice=invoice,
        purchase_order=purchase_order,
        goods_receipt=receipt,
        amount_difference=difference,
        percent_difference=percent_difference,
        amount_matches=invoice_amount_matches_po(invoice_id) if invoice else False,
        within_amount_tolerance=within_amount_tolerance(invoice_id) if invoice else False,
        vendor_exact_match=vendors_match(invoice_id) if invoice else False,
        vendors_are_similar=vendors_are_similar(invoice_id) if invoice else False,
        po_exists=po_exists(invoice.po_id) if invoice else False,
        po_approved=po_is_approved(invoice.po_id) if invoice else False,
        receipt_status=receipt_status_for(invoice.po_id) if invoice else "not_applicable",
        duplicate_detected=bool(duplicates),
        duplicate_invoice_ids=[item.invoice_id for item in duplicates],
        exception_types=exception_types_for(invoice_id) if invoice else ["unknown_invoice"],
        days_until_due=days_until_due(invoice_id) if invoice else None,
        invoice_dated_before_po=bool(
            invoice and purchase_order and invoice.invoice_date < purchase_order.created_date
        ),
    )


def _missing_po_id(po_id: str) -> bool:
    return not po_id or po_id.strip().lower() in {"none", "null"}


def _dump(model) -> dict:
    return model.model_dump()


def match_prior_cases(exception_type: str = "", vendor: str = "") -> list[PriorCase]:
    matches: list[PriorCase] = []
    wanted_vendor = normalize_vendor(vendor) if vendor else ""
    wanted_type = exception_type.strip()
    for case in load_prior_cases():
        if wanted_type and wanted_type not in case.exception_types:
            continue
        if wanted_vendor:
            fact_vendors = [
                normalize_vendor(str(case.facts.get("invoice_vendor") or "")),
                normalize_vendor(str(case.facts.get("po_vendor") or "")),
            ]
            if wanted_vendor not in fact_vendors:
                continue
        matches.append(case)
    return matches


def _vendor_pair(evidence: APCaseEvidence) -> tuple[str, str] | None:
    if evidence.invoice is None or evidence.purchase_order is None:
        return None
    invoice_vendor = normalize_vendor(evidence.invoice.vendor)
    po_vendor = normalize_vendor(evidence.purchase_order.vendor)
    if not invoice_vendor or not po_vendor:
        return None
    return invoice_vendor, po_vendor


def operational_vendor_alias_established(evidence: APCaseEvidence) -> bool:
    """True when a prior AP turn stored this vendor pair as an alias.

    Current Kernel facts must still support the alias. Precedent cannot
    override a live blocking must_hold on a different control.
    """
    pair = _vendor_pair(evidence)
    if pair is None:
        return False
    if not evidence.vendors_are_similar:
        return False
    invoice_vendor, po_vendor = pair
    from memory.store import load_memories

    for record in load_memories():
        if record.workflow != "accounts_payable":
            continue
        if record.accounting_treatment != "vendor_alias":
            continue
        names = {
            normalize_vendor(str(item.label or ""))
            for item in record.evidence
            if item.kind in {"invoice_vendor", "po_vendor"}
        }
        if {invoice_vendor, po_vendor} <= names or names == {invoice_vendor, po_vendor}:
            return True
        details_pairs: set[str] = set()
        for item in record.evidence:
            if item.kind == "vendor_pair":
                details_pairs.add(normalize_vendor(str(item.label or "")))
        joined = f"{invoice_vendor}:{po_vendor}"
        alt = f"{po_vendor}:{invoice_vendor}"
        if joined in details_pairs or alt in details_pairs:
            return True
    return False


def vendor_alias_established(evidence: APCaseEvidence) -> bool:
    """True when stored evidence already linked these two vendor strings."""
    pair = _vendor_pair(evidence)
    if pair is None:
        return False
    invoice_vendor, po_vendor = pair
    for case in match_prior_cases(exception_type="vendor_mismatch"):
        if case.final_decision != "APPROVE":
            continue
        case_invoice = normalize_vendor(str(case.facts.get("invoice_vendor") or ""))
        case_po = normalize_vendor(str(case.facts.get("po_vendor") or ""))
        if {case_invoice, case_po} == {invoice_vendor, po_vendor}:
            return True
    return operational_vendor_alias_established(evidence)


def invoice_lookup(invoice_id: str) -> dict:
    """Catalog payload for tools.get_invoice. Does not invent a missing bill."""
    invoice = load_invoice(invoice_id)
    if invoice is None:
        return {
            "found": False,
            "error": f"Invoice {invoice_id} was not found. Do not invent invoice data.",
        }
    return {"found": True, "invoice": _dump(invoice)}


@function_tool
def get_invoice(invoice_id: str) -> dict:
    """Look up one invoice by invoice_id. Returns found=false if it does not exist."""
    return invoice_lookup(invoice_id)


@function_tool
def get_purchase_order(po_id: str) -> dict:
    """Look up a purchase order by po_id. Returns found=false if it is missing."""
    if _missing_po_id(po_id):
        return {
            "found": False,
            "error": "No purchase order id was provided. Do not invent a PO.",
        }
    purchase_order = load_purchase_order(po_id)
    if purchase_order is None:
        return {
            "found": False,
            "error": f"Purchase order {po_id} was not found. Do not invent PO data.",
        }
    return {
        "found": True,
        "purchase_order": _dump(purchase_order),
        "po_exists": True,
        "po_is_approved": purchase_order.status.lower() == "approved",
    }


@function_tool
def get_goods_receipt(po_id: str) -> dict:
    """Look up the goods receipt for a PO. Returns found=false if none exists."""
    if _missing_po_id(po_id):
        return {
            "found": False,
            "error": "No purchase order id was provided, so there is no goods receipt to load.",
        }
    receipt = load_goods_receipt(po_id)
    if receipt is None:
        return {
            "found": False,
            "error": f"No goods receipt was found for {po_id}. Do not invent a receipt.",
            "receipt_status": "missing",
        }
    return {
        "found": True,
        "goods_receipt": _dump(receipt),
        "receipt_status": receipt_status_for(po_id),
        "goods_fully_received": goods_fully_received(po_id),
    }


@function_tool
def find_duplicate_invoices(invoice_id: str) -> dict:
    """Find other invoices that share the same vendor_invoice_number."""
    invoice = load_invoice(invoice_id)
    if invoice is None:
        return {
            "found": False,
            "error": f"Invoice {invoice_id} was not found. Do not invent duplicates.",
        }
    duplicates = load_duplicate_invoices(invoice_id)
    return {
        "found": True,
        "vendor_invoice_number": invoice.vendor_invoice_number,
        "duplicate_detected": len(duplicates) > 0,
        "duplicates": [_dump(item) for item in duplicates],
    }


@function_tool
def get_case_evidence(invoice_id: str) -> dict:
    """Return Python-computed three-way match facts. Do not recalculate these numbers."""
    if load_invoice(invoice_id) is None:
        return {"found": False, "error": f"Invoice {invoice_id} was not found."}
    return {"found": True, "evidence": _dump(collect_case_evidence(invoice_id))}


@function_tool
def get_company_policies() -> dict:
    """Return the full company AP policy set. Do not invent additional policies."""
    return {"found": True, "policies": [_dump(item) for item in load_policies()]}


@function_tool
def find_relevant_policies(exception_type: str) -> dict:
    """Find policies tagged for an exception type such as vendor_mismatch or duplicate."""
    wanted = exception_type.strip()
    policies = [
        item
        for item in load_policies()
        if not wanted or wanted in item.exception_types or not item.exception_types
    ]
    if wanted:
        tagged = [item for item in load_policies() if wanted in item.exception_types]
        if tagged:
            policies = tagged + [item for item in load_policies() if not item.exception_types]
    return {
        "found": True,
        "exception_type": wanted,
        "policies": [_dump(item) for item in policies],
    }


@function_tool
def get_prior_cases(exception_type: str = "", vendor: str = "") -> dict:
    """Search historical autonomous AP cases. Prior cases are evidence, not rules."""
    matches = match_prior_cases(exception_type=exception_type, vendor=vendor)
    return {
        "found": True,
        "match_count": len(matches),
        "cases": [_dump(item) for item in matches],
    }


from memory.tools import get_decision_memories  # noqa: E402

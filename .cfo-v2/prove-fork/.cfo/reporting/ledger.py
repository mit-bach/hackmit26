"""Canonical reporting ledger. P&L totals are derived here, not by agents."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

from accrual.estimation import money
from close.dates import now_iso
from reporting.models import (
    AccountClass,
    ChartAccount,
    PeriodBalances,
    ReportingLine,
)
from tools import DATA_DIR, DataFileError

ROOT = Path(__file__).resolve().parent.parent
DATA_REPORTING = DATA_DIR / "reporting"
STATE_DIR = ROOT / "runs" / "reporting"
LEDGER_PATH = STATE_DIR / "journal.json"


def configure_data_reporting(directory: Path | None = None) -> Path:
    """Point reporting seed files (chart, payroll, actuals) at another tree."""
    global DATA_REPORTING, _accounts
    DATA_REPORTING = Path(directory) if directory is not None else (DATA_DIR / "reporting")
    _accounts = None
    return DATA_REPORTING

_lines: list[ReportingLine] | None = None
_accounts: dict[str, ChartAccount] | None = None


def configure_paths(directory: Path) -> None:
    global STATE_DIR, LEDGER_PATH, _lines
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    STATE_DIR = directory
    LEDGER_PATH = directory / "journal.json"
    _lines = None


def reset_ledger() -> None:
    global _lines
    _lines = []
    _write([])


@contextmanager
def isolated_reporting(directory: Path):
    global STATE_DIR, LEDGER_PATH, _lines
    previous = (STATE_DIR, LEDGER_PATH, _lines)
    configure_paths(directory)
    try:
        yield
    finally:
        STATE_DIR, LEDGER_PATH, _lines = previous


def _read_json(path: Path):
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise DataFileError(f"Invalid JSON in {path.name}: {exc.msg}") from exc
    return raw


def _write(rows: list[ReportingLine]) -> None:
    global _lines
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(json.dumps([item.model_dump() for item in rows], indent=2) + "\n")
    _lines = rows


def load_chart() -> list[ChartAccount]:
    raw = _read_json(DATA_REPORTING / "chart_of_accounts.json")
    if not raw:
        return _default_chart()
    return [ChartAccount.model_validate(item) for item in raw]


def _default_chart() -> list[ChartAccount]:
    return [
        ChartAccount(account_id="4000-Revenue", name="Revenue", account_class="revenue", aliases=["Revenue"]),
        ChartAccount(account_id="5000-COGS", name="Cost of Goods Sold", account_class="cogs", aliases=["COGS"]),
        ChartAccount(account_id="5100-Hosting", name="Cloud Hosting", account_class="cogs", aliases=["Hosting"]),
        ChartAccount(account_id="5200-Supplier", name="Supplier COGS", account_class="cogs"),
        ChartAccount(account_id="5300-Freight", name="Freight", account_class="cogs"),
        ChartAccount(account_id="5400-Other-COGS", name="Other COGS", account_class="cogs"),
        ChartAccount(account_id="6000-Operating", name="Operating Expenses", account_class="opex", aliases=["Operating Expenses"]),
        ChartAccount(account_id="6100-Payroll", name="Payroll", account_class="opex", aliases=["Payroll"]),
        ChartAccount(account_id="1000-Cash", name="Cash", account_class="cash", aliases=["Cash", "1000-Cash"]),
        ChartAccount(account_id="1100-AR", name="Accounts Receivable", account_class="ar", aliases=["Accounts Receivable", "Unapplied Cash"]),
        ChartAccount(account_id="2000-AP", name="Accounts Payable", account_class="ap", aliases=["Accounts Payable"]),
    ]


def chart_map() -> dict[str, ChartAccount]:
    global _accounts
    if _accounts is None:
        accounts: dict[str, ChartAccount] = {}
        for item in load_chart():
            accounts[item.account_id] = item
            accounts[item.name] = item
            for alias in item.aliases:
                accounts[alias] = item
        _accounts = accounts
    return _accounts


def classify_account(account: str) -> AccountClass:
    found = chart_map().get(account)
    if found:
        return found.account_class
    lowered = account.lower()
    if "revenue" in lowered or "sales" in lowered:
        return "revenue"
    if "cogs" in lowered or "hosting" in lowered or "freight" in lowered or "supplier" in lowered:
        return "cogs"
    if "payroll" in lowered or "opex" in lowered or "operating" in lowered or "expense" in lowered:
        return "opex"
    if "receivable" in lowered or lowered == "ar":
        return "ar"
    if "payable" in lowered or lowered == "ap":
        return "ap"
    if "cash" in lowered:
        return "cash"
    return "other"


def canonical_account(account: str) -> str:
    found = chart_map().get(account)
    return found.account_id if found else account


def load_lines() -> list[ReportingLine]:
    global _lines
    if _lines is not None:
        return list(_lines)
    raw = _read_json(LEDGER_PATH)
    if isinstance(raw, list) and raw:
        _lines = [ReportingLine.model_validate(item) for item in raw]
        return list(_lines)
    _lines = []
    return []


def lines_for(*, period: str = "", account_class: str = "", transaction_id: str = "") -> list[ReportingLine]:
    rows = load_lines()
    if period:
        rows = [item for item in rows if item.period == period]
    if account_class:
        rows = [item for item in rows if item.account_class == account_class]
    if transaction_id:
        rows = [item for item in rows if item.transaction_id == transaction_id]
    return rows


def find_by_key(idempotency_key: str) -> ReportingLine | None:
    if not idempotency_key:
        return None
    for item in load_lines():
        if item.idempotency_key == idempotency_key:
            return item
    return None


def _next_id(prefix: str, existing: list[str]) -> str:
    numbers = []
    for item in existing:
        if not item.startswith(prefix):
            continue
        suffix = item[len(prefix) :].lstrip("-")
        if suffix.isdigit():
            numbers.append(int(suffix))
    return f"{prefix}-{max(numbers, default=0) + 1:03d}"


def post_line(line: ReportingLine) -> ReportingLine:
    if line.amount <= 0:
        raise ValueError("Reporting line amount must be positive.")
    if line.idempotency_key:
        existing = find_by_key(line.idempotency_key)
        if existing:
            return existing
    rows = load_lines()
    if not line.line_id:
        line = line.model_copy(update={"line_id": _next_id("RL", [item.line_id for item in rows])})
    if not line.entry_id:
        line = line.model_copy(update={"entry_id": _next_id("JE-RPT", [item.entry_id for item in rows])})
    if not line.account_class:
        line = line.model_copy(update={"account_class": classify_account(line.account)})
    line = line.model_copy(
        update={
            "amount": money(line.amount),
            "account": canonical_account(line.account),
        }
    )
    rows.append(line)
    _write(rows)
    return line


def post_balanced_entry(
    *,
    period: str,
    posting_date: str,
    debit_account: str,
    credit_account: str,
    amount: float,
    memo: str,
    transaction_id: str,
    source_workflow: str,
    source_document_id: str = "",
    vendor: str = "",
    customer: str = "",
    category: str = "",
    evidence_refs: list[str] | None = None,
    trace_ids: list[str] | None = None,
    idempotency_key: str = "",
) -> list[ReportingLine]:
    """Post a balanced pair and keep the same transaction_id on both sides."""
    amount = money(amount)
    if amount <= 0:
        raise ValueError("Journal amount must be positive.")
    refs = list(evidence_refs or [source_document_id or transaction_id])
    traces = list(trace_ids or [])
    key = idempotency_key or f"{transaction_id}:{debit_account}:{credit_account}"
    existing = [item for item in load_lines() if item.idempotency_key.startswith(key)]
    if existing:
        return existing
    rows = load_lines()
    entry_id = _next_id(f"JE-{period.replace('-', '')}", [item.entry_id for item in rows])
    debit = ReportingLine(
        line_id=_next_id("RL", [item.line_id for item in rows]),
        entry_id=entry_id,
        transaction_id=transaction_id,
        period=period,
        posting_date=posting_date,
        account=canonical_account(debit_account),
        account_class=classify_account(debit_account),
        side="debit",
        amount=amount,
        memo=memo,
        vendor=vendor,
        customer=customer,
        category=category,
        source_workflow=source_workflow,
        source_document_id=source_document_id,
        ledger_entry_id=entry_id,
        evidence_refs=refs,
        trace_ids=traces,
        idempotency_key=f"{key}:debit",
    )
    credit = debit.model_copy(
        update={
            "line_id": _next_id("RL", [item.line_id for item in rows] + [debit.line_id]),
            "account": canonical_account(credit_account),
            "account_class": classify_account(credit_account),
            "side": "credit",
            "idempotency_key": f"{key}:credit",
        }
    )
    rows.extend([debit, credit])
    _write(rows)
    return [debit, credit]


def signed_pnl(line: ReportingLine) -> float:
    """Income-statement signed amount: revenue credits positive, expense debits positive."""
    if line.account_class == "revenue":
        return money(line.amount if line.side == "credit" else -line.amount)
    if line.account_class in {"cogs", "opex"}:
        return money(line.amount if line.side == "debit" else -line.amount)
    return 0.0


def load_balances() -> dict[str, PeriodBalances]:
    raw = _read_json(DATA_REPORTING / "balances.json")
    if isinstance(raw, dict):
        return {key: PeriodBalances.model_validate(value) for key, value in raw.items()}
    rows = {}
    if isinstance(raw, list):
        for item in raw:
            parsed = PeriodBalances.model_validate(item)
            rows[parsed.period] = parsed
    return rows


def opening_cash(as_of_date: str) -> float:
    balances = load_balances()
    period = as_of_date[:7]
    if period in balances:
        return money(balances[period].cash)
    if balances:
        latest = sorted(balances)[-1]
        return money(balances[latest].cash)
    return 0.0


def period_balance(period: str, field: str) -> float:
    balances = load_balances()
    item = balances.get(period)
    if item is None:
        return 0.0
    return money(getattr(item, field))


def ingest_close_journals() -> list[ReportingLine]:
    """Pull shared close journals into the reporting book without inventing totals."""
    from close import ledger as close_ledger

    posted: list[ReportingLine] = []
    for item in close_ledger.load_entries():
        transaction_id = str(item.get("transaction_id") or item.get("entry_id"))
        source_document_id = str(item.get("source_document_id") or "")
        posted.extend(
            post_balanced_entry(
                period=str(item.get("period") or ""),
                posting_date=str(item.get("created_at") or item.get("period") or "")[:10]
                or f"{item.get('period')}-01",
                debit_account=str(item.get("debit_account")),
                credit_account=str(item.get("credit_account")),
                amount=float(item.get("debit") or 0),
                memo=str(item.get("memo") or ""),
                transaction_id=transaction_id,
                source_workflow="close",
                source_document_id=source_document_id,
                evidence_refs=list(item.get("evidence_refs") or [item.get("entry_id")]),
                idempotency_key=f"close:{item.get('idempotency_key') or item.get('entry_id')}",
            )
        )
    return posted


def ingest_ar_journals() -> list[ReportingLine]:
    from ar.store import journals

    posted: list[ReportingLine] = []
    for item in journals():
        posted.extend(
            post_balanced_entry(
                period=item.period,
                posting_date=(item.created_at or f"{item.period}-01")[:10],
                debit_account=item.debit.account,
                credit_account=item.credit.account,
                amount=item.debit.amount,
                memo=item.memo,
                transaction_id=item.related_payment_id or item.entry_id,
                source_workflow="ar",
                source_document_id=item.related_invoice_ids[0] if item.related_invoice_ids else item.entry_id,
                customer=item.counterparty,
                evidence_refs=[item.entry_id, *item.related_invoice_ids],
                idempotency_key=f"ar:{item.entry_id}",
            )
        )
    return posted


def remember_external_line(
    *,
    transaction_id: str,
    period: str,
    posting_date: str,
    account: str,
    side: str,
    amount: float,
    source_workflow: str,
    source_document_id: str = "",
    memo: str = "",
    vendor: str = "",
    customer: str = "",
    category: str = "",
    product: str = "",
    quantity: float | None = None,
    rate: float | None = None,
    ledger_entry_id: str = "",
    trace_ids: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    idempotency_key: str = "",
) -> ReportingLine:
    return post_line(
        ReportingLine(
            line_id="",
            entry_id=ledger_entry_id,
            transaction_id=transaction_id,
            period=period,
            posting_date=posting_date,
            account=account,
            account_class=classify_account(account),
            side=side,  # type: ignore[arg-type]
            amount=amount,
            memo=memo,
            vendor=vendor,
            customer=customer,
            product=product,
            category=category,
            quantity=quantity,
            rate=rate,
            source_workflow=source_workflow,
            source_document_id=source_document_id,
            ledger_entry_id=ledger_entry_id,
            trace_ids=list(trace_ids or []),
            evidence_refs=list(evidence_refs or []),
            idempotency_key=idempotency_key or f"{source_workflow}:{transaction_id}:{account}:{side}",
        )
    )


def now() -> str:
    return now_iso()

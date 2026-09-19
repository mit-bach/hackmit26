import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def isolated_approved_pool(tmp_path, monkeypatch):
    path = tmp_path / "approved_pool.json"
    path.write_text("[]\n")
    monkeypatch.setattr("scheduling.pool.POOL_PATH", path)
    return path


@pytest.fixture(autouse=True)
def isolated_ingestion_overlay():
    from invoice_ingestion.adapter import reset_ingested_invoices
    from invoice_ingestion.store import clear_ingestion_cache

    reset_ingested_invoices()
    clear_ingestion_cache()
    yield
    reset_ingested_invoices()
    clear_ingestion_cache()


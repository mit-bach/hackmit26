"""World Bot Grants, inbox catalog ops, and mailbox roundtrip."""

from __future__ import annotations

import json
from pathlib import Path

from compiler.compile_lib import compile_catalog

REPO = Path(__file__).resolve().parents[3]
KERNEL = REPO / ".cfo"
SLUG_MAP = REPO / ".cfo-v2" / "office" / "computer" / "cfo" / "slug-map.json"


def test_compiler_includes_inbox_send_and_world_grants(tmp_path) -> None:
    out = tmp_path / "cfo"
    out.mkdir()
    overrides = REPO / ".cfo-v2" / "office" / "computer" / "cfo" / "catalog.overrides.json"
    (out / "catalog.overrides.json").write_text(overrides.read_text(encoding="utf-8"), encoding="utf-8")
    result = compile_catalog(kernel=KERNEL, out_dir=out, phase="operational")
    catalog_ids = {row["id"] for row in result.catalog["ops"]}
    assert "inbox.tools.send_inbox_message" in catalog_ids
    assert "inbox.tools.send_office_outbound" in catalog_ids
    assert "inbox.tools.reply_in_thread" in catalog_ids
    assert "inbox.tools.list_world_personas" in catalog_ids
    send = next(row for row in result.catalog["ops"] if row["id"] == "inbox.tools.send_inbox_message")
    assert send["mutability"] == "write-local"
    assert send["ownerPrefixes"] == ["runs/inbox/"]
    assert send["sodClass"] == "inbox"

    names = result.grants["byDisplayName"]
    world = names["Counterparty Message Agent"]["ops"]
    email_inbox = names["Finance Inbox Agent"]["ops"]
    email_invoice = names["Email Invoice Agent"]["ops"]
    collect = names["Collections Agent"]["ops"]
    assert "inbox.tools.send_inbox_message" in world
    assert "inbox.tools.reply_in_thread" in world
    assert "inbox.tools.list_world_personas" in world
    assert "inbox.tools.dispatch_inbox_action" not in world
    assert "inbox.tools.send_office_outbound" not in world
    assert "tools.get_invoice" not in world
    assert "accrual.tools.create_accrual" not in world
    assert "scheduling.tools.get_payment_candidates" not in world
    assert "inbox.tools.send_inbox_message" not in email_inbox
    assert "inbox.tools.compose_counterparty_message" not in email_inbox
    assert "inbox.tools.send_office_outbound" in email_inbox
    assert "inbox.tools.dispatch_inbox_action" in email_inbox
    assert "inbox.tools.send_inbox_message" not in email_invoice
    assert "inbox.tools.send_office_outbound" in collect
    assert "inbox.tools.send_inbox_message" not in collect

    slug_map = json.loads(SLUG_MAP.read_text(encoding="utf-8"))
    assert slug_map["bots"]["world"]["defaultProfile"] == "vendor"
    assert slug_map["bots"]["world"]["profiles"]["vendor"] == "Counterparty Message Agent"
    assert slug_map["bots"]["email"]["profiles"]["triage"] == "Finance Inbox Agent"

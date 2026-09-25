"""CFO Kernel sidecar. Not a Bot. Does not bind HARNESS_BOT. Does not drain inboxes."""

from __future__ import annotations

LOCK_OP = "close.month_end.run_month_end"
TEST_PACKET_OP = "close.orchestrator.run_cfo_close"
HOST_SLUG = "_host"
HOST_BOT_ID = "kernel-host"
HOST_PROFILE = "sidecar"

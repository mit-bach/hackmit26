"""Grant re-check. Sidecar repeats the Pi filter. Union is not a Profile."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from cfo_kernel import HOST_BOT_ID, HOST_PROFILE, HOST_SLUG
from cfo_kernel.paths import Computer


class GrantConfigError(ValueError):
    """Slug map or grants file is not a valid Grant source."""


@dataclass(frozen=True)
class CatalogOp:
    id: str
    python: str
    export_name: str
    mutability: str
    eval_only: bool
    sod_class: str


@dataclass(frozen=True)
class GrantDecision:
    allowed: bool
    code: str
    message: str
    display_name: str
    op: CatalogOp | None


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    return raw if isinstance(raw, dict) else {}


def load_catalog(computer: Computer) -> dict[str, CatalogOp]:
    payload = load_json(computer.catalog_path)
    ops: dict[str, CatalogOp] = {}
    for row in payload.get("ops") or []:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        op_id = str(row["id"])
        ops[op_id] = CatalogOp(
            id=op_id,
            python=str(row.get("python") or ""),
            export_name=str(row.get("exportName") or op_id.split(".")[-1]),
            mutability=str(row.get("mutability") or "read"),
            eval_only=bool(row.get("evalOnly")),
            sod_class=str(row.get("sodClass") or ""),
        )
        export = ops[op_id].export_name
        if export and export not in ops:
            ops[export] = ops[op_id]
    return ops


def _grants_by_display_name(payload: dict) -> dict:
    if isinstance(payload.get("byDisplayName"), dict):
        return payload["byDisplayName"]
    if isinstance(payload.get("agents"), dict):
        return payload["agents"]
    return {}


def resolve_display_name(computer: Computer, slug: str, profile: str) -> tuple[str, str]:
    """Return (display_name, error_code). error_code empty means resolved."""
    if slug == HOST_SLUG:
        return HOST_PROFILE, ""
    payload = load_json(computer.slug_map_path)
    bots = payload.get("bots")
    if not isinstance(bots, dict):
        return "", "forbidden"
    bot = bots.get(slug)
    if bot is None:
        return "", "forbidden"
    if isinstance(bot, list):
        raise GrantConfigError("Slug map union is not a valid Profile shape.")
    if not isinstance(bot, dict):
        return "", "forbidden"
    profiles = bot.get("profiles")
    if isinstance(profiles, list):
        raise GrantConfigError("Slug map union is not a valid Profile shape.")
    if not isinstance(profiles, dict):
        return "", "forbidden"
    wanted = profile or str(bot.get("defaultProfile") or "")
    if wanted not in profiles:
        return "", "forbidden"
    display = profiles[wanted]
    if display is None:
        return "", "forbidden"
    return str(display), ""


# Belt-and-suspenders SoD. Compiler Grants are the SoT. These denials
# still fire if a constructor list ever unions the wrong ops onto a slug.
AP_PREPARE_ACCRUAL_DENY = frozenset({"accrual.tools.create_accrual", "accrual.tools.reconcile_accrual_with_invoice"})
CTL_PAY_RECORD_DENY = frozenset(
    {
        "tools.get_invoice",
        "tools.get_purchase_order",
        "tools.get_goods_receipt",
        "tools.find_duplicate_invoices",
    }
)
AUDIT_GROUND_TRUTH = "audit.tools.get_audit_ground_truth"


def sod_forbid(*, slug: str, profile: str, op_id: str, operational: bool) -> str | None:
    if slug == "ap" and profile == "prepare" and op_id in AP_PREPARE_ACCRUAL_DENY:
        return f"ap/prepare cannot call {op_id}"
    if slug == "ctl-pay" and op_id in CTL_PAY_RECORD_DENY:
        return f"ctl-pay cannot call AP RECORD_TOOLS ({op_id})"
    if slug == "audit" and operational and op_id == AUDIT_GROUND_TRUTH:
        return f"audit operational cannot call {op_id}"
    return None


def granted_ops(computer: Computer, display_name: str) -> set[str]:
    if not display_name:
        return set()
    grants = _grants_by_display_name(load_json(computer.grants_path))
    row = grants.get(display_name)
    if not isinstance(row, dict):
        return set()
    ops = row.get("ops") or []
    if not isinstance(ops, list):
        return set()
    return {str(item) for item in ops}


def authorize(
    computer: Computer,
    *,
    op: str,
    slug: str,
    profile: str,
    bot_id: str,
    catalog: dict[str, CatalogOp],
    operational: bool,
) -> GrantDecision:
    if slug == HOST_SLUG:
        if bot_id != HOST_BOT_ID or profile != HOST_PROFILE:
            return GrantDecision(False, "forbidden", "Host RPC identity mismatch.", "", None)
        if not op.startswith("kernel."):
            return GrantDecision(
                False, "forbidden", "Host identity may not call Catalog ops.", "", None
            )
        return GrantDecision(True, "", "host", HOST_PROFILE, None)

    if op.startswith("kernel."):
        return GrantDecision(
            False, "forbidden", "kernel.* ops are host-only. Sidecar is not a Bot.", "", None
        )

    try:
        display, err = resolve_display_name(computer, slug, profile)
    except GrantConfigError as exc:
        return GrantDecision(False, "forbidden", str(exc), "", None)
    if err:
        return GrantDecision(
            False,
            "forbidden",
            f"No Connectors for slug={slug!r} profile={profile!r}.",
            display,
            None,
        )

    meta = catalog.get(op)
    if meta is None:
        return GrantDecision(
            False, "unknown_op", f"Op {op!r} is not in the Catalog.", display, None
        )

    allowed = granted_ops(computer, display)
    if meta.id not in allowed and op not in allowed and meta.export_name not in allowed:
        return GrantDecision(
            False,
            "forbidden",
            f"Op {meta.id} is not granted to {display!r} ({slug}/{profile}).",
            display,
            meta,
        )
    sod = sod_forbid(slug=slug, profile=profile, op_id=meta.id, operational=operational)
    if sod:
        return GrantDecision(False, "forbidden", sod, display, meta)
    if meta.eval_only and operational:
        return GrantDecision(
            False,
            "forbidden",
            f"Op {meta.id} is evalOnly; operational phase cannot call it.",
            display,
            meta,
        )
    return GrantDecision(True, "", "ok", display, meta)

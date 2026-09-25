"""One RPC protocol: HTTP JSON or stdio newline JSON."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.isolation import AnswerKeyIsolationError, operational_phase_guard, evaluation_phase

from cfo_kernel import LOCK_OP, TEST_PACKET_OP
from cfo_kernel.grants import authorize, load_catalog
from cfo_kernel.host_ops import HOST_DISPATCH, call_host, host_mutability
from cfo_kernel import idempotency
from cfo_kernel.invoke import InvokeError, call_op
from cfo_kernel.paths import Computer, current, eval_phase
from cfo_kernel.gates import assert_kernel_gate
from cfo_kernel.validators import GateFailed, after_mutate

WRITE_MUTABILITY = frozenset({"write-local", "side-effect-external"})


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _trace_id() -> str:
    return "k_" + uuid.uuid4().hex[:12]


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value


def _ok(result: Any, trace_id: str) -> dict:
    return {"ok": True, "result": to_jsonable(result), "error": None, "traceId": trace_id}


def _err(code: str, message: str, trace_id: str, result: Any = None) -> dict:
    return {
        "ok": False,
        "result": to_jsonable(result) if result is not None else None,
        "error": {"code": code, "message": message},
        "traceId": trace_id,
    }


def _append_log(computer: Computer, row: dict) -> None:
    computer.log_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(row, sort_keys=True, default=str)
    with computer.log_path.open("a") as handle:
        handle.write(line + "\n")


def _log(
    computer: Computer,
    *,
    trace_id: str,
    op: str,
    bot_id: str,
    slug: str,
    profile: str,
    handle_id: str,
    ok: bool,
    error_code: str | None,
) -> None:
    _append_log(
        computer,
        {
            "ts": _now(),
            "traceId": trace_id,
            "op": op,
            "botId": bot_id,
            "slug": slug,
            "profile": profile,
            "handleId": handle_id,
            "ok": ok,
            "error": error_code,
        },
    )


def handle_rpc(payload: dict, computer: Computer | None = None) -> dict:
    """Serve one Kernel RPC. Does not drain inboxes. Does not bind HARNESS_BOT."""
    bound = computer or current()
    trace_id = _trace_id()
    op = str(payload.get("op") or "")
    bot_id = str(payload.get("botId") or "")
    slug = str(payload.get("slug") or "")
    profile = str(payload.get("profile") or "")
    handle_id = str(payload.get("handleId") or "")
    args = payload.get("args")
    if args is None:
        args = {}
    if not isinstance(args, dict):
        response = _err("invalid_args", "args must be a JSON object", trace_id)
        _log(
            bound,
            trace_id=trace_id,
            op=op,
            bot_id=bot_id,
            slug=slug,
            profile=profile,
            handle_id=handle_id,
            ok=False,
            error_code="invalid_args",
        )
        return response
    if not op:
        response = _err("invalid_args", "op is required", trace_id)
        _log(
            bound,
            trace_id=trace_id,
            op=op,
            bot_id=bot_id,
            slug=slug,
            profile=profile,
            handle_id=handle_id,
            ok=False,
            error_code="invalid_args",
        )
        return response

    operational = eval_phase() == "operational"
    phase_cm = operational_phase_guard if operational else evaluation_phase
    with phase_cm():
        return _handle_in_phase(
            bound,
            trace_id=trace_id,
            op=op,
            bot_id=bot_id,
            slug=slug,
            profile=profile,
            handle_id=handle_id,
            args=args,
            idempotency_key=payload.get("idempotencyKey"),
            operational=operational,
        )


def _handle_in_phase(
    computer: Computer,
    *,
    trace_id: str,
    op: str,
    bot_id: str,
    slug: str,
    profile: str,
    handle_id: str,
    args: dict,
    idempotency_key: Any,
    operational: bool,
) -> dict:
    catalog = load_catalog(computer)
    decision = authorize(
        computer,
        op=op,
        slug=slug,
        profile=profile,
        bot_id=bot_id,
        catalog=catalog,
        operational=operational,
    )
    if not decision.allowed:
        response = _err(decision.code, decision.message, trace_id)
        _log(
            computer,
            trace_id=trace_id,
            op=op,
            bot_id=bot_id,
            slug=slug,
            profile=profile,
            handle_id=handle_id,
            ok=False,
            error_code=decision.code,
        )
        return response

    mutability = "read"
    if op in HOST_DISPATCH:
        mutability = host_mutability(op)
    elif decision.op is not None:
        mutability = decision.op.mutability

    call_args = dict(args)
    if op.startswith("cash_recon.tools.") and "case_id" in call_args:
        case_id = str(call_args.pop("case_id") or "")
        if case_id:
            from cash_recon.tools import load_case_into_memory

            if not load_case_into_memory(case_id):
                response = _err("not_found", f"Unknown cash case {case_id}", trace_id)
                _log(
                    computer,
                    trace_id=trace_id,
                    op=op,
                    bot_id=bot_id,
                    slug=slug,
                    profile=profile,
                    handle_id=handle_id,
                    ok=False,
                    error_code="not_found",
                )
                return response

    if mutability in WRITE_MUTABILITY:
        key = str(idempotency_key or "")
        if not key:
            response = _err(
                "idempotency_required",
                f"Mutating op {op} requires idempotencyKey",
                trace_id,
            )
            _log(
                computer,
                trace_id=trace_id,
                op=op,
                bot_id=bot_id,
                slug=slug,
                profile=profile,
                handle_id=handle_id,
                ok=False,
                error_code="idempotency_required",
            )
            return response
        status, stored = idempotency.claim(computer, key=key, op=op, args=args)
        if status == "mismatch":
            response = _err(
                "idempotency_mismatch",
                "Same idempotency key with a different body",
                trace_id,
            )
            _log(
                computer,
                trace_id=trace_id,
                op=op,
                bot_id=bot_id,
                slug=slug,
                profile=profile,
                handle_id=handle_id,
                ok=False,
                error_code="idempotency_mismatch",
            )
            return response
        if status == "replay" and stored is not None:
            replayed = stored.get("response")
            if isinstance(replayed, dict):
                _log(
                    computer,
                    trace_id=trace_id,
                    op=op,
                    bot_id=bot_id,
                    slug=slug,
                    profile=profile,
                    handle_id=handle_id,
                    ok=bool(replayed.get("ok")),
                    error_code=None,
                )
                return replayed
        if status == "in_progress":
            response = _err(
                "idempotency_in_progress",
                "Idempotency key is already claimed",
                trace_id,
            )
            _log(
                computer,
                trace_id=trace_id,
                op=op,
                bot_id=bot_id,
                slug=slug,
                profile=profile,
                handle_id=handle_id,
                ok=False,
                error_code="idempotency_in_progress",
            )
            return response
    else:
        key = ""

    try:
        if op in HOST_DISPATCH:
            raw = call_host(op, call_args)
        elif decision.op is None:
            raise InvokeError(f"No Catalog metadata for {op}")
        else:
            if mutability in WRITE_MUTABILITY:
                assert_kernel_gate(op, call_args)
            if op == TEST_PACKET_OP:
                # Test packet. Not a second period lock. Documented in PROOF.md.
                raw = call_op(decision.op, call_args)
            elif op == LOCK_OP:
                raw = call_op(decision.op, call_args)
            else:
                raw = call_op(decision.op, call_args)
        raw = after_mutate(op, raw)
        response = _ok(raw, trace_id)
    except AnswerKeyIsolationError as exc:
        response = _err("eval_isolation", str(exc), trace_id)
    except GateFailed as exc:
        response = _err("blocked", str(exc), trace_id)
    except InvokeError as exc:
        response = _err("invalid_args", str(exc), trace_id)
    except Exception as exc:
        response = _err("kernel_error", f"{type(exc).__name__}: {exc}", trace_id)

    if key:
        idempotency.complete(computer, key=key, op=op, args=args, response=response)
    _log(
        computer,
        trace_id=trace_id,
        op=op,
        bot_id=bot_id,
        slug=slug,
        profile=profile,
        handle_id=handle_id,
        ok=bool(response.get("ok")),
        error_code=(response.get("error") or {}).get("code") if response.get("error") else None,
    )
    return response

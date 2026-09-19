from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from models import PaymentPlan, ScheduleTrace
from scheduling.agent import (
    payment_audit_agent,
    run_payment_audit,
    run_scheduler,
    scheduler_agent,
)
from scheduling.cash import (
    apply_cash_and_policy_net,
    compute_metrics,
    load_cash_position,
    payment_candidate,
    spendable_cash,
)
from scheduling.pool import load_pool
from skills.loader import usage_from_agent

RUNS_DIR = Path(__file__).resolve().parent.parent / "runs"


def _dump(model) -> str:
    return json.dumps(model.model_dump(mode="json"), indent=2)


def candidates_from_pool():
    rows = load_pool()
    candidates = []
    for row in rows:
        item = payment_candidate(row["invoice_id"], approval_source=row.get("approval_source", "ap_workflow"))
        if item is not None:
            candidates.append(item)
    return candidates


def run_schedule_workflow() -> ScheduleTrace:
    cash = load_cash_position()
    candidates = candidates_from_pool()
    if not candidates:
        raise ValueError(
            "Approved invoice pool is empty. Run AP validation on invoices first, "
            "or seed a demo pool with: python main.py schedule --seed-demo"
        )

    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"Payment schedule as of {cash.as_of_date}", flush=True)
    print(f"Spendable cash: ${spendable_cash(cash):,.2f}", flush=True)
    print(f"Approved pool: {len(candidates)} invoices", flush=True)
    print(flush=True)

    proposed: PaymentPlan = run_scheduler(
        (
            "Build this week's payment plan.\n\n"
            f"Cash position:\n{_dump(cash)}\n\n"
            f"Spendable cash (Python): {spendable_cash(cash)}\n\n"
            "Candidates (Python facts):\n"
            f"{json.dumps([item.model_dump() for item in candidates], indent=2)}\n\n"
            "Return a PaymentPlan. Only use invoice IDs from the candidate list."
        )
    )

    proposed_ids = [row.invoice_id for row in proposed.pay_this_week]
    plan = apply_cash_and_policy_net(candidates, proposed_ids, cash)
    plan = plan.model_copy(
        update={
            "reasons": list(proposed.reasons) + plan.reasons,
            "confidence": proposed.confidence,
        }
    )
    metrics = compute_metrics(candidates, plan, cash)

    audit = run_payment_audit(
        (
            "Audit this payment plan against treasury policy.\n\n"
            f"Cash:\n{_dump(cash)}\n\n"
            f"Plan:\n{_dump(plan)}\n\n"
            f"Metrics:\n{_dump(metrics)}"
        )
    )
    if not plan.reserve_ok:
        audit = audit.model_copy(
            update={
                "passed": False,
                "policy_violations": list(
                    dict.fromkeys(audit.policy_violations + ["P-013 minimum cash reserve"])
                ),
            }
        )

    trace = ScheduleTrace(
        as_of_date=cash.as_of_date,
        started_at=started_at,
        cash=cash,
        spendable_cash=spendable_cash(cash),
        candidates=candidates,
        plan=plan,
        metrics=metrics,
        audit=audit,
        agents=[
            usage_from_agent(scheduler_agent),
            usage_from_agent(payment_audit_agent),
        ],
    )
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RUNS_DIR / f"schedule-{stamp}.json"
    trace.trace_path = str(path)
    path.write_text(trace.model_dump_json(indent=2) + "\n")
    return trace

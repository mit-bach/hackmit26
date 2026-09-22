"""CLI for the independent audit workflow."""

from __future__ import annotations

import os


def _period(argv: list[str], default: str = "2026-09") -> str:
    if "--period" in argv:
        index = argv.index("--period")
        if index + 1 >= len(argv):
            raise ValueError("Usage: python main.py audit --period 2026-09")
        return argv[index + 1]
    rest = [item for item in argv if not item.startswith("--")]
    return rest[0] if rest else default


def _seed(argv: list[str], default: int = 26) -> int:
    if "--seed" in argv:
        index = argv.index("--seed")
        if index + 1 >= len(argv):
            raise ValueError("Usage: python main.py audit --seed 26")
        return int(argv[index + 1])
    return default


def run_audit_cli(argv: list[str]) -> int:
    try:
        period = _period(argv)
        seed = _seed(argv)
    except ValueError as exc:
        print(exc)
        return 1
    use_agent = "--llm" in argv
    if use_agent and not os.environ.get("OPENAI_API_KEY"):
        print(
            "OPENAI_API_KEY is not set.\n"
            "Copy .env.example to .env and add your key, or omit --llm for the deterministic auditor."
        )
        return 1
    from audit.report import format_audit_report
    from audit.workflow import run_audit

    run = run_audit(period, seed=seed, use_agent=use_agent)
    print(format_audit_report(run))
    if run.trace_path:
        print(f"\nTrace saved to {run.trace_path}")
    return 0


def run_audit_demo_cli(argv: list[str]) -> int:
    try:
        period = _period(argv)
        seed = _seed(argv)
    except ValueError as exc:
        print(exc)
        return 1
    if "--adversarial" in argv:
        from audit.demo import format_adversarial_demo, run_adversarial_demo

        print(format_adversarial_demo(run_adversarial_demo(period, seed=seed)))
        return 0
    from audit.demo import format_demo, run_audit_demo

    print(format_demo(run_audit_demo(period, seed=seed)))
    return 0


def run_audit_trace_cli(argv: list[str]) -> int:
    try:
        period = _period(argv)
        seed = _seed(argv)
    except ValueError as exc:
        print(exc)
        return 1
    from audit.dataset import clean_dataset, load_dataset
    from audit.trace import evidence_chain, format_chain
    from audit.workflow import run_audit

    dataset = load_dataset(period) if "--planted" in argv else clean_dataset(period)
    run = run_audit(period, seed=seed, use_agent=False, persist=False, dataset=dataset)
    print(format_chain(evidence_chain(dataset, run)))
    return 0


def run_eval_audit_cli(argv: list[str]) -> int:
    try:
        period = _period(argv)
        seed = _seed(argv)
    except ValueError as exc:
        print(exc)
        return 1
    from audit.demo import run_audit_demo
    from audit.eval import format_metrics

    payload = run_audit_demo(period, seed=seed)
    print(format_metrics(payload["metrics"]))
    return 0

"""Human-readable discrepancy stress-test report."""

from __future__ import annotations

from discrepancy.models import DiscrepancyBenchmark, FixRecord


def format_discrepancy_report(
    result: DiscrepancyBenchmark,
    *,
    initial: DiscrepancyBenchmark | None = None,
    fixes: list[FixRecord] | None = None,
) -> str:
    lines = [
        "DISCREPANCY STRESS TEST",
        f"Dataset: {result.data_root} / seed {result.seed} / {result.period}",
        f"Phase: {result.phase}",
        "",
    ]
    for fn in result.function_results:
        lines.append(fn.domain.upper().replace("_", " "))
        lines.append(f"{fn.passed} / {fn.total} detected")
        failed = [item for item in fn.cases if not item.passed]
        if failed:
            lines.append("FAILED:")
            for item in failed:
                lines.append(f"{item.discrepancy_id}")
                lines.append(f"Expected: {item.diagnostics.get('expected') or item.reason}")
                lines.append(f"Actual: {item.actual_status}")
                lines.append(f"Agent: {item.agent}")
                lines.append(f"  {item.reason}")
        lines.append("")
    if fixes:
        lines.append("FIXES APPLIED:")
        for item in fixes:
            lines.append(f"{item.discrepancy_id}: {item.behavior_changed}")
            lines.append(f"  files: {', '.join(item.files_changed)}")
            lines.append(f"  test: {item.regression_test}")
        lines.append("")
    if initial:
        lines.append(f"INITIAL RESULT")
        lines.append(f"{initial.passed} / {initial.total} passed")
        lines.append("AFTER FIXES")
        lines.append(f"{result.passed} / {result.total} passed")
    else:
        lines.append(f"{result.phase.upper()} RESULT")
        lines.append(f"{result.passed} / {result.total} passed")
    lines.append(f"Recall: {result.discrepancy_recall:.2%}  Unsafe auto-resolution: {result.unsafe_auto_resolution_rate:.2%}")
    return "\n".join(lines)

"""Human-readable CFO benchmark summary."""

from __future__ import annotations

from evaluation.models import BenchmarkResult


def format_summary(result: BenchmarkResult) -> str:
    lines = [
        "CFO AGENT BENCHMARK",
        f"Dataset: {result.data_root} / seed {result.seed} / {result.period}",
        f"Run: {result.run_id}",
        "",
    ]
    for fn in result.function_results:
        title = fn.domain.upper().replace("_", " ")
        lines.append(title)
        lines.append(f"Cases: {fn.cases_total}")
        lines.append(f"Pass: {fn.cases_passed}")
        lines.append(f"Partial: {fn.cases_partial}")
        lines.append(f"Fail: {fn.cases_failed}")
        if fn.cases_error:
            lines.append(f"Errors: {fn.cases_error}")
        if fn.workflow_error:
            lines.append(f"Workflow crash: {fn.workflow_error}")
        lines.append(f"Score: {fn.score:.2%}")
        if fn.metrics:
            for key, value in fn.metrics.items():
                lines.append(f"  {key}: {value}")
        failed = [item for item in fn.case_results if item.status in {"FAIL", "ERROR"}]
        if failed:
            lines.append("Failures:")
            for item in failed:
                lines.append(
                    f"  {item.scenario_id} {item.case_id}: expected {item.expected!r} "
                    f"actual {item.actual!r} error={item.error_type or '-'}"
                )
                if item.reason:
                    lines.append(f"    {item.reason}")
        lines.append("")

    overall = result.overall_metrics
    lines.append("OVERALL")
    lines.append(f"Cases: {overall.cases_total}  Pass: {overall.cases_passed}  Partial: {overall.cases_partial}  Fail: {overall.cases_failed}")
    lines.append(f"Overall score: {overall.overall_score:.2%}")
    lines.append(f"Cross-function consistency: {overall.cross_function_consistency_score:.2%}")
    hr = overall.human_review
    lines.append(
        f"Human review precision/recall: {hr.human_review_precision:.2%} / {hr.human_review_recall:.2%}"
    )
    lines.append(
        f"Unsafe auto-resolution rate: {hr.unsafe_auto_resolution_rate:.2%}  "
        f"Needless escalation rate: {hr.unnecessary_escalation_rate:.2%}"
    )
    if overall.error_counts:
        lines.append("Top failure categories:")
        for key, count in sorted(overall.error_counts.items(), key=lambda item: -item[1]):
            lines.append(f"  {key}: {count}")
    if result.end_to_end_results:
        lines.append("")
        lines.append("End-to-end storylines:")
        for story in result.end_to_end_results:
            lines.append(f"  {story.storyline_id}: {story.status} ({story.score:.2%})")
            for note in story.contradictions:
                lines.append(f"    contradiction: {note}")
    if result.regressions:
        lines.append("")
        lines.append("Baseline comparison:")
        lines.append(f"{'metric':<32} {'baseline':>10} {'current':>10} {'delta':>10}")
        for row in result.regressions:
            flag = " REGRESSION" if row.regression else ""
            lines.append(f"{row.metric:<32} {row.baseline:10.4f} {row.current:10.4f} {row.delta:10.4f}{flag}")
    return "\n".join(lines)

"""Run existing CFO workflows against generated operational data, then score."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from evaluation.comparison import compare_metrics, error_case
from evaluation.context import operational_dataset
from evaluation.evaluators import (
    run_ap,
    run_ar,
    run_audit_eval,
    run_cash,
    run_close,
    run_end_to_end,
    run_forecast,
    run_reporting,
)
from evaluation.isolation import evaluation_phase
from evaluation.keys import load_audit_ground_truth, load_cash_ground_truth, load_expected_results, load_manifest
from evaluation.models import BenchmarkResult, FunctionEvaluationResult
from evaluation.scoring import overall_metrics, summarize_function

DOMAINS = ("ap", "ar", "cash", "close", "audit", "reporting", "forecasting")
ALL_ORDER = ("ap", "ar", "cash", "close", "audit", "reporting", "forecasting")


class CFOEvaluationRunner:
    def run(
        self,
        *,
        data_root: Path,
        seed: int = 42,
        period: str = "2026-09",
        domains: list[str] | None = None,
        output: Path | None = None,
        compare_to: Path | None = None,
        live: bool = False,
    ) -> BenchmarkResult:
        data_root = Path(data_root)
        selected = list(domains or ALL_ORDER)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"EVAL-{period}-{seed}-{stamp}"
        dest = Path(output) if output else Path("runs") / "evaluation" / run_id
        dest.mkdir(parents=True, exist_ok=True)
        raw_dir = dest / "raw_outputs"
        raw_dir.mkdir(parents=True, exist_ok=True)

        manifest = load_manifest(data_root)
        raw_outputs: dict = {}
        function_results: list[FunctionEvaluationResult] = []

        runners = {
            "ap": lambda: run_ap(None),
            "ar": lambda: run_ar(None),
            "cash": lambda: run_cash(period, None),
            "close": lambda: run_close(period, None),
            "audit": lambda: run_audit_eval(period, [], seed=seed),
            "reporting": lambda: run_reporting(period, None),
            "forecasting": lambda: run_forecast(period, None),
        }
        raw_key = {"forecasting": "forecast"}
        with operational_dataset(data_root, dest / "state"):
            for domain in selected:
                if domain not in runners:
                    continue
                try:
                    result, raw = runners[domain]()
                except Exception as exc:
                    case = error_case(
                        case_id=f"{domain.upper()}-WORKFLOW",
                        domain=domain,
                        scenario_id=f"SCN-{domain.upper()}-WORKFLOW",
                        reason=str(exc),
                    )
                    result = summarize_function(domain, [case])
                    result.workflow_error = str(exc)
                    raw = {"error": str(exc)}
                function_results.append(result)
                raw_outputs[raw_key.get(domain, domain)] = raw

        with evaluation_phase():
            expected = load_expected_results(data_root)
            cash_truth = load_cash_ground_truth(data_root)
            audit_truth = load_audit_ground_truth(data_root)
            if "cash" in selected and cash_truth.get("labels"):
                raw_outputs.setdefault("cash", {})["ground_truth_labels"] = cash_truth.get("labels")
            if "audit" in selected:
                raw_outputs.setdefault("audit", {})["planted"] = audit_truth.get("planted_exceptions")

            e2e_fn = None
            stories = []
            if set(selected) >= {"ap", "ar", "cash"} or "end_to_end" in selected or domains is None:
                e2e_fn, stories = run_end_to_end(raw_outputs)
                function_results.append(e2e_fn)

            overall = overall_metrics(function_results, stories)
            regressions = []
            if compare_to:
                baseline = json.loads(Path(compare_to).read_text())
                current = {item.domain: item.score for item in function_results}
                current["overall_score"] = overall.overall_score
                before = {row["domain"]: row["score"] for row in baseline.get("function_results", [])}
                before["overall_score"] = baseline.get("overall_metrics", {}).get("overall_score", 0)
                regressions = compare_metrics(before, current)

            result = BenchmarkResult(
                run_id=run_id,
                seed=seed,
                period=period,
                data_root=str(data_root),
                dataset_manifest=manifest,
                function_results=function_results,
                end_to_end_results=stories,
                overall_metrics=overall,
                regressions=regressions,
                generated_at=stamp,
                live=live,
                output_dir=str(dest),
            )
            _ = expected
            self._persist(dest, result, raw_outputs)
            return result

    def _persist(self, dest: Path, result: BenchmarkResult, raw_outputs: dict) -> None:
        from evaluation.report import format_summary

        (dest / "benchmark.json").write_text(result.model_dump_json(indent=2) + "\n")
        cases = [item.model_dump(mode="json") for fn in result.function_results for item in fn.case_results]
        (dest / "cases.json").write_text(json.dumps(cases, indent=2) + "\n")
        failures = [item for item in cases if item.get("status") in {"FAIL", "ERROR", "PARTIAL"}]
        (dest / "failures.json").write_text(json.dumps(failures, indent=2) + "\n")
        (dest / "summary.md").write_text(format_summary(result) + "\n")
        (dest / "raw_outputs" / "workflows.json").write_text(json.dumps(raw_outputs, indent=2, default=str) + "\n")


def run_benchmark(**kwargs) -> BenchmarkResult:
    return CFOEvaluationRunner().run(**kwargs)

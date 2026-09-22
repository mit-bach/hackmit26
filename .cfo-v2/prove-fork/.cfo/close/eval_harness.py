"""Clean-room month-end eval. Never reads or writes persistent demo registers."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from close.eval_cases import (
    CANONICAL_CASES,
    EVAL_DATA,
    EvalCase,
    blocked_close_gate,
    cash_difference_packet,
    duplicate_register_asset,
    insurance_prepaid,
    server_candidate,
)


def _dump(model) -> dict:
    return model.model_dump(mode="json")


def _fingerprint(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode()
    return sha256(encoded).hexdigest()


def snapshot_runtime_paths() -> dict:
    from ar.store import STATE_DIR as ar_dir
    from bs_recon.store import STATE_DIR as recon_dir
    from cash_recon.store import RUNS_DIR as cash_runs
    from cash_recon.store import TRACES_DIR as cash_traces
    from close.cash_overlay import STATE_DIR as overlay_dir
    from close.month_end import STATE_DIR as close_dir
    from close.reviews import STATE_DIR as review_dir
    from fixed_assets.store import SEED_ASSETS, SEED_CANDIDATES, STATE_DIR as assets_dir
    from prepaid.store import SEED_PATH as prepaid_seed
    from prepaid.store import STATE_DIR as prepaid_dir

    from sample_data.paths import snapshot_loader_paths

    snap = snapshot_loader_paths()
    snap.update(
        {
            "ar": Path(ar_dir),
            "recon": Path(recon_dir),
            "cash_runs": Path(cash_runs),
            "cash_traces": Path(cash_traces),
            "close": Path(close_dir),
            "reviews": Path(review_dir),
            "overlays": Path(overlay_dir),
            "eval_prepaid_state": Path(prepaid_dir),
            "eval_prepaid_seed": Path(prepaid_seed),
            "eval_assets_state": Path(assets_dir),
            "eval_assets_seed": Path(SEED_ASSETS),
            "eval_capital_seed": Path(SEED_CANDIDATES),
        }
    )
    return snap


def restore_runtime_paths(snapshot: dict) -> None:
    from ar.store import configure_paths as configure_ar
    from bs_recon.store import configure_paths as configure_recon
    from cash_recon.store import configure_paths as configure_cash
    from close.month_end import configure_paths as configure_close
    from fixed_assets.store import configure_paths as configure_assets
    from prepaid.store import configure_paths as configure_prepaid

    from sample_data.paths import restore_loader_paths

    restore_loader_paths(snapshot)
    configure_ar(snapshot["ar"])
    configure_recon(snapshot["recon"])
    configure_close(snapshot["close"])
    configure_cash(runs_dir=snapshot["cash_runs"], traces_dir=snapshot["cash_traces"])
    configure_prepaid(snapshot["eval_prepaid_state"], seed_path=snapshot["eval_prepaid_seed"])
    configure_assets(
        snapshot["eval_assets_state"],
        seed_assets=snapshot["eval_assets_seed"],
        seed_candidates=snapshot["eval_capital_seed"],
    )
    from bs_recon.tools import _PACKETS

    _PACKETS.clear()


def _copy_eval_fixture(name: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(EVAL_DATA / name, dest)


def _seed_isolated_stores(root: Path, *, duplicate_asset: bool) -> None:
    from fixed_assets.store import configure_paths as configure_assets
    from prepaid.store import configure_paths as configure_prepaid
    from prepaid.store import reset as reset_prepaids
    from prepaid.store import save_items
    from fixed_assets.store import reset as reset_assets
    from fixed_assets.store import save_assets

    prepaid_seed = root / "prepaids.json"
    candidates = root / "capital_candidates.json"
    assets_seed = root / ("fixed_assets_duplicate.json" if duplicate_asset else "fixed_assets_empty.json")
    _copy_eval_fixture("prepaids.json", prepaid_seed)
    _copy_eval_fixture("capital_candidates.json", candidates)
    _copy_eval_fixture(assets_seed.name, assets_seed)

    configure_prepaid(root / "prepaid", seed_path=prepaid_seed)
    configure_assets(root / "assets", seed_assets=assets_seed, seed_candidates=candidates)
    reset_prepaids()
    reset_assets()
    save_items([insurance_prepaid()])
    if duplicate_asset:
        save_assets([duplicate_register_asset()])
    else:
        save_assets([])


def case_input_facts(case: EvalCase) -> dict:
    from fixed_assets.store import load_assets, load_seed_candidates
    from prepaid.store import load_items

    facts = {
        "case_id": case.case_id,
        "kind": case.kind,
        "prompt_has_expected_label": case.expected in case.prompt,
        "facts": dict(case.extra_facts),
    }
    if case.kind in {"prepaid"}:
        facts["prepaids"] = [_dump(item) for item in load_items()]
    if case.kind in {"fixed_asset", "duplicate_asset"}:
        facts["assets"] = [_dump(item) for item in load_assets()]
        facts["candidates"] = [_dump(item) for item in load_seed_candidates()]
    if case.kind == "reconciliation":
        facts["packet"] = _dump(cash_difference_packet())
    if case.kind == "final_close":
        facts["gate"] = _dump(blocked_close_gate())
    return facts


def deterministic_answer(case: EvalCase) -> str:
    from bs_recon.engine import classify_packet
    from close.agents import deterministic_final_review
    from close.models import ClosePeriod, MonthEndState
    from fixed_assets.agent import deterministic_prepare
    from prepaid.schedule import select_treatment

    if case.kind == "prepaid":
        return select_treatment(insurance_prepaid())
    if case.kind in {"fixed_asset", "duplicate_asset"}:
        return deterministic_prepare(server_candidate()).decision
    if case.kind == "reconciliation":
        return classify_packet(cash_difference_packet())
    if case.kind == "final_close":
        gate = blocked_close_gate()
        state = MonthEndState(
            period=ClosePeriod(period=gate.period, status="BLOCKED", opened_at="2026-09-01T00:00:00Z"),
            close_id="EVAL-CLOSE",
        )
        return deterministic_final_review(state, gate).decision
    raise ValueError(f"Unknown eval case kind {case.kind}")


def live_answer(case: EvalCase) -> str:
    import os

    from agent import run_agent
    from bs_recon.agent import bs_preparer
    from bs_recon.models import ReconDecision
    from bs_recon.tools import bind_packets
    from close.agents import month_end_reviewer
    from close.models import FinalCloseVerdict
    from fixed_assets.agent import fixed_asset_preparer
    from fixed_assets.models import AssetDecision
    from prepaid.agent import prepaid_preparer
    from prepaid.models import PrepaidDecision

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")
    if case.kind == "prepaid":
        result = run_agent(prepaid_preparer, case.prompt)
        return result.selected_method if isinstance(result, PrepaidDecision) else str(result)
    if case.kind in {"fixed_asset", "duplicate_asset"}:
        result = run_agent(fixed_asset_preparer, case.prompt)
        return result.decision if isinstance(result, AssetDecision) else str(result)
    if case.kind == "reconciliation":
        packet = cash_difference_packet()
        bind_packets(packet.period, [packet])
        result = run_agent(bs_preparer, case.prompt)
        return result.finding if isinstance(result, ReconDecision) else str(result)
    if case.kind == "final_close":
        result = run_agent(month_end_reviewer, case.prompt)
        return result.decision if isinstance(result, FinalCloseVerdict) else str(result)
    raise ValueError(f"Unknown eval case kind {case.kind}")


@dataclass
class EvalCaseResult:
    case_id: str
    kind: str
    expected: str
    allowed: tuple[str, ...]
    actual: str
    passed: bool
    input_facts: dict
    live: bool = False
    error: str = ""


@dataclass
class EvalRunReport:
    live: bool
    results: list[EvalCaseResult] = field(default_factory=list)
    input_fingerprint: str = ""
    workspace: str = ""

    def by_id(self) -> dict[str, EvalCaseResult]:
        return {item.case_id: item for item in self.results}

    @property
    def passed(self) -> int:
        return sum(int(item.passed) for item in self.results)

    @property
    def total(self) -> int:
        return len(self.results)


def _score_case(case: EvalCase, *, live: bool) -> EvalCaseResult:
    error = ""
    try:
        actual = live_answer(case) if live else deterministic_answer(case)
    except Exception as exc:
        actual = f"ERROR {exc}"
        error = str(exc)
    facts = case_input_facts(case)
    return EvalCaseResult(
        case_id=case.case_id,
        kind=case.kind,
        expected=case.expected,
        allowed=case.allowed,
        actual=str(actual),
        passed=case.matches(str(actual)),
        input_facts=facts,
        live=live,
        error=error,
    )


class IsolatedEvalWorkspace:
    """Temporary filesystem seeded only from ``data/eval/``."""

    def __init__(self) -> None:
        self._tmp = None
        self._previous: dict | None = None
        self.root = Path()

    def __enter__(self) -> IsolatedEvalWorkspace:
        from ar.store import configure_paths as configure_ar
        from bs_recon.store import configure_paths as configure_recon
        from cash_recon.store import configure_paths as configure_cash
        from cash_recon.store import reset_cash_state
        from close.month_end import configure_paths as configure_close
        from close.reviews import reset_reviews
        from close.cash_overlay import reset_overlays
        from bs_recon.tools import _PACKETS

        self._previous = snapshot_runtime_paths()
        self._tmp = TemporaryDirectory(prefix="close-eval-")
        self.root = Path(self._tmp.name)
        configure_ar(self.root / "ar")
        configure_recon(self.root / "recon")
        configure_close(self.root / "close")
        configure_cash(runs_dir=self.root / "cash-runs", traces_dir=self.root / "cash-traces")
        reset_cash_state()
        reset_reviews()
        reset_overlays()
        _PACKETS.clear()
        _seed_isolated_stores(self.root, duplicate_asset=False)
        return self

    def __exit__(self, *exc: object) -> None:
        from bs_recon.tools import _PACKETS

        _PACKETS.clear()
        if self._previous is not None:
            restore_runtime_paths(self._previous)
        if self._tmp is not None:
            self._tmp.cleanup()
        self._tmp = None
        self._previous = None

    def prepare(self, case: EvalCase) -> dict:
        _seed_isolated_stores(self.root, duplicate_asset=case.kind == "duplicate_asset")
        if case.kind == "reconciliation":
            from bs_recon.tools import bind_packets

            packet = cash_difference_packet()
            bind_packets(packet.period, [packet])
        return case_input_facts(case)


def run_isolated_eval(*, live: bool = False) -> EvalRunReport:
    with IsolatedEvalWorkspace() as workspace:
        results: list[EvalCaseResult] = []
        inputs: dict[str, dict] = {}
        for case in CANONICAL_CASES:
            inputs[case.case_id] = workspace.prepare(case)
            results.append(_score_case(case, live=live))
            inputs[case.case_id] = results[-1].input_facts
        return EvalRunReport(
            live=live,
            results=results,
            input_fingerprint=_fingerprint(inputs),
            workspace=str(workspace.root),
        )


def run_isolated_eval_repeats(*, live: bool = False, repeat: int = 1) -> list[EvalRunReport]:
    count = max(1, int(repeat))
    return [run_isolated_eval(live=live) for _ in range(count)]


def format_eval_report(reports: list[EvalRunReport] | EvalRunReport) -> str:
    rows = reports if isinstance(reports, list) else [reports]
    lines = [
        "MONTH-END CLOSE EVALUATION",
        "Ground truth is deterministic Python on an isolated eval snapshot.",
        "Live agents are optional and never see the answer key.",
        "",
    ]
    for index, report in enumerate(rows, start=1):
        if len(rows) > 1:
            lines.extend([f"RUN {index}/{len(rows)}", f"  input_fingerprint: {report.input_fingerprint}", ""])
        for item in report.results:
            lines.extend(
                [
                    f"CASE {item.case_id}",
                    f"  Q: {next(case.question for case in CANONICAL_CASES if case.case_id == item.case_id)}",
                    f"  expected: {item.expected}",
                    f"  agent/python: {item.actual}",
                    f"  result: {'PASS' if item.passed else 'FAIL'}",
                    f"  isolated: true",
                    "",
                ]
            )
        lines.append(f"Score: {report.passed}/{report.total}")
        lines.append("")
    if len(rows) > 1:
        fingerprints = {item.input_fingerprint for item in rows}
        lines.append(
            "Repeat setup: IDENTICAL" if len(fingerprints) == 1 else "Repeat setup: DIVERGED"
        )
    return "\n".join(lines).rstrip() + "\n"

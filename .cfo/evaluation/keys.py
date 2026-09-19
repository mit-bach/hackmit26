"""Load hidden answer keys. Operational workflows must never import this."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.isolation import AnswerKeyIsolationError, operational_phase
from sample_data.models import ExpectedResults


def load_expected_results(data_root: Path) -> ExpectedResults:
    if operational_phase():
        raise AnswerKeyIsolationError(
            "expected_results.json cannot be loaded during an operational workflow"
        )
    path = Path(data_root) / "expected_results.json"
    return ExpectedResults.model_validate(json.loads(path.read_text()))


def load_json_after_run(path: Path) -> Any:
    if operational_phase():
        raise AnswerKeyIsolationError(f"Evaluation-only file {path} read during operational phase")
    return json.loads(Path(path).read_text())


def load_cash_ground_truth(data_root: Path) -> dict:
    path = Path(data_root) / "cash_recon" / "ground_truth.json"
    if not path.exists():
        return {}
    return load_json_after_run(path)


def load_audit_ground_truth(data_root: Path) -> dict:
    path = Path(data_root) / "audit" / "ground_truth.json"
    if not path.exists():
        return {}
    return load_json_after_run(path)


def load_manifest(data_root: Path) -> dict:
    path = Path(data_root) / "manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())

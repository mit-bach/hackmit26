"""Build the discrepancy pack from valid company data plus operational overlays."""

from __future__ import annotations

import json
from pathlib import Path

from discrepancy.catalog import contracts
from discrepancy.holdout_catalog import holdout_contracts
from discrepancy.holdout_overlays import apply_holdout_overlays
from discrepancy.overlays import apply_overlays
from sample_data.orchestrator import generate_sample_data


def generate_discrepancy_data(*, seed: int = 42, period: str = "2026-09", output: Path | str = "data/discrepancy_demo"):
    dest = Path(output)
    generate_sample_data(seed=seed, period=period, output=dest)
    apply_overlays(dest)
    eval_dir = dest / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)
    payload = [item.model_dump(mode="json") for item in contracts()]
    (eval_dir / "discrepancy_contracts.json").write_text(json.dumps(payload, indent=2) + "\n")
    return dest


def generate_holdout_data(*, seed: int = 77, period: str = "2026-09", output: Path | str = "data/discrepancy_holdout"):
    dest = Path(output)
    generate_sample_data(seed=seed, period=period, output=dest)
    apply_holdout_overlays(dest)
    eval_dir = dest / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)
    payload = [item.model_dump(mode="json") for item in holdout_contracts()]
    (eval_dir / "holdout_contracts.json").write_text(json.dumps(payload, indent=2) + "\n")
    return dest

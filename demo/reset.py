"""Copy the immutable canonical demo pack into a writable runtime workspace."""

from __future__ import annotations

import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CANONICAL = REPO / "data" / "demo"
DEFAULT_RUNTIME = REPO / "runs" / "demo_runtime"

SKIP_DIR_NAMES = {"runs"}
SKIP_FILE_NAMES = {"expected_results.json", "expected_outcomes.json", "agent_cases.json"}


def reset_demo_runtime(
    dest: Path | None = None,
    *,
    source: Path | None = None,
    include_answer_keys: bool = False,
) -> Path:
    """Replace ``dest`` with a clean copy of the canonical demo pack.

    Never writes back to ``data/demo``. Answer keys stay out of the operational
    workspace unless ``include_answer_keys`` is explicitly requested.
    """
    src = Path(source or CANONICAL)
    target = Path(dest or DEFAULT_RUNTIME)
    if src.resolve() == target.resolve():
        raise ValueError("Refusing to reset the canonical demo directory onto itself")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    for path in src.rglob("*"):
        rel = path.relative_to(src)
        if any(part in SKIP_DIR_NAMES for part in rel.parts):
            continue
        if path.is_dir():
            (target / rel).mkdir(parents=True, exist_ok=True)
            continue
        if not include_answer_keys and path.name in SKIP_FILE_NAMES:
            continue
        dest_path = target / rel
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest_path)
    return target

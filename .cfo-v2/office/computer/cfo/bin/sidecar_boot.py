#!/usr/bin/env python3
"""Launch cfo_kernel so package dirs win over sibling CLI scripts like close.py."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _kernel_root() -> Path:
    env = os.environ.get("CFO_KERNEL", "").strip()
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve()
    return here.parents[5] / ".cfo"


def _computer_root() -> Path:
    env = os.environ.get("HARNESS_COMPUTER", "").strip()
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve()
    return here.parents[2]


def _prepare_path(kernel: Path, computer: Path) -> None:
    shim = computer / "cfo" / ".import-path"
    shim.mkdir(parents=True, exist_ok=True)
    for pkg in kernel.iterdir():
        if not pkg.is_dir() or not (pkg / "__init__.py").is_file():
            continue
        dest = shim / pkg.name
        if dest.is_symlink() or dest.exists():
            dest.unlink()
        dest.symlink_to(pkg)
    sys.path.insert(0, str(shim))
    if str(kernel) not in sys.path:
        sys.path.insert(1, str(kernel))
    os.environ["PYTHONPATH"] = os.pathsep.join([str(shim), str(kernel)])


def main() -> int:
    os.environ.pop("HARNESS_BOT", None)
    os.environ.setdefault("CFO_EVAL_PHASE", "operational")
    kernel = _kernel_root()
    computer = _computer_root()
    os.environ["CFO_KERNEL"] = str(kernel)
    os.environ["HARNESS_COMPUTER"] = str(computer)
    _prepare_path(kernel, computer)
    from cfo_kernel.__main__ import main as kernel_main

    return kernel_main(["--computer", str(computer), *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())

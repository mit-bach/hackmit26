#!/usr/bin/env python3
"""Repo-root shim. Kernel lives in .cfo/ (hidden from Obsidian)."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    engine = Path(__file__).resolve().parent / ".cfo"
    target = engine / Path(__file__).name
    if not target.is_file():
        raise SystemExit(f"CFO kernel not found: {target}")
    os.chdir(engine)
    sys.path.insert(0, str(engine))
    runpy.run_path(str(target), run_name="__main__")

#!/usr/bin/env python3
"""Repo-root shim for the Maximor demo website API."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    engine = Path(__file__).resolve().parent / ".cfo"
    os.chdir(engine)
    sys.path.insert(0, str(engine))
    sys.argv = [str(engine / "demo_web" / "__main__.py"), *sys.argv[1:]]
    runpy.run_module("demo_web", run_name="__main__")

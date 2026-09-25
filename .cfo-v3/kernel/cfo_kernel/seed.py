"""Assemble a Computer tree the Sidecar can attach to."""

from __future__ import annotations

import shutil
from pathlib import Path

from cfo_kernel.paths import DEFAULT_COMPUTER


def seed_computer(
    dest: Path,
    *,
    catalog: Path,
    grants: Path,
    slug_map: Path,
    data_src: Path | None = None,
) -> Path:
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    cfo = dest / "cfo"
    cfo.mkdir(exist_ok=True)
    shutil.copy(catalog, cfo / "catalog.json")
    shutil.copy(grants, cfo / "grants.json")
    shutil.copy(slug_map, cfo / "slug-map.json")
    data = dest / "data"
    source = Path(data_src) if data_src is not None else default_fixture_dir()
    if not data.exists():
        data.symlink_to(source.resolve(), target_is_directory=True)
    (dest / "runs").mkdir(exist_ok=True)
    (cfo / "idempotency").mkdir(exist_ok=True)
    return dest


def default_fixture_dir() -> Path:
    return DEFAULT_COMPUTER / "world" / "maximor"


def default_slug_map() -> Path:
    return DEFAULT_COMPUTER / "cfo" / "slug-map.json"

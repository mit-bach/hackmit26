#!/usr/bin/env python3
"""Same directories Harness initComputer creates. Kept so the layout can be read in one place.

Harness calls ensureSandboxLayout from initComputer on serve and on a new instance.
This file is not a step anyone runs to set up a desk.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RUN_DOMAINS = (
    "inbox",
    "ap",
    "ar",
    "bank",
    "cash_recon",
    "pay",
    "audit",
    "month_end",
    "accruals",
    "bs_recon",
    "integrations",
    "reporting",
    "ingestion",
)

DESK_DIRS = ("packets", "handles", "notes")


def bot_dir(slug: str) -> str:
    return "bot_" + slug.replace("-", "_")


def load_slugs(computer: Path) -> list[str]:
    roster_path = computer / "harness" / "roster.json"
    roster = json.loads(roster_path.read_text())
    slugs: list[str] = []
    for row in roster.get("bots", []):
        slug = row.get("slug")
        if isinstance(slug, str) and slug:
            slugs.append(slug)
    if not slugs:
        raise SystemExit(f"no bots in {roster_path}")
    return slugs


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_desk_readme(computer: Path, slug: str) -> None:
    path = computer / "workspace" / slug / "README.md"
    if path.exists():
        return
    path.write_text(
        f"# {slug}\n\n"
        "Packets go in packets/. Handles go in handles/. Notes go in notes/.\n"
        "Kernel traces live under runs/ and are not yours to invent.\n"
        f"Do not create workspace/{slug} siblings. Do not write data/, office/, cfo/, or another Bot's desk.\n"
    )


def init_computer(computer: Path) -> None:
    computer = computer.resolve()
    if not (computer / "harness" / "roster.json").is_file():
        raise SystemExit(f"not a Computer (missing harness/roster.json): {computer}")
    if (computer / "data").is_symlink():
        pass
    slugs = load_slugs(computer)
    for domain in RUN_DOMAINS:
        ensure_dir(computer / "runs" / domain)
    for slug in slugs:
        desk = computer / "workspace" / slug
        for name in DESK_DIRS:
            ensure_dir(desk / name)
        write_desk_readme(computer, slug)
        ensure_dir(computer / "harness" / "bots" / bot_dir(slug) / "memory")
    print(f"initialized {computer}")
    print(f"slugs {len(slugs)}: {', '.join(slugs)}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: init-computer.py <computer-root>")
    init_computer(Path(sys.argv[1]))


if __name__ == "__main__":
    main()

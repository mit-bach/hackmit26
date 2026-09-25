"""Static import reachability over .cfo-v3/kernel.

Usage: python import_graph.py <kernel_dir>

Parses every kernel .py file (not .venv, not __pycache__), collects every
import statement at any depth (module level and function level), resolves
names that land inside the kernel, and walks reachability from:

  compiler   -> compiler.__main__
  sidecar    -> cfo_kernel.__main__ plus every module that
                cfo_kernel/invoke.py can importlib from catalog.json
                "python" specs.
  sidecar+lockops -> sidecar plus the cfo_kernel LOCK_OP and
                TEST_PACKET_OP modules (close.month_end,
                close.orchestrator). Those ids are named in cfo_kernel but
                are not in catalog.json today; this root is conservative.

Prints, for each of the fourteen constructor modules, whether each root
reaches it and one shortest import chain when it does.
"""

from __future__ import annotations

import ast
import json
import sys
from collections import deque
from pathlib import Path

FOURTEEN = [
    "agent",
    "reporting.agents",
    "close.agents",
    "cash_recon.agent",
    "integrations.agent",
    "scheduling.agent",
    "ar.agents",
    "inbox.agents",
    "accrual.agent",
    "prepaid.agent",
    "bs_recon.agent",
    "fixed_assets.agent",
    "audit.agent",
    "invoice_ingestion.agents",
]


def module_name(path: Path, kernel: Path) -> str:
    parts = list(path.relative_to(kernel).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def collect(kernel: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for path in kernel.rglob("*.py"):
        rel = path.relative_to(kernel).parts
        if rel[0] in {".venv", "compile-out"} or "__pycache__" in rel:
            continue
        out[module_name(path, kernel)] = path
    return out


def is_package(name: str, mods: dict[str, Path]) -> bool:
    path = mods.get(name)
    return path is not None and path.name == "__init__.py"


def edges_for(name: str, path: Path, mods: dict[str, Path]) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    pkg = name if is_package(name, mods) else name.rpartition(".")[0]
    found: set[str] = set()

    def add_with_parents(target: str) -> None:
        parts = target.split(".")
        for i in range(1, len(parts) + 1):
            candidate = ".".join(parts[:i])
            if candidate in mods:
                found.add(candidate)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                add_with_parents(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base_parts = pkg.split(".") if pkg else []
                if node.level > 1:
                    base_parts = base_parts[: len(base_parts) - (node.level - 1)]
                base = ".".join(base_parts + ([node.module] if node.module else []))
            else:
                base = node.module or ""
            if base:
                add_with_parents(base)
            for alias in node.names:
                sub = f"{base}.{alias.name}" if base else alias.name
                if sub in mods:
                    found.add(sub)
    found.discard(name)
    return found


def bfs(roots: list[str], graph: dict[str, set[str]]) -> dict[str, str | None]:
    parent: dict[str, str | None] = {}
    queue: deque[str] = deque()
    for root in roots:
        if root in graph and root not in parent:
            parent[root] = None
            queue.append(root)
    while queue:
        cur = queue.popleft()
        for nxt in sorted(graph[cur]):
            if nxt not in parent:
                parent[nxt] = cur
                queue.append(nxt)
    return parent


def chain(target: str, parent: dict[str, str | None]) -> list[str]:
    out = [target]
    while parent[out[-1]] is not None:
        out.append(parent[out[-1]])  # type: ignore[arg-type]
    return list(reversed(out))


def main() -> int:
    kernel = Path(sys.argv[1]).resolve()
    mods = collect(kernel)
    graph = {name: edges_for(name, path, mods) for name, path in mods.items()}

    catalog = json.loads((kernel / "compile-out" / "catalog.json").read_text())
    op_modules = sorted({row["python"].partition(":")[0] for row in catalog["ops"]})
    missing = [m for m in op_modules if m not in mods]

    roots = {
        "compiler": ["compiler.__main__"],
        "sidecar": ["cfo_kernel.__main__", *op_modules],
        "sidecar+lockops": ["cfo_kernel.__main__", *op_modules, "close.month_end", "close.orchestrator"],
    }
    reach = {label: bfs(r, graph) for label, r in roots.items()}

    print(f"kernel modules: {len(mods)}")
    print(f"catalog op modules ({len(op_modules)}): {', '.join(op_modules)}")
    if missing:
        print(f"catalog op modules not in kernel: {missing}")
    for label, parent in reach.items():
        print(f"{label} reaches {len(parent)} modules")
    print()
    for target in FOURTEEN:
        importers = sorted(n for n, e in graph.items() if target in e)
        print(f"{target}")
        print(f"  imported by: {', '.join(importers) or '(none)'}")
        for label, parent in reach.items():
            if target in parent:
                print(f"  {label}: REACHED via {' -> '.join(chain(target, parent))}")
            else:
                print(f"  {label}: not reached")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Static import closure of .cfo-v3/kernel from the sidecar entry points.

Read-only. Parses every import statement (top level and inside functions)
and every importlib.import_module("literal") call. Does not execute kernel code.

    python3 -B reach.py /Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
K = ROOT / "kernel"

REMAP = (
    "accrual.ledger ar.store audit.store bs_recon.store bs_recon.tools cash_recon.demo "
    "cash_recon.case_store cash_recon.store close.context close.ledger close.month_end "
    "fixed_assets.store integrations.providers.base invoice_ingestion.extract "
    "invoice_ingestion.registry memory.store prepaid.store reporting.ledger reporting.store "
    "tools inbox.store ar.store accrual.workflow integrations.store invoice_ingestion.store "
    "invoice_ingestion.workflow scheduling.cash scheduling.pool scheduling.workflow workflow"
).split()


def mod_path(name: str) -> Path | None:
    rel = Path(*name.split("."))
    for cand in (K / f"{rel}.py", K / rel / "__init__.py"):
        if cand.is_file():
            return cand
    return None


def mod_name(path: Path) -> str:
    rel = path.relative_to(K).with_suffix("")
    parts = rel.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def package_of(path: Path) -> str:
    name = mod_name(path)
    return name if path.name == "__init__.py" else name.rpartition(".")[0]


def imports_of(path: Path) -> set[str]:
    out: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    pkg = package_of(path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = pkg.split(".") if pkg else []
                base = base[: len(base) - (node.level - 1)] if node.level > 1 else base
                prefix = ".".join(base)
                mod = f"{prefix}.{node.module}" if node.module else prefix
                mod = mod.strip(".")
            else:
                mod = node.module or ""
            if mod:
                out.add(mod)
            for a in node.names:
                if mod:
                    out.add(f"{mod}.{a.name}")
        elif isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            if name == "import_module" and node.args and isinstance(node.args[0], ast.Constant):
                if isinstance(node.args[0].value, str):
                    out.add(node.args[0].value)
    return out


PARENT: dict[Path, str] = {}


def closure(entries: set[str]) -> set[Path]:
    seen: set[Path] = set()
    todo = [(name, "entry") for name in sorted(entries)]
    while todo:
        name, via = todo.pop(0)
        parts = name.split(".")
        for i in range(1, len(parts) + 1):
            p = mod_path(".".join(parts[:i]))
            if p is None or p in seen:
                continue
            seen.add(p)
            PARENT[p] = via
            here = str(p.relative_to(K))
            todo.extend((child, here) for child in sorted(imports_of(p)))
    return seen


def main() -> None:
    catalog = json.loads((ROOT / "cfo" / "catalog.json").read_text())
    entries = {"cfo_kernel.__main__"}
    entries.update(REMAP)
    entries.update(op["python"].split(":")[0] for op in catalog["ops"])
    reach = closure(entries)
    compiler_reads: set[Path] = set(K.rglob("tools.py")) | set(K.rglob("agent.py")) | set(K.rglob("agents.py"))
    compiler_reads |= {K / "skills" / "assignments.py", K / "close" / "checklist.py"}
    compiler_reads |= set((K / "compiler").glob("*.py"))
    compiler_reads = {p for p in compiler_reads if ".venv" not in p.parts and p.is_file()}
    allpy = {p for p in K.rglob("*.py") if ".venv" not in p.parts and "__pycache__" not in p.parts}
    rel = lambda s: sorted(str(p.relative_to(K)) for p in s)
    print(json.dumps({
        "entries": sorted(entries),
        "sidecar_reach": rel(reach),
        "importer": {str(p.relative_to(K)): PARENT[p] for p in reach},
        "compiler_only": rel((compiler_reads & allpy) - reach),
        "no_reader": rel(allpy - reach - compiler_reads),
        "counts": {"all": len(allpy), "sidecar": len(reach), "compiler_only": len((compiler_reads & allpy) - reach), "none": len(allpy - reach - compiler_reads)},
    }, indent=1))


if __name__ == "__main__":
    main()

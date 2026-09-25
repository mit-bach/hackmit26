"""Find a Kernel reader for each file in .cfo-v3/world/maximor. Read-only.

A reader is a line in a kernel .py file that names the file's basename (or,
for the four document folders, the folder name). The reader counts as runtime
only when that .py file is in the sidecar import closure (reach.json).

    python3 -B world_readers.py /Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3 reach.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
REACH = json.loads(Path(sys.argv[2]).read_text())
SIDECAR = set(REACH["sidecar_reach"])
K = ROOT / "kernel"
W = ROOT / "world" / "maximor"

SOURCES = {
    str(p.relative_to(K)): p.read_text(encoding="utf-8").splitlines()
    for p in K.rglob("*.py")
    if ".venv" not in p.parts and "__pycache__" not in p.parts
}
DOC_DIRS = ("goods_receipts", "invoices", "packing_lists", "purchase_orders")


def hits(needle: str) -> list[tuple[str, int, str]]:
    pat = re.compile(r"[\"'/]" + re.escape(needle) + r"[\"'/]")
    out = []
    for rel, lines in SOURCES.items():
        for i, line in enumerate(lines, 1):
            if pat.search(line):
                out.append((rel, i, line.strip()[:160]))
    return out


def main() -> None:
    rows = []
    groups: dict[str, list[str]] = {}
    for p in sorted(W.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(W))
        parts = rel.split("/")
        if parts[0] == "documents" and len(parts) == 3 and parts[1] in DOC_DIRS:
            groups.setdefault(f"documents/{parts[1]}/*", []).append(rel)
            continue
        rows.append(rel)
    report = []
    for key, members in groups.items():
        folder = key.split("/")[1]
        h = hits(folder) + hits("documents")
        report.append({"path": key, "files": len(members), "hits": h})
    for rel in rows:
        name = Path(rel).name
        h = hits(name)
        if not h and "/" in rel:
            h = hits(Path(rel).parent.name)
        report.append({"path": rel, "files": 1, "hits": h})
    for row in report:
        row["runtime"] = [x for x in row["hits"] if x[0] in SIDECAR]
        row["offline"] = [x for x in row["hits"] if x[0] not in SIDECAR]
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()

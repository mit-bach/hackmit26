"""Rewrite compose_instructions(role, skills=..., safety=S) to a plain string.

Usage: python strip_compose.py <kernel_dir> <relpath> [<relpath> ...]

Each call becomes `role` or `role + "\\n\\n" + S` when safety= was passed.
That matches what the old loader returned with no skills rendered:
"\\n\\n".join([role.strip(), safety.strip()]). The `skills=` argument is
dropped. The `from skills import ...` line is removed. Any other reference
to a name from that import is reported and left for a manual edit.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def line_offsets(data: bytes) -> list[int]:
    out = [0]
    for i, byte in enumerate(data):
        if byte == 0x0A:
            out.append(i + 1)
    return out


def span(node: ast.AST, starts: list[int]) -> tuple[int, int]:
    return (
        starts[node.lineno - 1] + node.col_offset,
        starts[node.end_lineno - 1] + node.end_col_offset,
    )


def rewrite(path: Path) -> list[str]:
    data = path.read_bytes()
    tree = ast.parse(data, filename=str(path))
    starts = line_offsets(data)
    edits: list[tuple[int, int, bytes]] = []
    imported: set[str] = set()
    notes: list[str] = []

    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "skills" and node.level == 0:
            imported.update(alias.asname or alias.name for alias in node.names)
            a, b = span(node, starts)
            if data[b : b + 1] == b"\n":
                b += 1
            edits.append((a, b, b""))

    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        if node.func.id != "compose_instructions":
            continue
        if len(node.args) != 1:
            raise SystemExit(f"{path}:{node.lineno}: expected one positional role arg")
        role_a, role_b = span(node.args[0], starts)
        role_src = data[role_a:role_b]
        safety = next((kw.value for kw in node.keywords if kw.arg == "safety"), None)
        unknown = [kw.arg for kw in node.keywords if kw.arg not in {"skills", "safety"}]
        if unknown:
            raise SystemExit(f"{path}:{node.lineno}: unexpected kwargs {unknown}")
        if safety is None:
            replacement = role_src
        else:
            sa, sb = span(safety, starts)
            replacement = role_src + b' + "\\n\\n" + ' + data[sa:sb]
        a, b = span(node, starts)
        edits.append((a, b, replacement))

    edits.sort(key=lambda e: e[0], reverse=True)
    for a, b, rep in edits:
        data = data[:a] + rep + data[b:]
    path.write_bytes(data)

    tree = ast.parse(data, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in imported:
            notes.append(f"{path}:{node.lineno}: still references {node.id}")
    return notes


def main() -> int:
    kernel = Path(sys.argv[1]).resolve()
    notes: list[str] = []
    for rel in sys.argv[2:]:
        notes.extend(rewrite(kernel / rel))
        print(f"rewrote {rel}")
    for note in notes:
        print(note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

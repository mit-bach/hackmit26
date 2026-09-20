"""Compiler fail-closed when a constructor tools= name cannot resolve."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from compiler.compile_lib import CompileError, eval_tools_expr


def test_unresolvable_constructor_tool_fails_compile() -> None:
    tree = ast.parse("RECORD_TOOLS = [not_a_catalog_op]")
    assign = tree.body[0]
    assert isinstance(assign, ast.Assign)
    with pytest.raises(CompileError, match="cannot resolve tools name"):
        eval_tools_expr(assign.value, tree, Path("agent.py"), Path("."), {}, {})

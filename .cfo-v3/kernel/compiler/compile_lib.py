"""cfo-catalog compile: Catalog and Grants from Kernel constructors.

Reads kernel ``agent.py``, ``agents.py``, ``@function_tool`` signatures, and
`skills/assignments.py`. Does not import the OpenAI Agents SDK. Does not
guess tool lists. Constructor `tools=` that cannot resolve is a hard fail.
"""

from __future__ import annotations

import ast
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ANNOTATION_MAP = {
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "dict": "object",
    "list": "list",
    "Dict": "object",
    "List": "list",
    "Any": "object",
}

POLICY_FUNS = {"get_company_policies", "find_relevant_policies", "get_prior_cases"}

SOD_BY_MODULE = {
    "tools": "ap-records",
    "invoice_ingestion.tools": "ingestion",
    "accrual.tools": "accrual-read",
    "scheduling.tools": "treasury",
    "ar.tools": "ar",
    "cash_recon.tools": "cash-recon",
    "prepaid.tools": "prepaid",
    "fixed_assets.tools": "fixed-assets",
    "bs_recon.tools": "bs-recon",
    "close.tools": "close-read",
    "reporting.tools": "reporting",
    "audit.tools": "audit-read",
    "memory.tools": "memory-read",
    "inbox.tools": "inbox",
    "integrations.tools": "processor-payout",
}


@dataclass(frozen=True)
class ToolRef:
    module: str
    qualname: str

    @property
    def catalog_id(self) -> str:
        return f"{self.module}.{self.qualname}"

    @property
    def python(self) -> str:
        return f"{self.module}:{self.qualname}"


@dataclass
class CatalogOp:
    id: str
    python: str
    export_name: str
    args: dict[str, str]
    mutability: str
    sod_class: str
    eval_only: bool
    owner_prefixes: list[str]


@dataclass
class AgentGrant:
    display_name: str
    ops: list[str]
    skills: list[str]
    output_type: str
    source: str


@dataclass
class CompileResult:
    catalog: dict[str, Any]
    grants: dict[str, Any]
    grants_eval: dict[str, Any]
    warnings: list[str]
    grant_diff: dict[str, Any]


class CompileError(Exception):
    pass


def repo_root_from(start: Path | None = None) -> Path:
    here = (start or Path(__file__)).resolve()
    for parent in [here, *here.parents]:
        if (parent / ".harness").is_dir():
            return parent
    raise CompileError("could not find repo root containing .harness")


def kernel_root(repo: Path) -> Path:
    path = repo / ".cfo-v3" / "kernel"
    if not path.is_dir():
        raise CompileError(f"missing kernel at {path}")
    return path


def module_name_for(path: Path, kernel: Path) -> str:
    rel = path.resolve().relative_to(kernel.resolve())
    if rel.name == "__init__.py":
        parts = rel.with_suffix("").parts[:-1]
    else:
        parts = rel.with_suffix("").parts
    if parts[-1:] == ("__init__",):
        parts = parts[:-1]
    return ".".join(parts)


def annotation_type(node: ast.AST | None) -> str:
    if node is None:
        return "unknown"
    if isinstance(node, ast.Name):
        return ANNOTATION_MAP.get(node.id, node.id)
    if isinstance(node, ast.Constant):
        return "unknown" if node.value is None else str(node.value)
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left = annotation_type(node.left)
        right = annotation_type(node.right)
        if right in {"None", "NoneType", "unknown"}:
            return left
        if left in {"None", "NoneType", "unknown"}:
            return right
        return left
    if isinstance(node, ast.Subscript):
        base = annotation_type(node.value)
        if base in {"Optional", "Union"}:
            slc = node.slice
            if isinstance(slc, ast.Tuple) and slc.elts:
                return annotation_type(slc.elts[0])
            return annotation_type(slc)
        if base in {"list", "List"}:
            return "list"
        if base in {"dict", "Dict", "Mapping"}:
            return "object"
        return base
    return "unknown"


def parse_file(path: Path) -> ast.Module:
    source = path.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(path))


def is_function_tool_decorator(node: ast.AST) -> bool:
    if isinstance(node, ast.Name) and node.id == "function_tool":
        return True
    if isinstance(node, ast.Attribute) and node.attr == "function_tool":
        return True
    if isinstance(node, ast.Call):
        return is_function_tool_decorator(node.func)
    return False


def function_args(fn: ast.FunctionDef) -> dict[str, str]:
    out: dict[str, str] = {}
    skipped = {"self", "cls"}
    for arg in fn.args.args:
        if arg.arg in skipped:
            continue
        out[arg.arg] = annotation_type(arg.annotation)
    for arg in fn.args.kwonlyargs:
        if arg.arg in skipped:
            continue
        out[arg.arg] = annotation_type(arg.annotation)
    return out


def sod_class_for(module: str, qualname: str) -> str:
    if module == "tools" and qualname in POLICY_FUNS:
        return "ap-policy"
    if module == "memory.tools" and qualname == "get_decision_memories":
        return "memory-read"
    if module == "audit.tools" and qualname == "get_audit_ground_truth":
        return "audit-eval"
    if module == "accrual.tools" and qualname in {
        "create_accrual",
        "reconcile_accrual_with_invoice",
    }:
        return "accrual-write"
    return SOD_BY_MODULE.get(module, "kernel")


def wrapped_function_tool_name(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    if not is_function_tool_decorator(node.func):
        return None
    if not node.args:
        return None
    first = node.args[0]
    if isinstance(first, ast.Name):
        return first.id
    return None


def scan_function_tools(kernel: Path) -> dict[str, CatalogOp]:
    ops: dict[str, CatalogOp] = {}
    for path in sorted(kernel.rglob("tools.py")):
        if "__pycache__" in path.parts:
            continue
        module = module_name_for(path, kernel)
        tree = parse_file(path)
        defs: dict[str, ast.FunctionDef] = {}
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                defs[node.name] = node
                if not any(is_function_tool_decorator(d) for d in node.decorator_list):
                    continue
                ref = ToolRef(module, node.name)
                ops[ref.catalog_id] = CatalogOp(
                    id=ref.catalog_id,
                    python=ref.python,
                    export_name=node.name,
                    args=function_args(node),
                    mutability="read",
                    sod_class=sod_class_for(module, node.name),
                    eval_only=module == "audit.tools" and node.name == "get_audit_ground_truth",
                    owner_prefixes=[],
                )
        for node in tree.body:
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            if not isinstance(node.targets[0], ast.Name):
                continue
            original = wrapped_function_tool_name(node.value)
            if original is None or original not in defs:
                continue
            ref = ToolRef(module, original)
            if ref.catalog_id in ops:
                continue
            fn = defs[original]
            ops[ref.catalog_id] = CatalogOp(
                id=ref.catalog_id,
                python=ref.python,
                export_name=fn.name,
                args=function_args(fn),
                mutability="read",
                sod_class=sod_class_for(module, fn.name),
                eval_only=False,
                owner_prefixes=[],
            )
    if not ops:
        raise CompileError(f"no @function_tool ops found under {kernel}")
    return ops


def import_function_map(tree: ast.Module) -> dict[str, ToolRef]:
    """Map local names to Kernel callables imported in this file."""
    out: dict[str, ToolRef] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                local = alias.asname or alias.name
                out[local] = ToolRef(node.module, alias.name)
    return out


def constant_bindings(tree: ast.Module) -> dict[str, ast.AST]:
    out: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                out[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value:
            out[node.target.id] = node.value
    return out


def literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def load_string_dict(path: Path, name: str) -> dict[str, str]:
    tree = parse_file(path)
    bindings = constant_bindings(tree)
    node = bindings.get(name)
    if not isinstance(node, ast.Dict):
        raise CompileError(f"{path}: {name} is not a dict")
    out: dict[str, str] = {}
    for key, value in zip(node.keys, node.values):
        if key is None:
            continue
        ks = literal_string(key)
        vs = literal_string(value)
        if ks is None or vs is None:
            raise CompileError(f"{path}: {name} must be str-to-str")
        out[ks] = vs
    return out


def resolve_imported_name(
    name: str,
    tree: ast.Module,
    path: Path,
    kernel: Path,
    cache: dict[str, ast.Module],
) -> ast.AST | None:
    bindings = constant_bindings(tree)
    if name in bindings:
        return bindings[name]
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or not node.module:
            continue
        for alias in node.names:
            local = alias.asname or alias.name
            if local != name:
                continue
            module_file = module_to_path(node.module, kernel)
            if module_file is None:
                return None
            if str(module_file) not in cache:
                cache[str(module_file)] = parse_file(module_file)
            foreign = constant_bindings(cache[str(module_file)])
            return foreign.get(alias.name)
    return None


def module_to_path(module: str, kernel: Path) -> Path | None:
    rel = Path(*module.split("."))
    py_file = kernel / f"{rel}.py"
    init_file = kernel / rel / "__init__.py"
    if py_file.is_file():
        return py_file
    if init_file.is_file():
        return init_file
    return None


def canonicalize_tool_ref(
    ref: ToolRef,
    kernel: Path,
    ops: dict[str, CatalogOp],
    seen: set[str] | None = None,
) -> ToolRef:
    """Follow re-exports and function_tool() aliases to the Catalog op."""
    seen = set() if seen is None else seen
    if ref.catalog_id in ops:
        return ref
    if ref.catalog_id in seen:
        raise CompileError(f"circular tool re-export {ref.catalog_id}")
    seen.add(ref.catalog_id)
    path = module_to_path(ref.module, kernel)
    if path is None:
        raise CompileError(f"cannot resolve module {ref.module} for {ref.qualname}")
    tree = parse_file(path)
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == ref.qualname:
                original = wrapped_function_tool_name(node.value)
                if original:
                    return canonicalize_tool_ref(ToolRef(ref.module, original), kernel, ops, seen)
        if not isinstance(node, ast.ImportFrom) or not node.module:
            continue
        for alias in node.names:
            local = alias.asname or alias.name
            if local != ref.qualname:
                continue
            return canonicalize_tool_ref(ToolRef(node.module, alias.name), kernel, ops, seen)
    raise CompileError(f"{ref.catalog_id} is not a Catalog op")


def eval_tools_expr(
    node: ast.AST,
    tree: ast.Module,
    path: Path,
    kernel: Path,
    fn_map: dict[str, ToolRef],
    list_cache: dict[str, list[ToolRef]],
) -> list[ToolRef]:
    if isinstance(node, ast.List):
        refs: list[ToolRef] = []
        for elt in node.elts:
            refs.extend(eval_tools_expr(elt, tree, path, kernel, fn_map, list_cache))
        return refs
    if isinstance(node, ast.Tuple):
        refs = []
        for elt in node.elts:
            refs.extend(eval_tools_expr(elt, tree, path, kernel, fn_map, list_cache))
        return refs
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return eval_tools_expr(node.left, tree, path, kernel, fn_map, list_cache) + eval_tools_expr(
            node.right, tree, path, kernel, fn_map, list_cache
        )
    if isinstance(node, ast.Call):
        func_name = node.func.id if isinstance(node.func, ast.Name) else None
        if func_name in {"list", "tuple"} and node.args:
            return eval_tools_expr(node.args[0], tree, path, kernel, fn_map, list_cache)
        original = wrapped_function_tool_name(node)
        if original:
            return eval_tools_expr(ast.Name(id=original, ctx=ast.Load()), tree, path, kernel, fn_map, list_cache)
    if isinstance(node, ast.Name):
        if node.id in list_cache:
            return list(list_cache[node.id])
        bindings = constant_bindings(tree)
        if node.id in bindings:
            resolved = eval_tools_expr(bindings[node.id], tree, path, kernel, fn_map, list_cache)
            list_cache[node.id] = resolved
            return resolved
        if node.id in fn_map:
            ref = fn_map[node.id]
            foreign_path = module_to_path(ref.module, kernel)
            if foreign_path is not None:
                foreign_tree = parse_file(foreign_path)
                foreign_bindings = constant_bindings(foreign_tree)
                if ref.qualname in foreign_bindings:
                    foreign_map = import_function_map(foreign_tree)
                    return eval_tools_expr(
                        foreign_bindings[ref.qualname],
                        foreign_tree,
                        foreign_path,
                        kernel,
                        foreign_map,
                        {},
                    )
            return [ref]
        local_functions = {
            item.name for item in tree.body if isinstance(item, ast.FunctionDef)
        }
        if node.id in local_functions:
            return [ToolRef(module_name_for(path, kernel), node.id)]
        raise CompileError(f"{path}: cannot resolve tools name {node.id!r}")
    if isinstance(node, ast.Constant) and node.value is None:
        return []
    raise CompileError(
        f"{path}: cannot resolve tools= expression {type(node).__name__}; "
        "implicit all-tools is forbidden"
    )


def kwarg(call: ast.Call, name: str) -> ast.AST | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def display_name_of(
    call: ast.Call,
    tree: ast.Module,
    path: Path,
    kernel: Path,
    cache: dict[str, ast.Module],
) -> str:
    node = kwarg(call, "name")
    if node is None:
        raise CompileError(f"{path}: Agent() missing name=")
    text = literal_string(node)
    if text is not None:
        return text
    if isinstance(node, ast.Name):
        resolved = resolve_imported_name(node.id, tree, path, kernel, cache)
        text = literal_string(resolved) if resolved is not None else None
        if text is not None:
            return text
        raise CompileError(f"{path}: cannot resolve Agent name {node.id!r}")
    if isinstance(node, ast.Subscript):
        base_name: str | None = None
        if isinstance(node.value, ast.Name):
            base_name = node.value.id
        key = literal_string(node.slice)
        if base_name is None or key is None:
            raise CompileError(f"{path}: cannot resolve Agent name subscript")
        resolved = resolve_imported_name(base_name, tree, path, kernel, cache)
        if isinstance(resolved, ast.Dict):
            for dict_key, dict_val in zip(resolved.keys, resolved.values):
                if dict_key is None:
                    continue
                if literal_string(dict_key) == key:
                    text = literal_string(dict_val)
                    if text is not None:
                        return text
        raise CompileError(f"{path}: cannot resolve {base_name}[{key!r}]")
    raise CompileError(f"{path}: Agent name= must be a string or constant")


def output_type_of(call: ast.Call) -> str:
    node = kwarg(call, "output_type")
    if node is None:
        return ""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def is_agent_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name) and func.id == "Agent":
        return True
    if isinstance(func, ast.Attribute) and func.attr == "Agent":
        return True
    return False


def top_level_agent_calls(tree: ast.Module) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for node in tree.body:
        value: ast.AST | None = None
        if isinstance(node, ast.Assign):
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            value = node.value
        elif isinstance(node, ast.Expr):
            value = node.value
        if value is not None and is_agent_call(value):
            calls.append(value)
    return calls


def scan_agent_file(
    path: Path,
    kernel: Path,
    cache: dict[str, ast.Module],
) -> list[tuple[str, list[ToolRef], str, str]]:
    tree = parse_file(path)
    fn_map = import_function_map(tree)
    list_cache: dict[str, list[ToolRef]] = {}
    bindings = constant_bindings(tree)
    for name, value in bindings.items():
        if isinstance(value, (ast.List, ast.BinOp, ast.Tuple)):
            try:
                list_cache[name] = eval_tools_expr(value, tree, path, kernel, fn_map, list_cache)
            except CompileError:
                continue
    rows: list[tuple[str, list[ToolRef], str, str]] = []
    for call in top_level_agent_calls(tree):
        display = display_name_of(call, tree, path, kernel, cache)
        tools_node = kwarg(call, "tools")
        if tools_node is None:
            refs: list[ToolRef] = []
        else:
            refs = eval_tools_expr(tools_node, tree, path, kernel, fn_map, list_cache)
        rows.append((display, refs, output_type_of(call), str(path.relative_to(kernel))))
    return rows


def scan_sample_data_names(kernel: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    root = kernel / "sample_data" / "agents"
    if not root.is_dir():
        return rows
    for path in sorted(root.glob("*.py")):
        tree = parse_file(path)
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                target: ast.AST | None = None
                value: ast.AST | None = None
                if isinstance(item, ast.Assign) and len(item.targets) == 1:
                    target, value = item.targets[0], item.value
                elif isinstance(item, ast.AnnAssign):
                    target, value = item.target, item.value
                if isinstance(target, ast.Name) and target.id == "name" and value is not None:
                    text = literal_string(value)
                    if text:
                        rows.append((text, str(path.relative_to(kernel))))
    return rows


def scan_assignments(kernel: Path) -> dict[str, list[str]]:
    path = kernel / "skills" / "assignments.py"
    if not path.is_file():
        raise CompileError(f"missing {path}")
    tree = parse_file(path)
    bindings = constant_bindings(tree)
    node = bindings.get("AGENT_SKILLS")
    if not isinstance(node, ast.Dict):
        raise CompileError(f"{path}: AGENT_SKILLS is not a dict")
    out: dict[str, list[str]] = {}
    for key, value in zip(node.keys, node.values):
        if key is None:
            continue
        name = literal_string(key)
        if name is None:
            raise CompileError(f"{path}: AGENT_SKILLS keys must be strings")
        skills: list[str] = []
        elts: list[ast.AST]
        if isinstance(value, ast.Tuple):
            elts = list(value.elts)
        elif isinstance(value, ast.List):
            elts = list(value.elts)
        else:
            raise CompileError(f"{path}: AGENT_SKILLS[{name!r}] must be a tuple")
        for elt in elts:
            text = literal_string(elt)
            if text is None:
                raise CompileError(f"{path}: skill names must be strings")
            skills.append(text)
        out[name] = skills
    return out


def scan_checklist_owners(kernel: Path) -> set[str]:
    path = kernel / "close" / "checklist.py"
    if not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8")
    owners = set(re.findall(r'"(?:owner_agent|reviewer)":\s*"([^"]+)"', text))
    return owners


def apply_grant_denylist(agents: list[AgentGrant], overrides_path: Path) -> None:
    """Strip constructor ops that catalog.overrides.json forbids on a Display name."""
    if not overrides_path.is_file():
        return
    raw = json.loads(overrides_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return
    deny = raw.get("grantDenylist") or {}
    if not isinstance(deny, dict):
        return
    for agent in agents:
        blocked = deny.get(agent.display_name)
        if not isinstance(blocked, list):
            continue
        blocked_set = {item for item in blocked if isinstance(item, str)}
        agent.ops = [op_id for op_id in agent.ops if op_id not in blocked_set]


def apply_overrides(ops: dict[str, CatalogOp], overrides_path: Path) -> None:
    if not overrides_path.is_file():
        return
    raw = json.loads(overrides_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise CompileError(f"{overrides_path}: must be an object")
    patch = raw.get("ops", {})
    if not isinstance(patch, dict):
        raise CompileError(f"{overrides_path}: ops must be an object")
    for op_id, fields in patch.items():
        if not isinstance(fields, dict):
            raise CompileError(f"{overrides_path}: {op_id} must be an object")
        current = ops.get(op_id)
        if current is None:
            raise CompileError(f"{overrides_path}: unknown catalog id {op_id}")
        if "mutability" in fields:
            current.mutability = str(fields["mutability"])
        if "sodClass" in fields:
            current.sod_class = str(fields["sodClass"])
        if "evalOnly" in fields:
            current.eval_only = bool(fields["evalOnly"])
        if "exportName" in fields:
            current.export_name = str(fields["exportName"])
        if "ownerPrefixes" in fields:
            prefixes = fields["ownerPrefixes"]
            if not isinstance(prefixes, list) or not all(isinstance(p, str) for p in prefixes):
                raise CompileError(f"{overrides_path}: ownerPrefixes must be string[]")
            current.owner_prefixes = list(prefixes)


def qualify_export_names(ops: dict[str, CatalogOp]) -> None:
    by_export: dict[str, list[CatalogOp]] = {}
    for op in ops.values():
        by_export.setdefault(op.export_name, []).append(op)
    for export_name, group in by_export.items():
        if len(group) < 2:
            continue
        used: dict[str, CatalogOp] = {}
        for op in group:
            domain = op.id.split(".", 1)[0]
            prefixed = f"cfo_{domain}_{export_name}"
            if prefixed in used:
                raise CompileError(
                    f"exportName collision remains after prefix: {prefixed} "
                    f"({used[prefixed].id} vs {op.id})"
                )
            op.export_name = prefixed
            used[prefixed] = op


def load_overrides_defaults() -> dict[str, Any]:
    return {
        "version": "1",
        "ops": {
            "accrual.tools.create_accrual": {
                "mutability": "write-local",
                "sodClass": "accrual-write",
                "ownerPrefixes": ["runs/accrual/"],
            },
            "accrual.tools.reconcile_accrual_with_invoice": {
                "mutability": "write-local",
                "sodClass": "accrual-write",
                "ownerPrefixes": ["runs/accrual/"],
            },
            "audit.tools.get_audit_ground_truth": {
                "evalOnly": True,
                "sodClass": "audit-eval",
            },
        },
        "grantDenylist": {
            "Payment Audit": [
                "scheduling.tools.get_payment_candidates",
                "scheduling.tools.get_approved_pool",
            ],
            "Month-End Close Reviewer": [
                "accrual.tools.create_accrual",
            ],
        },
        "profileDenylist": {
            "ctl-pay/review-pay": [
                "scheduling.tools.get_payment_candidates",
                "scheduling.tools.get_approved_pool",
            ],
            "ctl-books/lock": [
                "accrual.tools.create_accrual",
            ],
        },
    }


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=False) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
        os.chmod(path, 0o644)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def catalog_payload(ops: dict[str, CatalogOp]) -> dict[str, Any]:
    rows = []
    for op_id in sorted(ops):
        op = ops[op_id]
        rows.append(
            {
                "id": op.id,
                "python": op.python,
                "exportName": op.export_name,
                "args": op.args,
                "mutability": op.mutability,
                "sodClass": op.sod_class,
                "evalOnly": op.eval_only,
                "ownerPrefixes": op.owner_prefixes,
            }
        )
    return {"version": "1", "ops": rows}


def grants_payload(agents: list[AgentGrant]) -> dict[str, Any]:
    by_name: dict[str, dict[str, Any]] = {}
    for agent in agents:
        by_name[agent.display_name] = {
            "ops": agent.ops,
            "skills": agent.skills,
            "outputType": agent.output_type,
            "source": agent.source,
        }
    return {"version": "1", "byDisplayName": by_name}


def grant_diff(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    prev_map: dict[str, set[str]] = {}
    if previous and isinstance(previous.get("byDisplayName"), dict):
        for name, row in previous["byDisplayName"].items():
            ops = row.get("ops", []) if isinstance(row, dict) else []
            prev_map[name] = set(ops)
    curr_map = {
        name: set(row.get("ops", []))
        for name, row in current["byDisplayName"].items()
        if isinstance(row, dict)
    }
    names = sorted(set(prev_map) | set(curr_map))
    added_names = sorted(set(curr_map) - set(prev_map))
    removed_names = sorted(set(prev_map) - set(curr_map))
    op_changes: dict[str, dict[str, list[str]]] = {}
    for name in names:
        before = prev_map.get(name, set())
        after = curr_map.get(name, set())
        plus = sorted(after - before)
        minus = sorted(before - after)
        if plus or minus:
            op_changes[name] = {"added": plus, "removed": minus}
    return {
        "addedDisplayNames": added_names,
        "removedDisplayNames": removed_names,
        "ops": op_changes,
    }


def empty_slug_map() -> dict[str, Any]:
    return {"version": "1", "bots": {}}


def compile_catalog(
    *,
    kernel: Path,
    out_dir: Path,
    phase: str = "operational",
    previous_grants: dict[str, Any] | None = None,
) -> CompileResult:
    if phase not in {"operational", "evaluation"}:
        raise CompileError(f"unknown phase {phase!r}")

    ops = scan_function_tools(kernel)
    overrides_path = out_dir / "catalog.overrides.json"
    if not overrides_path.is_file():
        write_json_atomic(overrides_path, load_overrides_defaults())
    apply_overrides(ops, overrides_path)
    qualify_export_names(ops)

    cache: dict[str, ast.Module] = {}
    agent_rows: list[tuple[str, list[ToolRef], str, str]] = []
    for pattern in ("agent.py", "agents.py"):
        for path in sorted(kernel.rglob(pattern)):
            if "__pycache__" in path.parts:
                continue
            agent_rows.extend(scan_agent_file(path, kernel, cache))
    for display, source in scan_sample_data_names(kernel):
        if not any(row[0] == display for row in agent_rows):
            agent_rows.append((display, [], "ScenarioPlan", source))

    skills = scan_assignments(kernel)
    warnings: list[str] = []
    constructed = {row[0] for row in agent_rows}
    for name in sorted(skills):
        if name not in constructed:
            warnings.append(f"AGENT_SKILLS has {name!r} with no Agent() constructor")

    for owner in sorted(scan_checklist_owners(kernel)):
        if owner not in constructed and owner not in skills:
            warnings.append(f"close/checklist.py owner {owner!r} is not in Grants")

    agents_operational: list[AgentGrant] = []
    agents_evaluation: list[AgentGrant] = []
    seen: set[str] = set()
    for display, refs, output_type, source in agent_rows:
        if display in seen:
            raise CompileError(f"duplicate Display name {display!r} ({source})")
        seen.add(display)
        op_ids: list[str] = []
        for ref in refs:
            resolved = canonicalize_tool_ref(ref, kernel, ops)
            if resolved.catalog_id not in ops:
                raise CompileError(
                    f"{source}: {display}: tools= item {resolved.catalog_id} is not a Catalog op"
                )
            op_ids.append(resolved.catalog_id)
        eval_ops = list(op_ids)
        operational_ops = [op_id for op_id in eval_ops if not ops[op_id].eval_only]
        for op_id in operational_ops:
            if ops[op_id].eval_only:
                raise CompileError(
                    f"production Grant for {display!r} includes evalOnly op {op_id}"
                )
        skill_names = list(skills.get(display, []))
        agents_operational.append(
            AgentGrant(
                display_name=display,
                ops=operational_ops,
                skills=skill_names,
                output_type=output_type,
                source=source,
            )
        )
        agents_evaluation.append(
            AgentGrant(
                display_name=display,
                ops=eval_ops,
                skills=skill_names,
                output_type=output_type,
                source=source,
            )
        )
        if display not in skills:
            warnings.append(f"constructor {display!r} is missing from AGENT_SKILLS")

    apply_grant_denylist(agents_operational, overrides_path)
    apply_grant_denylist(agents_evaluation, overrides_path)

    catalog = catalog_payload(ops)
    grants = grants_payload(agents_operational)
    grants_eval = grants_payload(agents_evaluation)
    for name, row in grants["byDisplayName"].items():
        for op_id in row["ops"]:
            if op_id not in ops:
                raise CompileError(f"Grant {name!r} lists unknown id {op_id}")
            if ops[op_id].eval_only:
                raise CompileError(
                    f"production Grant for {name!r} includes evalOnly op {op_id}"
                )

    active = grants if phase == "operational" else grants_eval
    diff = grant_diff(previous_grants, active)
    return CompileResult(
        catalog=catalog,
        grants=grants,
        grants_eval=grants_eval,
        warnings=warnings,
        grant_diff=diff,
    )


def write_compile_result(result: CompileResult, out_dir: Path) -> None:
    write_json_atomic(out_dir / "catalog.json", result.catalog)
    write_json_atomic(out_dir / "grants.json", result.grants)
    write_json_atomic(out_dir / "grants.eval.json", result.grants_eval)
    slug_map_path = out_dir / "slug-map.json"
    if not slug_map_path.is_file():
        write_json_atomic(slug_map_path, empty_slug_map())

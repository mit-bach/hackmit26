"""Import Catalog python callables and call the unwrapped Kernel function."""

from __future__ import annotations

import importlib
import inspect
from typing import Any

from cfo_kernel.grants import CatalogOp


class InvokeError(ValueError):
    """Args do not match the Kernel callable."""


def unwrap_callable(obj: Any) -> Any:
    seen: set[int] = set()
    current = obj
    while id(current) not in seen:
        seen.add(id(current))
        wrapped = getattr(current, "__wrapped__", None)
        if wrapped is not None:
            current = wrapped
            continue
        fn = getattr(current, "fn", None)
        if callable(fn) and fn is not current:
            current = fn
            continue
        break
    if not callable(current):
        raise TypeError(f"Catalog target is not callable: {obj!r}")
    return current


def resolve_python(spec: str) -> Any:
    module_name, sep, qualname = spec.partition(":")
    if not sep or not module_name or not qualname:
        raise InvokeError(f"Catalog python spec must be module:qualname, got {spec!r}")
    module = importlib.import_module(module_name)
    obj: Any = module
    for part in qualname.split("."):
        obj = getattr(obj, part)
    return unwrap_callable(obj)


def call_op(meta: CatalogOp, args: dict) -> Any:
    fn = resolve_python(meta.python)
    try:
        bound = inspect.signature(fn).bind(**args)
    except TypeError as exc:
        raise InvokeError(str(exc)) from exc
    bound.apply_defaults()
    return fn(*bound.args, **bound.kwargs)

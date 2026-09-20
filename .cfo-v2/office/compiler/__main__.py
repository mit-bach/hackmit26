"""CLI: python .cfo-v2/office/compiler/__main__.py [--kernel DIR] [--out DIR] [--phase operational|evaluation]."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from .compile_lib import CompileError, compile_catalog, kernel_root, repo_root_from, write_compile_result
except ImportError:
    from compile_lib import CompileError, compile_catalog, kernel_root, repo_root_from, write_compile_result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cfo-catalog")
    parser.add_argument("--kernel", type=Path, default=None, help="Kernel root (.cfo)")
    parser.add_argument("--out", type=Path, default=None, help="Computer cfo/ directory")
    parser.add_argument(
        "--phase",
        choices=("operational", "evaluation"),
        default="operational",
        help="stdout highlight; grants.json is always operational, grants.eval.json is always evaluation",
    )
    args = parser.parse_args(argv)

    try:
        repo = repo_root_from(Path(__file__))
        kernel = args.kernel.resolve() if args.kernel else kernel_root(repo)
        out_dir = (
            args.out.resolve()
            if args.out
            else repo / ".cfo-v2" / "office" / "computer" / "cfo"
        )
        previous = None
        previous_path = out_dir / "grants.json"
        if previous_path.is_file():
            previous = json.loads(previous_path.read_text(encoding="utf-8"))
        result = compile_catalog(
            kernel=kernel, out_dir=out_dir, phase=args.phase, previous_grants=previous
        )
        write_compile_result(result, out_dir)
    except CompileError as exc:
        sys.stderr.write(f"cfo-catalog: {exc}\n")
        return 1

    names = result.grants["byDisplayName"]
    eval_names = result.grants_eval["byDisplayName"]
    preparer = names.get("AP Preparer", {}).get("ops", [])
    approver = names.get("AP Approver", {}).get("ops", [])
    auditor = names.get("Auditor Agent", {}).get("ops", [])
    auditor_eval = eval_names.get("Auditor Agent", {}).get("ops", [])
    sys.stdout.write(f"cfo-catalog compile ok  phase={args.phase}\n")
    sys.stdout.write(f"  catalog ops: {len(result.catalog['ops'])}\n")
    sys.stdout.write(f"  display names: {len(names)}\n")
    sys.stdout.write(f"  wrote {out_dir / 'catalog.json'}\n")
    sys.stdout.write(f"  wrote {out_dir / 'grants.json'} (operational)\n")
    sys.stdout.write(f"  wrote {out_dir / 'grants.eval.json'} (evaluation)\n")
    sys.stdout.write("  AP Preparer ops:\n")
    for op_id in preparer:
        sys.stdout.write(f"    {op_id}\n")
    sys.stdout.write("  AP Approver ops:\n")
    for op_id in approver:
        sys.stdout.write(f"    {op_id}\n")
    sys.stdout.write(
        "  AP Preparer == AP Approver: "
        f"{'YES (SoD bug)' if preparer == approver else 'no'}\n"
    )
    ground_op = [op for op in auditor if op.endswith("get_audit_ground_truth")]
    ground_eval = [op for op in auditor_eval if op.endswith("get_audit_ground_truth")]
    sys.stdout.write(
        f"  Auditor Agent get_audit_ground_truth operational: {ground_op or 'omitted'}\n"
    )
    sys.stdout.write(
        f"  Auditor Agent get_audit_ground_truth evaluation: {ground_eval or 'omitted'}\n"
    )
    if result.grant_diff["ops"] or result.grant_diff["addedDisplayNames"] or result.grant_diff["removedDisplayNames"]:
        sys.stdout.write("  grant diff vs previous compile:\n")
        sys.stdout.write(json.dumps(result.grant_diff, indent=2) + "\n")
    else:
        sys.stdout.write("  grant diff vs previous compile: none\n")
    for warning in result.warnings:
        sys.stdout.write(f"  warning: {warning}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

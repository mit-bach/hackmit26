#!/usr/bin/env bash
# Kernel sidecar for the prove-fork Computer only.
# Does not walk to the repo .cfo or the Golden live office Computer.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
BOOT="$HERE/sidecar_boot.py"
COMPUTER="${HARNESS_COMPUTER:-$(cd "$HERE/../.." && pwd)}"

if [[ -z "${CFO_KERNEL:-}" ]]; then
  parent="$(cd "$COMPUTER/.." && pwd)"
  grand="$(cd "$COMPUTER/../.." && pwd)"
  if [[ -d "$parent/.cfo/cfo_kernel" ]]; then
    CFO_KERNEL="$parent/.cfo"
  elif [[ -d "$grand/.cfo/cfo_kernel" ]]; then
    CFO_KERNEL="$grand/.cfo"
  else
    echo "sidecar: isolated kernel missing next to $COMPUTER" >&2
    exit 1
  fi
fi
KERNEL="$CFO_KERNEL"

# Repo .cfo sits beside .cfo-v2/office/computer and has no sibling computer/.
kernel_parent="$(cd "$KERNEL/.." && pwd)"
if [[ -d "$kernel_parent/.cfo-v2/office/computer" && ! -d "$kernel_parent/computer" ]]; then
  echo "sidecar: refusing live office kernel at $KERNEL" >&2
  exit 1
fi

export HARNESS_COMPUTER="$COMPUTER"
export CFO_KERNEL="$KERNEL"
export CFO_EVAL_PHASE="${CFO_EVAL_PHASE:-operational}"
unset HARNESS_BOT || true

if [[ -x "$KERNEL/.venv/bin/python3" ]]; then
  PY="$KERNEL/.venv/bin/python3"
else
  PY="${CFO_PYTHON:-python3}"
fi

if [[ ! -d "$COMPUTER/data" ]]; then
  echo "sidecar: Computer data missing at $COMPUTER/data" >&2
  exit 1
fi

mkdir -p "$COMPUTER/runs" "$COMPUTER/cfo"
exec "$PY" "$BOOT"

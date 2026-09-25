#!/usr/bin/env bash
# Kernel sidecar for this Computer. Not a Bot. Does not drain inboxes.
set -euo pipefail

COMPUTER="/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3"
KERNEL="/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3/kernel"
BOOT="$(cd "$(dirname "$0")" && pwd)/sidecar_boot.py"

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
  echo "sidecar: symlink or copy world/maximor there first" >&2
  exit 1
fi

mkdir -p "$COMPUTER/runs" "$COMPUTER/cfo"
exec "$PY" "$BOOT"

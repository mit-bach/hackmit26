#!/usr/bin/env bash
# Kernel sidecar for this Computer. Not a Bot. Does not drain inboxes.
set -euo pipefail

if [[ -n "${HARNESS_COMPUTER:-}" ]]; then
  COMPUTER="$(cd "$HARNESS_COMPUTER" && pwd)"
else
  COMPUTER="$(cd "$(dirname "$0")/../.." && pwd)"
fi
export HARNESS_COMPUTER="$COMPUTER"
export PYTHONPATH="$COMPUTER/kernel"
export CFO_EVAL_PHASE=operational
unset HARNESS_BOT || true

exec "$COMPUTER/kernel/.venv/bin/python" -m cfo_kernel --computer "$HARNESS_COMPUTER"

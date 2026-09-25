#!/usr/bin/env bash
# Bind one Bot with Harness + the CFO Client extension.
# Usage: pi-bot.sh <slug> [--computer DIR]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../../.." && pwd)"
SLUG="${1:?usage: pi-bot.sh <slug> [--computer DIR]}"
shift || true
COMPUTER="${HARNESS_COMPUTER:-$ROOT/.cfo-v2/office/computer}"
if [[ "${1:-}" == "--computer" ]]; then
  COMPUTER="$(cd "$2" && pwd)"
fi

HARNESS_EXT="$ROOT/.harness/Harness-v2/extensions/index.ts"
CFO_EXT="$ROOT/.cfo-v2/office/computer/cfo/extensions/index.ts"

export HARNESS_BOT="$SLUG"
export HARNESS_COMPUTER="$COMPUTER"
export HARNESS_V2_ROOT="${HARNESS_V2_ROOT:-$ROOT/.harness/Harness-v2}"
export HARNESS_EXTRA_EXTENSIONS="${HARNESS_EXTRA_EXTENSIONS:-$CFO_EXT}"
export HARNESS_CLIENT_SKILLS="${HARNESS_CLIENT_SKILLS:-1}"
export CFO_EVAL_PHASE="${CFO_EVAL_PHASE:-operational}"

exec pi -e "$HARNESS_EXT" -e "$CFO_EXT" --name "$SLUG"

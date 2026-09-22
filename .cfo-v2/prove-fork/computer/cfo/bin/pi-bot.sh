#!/usr/bin/env bash
# Bind one Bot on the prove-fork Computer. Harness engine is shared; Client is this Computer.
# Usage: pi-bot.sh <slug> [--computer DIR]
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SLUG="${1:?usage: pi-bot.sh <slug> [--computer DIR]}"
shift || true
COMPUTER="${HARNESS_COMPUTER:-$(cd "$HERE/../.." && pwd)}"
if [[ "${1:-}" == "--computer" ]]; then
  COMPUTER="$(cd "$2" && pwd)"
  shift 2 || true
fi

CFO_EXT="$COMPUTER/cfo/extensions/index.ts"
if [[ ! -f "$CFO_EXT" ]]; then
  echo "pi-bot: Client extension missing at $CFO_EXT" >&2
  exit 1
fi

probe="$COMPUTER"
HARNESS_EXT=""
for _ in 1 2 3 4 5 6 7 8 9 10; do
  if [[ -f "$probe/.harness/Harness-v2/extensions/index.ts" ]]; then
    HARNESS_EXT="$probe/.harness/Harness-v2/extensions/index.ts"
    export HARNESS_V2_ROOT="${HARNESS_V2_ROOT:-$probe/.harness/Harness-v2}"
    break
  fi
  next="$(cd "$probe/.." && pwd)"
  if [[ "$next" == "$probe" ]]; then
    break
  fi
  probe="$next"
done
if [[ -z "$HARNESS_EXT" ]]; then
  echo "pi-bot: Harness extension missing" >&2
  exit 1
fi

if [[ -z "${CFO_KERNEL:-}" ]]; then
  parent="$(cd "$COMPUTER/.." && pwd)"
  grand="$(cd "$COMPUTER/../.." && pwd)"
  if [[ -d "$parent/.cfo/cfo_kernel" ]]; then
    export CFO_KERNEL="$parent/.cfo"
  elif [[ -d "$grand/.cfo/cfo_kernel" ]]; then
    export CFO_KERNEL="$grand/.cfo"
  fi
fi

export HARNESS_BOT="$SLUG"
export HARNESS_COMPUTER="$COMPUTER"
export HARNESS_EXTRA_EXTENSIONS="${HARNESS_EXTRA_EXTENSIONS:-$CFO_EXT}"
export HARNESS_CLIENT_SKILLS="${HARNESS_CLIENT_SKILLS:-1}"
export CFO_EVAL_PHASE="${CFO_EVAL_PHASE:-operational}"

exec pi -e "$HARNESS_EXT" -e "$CFO_EXT" --name "$SLUG"

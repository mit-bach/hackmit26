#!/bin/bash
# Usage: count.sh <root containing office/ and skills/>
# Counts markdown only.
set -euo pipefail
cd "$1"
files() { find office skills -name '*.md' -print0; }
printf 'files %s\n' "$(files | xargs -0 ls | wc -l | tr -d ' ')"
printf 'words %s\n' "$(files | xargs -0 cat | wc -w | tr -d ' ')"
printf 'not %s\n' "$(files | xargs -0 cat | grep -oiwE 'not' | wc -l | tr -d ' ')"
printf 'never %s\n' "$(files | xargs -0 cat | grep -oiwE 'never' | wc -l | tr -d ' ')"
printf 'do_not %s\n' "$(files | xargs -0 cat | grep -oiE '\bdo not\b' | wc -l | tr -d ' ')"
printf 'lines_with_not_or_never %s\n' "$(files | xargs -0 cat | grep -ciE '\b(not|never)\b' || true)"
printf 'peer_handle_not_approval %s\n' "$(files | xargs -0 cat | grep -ciE 'peer handle is not' || true)"
printf 'must_not_headings %s\n' "$(files | xargs -0 cat | grep -ciE '^## must not' || true)"

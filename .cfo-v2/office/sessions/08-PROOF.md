# Session 08 proof

Bot `close` with Profiles `accrue`, `prepaid`, `assets`, `bs`, `coordinate`. One Wake (Routine `month-end`). Different Grants per Profile — never union. Lock is not this Bot. Handle completion was not live-proven. Pi was not live-proven.

Client root: `.cfo-v2/`. Computer: `.cfo-v2/office/computer`. Kernel host: `.cfo/close/host.py`. Lock door: `close.month_end`. Test packet: `close.orchestrator.run_cfo_close`.

## Commands

Grant SoD against compiled Catalog/Grants and the session 08 fragment:

```bash
cd .cfo && .venv/bin/python -c "
from close.profile_grants import CREATE_ACCRUAL, mutating_ops, profile_allows
import json
from pathlib import Path
comp=json.loads(Path('../.cfo-v2/office/computer/cfo/grants.json').read_text())['byDisplayName']
print('prepaid allows create_accrual:', profile_allows('prepaid', CREATE_ACCRUAL))
print('coordinate mutating:', list(mutating_ops('coordinate')))
print('compiled prepaid has create_accrual:', CREATE_ACCRUAL in comp['Prepaid Preparer']['ops'])
print('compiled Close Manager ops:', comp['Close Manager']['ops'])
print('compiled Accrual Agent has create_accrual:', CREATE_ACCRUAL in comp['Accrual Agent']['ops'])
"
```

Result:

```
prepaid allows create_accrual: False
coordinate mutating: []
compiled prepaid has create_accrual: False
compiled Close Manager ops: []
compiled Accrual Agent has create_accrual: True
```

Host + default September BLOCKED + journals:

```bash
.cfo/.venv/bin/pytest \
  .cfo/tests/test_close_host.py \
  .cfo/tests/test_month_end_close.py \
  .cfo/tests/test_close_canonical.py \
  .cfo/tests/test_prepaid.py \
  .cfo/tests/test_fixed_assets.py \
  .cfo/tests/test_bs_recon.py \
  .cfo/tests/test_accrual_ledger.py -q
```

Result: `test_close_host.py` 8 passed. Combined close/prepaid/FA/BS/accrual ledger run: 36 passed (plus the 8 host tests in a prior invocation). Default `2026-09` demo stays `BLOCKED` on `$12.40`. Host `marked_closed` is false. Journals in those tests stay balanced (`debit == credit`; no `unbalanced:` findings from the host demo).

Canonical lock door:

```
test_canonical_run_is_month_end_run PASSED
```

`close.engine.CANONICAL_RUN` is `close.month_end.run_month_end`. Host calls that door with `allow_close=False` and never calls `period_lock.mark_period`.

## Disk

```
.cfo-v2/office/bots/close/
  BOT.md
  HOST.md
  NOTES.md
  catalog.fragment.json
  grants.fragment.json
  roster.fragment.json
  slug-map.fragment.json
  profiles/{accrue,prepaid,assets,bs,coordinate}.md
  routines/month-end.md
.cfo-v2/office/computer/cfo/grants.close.json
.cfo-v2/office/computer/skills/{accrual-evidence-evaluation,accrual-method-selection,prepaid-expense-accounting,fixed-asset-depreciation,balance-sheet-reconciliation,month-end-close-coordination}/SKILL.md
.cfo/close/host.py
.cfo/close/profile_grants.py
.cfo/tests/test_close_host.py
```

Host demo writes (under the test Computer, not the live Computer):

```
workspace/close/2026-09/pack.json
workspace/close/2026-09/host-run.json
workspace/close/2026-09/wakes/NNN-coordinate.json
workspace/close/2026-09/wakes/NNN-close-<profile>.json
workspace/close/2026-09/handles/ctl-books-*.json
```

Each wake names exactly one Profile. `coordinate` wakes have `ops: []` and `mark_closed: false`. Non-`accrue` wakes omit `accrual.tools.create_accrual`.

## Not live-proven

Pi bind, sidecar RPC Grant re-check, and `bot_send_prompt` completion. Session 01/02 execute the Handle payloads. Session 09 owns live `ctl-books`. This session wrote the payloads and proved Kernel gates.

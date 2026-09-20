# Gates

Run these before P0 burns a Pi turn. A failed gate is HARD. Patch or stop for the 05 repair agents. Do not start P1–P8.

Gates run against the **live** template (`.cfo-v2/office/computer`) plus Kernel `.cfo/`, except where a command names an instance. After a HARD patch, re-run the whole list.

Working directory: repo root `hackmit26`.

---

## G1 — Compiler

```bash
PYTHONPATH=.cfo-v2/office python3 -m compiler --phase operational
```

RUNS: exit 0. Writes live `computer/cfo/catalog.json` and `grants.json`.

HARD: non-zero. Constructor tool did not resolve. This is T3. Do not hand-edit Grant ops.

INTENDED: Collections Agent Grant includes send if AR repair landed. Close lock Profile is either granted or honestly empty (then P5 must not claim office-live lock). Stripe Display name is non-empty or P1 will HONEST “stripe not office-live.”

---

## G2 — Kernel import

Use `.cfo/.venv` if present. `sys.path` must include `.cfo`, not repo-root `inbox/`.

```bash
cd .cfo && .venv/bin/python - <<'PY'
import sys
sys.path.insert(0, ".")
from inbox.tools import classify_inbox_message
print("inbox.tools ok", classify_inbox_message)
try:
    from inbox.tools import send_office_outbound
    print("send_office_outbound ok", send_office_outbound)
except Exception as e:
    print("send_office_outbound FAIL", type(e).__name__, e)
from ar.agents import collections_agent
print("collections constructor", type(collections_agent))
PY
```

If `send_office_outbound` still ImportError, G2 is HARD for any P3 mailbox INTENDED step. You may continue P0, P2, P4 cash-without-AR, P5 BLOCKED, P7 on ops that exist. You may not tick AR send.

If `collections_agent` cannot construct, HARD T13 for collect.

---

## G3 — Catalog vs Grants

```bash
python3 - <<'PY'
import json
from pathlib import Path
root = Path(".cfo-v2/office/computer/cfo")
cat = {o["id"] for o in json.loads((root/"catalog.json").read_text())["ops"]}
g = json.loads((root/"grants.json").read_text())["byDisplayName"]
missing = []
for name, row in g.items():
    for op in row.get("ops") or []:
        if op not in cat:
            missing.append((name, op))
print("catalog", len(cat))
print("display names", len(g))
print("grant ops missing from catalog", missing)
empty = [n for n,r in g.items() if not r.get("ops")]
print("empty grants", empty)
PY
```

HARD: a Grant op is not in the Catalog.

Note empty names for P7 HONEST-EMPTY vs costume.

---

## G4 — Kernel pytest (subset)

Not office-live. Must not be red, or prove will misread BLOCKED as a tool throw.

```bash
cd .cfo && .venv/bin/python -m pytest tests/test_workflow.py tests/test_scheduling.py tests/test_ingestion_ap.py -q --tb=line
```

If venv pytest is too heavy, run the files the pipe will touch. A failing Kernel test is HARD for that pipe. Fix Kernel. Do not “prove around” a red `must_hold`.

Do not treat this as P2 INTENDED.

---

## G5 — Identity files from Computer cwd

P0 will recheck on the instance. Gate the template:

```bash
# After Floor repair these should exist:
ls -l .cfo-v2/office/computer/office/bots/ap/BOT.md \
      .cfo-v2/office/computer/office/constitution.md \
      .cfo-v2/office/bots/ap/BOT.md
```

If Computer cwd cannot see `office/bots/ap/BOT.md`, G5 is HARD for P0 INTENDED. Floor repair owns the layout (copy or symlink). Prove does not invent a second constitution.

---

## G6 — Intercept and handle-map

```bash
python3 - <<'PY'
import json
from pathlib import Path
c = Path(".cfo-v2/office/computer")
inter = json.loads((c/"harness/intercept.json").read_text())
hmap = json.loads((c/"cfo/handle-map.json").read_text())
print("intercept default", inter.get("default"))
print("collect intercept", (inter.get("bots") or {}).get("collect"))
print("collect write-off edge", [e for e in hmap["edges"] if e["from"]=="collect"])
PY
```

HARD if default `kind` is `operator`. HARD if collect write-off intercept is `ctl-cash` while handle-map says `ctl-pay` and you cannot tell which file the bus uses. Align is Floor. Prove refuses to start P3 write-off on a split brain.

---

## G7 — Serve is live Pi

Do not start `--fake`.

Read `RUN.md` section 3. Confirm `client.json` has `extraExtensions`, `clientSkills: true`, sidecar command.

When serve is up for P0, argv must include Client `-e` and `HARNESS_CLIENT_SKILLS=1`. If you cannot see argv, read `harness/extensions.json` on the selected Computer after serve writes it.

HARD: serve started `--fake` and you planned to tick office-live.

---

## G8 — World pack attached

```bash
ls -l .cfo-v2/office/computer/data
# expect symlink to ../world/maximor or equivalent Maximor pack
```

HARD if `data/` is missing or points at an empty tree. Do not load holdout. Do not load `examples/cfo-floor`.

---

## G9 — office.json sanity

```bash
python3 -m json.tool .cfo-v2/office/office.json
```

Note `currentId`. P0 will create a prove instance and select it. If `currentId` is `protocol-proof`, do not prove there.

---

## Gate rollup

Write `docs/Office-prove/logs/runs/_gates/GATES.md` with pass/fail per G1–G9. Then start P0.

If G2 send is FAIL and G1 compiled without send, AR mailbox is out of scope until 05 AR lands. Continue other pipes. Name the hole. Do not pretend collect contacted anyone.

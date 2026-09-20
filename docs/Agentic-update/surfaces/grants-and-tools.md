# Surface — Grants, Catalog, tools

Compiler: `.cfo-v2/office/compiler`.
Live files: `office/computer/cfo/catalog.json`, `grants.json`, `grants.eval.json`, `slug-map.json`, `catalog.overrides.json`.
Kernel constructors: `.cfo/**/agent.py`, `agents.py`.
Sidecar: `.cfo/cfo_kernel` Grant re-check on every op.

---

## Intended function of this surface

Constructor `tools=` lists are the Grant source. Compiler writes Catalog ids and per-Display-name ops. Slug-map says which Display name a Bot wears on a named Profile. Sidecar `authorize` re-checks. Client `call_connected_tool` refuses ops the bind Grant does not allow.

Skills never appear here as permissions.

Eval phase can include `get_audit_ground_truth`. Operational phase must not.

Overrides exist to tighten Verifier twins so they cannot hold Operator write or rebuild ops.

---

## Live counts (2026-09-20)

- Catalog ops: 89 on the live Computer. 94 in `instances/protocol-proof`.
- Display names in `grants.json`: 45.
- Empty `ops: []`: Audit Report Agent, Month-End Close Reviewer, Close Manager, five sample-data names (8 rows).
- Proof-only ops: `inbox.tools.send_office_outbound`, `inbox.tools.list_world_personas`, `inbox.tools.list_inbox_threads`, `inbox.tools.list_inbox_messages`, `inbox.tools.get_inbox_thread`.
- Stripe Display name: empty string. Bind refuses Connectors.

---

## What is good

Compiler as Grant source is the right SoT. Hand-editing Grant ops is forbidden by RUN.md.

Denylist for Verifier twins is the right SoD belt. Kernel sidecar `authorize` plus `sod_forbid` is a second belt.

Eval isolation for ground truth is good.

`call_connected_tool` + idempotency key is the right door for a bound Bot, when the Client extension loads and the sidecar is up.

---

## What is broken

### Constructor imports a tool the module does not export (T3)

`send_office_outbound` in `ar/agents.py` vs missing in `inbox/tools.py`. Collections Agent ImportError. Compiler cannot catalog a function that is not a `function_tool`. Tests in `compiler/test_compile_inbox.py` already expect it. Live tree fails those tests if run against current Kernel.

### Live compile stale vs instance snapshot (T2)

Someone compiled a fuller inbox into instance Computers. Live Computer did not receive those five ops. Recompile on live Kernel cannot create them until the functions exist.

### Empty ops on Profiles the office still wakes (T3, T8)

Close `coordinate`, `ctl-books` / `lock` Grant source Month-End Close Reviewer, `audit` / `report`. Wakes exist. Catalog door does not.

### Stripe empty by grain, still a Bot (T1, T3)

Intentional until a constructor exists. Inadequate as office-live Stripe.

### Denylist vs re-performance (T9)

`ctl-pay` / `review-match` cannot use `RECORD_TOOLS`. Review is packet + `get_case_evidence`. Incomplete packets get REFUSE (seen live). Complete packets that are wrong in a way evidence tools miss may pass. SoD vs re-performance is an unresolved tension. This corpus does not pick the Grant list. It names the tension.

### Consequential map is thin (T9)

`catalog.overrides.json` `consequential` names accrual writes to `ctl-books`. `verifier.ts` also regex-matches pay-run, lock, cash post, `side-effect-external`. Send, once it exists, may fall into side-effect-external → `ctl-pay`. Collect intercept.json says `ctl-cash`. Conflict.

### Connectors field is prompt text (T6)

Roster `connectors` for Operator Bots are Kernel op ids. For Source Bots they are provider names (`gmail`, `stripe`). Harness does not call them. Client search uses Grants. Models may think a connector string is a tool.

### Dual tool families for mail (T2)

`invoice_ingestion.tools.*` vs `inbox.tools.*`. See `pipes/intake.md`.

### Root package shadow (T2)

Repo-root `inbox/tools.py` duplicates Kernel inbox. `PYTHONPATH=.` vs `PYTHONPATH=.cfo` can load the wrong module.

---

## Capability this surface must possess

When Grants are adequate:

1. Every Profile the Roster can wake has a Display name and a Grant set that matches the constructor that is supposed to exist.
2. Every op a BOT.md “must call” exists in Catalog and on that Grant.
3. Every op a BOT.md “must not call” is absent from that Grant and denied by sidecar SoD.
4. Eval-only ops cannot load in operational phase.
5. Empty Display name is either given a constructor or the Bot is not claimed office-live.
6. Instance Computers and the live Computer do not silently diverge.

This file does not list the target ops for World or collect. Those functions are named in `pipes/ar.md` and `surfaces/world-inbox.md` as intended capability, not as a patch set.

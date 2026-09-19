# CFO Agentic System Extension

Design for a Client-system layer on Harness v2. One document. A later engineer can build from this file with no chat.

This is not Harness. This is not a rewrite of the Python finance engine. This is the door that lets standing Bots call the engine that already exists, with the same access rules Cursor already wired in Python.

Author: design pass. Date: 2026-09-19.

Live-system truth (code wins): [AGENTIC_SYSTEM_WORKFLOW.md](AGENTIC_SYSTEM_WORKFLOW.md). Harness contract: `GROK-WORKSHOP/harness-init/engineers/lark/HARNESS-V2.md`. Process shape only: `design-workshop/dominik/cfo-office-processes.md`.

---

## 1. Name map

One name for one thing. If two labels exist in the sources, this map picks one.

| Name | Meaning |
| --- | --- |
| Harness | The v2 runtime at `.harness/Harness-v2`. Roster, lanes, Handles, Rooms, Memory, approvals, Routines |
| Bot | A standing Harness identity. Bound with `HARNESS_BOT`. One lane |
| Display name | Python `Agent.name` string, for example `AP Preparer`. Not a Bot slug |
| Client system | One Roster plus skills plus a Computer. This office is one Client system |
| Computer | Shared cwd for that Client system. Files, `data/`, `runs/`, `harness/` |
| cfo-agentic-system | This Client-system layer. Pi extension plus Compiler plus Kernel |
| Kernel | The existing Python finance engine. Arithmetic, candidates, posting, gates |
| Catalog | `cfo/catalog.json`. Every Kernel op the Compiler found |
| Grant | One Display name mapped to a set of Catalog ids. From `Agent(..., tools=[...])` |
| Profile | A named Grant set on one Bot. A Wake names a Profile. Default is explicit |
| Slug map | `cfo/slug-map.json`. Operator-owned Bot slug → Profiles. The only topology file |
| Compiler | `cfo-catalog compile`. Reads Cursor artifacts. Writes Catalog and Grants |
| Connector | A Kernel op reached through `search_connected_tools` / `call_connected_tool` |
| Sidecar | The Kernel process that serves those ops. Does not drain inboxes |
| Handle | Harness accept-time record. Replaces in-process agent-to-agent calls as the bus |
| Operator | The human. Approvals and period lock sit here |

A Display name is not a Bot. A Grant is not a skill. A Connector is not a Room. The Sidecar is not a Bot. The Compiler does not choose how many Bots the office has.

---

## 2. Verdict

### What this office is

The repository is a connected Office of the CFO for a seeded company. Four layers appear in every workflow:

1. Source data — `data/` JSON, mock providers, optional live Stripe, human corrections
2. Kernel — Python arithmetic, candidate generation, matching, posting, gates, idempotency
3. Agentic reasoning — structured LLM decisions over those facts
4. Controls — validators, `HUMAN_REVIEW` queues, close gates, audit re-performance, period lock

Agents reason. Python calculates. An LLM never owns a ledger total.

That split stays. Harness does not become the ledger. The model does not become the ledger.

### What is load-bearing (keep)

- Stores under `data/` and `runs/`
- Candidate engines and cents tie-out
- AP hard policy holds in `workflow.py`
- Close checklist in `close/checklist.py`, gates in `close/gating.py`, period lock
- Shared IDs across approved pool, schedule, forecast, and close
- Eval isolation in `evaluation/isolation.py` (answer keys never open in operational phase)
- Constructor tool lists as the only Grant source
- Skill assignment in `skills/assignments.py` as the only skill SoT. Skills do not grant tools

### What is slop (do not port as architecture)

- Forty-three standing Bots as the floor. That count is how Cursor grew Agent objects. It is not a Harness topology
- Two close entrypoints: `close/month_end` (period lock) versus `close/orchestrator.run_cfo_close` (AP/accrual/schedule packet for tests)
- Skills that repeat SAFETY text already on the Agent
- Prompt packets that already contain full evidence, plus tools that refetch the same facts
- `get_audit_ground_truth` treated as a production Connector
- Docs that name agents the code does not construct
- In-process handoffs described as if they were a peer bus. They are function calls and JSON files

### What Harness already gives this Client

Bind (`HARNESS_BOT`), Handles, inboxes, Room Host, per-Bot Memory, Operator approvals, HTTP on loopback, Routines onto the owning Bot.

Roster fields `skills`, `connectors`, and `approvalLevel` exist. In this Harness cut they are prompt text. They do not filter Pi tools.

### What is missing (this layer)

1. An enforced per-Bot tool allowlist
2. The connector facade HARNESS-V2 named as later work: `search_connected_tools` / `call_connected_tool`
3. A compile step that reads Cursor’s current files instead of a hand-written ACL

cfo-agentic-system is that layer. It is Client code. It does not enter `.harness/Harness-v2/src`.

`.harness/Harness-v2/examples/cfo-floor` is a protocol-shaped stub. Six empty-skill Bots and `workspace/inbox/INV-1001.md` prove Handles. They are not this product.

---

## 3. Non-goals

1. Do not put invoices, ledgers, close DAGs, or specialist names into Harness source.
2. Do not rewrite Kernel modules in TypeScript.
3. Do not mandate 43 Bots. Do not mandate 6 Bots. The Slug map is operator-owned.
4. Do not union Grants when two Display names share one slug. That destroys segregation of duties.
5. Do not use `pi-subagents` or agent-room as the Bot network.
6. Do not use MCP as the local Bot-to-Bot bus.
7. Do not add finance HTTP routes to Harness.
8. Do not let a skill name grant a Connector.
9. Do not treat `close/orchestrator.run_cfo_close` as period close.
10. Do not build the extension in the same pass as this document.

---

## 4. Cursor format (Compiler input)

Cursor emits the same pattern in each domain folder. The Compiler reads that pattern. It does not invent a second agent registry.

### 4.1 Domain folder

Typical layout:

```text
<domain>/
  agent.py | agents.py    # Agent(name=..., tools=..., output_type=...)
  tools.py                # @function_tool adapters
  store.py                # persistence (when present)
  models.py
```

Root AP lives in `agent.py` and `tools.py` at the repo root. Ingestion lives in `invoice_ingestion/`. Close coordination lives in `close/agents.py` with no tools.

### 4.2 Agent constructor

Every operational agent is an OpenAI Agents SDK `Agent` with:

- `name` — Display name. Must match `skills/assignments.py` keys (ingestion uses `SOURCE_AGENTS` in `invoice_ingestion/models.py`)
- `instructions` — `compose_instructions(role, skills=skills_for(name), safety=...)`
- `tools` — a Python list of callables. This list is the Grant
- `output_type` — a Pydantic model. Copied into Bot instructions later. Not a Harness type

Example (root `agent.py`):

- AP Preparer → `RECORD_TOOLS`
- Exception Investigator → `RECORD_TOOLS + POLICY_TOOLS`
- AP Reviewer → evidence + policies + prior cases
- AP Approver → same as Reviewer
- AP Audit → evidence + policies, no `get_prior_cases`

Those five Display names share a domain and do not share Grants. The Compiler must keep that split.

### 4.3 Tools

Kernel ops the model may call are `@function_tool` functions in `**/tools.py`. There are about eighty. Most return dicts of Python facts. A few mutate.

Helpers that are not `@function_tool` stay Kernel-internal (`collect_case_evidence`, `bind_case`, `register_runtime_invoice`). The Compiler does not grant them unless a constructor lists them (none do today).

### 4.4 Skills

`skills/<name>/SKILL.md` plus `skills/assignments.py` (`AGENT_SKILLS`, `AGENT_ALIASES`).

Rule already in `.cursor/rules/skills.mdc`: adding a skill does not grant new external permissions. The Compiler copies skill names onto Grants metadata. It does not add Catalog ids from skills.

Sample-data agents in `sample_data/agents/base.py` use `build_agent` with no `tools` argument. Their Grant set is empty. They do not get Connectors.

### 4.5 What the Compiler must refuse

- A Display name in `AGENT_SKILLS` with no `Agent(name=...)` constructor (warn)
- An `Agent(name=...)` whose `tools=` the Compiler cannot resolve to Catalog ids (fail)
- Implicit “all tools in this module” (fail)
- Duplicate unqualified tool names without a module prefix in the Catalog (fail until qualified)

Known name collision: `get_bank_transaction` exists in `invoice_ingestion/tools.py` and in `cash_recon/tools.py`. Catalog ids are qualified. Pi-facing short names are unique or prefixed.

---

## 5. Contracts

Three files on the Computer. Catalog and Grants are Compiler output. The Slug map is operator-owned.

### 5.1 Catalog — `cfo/catalog.json`

```json
{
  "version": "1",
  "ops": [
    {
      "id": "tools.get_invoice",
      "python": "tools:get_invoice",
      "exportName": "get_invoice",
      "args": { "invoice_id": "string" },
      "mutability": "read",
      "sodClass": "ap-records",
      "evalOnly": false,
      "ownerPrefixes": []
    }
  ]
}
```

Field rules:

- `id` — `{module}.{function}` using the Python import path with dots, no leading package games. Root AP module is `tools`
- `python` — `{module}:{qualname}` the Sidecar imports
- `exportName` — name the model sees when unique. If not unique, `cfo_<domain>_<function>`
- `args` — JSON object of argument name → type name. Source: the function signature
- `mutability` — `read` | `write-local` | `side-effect-external`
- `sodClass` — coarse tag for SoD checks (`ap-records`, `ap-policy`, `accrual-write`, `audit-eval`, …)
- `evalOnly` — if true, production Grants must omit it
- `ownerPrefixes` — Computer path prefixes this op may write. Empty for `read`

Mutability assignment (Compiler table, hand-maintained exceptions allowed in `cfo/catalog.overrides.json`):

- Default: `read`
- `accrual.tools.create_accrual`, `accrual.tools.reconcile_accrual_with_invoice`: `write-local`
- Any future Kernel op that talks to Stripe, mail, or a bank: `side-effect-external`
- Period lock, pay-run release, write-off, send-as-user: `side-effect-external` even if the Python is local JSON, because the Operator gate must fire
- `audit.tools.get_audit_ground_truth`: `evalOnly: true`

`bind_case` and `bind_packets` are not Catalog ops. They are Sidecar session setup. See §11.

### 5.2 Grants — `cfo/grants.json`

```json
{
  "version": "1",
  "byDisplayName": {
    "AP Preparer": {
      "ops": ["tools.get_invoice", "tools.get_purchase_order", "tools.get_goods_receipt", "tools.find_duplicate_invoices", "tools.get_case_evidence"],
      "skills": ["three-way-match-analysis"],
      "outputType": "PreparerRecommendation"
    },
    "Close Manager": {
      "ops": [],
      "skills": ["month-end-close-coordination"],
      "outputType": "CloseManagerDecision"
    }
  }
}
```

`ops` is the resolved constructor list. Empty means no Connectors. Protocol tools from Harness still exist on a bound Bot.

### 5.3 Slug map — `cfo/slug-map.json`

Operator-owned. The Compiler may write a stub if the file is missing. It never overwrites a file that exists.

```json
{
  "version": "1",
  "bots": {
    "ap": {
      "defaultProfile": "prepare",
      "profiles": {
        "prepare": "AP Preparer",
        "investigate": "Exception Investigator",
        "review": "AP Reviewer",
        "approve": "AP Approver",
        "audit": "AP Audit"
      }
    }
  }
}
```

Rules:

1. Each Profile value is exactly one Display name that exists in Grants
2. `defaultProfile` is required
3. Two Profiles on one Bot may not point at Display names whose `sodClass` sets are defined as mutually exclusive unless the Operator also sets `"allowSodOverlap": true` on that Bot (default false). AP Preparer records versus AP Approver policy-only is overlap of domain, not of Grant union. The forbidden move is a hidden union of `ops` arrays
4. A 1:1 map is valid: `"preparer": { "defaultProfile": "main", "profiles": { "main": "AP Preparer" } }`
5. If a bound slug is missing from this file, the Bot gets **no Connectors**. Protocol tools still load. The session is not a finance worker

### 5.4 Fail closed

| Condition | Result |
| --- | --- |
| Constructor `tools=` cannot be resolved | Compiler exit non-zero |
| Grant lists an id not in Catalog | Compiler exit non-zero |
| Production Grant includes `evalOnly` op | Compiler exit non-zero |
| Slug map Profile names a missing Display name | Sidecar and Pi extension refuse Connectors for that Profile |
| Two Display names mapped without Profiles (a list union) | Refuse. Union is not a valid Slug map shape |
| `call_connected_tool` name not in the active Profile Grant | Kernel error `forbidden`. No Kernel call |
| Mutating op without idempotency key | Kernel error `idempotency_required` |
| Same key, different args hash | Kernel error `idempotency_mismatch` |
| Operator timeout on approval | Deny. Handle cancelled or stays blocked per Harness rules |

---

## 6. Profiles and segregation of duties

The office Roster will change. Grants must not.

A Wake, Handle, or Routine names a Profile:

- Inbox item field `profile` (string). If absent, use `defaultProfile`
- `bot_send_prompt` from a peer may pass `profile` in the prompt metadata the extension reads from the inbox row. Until Harness grows a first-class field, store it on the Handle `paths` sidecar file or in the wake text header `profile: approve`. The Kernel RPC always receives `profile`
- A Routine record may include `"profile": "approve"` in Client JSON the extension reads. Do not put that field into Harness types

**Do not union.** If one Bot `ap` runs Profile `prepare`, its Connectors are AP Preparer’s five record tools. When a later Wake says Profile `approve`, the extension **replaces** the tool set for that turn, or keeps one registered facade that consults the active Profile on each call. Replacing mid-session is allowed. Mixing both Grant sets in one turn is not.

**SoD that exists in code today (informative):**

- AP Preparer can load invoice/PO/receipt. AP Approver cannot. Approver sees evidence plus policy
- AP Audit cannot load `get_prior_cases`
- Accrual Agent is the only Display name granted `create_accrual`
- Auditor Agent is granted audit reads including `get_audit_ground_truth` (evalOnly — strip in production Grants)
- Audit Report Agent has `tools=[]`
- Close Manager and Month-End Close Reviewer have `tools=[]`
- Collections Agent does not get cash-application tools. Cash Application Agent does not get collection-candidate tools

When you compact Display names onto fewer Bots, keep those Grant sets on separate Profiles. The human SoD that the process doc gives to a Reviewer is the Operator approval path, not a Grant union.

---

## 7. Kernel Sidecar

### 7.1 Process

Start: `python -m cfo_kernel --computer <dir>`

The Sidecar is not a Bot. It does not bind `HARNESS_BOT`. It does not drain inboxes. Harness still owns lanes.

Environment:

- Computer root = `--computer` or `HARNESS_COMPUTER`
- Point existing `configure_data_dir` / run-root helpers at `<computer>/data` and `<computer>/runs`
- `CFO_EVAL_PHASE=operational` for live Bots so `evaluation.isolation` blocks answer keys

### 7.2 RPC

Request:

```json
{
  "op": "tools.get_invoice",
  "args": { "invoice_id": "INV-1001" },
  "botId": "bot_ap",
  "slug": "ap",
  "profile": "prepare",
  "handleId": "h_…",
  "idempotencyKey": null
}
```

Response:

```json
{
  "ok": true,
  "result": { },
  "error": null,
  "traceId": "k_…"
}
```

Transport: HTTP JSON on loopback (preferred for Pi `exec` / fetch) or newline JSON on stdio. One protocol. Pick HTTP on `127.0.0.1` with a random port written to `cfo/kernel.port`.

Every request:

1. Resolve Profile → Display name → Grant
2. If `op` not in Grant, return `forbidden`
3. If `evalOnly` and phase is operational, return `forbidden`
4. If mutability is not `read`, require `idempotencyKey` and claim it atomically under `cfo/idempotency/`
5. Import and call the Python callable with validated args
6. Run existing post-conditions (AP holds, close gates, period lock) when the op is in the write set
7. Append one line to `cfo/kernel.log.jsonl`
8. Return the dict the `@function_tool` already returns. Do not reshape amounts

The Pi extension filter is not enough. The Sidecar repeats the Grant check.

### 7.3 Idempotency

Derive the key from the client (Pi tool call id or Handle id plus op). Do not mint a new UUID per retry.

Claim with a unique file create (`cfo/idempotency/<key>.json`) that stores the request hash. If the file exists:

- Same hash → replay the stored response
- Different hash → `idempotency_mismatch`

Retention: outlive close reruns and eval replays. Do not expire inside the demo period.

### 7.4 Session state the current tools hide

Three in-memory binds will break if each RPC is a cold process:

1. `register_runtime_invoice` in root `tools.py` — ingestion overlay is process-local
2. `cash_recon.tools.bind_case` — bank/ledger/candidates live in module globals
3. `bs_recon.tools.bind_packets` — packets live in module globals

Sidecar rules:

- Prefer one long-lived Sidecar per Computer
- Persist ingestion overlay to `<computer>/runs/ingestion/overlay.json` and load it on start
- Cash: bind is Python-side before the agent turn today. Expose Sidecar-internal `kernel.bind_cash_case` called by the workflow host, not by the model. Store the bound case under `<computer>/runs/cash_recon/cases/<id>.json` and select it with `args.case_id`
- BS rec: same pattern with `period` + `account_id` already on the tools. `bind_packets` stays host-side

Until those three are file-backed, do not run multiple Sidecar workers against one Computer.

### 7.5 Inspect ops for tool-less Display names

Close Manager, Month-End Close Reviewer, and Audit Report Agent have empty Grants. Optional read-only Catalog ops may wrap existing fact functions (`ready_tasks`, `evaluate_close_gates`, structured audit statistics). They must not compute new amounts. They are new Catalog entries only if a constructor or an explicit override lists them. Default: keep empty Grants. Those Bots use Harness protocol tools and files on the Computer.

### 7.6 Eval isolation

`assert_answer_key_blocked` already wraps AP JSON reads. The Sidecar must call `operational_phase_guard()` for Bot traffic.

`get_audit_ground_truth` stays in Catalog with `evalOnly: true`. Production compile drops it from Auditor Agent Grants. Eval compile may keep it behind `CFO_EVAL_PHASE=evaluation`.

---

## 8. Pi extension

Load **with** Harness, not instead of it:

```bash
HARNESS_BOT=ap HARNESS_COMPUTER=/path/to/computer \
  pi -e /path/to/Harness-v2/extensions/index.ts \
     -e /path/to/cfo-agentic-system/extensions/index.ts \
     --name ap
```

Or a Client package whose `package.json#pi.extensions` lists both entries, Harness first.

### 8.1 Bind

If `HARNESS_BOT` is unset, register nothing. Unbound Pi is not a finance worker.

If set:

1. Read Slug map for that slug
2. Register `search_connected_tools` and `call_connected_tool`
3. Optionally register each granted `exportName` as its own Pi tool. If both exist, `call_connected_tool` is the canonical path and short names are aliases
4. Filter `resources_discover` skillPaths: `<computer>/skills/<name>` only when `name` is in the active Display name’s `skills` list from Grants (which came from `assignments.py`). Do not load the whole Computer skills tree
5. On each turn, read the inbox Profile (or default) and pass it on every Kernel RPC

Harness protocol tools stay registered by Harness. cfo-agentic-system does not reimplement `bot_send_prompt`.

### 8.2 Connector tools (the product names)

```text
search_connected_tools(query, status?)
call_connected_tool(name, args, idempotency_key?)
```

`search_connected_tools` returns Catalog rows this Profile may call. Never returns another Bot’s ops. Never returns evalOnly ops in operational phase.

`call_connected_tool`:

1. Resolve `name` to Catalog `id` (exportName or id)
2. RPC the Sidecar
3. If mutability is `side-effect-external`, or `write-local` while Bot `approvalLevel` is `always`, or the op is in the consequential set below, do not call the Sidecar until Harness approval allows the tool. Use the same `tool_call` intercept Harness already has. A peer Handle is not approval

Consequential set for this Client (fail closed):

- `create_accrual`, `reconcile_accrual_with_invoice`
- Any op that posts a journal, mutates `runs/ar/state.json`, writes period lock, or marks close CLOSED
- Pay-run release and send-as-user (not implemented as tools today; when they appear, they join this set)
- `get_audit_ground_truth` in operational phase (refuse, do not ask)

Read ops do not park the Handle.

### 8.3 Path ownership

Audit instructions already say: do not rewrite operational books. Enforce:

- Grants for Auditor Agent are read Catalog ops only
- `write-local` ops carry `ownerPrefixes`. AP writes under `runs/` paths the AP workflow already uses. Audit prefixes are `workspace/audit/` and `runs/audit/` only
- Harness path leases remain the backstop when two Bots edit the same file

### 8.4 Handoffs

Kernel is for objects and amounts. Files are for the next Bot.

1. The sending Bot writes a path on the Computer (evidence packet, result note)
2. It calls `bot_send_prompt` with that path
3. It awaits the Handle
4. It does not tell the Operator the teammate finished unless `done` is true

Do not dump Memory or Kernel traces into the prompt body.

---

## 9. Computer layout (final attached tree)

```text
<computer>/
  harness/roster.json
  harness/protocol.jsonl
  harness/bots/<botId>/...
  cfo/catalog.json
  cfo/grants.json
  cfo/slug-map.json
  cfo/catalog.overrides.json    # optional mutability / evalOnly patches
  cfo/kernel.port
  cfo/kernel.log.jsonl
  cfo/idempotency/
  data/                         # existing seeds
  runs/                         # existing mutable state
  skills/<name>/SKILL.md
  workspace/                    # Handle paths, briefs, findings
```

`harness/roster.json` stays Client-owned. The Compiler may print a suggested bots array to stdout. It does not overwrite the Roster.

Point `HARNESS_COMPUTER` at this tree. Keep Python imports working by running the Sidecar with cwd at the repo or with `PYTHONPATH` set to the repo root. The Computer may be the repo root during the hackathon.

---

## 10. Display names → Grants (code as of 2026-09-19)

Informative. If constructors change, the Compiler wins. This table is the expected first compile, so a reviewer can see SoD.

### Ingestion (`invoice_ingestion/agents.py`)

| Display name | Ops |
| --- | --- |
| Email Invoice Agent | `list_email_candidates`, `get_email`, `get_email_attachment` |
| ERP Invoice Agent | `list_erp_invoice_records`, `get_erp_invoice` |
| Procurement Invoice Agent | `list_procurement_records`, `get_procurement_record` |
| Vendor Portal Agent | `list_vendor_portal_documents`, `get_vendor_portal_document` |
| Employee Submission Agent | `list_employee_submissions`, `get_employee_submission` |
| Physical Mail / Document Agent | `list_mail_documents`, `get_mail_document` |
| EDI / Electronic Invoicing Agent | `list_edi_documents`, `get_edi_document` |
| Bank/Card Discovery Agent | `list_bank_transactions`, `get_bank_transaction`, `find_related_invoice` (ingestion module) |

These are Connectors, not automatic Bots. One `ingest` Bot may hold eight Profiles named after `SUPPORTED_SOURCES`. Eight Bots may map 1:1. The Compiler does not care.

### AP (`agent.py`)

| Display name | Ops |
| --- | --- |
| AP Preparer | `get_invoice`, `get_purchase_order`, `get_goods_receipt`, `find_duplicate_invoices`, `get_case_evidence` |
| Exception Investigator | Preparer set plus `get_company_policies`, `find_relevant_policies`, `get_prior_cases` |
| AP Reviewer | `get_case_evidence`, `get_company_policies`, `find_relevant_policies`, `get_prior_cases` |
| AP Approver | same as Reviewer |
| AP Audit | `get_case_evidence`, `get_company_policies`, `find_relevant_policies` |

### Accrual (`accrual/agent.py`)

Accrual Agent: all twelve `ACCRUAL_TOOLS`, including `create_accrual` and `reconcile_accrual_with_invoice` (`write-local`).

### Scheduling (`scheduling/agent.py`)

Payment Scheduler and Payment Audit: `get_cash_position`, `get_approved_pool`, `get_payment_candidates`, `get_treasury_policies`. Same Grant, different Display names. Profiles may share the Grant set. That is not a union of different lists.

### AR (`ar/agents.py`)

| Display name | Ops |
| --- | --- |
| Collections Agent | `get_collection_candidates`, `get_collection_invoice_facts`, `get_ar_customer`, `get_ar_precedents` |
| Cash Application Agent | `get_cash_application_facts`, `get_ar_customer`, `get_ar_precedents` |
| Cash Application Reviewer | same as Cash Application Agent |

`get_ar_close_snapshot` exists in `ar/tools.py` and is **not** on any constructor. Do not grant it.

### Cash recon (`cash_recon/agent.py`)

Preparer, Exception Investigator, Reviewer: `get_bank_transaction`, `get_ledger_entry`, `get_fee_evidence`, `get_match_candidates`, `get_candidate` (cash_recon module). All read. Posting stays in Python workflow code, not in these tools.

### Prepaid / fixed assets / BS rec

- Prepaid Preparer / Reviewer: `get_prepaid`, `list_prepaids`, `get_prepaid_treatment_candidates`, `get_prepaid_schedule`
- Fixed Asset Preparer / Reviewer: `get_fixed_asset`, `list_fixed_assets`, `get_depreciation_schedule`, `get_capital_candidates`
- BS Preparer / Reviewer: `get_reconciliation_packet`, `list_reconciling_items`

`list_period_reconciliations` exists in `bs_recon/tools.py` and is **not** on constructors. Do not grant it.

### Close (`close/agents.py`)

Month-End Close Reviewer, Close Manager: no ops.

### Reporting (`reporting/agents.py`)

| Display name | Ops |
| --- | --- |
| Variance Analysis Agent | `get_period_metrics`, `get_variance_facts`, `get_variance_trace` |
| Reporting Reviewer Agent | same variance set |
| Board Reporting Agent | `get_period_metrics`, `get_variance_facts`, `get_cash_forecast` |
| Cash Forecast Agent | `get_cash_forecast`, `get_forecast_snapshot`, `get_forecast_checks` |
| Forecast Reviewer Agent | same forecast set |
| Forecast Variance Agent | same forecast set |

### Audit (`audit/agent.py`)

Auditor Agent: period, payments, journals, approvals, vendors, invoices, operational decisions, planted recs, policy, **and** `get_audit_ground_truth` (evalOnly). Audit Report Agent: none.

### Sample data

Five Display names from `assignments.py`. Constructors have no tools. Grant sets empty.

---

## 11. Workflow overlay (Handles + Kernel, Python gates remain)

HARNESS-V2 pipes work as: write a file, send a Handle, await done. This office already has Python workflows that precompute facts, run an Agent, then validate. Keep that host logic in Python. Do not reimplement `workflow.py` in the Pi extension.

What changes:

1. The Agent is a bound Bot, not `Runner.run_sync` in the same process as the next specialist
2. The specialist next door is another Bot (or another Profile on a Bot), reached with `bot_send_prompt`
3. Tools hit the Sidecar instead of in-process `@function_tool`
4. `evaluate_close_gates` and AP `must_hold` still run in Python after the turn. The model cannot override a failed gate
5. Human review still mutates **source** objects, then a rerun. Harness `ask_user` is the Operator gate for consequential Kernel ops. It does not replace AR/cash/close review queues

Month-end DAG (`close/checklist.py`) stays the host. Task owners in that file are Display names (`owner_agent`, `reviewer`). The close host looks up the Slug map to send a Handle to the Bot that currently carries that Profile. If the slug is missing, the task stays blocked. The DAG does not hardcode `bot_ap`.

Close ingest today runs with `forward_to_ap=False` (recorded, not the period AP inbox). Do not “fix” that in the extension. Preserve it.

`close/orchestrator.run_cfo_close` remains a test packet. Period lock is `close/month_end` only.

Stripe/Adyen stay Kernel integrations (`docs/integrations.md`). They produce `ProviderPayout` records. They never become AP invoices. They are not Pi tools unless a constructor lists them (none do).

Payment plans do not send bank money. Do not add a send-as-bank Connector without an Operator gate.

---

## 12. Compiler procedure (aircraft-strict)

Working directory: the repo root that contains `agent.py` and `skills/assignments.py`.

1. Parse every `agent.py` and `agents.py` for `Agent(` constructors. Record `name` and `tools=` expression.
2. Resolve list names (`RECORD_TOOLS`) and inline lists to callables. Resolve each callable to `{module}:{qualname}`.
3. Scan `**/tools.py` for `@function_tool` functions. Build Catalog rows. Apply `cfo/catalog.overrides.json` if present.
4. Fail if a constructor tool is not a Catalog op.
5. Fail if two Catalog ops share `exportName` and no override prefixes them.
6. Read `skills/assignments.py` `AGENT_SKILLS`. Attach `skills` arrays to Grants. Warn on names with no constructor.
7. Mark `audit.tools.get_audit_ground_truth` evalOnly unless an override says otherwise.
8. Write `cfo/catalog.json` and `cfo/grants.json` atomically (temp file, then rename).
9. If `cfo/slug-map.json` is absent, write a stub that maps nothing (empty `bots`). Do not guess slugs from Display names.
10. Print a diff of Grant ids versus the previous compile. A drift with no constructor change is a Compiler bug.

Do not read `README.md` for tool lists. Code wins.

---

## 13. Done when (later build)

The layer is useful when all of these are true on disk, without a model:

1. Compiler output matches constructor lists in §10 (or the current code, if it moved).
2. A Bot bound as Profile `prepare` (AP Preparer) can call `tools.get_invoice` and cannot call `accrual.tools.create_accrual`.
3. A Bot bound as Profile `approve` cannot call `tools.get_invoice`.
4. Auditor Agent production Grants omit `get_audit_ground_truth`. Operational phase cannot open `ground_truth.json`.
5. Audit Report Agent and Close Manager have empty Connector lists.
6. `call_connected_tool` with an off-Grant name returns `forbidden` and writes no Kernel log result payload.
7. Two Display names cannot be attached to one slug as a union. The Slug map parser rejects a list of names where Profiles are required.
8. `create_accrual` without an idempotency key fails. A retry with the same key does not double-book.
9. Month-end still ends `BLOCKED` on the planted $12.40 cash break until a human mutates source objects and the host reruns. The extension does not clear unexplained cash.
10. No finance types appear under `.harness/Harness-v2/src`.

Until (1)–(4) work, do not claim the office is on Harness.

Live Pi turns that complete Handles remain a Harness proof. This layer adds Grant proofs on top.

---

## 14. Open risks

1. **In-memory AP overlay.** `register_runtime_invoice` does not edit `invoices.json`. A Sidecar restart drops ingested invoices unless overlay is persisted (§7.4).
2. **Cash `bind_case` and BS `bind_packets`.** Module globals assume one in-process turn. File-back them before more than one worker exists.
3. **Two close entrypoints.** Callers will confuse `run_cfo_close` with period lock. The extension must document and test against `close/month_end` only.
4. **Prompt plus tools duplication.** Many agents receive full evidence in the prompt and still have lookup tools. Leave it. Do not delete tools in the Compiler because they look redundant.
5. **Display name drift.** `close/checklist.py` `owner_agent` strings must stay equal to `Agent.name`. The Compiler should warn if a checklist owner is not in Grants.
6. **Harness skillPaths.** Harness v2 currently adds the whole `<computer>/skills` directory. cfo-agentic-system must filter. If Harness later adds per-Bot allowlisting, delete the duplicate filter rather than fight it.
7. **Profile transport.** Harness inbox items do not have a `profile` field today. Use wake-header or Handle-adjacent JSON until Harness grows the field. Do not fork Harness for this.
8. **Sample-data agents.** Empty Grants. They do not belong on the live floor. Keep them out of the Slug map unless you are generating fixtures.

---

## 15. Build order (when someone implements this)

Matches the load-bearing split: Kernel first, door second, Roster last.

1. Compiler: Catalog + Grants from constructors. Tests against §10.
2. Sidecar: read ops only. Grant check. kernel.log.jsonl.
3. Persist overlay / cash case / BS packets.
4. Pi `search_connected_tools` / `call_connected_tool` with Profile.
5. Write ops + idempotency + approval intercept for `create_accrual`.
6. Close host sends Handles using the Slug map. Python gates unchanged.
7. Strip evalOnly from production Grants. Isolation test.
8. Only then: Operator UI, Stripe as Connectors, Roster compaction.

Do not start with a new agent count. Do not start with a dashboard.

---

## Sources

- `docs/AGENTIC_SYSTEM_WORKFLOW.md`
- `docs/AGENTIC_SYSTEM_DIAGRAMS.md`
- `docs/integrations.md`
- `design-workshop/dominik/cfo-office-processes.md`
- `design-workshop/dominik/Data inputs and outputs.md`
- `GROK-WORKSHOP/harness-init/engineers/lark/HARNESS-V2.md`
- `skills/assignments.py`, `.cursor/rules/skills.mdc`
- Constructor files: `agent.py`, `invoice_ingestion/agents.py`, `accrual/agent.py`, `scheduling/agent.py`, `ar/agents.py`, `cash_recon/agent.py`, `prepaid/agent.py`, `fixed_assets/agent.py`, `bs_recon/agent.py`, `close/agents.py`, `reporting/agents.py`, `audit/agent.py`, `sample_data/agents/base.py`
- `close/gating.py`, `close/checklist.py`, `evaluation/isolation.py`
- `.harness/Harness-v2/README.md`, `extensions/index.ts`, `src/types.ts`, `examples/cfo-floor/harness/roster.json`

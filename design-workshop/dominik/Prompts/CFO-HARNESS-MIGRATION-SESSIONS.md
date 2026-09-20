# CFO Harness migration — Cursor session prompts

One pack. Thirteen fresh Cursor Agent sessions. Each session pastes **Constitution** first, then **one** session prompt. Do not merge sessions. Do not start a domain session before `00` has landed `office/constitution.md`.

This pack migrates the Office of the CFO off the in-process OpenAI Agents SDK control plane (that tree tried to be its own harness) and onto **Harness v2** as a Client system. The Python Kernel stays. Standing Bots, Handles, roster, Memory, Rooms, and Routines are Harness. Finance types never enter `.harness/Harness-v2/src`.

The product is **full replacement of a CFO team**. Not an assistant. Not a downsizing aid. No person is in the completion path. Verifier Bots are the concurrence. The human Operator is an emergency brake and a demo overlay.

Grain (who the Bots are): [`../cfo-bot-grain.md`](../cfo-bot-grain.md). Attach door: [`../../../docs/CFO_HARNESS_EXTENSION.md`](../../../docs/CFO_HARNESS_EXTENSION.md). Harness contract: [`../../../GROK-WORKSHOP/harness-init/engineers/lark/HARNESS-V2.md`](../../../GROK-WORKSHOP/harness-init/engineers/lark/HARNESS-V2.md). Layout: [`../../../docs/LAYOUT.md`](../../../docs/LAYOUT.md). Live Kernel: `.cfo/`. Live Harness: `.harness/Harness-v2`.

**`.harness/Harness-v2/examples/cfo-floor` is not this office.** Do not copy those six slugs. Do not design toward them.

---

## How to run

1. Open a **new** Cursor Agent chat on this repo. Do not continue an old thread.
2. Paste **Constitution** (the block under “Paste this first”).
3. Paste **exactly one** session prompt from `00` … `12`.
4. Let that session finish its proofs. Then start the next chat.

### Order

| When | Sessions | Why |
| --- | --- | --- |
| First, alone | `00` | Writes the law, Computer tree, roster skeleton, Bot MD template |
| Second, parallel | `01`, `02` | Client Pi extension + Kernel sidecar. Domain sessions read their output |
| Third, parallel | `03` `04` `05` `06` `07` `08` `10` `11` | File ownership does not overlap. Do not run two of these in one worktree |
| Fourth | `09` | Verifiers. Needs Operator Bots to exist so Handles have a destination |
| Last | `12` | Stitch, eval, disk proofs that the office runs with nobody in the queue |

If `01`/`02` are not done, a domain session still writes Bot files, Kernel adapters, and Grant fragments under `office/`. It does not invent a second bus.

### File ownership (do not cross)

| Session | May write |
| --- | --- |
| `00` | `office/**` (constitution, templates, roster skeleton, slug-map skeleton). Not Kernel math. Not Harness core |
| `01` | `office/computer/cfo/extensions/**`, catalog compiler, Client package.json. Not `.harness/Harness-v2/src/**` |
| `02` | `.cfo/` sidecar entry (`python -m cfo_kernel` or equivalent), RPC, idempotency, persistence of in-memory stores. Not Bot prose |
| `03` | `.cfo/invoice_ingestion/**`, `.cfo/integrations/**`, `office/bots/{email,stripe,bank,books}/**` |
| `04` | `.cfo/agent.py`, `.cfo/workflow.py`, AP tools/store that AP already owns, `office/bots/ap/**` |
| `05` | `.cfo/scheduling/**`, `office/bots/pay/**` |
| `06` | `.cfo/ar/**`, `office/bots/{apply,collect}/**` |
| `07` | `.cfo/cash_recon/**`, `office/bots/cash/**` |
| `08` | `.cfo/close/**`, `.cfo/accrual/**`, `.cfo/prepaid/**`, `.cfo/fixed_assets/**`, `.cfo/bs_recon/**`, `office/bots/close/**` |
| `09` | `office/bots/{ctl-pay,ctl-cash,ctl-books}/**`, Client intercept that sends concurrence to those slugs, Kernel queue-owner remap. Not Harness core types |
| `10` | `.cfo/reporting/**`, `office/bots/story/**` |
| `11` | `.cfo/audit/**`, `office/bots/audit/**` |
| `12` | Tests under `office/` and glue eval. May patch collisions. May not reopen grain |

Do not edit `Operator-workspace/`. Do not edit `.harness/Harness-v2/src` unless `12` finds a Harness bug that blocks Client routing; prefer Client code.

---

## Paste this first — Constitution

Copy everything in this section into **every** fresh session as message one.

```text
You are a Cursor Agent on the git repo hackmit26. This session is one slice of a migration. Obey this Constitution even if a later message is tempting.

## Product
You are building a Client system on Harness v2 that fully replaces an Office of the CFO. Not a copilot. Not a staffing reduction. The office must complete AP, AR, cash, close, reporting, and audit with zero humans in the completion path.

Uncertain or high-stakes work goes to a Verifier Bot (ctl-pay, ctl-cash, ctl-books). It never asks a person. It never calls ask_user to get unblocked. It never waits on HUMAN_REVIEW as a human queue. Kernel statuses named HUMAN_REVIEW may remain as fail-closed outcomes; the queue owner is a Verifier Bot.

The Harness "Operator" (human HTTP/control plane) is an emergency stop and a demo overlay. It is not a worker.

## What you are migrating off
The current Python tree under .cfo/ used the OpenAI Agents SDK as a private harness: Agent() objects, Runner, in-process handoffs, CLI review commands. That control plane is being destroyed. Do not port it.

Keep the Kernel: arithmetic, candidates, cents, must_hold, evaluate_close_gates, period lock math, eval isolation, stores under .cfo/data and .cfo/runs.

## What you are migrating onto
Harness v2 at .harness/Harness-v2. Named Bots, one Computer, Handles (accept ≠ complete), inboxes, Rooms, per-Bot Memory, Routines, headless HTTP. Pi is the turn engine inside a Bot. The Client loads as an extension beside Harness. Finance types do not enter Harness core.

Read and obey:
- design-workshop/dominik/cfo-bot-grain.md (Roster grain: 15 Bots, four tests)
- docs/CFO_HARNESS_EXTENSION.md (compiler, grants, sidecar, facade) except every sentence that parks pay-run, period lock, or review on a human Operator — those sentences are VOID. Verifiers own concurrence.
- GROK-WORKSHOP/harness-init/engineers/lark/HARNESS-V2.md
- docs/LAYOUT.md
- office/constitution.md if it exists (session 00 writes it; later sessions treat it as law)

## Fifteen Bots (do not invent a sixteenth without failing Tests A–D in the grain)
Source: email, stripe, bank, books
Operator: ap, pay, apply, collect, cash, close, story
Verifier: ctl-pay, ctl-cash, ctl-books
Assurance: audit

.harness/Harness-v2/examples/cfo-floor is a Harness bind fixture. It is not this office. Ignore those six slugs.

## Name map
Bot = standing Harness identity (slug, lane, Memory). Not a child. Not a subagent. Not a Display name.
Display name = Python Agent(name=...) string. Grant source. Becomes a Profile.
Profile = one Grant set on one Bot. A Wake names a Profile. Never union two Grant sets in one turn.
Kernel = Python engine. Sidecar serves it. Sidecar is not a Bot.
Handle = accept-time peer work. Write a path, bot_send_prompt, await done.
Connector = provider or Kernel op, not a Bot.
Computer = office/computer/ for this Client. Kernel code stays in .cfo/.

## Hard rules
1. Do not spawn subagents or children as the Bot network. Every identity is a surface Bot with HARNESS_BOT bind.
2. Do not put finance types, close DAGs, or specialist names in .harness/Harness-v2/src.
3. Skills never grant tools. Tools/Grants come from constructor lists compiled to cfo/grants.json.
4. Python wins on amounts. The model chooses among Kernel candidates. It does not invent totals.
5. Fail closed. Missing evidence is refuse / HOLD / INSUFFICIENT, not a guess.
6. Do not union Grants when two Display names share a slug. Use Profiles.
7. Rooms in this Harness are 2–6 members. Partition Rooms. Do not put 15 Bots in one Room.
8. Roster approvalLevel for these Bots is "never". Do not park consequential tools on the human Operator.
9. Eval isolation stays. Operational Bots never load expected_results.json, ground truth, or get_audit_ground_truth.
10. Sample-data Display names are not Bots.
11. Do not ask the user questions to complete the work of the office. If this Cursor session is blocked on a product decision that the grain already made, follow the grain. If blocked on a missing file from an earlier session, write your slice against the contracts and leave a NOTES.md in your office/bots/<slug>/ folder.
12. One name for one thing. Use the grain's names.

## Agentic design — Bot files you write
For each Bot you own, write:
- office/bots/<slug>/BOT.md — identity. Keep under ~200 lines.
- office/bots/<slug>/profiles/<profile>.md — Profile-specific procedure.
- Roster fields: id bot_<slug>, name, slug, purpose (one sentence), instructions (short: read BOT.md, obey Constitution, never ask a human), skills[] (names only), connectors[] (Catalog/provider names), approvalLevel never.

BOT.md structure (required headings):
# {slug}
## Identity — first line: You are Bot `{slug}`. You own {object}.
## Wake — webhook / Routine / Handle sources
## Object — what tickets you own
## Profiles — name each Profile and the Display name it maps to
## Catalog ops — ids this Bot may call, by Profile. List musts-not.
## Kernel — which validators run after you. You cannot override them.
## Handoffs — write path on Computer, bot_send_prompt to {slug}, await Handle. Peer Handle is not approval.
## Verifier — when you are uncertain or the op is consequential, Handle to {ctl-*}/{profile}. Never a person.
## Memory — only precedents about your object. Never another Bot's Memory. Never source objects you do not own.
## Must not — explicit. Include: do not ask a human; do not spawn children; do not invent amounts.
## Done when — object-level exit criteria.

Prompt engineering for those files:
- No "you are a helpful assistant". No "ask the user if unsure". No "escalate to management" unless the named Verifier slug is that management.
- Uncertainty policy is operational: call the Kernel op, then if the Kernel returns a fail-closed status, Handle to the Verifier with the packet path. Do not chat.
- Do not paste full evidence into instructions. Wake text names a path. Tools fetch facts. Duplicating both is slop.
- Do not copy SAFETY text into a skill. Skills are reusable judgment procedures. SAFETY / must-not lives on BOT.md once.
- Skill descriptions are third person, WHAT + WHEN, so Pi discovery works. SKILL.md under 500 lines; details in sibling reference.md.
- Skills stay assigned via .cfo/skills/assignments.py for Kernel-side compose if you still generate Display-name prompts, and via roster.skills / Computer skills/ for Pi. One logical skill, two loaders, same files when possible (Computer may symlink or copy).
- Output: keep existing Pydantic output_type names as the contract the Kernel validator already understands. Do not invent a parallel JSON dialect.
- Verifier BOT.md tone: find reasons to refuse. Concur only when the Kernel already allows AND the packet is complete. You are not a rubber stamp. You must not hold the Operator Bot's write Grants.
- Source BOT.md tone: land and classify. You do not match, pay, apply, accrue, or lock.
- Write as if the Bot will run unattended for a month.

## Code
- Do not reimplement match/accrual/close math in TypeScript.
- TypeScript Client code: Google TS style; explicit return types; no any; no finance types in Harness core.
- Persist anything that is today in-memory (AP overlay, cash bind_case, BS packets) before multi-process Bots share it. If you touch that store, write it to disk under the Computer/runs tree atomically.
- Idempotency keys on writes.
- After a mutating Kernel op, existing Python validators still run.
- Output everything in the following directory: .cfo-v2

## Proofs
Every session ends with a short office/bots/<slug>/PROOF.md (or office/sessions/NN-PROOF.md) listing commands you ran and what disk looked like. If you cannot run Pi live, prove at the Kernel/unit layer and state that Handle completion was not live-proven.

## Stop conditions
If you are about to add a Bot, run Tests A–D from the grain. If you are about to ask a human to approve a bill, stop and route to ctl-pay. If you are about to edit Harness core to know what an invoice is, stop.
```

---

# Session 00 — Constitution on disk

Paste after Constitution.

## Job

Materialize the Client-system law on disk so every later session has a file to obey. You create the Computer tree, the fifteen-Bot roster **skeleton**, the slug-map skeleton, Bot MD templates, Room partition, Routines, and `office/constitution.md` (a durable copy of the Constitution plus SUPERSEDES). You do not migrate Kernel workflows. You do not write the Pi facade. You do not copy `examples/cfo-floor`.

## Read first

- `design-workshop/dominik/cfo-bot-grain.md` (entire)
- `docs/CFO_HARNESS_EXTENSION.md` (Computer layout, slug-map schema, SUPERSEDE human gates)
- `.harness/Harness-v2/src/types.ts` (`BotRecord`, `RoomRecord` 2–6 members, `RoutineRecord`, `ApprovalLevel`)
- `.harness/Harness-v2/src/roster.ts`
- `docs/LAYOUT.md`
- `.cfo/skills/assignments.py` (Display names only; do not re-architect)

## Write

```
office/constitution.md          # law, SUPERSEDES list, name map, 15 slugs
office/SUPERSEDES.md            # explicit voids (see below)
office/templates/BOT.md         # the heading template from Constitution
office/computer/harness/roster.json
office/computer/cfo/slug-map.json
office/computer/cfo/catalog.json   # empty ops: [] placeholder, version 1
office/computer/cfo/grants.json    # empty agents: {} placeholder
office/bots/<each slug>/BOT.md     # stub identity from grain tables; later sessions replace body
office/sessions/00-PROOF.md
```

### SUPERSEDES (must list)

- `.cfo/README.md` language that human review is a first-class completion state
- `docs/CFO_HARNESS_EXTENSION.md` sentences that park pay-run, period lock, or review on the human Operator
- CLI commands whose happy path is a person mutating a review queue (`ar-review-correct`, close `--resolve` as a human) — they may remain as **eval fixtures / emergency tools**, not as the office’s completion path
- In-process `Runner` as the Bot bus
- Any design that uses `examples/cfo-floor` as the Roster

### roster.json rules

- `system`: `cfo-agentic-system`
- Fifteen bots. Slugs exactly as grain. `id`: `bot_<slug>` with hyphen slugs using underscore in id (`bot_ctl_pay` for `ctl-pay`) — pick one scheme, document it, stay consistent with Harness slug matching
- `approvalLevel`: `"never"` on all fifteen
- `instructions`: two to five sentences. Point at `office/bots/<slug>/BOT.md`. Say: never ask a human; Verifier slug if named in grain
- Rooms (each 2–4 members, never more than 6):
  - `intake`: email, stripe, bank, books
  - `pay`: ap, pay, ctl-pay
  - `cash`: apply, collect, cash, ctl-cash
  - `books-close`: close, ctl-books, story, audit
- Routines (wake the owning Bot; not a human ticket):
  - `weekly-pay-run` → `pay`
  - `daily-aging` → `collect`
  - `month-end` → `close`
  - `post-close-assurance` → `audit`
- `computer`: the Computer root you created (`office/computer`)

### slug-map.json rules

Map every grain Profile. No list-unions. `defaultProfile` required on every slug. Include `stripe` Profile `payout` even though no Display name exists yet (leave a comment in constitution; grants may be empty until session 03).

Do not overwrite a later session’s BOT.md if you re-run; this session only creates stubs if missing.

## Proofs

- `python` or `node` parse of roster JSON. If you can, run Harness roster parse against it (import `parseRoster` or a small script). Rooms must have 2–6 members.
- Grep the roster: no slug `ingest`. No `examples/cfo-floor` paths.
- Every slug in grain has a `BOT.md` stub and a roster row.

## Forbidden

- Implementing tools, sidecar, or Pi extension
- Adding Bots
- Putting 15 members in one Room
- `approvalLevel` `ask` or `always`

---

# Session 01 — Client attach (compiler + Pi facade)

Paste after Constitution.

## Job

Build the Client-system door onto Harness v2: catalog compiler, grants, `search_connected_tools` / `call_connected_tool`, bind-time Grant filter, skill intersect, and routing of consequential ops to **Verifier Bots** (not `ask_user`). Harness core stays ignorant of invoices.

## Read first

- `docs/CFO_HARNESS_EXTENSION.md` (compiler, catalog schema, facade, bind)
- `office/constitution.md`
- `.harness/Harness-v2/extensions/index.ts` (how Harness itself extends Pi — copy the *pattern*, do not edit unless a hook is missing; prefer a second `-e` path)
- `.harness/Harness-v2/src/bind.ts`, `src/prompt.ts`, `src/approvals.ts`
- `.cfo/agent.py` and `.cfo/skills/assignments.py` (compiler input examples)
- `.cursor/rules/skills.mdc`

## Write

```
office/computer/cfo/extensions/index.ts    # Pi extension
office/compiler/                           # cfo-catalog compile
office/computer/cfo/catalog.json           # first real compile
office/computer/cfo/grants.json
office/sessions/01-PROOF.md
```

Load with Harness, conceptually:

`pi -e .harness/Harness-v2/extensions/index.ts -e office/computer/cfo/extensions/index.ts`

(Exact CLI flags: read Harness README / `bin` / `src/cli.ts`. Do not guess a flag that does not exist.)

## Behavior

1. Compiler reads `.cfo/**/agent.py`, `agents.py`, named tool lists, `@function_tool` signatures, `assignments.py`. Writes catalog + grants. Fail closed if `tools=` cannot be resolved. No implicit “all tools”.
2. Catalog ids are `{module}.{function}` because `get_bank_transaction` collides across modules.
3. On `HARNESS_BOT` bind: resolve slug → Profile → Grant set. Register only those ops, or one `call_connected_tool` that refuses off-grant names.
4. `search_connected_tools({ query })` filtered by this Bot’s active Profile.
5. Computer `skills/` **intersect** `bot.skills`. Today Harness may load the whole skills dir; this extension must filter.
6. Consequential ops (`side-effect-external`, period lock, pay-run release, write-off, `create_accrual`) do **not** go to the human Operator. They create/await a Handle on `ctl-pay` / `ctl-cash` / `ctl-books` per grain. If Harness intercept only knows Operator, wrap it in Client code. Do not add `Invoice` to Harness types.
7. Protocol tools stay Harness: `bot_send_prompt`, rooms, memory.
8. `get_audit_ground_truth` is `evalOnly`. Production grants omit it.
9. TypeScript: explicit return types, no `any`, no finance domain types in files under `.harness/Harness-v2/src`.

## Proofs

- Compile over `.cfo` exits 0 and lists AP Preparer ≠ AP Approver grants.
- A fake bind as `ap` / Profile `prepare` cannot see `create_accrual`.
- A fake bind as `audit` in operational phase cannot see `get_audit_ground_truth`.
- Document how Verifier routing works in `office/sessions/01-PROOF.md`. If Harness cannot yet retarget intercept, implement the Client workaround and say so.

## Forbidden

- Forking Harness to know ledgers
- Unioning grants for a slug
- `ask_user` as the pay-run or lock path
- Rewriting Kernel math

---

# Session 02 — Kernel sidecar

Paste after Constitution.

## Job

Expose the existing `.cfo` engine as a sidecar process the Pi facade can call. Multi-Bot, multi-process. Re-check grants in the Kernel. Persist stores that are process-local today. Do not reimplement accounting in TypeScript. Do not bind `HARNESS_BOT`.

## Read first

- `docs/CFO_HARNESS_EXTENSION.md` § Kernel RPC, idempotency, eval isolation
- `office/constitution.md`
- `.cfo/` entrypoints: `workflow.py`, `close/gating.py`, `close/month_end.py`, `evaluation/isolation.py`
- In-memory / session risks: AP overlay in invoice ingestion, cash `bind_case`, BS packets (search `.cfo` for in-memory, overlay, bind_case, bind_packets)

## Write

- `python -m cfo_kernel` (package under `.cfo/`, name as you must for PYTHONPATH)
- RPC: `{ op, args, botId, slug, profile, handleId, idempotencyKey }` → `{ ok, result | error }`
- Grant re-check against `office/computer/cfo/grants.json` + slug-map Profile
- Atomic idempotency dir on the Computer
- Disk persistence for any store a second process must see
- `CFO_EVAL_PHASE=operational` by default for live Bots
- `office/sessions/02-PROOF.md`

DATA_DIR / runs root: Computer or `.cfo/data` + `.cfo/runs` with env pointed at the Computer. Document the choice. Later sessions must use the same env.

## Behavior

- After mutating ops, existing validators still run. The model cannot talk past `must_hold` or a failed `evaluate_close_gates`.
- Same idempotency key + different body → error.
- Sidecar does not drain inboxes.
- Close: one lock door is `close/month_end`. The other close entrypoint is a test packet, not a second period lock. Document which RPC name locks.

## Proofs

- RPC read op works against seeded data.
- Forbidden op for slug `audit` / profile `interpret` on `create_accrual` returns `forbidden` with no write.
- Kill the sidecar, start it again, an overlay/case you persisted is still there.
- Eval isolation: operational phase cannot open answer keys.

## Forbidden

- Making the sidecar a Bot
- Auto-posting when Kernel says HUMAN_REVIEW / HOLD / BLOCKED
- Loading ground truth in operational phase

---

# Session 03 — Source Bots (email, stripe, bank, books)

Paste after Constitution.

## Job

Migrate ingestion and integrations into four Source Bots. They land objects and send Handles. They do not match, pay, apply, accrue, or lock. Email and Stripe wake on webhooks. Stripe never produces `InvoiceCandidate`.

## Read first

- Grain § Source Bots
- `.cfo/invoice_ingestion/agents.py`, `tools.py`, `store.py`, `models.py`
- `.cfo/integrations/providers/__init__.py` (`WEBHOOK_PROVIDERS`, `INVOICE_PROVIDERS`, `CASH_PROVIDERS`, `SYNC_PROVIDERS`)
- `.cfo/integrations/providers/stripe.py` (module docstring: never produces InvoiceCandidate)
- `.cfo/skills/assignments.py` source Display names

## Bots you own

| Slug | Profiles (Display names / new) | Connectors |
| --- | --- | --- |
| `email` | invoice, employee, portal, document | gmail, outlook; employee upload; vendor portal PDF; mailroom |
| `stripe` | payout (new) | stripe, adyen |
| `bank` | card ← Bank/Card Discovery Agent | bank feed / poll (no webhook in registry — poll is the Wake) |
| `books` | erp-invoice, procurement, edi | xero webhook; netsuite + coupa sync |

## Migrate

- Replace in-process source `Agent()` runs with: webhook/poll → wake Source Bot → tools via sidecar → write Computer path → `bot_send_prompt` to `ap` (bill) or `apply` (remittance) or `cash` (deposit) or `collect`/`close` as grain § Wakes.
- Persist canonical invoice registry (today: in-memory overlay that dies with the process). Multi-Bot requires disk.
- Stripe/Adyen: unpack payout waterfall in Kernel (already there). Bot `stripe` explains and hands deposit to `cash` and charge-level facts to `apply`.
- Bank: a charge is not a bill. `invoice_missing` stays on `bank`.
- Structured ERP/EDI/Coupa: Python parse wins; the Bot does not remap filled fields.

## Prompt engineering (sources)

- First line: You own messages / payouts / bank lines / GL rows. You do not own open bills.
- Classification: if not an invoice, candidate is null. Short factual reason. No CoT dump.
- Email carries two Pipes. Classify destination. Do not split into email-ap and email-ar Bots.
- Never call AP record tools, `create_accrual`, or pay-run ops.

## Write

- Full `office/bots/{email,stripe,bank,books}/BOT.md` + profile md
- Kernel persistence + webhook → Handle glue (Client, not Harness core)
- Update slug-map Profiles if 00 left stripe empty
- `office/sessions/03-PROOF.md`

## Proofs

- Stripe fixture payout does not create an InvoiceCandidate.
- Email invoice path writes a file and would address `ap` (prove the send payload even if Pi is fake).
- Email remittance path addresses `apply`.
- Bank charge without supporting docs stays `invoice_missing`.
- Canonical identity: same AWS bill from two sources is one invoice (existing Kernel test — keep it green).

## Forbidden

- A fifth Source Bot for EDI/portal
- Source Bot approving a bill
- Using `ingest` as a slug

---

# Session 04 — Operator Bot `ap`

Paste after Constitution.

## Job

Migrate AP matching off the five-lane in-process team onto Bot `ap` with Profiles `prepare` and `investigate`. Concurrence is **not** yours. You send approve-shaped drafts to `ctl-pay`. You do not release cash.

## Read first

- Grain § Operator `ap` and SoD
- `.cfo/agent.py`, `.cfo/workflow.py`, AP `tools.py` / evidence collectors
- Constructor Grants: Preparer = RECORD_TOOLS; Investigator = RECORD + POLICY; Reviewer/Approver/Audit are **not this Bot**

## Profiles

- `prepare` ← AP Preparer
- `investigate` ← Exception Investigator (only when exceptions exist)

Do not put AP Reviewer, Approver, or AP Audit Grants on `ap`. Session 09 owns those on `ctl-pay`.

## Migrate

- Destroy in-process calls Preparer → Reviewer → Approver → Audit as Python function chaining.
- Flow: Kernel evidence → Wake `ap`/`prepare` → maybe `ap`/`investigate` (same Bot, **replace** Grant set for the turn, no union) → write packet path → Handle `ctl-pay` / `review-match`.
- Python `must_hold` still vetoes APPROVE.
- Approved bills enter the pay pool only after Verifier concurrence **and** Kernel allow. Until 09 exists, write the Handle payload and do not auto-APPROVE past a missing Verifier.

## Prompt engineering

- You match a vendor claim to PO and receipt. You do not pay.
- Investigator adds policy/precedent tools. Still not concurrence.
- If Kernel says must-hold, you HOLD. You do not bargain with a human.
- Packet path is the handoff. Do not paste the invoice into Memory.

## Write

- `office/bots/ap/**`
- Workflow host that wakes Harness instead of `Runner.run_sync` (or a Kernel “next wake” record 01/02 can execute)
- Keep AP unit tests green
- `office/sessions/04-PROOF.md`

## Proofs

- INV-001 still can APPROVE at Kernel layer.
- INV-018 duplicate still HOLD.
- Grant: `ap`/`prepare` cannot call Approver-only policy set if that split exists; `ap` cannot call `create_accrual`; `ap` cannot call pay-run release.
- No `ask_user` in the AP path.

## Forbidden

- Union prepare + approve on one turn
- Paying vendors
- Human review CLI as success path

---

# Session 05 — Operator Bot `pay`

Paste after Constitution.

## Job

Migrate payment scheduling onto Bot `pay` Profile `schedule`. Cash leaving the company is high-stakes. You propose a week. You do not concur. `ctl-pay` / `review-pay` concurs. Kernel policy net still strips illegal pays. No bank execution.

## Read first

- Grain why `pay` is not a Profile on `ap`
- `.cfo/scheduling/agent.py`, tools, policy net
- Display names: Payment Scheduler (yours), Payment Audit (session 09). **They share tools today.** You must not give `pay` a union with audit. Tighten `review-pay` later in 09 via catalog.overrides if needed. Your Bot only schedules.

## Migrate

- Weekly Routine already in roster (00). Implement the wake body: load pool + cash → Kernel candidates → Bot chooses plan → Kernel `apply_cash_and_policy_net` → Handle `ctl-pay`/`review-pay` with plan path.
- Identified wires after concurrence go to `cash` as expected outflows.

## Prompt engineering

- First line: You own the payment-run draft. You do not own three-way match. You do not move money.
- You never “just this once” breach reserve.
- If cash is short, defer. Do not ask a treasurer (there is none).

## Write

- `office/bots/pay/**`
- Scheduling host → Handle
- `office/sessions/05-PROOF.md`

## Proofs

- Seeded schedule still defers INV-009-class unnecessary early pay if that fixture still exists.
- Policy net still strips HOLD invoices.
- `pay` cannot load AP RECORD_TOOLS.
- No human in the path.

## Forbidden

- Executing ACH/wire
- Self-approving the plan
- Merging this Bot into `ap`

---

# Session 06 — Operator Bots `apply` and `collect`

Paste after Constitution.

## Job

Migrate AR cash application and collections onto two Bots. They are different open items. Collections must not run ahead of application. Material/ambiguous apply goes to `ctl-cash`. Write-off/reserve goes to `ctl-pay`. No person in the queue.

## Read first

- Grain § apply vs collect; process doc AR stages
- `.cfo/ar/agents.py`, tools, validators, `HUMAN_REVIEW` statuses
- Collections `enforce_collection_decision`

## Bots

| Slug | Profile | Display name |
| --- | --- | --- |
| `apply` | `apply` | Cash Application Agent |
| `collect` | `chase` | Collections Agent |

Cash Application Reviewer is **not** yours. Session 09 → `ctl-cash` / `review-apply`.

## Migrate

- Incoming remittance Handle from `email` / `stripe` / `bank` → `apply`. Kernel candidates → Bot proposal → validator. AUTO_APPLY may post. Fail-closed statuses become a Handle to `ctl-cash`, not a human CLI (`ar-review-correct` is emergency only).
- Aging Routine → `collect` only after `apply` has drained new deposits for that as-of (encode the gate in Kernel or in collect BOT.md + a Kernel check).
- Do not grant apply the collections tools or vice versa.

## Prompt engineering

- `apply`: You own unapplied cash. You stick money to invoices. You do not dun customers.
- `collect`: You own open invoices **after** application. You do not invent that someone unpaid if unapplied cash might be theirs — if aging is dirty, Handle `apply` first.
- Both: never “ask the AE”. There is no AE.

## Write

- `office/bots/apply/**`, `office/bots/collect/**`
- Persist `runs/ar/state.json` (already disk — keep it the SoT)
- `office/sessions/06-PROOF.md`

## Proofs

- Planted ambiguous remittance does **not** AUTO_APPLY (existing eval). Prove it becomes a Verifier Handle payload, not a human queue item.
- Collections cannot chase paid/disputed/cooldown (existing enforce).
- Apply cannot call `create_accrual` or pay-run.

## Forbidden

- One Bot `ar`
- Treating HUMAN_REVIEW as “post anyway because we are autonomous”
- Human `ar-review-correct` as the demo success path

---

# Session 07 — Operator Bot `cash`

Paste after Constitution.

## Job

Migrate bank reconciliation onto Bot `cash` with Profiles `match` and `investigate`. Trusted cash is the object. Sign-off is `ctl-cash` / `review-rec`. The $12.40 unexplained difference stays unexplained until source objects change. Autonomy is not “force MATCHED”.

## Read first

- Grain § cash
- `.cfo/cash_recon/agent.py`, tools, validators
- Stripe payout path from session 03 / integrations
- Close gate that cash must tie

## Profiles

- `match` ← Cash Reconciliation Preparer
- `investigate` ← Cash Exception Investigator

Reviewer Display name → session 09.

## Migrate

- Persist `bind_case` / session case so a second process can investigate.
- Proposed fee journals are never auto-posted (existing rule). Verifier + Kernel.
- Period cannot report RECONCILED if arithmetic does not tie.

## Prompt engineering

- You own unmatched bank lines. You do not own vendor bills. You do not pay. You do not apply AR except to trust identifiers AR already wrote.
- Rule from the process doc: the pipe that owns the counterparty identifies the line; you check the bank agrees.
- $12.40: if Kernel has no candidate, you do not invent one. Handle `ctl-cash`. If Verifier also cannot, the period stays open. That is correct replacement of a controller — a controller would also refuse to lie.

## Write

- `office/bots/cash/**`
- Persistence
- `office/sessions/07-PROOF.md`

## Proofs

- Seeded $12.40 still not MATCHED.
- Stripe payout tie still uses Kernel waterfall math.
- `cash` cannot `create_accrual` or release pay-run.

## Forbidden

- Auto-posting fee journals
- Clearing a break by editing the statement in Memory
- Human “resolve” as success

---

# Session 08 — Operator Bot `close`

Paste after Constitution.

## Job

Migrate month-end treatments and coordination onto Bot `close` with Profiles `accrue`, `prepaid`, `assets`, `bs`, `coordinate`. One Wake (month-end Routine). **Different Grants per Profile — never union.** Lock is not yours. `ctl-books` / `lock` concurs after `evaluate_close_gates` passes. Accrual is the Profile that may `create_accrual`.

## Read first

- Grain § close Profiles
- `.cfo/close/agents.py`, `checklist.py`, `gating.py`, `month_end.py`, orchestrator (know the two entrypoints; lock only through month_end)
- `.cfo/accrual/agent.py` (twelve tools including writes)
- `.cfo/prepaid/agent.py`, `.cfo/fixed_assets/agent.py`, `.cfo/bs_recon/agent.py`

## Profiles

| Profile | Display name | Write? |
| --- | --- | --- |
| `accrue` | Accrual Agent | `create_accrual`, reconcile with invoice |
| `prepaid` | Prepaid Preparer | no new math; Kernel schedules |
| `assets` | Fixed Asset Preparer | Kernel depreciation |
| `bs` | BS Recon Preparer | classify packet |
| `coordinate` | Close Manager (`tools=[]`) | none — Routine + `ready_tasks` |

Reviewer twins and Month-End Close Reviewer → session 09 `ctl-books`.

## Migrate

- Close Manager is not a sixteenth Bot. `coordinate` is a Profile or a pure Routine body that reads `ready_tasks` and sends Handles to the next Profile on **this same Bot** (new Wake, new Profile, no Grant union).
- One Kernel lock door.
- Close stays BLOCKED on planted $12.40, unmatched AR, missing prepaid evidence until **source objects** change. Verifier cannot override gates. A later “human mutate source” eval becomes: a Source or Operator Bot mutates **source** via legal Kernel ops, then rerun. If no legal op exists, the period stays BLOCKED. Replacement of a team includes leaving the books open when they are wrong.

## Prompt engineering

- You own period completeness, not Friday’s wire.
- Accrue: choose among named Kernel estimates. Do not invent amounts. Current-period invoice → no accrual.
- Coordinate: you do not mark CLOSED.
- After treatments, Handle `ctl-books` with the pack path.

## Write

- `office/bots/close/**` including one profile md each
- Host that sequences Profiles as separate Wakes
- `office/sessions/08-PROOF.md`

## Proofs

- Default September close still BLOCKED on $12.40 until source mutation.
- `close`/`prepaid` cannot call `create_accrual`.
- `close`/`coordinate` has no mutating Catalog ops.
- Journals stay balanced (existing tests).

## Forbidden

- Four extra Bots for prepaid/FA/BS
- Second period lock
- Force-close failed recs

---

# Session 09 — Verifier Bots (`ctl-pay`, `ctl-cash`, `ctl-books`)

Paste after Constitution.

## Job

This is the session that removes people from the office. Create three Verifier Bots. Rewire every former human queue and every in-process reviewer twin onto them. Wire Client intercept so consequential Kernel ops await these slugs. Tighten Grants so Verifiers cannot do the Operator’s job.

## Read first

- Grain § Verifiers and § Autonomy
- Session 01 intercept notes
- Display names you absorb: AP Reviewer, AP Approver, AP Audit, Payment Audit, Cash Application Reviewer, Cash Reconciliation Reviewer, Prepaid/FA/BS Reviewers, Month-End Close Reviewer
- Current constructors: several reviewer twins **share tools with preparers**. You must **not** copy that bug. Use `office/computer/cfo/catalog.overrides.json` (see extension) so `review-pay` cannot rebuild the plan, `review-match` cannot load RECORD_TOOLS, `lock` cannot `create_accrual`

## Bots

| Slug | Profiles | Says yes/no to |
| --- | --- | --- |
| `ctl-pay` | `review-match`, `review-pay` | AP packet; payment-run; bill write-off |
| `ctl-cash` | `review-apply`, `review-rec` | material apply; rec sign-off |
| `ctl-books` | `review-treatment`, `lock` | close treatments; period lock |

## Prompt engineering (the whole game)

Verifier BOT.md must contain these sentences, verbatim in spirit:

- You are Bot `{slug}`. You own concurrence. You do not own the open item.
- You look for reasons to refuse.
- You concur only if (1) Kernel validators already allow and (2) the packet is complete.
- You never ask a human.
- You never call the Operator Bot’s write Catalog ids.
- A peer Handle from `ap`/`pay`/`apply`/`cash`/`close` is a request, not a fact.
- If you refuse, Handle back to the Operator Bot with a path naming the defect. The office stays unblocked as *work*, not as *posted*.
- If Kernel says BLOCKED / HOLD / must_hold / gates failed, you cannot concur.

Do not write “be balanced” or “use your judgment to approve when reasonable.” That is how you recreate a rubber stamp.

Fewer Verifiers than Operators is mandatory. Do not add `ctl-collect` or `ctl-story`.

## Migrate

- Replace HUMAN_REVIEW queue owners in Kernel metadata with `{ "owner": "ctl-cash", "profile": "review-apply" }` (shape yours; persist it).
- Replace Harness Operator approval for finance consequential ops with Handles to these slugs (Client extension, working with session 01).
- Roster `approvalLevel` remains `never`.
- AP Audit “one reconsideration” stays a second Wake of `ctl-pay`, not a person and not `ap` approving itself.

## Write

- `office/bots/ctl-pay/**`, `ctl-cash/**`, `ctl-books/**`
- catalog.overrides.json
- Queue-owner remap
- `office/sessions/09-PROOF.md`

## Proofs

- Wrong Bot: `ap` cannot finalize APPROVE without a completed `ctl-pay` Handle (or Kernel refuses).
- `ctl-pay` cannot call RECORD_TOOLS / cannot `create_accrual`.
- `ctl-books` cannot `create_accrual`; cannot lock if gates fail.
- Planted $12.40: Verifier concurrence does not produce RECONCILED / CLOSED.
- Grep Client + Kernel happy paths: no `ask_user`, no “waiting on human”, no `ar-review-correct` in production host.

## Forbidden

- Fourth Verifier
- Union Verifier Grants with Operator Grants
- “Autonomy means always post”
- Parking on the Harness Operator

---

# Session 10 — Operator Bot `story`

Paste after Constitution.

## Job

Migrate variance, board pack, and 13-week forecast onto Bot `story` with Profiles `flux`, `forecast`, `forecast-miss`, `board`. This Bot does not move money. No dedicated reporting Verifier. `audit` samples the pack. Python owns every total.

## Read first

- Grain § story
- `.cfo/reporting/agents.py`, tools, forecast immutability
- `docs/reporting.md` if present

## Profiles

- `flux` ← Variance Analysis Agent
- `forecast` ← Cash Forecast Agent
- `forecast-miss` ← Forecast Variance Agent
- `board` ← Board Reporting Agent

Drop Reporting Reviewer Agent and Forecast Reviewer Agent as lanes. If you keep a `critique` Profile on **this same Bot**, it is optional self-check with the **same read Grants**, not a second identity. Prefer not to. Audit is the other pair of eyes.

## Migrate

- Wake from close pack path after `ctl-books` lock **or** from a Routine that reads last locked period (story may draft before lock but must label numbers as unlocked).
- Forecast snapshots stay immutable under `runs/reporting/forecasts/`.
- Agents narrate; they do not re-sum.

## Prompt engineering

- You own the story of the books. You do not own the books.
- Every claim needs an evidence id the Kernel already produced. Unsupported claims are omitted, not guessed.
- You do not ask a CFO to “review the deck.” You write the pack. Audit may find you.

## Write

- `office/bots/story/**`
- `office/sessions/10-PROOF.md`

## Proofs

- Existing reporting tests still pass (contributor sums, week roll-forward).
- `story` has no mutating finance Catalog ops.
- Board output only uses evidence ids from tools.

## Forbidden

- Making `story` a Verifier
- Inventing flux dollars
- Human sign-off on the pack as completion

---

# Session 11 — Assurance Bot `audit`

Paste after Constitution.

## Job

Migrate independent audit onto Bot `audit` with Profiles `interpret` and `report`. After-the-fact. Not a pay-path Verifier. Does not rewrite operational source objects. Production Grants omit `get_audit_ground_truth`.

## Read first

- Grain § audit
- `.cfo/audit/agent.py`, tools, `evaluation/isolation.py`
- Controls IDs in workflow docs

## Profiles

- `interpret` ← Auditor Agent (read Catalog ops; strip evalOnly in production)
- `report` ← Audit Report Agent (`tools=[]` today — keep report language from `ReportStats` only)

## Migrate

- Routine `post-close-assurance` wakes `audit` on the pack + protocol tail (`bot_get_agent_transcript_tail`).
- Writes under `workspace/audit/` and `runs/audit/` only. Path leases.
- Python still samples and re-performs. The Bot interprets severity and writes findings from Kernel finding IDs.

## Prompt engineering

- You own findings. You do not own pay-run. You do not concur for `ctl-*`.
- You do not fix the books. You write what is wrong.
- If finding IDs are missing, refuse the sentence. Do not invent fraud.
- You never open ground truth in operational phase.

## Write

- `office/bots/audit/**`
- Production vs eval Grant split
- `office/sessions/11-PROOF.md`

## Proofs

- Operational grant file does not contain `get_audit_ground_truth`.
- Audit tests still require planted issues to surface as findings without mutating AP source invoices.
- `audit` cannot `create_accrual` or write `runs/ar/state.json`.

## Forbidden

- Using audit as the pay-run approver
- Eval tools in production
- Editing another Bot’s Memory

---

# Session 12 — Stitch and prove the office

Paste after Constitution.

## Job

Integrate the fifteen Bots into one Computer that can run a month unattended. Fix collisions. Prove on disk that the office replaces a team: wrong Bot cannot post, Verifiers are on the path, humans are not, planted breaks still break.

## Read first

- Every `office/sessions/*-PROOF.md`
- `office/computer/harness/roster.json`, slug-map, grants, catalog
- `docs/CFO_HARNESS_EXTENSION.md` § later done-when (adapt: Operator proofs become Verifier proofs)
- Grain § watch later — do not “solve” those by adding Bots

## Work

1. Compile catalog/grants once. Fail if constructor tools drifted.
2. Fill any stub BOT.md left from 00.
3. Align Handle destination slugs across 03–11.
4. Rooms still 2–6. Routines fire on owning Bots.
5. Client extension + sidecar + Harness boot documented in `office/RUN.md` (commands from repo root).
6. Eval: `python main.py evaluate-cfo` (or current CLI) still isolates answer keys. Remap tests that expected a human queue so they expect Verifier-refused or Kernel fail-closed — **not** MATCHED.
7. If a test required a human to mutate source to close September, write an **autonomous source mutation** only when a legal Kernel op exists. Otherwise CLOSED must not happen. The $12.40 remains the honest demo.

## Proofs (must all appear in `office/sessions/12-PROOF.md`)

- Roster has exactly the fifteen grain slugs. No `ingest`. No sample-data Bots.
- `ap` / `prepare` cannot call `create_accrual` (sidecar forbidden).
- `ctl-pay` cannot call AP RECORD_TOOLS.
- `audit` operational cannot call `get_audit_ground_truth`.
- Compile fails if you break a constructor tool list on purpose (show the failure, then revert).
- Close still BLOCKED on $12.40 without source mutation.
- Grep production hosts: no `ask_user`, no “waiting for human”, no Operator approval for pay-run or lock.
- At least one fake or live Handle path: source file → `ap` accepted → `ctl-pay` accepted. Accept ≠ complete. Protocol log has both.
- State in one sentence: the office can run without a person in the queue. List what is still not live-Pi-proven.

## Forbidden

- Reopening grain to 6 or 43 Bots
- Declaring GrokBot-class if only fake workers were used — say so
- Closing the books by deleting the $12.40
- Editing Harness core to know invoices

---

## After the thirteen sessions

You will have a Client system: fifteen standing Pi Bots, a Kernel sidecar, a compiler, and a Computer. Harness is still the bus. The old Agents SDK control plane is gone. The CFO team is not “in the loop.” Verifiers and Kernel gates are the loop.

Interconnection bugs inside Display-name prompts (grain § watch later) are a **later** pass. Do not hide them by adding Bots during these sessions. File them under `office/WATCH.md` if you trip them.

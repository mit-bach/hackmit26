# Failure taxonomy

Use these category ids in later writing. One break can sit in more than one category. Do not invent a new category until these do not cover it.

This file names kinds of wrong. Pipe files give the instances.

---

## T1 — Identity error

The standing identity does not match the object.

Examples:

- Looking for Bot `ar` because the Harness fixture `cfo-floor` has slug `ar`. This office’s AR Operators are `apply` and `collect`.
- Treating a Display name as a Bot. Forty-three constructors were never forty-three lanes.
- Treating a Pipe as a Bot. “Accounts receivable” is a process.
- Bot `world` exists as files and as an instance Roster row. It is absent from the live Roster and slug-map.
- Bot `stripe` exists as a slug. It has no Display name and no Grants.

Inadequate: the office cannot bind, grant, or Handle an identity that is only a folder.

---

## T2 — Split brain / two sources of truth

Two artifacts describe the same fact and disagree.

Examples:

- Live Computer catalog 89 ops vs instance catalog 94 ops.
- Live Roster “Fifteen grain Bots” vs instance Roster “Sixteen grain Bots.”
- Constitution: do not invent a sixteenth Bot. Capabilities.md: World is the sixteenth Source Bot. RUN.md: inbox is not a sixteenth Bot. Email BOT.md: Counterparty is a fixture Display name, not a Roster slug. World BOT.md: You are Bot `world`.
- Collections Agent prompt: call `send_office_outbound` then Handle world. Skill `ar-collections-policy`: outbox / preview, do not invent emails as sent. `run_collections`: `sent=False`. Live collect BOT.md: no send op.
- `handle-map.json`: collect write-off → `ctl-pay`. `intercept.json`: Bot `collect` → `ctl-cash`.
- Two Handle stores: Harness `harness/bots/<id>/handles/` vs Client `workspace/verifier/handles/`.
- Root `inbox/tools.py` duplicate of `.cfo/inbox/tools.py`.
- Dual intake: `invoice_ingestion.tools.*` (email profiles) vs `inbox.tools.*` (inbox profile).

Inadequate: a later agent that “fixes the prompt” will fight a second file that still states the old fact.

---

## T3 — Tool missing or Grant missing

The identity exists. The action does not.

Examples:

- `send_office_outbound` is imported by `.cfo/ar/agents.py` and is not defined in `.cfo/inbox/tools.py`. ImportError. Collections Agent cannot construct.
- Live Grants for Collections Agent: four AR read ops. Instance Grants add send.
- Finance Inbox Agent live Grants: classify and dispatch. Instance Grants add send. Live Grants omit send.
- Stripe Profile `payout` Display name `""`. Bind refuses Connectors (`missing_display_name`).
- Close Manager, Month-End Close Reviewer, Audit Report Agent: `ops: []` on live Grants.
- `list_world_personas`, `list_inbox_threads`, `list_inbox_messages`, `get_inbox_thread` exist in the instance catalog and not in the live catalog.

Inadequate: a Skill that tells the model to send cannot send. Skills never grant tools.

---

## T4 — Last mile missing

The reasoning step exists. The world-facing effect does not.

Examples:

- Collections can choose `SEND_GENTLE_REMINDER` and write a draft. The simulated customer never receives it on the live Computer.
- Payment-run draft exists as Kernel plan. There is no send-as-bank Connector. That gap is intended. Outflows to `cash` must still be identified.
- Email can classify. Outbound missing-info on the live Computer has no World to answer.

Inadequate: judges see a decision object, not an office that acted.

---

## T5 — Bus not attached

Kernel or unit tests work. The standing Bot never ran that path on Harness.

Examples:

- `run_collections(live=False)` ages invoices in Python. No live Handle from `collect` to `world`.
- `python3 main.py close-month` writes `.cfo/runs` and stays BLOCKED. That is not Routine `month-end` on Bot `close`.
- `simulate-stripe` unpacks payouts in Python. Bot `stripe` has empty Grants.
- Session proofs 00–12 said Handle complete was not live-proven. On 2026-09-20 six AP stub Handles completed. AR, pay-run, cash, close, World still have no live Handle proof on this Computer.
- Documented `RUN.md` serve is `--fake`. Fake workers echo inboxes.

Inadequate: Kernel pytest is not office-live.

---

## T6 — Prompt / Kernel collision

The model is told to do work Python already forbids or already finished.

Examples:

- Skills restate `must_hold`, `enforce_collection_decision`, `validate_proposal`, `evaluate_close_gates`.
- BOT.md lists Catalog ops the compiled Grant does not contain, or omits ops the constructor contains.
- Roster `instructions` tell Pi to read `office/bots/<slug>/BOT.md` from Computer cwd `office/computer`. That path does not exist.
- Harness prompt still teaches `ask_user` and “blocked means Operator” unless the Client extension loads and blocks it.
- `approvalLevel: "never"` is Roster text. It does not strip Pi tools by itself.

Inadequate: the model spends the turn re-deriving law. Novelty has nowhere to go. Or the model calls a tool it does not have.

---

## T7 — Over-specified procedure

The Skill or BOT.md freezes the specialist’s reasoning as a numbered checklist.

Examples:

- Almost every `SKILL.md` uses the same skeleton: Purpose, When to Use, Inputs, Procedure, Decision Criteria, Output, Boundaries.
- `ar-collections-policy` tells the model which aging bucket maps to which send intensity.
- `cash-application` enumerates ten cases the Kernel candidate engine already enumerated.
- BOT.md “Handoffs” sections are protocol (good) mixed with case law (INV-009-class, $12.40, MSG-S12).

Inadequate for this product: the later agent cannot specialize, learn a vendor habit, or connect two facts that the checklist did not name. See `03-novelty-boundary.md`.

This category is the opposite of T6 in one way. T6 fights Kernel. T7 fights the specialist. A file can be both: it restates Kernel and also forbids extra judgment.

---

## T8 — Under-specified object or done-when

The identity exists. Exit criteria do not match the intended function.

Examples:

- Live collect “Done when”: contacted under Kernel allow. There is no send tool, so “contacted” can mean a draft in an outbox with `sent=False`.
- Email BOT.md still says Counterparty is not a Roster slug. Its done-when does not include a World round-trip.
- Story may draft before lock if every number is labeled `UNLOCKED`. Nothing on the live Computer proves those packets exist.
- Close Manager Profile `coordinate` has `tools=[]`. Coordination is Kernel `ready_tasks` plus self-Wakes. The Bot has nothing to call.

Inadequate: a later agent cannot tell finished from costume.

---

## T9 — Verifier / SoD hole

Concurrence is the wrong owner, missing, or still a person.

Examples:

- Kernel status `HUMAN_REVIEW` remains as a string. Queue owner is supposed to be a Verifier. CLI `ar-review-correct` and close `--resolve` still exist as emergency tools.
- Client intercept unlocks from `workspace/verifier/handles/` with `decision: CONCUR`. A completed Harness Handle does not unlock the Kernel op.
- `intercept.json` default is still `{ "kind": "operator" }`.
- Collect consequential routing in intercept points at `ctl-cash`. Grain write-off points at `ctl-pay`.
- Verifier Grants were denylisted so twins cannot rebuild the plan. Some Verifier Profiles now cannot re-perform (`RECORD_TOOLS` stripped from `ctl-pay` / `review-match`).

Inadequate: either a human is still in the path, or the Verifier cannot see enough to refuse for a reason.

---

## T10 — Memory that does not change the next period

Precedent is claimed. The next similar ticket does not change.

Examples:

- AP `prior_cases.json` is a static seed. `run_ap_workflow` does not append. Demo gap: AP self-improvement `NOT_IMPLEMENTED`.
- AR can `record_human_application` → precedent. That path is a human correction CLI, which SUPERSEDES voids as completion.
- Memory Sidecar remap was a known miss: decision memories could land in `.cfo/runs/memory` instead of the Computer.
- Semantic context graph / RAG is `NOT_IMPLEMENTED`. Identity links are not a graph database.
- BOT.md Memory sections are “only precedents about your object” with no store that a live Pi turn is proven to write and reread.

Inadequate: Maximor scoring looks for memory that changes what the system does next. Static seed files are not that.

---

## T11 — Cross-pipe identity break

The same event is not the same object downstream.

Examples:

- Close, AR, accrual, reporting, and cash-recon keep separate books and sometimes bridge them. Docs say this plainly in `docs/AGENTIC_SYSTEM_WORKFLOW.md`.
- INV-S12 live Handle: Email landed a marker. `tools.get_invoice(INV-S12)` not found. AP HOLD. ctl-pay REFUSE. The identity never entered the Kernel register.
- August Stripe memory once hid the September demo payout. Cross-workflow demo dropped a point.
- Apply identifiers are supposed to be trusted by `cash`. If apply never posts, cash re-interprets the deposit and Close inherits the argument.

Inadequate: the stretch goal is one shared picture of the company.

---

## T12 — Demo stub treated as product

A fixture, echo, or marker is left in the path judges will see.

Examples:

- Repeated protocol lines for `MSG-S12.json` / `INV-S12.json`.
- `serve --fake` completes Handles with `` `[${slug}] ${prompt}` ``.
- `examples/cfo-floor` six slugs used as if they were the office.
- Loud audit decoys (duplicate vendor, $50k round wire, GM 64% → 61%) while stealth holdout is not planted.
- Skills `status: new` on files that were extracted from old constructor text.

Inadequate: the demo shows the office refusing a fake packet, not running a month.

---

## T13 — Leftover V1 bus

The standing office still calls the old in-process harness for domain work.

Examples:

- `.cfo/**/workflow.py` still `run_agent` → `Runner.run_sync`.
- Close production uses `deterministic_coordinate()` instead of live Close Manager.
- Collections live path cannot start because the constructor import is broken.
- Compiler still needs `Agent(..., tools=[...])`. That is allowed. Calling `Runner` as the office is not.

Inadequate: two buses. Handles on Harness. Work in Runner. They do not share done.

---

## How to use this list

When you describe a defect, name the category ids.

Example: live collect send path is T1 (World off Roster) + T2 (four send stories) + T3 (op missing) + T4 (no mailbox effect) + T5 (no live Handle) + T6 (skill vs constructor).

When you describe an inadequacy of something that works, still name a category.

Example: `three-way-match-analysis` restates `must_hold` (T6, T7) even though AP Kernel match is good (`04-what-is-good.md`).

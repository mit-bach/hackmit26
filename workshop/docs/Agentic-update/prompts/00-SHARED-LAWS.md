# Shared laws — Office of the CFO deploy

Every implementing agent reads this file first. Then it reads only its numbered prompt. It does not read the other numbered prompts. It does not invent extra tickets.

Repo: `/Users/dominikbach/olympus/hackmit/hackmit26`

Office: `.cfo-v2/office`
Kernel: `.cfo/`
Harness: `.harness/Harness-v2`
Computer: `.cfo-v2/office/computer`

You are making this office **deployable and working**. You are not writing a website. You are not restoring V1 `Runner` as the Bot bus. You are not designing a new company.

Corpus (read from disk when your numbered prompt names a file; do not wait for the operator to attach it): `workshop/docs/Agentic-update/`. Snapshot date on that corpus: 2026-09-20. **Live disk wins** over the snapshot.

---

## Product in one paragraph

Maximor Demo Corp (`CO-MAXIMOR`), September 2026. An agentic Office of the CFO: standing Bots pay vendors, apply customer cash, reconcile the bank, close the month, forecast, and audit. Python owns amounts. A model chooses among Kernel candidates. Verifier Bots (`ctl-pay`, `ctl-cash`, `ctl-books`) replace a human queue. Simulated data only. No live Gmail write-back, live Stripe write-back, or live NetSuite post in the judged demo. Constitution: the office completes AP, AR, cash, close, reporting, and audit with zero humans in the completion path.

---

## Four layers (keep them apart)

1. **Kernel** — `.cfo/`. Arithmetic, candidate engines, cents, `must_hold`, `enforce_collection_decision`, `validate_proposal`, `compute_tie_out`, `evaluate_close_gates`, period lock, eval isolation.
2. **Office** — `.cfo-v2/office/`. Named Bots, Profiles, Grants, Handles, Rooms, Routines. Pi is the turn engine inside a Bot.
3. **World pack** — preexisting Maximor books the Computer loads as `data/`. Agents discover registers. They do not create the company.
4. **Overlay** — Harness HTTP, optional website. The human Operator is an emergency stop. It is not a worker.

Mixing layers is how “97% Kernel” gets sold as “the office works.” Kernel pytest green is not office-live. `--fake` echo workers are not office-live.

V1 ran Display names as in-process OpenAI `Agent()` objects with `Runner.run_sync`. V2 keeps the Kernel and puts each standing identity on a Harness Bot. Constitution SUPERSEDES voids `Runner` as the Bot bus. Constructors stay as the Grant source.

---

## Name map (use these names only)

| Name | Meaning |
| --- | --- |
| Pipe | AP, AR, cash, or close. A process. Not a Bot. |
| Bot | Standing Harness identity. One slug. One lane. `HARNESS_BOT`. |
| Display name | Python `Agent(name=...)`. Grant source. Becomes a Profile. |
| Profile | One Grant set on one Bot. A Wake names it. Do not union two in one turn. |
| Kernel | Python engine under `.cfo/`. |
| Skill | `SKILL.md`. Prompt. Never a tool. |
| Grant | Catalog op ids for one Display name. |
| Catalog | Named Kernel ops in `cfo/catalog.json`. |
| Handle | Accept-time peer work on the Harness bus. Accept is not complete. A peer Handle is not approval. |
| Verifier | `ctl-pay`, `ctl-cash`, `ctl-books`. Concurrence. Not a human. |
| Operator | Human at the Harness HTTP shell. Emergency stop. Not a worker. |
| Computer | `.cfo-v2/office/computer`. Harness cwd. |
| World | Simulated outside mailbox. Written as Bot `world`. Not on the live Roster. |
| Open item | Unfinished ticket: open invoice, open bill, unapplied cash, unmatched bank line, accrual. |

There is no Bot named `ar`. AR Operators are `apply` and `collect`. The Harness fixture `examples/cfo-floor` slug `ar` is not this office. Do not attach or copy that Roster.

---

## Fifteen grain Bots (live roster)

`email`, `stripe`, `bank`, `books`, `ap`, `pay`, `apply`, `collect`, `cash`, `close`, `story`, `ctl-pay`, `ctl-cash`, `ctl-books`, `audit`.

Rooms: intake (`email,stripe,bank,books`), pay (`ap,pay,ctl-pay`), cash (`apply,collect,cash,ctl-cash`), books-close (`close,ctl-books,story,audit`).

World is a sixteenth identity that exists as `BOT.md` and instance snapshots. It does not sit on the live Computer roster. Constitution: do not invent a sixteenth Bot without failing Tests A–D. Capabilities.md already treats World as a real lane. This pack records that split. Prompt **02** owns the grain decision and the mailbox round-trip. Other prompts must not silently add or delete `world`.

---

## Grain Tests A–D (new Bots)

Source: `workshop/design-workshop/dominik/cfo-bot-grain.md`.

- **A Wake.** Something in the world or the office names this identity (webhook, Routine, Handle to this slug). If the work only ever runs because the same Bot continued its own turn, it is a Profile, not a new Bot.
- **B Object.** Named owner of one class of record.
- **C Grant particularity.** The tool list would be unsafe to union onto a neighbor.
- **D Durable stance.** The Bot keeps Memory that changes the next period. A pure function over one JSON blob is Kernel, not a Bot.

Do not add a Bot because a folder has `agent.py`, a workflow has a reviewer step, Maximor listed a process name, you want a second prompt on the same tools, or you are afraid to delete a Display name.

---

## Law (not novel)

A specialist does not get a second version of these.

1. Python wins on amounts. The model chooses among Kernel candidates. It does not invent totals, combinations, fees, or residuals.
2. Skills never grant tools. Grants come from compiled constructors.
3. Fail closed. Missing evidence is not a guess.
4. Do not union two Grant sets in one turn. A Wake names one Profile.
5. A Bot is not a child. The Roster is not `pi-subagents`. Do not restore `Runner` as the Bot bus.
6. Accept is not complete. A peer Handle is not approval.
7. The human Operator is not a worker. Verifiers own concurrence.
8. Operational Bots never load ground truth or `get_audit_ground_truth`.
9. The planted $12.40 unexplained bank difference stays unexplained in the judged demo. `TXN-2026-09-015`. Close stays BLOCKED.
10. Grain Tests A–D decide whether something is a Bot.
11. Do not put finance types, invoice enums, or close DAGs in `.harness/Harness-v2/src`. Generic primitives only.
12. Do not treat `HUMAN_REVIEW` as a person in the completion path. Queue owner is a Verifier. Kernel may keep the string.
13. Hand-editing Grant ops is forbidden. Recompile from constructors. RUN.md already says this.
14. Instance snapshots under `.cfo-v2/office/instances/**` are evidence of a fuller compile, not live source of truth.

Kernel hard holds stay Kernel: `must_hold`, `enforce_collection_decision`, `validate_proposal`, `compute_tie_out`, `evaluate_close_gates`.

---

## Four pipes, four handoffs (not a mesh)

```
who owes us  →  money in   →  bank   →  the books
who we owe   →  money out  ↗
```

| Pipe | Direction | Standing Bots that own work |
| --- | --- | --- |
| AR | Money in | `apply`, `collect` (intake: `email`, `stripe`, `bank`) |
| AP | Money out | `ap`, `pay` (intake: `email`, `books`, `bank`) |
| Cash | Bank vs books | `cash` (intake: `bank`, `stripe`; identifiers from `apply` and `pay`) |
| Close | Period completeness | `close`, `story`, `audit` |

Verifiers: `ctl-pay` money out / write-off; `ctl-cash` apply and rec; `ctl-books` treatments and lock. `audit` is assurance after the fact. It does not concur on Friday’s wire.

Handoffs:

1. AR identifies customer deposits. Cash checks the bank agrees.
2. AP identifies vendor payments. Cash checks the bank agrees.
3. Cash hands trusted cash to close.
4. AR and AP hand agings that tie to close.

If AR and cash both interpret the same deposit from scratch, they disagree and close inherits the argument.

Process law: `workshop/design-workshop/dominik/cfo-office-processes.md`.

---

## Failure categories

Use these ids in NOTES and commit messages. Source: `docs/Agentic-update/02-failure-taxonomy.md`.

| Id | Kind |
| --- | --- |
| T1 | Identity error (wrong slug, Display name treated as Bot, World folder with no Roster row) |
| T2 | Split brain (two artifacts disagree: live vs instance, Skill vs constructor, handle-map vs intercept) |
| T3 | Tool missing or Grant missing |
| T4 | Last mile missing (decision exists, world-facing effect does not) |
| T5 | Bus not attached (Kernel works, standing Bot never ran that path on Harness) |
| T6 | Prompt / Kernel collision |
| T7 | Over-specified procedure (Skill freezes the specialist) |
| T8 | Under-specified done-when (costume can satisfy the sentence) |
| T9 | Verifier / SoD hole |
| T10 | Memory that does not change the next period |
| T11 | Cross-pipe identity break |
| T12 | Demo stub treated as product (`--fake`, `INV-S12` marker, `cfo-floor`) |
| T13 | Leftover V1 bus (`Runner.run_sync` as the office) |

Loudest inadequacy per pipe (do not invert):

| Pipe | Loudest inadequacy |
| --- | --- |
| Floor | Documented boot is `--fake`. Two Handle stores. BOT.md cwd miss. |
| AR | Apply/collect split is right. Send is dead. |
| AP | Match is strong. Learning and live bills are not. |
| Cash | Tie-out and $12.40 law are strong. Stripe Bot and identifier handoff are not. |
| Close | Honest BLOCKED is strong. Empty ops and `.cfo/runs` demo path are not. |

---

## Public show-path IDs (do not mint a second id)

| Story | IDs | Outcome |
| --- | --- | --- |
| CLEAN | Acme `INV-001` = `PO-101` = `GR-101`. Paid `PAY-AP-001`. Bank `TXN-2026-09-018A` MATCHED | Happy path |
| RESOLVED | Helios `INV-017`. Bank `TXN-2026-09-011` is $25 over books. `FEE-729103` supports FEE_NETTED | Explained exception |
| UNRESOLVED | Northstar `INV-AR-013` / `PAY-006` books $12,400.00. Bank `TXN-2026-09-015` is $12,412.40. No fee evidence | Close BLOCKED |

Do not resolve the $12.40. Do not relabel it as a fee. Helios is the explained cousin. Keep both.

---

## What “the office completes” means

A pipe is done when its open items have a next state the Kernel already allows, and a Verifier has concurred when grain requires concurrence.

The office is done for a period when:

1. Every deposit that belongs to a customer is applied or sitting in unapplied with a reason.
2. Every overdue invoice has a next step that is not “we forgot,” and any send that policy allows has actually entered the simulated mailbox.
3. Every vendor bill is matched or held. The weekly run is a Kernel-netted list. Cash has not left without `ctl-pay`.
4. Bank minus known open items equals ledger, or the break is named and unexplained where it is unexplained.
5. Close gates pass, or the period stays BLOCKED on a real break. The planted $12.40 stays unexplained.
6. Story packets cite Kernel evidence ids. Audit findings cite Kernel finding ids. No human signed the pack.

Autonomy is not “always post.”

---

## Prompt layers besides BOT.md and skills

If you only rewrite BOT.md and SKILL.md, the other layers still drive the model or the Python host. Inventory before you change one.

| Layer | Path |
| --- | --- |
| Roster instructions | `computer/harness/roster.json` `instructions` |
| Profile markdown | `office/bots/<slug>/profiles/*.md` |
| Kernel constructor instructions | `.cfo/**/agent.py`, `agents.py` |
| Skill injection | `skills/loader.py` `compose_instructions` |
| Harness identityBlock | `.harness/Harness-v2/src/prompt.ts` |
| Harness protocol skill | `.harness/Harness-v2/skills/harness/SKILL.md` |
| Routine prompt | Roster `routines[].prompt` |
| Handle prompt | `bot_send_prompt` text |
| Client verifierInstruction | `cfo/extensions/verifier.ts` |
| SAFETY blocks | Kernel agent modules |
| NOTES.md / PROOF.md | `office/bots/<slug>/` |

AR send is the canonical split brain: constructor vs Skill vs `run_collections` vs live BOT.md vs instance roster.

---

## Skills (the idea, not a rewrite recipe)

A Skill that is worth keeping:

- Tells the model what kind of judgment this object needs, without scoring the judgment.
- Tells the model which Kernel fields are authoritative, so it does not re-sum.
- Tells the model what it must not do.
- Names the output type and the Verifier when grain already named one.

A Skill that is not worth keeping as-is:

- Restates `must_hold` cases.
- Maps bucket → action as if the model owned eligibility.
- Claims the output is “preview only” when the office must actually send.
- Exists only because a constructor used to be long.

Do not freeze a numbered Kernel replay into a new Skill. Do not ship a 1:1 copy of a constructor as if that restored tools.

BOT.md is standing identity: who you are, what you own, how you wake, what you must not do, when you are done. Protocol belongs there. Case law (INV-009-class, MSG-S12, planted ids) does not.

---

## File ownership (do not overlap)

| Path / concern | 01 Floor | 02 AR | 03 AP | 04 Cash | 05 Close |
| --- | --- | --- | --- | --- | --- |
| `.harness/Harness-v2/src` generic bus only | **yes** | no, unless Floor left a hole that blocks your pipe; then generic only | same | same | same |
| `RUN.md`, `client.json`, `extensions.json`, intercept **default**, Handle unlock path | **yes** | no | no | no | no |
| BOT.md cwd / Computer-visible identity for all slugs | **yes** (layout) | your slugs’ text | your slugs’ text | your slugs’ text | your slugs’ text |
| `.cfo/inbox/`, World bind, collect send, apply | no | **yes** | Email missing-field only. Do not fork a second mailbox | no | no |
| `.cfo/ar/` | no | **yes** | no | identifiers only | AR snapshot read |
| `.cfo/workflow.py`, `.cfo/agent.py`, AP scheduling | no | no | **yes** | no | AP aging read |
| `.cfo/cash_recon/`, stripe Grants | no | charge-level to apply | identified wires to cash | **yes** | trusted cash read |
| `.cfo/close/`, reporting, audit | no | no | unreceived → close Handle | trusted cash Handle | **yes** |
| live `roster.json` | bind, extra slug only if Tests A–D | World / collect / email edges | ap / pay / ctl-pay | stripe / cash / ctl-cash | close / story / audit / ctl-books |
| `grants.json` / Catalog compile | no, unless bind requires a Display name Floor does not own | Collections / Finance Inbox / World | AP / Payment / Payment Audit | Stripe / cash rec | coordinate / lock / report |
| Instance snapshots | read-only | read-only | read-only | read-only | read-only |
| `examples/cfo-floor` | do not use | do not use | do not use | do not use | do not use |
| `web/` | do not edit | do not edit | do not edit | do not edit | do not edit |

Two agents must not rewrite the same Grant row. If AR adds `send_office_outbound` to Collections Agent, AP does not touch that row.

If two agents conflict on `roster.json` or `grants.json`: Tests A–D and SoD denylist win. World belongs to 02. Extra `-e` and Handle store belong to 01. `$12.40` belongs to 04 and 05 together: both refuse to clear it.

---

## Spawn order

1. Finish **01 Floor** first. Bind, attach, cwd, Handle store, live boot. The pipes cannot prove office-live without this.
2. Then spawn **02 AR** and **03 AP** in parallel. Mailbox and payables are different objects.
3. Then **04 Cash**, after apply/pay can write identifiers. If they have not, cash fails closed. It does not invent the counterparty.
4. Then **05 Close**. Close is the period pass over the other three. A board pack first is a lie.

They may **read** in parallel. They must not merge Floor last. If 02 starts before Floor is done, it still must not document `--fake` as success.

If Floor outcomes 1–3 in prompt 01 are not true when you start a pipe prompt: write `docs/Agentic-update/evidence/NOTES-floor-hole.md` naming the hole. Continue only on Kernel and Grant work you own. Do not rewrite `RUN.md`.

---

## What is good (do not delete)

Source: `docs/Agentic-update/04-what-is-good.md`.

- Grain split: 15 standing Bots. `pay` is not a Profile on `ap`. `apply` is not a Profile on `collect`. Close treatments are Profiles, not four extra lanes.
- Kernel as law. The planted $12.40 is a product feature. Relabeling it as a fee without evidence is a bug.
- Fail closed: APPROVE/HOLD, AUTO_APPLY/HUMAN_REVIEW/UNAPPLIED, unexplained cash unmatched, accrual INSUFFICIENT.
- Three Verifiers by stake class. Audit is not a fourth Verifier on Friday’s wire.
- Handle protocol: accept ≠ complete, sender never marks complete, Rooms 2–6, per-Bot Memory.
- Live Pi on 2026-09-20: `ctl-pay` REFUSED an incomplete APPROVE packet for INV-S12 instead of inventing a bill. That refusal is good behavior on bad evidence. It is not a real payables story.
- Honest demo gaps already written in `docs/demo-capability-gaps.md` and `.cfo-v2/office/final-demo/CAPABILITIES.md`: AP learning, vendor bank-change, semantic graph, live ERP write-back, adversarial holdout. Keep that honesty. Do not plant fake findings.

---

## Live Computer facts (2026-09-20). Disk wins if different.

- Roster: 15 slugs. Description “Fifteen grain Bots.” `world` not in `bots[]`. `collect` connectors: four `ar.tools.*` reads. No send. `stripe` skills `[]`.
- Instance `protocol-proof` / `fresh-protocol`: 16 slugs including `world`. Collect connectors include `inbox.tools.send_office_outbound`. Catalog 94 ops vs live 89.
- Live Grants: 45 Display names. Empty ops include Audit Report Agent, Month-End Close Reviewer, Close Manager.
- `from inbox.tools import send_office_outbound` → `ImportError`. Collections Agent cannot construct.
- Six completed Handles: `bot_email` (2), `bot_ap` (3), `bot_ctl_pay` (1). HOLD/REFUSE on INV-S12 marker. No collect, apply, cash, close, story, world Handles in that set.
- `intercept.json` default `{ "kind": "operator" }`. Collect override → `ctl-cash`. `handle-map.json` collect write-off → `ctl-pay`.
- Roster instructions: `Read office/bots/<slug>/BOT.md` from Computer cwd `office/computer`. That path does not exist. Actual: `.cfo-v2/office/bots/<slug>/BOT.md`.
- `RUN.md` step 3 still teaches `npm run serve -- --fake`.
- Two Handle stores: Harness `harness/bots/<botId>/handles/` vs Client `workspace/verifier/handles/`.
- `client.json`: `autoRoutines: false`. Sidecar `./cfo/bin/sidecar.sh`. Model grok-4.5.
- `kernel.port` existed (60440). That is not proof the sidecar was healthy at Handle-complete time.

---

## Verification (every prompt)

- After Kernel edits: run the Kernel tests that cover the ops you touched. Use `.cfo/.venv` and `sys.path` that loads `.cfo/`, not repo-root `inbox/`.
- After Harness `src` edits: run the existing Harness tests you just affected. Do not weaken `cfo-floor` fixture tests by pretending that fixture is this office.
- After Grant/constructor edits: recompile Catalog/Grants the way RUN.md already documents. Do not hand-edit `grants.json` ops.
- Prove with a command, an import, a Handle file, or a test. Do not prove with a rewritten Skill paragraph.
- A single screenshot of a chat is not proof.
- If you leave a hole, write `NOTES.md` under `office/bots/<slug>/` or `docs/Agentic-update/evidence/NOTES-<slug>.md`. Do not silently claim office-live.
- Do not commit unless the operator asks.

---

## Do not (all five prompts)

- Do not paste this pack into a website agent or a `web/` rewrite.
- Do not resolve `TXN-2026-09-015` / the $12.40.
- Do not implement live SMTP, live Gmail, live ACH, or live NetSuite.
- Do not restore `Runner` as the Bot bus. Compiler still needs `Agent(..., tools=[...])`. That is allowed.
- Do not register Roster slugs as children.
- Do not add Bot `ar`, `ap-investigator`, `accrue`, `prepaid`, `assets`, `bs`, `ctl-story`, or a Bot per match type / source format.
- Do not merge `apply` and `collect`. Do not merge `ap` and `pay`. Do not merge `story` into `close`.
- Do not treat `examples/cfo-floor` as this office.
- Do not demo `--fake` `MSG-S12` as the product.
- Do not plant stealth theft into operational books. Capabilities.md marks adversarial holdout as not built.
- Do not load `get_audit_ground_truth` on operational Grants.
- Do not use AUTO_APPLY on an ambiguous remittance to look autonomous.
- Do not rewrite all 33 skills into a new template for the sake of the template.

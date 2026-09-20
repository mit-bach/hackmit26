# CFO v2 Client — Harness integration gap analysis

Audit date: 2026-09-19.
Office under audit: `.cfo-v2/` (not `.cfo/`, not `.harness/Harness-v2/examples/cfo-floor`).
Method: disk paths, file counts, and source reads. No live `pi` turn. No commit.

**Verdict.** The migration wrote a full fifteen-Bot Roster, compiled Catalog/Grants, BOT.md files, and a modular Client extension. Harness *can* parse that Roster. The office still does not boot as fifteen Pi Bots on Harness v2. The documented boot path uses `--fake`. Client attach env is unset. Handle `completed` never happened on a live Pi. Kernel `Agent()` / `Runner.run_sync` still runs domain workflows in `.cfo/`.

`.harness/Harness-v2/examples/cfo-floor` is a six-slug protocol fixture (`ingest`, `ap`, `ar`, `cash`, `close`, `audit`). It is not this office. Harness v2 tests (`tests/cfo-scale.test.ts`) load that fixture via `makeCfoComputer()`, not `.cfo-v2/office/computer/harness/roster.json`.

---

## Name map

One name for one thing. If two labels exist, this table picks one.

| Name | Meaning |
| --- | --- |
| Grain | `design-workshop/dominik/cfo-bot-grain.md`. Fifteen standing slugs |
| Office | Client system root `.cfo-v2/` |
| Computer | `.cfo-v2/office/computer`. Harness cwd. `HARNESS_COMPUTER` |
| Kernel | Python engine under `.cfo/` |
| Sidecar | `python -m cfo_kernel` with `PYTHONPATH=.cfo`. Not a Bot |
| Harness | `.harness/Harness-v2` |
| Roster | `office/computer/harness/roster.json`. The file `loadRoster` reads |
| Fragment | Leftover per-session JSON. Harness does not merge these |
| Bot | Grain slug with `HARNESS_BOT`. Standing Harness identity |
| Display name | Python `Agent(name=...)`. Grant source. Becomes a Profile |
| Profile | One Grant set on one Bot. A Wake names it |
| Catalog | `office/computer/cfo/catalog.json` |
| Grant | Display name → Catalog ids in `cfo/grants.json` |
| Client extension | `.cfo-v2/office/computer/cfo/extensions/` loaded as a second `pi -e` |
| Harness extension | `.harness/Harness-v2/extensions/index.ts` |
| Handle | Harness accept-time record under `computer/harness/bots/<id>/handles/` |
| Client pending file | `computer/workspace/verifier/handles/<id>.json`. Not a Harness Handle |
| Operator | Human at the Harness HTTP shell. Emergency stop. Not a worker |
| Verifier | `ctl-pay`, `ctl-cash`, `ctl-books` |
| Skill | `SKILL.md` directory. Prompt. Never grants tools |
| Connector | Provider or named Kernel op string on the Roster. Prompt text in this Harness cut |

A Pipe is not a Bot. A Display name is not a Bot. `examples/cfo-floor` is not this office.

---

## 1. Tree of `.cfo-v2/office/`

Counted 288 files under `.cfo-v2/office/` excluding `node_modules`, `__pycache__`, and `dist`.

```
.cfo-v2/office/
  RUN.md
  SUPERSEDES.md
  WATCH.md
  constitution.md
  handles.py
  bots/                 15 grain slug dirs + __init__.py
  compiler/             Python Catalog compiler
  computer/             Computer (Harness cwd)
    ENV.md
    data -> ../../../.cfo/data
    cfo/                Catalog, Grants, slug-map, Client extension
    harness/            Roster, protocol.jsonl, per-Bot dirs
    runs/               Sidecar overlay (cash_recon only on disk today)
    skills/             Copied/symlinked SKILL.md trees
    workspace/          Session-12 fake packets only
  sessions/             00–12 PROOF.md
  source_wakes/         Python wake helpers (not Harness)
  templates/BOT.md
  tests/                Session-12 pytest + fake_handles.mjs
```

No `office/skills/` tree. Skills live on the Computer at `office/computer/skills/`.
No `office/extensions/` at office root. Client extension lives at `office/computer/cfo/extensions/`.
`constitution.md` and `RUN.md` exist at office root, not on the Computer.

### Computer / Harness / compiler

| Path | State |
| --- | --- |
| `computer/harness/roster.json` | Real merged Roster. 15 Bots. Harness load path |
| `computer/harness/roster-fragment.json` | Leftover session-06 apply/collect fragment. Not loaded |
| `computer/harness/protocol.jsonl` | 4 `send.accepted` lines from `fake_handles.mjs` (ran twice) |
| `computer/harness/seq` | `"4"` |
| `computer/harness/bots/` | 15 dirs named `bot_<id>` |
| `computer/harness/rooms/` | `intake`, `pay`, `cash`, `books-close`. Empty (no `log.jsonl`) |
| `computer/harness/approvals/`, `leases/`, `receipts/` | Empty |
| `computer/cfo/catalog.json` | 80 ops. Compiled |
| `computer/cfo/grants.json` | 43 Display names. `byDisplayName` (not empty `agents: {}`) |
| `computer/cfo/slug-map.json` | 15 grain slugs. Profiles. No list-unions |
| `computer/cfo/kernel.port` | Missing. Sidecar is not running |
| `computer/data` | Symlink to `.cfo/data`. Real |
| `compiler/` | Real AST compiler. `python -m compiler` imports |

### Bots: BOT.md vs stub vs NOTES only

All fifteen grain slugs have a real `BOT.md` (66–119 lines). Required headings from `office/templates/BOT.md` are present. No session-00 stub (`{slug}` / `{object}`) remains. None is NOTES-only.

| Slug | BOT.md lines | NOTES.md | PROOF.md | Extra |
| --- | ---: | --- | --- | --- |
| `email` | 83 | yes | no | `profiles/` (4) |
| `stripe` | 66 | yes | no | `profiles/payout.md` |
| `bank` | 68 | yes | no | `profiles/card.md` |
| `books` | 77 | yes | no | `profiles/` (3) |
| `ap` | 93 | yes | no | `profiles/`, `roster.json` |
| `pay` | 105 | yes | yes | fragments, `routines/weekly-pay-run.md` |
| `apply` | 68 | yes | yes | `profiles/`, `roster.json` |
| `collect` | 66 | yes | yes | `profiles/`, `roster.json` |
| `cash` | 101 | yes | yes | `profiles/`, `roster.json` |
| `close` | 106 | yes | no | `HOST.md`, fragments, 5 profiles |
| `story` | 117 | **no** | no | 4 profiles, `roster.json` |
| `ctl-pay` | 102 | yes | yes | 2 profiles |
| `ctl-cash` | 95 | yes | yes | 2 profiles |
| `ctl-books` | 94 | yes | yes | 2 profiles |
| `audit` | 119 | yes | no | Python host, fragments, `test_audit_bot.py` |

33 Profile files exist under `office/bots/*/profiles/`. That is prompt text on disk. Pi does not auto-load those files.

---

## 2. Roster vs Harness `BotRecord`

Harness type: `.harness/Harness-v2/src/types.ts` `BotRecord` fields `id`, `name`, `slug`, `purpose`, `instructions`, `skills`, `connectors`, `approvalLevel`.
Loader: `.harness/Harness-v2/src/roster.ts` `loadRoster` → `computer/harness/roster.json` (`paths.ts` `rosterPath`).

The merged Roster **matches** `BotRecord`. All fifteen rows have every field. `parseRoster` keeps all fifteen (session 00 already proved this with a type-strip import). `approvalLevel` is `"never"` on all fifteen. Default parse fallback `"ask"` is not used.

`Roster.computer` is the string `"office/computer"`. That is metadata relative to `.cfo-v2/`. Harness does not use it as a load path. Bind uses `HARNESS_COMPUTER` / `--computer`.

### Rooms (2–6 members)

Four Rooms. All in range.

| Room id | Members | Count |
| --- | --- | ---: |
| `intake` | `email`, `stripe`, `bank`, `books` | 4 |
| `pay` | `ap`, `pay`, `ctl-pay` | 3 |
| `cash` | `apply`, `collect`, `cash`, `ctl-cash` | 4 |
| `books-close` | `close`, `ctl-books`, `story`, `audit` | 4 |

On disk, `computer/harness/rooms/<id>/` exists and is empty. No Room Host log. No `host.lock`.

Leftover fragment `computer/harness/roster-fragment.json` defines Room `room_ar_open_items` (`apply`, `collect`). Harness does not load it. The merged Roster uses Room `cash` instead.

### Routines

Five Routines on the merged Roster. Conversation is `room:<id>`, not `operator_dm`.

| Name | Bot | Cadence | Conversation |
| --- | --- | --- | --- |
| `weekly-pay-run` | `pay` | weekly | `room:pay` |
| `daily-aging` | `collect` | daily | `room:cash` |
| `month-end` | `close` | monthly | `room:books-close` |
| `period-story` | `story` | monthly | `room:books-close` |
| `post-close-assurance` | `audit` | monthly | `room:books-close` |

`period-story` is extra vs constitution session-00’s four-row table. `WATCH.md` records that. It is not a sixteenth Bot.

**Disconnected.** `cadenceToMs` in `.harness/Harness-v2/src/routines.ts` accepts `hourly`, `daily`, and `every N s/m/h/ms` only. It returns `undefined` for `weekly` and `monthly`. Supervisor therefore **does not register timers** for four of five Routines. `npx harness routine <name>` can still `fireRoutine` by name (writes a Receipt + inbox item). `computer/harness/receipts/` is empty. No Routine has fired on this Computer.

### Fragments vs one merged Roster

Harness loads **one** file: `computer/harness/roster.json`. Fragments are session leftovers.

| Fragment | Role |
| --- | --- |
| `computer/harness/roster-fragment.json` | apply/collect session-06 |
| `office/bots/{ap,apply,collect,cash,story}/roster.json` | Single-Bot rows |
| `office/bots/{pay,close,audit}/roster.fragment.json` | Single-Bot rows |

Harness has no merge step. If someone pointed `HARNESS_ROSTER` at a fragment, `parseRoster` would load two Bots and drop the rest.

---

## 3. Roster vs grain 15 slugs

Grain slugs: `email`, `stripe`, `bank`, `books`, `ap`, `pay`, `apply`, `collect`, `cash`, `close`, `story`, `ctl-pay`, `ctl-cash`, `ctl-books`, `audit`.

Merged Roster: those fifteen, that order. **None missing. None extra.**

No slug `ingest`. No slug `ar` as a Bot. Sample-data Display names are Grant rows with `ops: []`. They are not Roster slugs.

`examples/cfo-floor` still has `ingest`. That tree is a Harness fixture. Do not treat a missing `ingest` on this office as a defect.

---

## 4. Skills transfer

| Tree | `SKILL.md` count |
| --- | ---: |
| `.cfo/skills/*/SKILL.md` | **31** |
| `.cfo-v2/office/computer/skills/*/SKILL.md` | **28** |
| `.cfo-v2/office/computer/cfo/skills/` | missing |
| `.harness/Harness-v2/skills/` | 1 (`harness/SKILL.md`, protocol skill) |

Missing on the Computer (present in Kernel):

1. `month-end-close-review` — **named on Roster** for `ctl-books`
2. `cross-ledger-data-consistency` — not on this Roster
3. `synthetic-finance-scenario-design` — sample-data / eval, not a floor Bot skill

Copy vs symlink vs empty:

- 26 skills: byte-identical **copies**
- 2 skills: **symlinks** into `.cfo/skills/` (`early-payment-discount-evaluation`, `payment-prioritization`)
- 1 empty botched directory named `financial-variance-analysis cash-forecasting ar-cash-forecasting forecast-vs-actual-interpretation board-financial-reporting` (spaces, no `SKILL.md`)

### Roster.skills populated?

Yes, except `stripe` (`skills: []` by design: no Display name, empty Grants).

Client intersect (`extensions/skills.ts`): `grant.skills ∩ roster.skills`. If roster is empty, grant skills pass through.

Mismatches:

| Bot | Roster-only (dropped by intersect) | Grant-only |
| --- | --- | --- |
| `ctl-cash` | `bank-reference-interpretation` | none |
| `ctl-books` | `balance-sheet-reconciliation`, `fixed-asset-depreciation` | none |

`ctl-books` still wants `month-end-close-review` from Grants ∩ Roster. That directory is **not** under `computer/skills/`. `kernelSkillsRoot` can walk up to `.cfo/skills/` **if** the Client extension is loaded. If only the Harness extension loads, `HARNESS_CLIENT_SKILLS` is unset and Harness dumps the whole `computer/skills/` directory (including the empty spaced name, excluding the missing review skill).

### Does the Client extension intersect skills?

Yes, in `cfo/extensions/index.ts` `skillPathsFor` + `intersectSkillNames`. It also prepends `$HARNESS_V2_ROOT/skills` when that env is set (`pi-bot.sh` sets it; `harness serve` does not).

Harness itself (`extensions/index.ts`) adds `<computer>/skills` as a **whole directory** unless `HARNESS_CLIENT_SKILLS=1`. The allowlist is Client-side. Documented `serve` does not set that env.

Skills never grant tools. That part of the contract holds in code.

---

## 5. Extensions: barrel vs attach

### Client extension is modular, not one stub file

`office/computer/cfo/extensions/` (source, 14 files):

| File | Role |
| --- | --- |
| `index.ts` | Barrel **and** real `pi.registerTool` attach |
| `load.ts` | Parse Catalog / Grants / slug-map |
| `profile.ts` | Bind slug → Profile → one Grant set |
| `search.ts` | `search_connected_tools` |
| `call.ts` | `call_connected_tool` |
| `kernel.ts` | HTTP to Sidecar `/rpc` |
| `intercept.ts` | Consequential op → Verifier packet |
| `verifier.ts` | Route table `ctl-*` |
| `send.ts` | Dynamic import of Harness `src/send.ts` |
| `skills.ts` | Intersect + directory paths |
| `paths.ts` | Path lease |
| `types.ts` | Client types (no invoice types) |
| `pi-api.ts` | Local Pi duck-type. Does not import `@earendil-works/pi-coding-agent` |
| `facade.test.ts` | Unit tests. No live Pi |

Compiled copies exist under `cfo/dist/`. `cfo/package.json` scripts: `build` / `test`. No `"pi": { "extensions": [...] }`. Pi will not auto-discover this package.

### What loads WITH Harness

Contract (`docs/CFO_HARNESS_EXTENSION.md` and `RUN.md`):

```bash
pi -e .harness/Harness-v2/extensions/index.ts \
   -e .cfo-v2/office/computer/cfo/extensions/index.ts \
   --name ap
```

That is a real two-extension attach **when those flags run**.

What actually happens:

| Path | Client extension | Pi |
| --- | --- | --- |
| `cfo/bin/pi-bot.sh <slug>` | Yes. Sets `HARNESS_BOT`, `HARNESS_COMPUTER`, `HARNESS_V2_ROOT`, `HARNESS_EXTRA_EXTENSIONS`, `HARNESS_CLIENT_SKILLS=1`. `exec pi -e harness -e cfo` | One interactive Pi. Not fifteen |
| `harness bot <slug>` (`cli.ts`) | Only if `HARNESS_EXTRA_EXTENSIONS` is already in the environment. `extraExtensionArgs()` | One Pi |
| `npm run serve -- --computer … --fake` (documented) | **No.** `--fake` starts `startFakeWorkers`. Supervisor is not started. Extra `-e` never applied | **No Pi** |
| `serve` without `--fake` | Only if env already has `HARNESS_EXTRA_EXTENSIONS`. Supervisor spawns `node <pi-cli> --mode rpc -e <harness only>` | Fifteen Pi **Harness-only** unless extra env is set |

Harness `package.json` `"pi.extensions"` lists only `./extensions/index.ts`. Finance types did not enter Harness core (`pkg.ts` `HARNESS_EXTRA_EXTENSIONS` is a generic path list). Session 01 added that hook. `RUN.md` serve block never exports it.

`pi-api.ts` is a local interface, not a fake Pi binary. Runtime Pi must supply a matching object. Unit tests never construct Pi. `/opt/homebrew/bin/pi` exists on this machine. `.harness/Harness-v2/node_modules/@earendil-works/pi-coding-agent` exists. `cfo/package.json` does not depend on it.

`index.ts` default export returns immediately when `HARNESS_BOT` is unset. Unbound Pi registers nothing. That is intended.

Bind tools that **do** register when bound: `search_connected_tools`, `call_connected_tool`. `pi.on("tool_call")` blocks `ask_user`. `pi.on("input")` replaces Profile on a `profile:` Wake header.

---

## 6. Sidecar / Kernel

`python -m cfo_kernel` is **real under `.cfo/cfo_kernel/`**. It is not under `.cfo-v2/`.

| Piece | Path | Real? |
| --- | --- | --- |
| Entry | `.cfo/cfo_kernel/__main__.py` | Yes |
| Computer remap | `.cfo/cfo_kernel/paths.py` `attach_computer` | Yes. `DATA_DIR` → `$HARNESS_COMPUTER/data`. `RUNS` → `$HARNESS_COMPUTER/runs` |
| Grant re-check | `.cfo/cfo_kernel/grants.py` `authorize` | Yes. Called from `rpc.py` on every op |
| SoD belt | `sod_forbid` (ap/prepare vs accrual writes, ctl-pay vs RECORD_TOOLS, audit vs ground truth) | Yes |
| Overlay persist | `configure_overlay_path(runs/ingestion/overlay.json)` plus cash cases, BS packets, month_end, AR | Code is real. Session 02 pytest proved overlay survive restart. **This Computer has no `kernel.port` and no `runs/ingestion/`** |
| Default Computer | `REPO_ROOT / ".cfo-v2" / "office" / "computer"` | Yes |

Sidecar is not a Bot. It ignores `HARNESS_BOT`. It does not drain inboxes.

Live Bots that skipped Sidecar env still hit `.cfo/runs` (session 12 close CLI wrote `.cfo/runs/month_end/2026-09.json`). `RUN.md` says do not point live Bots at `.cfo/runs`. The documented close demo command does exactly that (`python3 main.py close-month` chdirs into `.cfo/`).

---

## 7. Session PROOF.md 00–12 — claimed vs proven

Every proof file except none of them claims live Pi. Repeated line: **Handle completion was not live-proven. Pi was not live-proven.**

| Session | Claim | What actually ran |
| --- | --- | --- |
| 00 | Law, Roster skeleton, 15 BOT.md | JSON parse + Harness `parseRoster`. Catalog/Grants were already filled by a parallel session 01 |
| 01 | Compiler + Client attach | `python3 compiler`, `npm test` 8 then 12 facade tests. **Pi command written, not driven** |
| 02 | Sidecar | pytest 14 / 25. Overlay persist. No `HARNESS_BOT` |
| 03 | Source Bots | pytest 56. Disk packets under `sessions/03-disk/`. Send payloads are JSON, not Harness Handles |
| 04 | Bot `ap` | pytest 55. Kernel host. `Runner.run_sync` string absent from `workflow.py`; `run_agent` still imported |
| 05 | Bot `pay` | pytest 17. Kernel host. Fake Handle payload `done False` |
| 06 | `apply` / `collect` | pytest 75 / 9. Kernel `HUMAN_REVIEW` → ctl-cash payload |
| 07 | Bot `cash` | pytest 16+20. Writes `runs/cash_recon/handles/*.json` (**Kernel-shaped**, not Harness Handle files) |
| 08 | Bot `close` | Grant SoD + pytest close host. September stays BLOCKED |
| 09 | Verifiers | pytest 21 + facade 12. Client intercept unit test. No live Handle complete |
| 10 | Bot `story` | pytest 31. Compiler to `/tmp`. Import fix in `scheduling/host.py` |
| 11 | Bot `audit` | pytest 22. Operational Grants omit ground truth |
| 12 | Stitch | pytest 17 + facade 12 + `fake_handles.mjs` + close-month BLOCKED |

**Fake vs live:**

- `office/tests/fake_handles.mjs` imports Harness `send.ts` and writes real Harness Handle files with `status: "accepted"`. Accept is not complete. No Pi.
- Facade tests mock bind. They do not start Sidecar HTTP.
- `serve --fake` would echo-complete inboxes. That is Harness `startFakeWorkers`, not GrokBot-class, and it is not what session 12 left on disk (inboxes still `pending`).

`09-PROOF.md` **is** on disk. Session 12 text that said it was missing is stale.

---

## 8. BOT.md quality and Computer cwd

Bodies are real (identity, Wake, object, Profiles, Catalog ops, Kernel, handoffs, Verifier, Memory, must-not, done-when). Identity line form: `You are Bot \`<slug>\`. …`

Harness injects `bot.instructions` via `src/prompt.ts` `identityBlock`. Those instructions all say:

`Read office/bots/<slug>/BOT.md and obey office/constitution.md`

Computer cwd is `office/computer`. From that cwd:

| Path in instructions | Resolves to | Exists? |
| --- | --- | --- |
| `office/bots/email/BOT.md` | `office/computer/office/bots/email/BOT.md` | **No** |
| `office/constitution.md` | `office/computer/office/constitution.md` | **No** |
| actual BOT.md | `../bots/email/BOT.md` | Yes |
| actual constitution | `../constitution.md` | Yes |

There is no symlink of `office/bots` or `constitution.md` onto the Computer. Pi file tools that stay inside Computer cannot read BOT.md at the path the Roster names.

Profile markdown under `office/bots/<slug>/profiles/` has the same problem.

Harness also tells the model: `Named connectors (not a live facade in this cut)`. Real Connectors are Client tools, and only if the Client extension loaded.

---

## 9. Protocol: who writes Handles / inboxes

Harness write path (real code): `sendPrompt` → Handle file + `inbox.jsonl` + `protocol.jsonl`. `completeTurn` (Pi lane or fake worker) sets `completed`.

What is on this Computer:

| Artifact | Count / status | Writer |
| --- | --- | --- |
| `protocol.jsonl` | 4 events, all `type: send.accepted` | `fake_handles.mjs` → Harness `sendPrompt` (twice) |
| Handle files | 4, all `status: accepted` | Same |
| `inbox.jsonl` | `bot_ap` 2 pending, `bot_ctl_pay` 2 pending | Same |
| `transcript.jsonl` | `bot_ap`, `bot_email` only | Side effect of send |
| `lane.json` | none | No bindLane / no Pi |
| Room logs | none | No Room Host |
| Receipts | none | No `fireRoutine` |
| `workspace/verifier/` | missing | Client intercept never ran against this Computer |
| `runs/cash_recon/handles/` | Kernel session-07 JSON | Not Harness |

No `turn.end`. No `completed`. No `failed`. Accept ≠ complete holds, because nobody completed.

`send.ts` in the Client (`extensions/send.ts`) dynamic-imports `$HARNESS_V2_ROOT/src/send.ts`. If `HARNESS_V2_ROOT` is unset (serve workers), `sendPeerHandle` returns `null`. Intercept still writes a packet path and a **Client pending file** under `workspace/verifier/handles/`. `completedHandleAllowsOp` looks at that Client file (`status === "completed" && decision === "CONCUR"`), **not** at the Harness Handle. A Verifier finishing a Harness Handle does not unlock the Kernel op.

### Does v2 ever get `HARNESS_BOT` / `HARNESS_COMPUTER` / extra extensions for these 15?

Only if an operator exports them or uses `pi-bot.sh` one slug at a time. Documented `serve --fake` sets `--computer` (hence `HARNESS_COMPUTER` inside the server) and does not spawn Pi, so workers never see `HARNESS_BOT`. Supervisor (non-fake) sets `HARNESS_BOT` and `HARNESS_COMPUTER` per child. It does not set `HARNESS_EXTRA_EXTENSIONS`, `HARNESS_CLIENT_SKILLS`, or `HARNESS_V2_ROOT`.

---

## 10. What still uses OpenAI Agents SDK `Agent()` / `Runner` as the bus

**`.cfo-v2`:** compiler AST-parses `Agent(` text. It does not import `agents` and does not call `Runner`.

**`.cfo/` still constructs and runs them.** 19 files contain `Agent(`. `Runner.run_sync` lives in `.cfo/agent.py` `run_agent()`. Callers:

- `.cfo/workflow.py` (AP host still `from agent import … run_agent`)
- `.cfo/invoice_ingestion/sources.py`
- `.cfo/scheduling/agent.py`
- `.cfo/ar/workflow.py`
- `.cfo/cash_recon/workflow.py`
- `.cfo/accrual/workflow.py`
- `.cfo/prepaid/workflow.py`
- `.cfo/fixed_assets/workflow.py`
- `.cfo/bs_recon/workflow.py`
- `.cfo/close/agents.py`, `.cfo/close/eval_harness.py`
- `.cfo/reporting/workflow.py`
- `.cfo/audit/workflow.py`
- sample-data `build_agent`

Constitution SUPERSEDES §4 voids in-process `Runner` as the Bot bus. Kernel hosts were not rewritten off `run_agent`. Session 04’s grep that `Runner.run_sync` is absent from `workflow.py` is a string check. The function still calls `run_agent`.

Compiler still **needs** those `Agent(..., tools=[...])` constructors as the Grant source. That is allowed. Calling `Runner.run_sync` as the office bus is not migrated.

---

## 11. slug-map, Catalog, Grants

Compiled and populated. Not empty session-00 placeholders.

| File | Contents |
| --- | --- |
| `cfo/catalog.json` | version `1`, **80** ops, 1 `evalOnly` (`audit.tools.get_audit_ground_truth`) |
| `cfo/grants.json` | version `1`, **43** `byDisplayName`. 35 with ops, 8 with `ops: []` (Close Manager, Month-End Close Reviewer, Audit Report Agent, 5 sample-data) |
| `cfo/grants.eval.json` | Same 43. Auditor Agent keeps ground truth |
| `cfo/slug-map.json` | 15 bots, `defaultProfile` on each, Profiles are objects not lists |
| `cfo/catalog.overrides.json` | mutability + `grantDenylist` (session 09) |
| `cfo/handle-map.json` | 22 edges, grain slugs only |

Stripe Profile `payout` Display name is `""`. Bind refuses Connectors (`missing_display_name`). Matches grain / WATCH item 1.

### Fragments vs merged

Harness/Client load **merged** `grants.json` / `slug-map.json` / `catalog.json`. Leftovers (not loaded):

- `grants.ap.json`, `grants.apply.json`, `grants.cash.json`, `grants.close.json`, `grants.story.json`
- `grants-fragments/pay.json`, `grants-fragments/apply-collect.json`
- `slug-map.ap.json`, `slug-map.cash.json`, `slug-map-fragment.json`

`grants.ap.json` is a slice, not a second SoT, unless a human points the Sidecar at it (nothing does).

---

## 12. Verifier routing vs `ask_user`

| Mechanism | Where | Real? |
| --- | --- | --- |
| Roster `approvalLevel: "never"` | merged Roster | Yes. All 15 |
| Block Pi `ask_user` | Client `index.ts` `tool_call` hook | Yes, **if Client extension loaded** |
| Consequential Kernel op → `verifier_required` | `call.ts` + `verifier.ts` | Unit-tested. Routes `ctl-books` / `ctl-cash` / `ctl-pay` |
| `queue-owners.json` | `cfo/queue-owners.json` | Data. `HUMAN_REVIEW` → Verifier slugs |
| Harness `ask_user` / `waitForApproval` | Harness extension still registers them | Still on the protocol surface (`WATCH.md` item 10) |
| Production `ask_user(` | Client hosts, compiler, `cfo_kernel`, BOT.md | Grep empty. Tests assert absence |

Kernel status `HUMAN_REVIEW` remains fail-closed. Queue owner in product law is a Verifier. Kernel CLI `ar-review-correct` and `demo_month_end_close.py --resolve` remain as emergency tools (`SUPERSEDES.md`).

Without the Client extension, a Harness-only Pi Bot still has `ask_user`. `approvalLevel: "never"` is prompt text in this Harness cut (`docs/CFO_HARNESS_EXTENSION.md` §2: skills/connectors/approvalLevel do not filter Pi tools).

---

## 13. Boot path: `RUN.md` commands that fail, and why

Commands are from repo root unless noted. Aircraft-strict.

### Step 0 — one-time

1. `python3 -m pip install -r requirements.txt`  
   Root file is `-r .cfo/requirements.txt`. Works if pip can see it.
2. `cd .harness/Harness-v2 && npm install`  
   `node_modules` and `dist/src/cli.js` already exist here.
3. `cd .cfo-v2/office/computer/cfo && npm install`  
   Installs `typebox` only. Does not install Pi.
4. `ln -sfn ../../../.cfo/data .cfo-v2/office/computer/data`  
   Already present.

### Step 1 — compile

`PYTHONPATH=.cfo-v2/office python3 -m compiler --phase operational`

This **works** (`import compiler` resolved). Writes Catalog/Grants. Exit 1 if a constructor tool cannot resolve.

### Step 2 — Sidecar

```bash
PYTHONPATH=.cfo \
  HARNESS_COMPUTER="$PWD/.cfo-v2/office/computer" \
  python3 -m cfo_kernel --computer "$PWD/.cfo-v2/office/computer"
```

Needs Kernel deps (fastapi/uvicorn) on **that** `python3`. Session proofs used `.cfo/.venv/bin/python`. System `python3` may miss them. Data symlink must exist (it does). After a successful start, `cfo/kernel.port` appears. **It is not on disk now.** Client `callSidecar` then returns `sidecar_unavailable`.

### Step 3 — Harness + Client (the boot that is supposed to be fifteen Bots)

Documented:

```bash
cd .harness/Harness-v2
npm run serve -- --computer ../../.cfo-v2/office/computer --fake --no-open
```

This command:

1. Starts HTTP on `127.0.0.1:8787` if the port is free.
2. Loads the **real** fifteen-Bot Roster (`initComputer` / `loadRoster`).
3. Starts **fake** workers that complete inboxes with `` `[${slug}] ${prompt}` ``. No model. No Kernel. No Client tools.
4. Does **not** spawn Pi. Supervisor is skipped when `--fake`.
5. Does **not** set `HARNESS_EXTRA_EXTENSIONS`.
6. Does **not** start Sidecar.
7. If you already ran `fake_handles.mjs`, fake workers will **complete** those pending Handles with echo text. That is a protocol demo. It is not fifteen finance Bots.

`pi-bot.sh ap` binds **one** Bot with both extensions. It is not a floor of 15. Unbound Pi (`pi` with no `HARNESS_BOT`) registers no CFO tools.

Drop `--fake` without extra env: Supervisor tries fifteen RPC Pi processes with **only** the Harness extension. No Catalog. No Grants. No Sidecar door. `resolvePiCli` can find `pi-coding-agent`. API keys come from `~/.harness/config.json`. If `spawnPolicy` there is `"fake"`, `--fake` is implied even without the flag (`cli.ts`).

### Step 4 — Routines

```bash
npx harness routine weekly-pay-run --computer ../../.cfo-v2/office/computer
```

From `.harness/Harness-v2`, after `npm install`, local `bin/harness.js` exists. `fireRoutine` will accept and enqueue **if** dist is built. Auto-cadence for `weekly` / `monthly` will not run (see §2). With `--fake` serve, echo workers may complete the inbox without Kernel work.

### Step 5 — eval

`python3 main.py evaluate-cfo`  
Repo-root shim chdirs into `.cfo/` and runs Kernel eval. It is not a Bot. Operational phase isolation is pytest-proven. Session 12 did not run the full CLI.

### Step 6 — close demo

`python3 main.py close-month --month 2026-09 --seed-demo --deterministic`  
Runs in `.cfo/`, writes `.cfo/runs/`, stays BLOCKED on $12.40. Honest. Not a Harness Routine. Not a Verifier Handle.

---

## 14. Harness protocol fields this Client never fills

| Field / object | Harness writer | This Computer |
| --- | --- | --- |
| Handle `accepted` | `sendPrompt` | 4 files from fake_handles |
| Handle `completed` / `failed` / `blocked` | Pi `completeTurn` or fake worker | **Never** |
| Inbox `pending` → `claimed` → `done` | Lane drain | Stuck `pending` |
| `protocol.jsonl` `turn.end` | Lane | Missing |
| Memory `MEMORY.md` | `initComputer` creates default | 15 files. `bot_pay` and `bot_audit` have custom standing notes. Others are the default one-liner |
| Memory topics / log | Pi memory tools | Empty dirs |
| Rooms 2–6 | Roster JSON only | Dirs empty. No Host |
| Routines registered with running Harness | Supervisor `cadenceToMs` + `fireRoutine` | JSON present. Timers skip weekly/monthly. Receipts empty |
| Approvals | Harness `ask`/`always` | `approvalLevel` never. Approvals dir empty |
| `lane.json` | `bindLane` | Missing |
| `pi-session/` | Supervisor spawn | Missing |

Client pending files (`workspace/verifier/handles`) are a second schema (`decision: CONCUR`). Nothing in Harness writes them. Nothing on disk has them.

---

## What is real

1. Fifteen grain slugs, ids `bot_*`, `approvalLevel: "never"`, Rooms 2–6, no `ingest`.
2. Merged Roster at the path Harness `loadRoster` reads. Shape matches `BotRecord`.
3. BOT.md + Profile files for every slug (not stubs).
4. Compiler: 80 Catalog ops, 43 Display names, SoD split AP Preparer ≠ AP Approver, operational Grants omit `get_audit_ground_truth`.
5. Slug-map with Profiles and `defaultProfile`. Stripe empty Display name is intentional.
6. Client extension modules + two-`-e` launcher `pi-bot.sh`.
7. Sidecar package under `.cfo/cfo_kernel/` with Grant re-check and Computer remap.
8. Kernel math, `$12.40` fail-closed close, eval isolation tests.
9. `ask_user(` absent from production hosts. Verifier routing table exists in Client code.
10. Data symlink `computer/data` → `.cfo/data`.

## What is disconnected from Harness

1. Documented boot is `--fake`. Fifteen Pi processes with Client attach are not a RUN.md command.
2. `HARNESS_EXTRA_EXTENSIONS` / `HARNESS_CLIENT_SKILLS` / `HARNESS_V2_ROOT` unset on `serve`.
3. BOT.md and constitution paths in `instructions` sit **outside** Computer cwd.
4. Two Handle stores. Harness complete does not satisfy Client `completedHandleAllowsOp`.
5. Kernel `runs/cash_recon/handles` and `source_wakes` send JSON are not Harness protocol.
6. Routine cadences `weekly`/`monthly` are not Harness cadences.
7. Harness tests still prove `examples/cfo-floor` / `FLOOR_ROSTER`, not this office.
8. `docs/LAYOUT.md` does not list `.cfo-v2/`.
9. Roster `connectors` for Operator Bots are Kernel op ids (`tools.get_invoice`, …). Grain Connectors are providers (`gmail`, `stripe`). Harness treats the field as prompt text either way.
10. Domain workflows in `.cfo/**/workflow.py` still call `run_agent` → `Runner.run_sync`.

## Missing skills / Roster / protocol (precise)

Roster is **not** missing. Protocol **types** are not missing. Skills are **mostly** copied.

Still missing for a live floor:

- 3 Kernel skills not on the Computer, including Roster-named `month-end-close-review`
- Handle `completed` from a bound Pi
- Inbox drain by fifteen workers with Client tools
- Room logs, Receipts, `lane.json`, `kernel.port`
- Extra-extension env on the serve path
- A Computer-visible path to BOT.md / constitution

## Extension modularity

Not “one barrel instead of files.” The Client is 14 TypeScript modules plus `index.ts`. The fail is attach: Harness does not load that tree unless `-e` / `HARNESS_EXTRA_EXTENSIONS` is passed. `pi-api.ts` duck-types Pi. Tests never load Pi.

## What still works as Kernel

Python under `.cfo/` still runs: candidates, cents, `must_hold`, `evaluate_close_gates`, period lock, AR/AP/cash/close/audit pytest, Sidecar RPC when started, overlay remap, Grant `authorize`. `main.py` shims still chdir into `.cfo/`. OpenAI `Agent()` constructors remain the Grant source **and** the in-process bus for those hosts.

---

## Severity-ordered gaps

1. **No fifteen-Pi boot.** `RUN.md` serve uses `--fake`. Extra Client `-e` is not on that command. The office cannot start as 15 bound Pi Bots as documented.
2. **Client extension is dead on the documented bus.** Without `HARNESS_EXTRA_EXTENSIONS` + `HARNESS_CLIENT_SKILLS=1`, workers have Harness protocol tools only. No Catalog filter. No Sidecar. `ask_user` is not blocked.
3. **Handle complete never proven on live Pi.** Disk: 4 accepted Handles, pending inboxes. Client CONCUR file is a different path from Harness Handle complete.
4. **OpenAI `Runner` is still the Kernel workflow bus.** Constitution voided it. `.cfo/**/workflow.py` still calls `run_agent`.
5. **BOT.md is outside Computer cwd.** Roster tells Pi to read `office/bots/...` from `office/computer`. That path does not exist.
6. **Sidecar is not up.** No `kernel.port`. Even a correctly bound Pi gets `sidecar_unavailable` until step 2 runs (and stays running).
7. **Routines do not auto-fire.** `weekly` / `monthly` are unknown to `cadenceToMs`. Receipts empty.
8. **Skills incomplete on the Computer.** 28/31. `month-end-close-review` is on `ctl-books` Roster and missing from `computer/skills/`. One empty spaced directory is a bad copy.
9. **Verifier unlock ignores Harness Handles.** `completedHandleAllowsOp` reads `workspace/verifier/handles`.
10. **Stripe has no Grants.** Intentional per grain. Bot `stripe` cannot `call_connected_tool` anything.
11. **Close demo writes `.cfo/runs`**, not `$HARNESS_COMPUTER/runs`.
12. **Fragment JSON still litters** `cfo/` and `bots/`. Harmless unless someone loads a fragment as the Roster.
13. **`docs/LAYOUT.md` and Harness tests** still describe `.cfo/` + `cfo-floor`, not this office.

---

## Do not confuse with `examples/cfo-floor`

That example proves Handles with six slugs and fake workers. This office’s Roster is fifteen grain slugs under `.cfo-v2/office/computer`. Sharing names `ap`, `cash`, `close`, `audit` does not make the fixture the product.

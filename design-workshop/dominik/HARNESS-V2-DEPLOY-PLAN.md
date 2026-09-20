# Harness v2 deploy plan — 15-Bot CFO Client

Date: 2026-09-19.
Repo: `/Users/dominikbach/olympus/hackmit/hackmit26`.
One file. Evidence from trees named below. No other files edited.

## Name map

Use these names only.

| Name | Meaning |
| --- | --- |
| Harness | Runtime at `.harness/Harness-v2`. Roster, lanes, Handles, Rooms, Memory, Routines, HTTP |
| v1 | Foundry package at `.harness/Harness-v1` |
| Client | Office of the CFO at `.cfo-v2/office` |
| Computer | Shared files for one Client. Bind with `HARNESS_COMPUTER`. Live Computer is `.cfo-v2/office/computer` |
| Bot | Standing identity. One process. One lane. `HARNESS_BOT=<slug>` |
| child | Disposable inner helper. Not a Bot |
| Extension | A Pi module loaded with `-e` |
| Roster | Durable Bot list. v2 file is `harness/roster.json` |
| Handle | Accept-time record. `accepted` is not done |
| Host | Harness code that wakes Room members in order. Not a Bot |
| Operator | Human at the HTTP control plane. Emergency stop. Not a worker |
| Verifier | Client Bot that owns concurrence: `ctl-pay`, `ctl-cash`, `ctl-books` |
| Profile | One Grant set on one Bot. A Wake names a Profile |
| Grant | Catalog ids for one Display name. Client file `cfo/grants.json` |
| Kernel | Python engine behind the Client sidecar |
| cfo-floor | Six-Bot Harness example at `.harness/Harness-v2/examples/cfo-floor`. Not the office |

A child is not a Bot. A Handle is not a Receipt. Memory is not the Computer. The Host is not a Bot. cfo-floor is not the office Roster.

---

## Claim under test

The human believes v1 composed many Foundry Extensions (roster, comms, memory, routines, approvals) and v2 collapsed to one `extensions/index.ts`, so a Client cannot compose systems at scale.

**Verdict.** Half right.

v1 composed **Harness layers** inside one Pi package. It did not compose Client systems. There is no Client Extension tree in v1.

v2 moved those layers into `src/` and kept **one** Harness Extension entry. That is the right split. The hole is different: `serve` / supervisor still treat Client Extensions as an optional env string, skill loading still dumps the whole Computer skills directory, and the intercept still parks on the Operator. That last point blocks Verifier routing.

Do not put finance types in Harness `src/`. Do not bring children back as the Bot network.

---

## 1. v1 Extension inventory

Tree: `.harness/Harness-v1/extensions/`.

| File | Avenue | Registers |
| --- | --- | --- |
| `lib/manifest.ts` | load | No tools. Loads Foundry JSON. Builds protocol prompt |
| `foundry-roster.ts` | write | Tools `bot_search_agents`, `bot_get_profile`. Command `/foundry-roster` |
| `foundry-comms.ts` | write + steal | Tools `bot_send_prompt`, `bot_await_turn`. Also loads Timur00Kh `agent-room` |
| `foundry-subagents.ts` | choose | `registerSubagents(pi)` from `pi-subagents`. On `session_start`, `registerAgent` each roster slug as a **child** |
| `foundry-memory.ts` | write | Tools `memory_read`, `memory_write` |
| `foundry-routines.ts` | write | Tool `routine_list`. Command `/foundry-routine` |
| `foundry-approvals.ts` | write | Tool `ask_user` (`ctx.ui.confirm`) |

`package.json#pi.extensions` load order:

1. `./extensions/foundry-roster.ts`
2. `./extensions/foundry-comms.ts`
3. `./extensions/foundry-subagents.ts`
4. `./extensions/foundry-memory.ts`
5. `./extensions/foundry-routines.ts`
6. `./extensions/foundry-approvals.ts`
7. `./node_modules/@narumitw/pi-usage/dist/index.ts`

That is how v1 composed many `-e` modules: **Pi package install**, not a Client flag. `pi install` then `pi`. README does not document extra CLI `-e`. A second Client package would have required a fork of this list or a second `pi install`.

### How v1 loaded the Roster

`extensions/lib/manifest.ts` `loadManifest()` tries, in order:

1. `process.env.FOUNDRY_OUTPUT`
2. `<cwd>/foundry-output.json`
3. `<cwd>/foundry-output/aegis.json`
4. package `foundry-output/aegis.json`

**There is no `roster.md` loader.** Grep of `.harness/Harness-v1` finds zero `roster.md`. Identity is Foundry JSON. Not `~/.pi/agent/agents`. Not `roster.json`.

Sample shape: `.harness/Harness-v1/foundry-output/aegis.json`. Fields: `system`, `version`, `description`, `bots[]` (`id`, `name`, `slug`, `purpose`, `instructions`, `skills`, `connectors`, `approvalLevel`), `rooms[]` (`title`, `host`, `members`), `routines[]` (`name`, `bot`, `cadence`, `prompt`). Rooms have a `host` Bot slug. Rooms have no `id`. Routines have no `conversation`.

### Tools and commands (v1, including stolen packages)

Foundry-owned tools:

- `bot_search_agents(query)`
- `bot_get_profile(bot_id)`
- `bot_send_prompt(bot_id, prompt)` — writes `accepted`, then RPC-spawns a child
- `bot_await_turn(handle_id)` — reads the handle file
- `memory_read(path)` / `memory_write(path, content)` — shared `getAgentDir()/foundry/memory/`
- `routine_list()`
- `ask_user(action, detail)` — Operator confirm

Foundry-owned commands:

- `/foundry-roster`
- `/foundry-routine [name]` — injects into the **current** session as follow-up

From `pi-subagents` (loaded by `foundry-subagents.ts`): `/subagents`, `/agents`, `/run`, `/subagents-doctor`, `/subagent-cost`, tool `subagent`.

From `agent-room` (loaded by `foundry-comms.ts`): `/room`, tools `room_whoami`, `room_list_agents`, `room_send_message`, `room_control_agent`, `room_read_agent_history`, `room_summarize_agent`.

From `@narumitw/pi-usage`: `/usage`.

Pike live drive (`GROK-WORKSHOP/harness-init/engineers/pike/DRIVE-REPORT.md`): all six Foundry files plus `dist` (pi-usage) loaded. `/foundry-roster` printed `Aegis: atropos, clio, hermes, hephaestus`. `/foundry-routine` wrote a receipt then crashed: `ctx.sendUserMessage is not a function`. `bot_send_prompt` / `bot_search_agents` never appeared as `toolCall` in the host session. Handle files never reached `completed|failed|cancelled` because `foundry-comms.ts` never writes those statuses. Communication that worked was **agent-room hostname-pid chat** and **child spawn** (`/run clio`, `subagent hephaestus`). That is not the Handle protocol.

Operator note (`Operator-workspace/Prompts/Harness analysis.md`, read only): the human asked whether Bots could talk, where logs go, and called the Foundry Extensions lightweight. Pike confirmed the Handle layer did not function.

---

## 2. v2 inventory (deploy target)

Tree: `.harness/Harness-v2/`.

### Single Extension entry

`package.json#pi.extensions`:

```json
["./extensions/index.ts"]
```

`extensions/index.ts` is the only Harness Extension. It imports `src/` and registers protocol tools **after** `resolveBind` succeeds. Unbound Pi (`HARNESS_BOT` missing) registers `/bot` and `/whoami` only, then returns.

### Tools (bound Bot)

From `registerTools` in `extensions/index.ts`:

| Tool | Parameters |
| --- | --- |
| `bot_search_agents` | `query`, optional `status` |
| `bot_get_profile` | `bot_id` |
| `bot_send_prompt` | `bot_id`, `prompt`, optional `mode`, `on_busy`, `paths` |
| `bot_await_turn` | `handle_id` |
| `bot_get_agent_transcript_tail` | `bot_id`, optional `limit`, `before_seq`, `query` |
| `room_post` | `room_id`, `text` |
| `room_read_log` | `room_id` |
| `memory_read` | optional `path` (this Bot only) |
| `memory_write` | `path`, `content` |
| `ask_user` | `action`, `detail` — Operator confirm or `waitForApproval` |

HARNESS-V2.md also lists `conversation?` on `bot_send_prompt`. The registered tool **omits** `conversation`. `src/send.ts` accepts it on the library call. The model cannot pass it.

Missing vs v1: `routine_list`. Fire is CLI / `/routine run <name>` / HTTP, not a model tool.

### Commands (bound Bot)

`/bot`, `/whoami`, `/roster`, `/handles`, `/room` (list membership, does not attach), `/stop`, `/protocol`, `/routine run <name>`.

### CLI (`src/cli.ts`)

`serve`, `bot`, `send`, `stop`, `await`, `handle`, `roster`, `protocol`, `routine`, `floor`.

`harness bot <slug>` spawns:

```text
pi -e <extensionEntryPath()> ...extraExtensionArgs() --name <slug>
```

Env: `HARNESS_BOT`, `HARNESS_COMPUTER`.

`floor` **prints** one `-e` line per Bot. It does not print `extraExtensionArgs()`.

### Extra Extensions (`src/pkg.ts`)

```31:44:.harness/Harness-v2/src/pkg.ts
export function extraExtensionArgs(env: NodeJS.ProcessEnv = process.env): string[] {
  const raw = env.HARNESS_EXTRA_EXTENSIONS?.trim();
  if (!raw) {
    return [];
  }
  const args: string[] = [];
  for (const item of raw.split(/[:;,]/)) {
    const path = item.trim();
    if (path.length > 0) {
      args.push("-e", path);
    }
  }
  return args;
}
```

Colon, comma, or semicolon. More than one Client `-e` **already parses**. `src/index.ts` does **not** re-export this function. No test file mentions `HARNESS_EXTRA_EXTENSIONS`. Session 01 added it (`.cfo-v2/office/sessions/01-PROOF.md`).

### Bind (`src/bind.ts`)

`resolveBind`:

1. Computer = `HARNESS_COMPUTER` or cwd.
2. Slug = `HARNESS_BOT`. Missing → `{ ok: false, reason: "unbound" }`.
3. `loadRoster(computerRoot)`.
4. `findBot`. Missing → `{ ok: false, reason: "unknown" }`.

No Grant filter. No Profile. No skill intersect. No hook a Client can register.

### Roster (`src/roster.ts`, `src/types.ts`)

`resolveRosterFile`:

1. `HARNESS_ROSTER` (absolute, or relative to Computer)
2. `<computer>/harness/roster.json`
3. `<computer>/roster.json`

Required Bot fields: `id`, `slug`, `name`. Optional: `purpose`, `instructions`, `skills`, `connectors`, `approvalLevel` (default `ask`). Rooms: `id` required, `members.length` in **2–6** or the room is dropped. Routines: `name` and `bot` required. `conversation` defaults to `operator_dm`.

### Supervisor and fake workers

`src/server/supervisor.ts` `spawnBot` **does** pass `...extraExtensionArgs(env)` into `pi --mode rpc`. Env comes from `piEnvFromConfig`, which copies `process.env` and overlays API keys. If the Operator starts `serve` **without** `HARNESS_EXTRA_EXTENSIONS` in the environment, workers get **only** the Harness Extension.

`src/server/operator-config.ts` has `spawnPolicy`, `port`, `provider`, `model`, `apiKeys`, `openBrowser`. **No** extra-Extension field. `PATCH /api/config` cannot persist Client `-e` paths.

`src/worker.ts` `startFakeWorkers` drains inboxes in-process. No Pi. No Client Extension. `src/server/http.ts`: `--fake` (or config `spawnPolicy === "fake"`) starts fake workers and **does not** start the supervisor.

Default `serve` without `--fake` / `--lazy` tries live `pi --mode rpc` per Bot (`spawnPolicy` default `eager`). README demo still ships `--fake`.

### Prompt and approvals

`src/prompt.ts` `identityBlock`: standing Bot, not a child, Roster peers, Handle protocol. Skills allowlist is **text**. Connectors are "not a live facade in this cut."

`src/approvals.ts` `isConsequential`: delete-tree always. `always` = every `bash`/`write`/`edit`. `ask` = side-effect bash (`sudo`, `git push`, `send-as-user`, `ach pay`, `publish`, …). `never` = delete-tree only.

`extensions/index.ts` `tool_call`: if consequential, `createApproval`, `blockTurn`, then Operator `ctx.ui.confirm` (TUI) or `waitForApproval` (headless). Denied → `denied by Operator`. `ask_user` is the same Operator path.

`skills/harness/SKILL.md`: "`blocked` means the Operator, not done."

### Skill loading (this fights the Client)

```170:178:.harness/Harness-v2/extensions/index.ts
  pi.on("resources_discover", () => {
    const skillPaths = [`${harnessPackageRoot()}/skills`];
    const computerSkills = join(bind.computerRoot, "skills");
    // Client systems that filter skills themselves set HARNESS_CLIENT_SKILLS=1.
    // Otherwise a whole-directory skillPaths entry would ignore the Bot allowlist.
    if (existsSync(computerSkills) && process.env.HARNESS_CLIENT_SKILLS !== "1") {
      skillPaths.push(computerSkills);
    }
    return { skillPaths };
  });
```

HARNESS-V2.md: "Pi skills, loaded per Bot from that Bot's allowlist." Today the allowlist is a prompt sentence. The filesystem load is the **whole** `<computer>/skills` unless `HARNESS_CLIENT_SKILLS=1`.

### `ui/` — OpenMausBot-scale copy

Not OpenGrok source. README: "OpenMausBot-shaped." `ui/NOTICE` is OpenMausBot Apache-2.0. `ui/src` holds about 296 `.ts`/`.tsx` files (skins, phone pairing, webhooks, PostHog, onboarding reel, local VM). `src/server/omb-compat.ts` plus `src/server/api.ts` expose `/api/*` for that shell. `/v1/*` is the control plane (`roster`, `bots/:slug/prompt`, `handles`, `protocol`, `approvals`, `receipts`, SSE).

**Deploy:** `/v1` HTTP and SSE stay in the bus. The OpenMausBot clone is **out** of the 15-Bot bus critical path. It is an optional overlay. Constitution: the Operator is an emergency stop, not a worker.

### Tests vs the office

`tests/cfo-scale.test.ts` and `tests/helpers.ts` `CFO_ROSTER` are the **six-slug fixture** (`ingest`, `ap`, `ar`, `cash`, `close`, `audit`). Fake workers. Invoice-shaped prompts. This is not `.cfo-v2/office/computer/harness/roster.json`. SUPERSEDES.md voids cfo-floor as the office Roster.

---

## 3. Compare: many `-e` modules vs one entry

| | v1 | v2 today |
| --- | --- | --- |
| How Extensions load | `package.json#pi.extensions` (7 files) after `pi install` | One Harness file. Extra `-e` only if `HARNESS_EXTRA_EXTENSIONS` is already in the process env |
| Roster file | `FOUNDRY_OUTPUT` / `foundry-output.json` / `aegis.json` | `HARNESS_ROSTER` / `harness/roster.json` |
| Bind | None. Every Pi is the same floor | `HARNESS_BOT` required for protocol tools |
| Dispatch | Child spawn (`pi-subagents` RPC) | Disk inbox + Handle. Receiver's process drains |
| Rooms | Live `agent-room` (hostname-pid) | File Host, 2–6 slugs, wait then chip |
| Memory | One shared `foundry/memory/` | Per BotId tree |
| Routines | Inject into whoever is at the keyboard | Owning Bot inbox + Receipt |
| Approvals | Operator `confirm` | Operator `confirm` / approval JSON. Still Operator |
| Client attach | Not designed | Second `-e` plus env. Wrapper exists. `serve` does not persist it |

### How the Client attaches today

Documented in `.cfo-v2/office/computer/cfo/extensions/index.ts` and `.cfo-v2/office/computer/cfo/bin/pi-bot.sh`:

```bash
HARNESS_BOT=ap \
HARNESS_COMPUTER=.cfo-v2/office/computer \
HARNESS_V2_ROOT=.harness/Harness-v2 \
HARNESS_CLIENT_SKILLS=1 \
  pi -e .harness/Harness-v2/extensions/index.ts \
     -e .cfo-v2/office/computer/cfo/extensions/index.ts \
     --name ap
```

Client tools (only when `HARNESS_BOT` is set):

- `search_connected_tools(query, status?)`
- `call_connected_tool(name, args?, idempotency_key?)`

Client also:

- `resources_discover` → Grant skills ∩ Roster skills, per-directory paths
- `input` → Wake `profile:` header **replaces** the Grant set
- `tool_call` → **blocks** Harness `ask_user` ("Verifier Bots own concurrence")

`send.ts` in the Client dynamically imports Harness `src/send.ts` when `HARNESS_V2_ROOT` is set. If that import fails, Kernel intercept still writes a packet file and returns `verifier_required`. Await/done was **not** live-proven (session 01).

### Does `serve` set extra Extensions when spawning workers?

**Only by inheriting the parent environment.** Supervisor passes `extraExtensionArgs(env)`. Operator config has no field. `RUN.md` fake serve:

```bash
npm run serve -- --computer ../../.cfo-v2/office/computer --fake --no-open
```

That line sets neither `HARNESS_EXTRA_EXTENSIONS` nor `HARNESS_CLIENT_SKILLS`. `--fake` also skips Pi, so the Client facade never loads. Live `serve` without those env vars spawns 15 Pi workers with **Harness tools only**. Grants, Profiles, Kernel calls, Verifier intercept: absent.

---

## 4. Protocol vs HARNESS-V2.md

Spec: `GROK-WORKSHOP/harness-init/engineers/lark/HARNESS-V2.md`.

| Spec item | v2 status | Office impact |
| --- | --- | --- |
| accept ≠ complete | **Met** in `src/send.ts` + lane complete. Tests prove it with fake workers | Keep. This is the bus |
| Sender never marks complete | **Met** | Keep |
| `blocking` refused | **Met** | Keep |
| `done` only `completed\|failed\|cancelled` | **Met**. `blocked` is not done | Keep |
| Live Pi per Bot, not children | **Met** in code. Demo still defaults operators toward `--fake` | Fake is not a 15-Bot office |
| HTTP / supervisor / `pi --mode rpc` | **Met** (spec said "later"; now present) | Use live workers for deploy |
| Rooms 2–6, Host waits, chip | **Met** (`parseRoom`, `rooms.ts`) | Office Rooms already 3–4 members |
| Memory per BotId, inject 200 lines / 24 KB | **Met** | Keep |
| Roster search returns slugs, not `agent-host-pid` | **Met** | Keep |
| No Roster slug as child | **Met**. `pi-subagents` is not installed | Do not bring it back |
| Skills from Bot allowlist | **Miss** | Whole `computer/skills` unless env opt-out |
| Connector facade | Spec said later | Client owns it. Do not fork into Harness |
| Human gate on Operator | **Met as specified** | **VOID for this Client.** This blocks Verifiers |
| `bot_send_prompt` `conversation?` | Library yes, tool no | Minor |
| `/room` attach | Spec attach; code lists only | Minor |
| Fake workers | Not in spec | Demo only. Not the bus |

Pike v1 vs this spec: v1 failed accept≠complete, used children as the roster, used hostname-pid rooms. v2 fixed those. The remaining spec conflict with the office is the **Operator-shaped intercept**.

`.cfo-v2/office/SUPERSEDES.md` item 2 voids HARNESS-V2.md's sentence that consequential actions stop on the Operator, **at the office layer**. It also says: do not edit Harness `src` to know invoices. Map concurrence to Verifier slugs in **Client** code. That workaround exists (`intercept.ts`, `verifier.ts`, block `ask_user`). It is not enough: Harness still teaches `ask_user`, still parks `blocked` on the Operator, and still loads all skills.

---

## 5. What v2 MUST change (no finance types)

Generic primitives. Names like invoice, pay-run, and `ctl-pay` stay in the Client.

### 5.1 Extension composition

Today: one Harness Extension plus an untested env string.

Must:

1. Treat `HARNESS_EXTRA_EXTENSIONS` as a first-class serve/supervisor contract. Persist it on Operator config or a Computer-side file such as `harness/extensions.json` (paths only, no domain types).
2. Pass every extra `-e` to `harness bot`, `harness floor` printout, and `pi --mode rpc` workers.
3. Support more than one Client path (parser already splits). Document two `-e` as the attach rule: Harness first, Client second.
4. Test that the spawned argv contains both paths. No test exists now.
5. Export `extraExtensionArgs` from `src/index.ts` so a Client does not import `src/pkg.ts` by relative path.

Do not merge Client `extensions/index.ts` into Harness `extensions/index.ts`.

### 5.2 Client-owned Roster path

`HARNESS_ROSTER` already exists. Default `<computer>/harness/roster.json` already matches the office file.

Must:

1. Document that `serve --computer .cfo-v2/office/computer` is the bind. Do not point `--computer` at `examples/cfo-floor`.
2. Keep `HARNESS_ROSTER` for an out-of-tree file. Do not add a `roster.md` parser.
3. Refuse to start workers if the Roster has zero Bots. Already throws.

### 5.3 Bind hook for Grant filter

Harness bind stays identity (`HARNESS_BOT` + Roster). Grant JSON stays Client.

Must:

1. Stop clobbering Client `resources_discover`. Default: do **not** add the whole `<computer>/skills` directory. Honor `BotRecord.skills` as directory names under that tree (and under Harness `skills/` for the protocol skill). Empty allowlist → Harness protocol skill only.
2. Keep `HARNESS_CLIENT_SKILLS=1` as an explicit "Client owns skillPaths" override, and set it from serve config when extra Extensions are present.
3. Do not parse `cfo/grants.json` in Harness. Profile replace on Wake `profile:` stays Client (`profile.ts`).

### 5.4 Skill intersect

Client already intersects `grant.skills ∩ roster.skills` in `cfo/extensions/skills.ts`.

Must in Harness: load only named skill directories for this Bot. Then the Client intersect is additive, not a fight against a whole-tree dump.

### 5.5 Intercept retargetable to another Bot

This **blocks** Verifier routing.

Today:

- `ask_user` and consequential `tool_call` wait on the Operator.
- Client blocks `ask_user` and reroutes Kernel ops by writing `workspace/verifier/...` plus an optional Harness `sendPrompt`.
- Two Handle stores: Harness `harness/bots/<botId>/handles/` and Client `workspace/verifier/handles/`.
- Roster `approvalLevel: "never"` on all fifteen office Bots limits Harness intercept to delete-tree. The model is still told to call `ask_user`. The skill file still says blocked means Operator.

Must in Harness (generic):

1. Approval target is `operator` **or** a Bot id/slug. New field on the approval record, not a finance enum.
2. When target is a Bot: write a Handle to that Bot's inbox, set the original Handle `blocked`, await **that** Handle to `done`. Do not call `ctx.ui.confirm`.
3. Client supplies the target slug (Verifier table stays in `verifier.ts`). Harness does not know `ctl-*`.
4. `ask_user` may keep Operator as default. A Client Extension may keep blocking it. The intercept API must not force Operator for `tool_call`.
5. Rewrite `skills/harness/SKILL.md`: `blocked` means waiting on the configured approver (Operator or named Bot). A peer Handle is still not approval.

### 5.6 Extra Extensions actually passed to Pi workers

Supervisor already spreads `extraExtensionArgs(env)`. The gap is **config and tests**, not the spawn line. Fake workers never load Extensions. Deploy path is live Pi, not `--fake`.

---

## 6. What belongs where

### Harness owns

- Roster parse and bind (`HARNESS_BOT`, `HARNESS_COMPUTER`, `HARNESS_ROSTER`)
- Inbox, Handle lifecycle, `bot_send_prompt` / `bot_await_turn`, protocol log
- One lane per Bot, user DM preempt, peer queue
- Room Host (2–6), Memory isolation, leases
- Routine fire onto the owning Bot
- Extra `-e` forwarding
- Skill **path** filtering from `BotRecord.skills`
- Intercept primitive: Operator **or** Bot
- `/v1` HTTP, SSE, supervisor, `pi --mode rpc`
- Protocol skill under Harness `skills/harness`

### Client owns

- Fifteen grain slugs, BOT.md, constitution, SUPERSEDES
- `cfo/catalog.json`, `cfo/grants.json`, `cfo/slug-map.json`
- Profiles, Grant intersect, Wake `profile:` header
- `search_connected_tools` / `call_connected_tool`
- Kernel sidecar, cents, candidates, eval isolation
- Verifier routing table (`ctl-pay` / `ctl-cash` / `ctl-books`)
- Path prefixes, Catalog overrides, `CFO_EVAL_PHASE`
- Finance types, invoices, close DAG, specialist names

### Do not put in Harness `src/`

Invoices, ledgers, AP/AR/cash/close pipes, Catalog ops, Grant Display names, Verifier slugs as constants, Kernel RPC, `HUMAN_REVIEW`, cfo-floor's `ingest`/`ar` as product identity.

### Do not put in the Client as a second bus

In-process Runner, `pi-subagents` children as standing Bots, a second Handle store that `awaitTurn` cannot see, `ask_user` as completion.

---

## 7. `foundry-subagents.ts` vs "Bots are not children"

v1 `foundry-subagents.ts`: disable builtins, exclude markdown agent dirs, then `registerAgent({ name: bot.slug })` for every Foundry Bot. `/subagents` overlay showed Atropos/Clio/Hermes/Hephaestus as `[runtime]` children. Pike: `/run clio` and `subagent hephaestus` were the working "Bots." Room ids were `agent-<host>-<pid>`.

HARNESS-V2.md: "A Bot is not a child. The roster is not `pi-subagents` agent names." "Do not register Roster slugs as children." If a Bot needs a throwaway helper, the child has no Roster id, no Memory, no Routines, no lane.

**Do not port `foundry-subagents.ts`.** Do not install `pi-subagents` as the Bot network. Optional inner child stays off by default. The 15 office identities are 15 `HARNESS_BOT` processes.

v2 already follows this. Keep it.

---

## 8. Roster formats — what the Client must emit, what Harness must accept

### v1 Foundry JSON (do not emit this for v2)

- Path: `foundry-output.json` / `FOUNDRY_OUTPUT`
- Rooms: `{ title, host, members }` — **no `id`**, Host is a Bot slug
- Routines: no `conversation`
- No `computer` field required

v2 `parseRoom` **drops** a room with no `id` or with fewer than 2 / more than 6 members. A v1 Floor room with four members and no `id` would vanish.

### v2 Roster JSON (required)

Path the Client already writes: `.cfo-v2/office/computer/harness/roster.json`.

Harness accepts (`src/types.ts` / `parseRoster`):

```json
{
  "system": "cfo-agentic-system",
  "version": "1",
  "description": "…",
  "computer": "office/computer",
  "bots": [
    {
      "id": "bot_ctl_pay",
      "name": "ctl-pay",
      "slug": "ctl-pay",
      "purpose": "one sentence",
      "instructions": "standing duty. Point at BOT.md. Never ask a human.",
      "skills": ["three-way-match-analysis"],
      "connectors": ["tools.get_case_evidence"],
      "approvalLevel": "never"
    }
  ],
  "rooms": [{ "id": "pay", "title": "Pay", "members": ["ap", "pay", "ctl-pay"] }],
  "routines": [{
    "name": "weekly-pay-run",
    "bot": "pay",
    "cadence": "weekly",
    "prompt": "profile: schedule\n…",
    "conversation": "room:pay"
  }]
}
```

Client must emit:

| Field | Rule |
| --- | --- |
| `id` | `bot_` + slug with hyphens → underscores (`ctl-pay` → `bot_ctl_pay`) |
| `slug` | Grain slug. Bind key. Room `members` and Routine `bot` use slug |
| `approvalLevel` | `"never"` on all fifteen |
| Room `id` | Required. 2–6 members. Four office Rooms already match |
| Room `host` | **Omit.** Host is Harness code |
| Routine `conversation` | `room:<roomId>` for office Routines. If omitted, Harness defaults `operator_dm` and wakes look like Operator DMs |
| `skills` | Names that exist as directories. Intersected with Grants by the Client |
| `connectors` | Names for Client search. Harness does not call them |

Harness must accept: current `BotRecord` plus, after Phase 3, no new finance fields. Optional later: `approvalTarget` generic (`operator` \| `{ bot: "<slug>" }`) if intercept config lives on the Bot record. Prefer Computer-side Client config over stuffing Verifier slugs into the Roster.

**`roster.md`:** not a format. Do not add it.

Live office Roster already has 15 Bots, 4 Rooms, 5 Routines. That file is the emit target. Do not copy `examples/cfo-floor/harness/roster.json`.

---

## Sequenced deploy plan

Aircraft-strict. One action per step. Expected result after each phase: the next phase can run.

### Phase 1 — Extra Extensions on the bus

**Goal.** `harness serve` and `harness bot` load Harness **and** every Client `-e`. Fake workers stay a demo switch.

**Change (Harness):**

1. Export `extraExtensionArgs` from `src/index.ts`.
2. Add `extraExtensions: string[]` to `src/server/operator-config.ts`. Load from config file and from `HARNESS_EXTRA_EXTENSIONS`. `piEnvFromConfig` must set that env on children.
3. Keep `src/server/supervisor.ts` spreading `extraExtensionArgs(env)`. Add a unit test that the spawn argv contains `-e` Harness path and each extra path.
4. Update `src/cli.ts` `floor` so printed commands include extra `-e`.
5. When extra Extensions are set, set `HARNESS_CLIENT_SKILLS=1` on workers unless the Operator overrides.
6. Do not start fake workers when the Operator asks for live Pi. Keep `--fake` explicit.

**Change (docs only, later commit):** README serve example with `--computer .cfo-v2/office/computer` and extra Extensions. Not cfo-floor.

**Change (Client):** `RUN.md` live serve must export `HARNESS_EXTRA_EXTENSIONS` and `HARNESS_V2_ROOT`. `pi-bot.sh` already does.

**Done when:** `harness bot ap --computer .cfo-v2/office/computer` with those env vars registers `search_connected_tools`. A supervisor child argv contains both Extension paths. Tests cover argv. No invoice types in Harness.

**Files:** `src/pkg.ts`, `src/index.ts`, `src/cli.ts`, `src/server/operator-config.ts`, `src/server/supervisor.ts`, new `tests/pkg.test.ts` (or extend `tests/cli.test.ts`). Client: `.cfo-v2/office/RUN.md` only.

### Phase 2 — Roster path and skill allowlist

**Goal.** Fifteen Bots bind from the office Roster. Each Bot sees named skills only.

**Change (Harness):**

1. `extensions/index.ts` `resources_discover`: if `HARNESS_CLIENT_SKILLS=1`, Harness protocol skill only (Client adds the rest). Else push `skills/<name>` for each name in `bind.bot.skills`, never the parent directory as one entry.
2. Keep injecting allowlist text in `src/prompt.ts`.
3. Add a test Computer with two skill dirs. Bot A allowlists one. Assert the other dir is not in `skillPaths`.
4. Leave `src/bind.ts` identity-only. No `grants.json`.

**Change (Client):** none required if `HARNESS_CLIENT_SKILLS=1` is set from Phase 1. Keep `intersectSkillNames` in `cfo/extensions/skills.ts`.

**Done when:** Bot `ap` does not receive `board-financial-reporting` from a whole-tree load. Office `harness/roster.json` loads 15 Bots via `loadRoster`. `examples/cfo-floor` still exists as a fixture and is not used as `--computer` for the office.

**Files:** `extensions/index.ts`, `src/prompt.ts`, new test. Do not edit `tests/helpers.ts` `CFO_ROSTER` into the fifteen-Bot office (that would pull grain names into Harness tests). Use a generic two-Bot allowlist fixture.

### Phase 3 — Intercept retarget to a Bot

**Goal.** Consequential work can wait on another Bot. Operator is optional.

**Change (Harness):**

1. Extend `ApprovalRecord` in `src/types.ts` with `approver: { kind: "operator" } | { kind: "bot", botId: string }`. Default `operator`.
2. `src/approvals.ts`: if approver is a Bot, `sendPrompt` to that Bot, return when that Handle is `done`. Do not `ui.confirm`.
3. `extensions/index.ts` `tool_call` and `ask_user`: read approver from a generic hook. Hook source: env `HARNESS_APPROVER_BOT` **or** a small Computer file `harness/intercept.json` shaped `{ "default": "operator", "bots": { "<slug>": { "kind": "bot", "bot": "<slug>" } } }`. No Verifier names in Harness defaults.
4. `skills/harness/SKILL.md`: blocked waits on the configured approver.
5. Tests: Bot alpha consequential intercept → Handle on beta → beta completes → alpha resumes. Operator never called. Peer Handle still is not approval (beta must actually complete).

**Change (Client, after Harness ships the primitive):**

1. Write `harness/intercept.json` (or call the hook) so consequential Kernel ops wait on the Verifier slug from `verifier.ts`.
2. Stop writing a second Handle tree at `workspace/verifier/handles/` as the await source of truth. Keep packets as Computer files. Await the **Harness** Handle.
3. Keep blocking `ask_user` until models stop calling it.

**Done when:** a generic two-Bot test parks on a Bot, not the Operator. Client `call_connected_tool` `create_accrual` still returns `verifier_required` **and** a Harness `handleId` that `bot_await_turn` can watch. Harness source still has no invoice type.

**Files:** `src/types.ts`, `src/approvals.ts`, `src/paths.ts` (optional intercept path), `extensions/index.ts`, `skills/harness/SKILL.md`, `tests/approvals.test.ts`. Client later: `cfo/extensions/intercept.ts`, `cfo/extensions/call.ts`, `cfo/extensions/send.ts`.

### Phase 4 — Live Pi workers for fifteen Bots

**Goal.** Drop `--fake` for the office.

**Change (Harness):**

1. Eager supervisor starts one `pi --mode rpc` per Roster slug (already written). Prove it with the office Computer, not cfo-floor.
2. Lazy policy: start a Bot when inbox pending (already written). Prefer eager for the hackathon so Verifiers are live.
3. Cap is process count, not Room size. 15 processes is valid. Rooms stay ≤6.

**Change (Client):** sidecar up (`python -m cfo_kernel`). Compile Grants. Wrapper `pi-bot.sh` for TUI debug. `HARNESS_BOT` is grain slug.

**Done when:** `GET /v1/roster` shows 15 slugs. `ctl-pay` status is `idle` or `running`, not only fake echo. `bot_send_prompt` from `pay` to `ctl-pay` reaches `completed` without a human editing JSON.

**Files:** mostly runbooks. Harness only if supervisor fails at 15 children (`src/server/supervisor.ts`). Do not add office slugs to `tests/helpers.ts`.

### Phase 5 — Client facade on the live bus

**Goal.** Grants and Kernel calls work inside the bound Pi, not only `npm test` in `cfo/`.

**Change (Client only):**

1. Keep facade tests. Add a live proof: bound `ap` / Profile `prepare` `search_connected_tools` hides `create_accrual`.
2. `sendPeerHandle` must use exported Harness `sendPrompt` (package import or `HARNESS_V2_ROOT`). Returning null is a fail, not a silent packet-only path, for consequential ops.
3. Sidecar errors stay `sidecar_unavailable`. Models do not invent amounts.

**Change (Harness):** none unless the export in Phase 1 is missing.

**Done when:** session-01 proof item "Await/done was not live-proven" is closed on a live Handle.

**Files:** `.cfo-v2/office/computer/cfo/extensions/*.ts`, `.cfo-v2/office/sessions/` proof. Not Harness `src/`.

### Phase 6 — Operator overlay, not the bus

**Goal.** Humans can stop a Bot. Humans cannot complete pay-run.

**In deploy:** `GET/POST /v1/*`, SSE, `harness stop`. Loopback bind.

**Out of deploy critical path:** `ui/` OpenMausBot clone, `omb-compat.ts` product APIs (phone, skins, webhooks, PostHog), auto-open browser, Settings roster editor as the way to add a sixteenth Bot.

**Done when:** office runbook starts `serve --no-open` without `--fake`, with extra Extensions. Browser is optional.

**Files:** `src/cli.ts` help text, `src/server/http.ts` only if `/v1` is broken. Do not delete `ui/` in this plan. Do not require `ui:build` to drain inboxes.

### Phase 7 — Prove the office, then stop editing Harness

Proofs on disk:

1. Fifteen `HARNESS_BOT` processes, one Computer, office `roster.json`.
2. Handle accept then complete across at least `ap` → `ctl-pay` and `close` → `ctl-books`.
3. `protocol.jsonl` answers who sent what and whether it finished.
4. `ask_user` does not unblock money movement.
5. No Roster slug registered as a child (`pi list` / process args have no `pi-subagents` Bot network).
6. Finance types still absent from `.harness/Harness-v2/src`.

If a proof needs a new Harness primitive, it must be nameless of invoices. If it needs a Catalog op, it goes in the Client.

---

## Lost v1 capabilities (honest list)

**Lost on purpose. Do not restore.**

- Six Foundry files plus pi-usage inside the Harness package
- `pi-subagents` as the Bot network (`foundry-subagents.ts`, `/run`, `subagent`)
- Timur00Kh `agent-room` live process rooms and hostname-pid ids
- Shared `foundry/memory/` across Bots
- `/foundry-routine` injecting into the current pane
- `FOUNDRY_OUTPUT` / `foundry-output.json` / `aegis.json` as the office Roster
- Operator `ask_user` as the only concurrence (v1 had this; the office cannot)

**Lost by collapse, must restore as generic Client attach.**

- First-class **multiple** Pi `-e` modules next to Harness (v1 had this for Harness layers; v2 needs it for Client packages)
- Package-manifest composition (`pi.extensions` array). v2 may keep a single Harness entry **if** serve/supervisor always forwards extra `-e`

**v1 never had, do not pretend it was lost.**

- Client-owned Grant filter
- Verifier Bots
- Durable Handle completion written by the receiver
- Per-Bot Memory isolation
- Room Host that waits on a busy member using Roster slugs
- `roster.md`

---

## First three deploy phases (short)

1. **Extra Extensions on the bus** — persist and test `HARNESS_EXTRA_EXTENSIONS` through `serve` / supervisor / `harness bot`. Client `-e` actually loads on Pi workers.
2. **Roster path and skill allowlist** — office `harness/roster.json`; load named skill directories only; no whole-tree dump.
3. **Intercept retarget to a Bot** — `blocked` can wait on another Bot. Operator is not the Verifier. No finance types in Harness.

Then live 15-Bot Pi (not `--fake`), Client facade await-done, Operator overlay out of the critical path.

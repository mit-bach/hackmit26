# Design review — Office of the CFO on Harness v2

Outside review, 2026-09-24. The reviewer did not build any of this. Scope: `MD-CATALOG.md`, the files it names, the Harness runtime (`.harness/Harness-v2/src`, `extensions/index.ts`), the CFO Client extension (`.cfo-v2/office/computer/cfo/extensions`), the Roster, Catalog, and Grants, and 62 recorded Pi sessions under `.cfo-v2`. Every claim marked **verified** was checked by running code or by grepping recorded sessions. Claims marked **by reading** come from reading the code and were not executed.

---

## 1. Verdict

The core ideas are good. The implementation does not do what the documents say it does.

Three ideas deserve to survive:

1. **Python owns the numbers.** The model chooses among Kernel candidates and never computes amounts, tolerances, or holds. `must_hold` runs after the model and the model cannot override it.
2. **Per-Profile Grants are enforced in code.** `call_connected_tool` refuses any Catalog op outside the active Profile's Grant. This is a real permission boundary, and it is tested.
3. **Context assembly is small, stable, and hashed.** The office layer is about 3 KB and the Bot layer is 4–18 KB. Each version is hashed and saved beside the session. That is better than most agent systems.

Everything around those three ideas is weaker than it looks. The markdown describes controls: Verifier concurrence, a sandbox, eval isolation, and "finance facts only through the Grant door." Most of them are not enforced, and some cannot work at all:

- **The Verifier gate cannot unlock.** The live tool always passes `handleId = null`, so a consequential op returns `verifier_required` forever. (Verified.)
- **The gate has almost nothing to gate.** The Catalog holds 101 ops: 96 reads and 5 local writes. There is no pay-run op, no period-lock op, and no cash-posting op. The Verifier Bots (`ctl-pay`, `ctl-cash`, `ctl-books`) guard actions that do not exist. (Verified.)
- **The sandbox is a regex over the command string.** `cat workspace/cash/...` reads another Bot's desk. `sed -i` or `python3` rewrites `harness/roster.json`. `cd .. &&` leaves the Computer. (Verified.)
- **The answer keys are inside every Bot's reach.** `data/expected_outcomes.json`, `data/expected_results.json`, and `data/holdout/ADVERSARIAL-PLANT-NOTES.md` pass the read check. Only prose protects them. (Verified.)
- **In practice, Bots use the shell as much as the Grant door:** 530 `bash` calls against 531 `call_connected_tool` calls across the recorded sessions. Many of those calls list `data/` or parse it with `python3`. (Verified.)

The catalog looks the way it does for two reasons. The cosmetic reason is copies: 2,352 markdown files, of which 532 are unique, and one protocol card written 594 times. The real reason is that the system's control flow and safety rules live in prose that the model must obey. They do not live in code that runs. Prose that must be obeyed grows every time the model misbehaves, which is why the files read like a list of past failures.

---

## 2. What the system is (as the reviewer understands it)

- **Kernel** (`.cfo/`): Python finance engine. It owns arithmetic, candidates, holds, and close gates, and runs as a sidecar behind RPC.
- **Harness v2** (`.harness/Harness-v2`): a runtime that spawns one Pi process per Bot (`pi --mode rpc -e harness -e cfo`) with `cwd` set to the Computer. It gives each Bot an inbox, Handles (accepted ≠ completed), pair threads, Rooms, per-Bot Memory, and a file-based lane (a Bot's single turn queue).
- **Client** (`.cfo-v2/office`): 16 standing Bots. Each has a `BOT.md`, Profiles, and Skills. The compiler produces `catalog.json` and `grants.json` from the Kernel. The CFO Pi extension adds `search_connected_tools` and `call_connected_tool`, which together are the "Grant door."
- **Instances** (`office/instances/*`, `prove-fork/*`): full clones of the Computer used for the recorded demo, prove runs, and trials.

Each turn gets this system prompt:

```text
<Pi base prompt> + office/system.md + Roster + BOT.md + active profile + roster-listed SKILL.md bodies
```

---

## 3. Angle: do the controls actually control anything?

This is the most important section. The documents promise controls. The table checks each one against the code.

| Promise in the markdown | Where it is enforced | Reality |
| --- | --- | --- |
| Consequential Kernel ops need Verifier concurrence | `cfo/extensions/intercept.ts` `gateConsequentialCall` | **Cannot unlock.** `extensions/index.ts` calls `callConnectedTool(bind, catalog, {...}, undefined, null, ...)`. With `handleId` always `null`, `completedHandleAllowsOp` always returns false. Each retry sends a new Verifier Handle and gets `verifier_required` again. |
| `ctl-pay` guards pay-run release, `ctl-books` guards period lock, `ctl-cash` guards cash posting | `verifier.ts` regexes `pay_run`, `period_lock`, `post_match` … | **No such ops exist.** The Catalog has only two consequential ops: `create_accrual` and `reconcile_accrual_with_invoice`. |
| Verifier answers CONCUR or REFUSE | `handleConcurrence()` | **Fails open.** "I do not concur" contains `CONCUR` and no `REFUSE`, so it parses as CONCUR. "CONCUR is not possible" starts with CONCUR, so it also parses as CONCUR. |
| Human approval for dangerous tools | `approvals.ts` `isConsequential` | **Effectively off.** Every Bot has `approvalLevel: "never"`, so only `rm -rf` triggers approval. The intercept config and `ask_user` flow are mostly dead code for this Roster. |
| Writes stay in `workspace/<slug>/` | `sandbox.ts` `sandboxAllowsBash` | **Regex over the command.** Only paths that start with `/`, `./`, or `../` are checked. `sed -i … harness/roster.json` and `python3 -c "open('harness/roster.json','w')…"` are allowed. |
| Bots cannot read another Bot's desk | `sandboxAllows` for `read` | Pi `read` blocks it. `bash` with `cat workspace/cash/x` does not. |
| Bots stay on this Computer | `normalizeRel` | `cd .. && cat sessions/ADVERSARIAL-SCENARIOS.md` is allowed. The path check does not resolve symlinks, so `data/…` counts as "inside" even though it points to `world/maximor`. |
| Eval isolation: operational Bots never load ground truth | Prose in `BOT.md` and constitution rule 9 | **Prose only.** `data/expected_outcomes.json` (whose own `note` field says "Operational agents must not load this file") and `data/holdout/*` pass the read check. No recorded session opened them, but `ls data` is common and shows the filenames. |
| Finance facts come from Grant tools, not the shell | `system.md`, every `BOT.md` | **Prose only.** 530 `bash` calls against 531 `call_connected_tool` calls in the recorded sessions. Many are `python3 - <<PY … Path('data/ar_invoices.json')`. |
| Bots cannot read another Bot's Memory | `sandboxAllows` | They can read that Bot's full Pi transcript under `harness/bots/bot_x/pi-session/`, which contains more than its Memory does. |
| Kernel data is read-only | `SANDBOX.md` "prescribed" layout | `data/` is a writable symlink. The tool hook blocks Pi `write` but not `bash`. |

`SANDBOX.md` opens with "There is no sandbox." That was true when it was written, and it is still mostly true. The new `sandbox.ts` adds prefix checks for Pi's `read`, `write`, and `edit` tools. Those are real checks. The `bash` check is not. As long as every Bot has an unrestricted shell as the same OS user, no path rule in TypeScript is a boundary. It only changes how often an obedient model gets told no.

**Why the tests did not catch the Verifier bug.** `facade.test.ts` ("completed Verifier Handle lets a consequential op past intercept") passes a real `handleId` into `callConnectedTool` directly. The function is correct. The Pi tool wiring is not, and nothing tests the wiring. This is the most common failure shape in the codebase: the unit is proven, and the path the model actually takes is not.

---

## 4. Angle: is a multi-agent "office" the right shape?

### What the LLM actually decides

Read `ap/BOT.md` and `ap/profiles/prepare.md` side by side:

- `collect_case_evidence` runs before the model.
- `must_hold` runs after the model, and the model cannot override it.
- The model must copy `exception_types` from the Kernel and must not invent any.
- `APPROVE` is allowed only when the Kernel already shows a clean match.

The model's real contribution to AP is one short sentence of "vendor-specific mess" plus routing: whom to send the packet to next. The same pattern repeats for `cash`, `apply`, `pay`, and every `ctl-*` profile. `review-bs.md` says "CONCUR only when the Kernel packet says `can_sign_off`." That makes the Verifier a boolean check with an LLM wrapped around it.

This is a sound instinct: keep the model away from money. But it raises a design question the documents never ask. If Python decides, why do 16 persistent chat sessions pass files to each other?

### Routing belongs in code

Handoffs are fixed. `ap` goes to `ctl-pay/review-match`, then to `pay`. `cash` goes to `ctl-cash/review-rec`, then to `close`. These are edges in a DAG (a fixed workflow graph). Today they are written as English in `## Handoffs` sections and executed by a model choosing to call `bot_send_prompt`. Each edge can fail in ways a function call cannot: the model forgets, names the wrong Profile, answers with assistant text instead of `ask_bot`, or calls `ask_user`. Much of the protocol card exists only to stop these failures.

A workflow engine in code would own the edges. The LLM would run only at nodes that need judgment: triage of messy inbound mail, reading a revised PDF, writing the flux narrative, drafting a vendor reply. That removes most of `PROTOCOL.md`, most of each `## Handoffs` section, and the whole class of "did not call ask_bot to reply" failures.

### The Verifier is a correlated second opinion

Every Bot runs on the same provider, model, and thinking level (`xai / grok-4.5 / low` in `client.json`). It reads the same Kernel packet. A second instance of the same model reading the same evidence is not segregation of duties. Its errors correlate with the first instance's errors. Where the Verifier's rule is deterministic, such as `can_sign_off`, it should be code. Where it is judgment, it should differ from the preparer in model, prompt, or evidence. Otherwise it only adds latency and failure points.

### Coordination costs are real and unbounded

- `ask_bot` is synchronous with a 120-second timeout. A chain such as `email → ap → ctl-pay` nests those waits. A cycle (A asks B while B asks A) stalls both until a timeout, because each Pi process blocks inside its own tool call.
- `cash/BOT.md` tells the Bot to `bot_send_prompt` to **itself** with `profile: investigate` and then await the Handle. `ask_bot` refuses self-messages, but `bot_send_prompt` does not. The lane cannot start the queued turn while the current turn waits in `bot_await_turn`. The Bot therefore always stalls for 120 seconds, then runs "investigate" later with nothing waiting for the result. (By reading.)
- Each Bot is a long-lived Pi session. History accumulates across wakes and across Profile switches. "Replace the Grant set. Do not union" is true for Kernel ops. It is not true for context: the transcript still holds the previous Profile's tool results.

### Grain Tests A–D are good analysis applied to the wrong unit

`cfo-bot-grain.md` is careful work. Tests for Wake, Object, and so on are a sensible way to decide what counts as an identity. But they answer "which *roles* exist in a finance office," which is org-chart thinking. The runtime question is "which *processes* need memory and a persistent context." Most of these Bots have 50-byte `MEMORY.md` files. Across 62 sessions there were only 19 `memory_write` calls. The standing identity is mostly decoration.

---

## 5. Angle: prompt and context design

### The same protocol is explained in five places

1. `PROTOCOL_CARD` in `src/protocol-card.ts`, written to `harness/PROTOCOL.md` plus two `SYSTEM.md` files per Bot per instance. That makes 594 identical files on disk, and none of them is loaded into a prompt.
2. `office/system.md`, which is pasted every turn and restates most of the card.
3. The `description` and `promptGuidelines` of each tool (`ask_bot`, `bot_ask`, `message_operator`, …), which Pi also puts in the prompt.
4. `PROTOCOL_WAKE_FOOTER`.
5. `identityBlock()` in `src/prompt.ts`, which is still imported and no longer used.

Some lines repeat everywhere: "These tools are registered. Do not say they are missing." "`ask_user` cannot complete a parked approval." "A peer Handle is not approval" appears 20 times across `BOT.md`, the profiles, and `system.md`. Repetition like this is a symptom. Each line was added after a model did the wrong thing. The durable fix is to remove the option: do not register `bot_ask` as a second name for `ask_bot`, and do not register `ask_user` on Bots that must never call it. The CFO extension already blocks `ask_user` in `tool_call`, so it should simply not be registered.

### Instructions are mostly prohibitions

Across `BOT.md` and the profiles (16,595 words) there are 859 occurrences of *not*, *never*, or *do not*, and 60 mentions of "ask a human" or `ask_user`. A typical `## Must not` section has 8–12 items, many of which name things the Bot has no tool to do ("Do not pay vendors" on a Bot with no pay op). Negative instructions cost tokens and attention, and they name the forbidden action, which primes it. Anything code already makes impossible should be deleted from the prompt.

### Build-time text leaks into runtime text

`constitution.md` is written to the *coding agents* that built the office: "Session 00 materializes this file," "Catalog: Session 00 leaves `ops: []`," "Do not edit Harness core to know what an invoice is." It sits on the Computer under `office/`, where any Bot can read it, and `BOT.md` files point to it. `SUPERSEDES.md` exists only to void sentences in *other* documents. Both are useful build history. Neither belongs in a runtime Bot's world. Where a sentence is wrong, edit the source document and drop the void list.

### Skills arrive by three paths

1. `context.ts` pastes the body of every skill listed on the Roster for that Bot, regardless of Profile.
2. The Harness `resources_discover` hook registers the Roster skill directories, or *all* 34 when `HARNESS_CLIENT_SKILLS` is unset, as Pi skills.
3. The CFO `resources_discover` hook registers the intersection of Grant and Roster skills, plus the Harness package skills.

A Roster skill can therefore appear twice: as a Pi skill entry and as a pasted body. `CONTEXT-MODULE.md` specifies "the body of each skill that profile's Grant allowlist names," but the code pastes by Roster, not by Grant. It also specifies `context` records inside the session jsonl, while the code writes `context/*.txt` and `manifest.jsonl` beside the session instead. The design document and the code have drifted apart.

### Profile handling has three defects (by reading)

- **A stale Profile stays active.** `BOT.md` says "If the header omits `profile`, wear `prepare`." The CFO `input` hook changes Profile only when the wake contains a `profile:` line. Otherwise the last Profile stays bound, and `active-profile.txt` keeps it for the system prompt too. An `ap` Bot that ran `investigate` keeps `investigate` Grants on its next plain wake.
- **The prompt and the Grant can disagree after a restart.** On a new process, the CFO bind falls back to `HARNESS_PROFILE` or `defaultProfile`. `context.ts` still reads the old `active-profile.txt`. The system prompt then describes one Profile while the Grant belongs to another.
- **Untrusted text can switch the Profile.** `PROFILE_HEADER` is `/^profile:\s*…$/im` and matches any line in the wake. If a wake quotes vendor email or counterparty text, a line starting with `profile:` switches the Grant set. It can only switch among that Bot's own Profiles, but it is still untrusted text controlling a privilege switch.

Every Profile switch also changes the system prompt. That breaks the prompt cache for the whole session history, which is exactly what `CONTEXT-MODULE.md` was written to avoid. The self-handoff pattern (`prepare` → `investigate` on the same Bot) makes this common.

---

## 6. Angle: sources of truth and drift

| Claim | Where | Reality |
| --- | --- | --- |
| "Fifteen Bots. Do not invent a sixteenth without failing Tests A–D." | `constitution.md` | The Roster has 16 (`world` was added). Room `intake` has 5 members, not the 4 the constitution lists. |
| Required `BOT.md` headings include `## Catalog ops` | `constitution.md` | `ap/BOT.md` uses `## Finance records` instead. |
| `review-assets.md` is the Fixed Asset Reviewer profile | Catalog listing | It is byte-identical to `review-bs.md`, title included. |
| "The same names exist under `.cfo/skills/`" | `MD-CATALOG.md` | `accrual-method-selection` and `inbox-triage` differ between `.cfo/skills` and `computer/skills`. |
| Skill descriptions | `MD-CATALOG.md` | Every skill shows `---`. The generator took the first line of the YAML front matter. |
| "The context module no longer depends on the model opening them" | `MD-CATALOG.md` on `SYSTEM.md` files | True. That is also why the 32 `SYSTEM.md` files per instance are dead weight. |
| Session proofs | `sessions/NN-PROOF.md`, `bots/*/PROOF.md` | Narrative claims written by the agent that did the work. They are not executable checks. |

The root cause is that one fact lives in several hand-edited places: the constitution, the grain, `BOT.md`, the roster JSON, the slug map, and the Grants. Only some of these are generated. Pick one machine-readable source (roster plus slug map), generate the rest, and turn the constitution into a short README.

---

## 7. Angle: file and repo hygiene

- 2,352 markdown files outside `node_modules` and `.venv`; 532 unique by content.
- One file, the protocol card, has 594 copies.
- 12,435 tracked files. `prove-fork/` alone has 4,540 tracked files and `office/instances/` has 1,062. On disk, `prove-fork` is 423 MB and `instances` is 193 MB.
- Each instance clones `skills/`, `office/`, `harness/`, and `cfo/` in full. Instances should reference the template by version (symlink or content hash) and copy only runtime state: `harness/bots/*`, `workspace/`, and `runs/`.
- `harness/protocol.jsonl` is 0 bytes in the template, and `seq` is committed.
- `.cfo/.venv` holds two Python versions (3.13 and 3.14) side by side.
- 16 desk `README.md` files carry the same four-line boilerplate. 16 `MEMORY.md` files are 47–54 bytes each.

None of this is a design flaw on its own. It is why the catalog looks absurd. Most of the catalog lists copies, and most of the copies exist because instances are full clones.

---

## 8. Angle: how it was built

The documents show the process. There are numbered sessions (00–12), each with a PROOF and NOTES file, driven by long operator prompts (`00-OPERATOR.md` is 34 KB and `CFO-HARNESS-MIGRATION-SESSIONS.md` is 44 KB). Each session was a coding agent working to a spec, then writing a report.

That process fits a hackathon, and it explains most of the findings:

- **Specs describe intent, and proofs describe what the agent believed.** Nobody checked the full path end to end, so `handleId = null` survived with a green unit test.
- **Each observed model failure became a new sentence.** That is why prohibitions pile up.
- **Documents about documents accumulated:** CATALOG, SUPERSEDES, INVENTORY, DOCUMENTS, CAPABILITIES, and GAP-ANALYSIS. When the code cannot be trusted to show the truth, the prose multiplies.
- **The vocabulary is well controlled** (Bot, Profile, Handle, Grant, Wake). The discipline went into words rather than into enforcement.

---

## 9. What is genuinely good

Section 1 named the three ideas to keep. Several smaller pieces are also worth carrying forward:

- The Grant door itself: `refuseConnectedTool`, the evalOnly filter, and write-path checks on Kernel args. It is small and correct.
- **Idempotency keys are required on every non-read op.**
- **Handles separate "accepted" from "completed," and a completed Handle is not treated as approval.** That is the right model.
- **Missed replies are caught.** `completeTurn` marks a peer wake `failed` when the Bot answered with assistant text instead of `ask_bot`. Failure is detected and recorded instead of silently completed.
- **Stable context hashing, with the assembled text saved beside each session.** This makes "what did the model see" answerable after the fact.
- **The Harness test suite has 26 files covering lanes, stops, recovery, rooms, and approvals.** It is a real foundation.
- **The team's own `SANDBOX.md` is candid.** It says "There is no sandbox" plainly. Keep that honesty and apply it to every control.

---

## 10. Recommendations, in priority order

### Fix now (correctness of controls)

1. **Wire the Verifier unlock.** Pass the Verifier Handle id through `call_connected_tool`, either as an explicit `verifier_handle` param or by looking up the pending index by `idempotency_key`. Add a test that drives the *Pi tool*, not `callConnectedTool` directly.
2. **Make concurrence structured.** The Verifier returns `{"decision": "CONCUR" | "REFUSE", "reason": "..."}` through a dedicated tool (`verifier_decide`). Remove the free-text regex parse.
3. **Move answer keys out of the Computer.** Keep `expected_*`, `holdout/`, and `sessions/ADVERSARIAL-*` outside any tree a Bot's `cwd` can reach, and outside the `data/` symlink target.
4. **Replace the bash regex with an OS boundary,** or remove `bash`. Options: run each Bot's Pi as its own user, run it in a container with a read-only `data/` mount and a writable `workspace/<slug>` mount, or use macOS `sandbox-exec`. If none is possible before the demo, drop `bash` from operational Bots and keep `read`, `write`, and `edit`, whose paths are checked.
5. **Fix Profile defaults.** No `profile:` header should mean `defaultProfile` on every wake. Match the header only in the Harness wake header block, never in the body. Resolve Profile in one place and pass it to both the Grant bind and `assembleContext`.

### Simplify (remove prose that code can replace)

6. **Delete dead text and dead copies:** `identityBlock`, the 594 `SYSTEM.md` and `PROTOCOL.md` copies, the duplicate `bot_ask` tool, and `ask_user` registration on Client Bots.
7. **Remove every `Must not` line that names an action with no tool behind it.** Keep prohibitions only where the Bot has the capability.
8. **Paste skills by Grant, not by Roster,** and choose one skill path: either Pi skill discovery or pasted bodies, not both.
9. **Retire `constitution.md` and `SUPERSEDES.md` from the Computer.** Keep a short build README in `workshop/`. Fix the sentences the void list points at.
10. **Make instances reference the template.** Copy only runtime state.

### Rethink (architecture)

11. **Put the workflow graph in code.** A small TypeScript or Python state machine owns the handoffs (`ap → ctl-pay → pay`, `cash → ctl-cash → close`). LLM Bots run at nodes that need judgment and return a typed result. Wakes stay, Rooms become optional, and most of `PROTOCOL.md` goes away.
12. **Make Verifiers either code or independent.** Deterministic rules such as `can_sign_off` should be functions. Judgment review should use a different model or prompt, and ideally different evidence (for example, raw source documents rather than the preparer's packet).
13. **Decide whether standing identity earns its cost.** If Memory stays near empty, run each wake as a fresh session with the assembled context plus the wake. You lose nothing measurable and gain cache stability, no cross-Profile history bleed, and easier replay.

---

## 11. Direct answer

Is this a good design, doing things in a way that makes sense? **Partly.** The principles (Kernel owns math, per-Profile Grants, fail closed, accepted ≠ completed) are sound and better than average. The system built on them is an org chart of LLM sessions that coordinate through prose. Its safety story depends mostly on the model obeying text, and where code was meant to back that text up, the code has holes or is disconnected. The markdown looks strange because it is doing two jobs that code should do: holding the workflow graph and enforcing the rules. Move those two jobs into code, and most of the catalog can be deleted.

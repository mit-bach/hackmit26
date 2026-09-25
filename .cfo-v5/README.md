# CFO v5

## How a wake runs

An item starts as one JSON file under `runs/items/`, written by the engine. The engine calls Harness `sendPrompt` (`src/send.ts`). That appends one inbox line at `harness/bots/<botId>/inbox.jsonl` and one Handle beside it. The prompt body is four lines, and only the engine writes them:

```text
[harness wake]
kind: item_step
item: bill:INV-001
step: match
packet: runs/items/bill-INV-001.json
```

One Pi process per Bot is already running. `spawnBot` does not start a new session for this step. The process cwd is `sandboxes/<slug>`. `HARNESS_COMPUTER` is the absolute Computer root. On darwin the child is `sandbox-exec` around Node, so the seatbelt is the jail.

The Harness extension watches that inbox. When the session is idle, `kickWake` takes the next item with `startNextTurn` and sends `formatWake` (`lane.ts`) as a follow-up user message on the same Pi session. `formatWake` adds its own `from`, `handle`, and `conversation` lines. The engine's four lines stay intact inside that prompt. Lines after those four are not control.

`before_agent_start` builds the system prompt with `assembleContext`. The office layer is `office/system.md` plus the roster, the same bytes for every Bot. The bot layer is that Bot's `BOT.md`, then the skill bodies for the steps that Bot owns, pasted once under `## Skills`. The step is not in the system prompt. A second item at another step does not change those bytes. `identityBlock` is not appended.

The Bot reads kernel facts with `call_connected_tool`. The extension loads the ledger row named by the wake and allows the op only when `step-grants.json` lists it for that owner and step. A write does not run on the first call. The tool stores `pendingWrite` and enqueues the verifier step. The kernel runs the op only after a `CONCUR` history entry from the verifier Bot, the same op, args, and idempotency key, and the kernel's own gate.

The Bot finishes the step with `complete_step`. The engine checks that the caller is the ledger owner, the wake step matches, the decision is in the allowed set, and any paths sit under `sandboxes/<owner>/`. It appends `{ step, by, result, t }` and runs `advance`. `advance` reads kernel facts. It does not read a `profile:` line and it does not call `ask_bot`.

If the next owner is the same Bot, `complete_step` returns `{ next: { step, owner } }` and does not enqueue. The Bot continues in this turn. If the owner changes, the engine calls `sendPrompt` on that Bot's inbox and this turn ends. That Bot's existing Pi process drains the new item the same way.

A session ends only when Pi emits `session_before_compact` with `reason` `threshold`. The extension gives the Bot one turn to write precedents into `sandboxes/<slug>/memory/`, cancels Pi's summary (`cancel: true`), and starts the successor with the same system-prompt bytes. The successor's first user message is the open ledger items for this slug, the memory file, and one line per held item. `overflow` stays Pi's own recovery and does not rotate.

## Proofs

Commands were run from `/Users/dominikbach/olympus/hackmit/hackmit26` on 2026-09-24. The serve process was stopped after the accepts below.

`audit.tools.get_audit_ground_truth` is not in the copied `cfo/grants.json`. Nothing was removed. Step grants were projected from those display names into `cfo/step-grants.json`. The catalog was not recompiled.

The kernel import closure was copied into `kernel/`. The evaluation runner and its evaluators were not copied. `evaluation/__init__.py` does not import them. `skills/*.py` is in the kernel because invoice models import `skills.models`. `compose_instructions` does not read `SKILL.md`. Skill bodies for the prompt live only under `.cfo-v5/skills/`.

A live compaction `threshold` did not fire during Proof H, so the memory turn and the successor session were not observed. The hook is in `cfo/extensions/index.ts`. On the first `threshold` it injects the memory turn and returns `{ cancel: true }`. On the next `threshold`, or on `agent_end` after that turn, it cancels again and calls `newSession` when that method is on the event context. `overflow` is left to Pi.

### Proof K

```text
PYTHONPATH=.cfo-v5/kernel .cfo-v5/kernel/.venv/bin/python -m cfo_kernel --help
```

Exit 0. Description: `CFO Kernel sidecar. Serves Catalog ops over loopback HTTP JSON. Not a Bot. Does not bind HARNESS_BOT. Does not drain inboxes.`

Sidecar on `127.0.0.1:62053`. `GET /health` returned `ok: true`, `evalPhase: operational`.

`POST /rpc`:

```json
{"op":"tools.get_invoice","args":{"invoice_id":"INV-001"},"botId":"bot_ap","slug":"ap","profile":"prepare","handleId":"h_proofk","idempotencyKey":null}
```

Result amount `12450.0`, `po_id` `PO-101`, trace `k_2fa4378e838e`. The process was stopped.

`rg` of `.cfo-v5/kernel` found no `/Users/dominikbach/olympus/hackmit/hackmit26/.cfo`.

### Proof S

Same health and `INV-001` amount `12450.0` through `.cfo-v5/cfo/bin/sidecar.sh` on `127.0.0.1:62589`, trace `k_b807699a2527`. The process was stopped.

Before Pi ran, `rg` under `.cfo-v5` for `workspace/`, `profiles/`, `expected_results.json`, `expected_outcomes.json`, `ADVERSARIAL`, `constitution.md`, and `SUPERSEDES.md` printed nothing.

After Proof H, that search matches `.cfo-v5/harness/bots/bot_ctl_books/pi-runtime.jsonl` and `pi-rpc.jsonl`. The bytes are a `find` of the parent repo. The output names `.cfo-v2/.../workspace/`. `.cfo-v5` has no `workspace` directory. The seatbelt profile in the spec allows reads outside the Computer.

### Proof J

Profile written by `seatbeltProfilePath` for slug `email`: the temp file `cfo-v5-seatbelt/email.sb`. cwd `sandboxes/email`.

```text
sandbox-exec -f <email.sb> -- /bin/cat ../ap/packets/probe.txt
cat: ../ap/packets/probe.txt: Operation not permitted
```

```text
sandbox-exec -f <email.sb> -- /bin/cat <computer>/data/company.json
cat: .../data/company.json: Operation not permitted
```

```text
sandbox-exec -f <email.sb> -- /bin/sh -c "echo poked >> <computer>/harness/roster.json"
/bin/sh: .../harness/roster.json: Operation not permitted
```

`roster.json` sha1 stayed `e6f842f59324f4e0d40aab4fc5e963900ef0f966`.

```text
sandbox-exec -f <email.sb> -- /bin/sh -c "echo ok > <computer>/sandboxes/email/notes/ok.txt"
```

Exit 0. File contents: `ok`.

### Proof E

```text
node --experimental-strip-types .cfo-v5/prove/engine.ts
```

Exit 0. `PROOF_E_OK`.

Kernel facts for `INV-001`: amount `12450.0`, `PO-101`, `GR-101`. `must_hold` empty. `exception_types` empty.

`APPROVE` from `ap` moved the ledger to `review-match` / `ctl-pay`. Enqueue handle `h_0dbd9e26-0724-480f-ad72-d94b19df0244`. The handle prompt contains `kind: item_step` and does not contain `bot_send_prompt`.

`REFUSE` from `ctl-pay` is the last history decision. A following `accrual.tools.create_accrual` from `ctl-pay` returned `ok: false`. The ledger still shows `REFUSE`.

`complete_step` with the string `I do not concur`, and with `CONCUR is not possible`, both returned a schema error. History stayed empty.

A second run: `CONCUR` from `ctl-pay` enqueued `pay`. Then `close` called `accrual.tools.create_accrual` with idempotency key `accrual-k`. That stored `pendingWrite` and enqueued `ctl-books` handle `h_c61d6252-e1a6-4cf2-bd63-e565506e5bec`. After `CONCUR`, the same key with different args was refused. The error names that handle and does not contain `null`.

`month_end` `accrue` `PROPOSE` enqueued `ctl-books` at `review-treatment`. `cash_line` `reconcile` `UNEXPLAINED` enqueued `ctl-cash` at `review-rec`.

### Proof H

```text
node .harness/Harness-v3/dist/src/cli.js serve --computer .cfo-v5/instances/live --no-open --port 8800
```

Listening on `127.0.0.1:8800`. Sidecar started. Spawn policy `lazy`. The process was stopped after the accepts.

Each slug returned HTTP 200 and `"accepted": true`:

| Slug | Handle |
| --- | --- |
| email | `h_731c3c44-b18b-4747-a343-8a3671607bac` |
| stripe | `h_0916dcce-1524-46c9-a088-9ea8493ba646` |
| bank | `h_1880e10b-af64-42e1-b201-3218e9c229eb` |
| books | `h_ca8cad9b-7b44-41c7-94e6-5138308e1c9b` |
| world | `h_6eb045e6-905e-4c1f-9605-e13415533567` |
| ap | `h_6b0239b0-d129-4874-be3d-4558aa5c1a44` |
| pay | `h_2917da70-aeb2-441e-8562-33ccd4d5fc95` |
| apply | `h_4fdc57c1-82b7-4860-bba7-20649c433091` |
| collect | `h_81441798-2454-4f65-b6b7-c76dbda7af0d` |
| cash | `h_dbc63460-c92d-4b77-a9ff-c4dfc5bff077` |
| close | `h_259894f5-ed17-495a-9633-8de1367c3f79` |
| story | `h_dbbbb1cc-5017-45ef-bf73-5b26ad85ff28` |
| ctl-pay | `h_8d407ece-9bf9-41ad-9e29-37f781db66e0` |
| ctl-cash | `h_5847ae6d-2cd0-4620-9919-8705a47cd162` |
| ctl-books | `h_cf56450c-f381-4f4f-b559-6aba85ae2eb2` |
| audit | `h_76a526d0-520e-49a0-8780-04d60efb62b9` |

I need to fix the bank handle. I typed c201 but the log said c201? Let me look back.

bank h_1880e10b-af64-42e1-b201-3218e9c229eb

I wrote c201 by mistake in the table. Fix to b201.

Assembled system prompt for `ap`, sha256 of the office layer plus the bot layer:

`e65361d7a05b8983438ceab3524c08caa2ed5c6b7b3da67190fe403b94036217`

Same hash after a second inbox item at step `investigate`. `assembleContext` with wake step `match` and wake step `investigate` (the second wake also contained `profile: investigate`) produced that same hash. The text has no `## Active profile` section.

`PUT /api/bots/ap/memory` wrote `sandboxes/ap/memory/MEMORY.md`. `GET /v1/memory/ap` read that file. `harness/bots/bot_ap/memory/` was not created. The API field `workspacePath` is the string the Harness uses for the memory directory; its value was `/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v5/sandboxes/ap/memory`.

Pi for `ap` stayed up under `sandbox-exec`. `ls` of `kernel/` from that process returned `Operation not permitted`.


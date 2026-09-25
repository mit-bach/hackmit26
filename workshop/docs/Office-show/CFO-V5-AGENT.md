# Build CFO v5

You are implementing this file. It is the spec. `DESIGN-REVIEW.md`, `PROFILES-AND-PROPOSAL.md`, and `CFO-V5.md` explain why. If they disagree with this file, this file wins. Do not treat those essays as a second spec and do not leave their open questions for a later agent.

Repo: `/Users/dominikbach/olympus/hackmit/hackmit26`.

Create a branch named `cfo-v5` from the current HEAD and stay on it. Do not commit. Do not push. Do not modify `.cfo`, `.cfo-v2`, or `.cfo-v3` except by reading `.cfo` and `.cfo-v2`. Do not delete them. Do not open `.cfo-v4` if it appears. Do not copy a file, a sentence, or a directory name out of `.cfo-v3` or `.cfo-v4`.

`.cfo-v3` is a failed layout (one shared `workspace/` with a folder per Bot). `.cfo-v4` was a failed kernel (a short rewrite, not the finance engine). You are not continuing either tree.

## What "done" means

A running office whose only inputs are `.harness/Harness-v2` and `.cfo-v5`.

- Repo `.cfo` is not on `PYTHONPATH`.
- `.cfo-v2` is not the Computer root.
- Sixteen standing Bots, one Pi process each. A session ends only at Pi's compaction threshold. You do not start a fresh session per step.
- No `workspace/` directory. No `profiles/` directory. No `profile:` control line. No English `## Handoffs` that a model must obey to move a bill.
- The sandbox is the process jail, not a path regex in `sandbox.ts`.

If a proof below fails, stop and write the failure in `.cfo-v5/README.md`. Do not shrink the kernel, skip the ledger, or skip `complete_step` to make a check pass.

## Order of work

Do these in order. Do not start a later stage before the earlier proof in that stage passes.

1. Read the files in "Read these" and write `.cfo-v5/README.md` section "How a wake runs" (see that heading). No other files yet.
2. Copy the kernel. Proof K.
3. Lay down the Computer tree, data, roster, and sidecar. Proof S.
4. Patch Harness spawn and memory paths. Proof J (the jail).
5. Build the workflow engine, `complete_step`, and step grants. Proof E (no model).
6. Wire the Pi extension, prompts, and compaction hook. Proof H (serve).
7. Fill `.cfo-v5/README.md` with commands and command output.

## Read these

Read until you can write the README section. Do not explore the repo at random.

Office that runs today:

- `.cfo-v2/office/computer/harness/roster.json` — 16 slugs, rooms, routines. Copy the slugs and rooms. Do not copy routine prompt text that contains `profile:` or `bot_send_prompt`.
- `.cfo-v2/office/computer/harness/client.json` — sidecar, provider, model. You will rewrite the sidecar paths.
- `.cfo-v2/office/computer/cfo/extensions/` — Grant door: `call.ts`, `intercept.ts`, `verifier.ts`, `index.ts`, `kernel.ts`, `profile.ts`. You are replacing profile binding and the intercept, not rewriting the RPC client from scratch.
- `.cfo-v2/office/computer/cfo/bin/sidecar.sh` — walks up looking for a directory named `.cfo`. That walk is wrong for v5. Do not copy it.
- `.cfo-v2/office/computer/office/system.md` and `.cfo-v2/office/bots/*/BOT.md` — source text for identity. Fold profile files into `BOT.md` step sections. Drop `## Must not` lines that name a tool the Bot will not have.
- `.cfo-v2/office/world/maximor` — the world pack `data/` is copied from. Not symlinked.

Kernel:

- `.cfo/cfo_kernel/__main__.py` — `python -m cfo_kernel --computer <dir>`.
- `.cfo/cfo_kernel/paths.py` — `KERNEL_ROOT` is the parent of the `cfo_kernel` package. `DEFAULT_COMPUTER` is hardcoded to `.cfo-v2/office/computer`. After the copy, `DEFAULT_COMPUTER` must be `.cfo-v5` itself (the Computer root), and every path must come from `HARNESS_COMPUTER`.
- `.cfo/cfo_kernel/rpc.py` — imports `evaluation.isolation`. Copy that module. Do not copy the eval suite.
- `.cfo/inbox/classify.py` around `has_prompt_injection` and `has_unsafe_mutation_request`. Keep the branch that rejects injection even when the text looks like `VENDOR_INVOICE`. Also reject when `has_unsafe_mutation_request` is true and the class is `VENDOR_INVOICE`. Today that second case is excluded (`classification != "VENDOR_INVOICE"`). That exclusion is the bug. An unsafe mutation request must not create a bill.

Harness:

- `.harness/Harness-v2/src/server/supervisor.ts` — `spawnBot` uses `cwd: computerRoot` and `spawn(process.execPath, args)`. This is the spawn you change. Pi is not started as the `pi` binary.
- `.harness/Harness-v2/src/bind.ts` — `HARNESS_COMPUTER` wins over cwd. You must set it to the absolute Computer root. If you only change cwd, the Bot binds to `sandboxes/<slug>` and cannot find the roster.
- `.harness/Harness-v2/src/paths.ts` — `memoryDir` is `harness/bots/<botId>/memory`. v5 memory is `sandboxes/<slug>/memory`. Inbox, handles, lane, and pi-session stay under `harness/bots/<botId>/`.
- `.harness/Harness-v2/src/sandbox.ts` — prefix regex. Do not extend it. For a Computer that has `sandboxes/`, do not use it as the boundary.
- `.harness/Harness-v2/src/context.ts` — `assembleContext`. Keep the two hashed layers. The bot layer is `BOT.md` plus skill bodies, once. It does not change when the step changes.
- `.harness/Harness-v2/src/protocol-card.ts` — one card in code. Do not write `SYSTEM.md` copies.
- Pi types: `session_before_compact` has `reason: "manual" | "threshold" | "overflow"`. Rotation runs only on `"threshold"`.

## Where code lives

| Path | Owns |
| --- | --- |
| `.harness/Harness-v2/src` | Spawn jail, cwd, `HARNESS_COMPUTER`, memory path when `sandboxes/` exists. Nothing about invoices, steps, or CONCUR. |
| `.cfo-v5/kernel` | Python finance engine. Amounts, holds, catalog RPC. |
| `.cfo-v5/cfo/engine` | Item ledger, workflows, `complete_step`, step-grant check. TypeScript. Finance types stay here. |
| `.cfo-v5/cfo/extensions` | Pi extension. Tools: `search_connected_tools`, `call_connected_tool`, `complete_step`. No `ask_user`. No `bot_ask`. |
| `.cfo-v5/office` | `system.md`, `bots/<slug>/BOT.md` only. |
| `.cfo-v5/harness` | `roster.json`, `client.json`, `extensions.json`. Harness still writes inboxes and sessions here at runtime. |
| `.cfo-v5/sandboxes/<slug>` | That Bot's cwd. `memory/`, `packets/`, `notes/`. |
| `.cfo-v5/data` | World pack. No answer keys. |
| `.cfo-v5/runs` | Kernel traces and `runs/items/` ledger. Not a Bot cwd. |
| `.cfo-v5/prove` | The scripts for proofs K, S, J, E, H. |

The engine may import `.harness/Harness-v2/src/send.ts` to enqueue a Handle. Do not copy those functions into `.cfo-v5`. Do not put the engine inside `.harness`.

A v2 Computer has no `sandboxes/` directory. Every Harness change must keep that path working: old cwd, old memory path. Gate the new behavior on `existsSync(join(computerRoot, "sandboxes"))`.

## Layout

```text
.cfo-v5/
  README.md
  kernel/                      PYTHONPATH. Package cfo_kernel lives here.
  data/                        copy of the world pack, answer keys removed
  runs/items/                  ledger JSON, one file per item
  office/system.md
  office/bots/<slug>/BOT.md
  skills/<name>/SKILL.md       pasted into the prompt. The kernel does not load these.
  harness/roster.json
  harness/client.json
  harness/extensions.json
  cfo/catalog.json
  cfo/grants.json              copied, then step-grants compiled from it
  cfo/step-grants.json
  cfo/engine/                  workflows, ledger, complete_step
  cfo/extensions/              Pi extension
  cfo/bin/sidecar.sh
  sandboxes/<slug>/{memory,packets,notes}/
  prove/
  sandbox/seatbelt.sb          template, SLUG and COMPUTER substituted per Bot
```

There is no `workspace/`. There is no `profiles/`. There is no per-Bot `roster.json`. There is no `constitution.md`, `SUPERSEDES.md`, `PROOF.md`, `NOTES.md`, or `SYSTEM.md`.

Slugs, in this order: `email`, `stripe`, `bank`, `books`, `world`, `ap`, `pay`, `apply`, `collect`, `cash`, `close`, `story`, `ctl-pay`, `ctl-cash`, `ctl-books`, `audit`.

Rooms stay as in the v2 roster: `intake` (email, stripe, bank, books, world), `pay` (ap, pay, ctl-pay), `cash` (apply, collect, cash, ctl-cash), `books-close` (close, ctl-books, story, audit).

## Kernel copy

Do not hand-pick files. From `.cfo`, with its venv:

```bash
PYTHONPATH=. python -c "import cfo_kernel.server, cfo_kernel.rpc, cfo_kernel.invoke"
```

Use `modulefinder` (or walk `sys.modules` after that import) and copy every package and module that resolves under `.cfo/`. You need the import closure of `python -m cfo_kernel`, including `evaluation.isolation` and whatever `cfo_kernel.invoke` imports (`accrual`, `inbox`, `cash_recon`, and the rest). Copy those packages into `.cfo-v5/kernel` so `import cfo_kernel` works with `PYTHONPATH=.cfo-v5/kernel`.

Do not copy: `.venv`, `tests`, `evals`, `demo_web`, `demo`, `sample_data`, `skills`, `runs`, `traces`, `web`. Do not copy `data` into the kernel tree.

After the copy:

- `rg` of `.cfo-v5/kernel` finds no runtime path to `/Users/dominikbach/olympus/hackmit/hackmit26/.cfo`.
- `DEFAULT_COMPUTER` is `.cfo-v5`, not a path under `.cfo-v2`.
- Create `.cfo-v5/kernel/.venv` with the same requirements the sidecar imports (`fastapi` and whatever the copied code imports). Do not reuse `.cfo/.venv` by path in `sidecar.sh`.

`sidecar.sh` sets `PYTHONPATH` to `.cfo-v5/kernel`, `HARNESS_COMPUTER` to `.cfo-v5`, `CFO_EVAL_PHASE=operational`, unsets `HARNESS_BOT`, and execs `python -m cfo_kernel --computer "$HARNESS_COMPUTER"`. It does not search parent directories for `.cfo`.

### Data

Copy `.cfo-v2/office/world/maximor` to `.cfo-v5/data`. Then delete, if present:

- `expected_results.json`
- `expected_outcomes.json`
- `holdout/`
- any file whose name contains `ADVERSARIAL`

Do not symlink `data` at the world pack. The world pack still contains the answer keys, and a symlink would put them on the Computer.

Copy `catalog.json` and `grants.json` from `.cfo-v2/office/computer/cfo/`. The compiler output is the contract. Do not re-compile unless an op id in the workflows is missing, and if you re-compile, say so in the README.

Operational grants must not include `audit.tools.get_audit_ground_truth`. If the copied grants include it, remove it from every operational entry and record the removal.

### Proof K

```bash
PYTHONPATH=.cfo-v5/kernel .cfo-v5/kernel/.venv/bin/python -m cfo_kernel --help
```

Exit 0. The description is the sidecar (`Serves Catalog ops`), not a new program.

Start it with `--computer .cfo-v5` on `127.0.0.1` and an ephemeral port. `GET /health` is ok. `POST /rpc` for `tools.get_invoice` with invoice id `INV-001` returns amount `12450.0`. Stop the process. Put the request and the amount in the README.

## The jail

Changing cwd is not a sandbox. `cd ..` still walks out. A prefix regex in `sandbox.ts` is the design that failed. v5 wraps the existing Pi spawn.

In `supervisor.ts` `spawnBot`, when `sandboxes/` exists:

- `cwd` is the absolute path `.cfo-v5/sandboxes/<slug>`.
- `HARNESS_COMPUTER` is the absolute path `.cfo-v5`.
- On darwin, the child is `sandbox-exec -f <profile> -- <node> <cli> ...`, not a raw node spawn. Generate the profile per slug from `sandbox/seatbelt.sb` into a temp file. The profile is the boundary.

Seatbelt profile (substitute `COMPUTER` and `SLUG` and `BOTID`):

```text
(version 1)
(allow default)
(deny file-read* file-write* (subpath "COMPUTER/data"))
(deny file-read* file-write* (subpath "COMPUTER/kernel"))
(deny file-read* file-write* (subpath "COMPUTER/sandboxes"))
(allow file-read* file-write* (subpath "COMPUTER/sandboxes/SLUG"))
(deny file-write* (subpath "COMPUTER/office"))
(deny file-write* (subpath "COMPUTER/cfo"))
(deny file-write* (subpath "COMPUTER/harness/roster.json"))
(deny file-write* (subpath "COMPUTER/harness/client.json"))
(deny file-write* (subpath "COMPUTER/runs"))
```

`(allow default)` stays, because a default-deny profile cannot name every file Node and Pi open. The denies are the control. Read of `office/`, `harness/`, and `cfo/catalog.json` stays allowed so bind and `assembleContext` work. Write of another slug's sandbox is denied because the allow for `sandboxes/SLUG` does not cover `sandboxes/email` when SLUG is `ap`. If a deny does not win over `(allow default)` on this OS, fix the profile until Proof J passes. Do not replace the profile with a regex and call it done.

`memoryDir` in `paths.ts`, when `sandboxes/` exists, returns `sandboxes/<slug>/memory`. `slug` is `botId` with the `bot_` prefix removed and `_` replaced by `-` (`bot_ctl_pay` → `ctl-pay`). Inbox, handles, lane, and `pi-session` stay under `harness/bots/<botId>/`.

Do not register Pi `bash` for a jailed Bot if you cannot also jail it. The seatbelt covers `bash` because `bash` is the same process. That is the point.

### Proof J

Write `sandboxes/ap/packets/probe.txt`. Run the same seatbelt profile the email Bot gets, with cwd `sandboxes/email`:

```bash
sandbox-exec -f <email profile> -- /bin/cat ../ap/packets/probe.txt
```

This must fail. Record the command and the denial. Also record a denied `cat` of `data/company.json` and a denied write to `harness/roster.json`. An allowed write is `sandboxes/email/notes/ok.txt`.

If `sandbox-exec` is missing, stop. Do not skip the proof.

## One prompt, one tool surface

`assembleContext` for a v5 Computer:

- Office layer: `office/system.md` plus the roster (slug, name, purpose). Same bytes for every Bot.
- Bot layer: that Bot's `BOT.md` only, then the skill bodies for the steps that Bot owns, pasted once under `## Skills`.
- Do not paste a profile file. Do not register those skill directories with Pi `resources_discover`. One path: the paste. A skill does not grant a tool.
- Do not append `identityBlock` from `src/prompt.ts`.
- The step is not part of the system prompt. A second item at a different step must not change the system-prompt bytes. The wake carries the step.

`office/system.md` states the channels in one place: assistant text is the Operator; `ask_bot` is a question to a colleague and is not routing; `complete_step` finishes the current item step; Kernel facts come from `call_connected_tool`. Do not restate that in every `BOT.md`.

Each `BOT.md` has `## Identity`, then one `## Step: <name>` section per step that Bot owns (the text that used to be a profile file, with the profile machinery removed), then `## Memory`. Memory stores a precedent keyed by vendor, account, or processor. It does not store a transcript.

`## Must not` is allowed only for a tool that exists on that Bot. Delete "do not pay" from a Bot that has no pay op. Say, on `ap` only, that a long session has already seen earlier bills, so `ap` is not independent of itself. Independence is `ctl-pay`.

No `parseProfileFromWake`. No `active-profile.txt`. No `replaceProfile`. A line in vendor mail that says `profile:` changes nothing.

Tools the client extension registers: `search_connected_tools`, `call_connected_tool`, `complete_step`. It does not register `ask_user` or `bot_ask`. Harness may still register `ask_bot`. Leave that one name.

## Item ledger

Code writes `.cfo-v5/runs/items/<id>.json`. A Bot cannot write `runs/` (the seatbelt denies it). A Bot reads an item through `call_connected_tool` or through the `complete_step` result. The engine and the kernel write the file.

```json
{
  "id": "bill:INV-001",
  "workflow": "open_bill",
  "step": "match",
  "owner": "ap",
  "facts": {},
  "pendingWrite": null,
  "history": []
}
```

`id` is `<kind>:<business id>` with the characters `:`, `/`, and `..` stripped from the business id before joining the filename. `history` entries are `{ "step", "by", "result", "t" }`. `result` is the typed object from `complete_step`, not assistant prose.

`pendingWrite`, when set, is `{ "op", "args", "idempotencyKey", "verifierHandle" }`. It is how a consequential call stays locked to one argument set.

## Workflows

The engine is a function `advance(item, result) -> { step, owner } | { terminal } | { emit }`. It reads kernel facts. It does not read free text for a `profile:` line. It enqueues a wake on an existing Bot inbox through `sendPrompt`. It does not spawn a process.

Wake text, written only by the engine:

```text
[harness wake]
kind: item_step
item: bill:INV-001
step: match
packet: runs/items/bill-INV-001.json
```

The header is the first four lines. Nothing after them is control. `formatWake` in `lane.ts` may add its own prefix; the engine's four lines stay intact inside the prompt.

If `advance` returns the same owner, `complete_step` returns the next step in the tool result and does not enqueue. The Bot continues in this turn. That replaces the self-handoff that waited 120 seconds.

If `advance` returns a different owner, the engine enqueues and this turn ends.

`ask_bot` is not used by `advance`.

### Steps

`decision` on `complete_step` must be one of the values in the last column. Any other value is an error, the ledger does not move, and the turn can retry once.

| Workflow | Step | Owner | Allowed decisions | Next |
| --- | --- | --- | --- | --- |
| `open_bill` | `match` | `ap` | `APPROVE`, `HOLD`, `INVESTIGATE` | Kernel `must_hold` or `HOLD` → terminal `hold`. `INVESTIGATE` or non-empty `exception_types` → `investigate` on `ap` (same turn). `APPROVE` with a clean kernel match → `review-match` on `ctl-pay`. |
| `open_bill` | `investigate` | `ap` | `APPROVE`, `HOLD` | `APPROVE` → `review-match` on `ctl-pay`. Else terminal `hold`. |
| `open_bill` | `review-match` | `ctl-pay` | `CONCUR`, `REFUSE` | `CONCUR` and kernel still allows → emit `pay_run` for that invoice id. `REFUSE` → terminal `hold`. |
| `pay_run` | `schedule` | `pay` | `PROPOSE`, `HOLD` | `PROPOSE` → `review-pay` on `ctl-pay`. |
| `pay_run` | `review-pay` | `ctl-pay` | `CONCUR`, `REFUSE` | `CONCUR` stores the decision on the item. It does not send money. There is no ACH op. |
| `intake` | `triage` | `email` | `ROUTE`, `REJECT` | Channel is a field on the item (`email`, `employee`, `portal`, `document`), chosen from the source event, not from a model. `REJECT` is terminal. `ROUTE` emits `open_bill` only when the kernel created a bill. |
| `books_intake` | `capture` | `books` | `ROUTE`, `REJECT` | Source field is `erp`, `procurement`, or `edi`. Same rule: the event picks it. |
| `world_reply` | `reply` | `world` | `SENT`, `HOLD` | Counterparty type (`vendor`, `customer`, `bank`, `employee`) is a field. One step. |
| `stripe_payout` | `unpack` | `stripe` | `DONE`, `HOLD` | `DONE` emits `cash_line` for the deposit. |
| `bank_line` | `land` | `bank` | `DONE`, `HOLD` | `DONE` emits `cash_line`. |
| `cash_line` | `reconcile` | `cash` | `MATCHED`, `EXPLAINED`, `UNEXPLAINED` | `UNEXPLAINED` → `review-rec` on `ctl-cash`. `MATCHED` or `EXPLAINED` → `review-rec` when the kernel requires sign-off, otherwise terminal. |
| `cash_line` | `review-rec` | `ctl-cash` | `CONCUR`, `REFUSE` | `REFUSE` or an unexplained residual stays open. Do not invent a match. |
| `ar_apply` | `apply` | `apply` | `PROPOSE`, `HOLD` | `PROPOSE` → `review-apply` on `ctl-cash`. |
| `ar_apply` | `review-apply` | `ctl-cash` | `CONCUR`, `REFUSE` | |
| `collect` | `chase` | `collect` | `SENT`, `HOLD` | |
| `month_end` | `accrue` | `close` | `PROPOSE`, `NONE` | Fan-out from the period workflow. `NONE` means this step does not apply to this item. |
| `month_end` | `prepaid` | `close` | `PROPOSE`, `NONE` | |
| `month_end` | `assets` | `close` | `PROPOSE`, `NONE` | |
| `month_end` | `bs` | `close` | `PROPOSE`, `NONE` | |
| `month_end` | `review-treatment` | `ctl-books` | `CONCUR`, `REFUSE` | Reviews an `accrue` or `prepaid` proposal. |
| `month_end` | `review-assets` | `ctl-books` | `CONCUR`, `REFUSE` | |
| `month_end` | `review-bs` | `ctl-books` | `CONCUR`, `REFUSE` | |
| `month_end` | `lock` | `ctl-books` | `CONCUR`, `REFUSE` | `CONCUR` does not lock the period by itself. The kernel gate does, and only if its own checks pass. |
| `story` | `flux` | `story` | `DRAFT`, `HOLD` | |
| `story` | `forecast` | `story` | `DRAFT`, `HOLD` | Covers forecast, miss, and board. One step. The packet says which. |
| `audit` | `interpret` | `audit` | `FINDING`, `NONE` | Same turn continues to `report` on `audit`. |
| `audit` | `report` | `audit` | `DRAFT` | |

There is no `coordinate` step. The month-end workflow is the coordinator. There is no `cash` step named `investigate`; `reconcile` is the only cash step because both old profiles had the same ops.

Implement `open_bill` end to end, including the enqueue to `ctl-pay`. Implement the other workflows as tables the engine will run: the same `advance` function, the same ledger, the same `complete_step`. A workflow with no starter event yet still has its transition function and a prove test that feeds it a fixture result. Do not leave them as comments.

### complete_step

Client tool:

```ts
complete_step({
  item: "bill:INV-001",
  result: { decision: "APPROVE", reason: "string", evidence_used: ["PO-101"] },
  paths: ["sandboxes/ap/packets/INV-001.json"]
})
```

The engine checks:

- The caller is the ledger `owner` and the wake `step` matches the ledger `step`.
- `decision` is in the allowed set for that step.
- `paths`, if any, are under `sandboxes/<owner>/`.

Then it appends history, runs `advance`, and either returns `{ next: { step, owner } }` or `{ enqueued: { owner, handleId } }`.

Verifier decisions are only this object. Do not scan prose for the substring `CONCUR`. The strings `I do not concur` and `CONCUR is not possible` do not unlock a write. Add those two strings as negative tests.

### Step grants

Compile `.cfo-v5/cfo/step-grants.json` from the copied `grants.json`. Shape:

```json
{
  "ap": {
    "match": ["tools.get_case_evidence", "tools.get_invoice"],
    "investigate": ["tools.get_case_evidence", "tools.get_prior_cases"]
  }
}
```

Map today's profile display names onto steps:

| Bot | Step | Grant display name |
| --- | --- | --- |
| `ap` | `match` | AP Preparer |
| `ap` | `investigate` | Exception Investigator |
| `ctl-pay` | `review-match` | AP Reviewer |
| `ctl-pay` | `review-pay` | Payment Audit |
| `pay` | `schedule` | Payment Scheduler |
| `email` | `triage` | Finance Inbox Agent |
| `books` | `capture` | ERP Invoice Agent plus Procurement Invoice Agent plus EDI / Electronic Invoicing Agent, as the union |
| `world` | `reply` | Counterparty Message Agent |
| `stripe` | `unpack` | Stripe Payout Agent |
| `bank` | `land` | Bank/Card Discovery Agent |
| `cash` | `reconcile` | Cash Reconciliation Preparer |
| `ctl-cash` | `review-rec` | Cash Reconciliation Reviewer |
| `ctl-cash` | `review-apply` | Cash Application Reviewer |
| `apply` | `apply` | Cash Application Agent |
| `collect` | `chase` | Collections Agent |
| `close` | `accrue` | Accrual Agent |
| `close` | `prepaid` | Prepaid Preparer |
| `close` | `assets` | Fixed Asset Preparer |
| `close` | `bs` | Balance Sheet Reconciliation Preparer |
| `ctl-books` | `review-treatment` | Prepaid Reviewer |
| `ctl-books` | `review-assets` | Fixed Asset Reviewer |
| `ctl-books` | `review-bs` | Balance Sheet Reconciliation Reviewer |
| `ctl-books` | `lock` | Month-End Close Reviewer |
| `story` | `flux` | Variance Analysis Agent |
| `story` | `forecast` | Cash Forecast Agent plus Forecast Variance Agent plus Board Reporting Agent, as the union |
| `audit` | `interpret` | Auditor Agent |
| `audit` | `report` | no ops |

`call_connected_tool` takes the current inbox item, loads the ledger, and allows the op only if it is listed for `(owner, step)`. The error includes the item id and the step: `get_prior_cases is not available at step match of bill:INV-001`.

No current item (Operator DM, or an `ask_bot` consultation) allows the read ops in that Bot's union and no write ops.

A write (`mutability` other than `read`, plus `accrual.tools.create_accrual` and `accrual.tools.reconcile_accrual_with_invoice`) does not run on the first call. The tool stores `pendingWrite` and enqueues the verifier step. The kernel runs the op only when all of these are true:

- The ledger has a `CONCUR` history entry from the verifier Bot for this step.
- `pendingWrite.op`, `pendingWrite.args`, and `pendingWrite.idempotencyKey` equal this call.
- The kernel's own gate for that op passes (`can_sign_off`, reserve, period gate). A TypeScript regex over the op name is not that gate. If the kernel already has the gate, call it. If it does not, add the check next to the op in Python and call it from the RPC path.

A second call with the same idempotency key and different args stays locked. Pass the verifier handle id into that check. Do not pass a literal `null` and then look for a completed handle.

`ctl-pay`, `ctl-cash`, and `ctl-books` cannot call a write op. Their tools are the reads in the step grant plus `complete_step`.

Same-model verifiers are not segregation of duties. Do not write that they are. The control in this pass is the structured decision plus the kernel gate. Do not block the build on a second provider.

## Compaction

On `session_before_compact` with `reason === "threshold"`:

1. Do not let Pi summarize the session as the only record. Cancel the default compaction (`{ cancel: true }` on the before-compact result) after the Bot has had one injected turn whose only job is to write precedents to `sandboxes/<slug>/memory/`. If that turn does not happen, still rotate. A missed memory turn is a note in the README, not a stuck session.
2. Start the successor with the same system-prompt bytes (`assembleContext` is unchanged because the step is not in the prompt).
3. The successor's first user message is: open ledger items whose `owner` is this slug, the memory file, and one line per held item (`id`, `step`, `reason`). Work that exists only in the transcript is gone on purpose.

`reason === "overflow"` stays Pi's own recovery. Do not rotate on overflow.

At most one Pi process per Bot. The engine queues on that inbox.

## Proof E (no model)

A Node script in `.cfo-v5/prove/engine.ts` drives `open_bill` with scripted `complete_step` results. No Pi, no API key.

1. Seed item `bill:INV-001` at step `match`, owner `ap`. Facts from the kernel for `INV-001` (`12450.0`, `PO-101`, `GR-101`).
2. Scripted `APPROVE` from `ap`. The ledger's next step is `review-match` and the owner is `ctl-pay`. The script asserts no `bot_send_prompt` call from a model. The enqueue is `sendPrompt` from the engine. Record the handle id.
3. Scripted `REFUSE` from `ctl-pay`. A following `call_connected_tool` write is refused. The ledger shows `REFUSE`.
4. A second run where `ctl-pay` returns `CONCUR`, then a write with the same idempotency key and different args is refused.
5. `complete_step` with result text `I do not concur` is a schema error, not a `REFUSE` and not a `CONCUR`.

Also run one fixture through `month_end` (`accrue` → `review-treatment`) and one through `cash_line` (`reconcile` → `review-rec`) so those tables are executed.

## Proof S

Sidecar health and `INV-001` as in Proof K, against `.cfo-v5` after the tree exists. `rg` under `.cfo-v5` finds no `workspace/`, no `profiles/`, no `expected_results.json`, no `expected_outcomes.json`, no `ADVERSARIAL`, no `constitution.md`, no `SUPERSEDES.md`.

## Proof H

```bash
node .harness/Harness-v2/dist/src/cli.js serve --computer .cfo-v5 --no-open --port 8800
```

Build Harness first (`npm run build` in `.harness/Harness-v2`). An Operator message to each of the 16 slugs is accepted (HTTP accept, not a model reply). For `ap`, record the assembled system-prompt hash, then enqueue a second item at a different step and record the hash again. The two hashes match.

Memory read and write for `ap` use `sandboxes/ap/memory/` and do not create `harness/bots/bot_ap/memory/`.

Stop the serve process when the proof is recorded.

## README

`.cfo-v5/README.md` starts with "How a wake runs": ten to twenty lines, from inbox item to Pi turn to `complete_step` to the next inbox. Then the proof commands and their real output. Then the serve command. Failures go here too, with the command that failed.

Do not invent a smaller kernel. Do not claim a proof you did not run.

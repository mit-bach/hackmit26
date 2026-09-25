# Profiles — analysis and a replacement design

Outside review, 2026-09-24. Companion to `DESIGN-REVIEW.md`. Data comes from `cfo/slug-map.json`, `cfo/grants.json`, the `BOT.md` and profile files, the CFO extension (`profile.ts`, `index.ts`), `src/context.ts`, the Pi extension types, and the recorded sessions.

**Design constraints this proposal keeps:**

- At most 16 sessions run at once: one per standing Bot.
- Sessions are long-running. A session ends only when it reaches its compaction limit. A successor session for the same Bot then takes over.

---

## 1. Short answer

**Delete the Profile mechanism.** A Profile is chosen by a text header in the wake, parsed by a regex, saved in a sticky file, and swapped inside a running session. Each of those steps is a defect.

**Profiles also work against long-running sessions.** Each switch rewrites the Bot's system prompt and tool scope mid-session. That breaks the prompt cache for the whole history, and it leaves the old Profile's work in the transcript anyway. A long-running Bot should have **one identity, one system prompt, and one tool surface for the life of its session.**

**Keep the scoping, but move it.** Tool scoping should not come from a mode the Bot is in. It should come from the **work item the Bot is holding right now and the step that item is at**. Code decides the step. The tool handler checks each call against it. The Bot's prompt and tool list never change.

---

## 2. Where Profiles came from

`cfo-bot-grain.md` took 43 Python `Agent(name=...)` Display names and asked which *standing identities* the office needs. It concluded that a Display name is not a Bot, and produced 15 Bots (16 today). Each Display name still had its own `tools=` list, and those lists had to live somewhere, so each one became a Profile on some Bot:

> "Display names remain in `cfo/grants.json`. They become Profiles. They do not each get a lane."

The standing-Bot decision was right. The leftover was treating each old Agent's tool list as a *mode of the Bot*. A tool list describes a step of work. It should attach to the step, not to the worker.

---

## 3. What the 41 Profiles actually do

There are 41 Profiles across 16 Bots.

| Group | Count | Profiles | What the Profile changes |
| --- | --- | --- | --- |
| Only Profile on its Bot | 5 | `stripe/payout`, `bank/card`, `pay/schedule`, `apply/apply`, `collect/chase` | Nothing. There is nothing to choose. |
| Same tools as a sibling | 8 | `world/vendor`, `customer`, `bank`, `employee` (one Display name, identical Grant); `email/inbox` = `email/triage` (one Display name); `cash/match` = `cash/investigate` (identical 7 ops) | Only the prompt paragraph. No capability difference. |
| Zero tools | 2 | `close/coordinate`, `audit/report` | No tools at all. |
| Chosen by the input's source channel | 7 | `email/invoice`, `employee`, `portal`, `document`; `books/erp-invoice`, `procurement`, `edi` | Disjoint tool sets (2–3 ops each). The right one follows from where the item came from. |
| Distinct step, distinct tools | 10 | `ap/prepare`, `ap/investigate`; `close/accrue`, `prepaid`, `assets`, `bs`; `story/flux`, `forecast`, `forecast-miss`, `board` | Real differences, but some are small. `story/forecast`, `forecast-miss`, and `board` differ by one op. |
| Reviewer and assurance | 9 | `ctl-pay/review-match`, `review-pay`; `ctl-cash/review-apply`, `review-rec`; `ctl-books/review-treatment`, `review-assets`, `review-bs`, `lock`; `audit/interpret` | Distinct read sets for review. |

Four more facts matter:

- **The per-Bot union is small.** The largest union of a Bot's Profile tools is 23 Kernel ops (`close`). Next are `email` (18) and `ctl-books` (13). Most Bots are under 10. The ops sit behind `search_connected_tools` and `call_connected_tool`, so they never become Pi tool registrations. A Bot can see its whole union without any cost to focus.
- **Most scoping restricts reads.** Of the 101 Catalog ops, 96 are reads. The only writes are two accrual ops (`close/accrue`) and three inbox send ops.
- **The separation of duties that matters is already between Bots, not between Profiles.** Preparer versus Verifier is `ap` versus `ctl-pay`, and `cash` versus `ctl-cash`. No Profile switch is needed for that.
- **Every real selection is decidable by code.** The source channel decides intake. Kernel `exception_types` decides `investigate`. The close checklist decides `accrue`, `prepaid`, `assets`, or `bs`. The op under review decides which review applies. No Profile choice needs judgment, yet all are made by a model writing `profile: …` into a message.

---

## 4. Why the mechanism is wrong

1. **The sender chooses the receiver's capabilities.** An upstream model writes `profile: investigate` into free text, and the receiver's Grant set follows it.
2. **Parsing is loose.** `/^profile:\s*…$/im` matches any line in the wake, including quoted vendor or counterparty text.
3. **State is sticky.** A wake with no header keeps the last Profile, although `BOT.md` promises the default. `active-profile.txt` survives restarts while the in-memory Grant bind resets. The system prompt and the Grant can then describe different Profiles.
4. **Two owners resolve it.** The CFO extension binds Grants. `context.ts` separately reads a file to choose the prompt text.
5. **It rewrites the system prompt of a long-running session.** Every switch changes the bot layer, so the provider reprocesses the entire session history. The longer the session, the more each switch costs. This is the direct conflict with the long-running design.
6. **"Do not union" is false for context anyway.** Tools are replaced, but the transcript keeps the previous Profile's results and reasoning. In a long session, the Bot has already seen precedent from earlier items. The isolation the split promises cannot hold, so it should not be claimed.
7. **Self-handoffs stall.** `cash` sending `profile: investigate` to itself waits 120 seconds, because the lane cannot run its own queued turn while the current turn waits.
8. **Prose multiplies to explain it.** Every `BOT.md` carries a Profiles table, "wear X, never wear both," "replace the Grant set, do not union," and "Profile Y is not on this Bot."

---

## 5. The replacement: standing Bots, item-bound steps

Keep what already fits the philosophy: 16 standing Bots, one lane each, inboxes, Handles, `ask_bot`, Rooms, and per-Bot Memory. Change four things:

1. Code owns routing and step selection.
2. Each Bot has one stable prompt and one stable tool surface.
3. Tool calls are authorized against the **current item's step**.
4. Compaction rotates the session over durable state.

### 5.1 The item ledger (new, small)

The office tracks one record per open item: a bill, a bank line, an unapplied payment, a payout, or a period. It is the durable state of the office. The transcript is working memory, and the ledger is the record.

```json
{
  "id": "bill:INV-004",
  "workflow": "open_bill",
  "step": "investigate",
  "owner": "ap",
  "facts": { "exception_types": ["PRICE_VARIANCE"], "must_hold": false },
  "history": [
    { "step": "match", "by": "ap", "result": "runs/ap/packets/INV-004.json", "t": "…" }
  ]
}
```

It lives on the Computer, for example under `runs/items/`, and only code writes it: the engine and the Kernel. Bots read it through a tool.

### 5.2 The workflow engine (code, replaces English `## Handoffs`)

Each item class has a small state machine. The engine reads Kernel facts, chooses the next step and its owner Bot, and **enqueues a wake on that Bot's existing inbox**. It never starts a session. The 16 standing sessions stay the only sessions.

```ts
const openBill: Workflow<OpenBill> = {
  start: { step: "match", owner: "ap" },
  next: (bill, step, result) => {
    if (kernel.mustHold(bill)) return { terminal: "hold" };
    switch (step) {
      case "match":
        return bill.exceptionTypes.length > 0 || result.decision === "INVESTIGATE"
          ? { step: "investigate", owner: "ap" }
          : result.decision === "APPROVE"
            ? { step: "review-match", owner: "ctl-pay" }
            : { terminal: "hold" };
      case "investigate":
        return result.decision === "APPROVE"
          ? { step: "review-match", owner: "ctl-pay" }
          : { terminal: "hold" };
      case "review-match":
        return result.decision === "CONCUR" && kernel.allows(bill)
          ? { emit: { workflow: "pay_run", item: bill.invoiceId } }
          : { terminal: "hold" };
    }
  },
};
```

Wakes are written by code in a fixed header. Peer free text is never parsed for control:

```text
[harness wake]
kind: item_step
item: bill:INV-004
step: investigate
packet: runs/items/bill-INV-004.json
```

`close/coordinate` disappears as a Profile. The month-end checklist is a workflow, and it enqueues `accrue`, `prepaid`, `assets`, and `bs` steps on `close` for the items that need them.

### 5.3 Finishing a step: `complete_step` (replaces routing by `bot_send_prompt`)

A Bot finishes its step by calling one tool with a typed result:

```ts
complete_step({
  item: "bill:INV-004",
  result: { decision: "HOLD", reason: "…", evidence_used: ["PO-105", "GR-105"] },
  paths: ["runs/ap/packets/INV-004.json"],
});
```

The engine validates the result against that step's schema, updates the ledger, and routes. **If the next step belongs to the same Bot, the tool result returns the next step immediately, and the Bot continues in the same turn.** The self-handoff and its 120-second stall disappear. If the next step belongs to another Bot, the engine writes a Handle to that Bot's inbox, and this Bot's turn ends.

`ask_bot` stays for what it is good at: free-form consultation between colleagues ("have you seen this vendor alias?"). It no longer carries routing or approval.

### 5.4 One stable prompt and tool surface per Bot

The system prompt for a Bot is fixed for the life of its session:

```text
<Pi base> + office/system.md + Roster + BOT.md (all steps this Bot owns) + union of its skills
```

`BOT.md` gets one section per step the Bot owns. These sections carry what the Profile files said, minus the Profile machinery. `ap/BOT.md` has `## Step: match` and `## Step: investigate`. The wake names the step, and the Bot reads the matching section, which is already in its context.

The Bot's Kernel tool surface is the **union** of what its steps need. The prompt never changes mid-session, so the whole history stays cached. This is the best case for a long-running session.

### 5.5 Item-bound authorization (what replaces Grant switching)

Scoping moves from "which Profile is bound" to "which item and step does this Bot hold right now." `call_connected_tool` checks each call like this:

1. Find the Bot's current inbox item. Look up its ledger record and step.
2. Look up the allowed ops for `(bot, step)` in a compiled table (`cfo/step-grants.json`, compiled from today's `grants.json` content).
3. Refuse any op outside that list with a clear message: `get_prior_cases is not available at step match of bill:INV-004`.
4. For write ops, also require the item's ledger state to permit the write. For example, `create_accrual` requires a stored `CONCUR` from `ctl-books` on that item. The Kernel enforces this, not a TypeScript regex.

When the Bot holds no item (an Operator DM or a peer consultation), it gets the read ops of its union and no writes.

The `(bot, step)` table looks like today's Grants. The difference is who selects, when, and what changes:

| | Profile today | Step grant |
| --- | --- | --- |
| Who selects | A model writing `profile:` into free text | The engine, from Kernel facts, written in the ledger |
| Where it is stored | `active-profile.txt` and extension memory, which can disagree | One ledger record |
| What changes on a switch | System prompt, bot layer, Grant bind | Nothing in the session. The next call is checked against the new step. |
| Default when missing | Stale previous Profile | No item means read-only union |
| Prompt cache | Broken on every switch | Stable for the whole session |

### 5.6 Verification in a long-running world

Verifier Bots (`ctl-pay`, `ctl-cash`, `ctl-books`) stay standing. The engine gives them review steps like any other step. They answer with `complete_step({ decision: "CONCUR" | "REFUSE", reasons })`, which is structured and never parsed from prose. The engine stores the decision on the item. Kernel write commands check that stored decision.

Deterministic checks (`can_sign_off`, ties to zero, reserve not breached) move into Kernel functions. The Verifier's step then covers only what needs judgment. Where possible, run Verifiers on a different model or prompt style from the preparers, so their errors do not correlate.

The "`ap/prepare` must not see precedent" rule cannot hold in a long session, because the Bot has already seen precedent from earlier bills. Step authorization still blocks `get_prior_cases` during `match`, which stops fresh lookups. The real independence check is `ctl-pay`, a separate Bot. State this plainly in `BOT.md` instead of promising isolation.

### 5.7 Compaction is the session boundary

Each Bot's session runs until Pi's compaction threshold. Pi's extension API fires `session_before_compact` with `reason: "threshold"`, and the extension may cancel it or supply its own compaction result. Use that hook as the rotation point:

1. **Before rotation**, the extension gives the Bot one turn to write what it learned to Memory: precedents keyed by vendor, account, or processor, not transcripts. This finally gives `memory_write` a real job. Today it is nearly unused: 19 calls across 62 sessions.
2. **Harness ends the session** and starts the successor for the same Bot, with the same system prompt bytes, so the cache prefix carries over.
3. **The successor's first message** is built from durable state:
   - the ledger items this Bot owns that are still open, with their steps;
   - the Bot's `MEMORY.md`;
   - a short summary of the last session, such as the recent threads and why items were held.

Nothing about the work lives only in the transcript. That lets a long session be long safely: losing a session loses working memory, not office state.

### 5.8 Concurrency

The office has at most 16 Pi processes, one per Bot, each processing its inbox in order. Parallelism comes from different Bots working different items at once. When a Bot has a backlog, the engine queues on that Bot's inbox. It never spawns a helper session.

---

## 6. Mapping from Profiles

| Today | Becomes |
| --- | --- |
| 5 single-Profile Bots | No change in behavior. Delete the Profile file and fold it into `BOT.md`. Each has one step. |
| `email` 4 channel Profiles, `books` 3 channel Profiles | Steps chosen by the event's source channel (`intake.email`, `intake.portal`, …). One `BOT.md` section each, or one section with a per-channel paragraph. |
| `email/inbox` + `email/triage` | One step, `triage` |
| `world` × 4 | One step, `reply`. The counterparty type is a field on the item. |
| `cash/match` + `cash/investigate` | One step, `reconcile`. The exception guidance is a subsection. The tools were already identical. |
| `ap/prepare`, `ap/investigate` | Two steps on `ap`. The engine picks `investigate` from `exception_types`. `ap` continues in the same turn through `complete_step`. |
| `close/accrue`, `prepaid`, `assets`, `bs` | Four steps on `close`, enqueued by the month-end workflow |
| `close/coordinate` | Deleted. It is the month-end workflow. |
| `story` × 4 | Steps `flux` and `forecast`. Forecast, miss, and board differ by one op and a paragraph. |
| `audit/interpret`, `audit/report` | Two steps on `audit`, in sequence, same turn |
| 8 reviewer Profiles | Review steps on `ctl-*`. Deterministic parts move into the Kernel. |

The result is 41 Profiles becoming 28–33 steps across the same 16 Bots. The range depends on whether the seven intake channels stay separate steps or become two. No step changes the prompt or restarts a session.

---

## 7. What changes and what does not

**Unchanged:** 16 standing Bots, one Pi session each, lanes, inboxes, Handles (accepted ≠ completed), `ask_bot` for consultation, Rooms, per-Bot Memory, the Operator DM, and `assembleContext` with hashed layers. Most of Harness v2 stays exactly as it is.

**Removed:** `profile:` headers, `parseProfileFromWake`, `active-profile.txt`, `replaceProfile`, the `slug-map` Profile layer, `profiles/*.md` as separate files, self-handoffs, routing by `bot_send_prompt`, and the Profile-explaining prose in every `BOT.md`.

**Added:**

- the item ledger;
- the workflow engine, about one state machine per pipe;
- `complete_step`, with typed results per step;
- `step-grants.json`, compiled like today's Grants;
- compaction rotation in the Harness extension.

---

## 8. Migration path

Each step is useful on its own, and the demo keeps working after each one.

1. **Freeze the prompt per session.** Put every step section into `BOT.md` and paste the union of skills. Keep Profiles only as the Grant filter for now. The system prompt stops changing mid-session.
2. **Resolve the step in code.** Add the ledger for AP. The router writes `step:` from Kernel facts, and `call_connected_tool` checks `(bot, step)` against the ledger. Stop reading `profile:` from wake text.
3. **Add `complete_step`** for `ap` and `ctl-pay`. Route AP through the engine instead of `## Handoffs` prose. Compare the result against the recorded golden run.
4. **Collapse the no-op Profiles:** the single-Profile, identical-Grant, and zero-tool groups (15 of 41).
5. **Wire compaction rotation:** the Memory turn, the successor session, and the ledger-built opening message.
6. **Repeat for cash, close, and intake.** Then delete the Profile code path.

After step 2 the Profile concept is harmless. After step 6 it no longer exists, and the 16 sessions run from one stable prompt each until compaction.

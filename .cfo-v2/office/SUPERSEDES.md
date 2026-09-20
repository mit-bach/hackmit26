# SUPERSEDES

Client-system voids. Kernel math stays. These sentences and designs are not the office’s completion path.

Queue owner for fail-closed Kernel statuses named `HUMAN_REVIEW` is a Verifier Bot (`ctl-pay`, `ctl-cash`, `ctl-books`). The Harness Operator (human HTTP/control plane) is an emergency stop and a demo overlay. It is not a worker. It is not a review queue.

---

## 1. `.cfo/README.md` — human review as a first-class completion state

VOID as office law:

> Human review is a first-class state in AR cash application, bank reconciliation, and month-end close.

Those Kernel statuses may remain as fail-closed outcomes (do not auto-post). They do not complete by waiting on a person. `ctl-cash` owns material cash-application and bank-rec concurrence. `ctl-books` owns period lock concurrence. `ctl-pay` owns AP match concurrence, pay-run release, and write-off.

Related README architecture pointers that treat “human-review paths” as the control layer are VOID for completion. Keep Python validators.

---

## 2. `docs/CFO_HARNESS_EXTENSION.md` — human Operator as pay-run, period lock, or review gate

VOID every sentence that parks pay-run, period lock, or review on the human Operator. Verifiers own concurrence.

Named voids (informative; the rule is the class, not only these lines):

| Location (as of 2026-09-19) | VOID text |
| --- | --- |
| §1 Name map, Operator | “The human. Approvals and period lock sit here.” |
| §5.1 mutability | “Period lock, pay-run release, write-off, send-as-user: `side-effect-external` … because the Operator gate must fire.” Consequential ops still fail closed. The gate owner is the named Verifier Bot, not `ask_user`. |
| §5.4 | “Operator timeout on approval \| Deny.” Do not use Operator timeout as the office’s concurrence clock. |
| §6 | “The human SoD that the process doc gives to a Reviewer is the Operator approval path, not a Grant union.” SoD stays as **separate Profiles and Verifier slugs**. It is not a human queue. |
| §8.2 | Intercept that waits on Harness Operator approval before Sidecar for consequential ops. Client intercept must Handle to `ctl-*`. A peer Handle is still not approval. |
| §11 | “Human review still mutates **source** objects, then a rerun. Harness `ask_user` is the Operator gate for consequential Kernel ops.” |
| §11 | “Do not add a send-as-bank Connector without an Operator gate.” Send-as-bank is not in session 00. When it exists, concurrence is `ctl-pay` / `ctl-cash`, not the human Operator. |
| §13 item 9 | “Month-end still ends `BLOCKED` on the planted $12.40 cash break until a human mutates source objects and the host reruns.” The planted trap stays fail-closed. The queue owner is `ctl-cash` / `ctl-books`. Autonomy is not “always post.” |

Keep from that document: compiler, Catalog, Grants, slug-map shape, Sidecar RPC, eval isolation, no finance types in Harness core, no Grant unions, Computer layout.

“Operator-owned” as applied to `cfo/slug-map.json` means **this Client system owns the file**, not that a human must edit it to complete a period.

---

## 3. CLI commands whose happy path is a person mutating a review queue

VOID as the office’s completion path. They may remain as eval fixtures / emergency tools.

| Command | Why void as completion |
| --- | --- |
| `python main.py ar-review-correct …` | Person mutates an AR review queue |
| `python main.py ar-review-list` / `ar-review-show` | Human review queue inspection as the happy path |
| `python demo_month_end_close.py --resolve` | Person resolves planted close blockers |
| `python close.py reviews --period …` | Human review listing as close completion |

Reruns after a Verifier concurrence plus Kernel-allowed source mutation are Kernel/eval machinery. They are not a human ticket in the Bot network.

---

## 4. In-process `Runner` as the Bot bus

VOID. Do not port OpenAI Agents SDK `Runner`, in-process `Agent()` handoffs, or child/subagent trees as the standing office.

The Bot bus is Harness: write a path on the Computer, `bot_send_prompt`, accept-time Handle, await done. Peer Handle is not approval.

---

## 5. `examples/cfo-floor` as the Roster

VOID. `.harness/Harness-v2/examples/cfo-floor` is a Harness bind fixture (six slugs including `ingest`). It is not this office.

This office’s Roster is `office/computer/harness/roster.json`, system `cfo-agentic-system`, fifteen grain slugs. Do not copy that example. Do not add slug `ingest`. Do not put 15 Bots in one Room.

---

## Harness v2 (do not fork)

`GROK-WORKSHOP/harness-init/engineers/lark/HARNESS-V2.md` describes a human gate on the Operator for consequential actions. For this Client, that sentence is VOID at the office layer. Do not edit `.harness/Harness-v2/src` to know what an invoice is. Map `blocked` / concurrence to Verifier slugs in Client code (later sessions). Roster `approvalLevel` for these fifteen Bots is `"never"`.

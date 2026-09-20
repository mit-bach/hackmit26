# Surface — memory and learning

Maximor scoring looks for memory that changes what the system does next. Process law: a Bot keeps Memory that changes the next period. A pure function over one JSON blob is Kernel, not a Bot.

---

## Intended function of this surface

Each Bot stores precedents about its object:

- Email: this vendor’s attachment layout.
- apply: this customer’s remittance habit.
- collect: this customer’s promise and dispute habit.
- ap: this vendor’s alias and invoice layout, only if Kernel still supports it.
- cash: this processor’s payout label.
- close: this vendor’s usual accrual method, only if current evidence supports it.
- story: which metric usually moves.
- audit: which control needs which evidence class.
- World (if bound): how this counterparty delays.

Never another Bot’s Memory. Never ground truth. Never editing a statement in Memory to clear a break. Precedent is color. It cannot override a present fact or a hard hold.

---

## What exists that is good

- BOT.md Memory sections exist as boundaries.
- Kernel AR precedent path: correction → retrieve on a later similar remittance.
- `prior-period-precedent` Skill names the right rule: reuse only when current evidence supports it.
- `memory.tools.get_decision_memories` exists as a Catalog op on some Grants (accrual, etc.).
- Harness per-Bot Memory tree: `MEMORY.md`, topics, log. Isolation is the right shape.
- Identity links in close/context are provenance, not a fake graph DB. Demo gaps admit RAG is not built.

---

## What is broken

### AP does not learn (T10)

`prior_cases.json` static. Demo gap NOT_IMPLEMENTED. Alias INV-021 is a seed, not a loop.

### AR learns through a voided CLI (T9, T10)

`record_human_application` is the learning write. SUPERSEDES voids human review CLI as completion. Verifier concurrence does not clearly write the same precedent.

### Sidecar remap miss (migration audit, T11)

Decision memories could land under `.cfo/runs/memory` instead of Computer `runs/memory`. Restart loses office memory. Audit claimed a fix. Live proof is not in the 09-20 Handle set.

### Pi Memory tools vs Kernel memory tools (T2)

Harness `memory_read` / `memory_write` are per-Bot markdown. Kernel `get_decision_memories` is a Catalog op. Two stores. A Bot told to “keep Memory” may write the Harness file and never affect Kernel candidates, or the reverse.

### prior-period-precedent over-assigned (T7)

One Skill on AP, cash, prepaid, accrual, lock. Becomes an essay. Stops being object-specific habit.

### Semantic graph claimed in Maximor brief, not built

Do not ship a context-graph story. Capabilities.md already forbids it.

### bot_pay and bot_audit had custom MEMORY.md; others default one-liners (09-19)

Most Memory files were the default standing note. That is not habit.

---

## Capability this surface must possess

When memory is adequate:

1. A decision on an open item can be retrieved the next period by the Bot that owns that object class.
2. Retrieval cannot override Kernel hard holds or a contradictory live document.
3. AP and AR both can change behavior without a human editing a seed JSON as the happy path.
4. Harness Memory and Kernel memories do not silently diverge, or the office picks one SoT per fact type and keeps it.
5. No Bot stores another Bot’s object.

How embedding, files, or traces are arranged is novelty. This file requires the change in next-period behavior, and the fail-closed override rule.

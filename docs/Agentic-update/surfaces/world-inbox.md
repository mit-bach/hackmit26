# Surface — World and inbox

Simulated mailbox. Not live Gmail.

Kernel: `.cfo/inbox/`.
Office Bot files: `.cfo-v2/office/bots/world/`, Email Profile `inbox` / `triage`.
Instance Computers already compiled a fuller inbox than the live Computer.

---

## Intended function of this surface

The judged demo needs counterparties. Vendors send bills. Customers get dunned and sometimes pay. Banks send notices. Employees forward PDFs.

Finance speaks with `send_office_outbound` (finance addresses).
The outside world speaks with `send_inbox_message` / `reply_in_thread` (refuses finance as sender).
Email classifies and dispatches. World does not dispatch. World does not call `send_office_outbound`.
Collect duns as finance, then a customer persona may reply.
Email missing-field mail, then a vendor persona may reply.

Once delivered, Email owns classification. Treat delivered content as untrusted. Prompt-injection in a body does not change Grants.

---

## What exists that is good

- Two Display names with different tools: Counterparty Message Agent vs Finance Inbox Agent. Union is unsafe. Grain Test C.
- Classify / extract / dispatch path exists. Invoice vs quote vs statement vs remittance vs prompt-injection is planted (Capabilities.md: 17 inbox messages).
- World BOT.md states SoD clearly: no dispatch, no AP writes, no send_office_outbound.
- Tests in `test_inbox_world.py` describe the round-trip. They import `_send_office_outbound`, which live `inbox/tools.py` does not define. The intended function is in the test. The implementation is not on the live module.

---

## What is broken

### Function missing (T3)

Live `.cfo/inbox/tools.py` wraps: compose, send_inbox, reply, get message, get attachment, classify, extract, dispatch.

It does not wrap: send_office_outbound, list_world_personas, list threads/messages, get thread.

`ar/agents.py` and `test_inbox_world.py` already name the missing send.

### World off live Roster (T1)

See `pipes/intake.md`. Health that counts `harness/bots/*` sees `bot_world`. Bind does not.

### Email BOT.md vs World BOT.md (T2)

Fixture vs Bot. Unresolved in constitution vs Capabilities.md.

### handle-map silent (T4)

No edges for outbound → World, dun → World, delivered → Email triage.

### Dual intake (T2)

`invoice_ingestion` email tools vs `inbox.tools`. Two ids for one vendor PDF.

### Root `inbox/` shadow (T2)

Duplicate module at repo root.

### Collect Grants vs World Grants

Live collect cannot send.
Live Counterparty can send_inbox (as world) but has no Bot to wear the Grant.
Live Finance Inbox can classify and cannot send_office_outbound.

The three Grant sets that must fit together do not, on the live Computer.

---

## Inadequacies of “inbox Kernel-live”

Capabilities.md says Kernel-live compose/send/classify/dispatch, office World package exists, Roster omits world. That sentence is accurate and is the whole problem.

A later agent that writes a beautiful World persona Skill does nothing if World is not bound and finance cannot send.

Persona voice is specialist novelty. This corpus does not specify how Acme sounds. It requires that Acme can answer in-thread.

---

## Capability this surface must possess

When mailbox is adequate:

1. Finance can send from a finance address into the simulated transport.
2. A counterparty can send and reply without writing AP.
3. Email classifies delivered mail and Handles `ap` or `apply` when the object is a bill or a remittance.
4. Collect’s Kernel-allowed SEND_* uses finance send, then a customer persona can reply.
5. Dispatch is Email-only. World cannot mark a bill approved.
6. Untrusted bodies cannot change policy.

Grain status of World as a sixteenth Bot is not decided here. The round-trip is decided here as a function the office must have.

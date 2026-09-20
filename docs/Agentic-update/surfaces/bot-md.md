# Surface — BOT.md

Template: `.cfo-v2/office/templates/BOT.md`.
Live files: `.cfo-v2/office/bots/<slug>/BOT.md`.
Harness injects Roster `instructions`, which point at those files.

---

## Intended function of this surface

BOT.md is standing identity. It answers:

- Who are you.
- What object you own.
- How you wake.
- Which Profiles you may wear (not unioned).
- Which Catalog ops the active Profile may call.
- Which Kernel validators you cannot override.
- Who you Handle, and that peer Handle is not approval.
- Which Verifier owns your fail-closed work.
- What Memory you may keep.
- What you must not do.
- When you are done.

It is not a Skill. It is not a workflow runner. It is not a match algorithm.

Constitution required headings match the template. Identity first line: `You are Bot `{slug}`. You own {object}.`

---

## What is good

All fifteen grain slugs have real BOT.md files (not session-00 stubs). World has a sixteenth file. Required headings are present.

Object ownership is usually sharp: `ap` open bills, `pay` the draft, `apply` unapplied cash, `collect` open invoices after apply, `cash` unmatched bank lines, `close` period completeness, `story` the story of the books, Verifiers concurrence not the open item.

Must-not lists repeat law that is easy to violate (ask a human, spawn children, invent amounts, union Grants). That repetition is cheaper than a silent SoD break.

Done-when on AP, pay, cash, close is mostly object-level, which is the right grain.

---

## What is broken

### Computer cannot read the file at the path Roster names (T6)

Instructions: `Read office/bots/<slug>/BOT.md and obey office/constitution.md`.
Computer cwd: `office/computer`.
Resolved path: `office/computer/office/bots/...` — missing.
Actual file: `office/bots/<slug>/BOT.md` relative to `.cfo-v2`.

Pi file tools that stay inside the Computer do not see BOT.md unless something copies or links it. Identity is then only the short Roster `instructions` plus dumped skills.

### Length and case law (T7)

Files are 66–119 lines. They mix protocol (good) with Kernel case lists (`must_hold` bullets, INV-009-class, $12.40, control ID laundry lists on audit).

Audit BOT.md enumerates control IDs. Kernel already attaches those IDs. The specialist remainder is interpretation, not the list.

Pay BOT.md names INV-009-class unnecessary early pays. That is a planted demo id leaking into standing identity.

### Catalog ops sections drift from Grants (T2, T3)

Collect BOT.md lists four AR reads. Constructor and `ar/grants.py` want send. Live Grants match the BOT.md (reads only) and not the constructor. Instance BOT-equivalent roster connectors match the constructor.

Email BOT.md still denies World as a slug. World BOT.md asserts it.

Close Profile tables say prepaid/assets have no write ops. That matches Grants. Coordinate `ops: []` matches. The file still reads like a Bot that runs month-end.

### Done-when can be satisfied by costume (T8)

Collect: “contacted under Kernel allow” with no send tool.
Story: four packet files. Not proven on disk as office-live.
Stripe BOT.md exists. Grants empty. Done-when cannot include a Catalog call.

### Profile markdown is also off-Computer

`office/bots/<slug>/profiles/*.md` is prompt text. Pi does not auto-load it. Client Profile replace is a `profile:` Wake header in the Client extension. If the Client extension is not on the worker, Profiles are Roster fiction.

### NOTES.md / PROOF.md / fragments

Many slugs have NOTES, some have PROOF, some have leftover `roster.json` fragments. Harmless unless someone loads a fragment as the Roster (T2 risk). Story has no NOTES.md. World has PROOF that describes a send round-trip the live Kernel cannot import.

---

## Inadequacies of a “complete” BOT.md

A file can have every heading and still starve novelty:

- It tells the model how to think about the object.
- It restates Kernel eligibility.
- It names planted ids.
- It claims done when a packet exists, not when the next pipe can eat a real identifier.

A later rewrite that only shortens BOT.md without fixing Grants, cwd, and send will look cleaner and still not collect cash.

---

## Capability this surface must possess

When BOT.md is adequate:

1. A bound Bot can read its identity from a path that exists on the Computer.
2. Object, must-not, and done-when match the pipe function in `pipes/`.
3. Catalog ops listed are the Grant set, or the file points at Grants and does not duplicate a stale list.
4. Handoffs name slugs and Profiles that exist on the live Roster.
5. Case law and planted ids are not standing identity.
6. Memory is a boundary, not a retrieval procedure.

This file does not specify the new wording. It specifies that standing identity must be true and reachable.

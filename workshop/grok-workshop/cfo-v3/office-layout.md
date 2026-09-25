# Layer 2 — One Computer

## Wrong, found 2026-09-24T21:49Z

This layer built the wrong shape. `.cfo-v3` is one flat Computer. It holds `workspace/<slug>/` and `runs/` made by hand, and `kernel/` and `world/` sit inside the directory that is every Bot's `cwd`.

The sandbox design is different. `workshop/docs/Office-show/SANDBOX-INIT.md` and `.harness/Harness-v2/src/sandbox.ts` say Harness makes `workspace/`, `runs/`, and memory directories when it initializes a Computer. `createOfficeInstance` in `src/server/office-instances.ts` clones a template into `instances/<id>/` and runs `initComputer` there. Each instance is its own sandbox. `office.json` lists them. A hand-made `workspace/` in the template is copied into every instance by `cloneTemplateComputer`.

Target:

```text
.cfo-v3/
  kernel/            not under any Bot cwd
  world/maximor/     read-only source for data/
  template/          office/, skills/, cfo/, harness/{roster,client,intercept}.json. No workspace/, no runs/.
  office.json
  instances/<id>/    created by Harness. data/ -> ../../world/maximor
```

The text below this section describes the flat layout and is not the target.

Authority: `DESIGN-REVIEW.md` sections 6 and 7, and `bloat-eviction.md` on this desk. This file replaces the earlier draft of the same name.

Depends on layer 1 only for the compiler command. Directory creation can start before the kernel copy finishes. Do not write `.cfo-v3/kernel`.

## Job

Create one Computer at `/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3`. The process `cwd` for every Bot is this directory. Nothing else is on `PYTHONPATH` except `.cfo-v3/kernel`.

```text
.cfo-v3/
  kernel/                 layer 1
  office/
    system.md
    bots/<slug>/BOT.md
    bots/<slug>/profiles/
  skills/<name>/SKILL.md
  data/                   world pack the tools read. No answer keys.
  cfo/                    catalog.json, grants.json, slug-map, path-leases.json
  harness/                roster.json, client.json, intercept.json
  workspace/<slug>/{packets,handles,notes}/
  runs/<domain>/
```

`computer/office/bots` as a second tree does not exist. One Bot directory.

## Copy

- World registers, invoices, bank, payroll, vendors, customers, documents. From `.cfo-v2/office/world/maximor`.
- Roster of the 16 slugs and the client extension the serve process loads. Point its Python at `.cfo-v3/kernel`.

## Do not copy

See `bloat-eviction.md`. In particular: `expected_results.json`, `expected_outcomes.json`, `holdout/`, `sessions/ADVERSARIAL-SCENARIOS.md`, `constitution.md`, `SUPERSEDES.md`, `PROOF.md`, `NOTES.md`, `HOST.md`, protocol-card `SYSTEM.md` copies, `prove-fork/`, `office/instances/`, `final-demo/`, reference datasets, and both extra skill trees. `.cfo/skills` is not a second source. If a skill body is pasted, it lives only under `.cfo-v3/skills`.

## Done when

`find .cfo-v3 -name 'ADVERSARIAL*' -o -name 'expected_results.json' -o -name 'PROOF.md' -o -name 'SYSTEM.md'` prints nothing.

`workspace/` has 16 slug directories and no `sources/`.

Write the tree you actually created under `## Proved`.

## Proved

[Office layout](9589c949-2cdd-413d-a93f-6a54a55e8dff) created the Computer before this plan text was rewritten. Checked on disk: `.cfo-v3/world/maximor`, `.cfo-v3/data` symlink, `.cfo-v3/cfo/catalog.json`, `.cfo-v3/workspace/ap/packets`. A search for `ADVERSARIAL*`, `expected_results.json`, and `PROOF.md` under `.cfo-v3` printed nothing.

Still absent, owned by the Bot-text layer: `office/system.md`, `BOT.md`, `profiles/*.md`, `SKILL.md`, `cfo/path-leases.json`. Skill directories exist and are empty.

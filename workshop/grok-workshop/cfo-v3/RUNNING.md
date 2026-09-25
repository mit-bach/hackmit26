# RUNNING

Desk: `/Users/dominikbach/olympus/hackmit/hackmit26/workshop/grok-workshop/cfo-v3`

Branch: `cfo-v3`. Do not commit from this desk unless the operator says so.

`Deployment/` is absent.

Live children:

| id | tag | workspace | session | writes |
| --- | --- | --- | --- | --- |
| kestrel | engineer | `engineers/kestrel/` | 7219b67c-1df7-4418-b898-0826a130d99c | `.cfo-v3/cfo/{catalog,grants,slug-map}.json` via compiler |
| lark | writer | `engineers/lark/` | c3d6b816-59ad-4bb0-8e65-438b30fbc559 | markdown under `.cfo-v3/office` and `.cfo-v3/skills` |
| heron | verifier | `engineers/heron/` | 52888ed5-d831-4dc0-b3af-c789751bd3f1 | own workspace only |
| wren | engineer | `engineers/wren/` | cdca3358-b594-4ad1-8138-809bf9a4d5a0 | `.cfo-v3/cfo/extensions/` |
| finch | engineer | `engineers/finch/` | 537f2d25-9dc0-438a-88c8-03a9eaeb9171 | `.cfo-v3/kernel/*.py` |
| sparrow | engineer | `engineers/sparrow/` | f0756d1b-bdf2-4404-bc34-de591b701233 | `.cfo-v3/cfo` package files and `node_modules` |
| osprey | engineer | `engineers/osprey/` | dff27c44-b089-4d39-aa51-c54be9778ea4 | `.cfo-v3/cfo/extensions/{intercept,call,index}.ts` |
| plover | engineer | `engineers/plover/` | 79984973-819f-4a6b-beb4-41bb22d286ea | `facade.test.ts`, `.cfo-v3/harness/intercept.json` |

Finished: kestrel (grants compiled; parent placed `catalog.overrides.json`), wren (verifier handle lookup and structured CONCUR).

The four chat workers without an archive have all finished: kernel copy, office layout, Bot text, and Harness wiring. Their notes are the `## Landed` or `## Proved` sections of the plan files.

Key files:

- `/Users/dominikbach/olympus/hackmit/hackmit26/workshop/docs/Office-show/DESIGN-REVIEW.md`
- `/Users/dominikbach/olympus/hackmit/hackmit26/workshop/docs/Office-show/PROFILES-AND-PROPOSAL.md`

Persona for the next child: `/Users/dominikbach/.grok/skills/eng-orch/shared/personas/engineer.md`

## Authority

The operator rejected the first five plan drafts because a subagent wrote them. Those files were rewritten in this desk by the parent on 2026-09-24. The rewritten files are the plans. `DESIGN-REVIEW.md` wins over `PROFILES-AND-PROPOSAL.md` where they conflict, except that the profile mechanism is a known defect and is not built into an item ledger in layers 1–5.

## Sandbox correction (2026-09-24)

The operator rejected the desk layout. `engineers/<id>/` is orchestration scratch. It is not a Bot sandbox.

The sandbox that already exists is in `.harness/Harness-v2/src/sandbox.ts` and `workshop/docs/Office-show/SANDBOX-INIT.md`. One Computer is the jail. Each Bot may write only `workspace/<slug>/{packets,handles,notes}` and `harness/bots/bot_<slug>/memory/`. Several agents writing one shared `.cfo-v3` at the same time is the opposite of that.

Do not launch another child onto the shared `.cfo-v3` tree. The next child, when the operator names the start, gets its own Computer clone, does one layer there, and the parent copies the result back. Subagent output already on `.cfo-v3` is untrusted until a verifier reads it.

Use model `grok-4.7-xhigh` for the next child. Do not mint a bench.

## Open work

Leave `.cfo` and `.cfo-v2` on disk. Do not delete them. The office that runs is `.harness/Harness-v2` plus repo-root `.cfo-v3` only.

Layers, in order. A later layer does not start until the prior layer's `## Proved` section exists, except layer 3, which only touches Harness and may run beside layer 1.

1. `kernel-migration.md` — Python into `.cfo-v3/kernel`. No import of repo `.cfo`.
2. `office-layout.md` — one Computer. Ban list is `bloat-eviction.md`.
3. `harness-wiring.md` — verifier handle, concurrence parse, bash boundary, profile header. Serve `.cfo-v3`.
4. `behavior-and-tools.md` — Bot text under `.cfo-v3` only. No item ledger.
5. Prove — one serve, health shows the `.cfo-v3` Computer, a granted read runs, answer keys are not on that tree. No new golden tape in this arc.

`prompts/` stays empty until a mission is archived. `engineers/` stays empty until that launch. The next launch is one child for layer 1, after the operator says to start the layers.

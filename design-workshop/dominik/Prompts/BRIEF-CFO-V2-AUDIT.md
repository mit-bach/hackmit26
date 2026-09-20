# Explore brief — CFO V2 gap analysis

You are auditing a migrated Client system. Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

Migrated office: `.cfo-v2/` (not `.cfo/`). Original kernel: `.cfo/`. Grain: `design-workshop/dominik/cfo-bot-grain.md`. Extension contract: `docs/CFO_HARNESS_EXTENSION.md`. Migration prompts: `design-workshop/dominik/Prompts/CFO-HARNESS-MIGRATION-SESSIONS.md`. Harness v2: `.harness/Harness-v2`. Layout: `docs/LAYOUT.md`.

Return a structured report. Do not write files. Do not modify anything.

Investigate with paths:

1. Tree of `.cfo-v2/office/` — bots, computer, sessions, compiler, extensions, skills, RUN.md, constitution, roster.json
2. `office/computer/harness/roster.json` vs Harness v2 BotRecord (id, name, slug, purpose, instructions, skills, connectors, approvalLevel). Rooms 2-6? Routines? approvalLevel never?
3. Roster vs grain 15 slugs. Fragments vs merged roster.
4. Skills: `.cfo/skills/` vs `.cfo-v2` Computer skills/. SKILL.md copied? roster.skills populated? extension skill intersect used? Count original vs v2.
5. Extensions under `.cfo-v2/office/computer/cfo/extensions/` and compiler. One barrel or modular? Load WITH Harness (`pi -e harness -e cfo`)? Bind register tools? Fake vs real Pi?
6. Sidecar / kernel: `python -m cfo_kernel` real? Grant re-check? Persist overlays?
7. Session PROOF.md 00-12 — claimed vs proven (fake handles vs live Pi)
8. BOT.md quality; whether roster.instructions point at a path Pi can actually read from the Computer cwd
9. Protocol: protocol.jsonl, handles, inboxes — Harness writes or hand-rolled?
10. What still uses OpenAI Agents SDK Agent()/Runner in `.cfo-v2` or `.cfo/` as the bus?
11. Missing Harness attach: HARNESS_BOT, HARNESS_COMPUTER, HARNESS_EXTRA_EXTENSIONS, worker bind, boot of 15 bots
12. slug-map, catalog, grants — compiled or empty?
13. Verifier routing vs ask_user
14. Boot path: exact commands that would fail and why

Return: what is real; what is disconnected from Harness; what is missing; skills transfer counts; extension modularity; boot failures.

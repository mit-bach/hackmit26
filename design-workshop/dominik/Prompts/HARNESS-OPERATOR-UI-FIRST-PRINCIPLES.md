# Harness Operator UI — first-principles review, then intentional cut

Paste-ready prompt for **one** fresh Cursor Agent session. This session owns the Operator shell under `.harness/Harness-v2/ui/`. It does **not** implement CFO V2. It does **not** invent a second protocol.

This is **not** a from-scratch UI. It is **not** a GrokBot rewrite. The cloned SPA already has a visual language, assets, layout grammar, and working chat primitives. If you throw those away and generate a new shell, you will get generic AI UI. That is a failed session.

The job is: observe the live interface and its code, write down the initial state you are keeping, then cut and rewire so every remaining control is intentional, wired, and proven in a browser.

This prompt is independent of whatever backend pass is in flight. Read the live tree. Do not assume the clone’s Settings, Plugins, Companion, or Engines screens mean anything until you can name the disk file or HTTP route they write.

---

## How to run

1. Open a **new** Cursor Agent chat on this repo. Do not continue an old thread.
2. Paste **Constitution** first.
3. Paste **Session prompt** second.
4. Do not skip Phase 0 or Phase 1. Do not write product UI until the initial-state document exists on disk.
5. Do not mark the session done until the browser pass at the end is green.

Repo: this `hackmit26` worktree. Live Harness: `.harness/Harness-v2/`. Design contract: `GROK-WORKSHOP/harness-init/engineers/lark/HARNESS-V2.md`.

---

## Paste this first — Constitution

```text
You are reviewing and then cutting the Harness v2 Operator shell so it is a desk for THIS runtime, not a reskin of OpenMausBot / OpenGrokBot, and not a new app generated from a blank canvas.

Product
- Named Bots on one Computer. Pi is the per-Bot turn engine. The Operator never has to open the Pi TUI.
- Truth is on disk under <computer>/harness/: roster.json, protocol.jsonl, bots/<botId>/{inbox.jsonl,handles/*.json,transcript.jsonl,memory/}, rooms/<id>/log.jsonl, approvals/, receipts/, intercept.json, extensions.json.
- Operator secrets and spawn live in ~/.harness/config.json (or HARNESS_CONFIG). Keys are write-only on the wire.
- A Client system (later: CFO V2) attaches with extra -e modules, Computer/skills/<name>/SKILL.md, and roster.skills / roster.connectors. Finance types must not enter Harness core or this UI's types.

What this session is
- A complete code review of the existing Operator UI: how every screen, route, store action, asset, and fetch actually works.
- Then a first-principles cut: keep the working React/Vite/Tailwind shell, tokens, type, avatars, icons, chat transcript primitives, and layout grammar that already render. Rebuild information architecture, navigation, settings, inspector, roster, rooms, and empty states around Harness nouns.
- Not a rewrite of GrokBot. Not a greenfield SPA. Not a pixel dump into new components that look like every other AI dashboard.
- Not a phone companion. Not Composio. Not a VPS/fleet console. Not an onboarding reel.

Preserve (non-negotiable)
- Do not delete or regenerate the visual system in order to "start clean."
- Do not replace existing assets (avatars, icons, fonts, tokens, motion) with generated placeholders or stock Lucide-only chrome unless the original file is FOREIGN product branding you must remove.
- Do not rewrite App.tsx / the chat surface from a template. Edit in place.
- If a component already renders and maps (or can map) to a Harness noun, keep its structure and restyle/rewire. Do not invent a sibling.

Hard bans
- Do not restore foundry-subagents / agent-room as the Bot network.
- Do not add finance types, Stripe, invoices, or Kernel RPCs to ui/.
- Do not leave a button, tab, settings row, or modal that 404s, no-ops, or pretends a foreign product exists.
- Do not leave placeholders, "coming soon," fake data, decorative controls, or disabled rows that look important.
- Do not "hide with CSS." Delete the route, the nav item, the locale string, and the fetch.
- Do not invent MCP, Box, TTS, image gen, company SSO, or multi-tenant workspaces "for later."
- Do not treat examples/cfo-floor six slugs as the office. They are a bind stub.
- TypeScript: Google style. Explicit return types. No any. No silent catch that swallows a missing API.

Done means
- The initial-state document is on disk and matches what you actually kept.
- Every remaining control maps to a Harness artifact or a documented Operator config field, and exists because you can name its purpose in one sentence.
- What you tried to create and what you actually shipped are written down. Gaps are closed or explicitly refused — not left as stubs.
- npm test in .harness/Harness-v2 stays green.
- You served the app and clicked the real paths in a browser: roster, DM, room, stop, approval, routine, memory, skills, keys, extra extensions, intercept, protocol inspector, search.
- A stranger can operate a floor without opening Pi.
```

---

## Paste this second — Session prompt

```text
Mission
Do not rewrite the GrokBot UI. Observe it, take it apart, keep the working shell, then cut it to an intentional Harness Operator desk. Nothing on screen may be accidental, decorative, or a placeholder.

Work in phases. You may not skip a phase. You may not start deleting or restyling product screens until Phase 1 is written to disk.

────────────────────────────────
Phase 0 — Observe, decompose, code review
────────────────────────────────
Read first (do not skip)
- .harness/Harness-v2/README.md
- .harness/Harness-v2/src/types.ts (Bot, Handle, Room, Routine, ProtocolEvent, Approval, Receipt)
- .harness/Harness-v2/src/paths.ts (where comms live)
- .harness/Harness-v2/src/server/http.ts, api.ts, omb-compat.ts, desk.ts, operator-config.ts
- .harness/Harness-v2/ui/src/App.tsx, ui/src/state/store.tsx, ui/src/components/SettingsModal.tsx
- GROK-WORKSHOP/harness-init/engineers/lark/HARNESS-V2.md (lane owner = bound Bot; Room Host in-library; protocol on disk)

Then walk the entire UI, not a sample of it:
- ui/src/ (every route, layout, modal, empty state)
- ui/src/components/
- ui/src/state/
- ui/src/assets/ (and any public/ static files: avatars, icons, fonts, CSS tokens)
- how the store talks to /api/* and /v1/*
- what a click does: fetch, local state, disk write, or nothing

For every screen, nav item, settings section, modal, and store action write:
- What the Operator sees
- Which files implement it
- Which HTTP route or disk path it hits (or NONE)
- Verdict: WIRED (route + disk), KEEP-VISUAL (renders, wrong noun, rewire), STUB (ok / empty / decorative), FOREIGN (OpenMausBot-only: MCP, Box, VPS, phone, fleet, company org, TTS, image gen, Composio OAuth marketplace, local VM, backups, people/invite, custom domain, onboarding reel, agent-browser)

This is a code review. Quote real component names and routes. Do not summarize from memory.

────────────────────────────────
Phase 1 — Save the initial state (what we are keeping)
────────────────────────────────
Write .harness/Harness-v2/OPERATOR-UI-INITIAL-STATE.md before any product deletion.

That file must list, as of HEAD when you started:
1. Visual system we keep: tokens, type, density, avatars, icons, transcript chrome, sidebar grammar. Name the files.
2. Working surfaces we keep and rewire (chat, composer, roster list, etc.). Name the components.
3. Assets we keep. Name the files. If you later remove an asset, you must say why it was FOREIGN branding, not "cleanup."
4. Surfaces we will delete (FOREIGN / STUB), each with one reason.
5. Harness nouns that have no surface yet.

Commit or at least save this file. Treat it as the baseline. Later diffs are against this baseline, not against a blank app.

Do not regenerate CSS, do not swap the icon set, do not restyle the chat bubble "while you are here."

────────────────────────────────
Phase 2 — Target (what we are trying to create)
────────────────────────────────
Write .harness/Harness-v2/OPERATOR-UI-TARGET.md. First principles, not clone fidelity.

Every remaining control must have a purpose. If you cannot name the purpose, it does not ship. If you need a control and it does not exist, design it against a Harness noun — then implement it by extending KEEP-VISUAL components, not by inventing a new visual language.

Harness nouns the UI must make first-class (if a noun has no screen, add one; if a screen has no noun, delete it)

1. Roster
   - Bots: slug, name, purpose, instructions, approvalLevel, skills[], connectors[]
   - Create / patch / delete persist roster.json. Deleting a Bot that would empty the roster is refused. Rooms that would drop below 2 members are repaired or refused.
   - Live status from lane.json (offline | idle | running | blocked), pending inbox count, Pi session pid if spawned.

2. Comms (this is the Grok-like data structure — it already exists on disk)
   - protocol.jsonl is the office-wide log (seq, type, from, to, handleId, roomId, text, status).
   - Per Bot: inbox.jsonl, handles/<id>.json (accept ≠ complete), transcript.jsonl.
   - Per Room: rooms/<id>/log.jsonl. Host wakes 2–6 members in roster order.
   - The chat view is a projection of those files. The inspector is protocol + transcript, not a fake RuntimeEvent tee from another product.
   - Search hits land on a real message id / handle id in that projection.

3. Operator controls that today live in the Pi TUI and must live here
   - Provider + model + API keys (Anthropic, OpenAI-compat, xAI, Google). Nested { anthropic: { key } } must persist. Test key must not lie.
   - Spawn policy: eager | lazy | fake. Extra Pi -e paths (HARNESS_EXTRA_EXTENSIONS / harness/extensions.json / Settings).
   - Client skill filter (HARNESS_CLIENT_SKILLS): a Bot only sees roster.skills that exist as Computer/skills/<name>/SKILL.md plus the Harness protocol skill.
   - Intercept map (harness/intercept.json): consequential tools can park on Operator or on a named Verifier Bot. No silent "ask_user" that only the TUI can answer.

4. Skills and connectors (plug-and-play slot for CFO V2 later)
   - Skills: grant/revoke names on the Bot record; read SKILL.md; never pretend GitHub import works unless you implement it.
   - Connectors: roster.connectors[] plus Operator key presence. Not a thousand-card Composio catalog. Connecting "Anthropic" is a key, not an OAuth popup.

5. Approvals, Routines, Memory, Computer
   - Approval cards Allow/Deny write approvals/<id>.json.
   - Routines persist on roster.json (name, bot, cadence, prompt, conversation). Cadence: hourly, daily, weekly, monthly, every N s|m|h. Receipts are runs.
   - Memory is per BotId under memory/. The panel reads and writes those files. No shared memory.
   - Computer panel is the shared cwd (workspace/ + harness/), not a VM screenshot.

Navigation (replace the clone's IA, not the clone's chrome)
- Sidebar: Bots, Rooms, Routines, Protocol (office-wide), Computer, Settings.
- Bot pane: transcript, composer, stop, pending handle, approval card, skills, memory, inspector (protocol + handle files).
- Room pane: members, log, post. No "group goal orchestration" unless it maps to room_post + Host.
- Settings: profile, keys, spawn, extra extensions, intercept, that's it.
- Delete or do not link: Companion, Workspaces, People, Usage/billing, Local VM, Backups, Organization, Plugins marketplace, MCP servers, experimental browser engine, onboarding reel, phone pairing.

Empty states
- Every empty state says what is missing and the one action that creates it (add a Bot, paste a key, write extensions.json).
- No "coming soon." No OpenMausBot copy that names Maus, GrokBot, Composio, or a phone.
- Product language is Harness: Bot, Handle, Room, Computer, Operator, Protocol, Routine, Receipt, Memory, Intercept.
- Unintended layout from the clone (double sidebars, ghost tabs, settings sections that scroll into dead widgets) is a bug. Remove it.

────────────────────────────────
Phase 3 — Cut and rewire (what we actually create)
────────────────────────────────
Implement against OPERATOR-UI-TARGET.md using only the KEEP list from INITIAL-STATE.

Rules
- Prefer deleting ui/src/components/<Foreign> and the store actions that fetch them over wrapping them in "unavailable."
- Keep omb-compat / /api/* only where the surviving UI still speaks that path. New screens may call /v1/* or /api/* that already persist. Do not add a third API dialect.
- If you must add a route, put the disk write in src/ (roster, protocol, operator-config, intercept, client-attach) and test it in tests/*.test.ts.
- extraExtensionArgs / Client skills / intercept stay Client-shaped. The UI edits the files; it does not fork Harness for CFO.
- No placeholder copy. No unused routes. No dead store keys. No settings row without a write.
- After the cut, write .harness/Harness-v2/OPERATOR-UI.md: remaining screens, the disk path each reads/writes, and a short "target vs shipped" table. If shipped ≠ target, fix it in this session or state why the target was wrong.

────────────────────────────────
Proofs (required)
────────────────────────────────
1. npm test in .harness/Harness-v2.
2. npm run serve -- --computer examples/protocol-floor --fake --no-open (or the floor that exists).
3. Browser: open the shell. Confirm the nav has no FOREIGN items. Create or select a Bot. Send a DM. See the Handle in the inspector and a protocol.jsonl line. Open a Room, post, see members. Open Settings, save a nested Anthropic key, reload, see configured=true without the secret echoed. Toggle a skill that exists on disk. Edit extra extensions. Open Protocol and search. Trigger an approval in fake/consequential path if you can; Allow it.
4. grep the running UI source for: composio, mcpServers, companion, fleet, opencodeGo, elevenlabs, VpsConnection, onboarding reel. Remaining hits must be dead code you are deleting in this session or a comment pointing at a deleted screen. Zero remaining clicks.
5. Visual check: the shell still looks like the preserved initial state (same type, tokens, transcript chrome), not a new generated dashboard.

Out of scope
- Migrating CFO V2 onto the floor.
- Redesigning Pi itself.
- Pixel-perfect marketing site.
- Restoring OpenMausBot features "because the clone had them."
- Throwing away the clone's working chrome to "design from zero." First principles apply to information architecture and purpose, not to inventing a new look.

Return
- OPERATOR-UI-INITIAL-STATE.md (Phase 1 baseline).
- OPERATOR-UI-TARGET.md (Phase 2 intent).
- OPERATOR-UI.md (Phase 3: remaining screens, disk paths, target vs shipped).
- The UI source changes (edit in place).
- Tests for any new persist routes.
- The browser proof notes (what you clicked, what broke, what you fixed).
```

---

## Operator note (not part of the paste)

This file is **not** an instruction to the agent that is currently wiring `/api` persistence on the cloned shell. That pass should keep going: make keys, roster, rooms, skills, memory, extras, and protocol inspector actually write the Harness they already have. This prompt is the **next** session, on a clean chat, after that desk is real enough to cut.

The failure mode this prompt exists to prevent: a greenfield restyle that discards avatars, tokens, and chat primitives and ships generic AI-dashboard slop. The next agent must freeze the initial visual and structural state on disk before it deletes or redesigns anything.

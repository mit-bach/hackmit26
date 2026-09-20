# Operator UI — target (Phase 2)

First principles for the desk. Not clone fidelity. Not a new look.

The Operator runs named Bots on one Computer without opening the Pi TUI. Truth is files under `<computer>/harness/` plus `~/.harness/config.json`. Every remaining control exists because it reads or writes one of those artifacts, and that purpose can be said in one sentence.

If a KEEP-VISUAL component already maps to a noun, extend it. Do not invent a sibling visual language. If a screen has no noun, delete it. If a noun has no screen, add one by rewiring a kept surface.

---

## Purpose of the product

Named Bots. One Computer. Pi is the per-Bot turn engine. The Host is in-library, not a Chief of Staff Bot. Protocol is on disk. A Client system (later: CFO V2) attaches with extra `-e` modules, `Computer/skills/<name>/SKILL.md`, and grants on the Roster. Finance types do not enter this UI.

---

## Navigation

Sidebar, same chrome as `Sidebar.tsx`:

1. **Bots** — roster list (live status, pending inbox). Select → Bot pane.
2. **Rooms** — roster rooms in the same list (they already are `groups`). Select → Room pane.
3. **Routines** — `showRoutines` → existing `RoutinesPage` / calendar.
4. **Protocol** — replaces Team map. Office-wide `protocol.jsonl` + search.
5. **Computer** — shared cwd file tree (`/api/computer/tree`), not a VM screenshot.
6. **Settings** — profile, keys, spawn, extra extensions, intercept, skins.

Delete or do not link: Companion, Workspaces, People, Usage/billing, Local VM, Backups, Organization, Plugins marketplace, MCP, experimental browser, onboarding reel, phone pairing, Team map, Connected apps.

`activeView`: `"chat" | "routines" | "protocol" | "computer"`.

---

## First-class nouns

### 1. Roster

**Purpose:** Create, patch, and delete standing Bots. The floor is `roster.json`.

- Fields: slug, name, purpose, instructions, approvalLevel, skills[], connectors[].
- Create / patch / delete persist `roster.json`. Deleting the last Bot is refused. Rooms that would drop below 2 members are repaired or refused (already in `deleteBot` in `desk.ts`).
- Live status from `lane.json`: offline | idle | running | blocked. Pending inbox count. Pi pid if spawned.
- Surface: sidebar rows + `NewBotDialog` (blank Bot: name, slug, purpose — no Gmail/GitHub role catalog) + Bot settings identity.

### 2. Comms (the chat is a projection)

**Purpose:** See and send work the protocol already stores on disk.

- Office log: `protocol.jsonl` (seq, type, from, to, handleId, roomId, text, status).
- Per Bot: `inbox.jsonl`, `handles/<id>.json` (accept ≠ complete), `transcript.jsonl`.
- Per Room: `rooms/<id>/log.jsonl`. Host wakes 2–6 members in roster order.
- Bot pane: transcript (`ChatView`), composer, Stop, pending Handle chip, approval card.
- Room pane: members, log, post. No “group goal orchestration.”
- Inspector: protocol + Handle files + transcript for the open Bot or Room. Not a fake RuntimeEvent tee.
- Search hits land on a real message id / handle id in that projection (`GET /api/search`).

### 3. Operator controls that used to live in the Pi TUI

**Purpose:** Run the floor from this desk.

| Control | Purpose | Disk |
| --- | --- | --- |
| Provider + model | Which Pi backend to spawn | `~/.harness/config.json` |
| API keys (Anthropic, OpenAI-compat, xAI, Google) | Nested `{ anthropic: { key } }`. Test key must not lie. Secret never echoed | same, mode 0600 |
| Spawn policy eager \| lazy \| fake | When a Bot process exists | same |
| Extra Pi `-e` paths | Client attach modules | config + `harness/extensions.json` |
| Client skill filter | Bot only sees roster.skills that exist as `Computer/skills/<name>/SKILL.md` plus the Harness protocol skill | config `clientSkills` / env |
| Intercept map | Consequential tools park on Operator or a named Verifier Bot | `harness/intercept.json` |

Settings sections: **Profile**, **Keys**, **Spawn & attach** (today’s Harness desk), **Intercept** (can stay on the same card), **Appearance** (skins — Operator chooses the desk look; this is the preserved visual system, not a foreign product).

### 4. Skills and connectors

**Purpose:** Grant what a Bot may load. Slot for a Client system later.

- Skills: grant/revoke names on the Bot record; read `SKILL.md`. No GitHub import button.
- Connectors: `roster.connectors[]` plus Operator key presence (Anthropic is a key, not OAuth). Not a Composio catalog.

### 5. Approvals, Routines, Memory, Computer

| Noun | Purpose | Disk | Surface |
| --- | --- | --- | --- |
| Approval | Operator Allow/Deny of a parked consequential tool | `approvals/<id>.json` | card on the Bot transcript |
| Routine | Standing prompt on one Bot’s lane | `roster.json` routines; runs → `receipts/` | Routines page |
| Memory | Per-Bot notes, not the Computer | `harness/bots/<botId>/memory/` | Memory section, read/write those files. No shared brain. No fake journal if there is no journal file |
| Computer | Shared cwd | `workspace/` + `harness/` | Computer dock/page via tree+file API |

Cadence: hourly, daily, weekly, monthly, every N s\|m\|h.

---

## Bot pane (keep `ChatView` / `Composer`)

Visible because each earns its keep:

- Transcript (projection of `transcript.jsonl` + pending approval cards)
- Composer (writes `user_dm`)
- Stop (writes `user_stop`)
- Pending Handle / busy (lane)
- Approval Allow/Deny
- Header: open Bot settings, Computer dock, Inspector
- Find-in-chat (search within the projection)
- Export transcript (reads the same messages)

Not on this pane: calls, TTS, usage chip, task threads, Chief of Staff, model CLI picker, PlaceChip/VM.

### Bot settings (keep `BotSettingsDialog` rail, fewer rows)

| Section | Purpose |
| --- | --- |
| Overview | slug, live status, purpose, pending |
| Identity | name, slug, purpose, instructions, avatar color/body, approvalLevel |
| Skills | grant/revoke + read SKILL.md |
| Memory | read/write this Bot’s memory files |
| Routines | routines owned by this Bot |
| Permissions | approvalLevel only (`ask` / `always` / `never`) |

### Room pane (keep `GroupView`)

Members (2–6), log, post, rename, delete Room (roster). Composer is `room_post`, not goal orchestration.

---

## Empty states

Every empty state names what is missing and the one action that creates it.

| Missing | Copy / action |
| --- | --- |
| No Bots | Add a Bot (opens New Bot). Roster must keep ≥1 after delete |
| No Rooms | Create a Room with 2–6 Bots |
| No Routines | Add a Routine on a Bot |
| No protocol lines | Send a DM or post to a Room |
| No API key | Paste a key in Settings → Keys |
| No extra extensions | Write a path in Settings or `harness/extensions.json` |
| No skills on disk | Add `Computer/skills/<name>/SKILL.md`, then grant it |
| Computer tree empty | Files appear under this Computer’s cwd |
| Memory empty | Write MEMORY.md for this Bot |

No “coming soon.” No OpenMausBot / Maus / GrokBot / Composio / phone copy.

---

## Implementation rules

- Edit `App.tsx` in place. Do not rewrite the chat surface from a template.
- Prefer deleting `ui/src/components/<Foreign>` and the store fetches over wrapping “unavailable.”
- Keep omb-compat / `/api/*` only where the surviving UI still speaks that path.
- New persist goes in `src/` and `tests/*.test.ts`.
- TypeScript: Google style, explicit returns, no `any`, no silent catch that swallows a missing API.
- Product language: Bot, Handle, Room, Computer, Operator, Protocol, Routine, Receipt, Memory, Intercept.

---

## Out of scope (refuse, do not stub)

Migrating CFO V2. Redesigning Pi. Pixel-perfect marketing. Restoring OpenMausBot features. Inventing MCP, Box, TTS, image gen, SSO, multi-tenant workspaces “for later.” Treating `examples/cfo-floor` six slugs as the office (`examples/protocol-floor` is the demo Computer).

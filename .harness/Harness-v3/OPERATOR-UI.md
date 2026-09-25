# Operator UI — remaining desk (Phase 3)

What ships after the cut. Every remaining control maps to a Harness artifact or an Operator config field. Visual system is the Phase 1 keep list (`OPERATOR-UI-INITIAL-STATE.md`): tokens, type, avatars, transcript chrome, sidebar grammar. Information architecture is `OPERATOR-UI-TARGET.md`.

Entry: `ui/src/main.tsx` → `App`. Loopback `GET /api/auth/session` authenticates. HTTP from the SPA is `/api/*`; SSE is `GET /api/events`. Headless `/v1/*` still exists for a terminal Operator. The floor can be run with no SPA: `harness serve --computer DIR --fake`, `harness send <slug> …`, `harness protocol`, `harness roster`.

---

## Remaining screens

| Surface | What the Operator sees | Components | Reads / writes |
| --- | --- | --- | --- |
| Shell | Sidebar + main column + docks | `App.tsx` `Shell` | SSE hello snapshot |
| Bots (roster) | Named Bots with live status | `Sidebar.tsx` `BotListItem` | `GET /api/bots` ← `harness/roster.json` + `lane.json` |
| New Bot | Name, slug, purpose, instructions | `NewBotDialog.tsx` | `POST /api/bots` → `roster.json` + `harness/bots/<id>/` |
| Bot DM | Your 1:1 with that Bot | `ChatView.tsx`, `Composer.tsx` | `POST /api/bots/:id/messages` → `user_dm` |
| Bot threads | Read-only Bot↔Bot handoff log | `GroupView.tsx` (no composer) | `pair:<id>:<id>` projected from `protocol.jsonl`; POST messages 403 |
| Rooms | Members, log, post | `GroupView.tsx`, `ManageMembersPanel.tsx` | `POST /api/groups` → `roster.rooms` (2–6 members); `POST /api/groups/:id/messages` → `room_post` + `rooms/<id>/log.jsonl` |
| Approval | Allow / Deny on a parked tool | `ApprovalCard.tsx` | `POST /api/threads/:id/respond` → `harness/approvals/<id>.json` |
| Inspector | Protocol / Handles / Transcript | `InspectorPanel.tsx` | `GET /api/threads/:id/events` ← `protocol.jsonl` + Handle files + `transcript.jsonl` |
| Routines | Calendar / list / logs | `RoutinesPage.tsx` (`RoutineCalendarPage.tsx`) | `GET/POST/PATCH/DELETE /api/routines` → `roster.routines`; runs ← `receipts/` |
| Protocol | Office-wide log + search | `ProtocolPage.tsx` | `GET /api/protocol?query=` ← `protocol.jsonl` |
| Demo | Replay protocol from wipe; director camera (cast, seq in/out, scenes) | `DemoPage.tsx` | `GET /api/demo` ← protocol + transcripts; `POST /api/demo/record`; `GET/PUT /api/demo/scenes`; `GET /api/demo/frame` |
| Search | Jump to a message / Handle | `CommandPalette.tsx`, `SearchResults.tsx`, `ChatFindBar.tsx` | `GET /api/search?q=` |
| Computer | Shared cwd tree + file edit | `ComputerPanel.tsx` | `GET /api/computer/tree`, `GET/PUT /api/computer/file` ← `workspace/` + `harness/` |
| Bot settings | Overview, identity, skills, memory, routines, approvals | `BotSettingsDialog.tsx` + `bot-settings/*` | PATCH bot → `roster.json`; skills → `Computer/skills/<name>/SKILL.md`; memory → `harness/bots/<id>/memory/` |
| Settings | Operator, Harness desk, Keys, Appearance | `SettingsModal.tsx`, `HarnessDeskSettings.tsx`, `ApiKeys.tsx`, `SkinPicker.tsx` | `PUT /api/config` → `~/.harness/config.json`; `PUT /api/intercept` → `harness/intercept.json`; extra `-e` → config + `harness/extensions.json` |
| Shortcuts | Cheat sheet | `KeyboardShortcutsModal.tsx` | NONE (local) |
| About | Product name + version | `AboutDialog.tsx` | NONE |

Empty states name the missing artifact and the one action that creates it (Add a Bot, paste a key, write `Computer/skills/<name>/SKILL.md`).

Plus menu: New Bot, New Room (2–6 members), Archived if any. Tools: Demo, Protocol, Routines, Computer. You: Settings, Keyboard shortcuts, About.

---

## Disk map (as if there were no UI)

Same files a terminal Operator would touch:

```
<computer>/harness/
  roster.json                 Bots, rooms, routines
  protocol.jsonl              Office log
  demo/latest/                Optional recorded replay (survives wipe)
  intercept.json              Operator vs Verifier Bot
  extensions.json             Extra Pi -e paths
  bots/<botId>/
    inbox.jsonl
    handles/<id>.json         accept ≠ complete
    transcript.jsonl
    memory/                   Per-Bot only
    lane.json                 offline | idle | running | blocked
  rooms/<id>/log.jsonl
  approvals/<id>.json
  receipts/
<computer>/workspace/         Shared cwd
<computer>/skills/<name>/SKILL.md
~/.harness/config.json        Keys (nested { anthropic: { key } }), spawn, provider, model, extraExtensions, clientSkills
```

---

## Target vs shipped

| Target | Shipped | Note |
| --- | --- | --- |
| Nav: Bots, Rooms, Routines, Protocol, Computer, Demo, Settings | Yes | Sidebar footer + plus menu. Rooms live in the same list as Bots. Demo is full-stage replay of protocol.jsonl. |
| Roster create/patch/delete on `roster.json` | Yes | Last Bot delete refused in `desk.ts`. Room membership 2–6. UI New Room refuses 1 and >6 before POST. |
| Chat is a projection of protocol / transcript / handles | Yes | Inspector lenses labeled Protocol / Handles / Transcript. |
| Stop, pending Handle, approval Allow/Deny | Yes | Approval wire includes `card.tool`. Pump fingerprints `id:status` so Allow hydrates. |
| Provider + nested keys; Test must not lie | Yes | Test never persists and never calls the provider. `serializeOperatorConfig` writes nested `{ anthropic: { key } }`. |
| Spawn eager \| lazy \| fake; extra `-e`; client skill filter; intercept | Yes | Settings → Harness. `--fake` reports spawnPolicy fake even if disk still says eager. extra `-e` writes `harness/extensions.json`. |
| Skills grant/revoke + read SKILL.md; no GitHub import | Yes | `SkillsSection.tsx`. |
| Connectors = roster names + key presence, not Composio | Yes | Four provider cards from Operator config. No OAuth marketplace. |
| Routines on roster; cadence hourly/daily/weekly/monthly/every N | Yes | Desk GET maps receipts as runs. POST `/run` publishes `routine.run`. Room-goal / call / webhook not offered (`routinesOnly`). |
| Memory per BotId under `memory/` | Yes | Panel reads and writes those files. No Obsidian / folder-open 404. |
| Computer = shared cwd, not a VM | Yes | `ComputerPanel` uses `/api/computer/tree`. Per-Bot `/computer` 404s. |
| No Companion, Workspaces, People, Usage, Local VM, Backups, Org, Plugins, MCP, browser engine, onboarding reel, phone | Yes | Routes and settings sections deleted. Move-to-section / Work-Personal folder picker deleted this pass (it POSTed `/api/sidebar-sections`, which does not exist). |
| Empty states, Harness language | Yes | Live plus/room/routines/attention copy uses Bot, Room, Routine, Handle, Receipt. Locale JSON still holds unused strings for deleted screens (not linked). |
| Visual system preserved | Yes | Same `styles.css` tokens, Inter, mascot avatars, bubble chrome. Brand title is Harness. |

### Refused (target was wrong, or out of scope)

- Per-Bot CLI model picker in the chat header — model lives in Settings (Operator config), not on the Bot record.
- Composio / MCP / Box / VPS / TTS / image gen / SSO — deleted, not stubbed.
- `examples/cfo-floor` as the office — demo Computer is `examples/protocol-floor`.
- Rewriting `App.tsx` from a template — edited in place.
- Live Pi Stop / live Pi approval under `--fake` — fake workers complete instantly. Approval was proved with a seeded `approvals/<id>.json` Allow write.
- Flattening leftover sidebar *section folders* (Bots vs computer-named group) into two explicit Bots / Rooms lists — KEEP-VISUAL list grammar still groups by leftover `section` strings when present. No Work/Personal picker remains.

### Dead code that is not a click

`store.tsx` still types `composio` / `fleet` / `mcpServers` / `opencodeGo` / `elevenlabs` / `onboarding` as deleted-screen fields so the hello snapshot does not explode. `ProviderIcons` still knows `opencodeGo` for leftover instance ids. Locale packs still contain unused Companion / Composio / onboarding reel strings. Vite does not bundle unreferenced screens.

---

## Browser proof (this session)

Served: `node dist/src/cli.js serve --computer examples/protocol-floor --fake --no-open --port 8797` (Computer = `examples/protocol-floor`). Title: **Harness**.

| Path | What I clicked | Disk / API | Result |
| --- | --- | --- | --- |
| Nav | Tools, You | NONE | Tools = Protocol, Routines, Computer. You = Settings, Keyboard shortcuts, About. No Companion / People / Workspaces / MCP / fleet. |
| Roster | Alpha, Beta, Gamma, Floor | `GET /api/bots` | Three Bots + Floor. No New thread. No bulletin. |
| Approval | Allow on seeded `ap_operator_ui_proof` | `harness/approvals/ap_operator_ui_proof.json` | status `allowed`. Length-only pump missed the card drop; `id:status` fingerprint is the fix (needs rebuilt `dist` for live SSE). |
| DM | Composer “operator-ui-proof DM after Allow” | `protocol.jsonl` seq 22–25, `handles/h_4feee2c4-…` | Handle in Inspector; protocol lines on disk. |
| Inspector | Protocol / Handles / Transcript | those files | User input 11:04 PM visible. |
| Computer | Tools → Computer | `GET /api/computer/tree?from=.` | Tree includes `harness/`, `roster.json`, `protocol.jsonl`, receipts, `skills/briefing/SKILL.md`, per-bot handles/transcript/memory. First paint used to look empty; `treeLoading` + array parse fixed that. |
| Protocol + search | query `operator-ui-proof` | `GET /api/protocol?query=` | 3 hits (seqs 22, 24, 25). Click seq 25 landed on Alpha DM. |
| Room | Floor; post “operator-ui-proof room post”; members panel | `rooms/floor/log.jsonl`, `protocol.jsonl` seq 26–38 | Members 3 (Alpha/Beta/Gamma checked). Composer Message Floor. Host woke members in roster order (`send.accepted` alpha, then beta, then gamma). Replies land in Bot DMs, not the room log. Plus → New Room requires 2–6 Bots; no Work/Personal field. |
| Settings Harness | spawn, extra `-e`, clientSkills, intercept JSON, Save | `~/.harness/config.json`, `harness/extensions.json`, `harness/intercept.json` | spawnPolicy **fake** with `--fake`. extraExtensions `["./extensions/index.ts"]`. Nested Anthropic `configured=true`, secret not echoed. Overlay intercepted the Save click; DOM click + PUT succeeded. |
| Keys Test | Test on draft / stored | `POST /api/keys/test` | Does not save. Does not claim a live provider call. |
| Skills | Revoke then Grant `briefing` | `roster.json` `bots[].skills` | Switch disabled while PATCH in flight, then `Grant briefing` / `Revoke briefing`. `Computer/skills/briefing/SKILL.md` exists. |
| Memory | Edit MEMORY.md, Save | `harness/bots/bot_alpha/memory/MEMORY.md` | Wrote `operator-ui-proof memory write`. Copy names `harness/bots/<id>/memory/`. No Obsidian button. |
| Routines | Tools → Routines → Run logs | `roster.routines`, `receipts/` | `morning-brief` on calendar. Run log **Open morning-brief run: Completed** (not Queued). New menu is Routine, not webhook/call. |
| Search | sidebar Search | `GET /api/search` | Hits land on the Alpha DM projection. |

### What broke, what was fixed

1. Nested key persist wrote `apiKeys` blob — `serializeOperatorConfig` now writes `{ anthropic: { key } }`.
2. extra `-e` stayed in Operator config only — `applyConfigPatch` / attach also write `harness/extensions.json`.
3. Routine runs showed Queued — omb GET `/api/routines` stub deleted; POST `/run` publishes `wireRun`; pump emits `routine.run` on receipt status change.
4. GET spawn eager despite `--fake` — `configStatus` honors `ctx.fakeWorkers`.
5. New thread POSTed `/tasks` 200 — POST 400; `useShowThreads()` forced false.
6. Computer empty first paint — loading copy vs empty copy; parse raw array.
7. Protocol empty first paint — loading copy vs empty copy.
8. Approval Allow did not SSE-refetch — pump compared count, now `id:status`.
9. New Room allowed 1 Bot and a Work/Personal team field — UI requires 2–6; team field deleted; desk already 400s a 1-member Room.
10. Move to section POSTed `/api/sidebar-sections` (no such route) — picker and menu items deleted.
11. Memory “open folder” 404 — buttons deleted.
12. GroupView leftover `roomNeedsSetup` / extra `</button>` — compile errors from the prior cut, already removed.

### Visual check

Screenshot of Alpha DM: same Inter, same tokens, same left/right bubble chrome, same mascot avatars, title Harness. Not a generated dashboard.

### Gaps still honest

- Stop is not clickable under `--fake` (no live Pi turn). Interrupt route exists.
- Live Pi consequential approval was not produced; seeded file + Allow was.
- Sidebar can still show a computer-named folder grouping leftover `section` strings. There is no control to invent Work/Personal teams.
- `POST /tasks/:id` PATCH overlay remains 200 for pin/model (`tests/api.test.ts`). `POST /tasks` is 400.

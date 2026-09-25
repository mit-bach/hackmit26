# Operator UI — initial state (Phase 1 baseline)

This is the keep/cut inventory **before** Phase 3 deletion. Later diffs are against this file, not against a blank app.

Observed: 2026-09-19, `.harness/Harness-v2/ui/` plus the HTTP host in `src/server/`. Routing is not React Router. `AppState.activeView` is `"chat" | "team-map" | "routines"`. HTTP from the SPA is **`/api/*` only**; SSE is `GET /api/events`. Headless `/v1/*` exists on the host and is unused by the SPA.

Entry: `ui/src/main.tsx` → `chooseRoot()` → `/pair` → `PairPage`, else `readSessionState()` → `App`. Loopback `GET /api/auth/session` already returns `{ kind: "loopback" }`, so a local Operator never needs Pair.

Working tree already contains a **partial Harness desk pass** (not yet the cut): `src/server/desk.ts`, `src/intercept.ts`, `src/client-attach.ts`, `ui/src/components/HarnessDeskSettings.tsx`, `tests/desk.test.ts`, and edits in `SettingsModal.tsx` / `store.tsx` / `locales/en.json`. That pass is **backend for KEEP-VISUAL rewiring**. It is not a new visual language. This baseline still treats the clone’s screens as they render.

Verdict key:

- **WIRED** — click hits an `/api` (or `/v1`) route that reads or writes a disk file this runtime owns.
- **KEEP-VISUAL** — the chrome renders and can map to a Harness noun; the noun or path is wrong today.
- **STUB** — empty, decorative, or catch-all `{ ok: true }` with no disk write.
- **FOREIGN** — OpenMausBot-only product: MCP, Box, VPS, phone, fleet, company org, TTS, image gen, Composio OAuth marketplace, local VM, backups, people/invite, custom domain, onboarding reel, agent-browser.

---

## 1. Visual system we keep

Do not regenerate CSS. Do not swap the icon set. Do not restyle chat bubbles “while here.”

| Piece | Files |
| --- | --- |
| Tokens, skins, density, motion | `ui/src/styles.css` (`@theme`, `[data-skin=midnight\|atelier\|foundry\|lagoon\|graphite\|linen\|dusk\|daylight]`, `--color-app/panel/raised/composer/card/ink/accent/bubble-user/success/danger`, `--animate-msg-in/panel-in/caret/status-pulse`) |
| Skin switcher (logic only) | `ui/src/lib/skins.ts` |
| Type | Inter via `--font-sans` in `styles.css`; 13–15px body; 11.5px uppercase section labels |
| Chat transcript chrome | `ChatView.tsx` (`Bubble`, `DaySeparator`, `ActivityChip`, `PinnedBanner`), `ChatMarkdown.tsx`, `ReplyQuote.tsx`, `WorkingIndicator.tsx`, `TurnPresence.tsx`, `TurnNarrationRun.tsx`, `ToolActivity.tsx`, `DigestChip.tsx` |
| Composer grammar | `Composer.tsx`, `MentionTextarea.tsx`, `MentionText.tsx`, `ComposerAttachments.tsx`, `ComposerQueuedMessages.tsx`, `ComposerTray.tsx` |
| Sidebar grammar | `Sidebar.tsx` (rail, search, section headers, bot/room rows, footer), `SidebarThreadRow.tsx`, `SidebarSectionHeader.tsx`, `SidebarBotActivity.tsx`, `SidebarAttentionPanel.tsx`, `SidebarMoreMenu.tsx`, `SidebarPopoverMenu.tsx`, `SidebarProfileMenu.tsx` |
| Modal / card grammar | `SettingsModal.tsx` shell, `SettingsPrimitives.tsx` (`Card`, `Switch`), `ConfirmDialog.tsx`, `BotSettingsDialog.tsx` (accordion rail) |
| Right-dock panel chrome | `InspectorPanel.tsx` (header, lenses, width), `ComputerPanel.tsx` (header, close, `PANEL_WIDTH_KEY` resize) — **keep the dock**, not the Box/VPS body |
| Avatars / motion | `Avatar.tsx`, `CursorAvatar.tsx`, `cursor-face-data.ts`, `lib/mascot.ts`, `shared/mascot-bodies.ts`, `shared/bot-avatar.ts` |
| Provider marks used as type | `ProviderIcons.tsx` (Anthropic / OpenAI / xAI marks for key rows) |
| Layout | `App.tsx` `Shell`: sidebar + main column + sibling docks; mobile drawer |
| Tailwind + Vite | `ui/` package as-is |

**FOREIGN branding we may retitle, not redraw:** `ui/index.html` title `OpenMausBot`; `ui/src/lib/brand.ts` `DEFAULT_BRAND.name`; `GET /api/brand` in `omb-compat.ts` returns `{ brand: { name: "OpenMausBot" } }`; `ui/public/app-icon.svg` title/desc say OpenMausBot / SupaMaus. The **geometry of the cursor mascot is the visual system** (same body as `CursorAvatar`). Do not replace it with a Lucide spark. Change copy only.

---

## 2. Working surfaces we keep and rewire

| Surface | Components | Today’s HTTP | Harness noun |
| --- | --- | --- | --- |
| Bot DM | `ChatView.tsx`, `Composer.tsx` | `POST /api/bots/:id/messages`, `POST …/interrupt` | `user_dm` / `user_stop` → inbox + Handle + `transcript.jsonl` |
| Room | `GroupView.tsx`, `ManageMembersPanel.tsx` | `POST /api/groups/:id/messages`, `POST /api/groups`, PATCH/DELETE via desk | Room log + Host `room_post` |
| Roster list | `Sidebar.tsx` `BotListItem` / `GroupListItem` | `GET /api/bots` (omb wire) | `roster.json` bots + rooms |
| New Bot | `NewBotDialog.tsx` | `POST /api/bots` | create `BotRecord` (drop role-app hints) |
| Stop | Chat header + Composer square | `POST /api/bots/:id/interrupt` | `user_stop` |
| Approval card | `QuestionCard.tsx`, `OptionCard.tsx`, `PendingApproval.tsx`, `ApprovalCard.tsx` | `POST /api/threads/:id/respond` | `approvals/<id>.json` Allow/Deny |
| Inspector | `InspectorPanel.tsx`, `RunLog.tsx` | `GET /api/threads/:id/events` (desk `inspectorPage`) | protocol.jsonl + transcript.jsonl + Handle files |
| Search | `CommandPalette.tsx`, `SearchResults.tsx`, `ChatFindBar.tsx` | `GET /api/search?q=` | protocol + roster hits → message/handle id |
| Routines | `RoutinesPage.tsx`, `RoutineCalendarPage.tsx`, `routines/*`, `RoutineRunCard.tsx` | `GET/POST/PATCH/DELETE /api/routines`, `POST …/run` | `roster.routines` + `receipts/` |
| Skills | `bot-settings/SkillsSection.tsx` | `GET/PATCH /api/bots/:id/skills[/:name]` | `roster.skills[]` + `Computer/skills/<name>/SKILL.md` |
| Memory | `bot-settings/MemorySection.tsx`, `lib/memory.ts` | `GET/PUT /api/bots/:id/memory[/file]` | `harness/bots/<botId>/memory/` |
| Identity / instructions | `IdentitySection.tsx`, `OverviewSection.tsx`, `SoulField.tsx` (as instructions editor) | `PATCH /api/bots/:id` | `BotRecord` name/purpose/instructions/approvalLevel |
| Settings shell | `SettingsModal.tsx` | `PUT /api/config` | `~/.harness/config.json` |
| Harness desk | `HarnessDeskSettings.tsx` | `/api/comms`, `/api/intercept`, `/api/config` | spawn, extra `-e`, intercept, comms paths |
| Keys | `ApiKeys.tsx` `ApiKeyRow` | `PUT /api/config`, `POST /api/keys/test` | nested `{ anthropic: { key } }` write-only |
| Computer dock | `ComputerPanel.tsx` **chrome only** | today Box/VPS **FOREIGN**; rewire to `/api/computer/tree` + `/api/computer/file` | shared cwd `workspace/` + `harness/` |
| Shortcuts cheat sheet | `KeyboardShortcutsModal.tsx` | NONE | KEEP-VISUAL, trim FOREIGN keys |
| Confirm | `ConfirmDialog.tsx` | local | delete-Bot confirm |

---

## 3. Assets we keep

| Asset | Path | Note |
| --- | --- | --- |
| Cursor / mascot body + face | `CursorAvatar.tsx`, `cursor-face-data.ts`, `shared/mascot-bodies.ts` | Product chrome, not OpenMausBot wordmark |
| App tile SVG | `ui/public/app-icon.svg` | Same mascot. Retitle away from OpenMausBot; do not redraw |
| Skins | `styles.css` `[data-skin]` blocks | Eight skins |
| Mascot preview CSS | `ui/src/mascot-preview.css` | Dev preview |
| Locales (en as source) | `ui/src/locales/en.json` | Cut FOREIGN strings in Phase 3; keep structure |

If an asset is removed later, the reason must be **FOREIGN branding**, not “cleanup.”

---

## 4. Surfaces we will delete (FOREIGN / STUB)

Each row: one reason.

### App shell / routes

| What the Operator sees | Files | HTTP | Verdict | Reason |
| --- | --- | --- | --- | --- |
| Pair / sign-in / invite | `main.tsx` `/pair`, `pair/PairPage.tsx` | `/api/auth/pair`, email invite | FOREIGN | Phone/device pairing. Loopback session already authenticates |
| Welcome reel | `WelcomeFlow.tsx`, `onboarding/reel/**`, beats (`PhoneBeat`, `EnginesBeat`, …) | `/api/config` onboarding | FOREIGN | Onboarding reel + phone |
| Guided / first-conversation tours | `GuidedTour.tsx`, `FirstConversationTour.tsx` | config hints | FOREIGN | Clone onboarding |
| Workspace backup recovery gate | `WorkspaceBackupSettings.tsx` `WorkspaceBackupRecovery` wraps `App` | `/api/workspace-backup/*` | FOREIGN | Backups |
| Team map | `TeamMapPage.tsx`, `TeamCanvas.tsx`, `TeamLibraryPanel.tsx`, `CanvasComputers.tsx` | `/api/team-map`, Box/VM buttons | FOREIGN | Org canvas + Box computer, not Protocol |
| Local VM overlay | `LocalVmWorkspace.tsx` | `/api/bots/:id/local-computer` | FOREIGN | Local VM |
| No-engines wall | `NoEngines.tsx`, `EngineSetup.tsx`, `EngineLibrary.tsx` | `GET /api/instances` CLI engines | FOREIGN | Pi is the engine; this is OpenMausBot CLI install |
| Plugins marketplace | `PluginsPanel.tsx`, `McpServersPanel.tsx`, `ConnectorCard.tsx` (Composio) | `/api/connectors/*` OAuth, `/api/mcp/servers*` | FOREIGN | Composio + MCP |
| Remote desktop | `remote-desktop-panel.tsx` | computer screenshot | FOREIGN | Box/VPS viewer |
| Remote agent settings | `RemoteAgentSettingsPanel.tsx` | remote client | FOREIGN | Multi-tenant remote shell |
| Update banner (desktop updater) | `UpdateBanner.tsx` | `window.ogb.updater` | STUB/FOREIGN | No Harness updater |

### Sidebar footer

| Control | Files | HTTP | Verdict | Reason |
| --- | --- | --- | --- | --- |
| Team map | `Sidebar.tsx` `showTeamMap` | NONE (view switch) | FOREIGN | See Team map |
| Connected apps | `togglePlugins` | PluginsPanel | FOREIGN | Composio |
| Phone | `SidebarPhoneButton.tsx`, `phoneSettingsAction()` | companion settings | FOREIGN | Phone companion |

### Settings modal sections (`SECTIONS` in `SettingsModal.tsx`)

| id | Operator sees | Files | HTTP | Verdict | Reason |
| --- | --- | --- | --- | --- | --- |
| `desktopWorkspaces` | Connected desktop workspaces | `ConnectedWorkspacesSettings.tsx` | `window.ogb.environments` | FOREIGN | VPS/host pairing |
| `organization` | Company enroll | `OrganizationSettings.tsx`, `OrganizationIdentity.tsx` | `ogb.organization` | FOREIGN | Company SSO/org |
| `experimental` | Skill authoring + built-in browser | `BrowserProfilesManager.tsx` | `/api/config` browser | FOREIGN | Agent-browser |
| `engines` | CLI engines | `EnginesSettings.tsx` | `/api/instances` | FOREIGN | Not Pi provider/model |
| `companion` | Remote access, custom domain, pairing, phone | `CompanionSection.tsx`, `CustomDomainSettings.tsx`, `ServerPairingCard.tsx`, `RemoteComputerSection.tsx`, `PhoneSetupFlow.tsx` | pairing APIs | FOREIGN | Phone, custom domain |
| `computer` | Local VM / Box / VPS inventory | `LocalComputerSection.tsx` | `/api/computers/boxes*`, `/api/computers/vps*` | FOREIGN | VM/Box/VPS |
| `usage` | Tokens / billing | `UsageSection.tsx`, `UsageBudget.tsx`, `UsageHistory.tsx` | usage APIs | FOREIGN | Billing (not receipts) |
| `people` | Invite members | `PeopleSection.tsx` | `/api/auth/sessions` | FOREIGN | People/invite |
| `backups` | Workspace + company backup | `WorkspaceBackupSettings.tsx`, `CompanyBackupSettings.tsx` | backup APIs | FOREIGN | Backups |
| `workspaces` | Fleet tenants | `WorkspacesSection.tsx` | `/api/fleet*` | FOREIGN | Fleet |
| connections: Box, VPS, OpenCode Go, Composio | `ApiKeys.tsx` `VpsConnection`, sections `box` `composio` `opencodeGo` | `/api/config` | FOREIGN | Not Anthropic/OpenAI/xAI/Google keys |

Keep from Settings: **profile** (general, stripped), **keys** (providers only), **harness** (spawn, extras, intercept), **appearance/skins** (visual system — Operator chooses desk look). Drop analytics, replay tour, room-turn OpenMausBot timeout, thread concurrency, diagnostics export, experimental flags.

### Bot settings sections (`BOT_SECTIONS`)

| id | Reason |
| --- | --- |
| `access` | `AccessSection.tsx`: VPS, MCP, Composio apps, agent-browser, webhooks — FOREIGN |
| `voice` | `VoiceSection.tsx`, `VoiceSettings.tsx`, `lib/tts/*`, `SpeakButton.tsx` — TTS FOREIGN |
| `usage` | `bot-settings/UsageSection.tsx` — billing |
| `history` | OpenMausBot soul/history rollback, not protocol |
| `model` | Per-bot CLI engine picker; Operator model lives in Settings |
| GitHub skill import row | `SkillsSection.tsx` import from URL — host already 400s HTTP; do not pretend it works |
| `AvatarImageGenerator` | image gen FOREIGN; keep `BotProfileAvatarCard` color/body picker |

Keep: overview, identity (name/slug/purpose/instructions/avatar color), skills, memory, routines, permissions **as approvalLevel only**.

### Chat chrome to strip (leave the bubble)

| Control | Files | Reason |
| --- | --- | --- |
| Chief of Staff chip | `ChatView.tsx`, sidebar `makeChief` | Not a Harness noun; Host is in-library |
| `TaskPicker` | `TaskPicker.tsx` | OpenMausBot threads/tasks overlay (in-memory `taskOverlays`) |
| `UsageChip` | `ChatView.tsx` | Billing |
| `ModelPicker` in header | `ModelPicker.tsx` | Engine CLI; model is Settings |
| `CallButton` / `CallView` / `GroupCallView` | `CallView.tsx`, `GroupCallView.tsx`, `lib/call.ts` | Phone/voice call |
| `SpeakButton` on bubbles | `SpeakButton.tsx` | TTS |
| Goal mode in composer | `Composer.tsx` `mode: "goal"`, `GoalRunCard.tsx` | Not `room_post` + Host |
| `PlaceChip` / computer place | `PlaceChip.tsx`, `lib/place.ts` | Box/VPS/local VM place |
| `FullAccessWarning` / local VM warning | `FullAccessWarning.tsx`, `LocalComputerAutoWarning.tsx` | VM |
| Webhooks on Routines page | `WebhooksPanel.tsx` | `/api/webhooks` empty stub |

### Other FOREIGN / STUB files (unlink then delete)

`AndroidDevicePanel.tsx`, `BrowserPanel.tsx`, `BrowserViewport.tsx`, `BrowserProfilesManager.tsx`, `CloudBackendPicker.tsx`, `CloudScreenPreview.tsx`, `LocalScreenPreview.tsx`, `MacLocalControl.tsx`, `LinuxLocalControl.tsx`, `ClaudeSignIn.tsx`, `ClaudeAccountSettings.tsx`, `CodexAccountSettings.tsx`, `CodexDeviceSignIn.tsx`, `SignInAccessCard.tsx`, `ComputerSharingSettings.tsx`, `DesktopWorkspaceSwitcher.tsx`, `ThreadConcurrencySettings.tsx`, `RoomTurnTimeoutSettings.tsx`, `bot-settings/ManagedTeamsSettings.tsx`, `TeamDialog.tsx` (team folders — not Rooms), `BotProjects.tsx` (task folders), `onboarding-preview.tsx`, `mascot-preview.tsx` (dev entries — keep if unused by App), `lib/mcp-servers.ts`, `lib/phone-setup.ts`, `lib/tts/`, `shared/image-generation.ts`, `shared/workspace-backup-client.ts`.

### Store actions that exist only for deleted screens

`showTeamMap`, `togglePlugins`, `toggleWelcome`, `toggleTour`, webhook hydrate/patch, `screenFrame`, `provisioning`, `computerControl` (VM lease), `createProject` / `updateProject` / `deleteProject` / `reorderProjects`, group `mode: "goal"`, `newTask`/`switchTask` if we drop TaskPicker (Harness has one lane, not N threads).

`api<T = any>` in `store.tsx` is a TypeScript ban; fix when touched.

### Copy that names a foreign product

`en.json` (and other locales): Maus, GrokBot, Composio, OpenMausBot, companion, fleet, Box, VPS, “Chief of Staff”, `pnpm dev:server`. Empty states must name the missing Harness artifact.

---

## 5. Harness nouns that have no first-class surface yet

| Noun | Disk | HTTP already? | Gap |
| --- | --- | --- | --- |
| Roster as roster | `harness/roster.json` | GET `/api/bots` wire; PATCH/POST/DELETE exist | Sidebar still speaks “threads / teams / Chief of Staff” |
| Live lane status | `lane.json` | folded into wire `busy` | Need idle/running/blocked/offline + pending inbox + pid |
| Protocol (office-wide) | `protocol.jsonl` | `GET /api/protocol`, `GET /api/search` | No nav item; inspector is per-bot RuntimeEvent clone |
| Handle files | `handles/<id>.json` | `GET /api/handles/:id` | Inspector does not name Handle status accept ≠ complete |
| Inbox | `inbox.jsonl` | GET on `/api/bots/:id` | No pending-handle chip |
| Intercept | `harness/intercept.json` | GET/PUT `/api/intercept` | Only a JSON textarea in HarnessDeskSettings |
| Extra extensions | `extensions.json` + config | `/api/config`, `/api/attach` | Buried in Settings → Harness |
| Client skill filter | `HARNESS_CLIENT_SKILLS` | config `clientSkills` | Same |
| Computer files | cwd | `/api/computer/tree`, `/file` | ComputerPanel does not call them |
| Spawn policy | `~/.harness/config.json` | config | Same buried row |
| Google key | config nested `google` | `patchOperatorConfig` already | `ApiKeys.tsx` has no Google row |
| Receipts | `receipts/` | desk maps to routine runs | Calendar still says Automations / `runOn: "maus"` |
| Pi session pid | `pi-session/` + supervisor | `GET /api/sessions` | Not shown on roster row |

---

## Phase 0 inventory (screen → files → HTTP → verdict)

### Entry and shell

| What Operator sees | Files | HTTP / disk | Verdict |
| --- | --- | --- | --- |
| Tab title OpenMausBot | `index.html`, `lib/brand.ts`, `GET /api/brand` | brand JSON | FOREIGN copy on KEEP visual |
| Connecting / No bots | `App.tsx` `Shell` empty main | waits hydrate `GET /api/bots` | KEEP-VISUAL (copy is clone: `pnpm dev:server`) |
| Bot 1:1 | `ChatView` | messages + interrupt | WIRED |
| Room | `GroupView` | groups messages | WIRED (goal mode STUB/FOREIGN) |
| Settings modal | `SettingsModal` | mixed | mixed — see §4 |
| Bot settings dialog | `BotSettingsDialog` | mixed | mixed |
| Inspector dock | `InspectorPanel` | `/api/threads/:id/events` | KEEP-VISUAL (wired to protocol via desk; UI copy still “RuntimeEvent tee”) |
| Computer dock | `ComputerPanel` | Box/VPS/local | FOREIGN body; KEEP-VISUAL dock |
| Command palette | `CommandPalette` | `/api/search` | WIRED via desk |
| New bot | `NewBotDialog` | `POST /api/bots` | KEEP-VISUAL (roles + Gmail/GitHub hints FOREIGN) |
| Keyboard shortcuts | `KeyboardShortcutsModal` | NONE | KEEP-VISUAL |

### Store bootstrap (`StoreProvider` in `store.tsx`)

Loads `GET /api/bots`, `GET /api/instances`, `GET /api/config`, `GET /api/routines`, `GET /api/webhooks`. SSE `openLiveEvents` → `/api/events`. Webhooks are STUB. Instances are a synthetic Pi row (`piInstance()` in `omb-compat.ts`) — KEEP-VISUAL if we stop using them to block the UI.

### HTTP dialects

| Dialect | Audience | UI uses? |
| --- | --- | --- |
| `/api/*` + desk + omb-compat | Operator SPA | yes |
| `/v1/*` in `http.ts` | headless / tests | no |
| `window.ogb` | Electron OpenMausBot | absent in browser serve |

New screens must call existing `/api/*` (or `/v1/*` that already persist). Do not add a third dialect.

---

## What a click does today (summary)

| Click | Fetch | Disk write | Else |
| --- | --- | --- | --- |
| Send in DM | `POST /api/bots/:id/messages` | inbox, Handle, protocol, transcript | SSE hello |
| Stop | `POST …/interrupt` | `user_stop` Handle | |
| Allow/Deny card | `POST /api/threads/:id/respond` | `approvals/<id>.json` | |
| Room post | `POST /api/groups/:id/messages` | room log + member inboxes | Host |
| Save Anthropic key | `PUT /api/config` `{ anthropic: { key } }` | `~/.harness/config.json` 0600 | secret not echoed |
| Test key | `POST /api/keys/test` | may save nested key | must not lie |
| Toggle skill | `PATCH /api/bots/:id/skills/:name` | `roster.json` skills[] | |
| Save memory | `PUT /api/bots/:id/memory/file` | `memory/MEMORY.md` or topic | |
| Save Harness desk | `PUT /api/config` + `PUT /api/intercept` | config + `intercept.json` | |
| Team map / phone / plugins / VM / MCP / backup / people / fleet | various | **none that this runtime owns** | FOREIGN |
| GitHub skill import | `POST …/skills` with URL | refused 400 | do not keep the button |
| Task/thread switch | `POST /api/bots/:id/tasks` | **in-memory `taskOverlays` only** | STUB |
| Edit message / branch | `…/messages/:id/edit` | omb catch-all stub | STUB |

This baseline is frozen. Phase 3 may only delete rows from §4, rewire rows from §2, and add first-class surfaces for §5 by extending KEEP-VISUAL components.

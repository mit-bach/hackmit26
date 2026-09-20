# Live Harness — operator handoff

**CFO V2 desk (show this):** `http://127.0.0.1:8800/`

Leave 8792 for the other UI agent. Do not reuse 8791/8795.

Computer: `.cfo-v2/office/computer`. Config: `harness/client.json` (xAI/Grok 4.5, thinking `low`, transcript **full**, extra `-e` `./cfo/extensions/index.ts`, Kernel sidecar). Pi auth is `~/.pi/agent/auth.json`. Wipe: `node dist/src/cli.js wipe --computer ../../.cfo-v2/office/computer` from Harness-v2, or `POST /api/wipe`. Run notes: `.cfo-v2/office/RUN.md`. Demo seed: `.cfo-v2/office/seed_demo.py` and `DEMO-WALKTHROUGH.md`.

`.cfo-v2/` is the office. `examples/cfo-floor` is a six-slug fixture. They are not the same product.

## Demo (no live mailbox)

Seed (once per wipe of `runs/`):

```bash
HARNESS_COMPUTER=.cfo-v2/office/computer PYTHONPATH=.cfo \
  .cfo/.venv/bin/python .cfo-v2/office/seed_demo.py
```

Then on `http://127.0.0.1:8800/`:

1. Open **Email**. Header **Transcript detail** → **Full**. Ask it to `call_connected_tool` `list_email_candidates` for `2026-09`. Expect MSG-E01…MSG-E04 plus expanded Kernel JSON.
2. Open **AP**. Ask it to `call_connected_tool` `tools.get_invoice` `ING-001`. Expect Acme Supplies / 12,450 from demo-inbox.
3. Bug icon → Inspector **Pi events** / **Pi RPC** for the verbatim Harness stream (not a mascot-only “thinking” row).

Proven live 2026-09-20: Email replied `office-ok`; `search_connected_tools` and `list_email_candidates` ran; AP loaded ING-001. Capabilities were not deleted — they were hidden by thinking-only UI and a `turn_end` that cleared the stream mid-tool.

---

## What live actually did (cfo-floor + xAI Grok 4.5)

Forced spawn with `HARNESS_CONFIG` `provider=xai` `model=grok-4.5`. Did not rewrite `~/.pi/agent/settings.json`.

| Claim | Result |
| --- | --- |
| Six Pi RPC children on cfo-floor | Pass. `/api/sessions` showed alive pids. `fakeWorkers: false`. |
| Operator HTTP send → Handle `completed` | Pass. `live-ok`. |
| Ingest → Payables `bot_send_prompt` then `bot_await_turn` | Pass. Protocol seq 60–64. Peer text `peer-ok`. |
| Same Computer files visible from cmux | Pass. `examples/cfo-floor/harness/bots/bot_ingest/pi-session/*.jsonl` and `harness/protocol.jsonl` match the HTTP Computer. |
| Composer send shows a real bubble | Pass after xAI override. Screenshot: user `Reply with exactly: ui-ok` → bot `ui-ok`. Sidebar preview `ui-ok`. |
| Default Codex `gpt-5.4-mini` | Fail. ChatGPT account rejects that model. Older bubbles stay `(settled)` or the Codex error string. |

Without a working provider/model, live chat is the Codex error. Fake `--fake` replies (`[ingest] …`) are not this engine.

---

## cmux vs Operator UI

Operator-selected pane at test start: `workspace:55` “π - Harness-v2”, unbound `pi` in `.harness/Harness-v2` (model overlay, footer still `gpt-5.4-mini`). Not driven.

Isolated throwaway:

- `workspace:56` unbound `pi` in the Harness-v2 tree (cwd isolation missed; landed in the package, not `/tmp`).
- `workspace:57` bash listing of cfo-floor `pi-session` + protocol tail.

| Pi TUI (cmux) | Operator UI |
| --- | --- |
| `/` opens slash overlay: settings, model, tree, thinking, … | `/` in composer is a draft character. No Pi overlay. No `/model`, `/login`, `/settings`, `/session`. OMB slash ids are `/goal` `/learn` `/setup` only; none appeared. |
| `/help` + Enter is a **paid user prompt**, not help. | N/A. |
| Ctrl+P model catalog is the real Pi list (Codex + xAI). | Header “P grok-4.5” opens OMB picker. Refresh → **Local / no local models found**. Stub instance `GET /api/instances` returns one option (`grok-4.5`). Picking in that menu does not drive Pi `/model`. |
| Login is Pi TUI / `~/.pi/agent/auth.json`. | You → Get iOS, Settings, shortcuts, About. No Pi login. `GET /api/auth/session` is loopback `{kind:"loopback"}`. Settings → Engines: “Pi Bring your own model Ready” + “Add Claude account”. Settings → Connections: Anthropic/OpenAI/xAI/Box/VPS/OpenCode/Composio key fields (OMB). Real spawn model is Settings → **Harness** text fields (provider/model) after worker restart. |
| Bound Bot: `HARNESS_BOT=… pi -e extensions/index.ts` | HTTP + SSE projection of `harness/` files. |

A second Pi TUI on the same `pi-session` dir as a live RPC child is not a supported attach. cmux can **read the same files**. It cannot be the Operator desk.

---

## Broken or not ported (Operator chrome)

Keep-visual OMB. These were clicked or snapshotted live:

1. **Pi slash commands** — not in the desk.
2. **Pi model selector / Ctrl+P catalog** — stub. Harness desk text fields are the real control; they do not hot-reload running RPC children.
3. **Pi login / logout / Codex ChatGPT account** — not ported. Loopback auth.
4. **Computer dock** — “Where this conversation works: Off”, disabled. Not the Computer file tree.
5. **Calls** — “need the macOS desktop app”.
6. **ElevenLabs speak** — disabled.
7. **You menu** — iOS / Help Center / Feedback leftovers.
8. **Settings leftover OMB** — Local VM, People, Backups, Remote access, Usage, Experimental, Engines Claude account. Dead relative to this host.
9. **Skills** — desk API can list `Computer/skills/<name>/SKILL.md` grants. cfo-floor roster `skills: []`. Skills never grant Kernel tools. UI skill authoring is OMB-shaped, not Pi `/skill:`.
10. **Connectors** — roster strings / empty Composio catalog. Not live Gmail/Stripe/Xero.
11. **Visible chat leaf** — HTTP sends that are not on the OpenMausBot `parentId` walk do not show in the open thread. Composer send does.
12. **Brand** — window title still OpenMausBot.

Working desk pieces (live): bot list, composer send, Handle-backed reply, Settings → Harness spawn/provider/model/extensions, protocol files on disk.

---

## CFO V2 specifically (why deploy is no)

Computer: `.cfo-v2/office/computer`. Roster: 15 Bots. Documented live bind is `cfo/bin/pi-bot.sh` (Harness `-e` **plus** Client facade `-e`). Documented Operator demo is `--fake`.

Live lazy serve on port 8793 (`fakeWorkers: false`, Client extra `-e` + `clientSkills: true`):

- Kernel sidecar **not running** (`cfo/kernel.port` missing). Domain ops have nowhere to go.
- `harness/extensions.json` on that Computer is `{ extraExtensions: [], clientSkills: false }`. Attach is not the default disk state.
- Stale inboxes: close/story/audit **67+** routine lines; ap/ctl-pay leftover a2a. Lazy spawn **immediately** started those Bots. `monthly` cadence is `30 * 24 * 60 * 60 * 1000` = 2592000000 ms → `TimeoutOverflowWarning`, interval clamped to **1 ms**. Do not leave live workers on this office until inboxes are drained or archived and cadence is fixed.
- Serve was stopped after that observation so stale routines would not keep calling the model.
- Kernel still owns `python main.py demo-inbox` / `simulate-stripe` / `close-month`. Those are not Harness Bots finishing Handles on live Pi.

A working cfo-floor ping is not a working Office of the CFO.

---

## Should work in this Harness (operator punch list)

Port or rewire; do not leave OMB chrome that lies.

| Must work | Disk / engine | Today |
| --- | --- | --- |
| Provider + model for spawn | `~/.harness/config.json` or Settings → Harness; restart workers | Partial. Text fields exist. Header picker is fake. Default Pi settings still Codex `gpt-5.4-mini`. |
| Keys / Pi auth | Nested keys in operator config; Pi `auth.json` for OAuth | Partial. Connections form exists. No Pi login. Codex ChatGPT account cannot use `gpt-5.4-mini`. |
| Slash / thinking / session / compact | Pi TUI only today | Missing on desk. |
| Skills as `SKILL.md` grants | `Computer/skills/` + roster.skills + client filter | API exists. Not wired as Pi `/skill`. Empty on cfo-floor. |
| Client attach | extra `-e` + `extensions.json` | Implemented. Not applied on CFO V2 disk. |
| Bot-to-bot | `bot_send_prompt` / Handles / protocol.jsonl | Live pass on cfo-floor with a working model. |
| Rooms / Host | roster rooms, serial wake | Not re-proven live this pass (fake-era leftover Payables preview `[ap] These nuts.`). |
| Computer files | `/api/computer/tree` | API exists. Chat “Off” control is dead OMB. |
| Approvals | `harness/approvals/` | Not exercised live this pass. |
| Routines | roster cadence → inbox | Dangerous: monthly overflow; CFO V2 backlog. |
| Stop | cancel running Handle | Not re-clicked this pass. |
| Kernel sidecar | `python -m cfo_kernel` | Required for CFO V2. Down. |

---

## Verification leftovers

- Throwaway cmux: `workspace:56`, `workspace:57` (closed after this note).
- Operator pane `workspace:55` left as found.
- Live cfo-floor serve may still be on `127.0.0.1:8791` with xAI override in `/tmp/harness-live-xai.json`.
- Isolated unbound `/help` spent a Grok 4.6 turn; interrupted after the reply.
- Did not commit.

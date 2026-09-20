# SOURCE

## Spec

- `GROK-WORKSHOP/harness-init/engineers/lark/HARNESS-V2.md`
- Operator prompts in `GROK-WORKSHOP/harness-init/Source-material/Grok-Pi Coding Agent GrokBot Extensions Research-20260919-1439.md`
- Client-system *shape* only: `design-workshop/dominik/cfo-office-processes.md` (not in Harness code)

## Pi

- `@earendil-works/pi-coding-agent` ^0.85.1 (peer). Turn engine, RPC, extension ABI.
- Docs used: https://pi.dev/docs/latest/extensions and https://pi.dev/docs/latest/rpc

## Not installed as the Bot network

- `pi-subagents`
- `pi-agents-talk-to-each-other`
- `pi-cross-session`

Those move text between live processes. They do not give durable BotId, accept≠complete Handles, or a Room Host.

## External protocol notes

- https://docs.x.ai/grok-bot/chat-and-collaboration
- https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/plans/2026-09-02-bot-concurrency.md
- https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/memory.md

## Operator shell

- Operator SPA is the OpenMausBot frontend (Apache-2.0), vendored under `ui/src`, `ui/shared`, and `ui/public`. See `ui/NOTICE` and `ui/LICENSE`.
- The Harness host implements the OpenMausBot `/api` shapes so that UI is unchanged. Pi is the only engine. Computer panel file tree stays on Harness routes; Box/CUA/Electron bridges are stubbed.
- Computer panel is the shared files tree, not Box/CUA.

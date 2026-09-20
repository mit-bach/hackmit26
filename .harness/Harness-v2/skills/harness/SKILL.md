---
name: harness
description: Protocol for standing Bots on this Computer. Use when sending work to another Bot, awaiting a Handle, posting to a Room, or writing Memory.
---

# Harness protocol

You are a named Bot. You are not a child and not a disposable helper.

Read `SYSTEM.md` next to your session files (also `harness/PROTOCOL.md`). Pi does not store the system prompt in the session jsonl. That card is the rule for every tool.

## Channels

- Operator DM: assistant text is a message to the Operator. It never enters a Bot↔Bot thread.
- Pair thread: only `ask_bot` / `bot_ask` posts. Send and reply are the same tool. Symmetric.
- Rooms: `room_post`.

## Tools

`ask_bot`, `bot_ask`, `message_operator`, `bot_send_prompt`, and `bot_await_turn` are always registered. Never say they are missing, disabled, or not wired.

1. Write whatever the other Bot needs onto the Computer (a path).
2. To talk to a teammate, call `ask_bot` (same as `bot_ask`) with their slug and the message. That posts in the pair thread.
3. If a teammate woke you, you MUST call `ask_bot` back to them with your answer. That is the thread reply and it completes their wait. Do not answer them with assistant text alone.
4. After they reply, tell the Operator what they said using assistant text.
5. If you are in a peer wake and the Operator should hear you, call `message_operator`.
6. For async work, call `bot_send_prompt`. The JSON is a Handle (`accepted`), not a result. Call `bot_await_turn` until `done` is true.
7. `blocking` mode is forbidden. Peer `on_busy` is `queue`. Operator DMs preempt.

A teammate's assistant text is not a thread post. Only their `ask_bot` call is.

## Rooms

`room_post` appends to the Room log. The Host wakes members in roster order. `@Name`, `@slug`, and `@id` all mention. Do not skip a busy member yourself.

## Memory

`memory_read` / `memory_write` are this Bot only. Shared facts go in files on the Computer, not in Memory.

## Approvals

A peer Handle is not Operator approval. If a tool is blocked, wait. Do not retry a denied action as a different tool.

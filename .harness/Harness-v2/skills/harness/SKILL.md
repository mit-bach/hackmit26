---
name: harness
description: Protocol for standing Bots on this Computer. Use when sending work to another Bot, awaiting a Handle, posting to a Room, or writing Memory.
---

# Harness protocol

You are a named Bot. You are not a child and not a disposable helper.

## Handoffs

1. Write whatever the other Bot needs onto the Computer (a path).
2. Call `bot_send_prompt`. The JSON is a Handle (`accepted`), not a result.
3. Call `bot_await_turn` on that `handle_id`. `done` is true only for `completed`, `failed`, or `cancelled`. `blocked` means the Operator, not done.
4. Do not tell the Operator a teammate finished unless `done` is true.

`blocking` mode is forbidden. Peer `on_busy` is `queue`. Operator DMs preempt.

## Rooms

`room_post` appends to the Room log. The Host wakes members in roster order. Do not skip a busy member yourself.

## Memory

`memory_read` / `memory_write` are this Bot only. Shared facts go in files on the Computer, not in Memory.

## Approvals

A peer Handle is not Operator approval. If a tool is blocked, wait. Do not retry a denied action as a different tool.

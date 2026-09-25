# create_accrual unlock

## Root cause
`cfo/extensions/index.ts` registers `call_connected_tool` with only `name` / `args` / `idempotency_key`.
Its execute path always passes `handleId: null` into `callConnectedTool`.

`gateConsequentialCall` → `completedHandleAllowsOp(computerRoot, handleId, op)` therefore never sees the CONCUR handle, so every retry re-enters `interceptVerifier` and parks a NEW handleId.

## Required client fix (host/Operator must patch; ctl-books desk cannot write cfo/)
Add optional `handle_id` to the tool schema and pass it through:

```ts
handle_id: Type.Optional(Type.String({...})),
// ...
const handleIdParam = readString(params, "handle_id");
// ...
handleIdParam.length > 0 ? handleIdParam : null,
```

Tests in `facade.test.ts` already call `callConnectedTool(..., handleId)` after writing harness CONCUR.

## After patch, close second-call shape
```
call_connected_tool
  name: accrual.tools.create_accrual
  args: { vendor, period, method, confidence, evidence, reasoning_summary }
  idempotency_key: accrual-2026-09-<vendor-key>
  handle_id: h_<from verifier_required / COMPLETED CONCUR>
```

Prefer earliest COMPLETED-CONCUR handles:
- h_6c062928-6dc6-4533-b3bf-400df14afadd aether
- h_29fcb227-0612-47db-bb13-41a2d60594b8 cleanspace
- h_efe7f061-08bf-471e-94c8-279748bda539 clearing
- h_321a287c-7212-4f31-8b01-d2373107686a harbor
- h_3bb0a19e-a919-4fa7-aa16-34ebb366b796 lindholm
- h_f5796a0d-2ba3-472d-a677-0a754a63e634 pulse

## Not unlock paths
- bot_resolve_approval (no approval queue for these)
- ask_bot vs bot_send_prompt: both can complete harness handles; intercept uses sendPeerHandle; CONCUR via ask_bot already completes the same handle file
- ctl-books cannot call create_accrual (VERIFIER_SLUGS forbidden)
- packet JSON allow text is not source of truth

## bot_send_prompt
Not required if handle already COMPLETED+CONCUR. Re-parking creates yet another handleId.

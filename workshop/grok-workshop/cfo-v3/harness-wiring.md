# Layer 3 — Harness serves `.cfo-v3` and the controls work

Writes only under `/Users/dominikbach/olympus/hackmit/hackmit26/.harness/Harness-v2`. This file replaces the earlier draft of the same name.

Authority: `DESIGN-REVIEW.md` sections 3 and 10, items 1 through 5. Those items are verified defects. Do them. Do not start item 11 (workflow graph) or item 12 (verifier model split) here.

## Job

1. `call_connected_tool` passes the real verifier handle id. A test must call the Pi tool path, not `callConnectedTool` with a hand-fed id. Today `handleId` is always `null`, so a consequential op stays `verifier_required`.
2. Concurrence is a structured decision. The strings `I do not concur` and `CONCUR is not possible` must not count as CONCUR. Add a test with those strings.
3. `bash` cannot write or read outside the Bot desk. A regex on the raw command is not enough. `python3 -c "open('harness/roster.json','w')"` and `cat workspace/cash/...` from another slug must fail. If that cannot be done in-process, remove `bash` from operational Bots and keep `read`, `write`, and `edit`, which already have a path check.
4. `profile:` matches only the harness wake header, not a later line in the body. One function sets both the Grant and the context layer. No header means `defaultProfile` on every wake.
5. Serve command uses `--computer` pointing at repo-root `.cfo-v3`. Document it under `## Proved`. Do not document a second port. Do not require `.cfo` or `.cfo-v2` on `PYTHONPATH`.
6. Leave context assembly as office text plus bot text. Do not put `MEMORY.md` or recent-work lines back into the system prompt. Delete the unused `identityBlock` import if nothing calls it.

## Done when

The new tests fail on the old behavior and pass after the change. The serve line is written under `## Proved`.

## Landed

Serve against repo-root `.cfo-v3` sets `HARNESS_COMPUTER` to that directory and `CFO_KERNEL` to `.cfo-v3/kernel` when `kernel/cfo_kernel` is present. A directory named `.cfo` is never selected. Office lookup no longer walks `.cfo-v2/office`.

Bash checks resolved paths, including `python3` `open`, `sed -i`, bare relative paths, `cd ..`, another Bot's `workspace/`, and answer-key names. Context still pastes office text, bot text, the resolved profile, and `skills/<name>/SKILL.md`. It does not paste `MEMORY.md`, recent work, `cfo/skills`, `PROTOCOL.md`, or per-bot `SYSTEM.md`. A `profile:` line in the wake body does not change that layer. No header uses `cfo/slug-map.json` `defaultProfile`.

`call_connected_tool` (`handleId` null) and the free-text CONCUR parse still live in `.cfo-v3/cfo/extensions/`. This pass did not write that tree.

Files:

- `.harness/Harness-v2/src/sidecar.ts`
- `.harness/Harness-v2/src/cli.ts`
- `.harness/Harness-v2/src/index.ts`
- `.harness/Harness-v2/src/sandbox.ts`
- `.harness/Harness-v2/src/context.ts`
- `.harness/Harness-v2/src/wake-profile.ts`
- `.harness/Harness-v2/src/server/office-instances.ts`
- `.harness/Harness-v2/extensions/index.ts`
- `.harness/Harness-v2/tests/context.test.ts`
- `.harness/Harness-v2/tests/sandbox.test.ts`
- `.harness/Harness-v2/tests/kernel-env.test.ts`

## Proved

From `.harness/Harness-v2`, after `npx tsc -p tsconfig.json`:

```
node dist/src/cli.js serve --computer /Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3 --no-open
```

That is the existing serve entry. It does not use a second port and does not put `.cfo` or `.cfo-v2` on `PYTHONPATH`.

Tests run: `tests/context.test.ts`, `tests/sandbox.test.ts`, `tests/kernel-env.test.ts`.

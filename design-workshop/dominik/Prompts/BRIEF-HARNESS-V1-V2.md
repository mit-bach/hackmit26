# Explore brief — Harness v1 vs v2 deploy plan

Repo: `/Users/dominikbach/olympus/hackmit/hackmit26`

Harness v2 (deploy target): `.harness/Harness-v2/`
Harness v1: `.harness/Harness-v1/` — Foundry extensions (`foundry-roster.ts`, `foundry-comms.ts`, `foundry-subagents.ts`, `foundry-memory.ts`, `foundry-routines.ts`, `foundry-approvals.ts`).
Design: `GROK-WORKSHOP/harness-init/engineers/lark/HARNESS-V2.md`
Pike drive: `GROK-WORKSHOP/harness-init/engineers/pike/DRIVE-REPORT.md`
Operator note: `Operator-workspace/Prompts/Harness analysis.md` (read only; do not edit)

The human believes v1 composed many Foundry extensions (roster, comms, memory, routines, approvals) and v2 collapsed to one `extensions/index.ts`, losing scale for clients.

Return a structured report. Do not write files. Do not modify anything.

Investigate:

1. v1 extension inventory: every extensions/*.ts plus lib/manifest, how roster was loaded (foundry-output JSON vs roster.md vs roster.json). Tools and slash commands each file registers.
2. v2: `extensions/index.ts`, `src/cli.ts`, `src/bind.ts`, `src/worker.ts` or supervisor, `src/prompt.ts`, `src/approvals.ts`, `src/roster.ts`, `src/pkg.ts` (`extraExtensionArgs` / `HARNESS_EXTRA_EXTENSIONS`), types, README.
3. Compare: multiple Pi `-e` modules vs one blob; how a Client at `.cfo-v2/office/computer/cfo/extensions/` attaches; whether `serve` sets extra extensions.
4. v2 `ui/` — OpenGrok-scale copy vs this runtime. In or out of deploy?
5. Protocol vs HARNESS-V2.md: accept≠complete, fake workers vs live Pi, HTTP, rooms 2-6, memory, approvals still Operator-shaped (blocks verifier routing).
6. What v2 MUST change to be deployable as the bus for a 15-bot CFO Client WITHOUT finance types in Harness core. Extension composition, Client-owned roster, bind hooks for grant filter, skill intersect, intercept retargetable to another Bot not only Operator.
7. What belongs in Harness vs CFO Client.

Return: v1 inventory; v2 inventory; lost capabilities; deploy blockers; sequenced plan (phases); Harness vs Client split.

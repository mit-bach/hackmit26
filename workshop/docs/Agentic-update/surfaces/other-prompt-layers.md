# Surface — other prompt layers besides BOT.md and skills

BOT.md and SKILL.md are not the whole prompt surface. A later agent that only rewrites those two will leave the other layers in place. Those layers will still drive the model or the Python host.

---

## Layers that already tell a model what to do

| Layer | Path | What it is |
| --- | --- | --- |
| Roster instructions | `computer/harness/roster.json` `instructions` | Two to five sentences. Point at BOT.md. Wrong cwd path today. |
| Profile markdown | `office/bots/<slug>/profiles/*.md` | Extra procedure. Pi does not auto-load. Client `profile:` header is the Grant switch, not this file. |
| Kernel constructor instructions | `.cfo/**/agent.py`, `agents.py` `Agent(instructions=...)` | Still used if `Runner` runs. Still the Grant source. Collections Agent here imports send and cannot construct. |
| Skill injection | `skills/loader.py` `compose_instructions` | Embeds SKILL.md into constructor instructions. |
| Harness identityBlock | `.harness/Harness-v2/src/prompt.ts` | Standing Bot, peers, Handle protocol, connector sentence “not a live facade.” |
| Harness protocol skill | `.harness/Harness-v2/skills/harness/SKILL.md` | `blocked` means Operator in older text. |
| Routine prompt | Roster `routines[].prompt` | Includes `profile:` and demo procedure. |
| Handle prompt | whatever `bot_send_prompt` writes | Wake text. Must name a path, not paste the invoice. |
| Client verifierInstruction | `cfo/extensions/verifier.ts` | Concur or refuse. Packet path. |
| SAFETY blocks | Kernel agent modules | Hard-hold English. Overlaps skills. |
| NOTES.md / PROOF.md | `office/bots/<slug>/` | Operator notes. Not loaded by Pi unless someone pastes them. |
| World pack copy | `world/maximor` | Data, not prompt, but models will quote it if they open it. |

---

## Why this matters

User intuition: “we have BOT.md and skills.”

That is the office-facing pair. The Kernel constructors are a third brain. As long as `workflow.py` calls `run_agent`, the constructor prompt is the one that runs for that host. As long as Pi runs, BOT.md + skills + Roster + Harness identityBlock run, if those files are reachable.

Split brain T2 is often two of these layers disagreeing. AR send is constructor vs skill vs workflow vs live BOT.md vs instance roster.

---

## What is good

Keeping SAFETY and Kernel validators in Python-adjacent text is better than hoping the model remembers. The inadequacy is duplication across SAFETY, Skill, and BOT.md until nobody knows which is law.

---

## Capability

There should be one standing identity the bound Bot actually reads, plus Kernel law it cannot override. Constructor instructions should not be a second office. They remain Grant source. They should not silently outrank BOT.md when both run.

This file does not merge the layers. It requires that a later writer inventory them before changing one.

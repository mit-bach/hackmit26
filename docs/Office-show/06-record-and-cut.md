# Record and cut (the showcaser)

The Harness **Demo** page is the showcaser. Operators UI: Tools → Demo. It replays protocol from seq 0, spawns mosaic panes for awake Bots, and can play at 0.5×–4×.

Code: `.harness/Harness-v2/ui/src/components/DemoPage.tsx`, `.harness/Harness-v2/src/demo-replay.ts`. Disk: `{COMPUTER}/harness/demo/latest/` after record.

You do not film 40 hours of waiting. You record the protocol, then **cut** seq ranges. Screen capture of Demo playback is the video. The instance remains so you can Inspector-zoom a Handle if a judge asks.

---

## Record (once, at the end)

When ME is done and you have not aborted:

```bash
curl -sS -X POST {URL}/api/demo/record
```

Or Demo page → Record.

This copies:

- `protocol.jsonl`
- each Bot `transcript.jsonl`
- derived activities
- `meta.json` (`recordedAt`, `lastSeq`, `eventCount`, bot ids)

Wipe does **not** delete `harness/demo/latest/`. Still: copy that folder to `docs/Office-show/runs/<id>/recording/`. Then do not wipe the golden Computer.

Do not Record after a FAILED run and call it the goose.

Live vs recording: Demo can play `source=live` (current protocol) or `source=recording` (the snapshot). After record, prefer **recording** so later peeks do not extend the tape.

---

## What you do not record as a second product

- Kernel `evaluate-cfo` 97%
- `--fake` protocol
- Prove instance protocol
- Website pages with hard-coded outcomes
- Holdout catalogs

The website may later **point at the same IDs**. It must not invent traces the golden desk never produced.

---

## Cut after you have seqs

You cannot know seq numbers until the run ends. `cuts/README.md` is a template. Fill `runs/<id>/CHAPTERS.md` like:

```
A onboard     seq 1–40
B inbox traps seq 41–90
C INV-001     seq 91–140
D pay-run     …
E Helios+$12.40
F close BLOCKED + story UNLOCKED
G audit INV-001
```

The ten-minute table in `final-demo/SCENARIOS.md` maps to these chapters. It is a **suggested edit**, not a second run.

---

## Suggested videos (several cuts, one tape)

Not everything is a video. Everything is on the tape. You pick:

| Cut | Why it exists | Likely chapter |
| --- | --- | --- |
| Desk | 15 Bots, not a chatbot | A start, mosaic |
| Inbox traps | Quote/injection die | B |
| Acme clean | One id AP → ctl-pay | C |
| Pay-run | Valid is not paid | D |
| `$12.40` | Close will not lie | E–F |
| Audit | Independent, same INV-001 | G |
| Optional: dun+World | Last mile | W4 |
| Optional: GM flux | Story UNLOCKED | F |

A single 10-minute reel is a concatenation of those cuts. Portfolio can also ship them as separate clips. You decide after you scrub. You do not re-run the month to get a different Acme.

---

## How to scrub

1. Open Demo on the golden Computer (recording source).
2. Play at 4×. Note seq when a featured id appears (`INV-001`, `TXN-2026-09-015`).
3. Inspector → Pi RPC on that Handle. Confirm a real tool return, not English.
4. Write CHAPTERS.md.
5. Screen-record Demo at 1× for the cut ranges only.
6. Do not splice in Kernel CLI windows as if they were Bots.

If a cut is boring (twenty identical HOLDs), drop it. Texture can stay on the raw slider for anyone who wants scale.

---

## Operator on camera

If overlay DMs appear, they should be the onboard sentences. If you see “Call tools.get_case_evidence,” you recorded a prove desk by mistake. Do not ship it.

Verifier panes should never show Operator as `from`. `from` is `bot_ap` or `bot_pay`.

---

## After videos

The goose is still the instance + recording. Videos are views. If a judge wants “what else did collect do?”, you open the desk, you do not invent a clip.

Keep `golden-…` selected only when showing. Daily work goes back to `live`.

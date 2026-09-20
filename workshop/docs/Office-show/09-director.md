# Director (camera, scenes, tape)

The Demo page is a **camera**, not the movie. It can replay the whole Golden tape or a seq-in / seq-out cut. An agent or a human sets the shot, records a clip, then edits later. That last step stays outside the Harness: screen capture, stitch, cut, upload.

This file is the spec for that camera. Implementation that already exists is marked **shipped**. The rest is the overhaul that can land without changing the Golden desk.

---

## Two jobs that were collapsed into one

| Job | Question | Artifact |
| --- | --- | --- |
| Tape | What happened on the desk? | `{COMPUTER}/harness/demo/latest/` = `protocol.jsonl` + transcripts + `meta.json` |
| Picture | What should a viewer see right now? | Director: max panes, featured Bots, seq in/out, saved `scenes.json` |
| Movie | What do we upload? | Screen capture of Demo + post-edit. Not a Harness file. |

The first Demo build only did tape, and it did it badly: `GET /api/demo` parsed every Bot’s `pi-runtime.jsonl` (megabytes of Pi RPC). The serve event loop blocked. Tools → Demo looked empty or frozen. Nine or ten awake Bots made the mosaic tiny and the markdown too heavy to paint.

**Shipped fix:** record and load from `protocol.jsonl` + `transcript.jsonl` only. Activities are derived from transcript kinds. Pane markdown is capped. The camera can keep 1, 2, 4, 6, 9, or 16 panes and hide the rest as “off camera.”

---

## Tape (full session)

Record once, at the end of a show run, or any time you want a snapshot that survives wipe.

```bash
# Does not need HTTP. Use this when serve is busy with Pi.
node dist/src/cli.js demo record --computer ../../.cfo-v2/office/computer

# Same snapshot via the SPA
# Tools → Demo → Record
# or: curl -sS -X POST http://127.0.0.1:8800/api/demo/record
```

`--computer` on the live template honors `office.json` `currentId`, so a selected Golden desk is what gets recorded.

What is copied:

- `harness/demo/latest/protocol.jsonl`
- `harness/demo/latest/transcripts/<botId>.jsonl`
- `harness/demo/latest/activities/<botId>.jsonl` (turn.started / turn.completed only)
- `harness/demo/latest/meta.json`
- existing `scenes.json` is kept across re-record

What is **not** copied: `pi-rpc.jsonl`, `pi-runtime.jsonl`, Pi session trees. Those stay on the Computer for Inspector. They are not the movie.

After record, copy the folder off-instance:

```
docs/Office-show/runs/<id>/recording/
```

Play **Tape** (source=recording) when showing. Live keeps growing if anyone peeks.

Headless status:

```bash
node dist/src/cli.js demo meta --computer ../../.cfo-v2/office/computer
```

---

## Picture (director)

The timeline is still protocol seq. The camera is a filter on **who is on stage** and **which seqs the playhead walks**.

| Control | What it does | Default |
| --- | --- | --- |
| Max panes | 1 / 2 / 4 / 6 / 9 / 16. Overflow chip `+N off camera` | 6 in the SPA, 16 in the engine |
| Featured Bots | Those slugs stay on stage if they are awake. Recency fills the rest | none |
| In seq / Out seq | Playhead only walks beats inside the range. Fold still uses history so you know who is awake | 0 / 0 = full tape |
| Scene | Named director preset saved to `scenes.json` | Full tape |

**Shipped in Tools → Demo → settings (clapper).** Scene dropdown in the header. Save scene writes `PUT /api/demo/scenes`.

`GET /api/demo/frame?seq=21&maxPanes=4&featured=ap,ctl-pay` is the same camera for an agent that does not open the SPA.

### Why 9–10 Bots failed

Layout math already returned cells for 9 and 15. The stage still died because:

1. Load blocked on Pi runtime logs.
2. Each pane rendered the Bot’s **entire** transcript as markdown. Ten of those freeze the tab.
3. The stage only lists **open turns**. After `turn.end` a Bot vanishes unless the hold-last-awake path keeps them. Ten spawned Bots are not ten panes unless ten Handles are actually running.

The camera now caps mosaic bubbles at 8 lines (40 in solo/hero) and can pin a cast of 4 or 6 while 16 Bots exist on the roster.

To **show** a 16-Bot desk: max panes 16, or a 9-up with overflow. To **tell** INV-001: featured `books, ap, ctl-pay`, max panes 4, seq 1–21.

---

## Scenes (cuts on disk)

`harness/demo/latest/scenes.json`:

```json
{
  "scenes": [
    {
      "id": "C",
      "title": "INV-001 → ctl-pay",
      "seqFrom": 1,
      "seqTo": 21,
      "featured": ["books", "ap", "ctl-pay"],
      "maxPanes": 4
    }
  ]
}
```

Scenes are **edit notes**, not a second protocol. Changing a scene does not change what Bots did.

Golden’s filled table lives in `runs/golden-20260920-r1/CHAPTERS.md` and is copied into that `scenes.json` after record.

---

## Movie (after the camera)

The Harness will not export MP4. A director still:

1. Picks Tape source, scene, speed (1× for capture, 4× for scrub).
2. Screen-records the Demo stage (or a tight crop of two panes).
3. Optionally records Inspector → Pi RPC for one Handle if a judge must see a tool return.
4. Stitches, cuts silence, adds titles in an editor.
5. Drops the file on the website Videos page (`src` or `embedUrl` in `web/src/data/videos.ts`).

Do not splice Kernel CLI, prove desks, or `--fake` echo workers into that file.

---

## Agent workflow (what you can ask next)

1. `demo meta` — is there a tape, what lastSeq.
2. `demo record` — snapshot now.
3. Open Demo, source Tape, play 4×, note seqs when IDs appear.
4. Set in/out, featured, max panes. Save scene.
5. Play the scene at 1×. Capture.
6. Repeat for other chapters. Concatenate later.

If serve is wedged, skip HTTP: record from the CLI against the instance directory, then restart serve **after** Pi turns drain if you can. Do not start a second office on 8787.

---

## Later overhaul (not this pass)

These are real, and they should not block capturing Golden:

- A scene list that **previews** a still frame per cut.
- Multi-select panes by drag, not only featured chips.
- Record **while** playing (in-app capture). OS screen record is enough for the first videos.
- A cut list that emits an EDL / ffmpeg concat script.
- Live follow-cam: always pin the Bot that just emitted `turn.start`.
- Website Videos cards wired to real files (they are placeholders until MP4s exist).

---

## API

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/demo` | Full bundle. Protocol + clipped transcripts. Not Pi RPC. |
| GET | `/api/demo?source=live\|recording\|auto` | Auto prefers tape if present. |
| GET | `/api/demo/meta` | Cheap. No transcript load. |
| GET | `/api/demo/frame?seq=&maxPanes=&featured=&from=&to=` | One camera frame. |
| POST | `/api/demo/record` | Snapshot live → `demo/latest`. |
| DELETE | `/api/demo/record` | Drop the tape. |
| GET | `/api/demo/scenes` | `{ scenes }` |
| PUT | `/api/demo/scenes` | Persist director cuts. |

CLI: `harness demo record|meta|scenes`.

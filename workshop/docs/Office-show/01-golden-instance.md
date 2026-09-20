# The golden instance

One Harness office instance. One Computer. One `protocol.jsonl`. That is the goose.

---

## Name and place

```
golden-<YYYYMMDD>-r<n>
```

Computer: `.cfo-v2/office/instances/golden-<YYYYMMDD>-r<n>/`

Create from live template **after** prove (and repair) have landed on that template. Clone copies roster, skills, Catalog, Grants, intercept, `data` symlink. Runtime starts empty. That is what you want.

```bash
curl -sS -X POST {URL}/api/office-instances \
  -H 'content-type: application/json' \
  -d '{"name":"golden-20260920-r1"}'
curl -sS -X POST {URL}/api/office-instances/golden-20260920-r1/select
```

Confirm snapshot Computer path ends with `instances/golden-…`. If `currentId` is still `protocol-proof` or a `prove-` desk, stop.

---

## What this desk is not

- Not `live`. You will record here. You may keep serving it for weeks. Do not mix later compile experiments into it.
- Not `prove-…`. QA already happened.
- Not `protocol-proof` / `fresh-protocol`. Historical dirt.
- Not a second World pack. `data/` still points at `world/maximor`.

---

## Serve

Live Pi. Client `-e`. `HARNESS_CLIENT_SKILLS=1`. Sidecar on **this** Computer. No `--fake`.

Full verbosity (`client.json` `transcriptVerbosity: full`, `showToolCalls: true`). The Demo page and Inspector Pi RPC are the proof. Thinking low is fine (`thinkingLevel: low`).

Lazy spawn is fine. The show driver may spawn a Bot before the first Handle so the mosaic has a body.

`autoRoutines: false` stays. The calendar in `03-calendar.md` fires Routines on story-clock Fridays and month-end. Wall-clock weekly would fire at the wrong time while you compress a month into an afternoon.

---

## Do not wipe this desk

Wipe clears inboxes, Handles, transcripts, protocol. Record copies protocol into `harness/demo/latest/` **first**, and that folder survives wipe. Still: do not wipe a successful golden desk. You want to open the live Bots later, not only the slider.

If you must free workers, `POST /api/bots/<id>/kill` is enough. Protocol stays.

If the run HARD-throws: do not wipe-and-continue. New `golden-…-r2`. Leave `r1` on disk with a `FAILED.md` in `docs/Office-show/runs/`.

---

## Logs for the show (not prove classes)

```
docs/Office-show/runs/<instance-id>/
  README.md          story clock, start time, serve URL
  INJECT.md          what you injected, when
  CHAPTERS.md        seq ranges, filled after record
  FAILED.md          only if aborted
```

Do not write HARD/SOFT coverage tables here. That is Office-prove. Here you write: story time, Kernel ids, protocol seq.

---

## Copy the recording off the instance

After `POST /api/demo/record`:

```
{COMPUTER}/harness/demo/latest/
  meta.json
  protocol.jsonl
  transcripts/bot_*.jsonl
  activities/bot_*.jsonl
```

Copy that tree to `docs/Office-show/runs/<instance-id>/recording/` (or another disk you will not wipe). Instance `demo/latest` is the Demo page source. The copy is the backup.

---

## After the show

Keep `office.json` able to select this id. The golden desk is a deliverable. Later compile work uses `live` plus new `prove-` / `golden-r2` clones. Do not select golden as the compile target.

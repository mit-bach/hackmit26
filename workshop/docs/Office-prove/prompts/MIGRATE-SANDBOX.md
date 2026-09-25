# Migrate the fork onto the sandbox layout

Paste this into the debugging chat `a6b2306a-1d5b-4e6a-9bd3-8e9d28b9c786`. Stay on port 8801 and `.cfo-v2/prove-fork/`. Do not POST 8800. Do not edit `.cfo/`, `.cfo-v2/office/instances/golden-20260920-r1/`, or the golden recording. Do not record a Demo tape.

Read these before you move a file:

- `workshop/docs/Office-show/SANDBOX.md` — what the golden month invented, and why that is not a layout.
- `workshop/docs/Office-show/SANDBOX-INIT.md` — which directory holds a packet, a handle, a kernel trace, and how a new slug or a new file type is added.
- `.harness/Harness-v2/src/sandbox.ts` — the write prefixes the running hook enforces.

Initializing a Computer creates `workspace/<slug>/{packets,handles,notes}`, the `runs/` domains, and each Bot memory directory. You do not create those yourself. A write outside `workspace/<slug>/` or that Bot's `memory/` is blocked. Move old files into the directories the reference names, then prove one Bot can finish a real item there.

Restart the 8801 serve after the Harness build so the lease file lists every slug. Confirm `/health` is that fork, `fakeWorkers` false, and `currentId` is not `golden-20260920-r1`.

## Move what the agents invented

Do this on the fork copy only. Leave files in place until the copy has landed, then stop using the old path.

| Old | New |
| --- | --- |
| `workspace/sources/stripe/` | `workspace/stripe/packets/` |
| `workspace/<slug>/<anything-except-packets-handles-notes>/` | `workspace/<slug>/packets/` |
| A second copy of the same plan under both `workspace/pay` and `runs/pay` | Bot text in `workspace/pay/packets/`. Kernel output stays in `runs/pay/`. |

Do not create a new top-level folder. Do not point a packet at `.cfo/runs/`. If a host path is absolute and outside the Computer, change the fork host so the file lands under `runs/` on that Computer.

Update fork `BOT.md` and profile text that tell a Bot to write `workspace/sources`, `workspace/books/masters`, or any path outside `packets/`, `handles/`, and `notes/`. Put the path in the file. Do not leave “make a folder if you need one.”

## Prove one desk

One new fork instance. Creating it builds the desk directories. One Bot, one open item, business English, no Catalog op name in the Wake.

Pass only if:

- The new files are under `workspace/<slug>/packets/` or `handles/`.
- The kernel log shows the finance read the situation needs, and the Wake did not name it.
- A write outside that desk was blocked, which you can see in the Pi tool result, not by deleting a golden file.

If the Bot creates `workspace/sources` or a period folder beside `packets/`, the trial failed. Edit the fork prompt that told it to, and retry on a fresh instance.

Write the instance id, the Wake, and the packet path under `workshop/docs/Office-prove/logs/runs/<id>/`. Do not merge onto the live template in this pass.

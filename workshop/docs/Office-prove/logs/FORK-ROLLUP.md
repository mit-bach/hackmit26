# Fork rollup — isolated prove on 8801

- **Serve:** `http://127.0.0.1:8801/` computer tree `.cfo-v2/prove-fork/`
- **Golden:** `http://127.0.0.1:8800/` `.cfo-v2/office/office.json` `currentId` `golden-20260920-r1` (untouched)
- **Last prove instance:** `prove-20260920-fork-floor-r1` (P0 INTENDED). Next: month instance on this same 8801 office.
- **Isolation:** copied Kernel, bots, constitution, World pack, Client, sidecar.bin, operator-config. Harness `src/` not edited. Live catalog mtime unchanged. Live `extensions.json` still Golden Client.

## Isolation map

| Thing | Golden | Prove-fork |
| --- | --- | --- |
| Port | 8800 | 8801 |
| office.json | `.cfo-v2/office/office.json` | `.cfo-v2/prove-fork/office.json` |
| Kernel source | `.cfo/` | `.cfo-v2/prove-fork/.cfo` (`.venv` symlink only) |
| Skills | live computer + `.cfo/skills` | prove-fork copies |
| BOT.md | `.cfo-v2/office/bots` | `.cfo-v2/prove-fork/bots` |
| World pack | `.cfo-v2/office/world/maximor` | `.cfo-v2/prove-fork/world/maximor` |
| Client extra | live `cfo/extensions/index.ts` | instance `cfo/extensions/index.ts` |
| HARNESS_CONFIG | `~/.harness/config.json` | `.cfo-v2/prove-fork/operator-config.json` |

## Done list (this fork)

- [x] P0 INTENDED on `prove-20260920-fork-floor-r1`
- [ ] P1 intake (month instance)
- [ ] P2–P5 pipes
- [ ] P6 every Computer SKILL.md
- [ ] P7 every granted Catalog op
- [ ] P8 identity survival
- [ ] `$12.40` remains unexplained

Do not overwrite `docs/Office-prove/logs/ROLLUP.md` (show epitaph). Do not POST 8800.

# Fork rollup — isolated prove on 8801

- **Serve:** `http://127.0.0.1:8801/` computer tree `.cfo-v2/prove-fork/`
- **Golden:** `http://127.0.0.1:8800/` `.cfo-v2/office/office.json` `currentId` `golden-20260920-r1` (untouched)
- **Last prove instance:** `prove-20260920-fork-month-r2` (P1-S08 INTENDED after T12 patch). Floor `prove-20260920-fork-floor-r1` is P0 INTENDED. Month-r1 stopped at S08 HARD.
- **Last step:** P1 through S09 on r2. S03/S04/S05/S06/S07/S09 INTENDED. S02 SOFT (duplicate attach, no AP Handle). S16 world SOFT (status line, pair thread empty). S11 transport fail, retry after 8801 restart. Injection still REJECTED.

## Isolation map
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
- [x] P1-S08 injection no longer mints (r2, after fork-only Kernel patch)
- [ ] P1 remainder (list/clean bill/quote already INTENDED on r1; replay S01–S07 on r2)
- [ ] P2–P5 pipes
- [ ] P2–P5 pipes
- [ ] P6 every Computer SKILL.md
- [ ] P7 every granted Catalog op
- [ ] P8 identity survival
- [ ] `$12.40` remains unexplained

Do not overwrite `docs/Office-prove/logs/ROLLUP.md` (show epitaph). Do not POST 8800.

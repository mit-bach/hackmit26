# COMPILE — catalog and grants for `.cfo-v3/cfo`

Child `kestrel`. Mission `prompts/kestrel/0001.md`. Repo `/Users/dominikbach/olympus/hackmit/hackmit26`, branch `cfo-v3`. Not committed.

## Result

The compiler under `.cfo-v3/kernel/compiler` ran against `.cfo-v3/kernel`, and it exited with status 0. It produced 101 catalog ops and 41 Display names. The operational `grants.json` omits `audit.tools.get_audit_ground_truth` for every Display name. That op appears only in `grants.eval.json`, on `Auditor Agent`.

Installed in `.cfo-v3/cfo`:

| File | sha1 | Source |
|---|---|---|
| `catalog.json` | `0ad87efb…d077` | `compile-out-v2overrides/catalog.json` |
| `grants.json` | `0f32d5cd…0626` | `compile-out-v2overrides/grants.json` (the same bytes as `compile-out/grants.json`) |
| `slug-map.json` | `87bf6666…a56` | Not changed. The compiler writes this file only if it is absent. |

The installed `catalog.json` is byte-identical to the copied one. It is now proved to come from the v3 kernel plus one overrides file (see the next section). The installed `grants.json` is new.

## Commands

The compiler always writes `grants.eval.json` in its `--out` directory. It also writes `catalog.overrides.json` there when that file is absent. The mission lets me change only `catalog.json`, `grants.json`, and `slug-map.json` in `.cfo-v3/cfo`. So I compiled into staging directories in this workspace and copied the two product files into place. Before each run, I copied the old `grants.json` into staging, so that the compiler's own grant diff is against the copied file.

The shell was clean: `env -i`, with `PYTHONPATH` set to `.cfo-v3/kernel` only.

Run A: the compiler's built-in overrides (`.cfo-v3/cfo` has no `catalog.overrides.json`):

```bash
cd /Users/dominikbach/olympus/hackmit/hackmit26
K=workshop/grok-workshop/cfo-v3/engineers/kestrel
cp .cfo-v3/cfo/grants.json $K/compile-out/grants.json
env -i HOME=$HOME PATH=/usr/bin:/bin PYTHONPATH=$PWD/.cfo-v3/kernel \
  $PWD/.cfo-v3/kernel/.venv/bin/python -m compiler \
  --kernel $PWD/.cfo-v3/kernel --out $PWD/$K/compile-out --phase operational
```

Exit status 0. Stdout is in `compile-stdout.txt`. Stderr was empty.

Run B: seeded with the v2 Computer's overrides file. That file is used only as compiler input in staging. Nothing at runtime reads it.

```bash
cp .cfo-v2/office/computer/cfo/catalog.overrides.json $K/compile-out-v2overrides/
cp $K/copied/grants.json $K/compile-out-v2overrides/grants.json
env -i HOME=$HOME PATH=/usr/bin:/bin PYTHONPATH=$PWD/.cfo-v3/kernel \
  $PWD/.cfo-v3/kernel/.venv/bin/python -m compiler \
  --kernel $PWD/.cfo-v3/kernel --out $PWD/$K/compile-out-v2overrides --phase operational
```

Exit status 0. Output is in `compile-v2overrides-stdout.txt`.

The compiler source does not read `.cfo` or `.cfo-v2`. A search of `.cfo-v3/kernel/compiler` for `.cfo/`, `.cfo-v2`, and `cfo-v2` found nothing. `repo_root_from` finds the repo by `.harness`, and the default kernel is `.cfo-v3/kernel`. No `BLOCKED.md` was needed.

Stdout highlights, which are the same for both runs:

- `catalog ops: 101`, `display names: 41`
- AP Preparer and AP Approver have different op lists: `AP Preparer == AP Approver: no`.
- `Auditor Agent get_audit_ground_truth operational: omitted`
- `Auditor Agent get_audit_ground_truth evaluation: ['audit.tools.get_audit_ground_truth']`

## Diff against the copied files

The copies are kept in `copied/`.

**grants.json**

- The copied file has 46 Display names. The compiled file has 41. The five removed names are all sample-data agents: `AP/AR Sample Data Agent`, `Audit Controls Sample Data Agent`, `Cash Recon Sample Data Agent`, `Close Sample Data Agent`, and `Reporting Forecasting Sample Data Agent`. In the copied file, each one had `ops: []`, output type `ScenarioPlan`, and `source: sample_data/agents/*.py`. They are gone because the kernel copy leaves out `sample_data`, as `kernel-migration.md` requires. The compiler warns about all five, because `skills/assignments.py` still lists them in `AGENT_SKILLS`.
- The 41 shared names have no op changes (the compiler's diff shows `"ops": {}`). They also have no changes to skills, output type, or source, and their order is the same.
- `audit.tools.get_audit_ground_truth` is absent from both the copied and the compiled operational grants. The file contains zero occurrences of the string.
- Runs A and B produce the same `grants.json`. The larger `grantDenylist` in the v2 overrides removes nothing that the v3 constructors grant.

**catalog.json**

- Both files have the same 101 op ids. No op was added or removed.
- Run B's catalog is byte-identical to the copied catalog.
- Run A differs from the copy in three ops only: `inbox.tools.send_inbox_message`, `inbox.tools.reply_in_thread`, and `inbox.tools.send_office_outbound`. Each one falls from `mutability: write-local, ownerPrefixes: ["runs/inbox/"]` to `mutability: read, ownerPrefixes: []`. The cause is that the compiler's built-in overrides have no inbox entries. The v2 overrides file has them.
- I installed Run B's catalog. Run A would mark three outbound-send ops as read-only and remove their owner prefixes.

## Open item for the owner of `.cfo-v3/cfo`

`.cfo-v3/cfo/catalog.overrides.json` does not exist. The next person to run a plain compile with `--out .cfo-v3/cfo` gets the built-in overrides. That compile writes them to `.cfo-v3/cfo/catalog.overrides.json`, and the three inbox send ops fall back to `read`. To prevent this, someone permitted to write that path must place an overrides file there first. The v2 file is at `.cfo-v2/office/computer/cfo/catalog.overrides.json`, and a staged copy is at `compile-out-v2overrides/catalog.overrides.json`. The v2 file also carries a `comment` and a `consequential` block, which the compiler does not read.

## What this does not prove

- I did not start the sidecar or the serve process against the new files.
- I did not judge whether the operational `Auditor Agent` grant should include `audit.tools.get_planted_reconciliations`. That grant is the same in the copied file and the compiled file.

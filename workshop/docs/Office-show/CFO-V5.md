# CFO v5

`.cfo-v4` is deleted. It used the same layout as `.cfo-v3`: one Computer, one `workspace/` directory, and a folder per Bot inside it. That is a shared tree with a name rule. It is not a sandbox. This file is the plan. Nothing under `.cfo-v5` gets created until this plan is accepted.

Harness stays at `.harness/Harness-v2`. It is not copied into the office. `.cfo`, `.cfo-v2`, and `.cfo-v3` stay on disk and are not the template.

## What failed

`sandbox.ts` says a Bot may write `workspace/<slug>/` and `harness/bots/bot_<slug>/memory/`. Those paths sit on one Computer next to every other Bot, next to `data/`, and next to `harness/roster.json`. The check is a path prefix in the tool hook. `bash` can still read a sibling folder. A shared parent named `workspace` is one directory. Sixteen children of it are not sixteen sandboxes.

v3 and v4 both built that parent. v4 also shipped a kernel of about 1,100 lines, not the finance engine.

## What a sandbox is

A Bot process has one current directory. That directory is the sandbox. The process cannot see another Bot's files by relative path, because those files are not inside its current directory.

Shared facts (invoices, bank lines, catalog) are not files in that directory. The kernel serves them over RPC. The Bot calls a granted op. It does not `ls data/`.

## Layout

```text
.cfo-v5/
  kernel/                         finance engine, not a Bot cwd
  data/                           world pack, no answer keys, not a Bot cwd
  office/
    system.md
    bots/<slug>/BOT.md            identity, one file per Bot
  harness/
    roster.json                   the only roster
  sandboxes/
    <slug>/                       this path is that Bot's cwd
      memory/
      packets/
      handles/
      notes/
```

There is no `workspace/` directory. There is no `roster.json` inside a Bot folder. Memory for `ap` is `sandboxes/ap/memory/`. `email` cannot open that path by walking `../ap`, because the Pi process for `email` is started with cwd `sandboxes/email` and is not given `..`.

`runs/` is kernel output. It lives under `kernel` or at `.cfo-v5/runs` and is not on the Bot cwd. A Bot reads a trace only if a granted op returns it.

## What the kernel is

The kernel is the existing sidecar code that computes amounts, holds, and grants. It is copied from `.cfo` into `.cfo-v5/kernel` by following imports from `python -m cfo_kernel`, not by copying a short rewrite. `PYTHONPATH` is only `.cfo-v5/kernel`. Repo `.cfo` is not on that path.

Answer keys (`expected_results.json`, `expected_outcomes.json`, `holdout/`, `ADVERSARIAL-SCENARIOS.md`) are not in `.cfo-v5`.

## What Harness does

Serve stays:

```bash
node .harness/Harness-v2/dist/src/cli.js serve --computer <computer> --no-open
```

The change in Harness, when implementation starts, is the spawn cwd. For Bot `ap`, cwd is `.cfo-v5/sandboxes/ap`. The Grant door still talks to the sidecar. The sidecar's `--computer` is `.cfo-v5`, not the Bot directory.

`profile:` in the body of a message does not change tools. A step, if one is used, is a header field written by code.

## Done when

- `.cfo-v5/sandboxes/<slug>` exists for each roster slug, and that directory is the only writable tree for that Bot.
- `python -m cfo_kernel --help` runs with `PYTHONPATH=.cfo-v5/kernel`.
- `tools.get_invoice` for `INV-001` returns $12,450.00 from that kernel against `.cfo-v5/data`.
- A file created in `sandboxes/ap/packets/` is not visible as a relative path from a process whose cwd is `sandboxes/email`.

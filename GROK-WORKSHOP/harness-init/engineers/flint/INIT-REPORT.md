# Foundry Pi harness init

Launch directory: `/Users/dominikbach/olympus/hackmit/hackmit26/Harness`

Job: import `https://github.com/mit-bach/foundry-harness` into Harness, then install it so Pi can load the Foundry package.

Status: done. Pi is installed. `pi list` from the launch directory shows the Foundry package.

This report is the durable record. A later child must act from this file, not from chat.

## Name map

Use these names only.

| Name | Object |
| --- | --- |
| Harness | `/Users/dominikbach/olympus/hackmit/hackmit26/Harness` |
| foundry-harness | Git repository `https://github.com/mit-bach/foundry-harness` |
| Foundry package | Pi package installed from Harness by `pi install .` |
| Pi | Binary `/opt/homebrew/bin/pi`, version `0.85.1` |
| launch directory | Harness |
| vendor fallback | `vendor/agent-room.ts` (named in `vendor/SOURCE.txt`, not in the git tree) |
| agent-room pin | npm git dependency `pi-agents-talk-to-each-other` at commit `e4f162a` |

foundry-harness is the same object as Harness after the clone.

## What is true on disk

Harness is a git checkout of foundry-harness.

- Remote: `origin` → `https://github.com/mit-bach/foundry-harness` (fetch and push)
- Branch: `main`, up to date with `origin/main`
- HEAD: `391fb843b98bee2448d4f352c6ea9a7f2bc505c2`
- Subject: `Load agent-room and usage from the real GitHub/npm packages`
- Working tree after clone: clean
- After `npm install`: untracked `package-lock.json` only

These paths exist in Harness:

- `extensions/`
- `skills/`
- `vendor/`
- `foundry-output/`
- `package.json`

`node_modules/` was absent after clone. `package.json` lists runtime dependencies. `npm install` created `node_modules/`. That directory is present now.

Required packages after `npm install`:

- `pi-subagents@0.69.0`
- `@narumitw/pi-usage@0.60.8` with `node_modules/@narumitw/pi-usage/dist/index.ts`
- `pi-agents-talk-to-each-other@0.5.5` at git commit `e4f162a31c3779476dded0957fd1cf95e813aaf3`, with `node_modules/pi-agents-talk-to-each-other/extensions/agent-room/index.ts`
- peer packages `@earendil-works/pi-coding-agent@0.85.1`, `@earendil-works/pi-ai@0.85.1`, `@earendil-works/pi-agent-core@0.85.1`, `@earendil-works/pi-tui@0.85.1`, `typebox@1.3.34`

Pi was already on PATH. Version `0.85.1` meets `SOURCE.md` (`@earendil-works/pi-coding-agent` ≥ 0.85). This job did not reinstall Pi.

Global package `@earendil-works/pi-coding-agent@0.85.1` is installed.

`pi install .` from Harness wrote the Foundry package into user settings at `/Users/dominikbach/.pi/agent/settings.json` as:

```json
"packages": [
    "../../olympus/hackmit/hackmit26/Harness"
]
```

That relative string is relative to `~/.pi/agent`. `pi list` resolves it to `/Users/dominikbach/olympus/hackmit/hackmit26/Harness`.

`pi list` does not show `git:github.com/mit-bach/foundry-harness`. The README names that git source. The operator ordered clone-then-`pi install .`. This job used that path. It did not also install the git source.

Print-mode load from the launch directory ran the Foundry package factories. `foundry-subagents.ts` wrote Harness `.pi/settings.json` (gitignored) with `subagents.disableBuiltins = true`. No `Failed to load extension` line appeared.

Print-mode then failed on the host default model. That is not a Foundry package load failure.

## Commands and observed output

### 1. Empty Harness, Pi on PATH

```bash
ls -la /Users/dominikbach/olympus/hackmit/hackmit26/Harness
which pi
pi --version
```

Observed:

```text
total 0
drwxr-xr-x  2 dominikbach  staff   64 Sep 19 13:36 .
drwxr-xr-x@ 9 dominikbach  staff  288 Sep 19 14:09 ..
/opt/homebrew/bin/pi
0.85.1
```

### 2. Clone foundry-harness into Harness

```bash
git clone https://github.com/mit-bach/foundry-harness /Users/dominikbach/olympus/hackmit/hackmit26/Harness
```

Observed:

```text
Cloning into '/Users/dominikbach/olympus/hackmit/hackmit26/Harness'...
```

### 3. Checkout identity and tree

```bash
cd /Users/dominikbach/olympus/hackmit/hackmit26/Harness
git remote -v
git rev-parse HEAD
git log -1 --oneline
git status
git branch -vv
```

Observed:

```text
origin	https://github.com/mit-bach/foundry-harness (fetch)
origin	https://github.com/mit-bach/foundry-harness (push)
391fb843b98bee2448d4f352c6ea9a7f2bc505c2
391fb84 Load agent-room and usage from the real GitHub/npm packages
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
* main 391fb84 [origin/main] Load agent-room and usage from the real GitHub/npm packages
```

`extensions/`, `skills/`, `vendor/`, `foundry-output/`, and `package.json` existed. `node_modules` was absent.

`git ls-files vendor` showed only:

```text
vendor/AGENT-ROOM-LICENSE
vendor/SOURCE.txt
```

`vendor/agent-room.ts` is not in the git tree.

### 4. Pi and global package before install

```bash
pi list
npm ls -g --depth=0 @earendil-works/pi-coding-agent
```

Observed:

```text
No packages installed.
/opt/homebrew/lib
└── @earendil-works/pi-coding-agent@0.85.1
```

### 5. Install clone dependencies

```bash
cd /Users/dominikbach/olympus/hackmit/hackmit26/Harness
npm install
```

Observed:

```text
npm warn deprecated node-domexception@1.0.0: Use your platform's native DOMException instead
npm warn deprecated node-domexception@1.0.0: Use your platform's native DOMException instead

added 280 packages, and audited 281 packages in 19s

10 packages are looking for funding
  run `npm fund` for details

found 0 vulnerabilities
```

`npm ls --depth=0` after that:

```text
foundry-harness@0.1.0 /Users/dominikbach/olympus/hackmit/hackmit26/Harness
├── @earendil-works/pi-agent-core@0.85.1
├── @earendil-works/pi-ai@0.85.1
├── @earendil-works/pi-coding-agent@0.85.1
├── @earendil-works/pi-tui@0.85.1
├── @narumitw/pi-usage@0.60.8
├── pi-agents-talk-to-each-other@0.5.5 (git+ssh://git@github.com/Timur00Kh/pi-agents-talk-to-each-other.git#e4f162a31c3779476dded0957fd1cf95e813aaf3)
├── pi-subagents@0.69.0
└── typebox@1.3.34
```

### 6. Install the Foundry package into Pi

```bash
cd /Users/dominikbach/olympus/hackmit/hackmit26/Harness
pi install .
```

Observed:

```text
Installing ....
Installed .
```

### 7. Prove the Foundry package from the launch directory

```bash
cd /Users/dominikbach/olympus/hackmit/hackmit26/Harness
which pi
pi --version
pi list
```

Observed:

```text
/opt/homebrew/bin/pi
0.85.1
User packages:
  ../../olympus/hackmit/hackmit26/Harness
    /Users/dominikbach/olympus/hackmit/hackmit26/Harness
```

`pi list --approve` printed the same two package lines.

### 8. Load test (print mode, no TUI)

```bash
cd /Users/dominikbach/olympus/hackmit/hackmit26/Harness
pi -p --no-session --verbose --thinking off "Reply with only the word pong."
```

Observed (exit 1):

```text
Codex error: The 'gpt-5.4-mini' model is not supported when using Codex with a ChatGPT account.
```

No `Failed to load extension` line. After this run, Harness `.pi/settings.json` existed with Foundry subagent settings. That file is gitignored. `foundry-subagents.ts` writes it when the factory runs.

Auth check without credentials:

```bash
pi auth check --provider openai-codex --json --no-refresh
```

Observed:

```text
{"status":"ready","provider":"openai-codex","authType":"oauth"}
```

The host default model is still `openai-codex/gpt-5.4-mini` in `~/.pi/agent/settings.json`. Print-mode used that model and failed. This job did not change host model settings.

## What this job repaired

No clone source edit. No floor-protocol rewrite. No extension redesign.

Install-blocking work was environment only:

1. Clone foundry-harness into Harness (the directory was empty).
2. Run `npm install` in Harness because `node_modules` was absent and `package.json` dependencies require it.
3. Run `pi install .` from Harness.

`vendor/agent-room.ts` is missing. That did not block install or load. `foundry-comms.ts` resolves agent-room from `pi-agents-talk-to-each-other` first. After `npm install`, that file exists. This job did not add the vendor fallback.

## What the prior session left incomplete

`vendor/SOURCE.txt` says `vendor/agent-room.ts` is a verbatim copy of Timur00Kh `extensions/agent-room/index.ts` at commit `e4f162a`. The git tree has the license and the SOURCE note. It does not have `vendor/agent-room.ts`. The live load path is the npm git pin in `node_modules`, not the vendor fallback.

The clone had no `package-lock.json`. `npm install` created one. It is untracked in Harness. This job did not commit it.

`foundry-output/aegis.json` is a sample roster in the clone. This job did not copy it to `foundry-output.json`. That copy is a later project step, not harness init.

README install text prefers `pi list` to show `git:github.com/mit-bach/foundry-harness`. The operator named Harness as the harness location and ordered `pi install .`. The list line is the local Harness path. Both statements are true. They are not the same string.

## What still fails

Print-mode from the launch directory fails on the host default model:

```text
Codex error: The 'gpt-5.4-mini' model is not supported when using Codex with a ChatGPT account.
```

That error is after Foundry package load. It blocks a non-interactive model turn. It does not block `pi list`.

The vendor fallback file `vendor/agent-room.ts` is still missing. If `node_modules/pi-agents-talk-to-each-other` is removed, `foundry-comms.ts` will throw:

```text
agent-room missing. Install github:Timur00Kh/pi-agents-talk-to-each-other#e4f162a (see SOURCE.md).
```

That throw was not observed with `node_modules` present.

## What this job did not prove

- Interactive Pi TUI. The operator forbade a live TUI drive.
- Slash commands `/foundry-roster` and `/foundry-routine` in a session.
- Tools `bot_send_prompt`, `bot_await_turn`, `ask_user`, room tools, memory tools at runtime.
- A completed model reply.
- `pi list` line `git:github.com/mit-bach/foundry-harness`.
- Load after deletion of `node_modules`.
- Any CFO office, bot, room, or routine design.

## Do not

- Do not copy `foundry-output/aegis.json` to `foundry-output.json` as if that were init.
- Do not design the CFO office in this tree.
- Do not drive a live Pi TUI for proof.
- Do not reinstall Pi. Version `0.85.1` meets `SOURCE.md`.
- Do not `git add -A` in `/Users/dominikbach/olympus/hackmit/hackmit26`.
- Do not commit the parent Hack MIT repo.
- Do not print API keys.

## Re-verify

Run these from the launch directory.

1. `cd /Users/dominikbach/olympus/hackmit/hackmit26/Harness`
2. `git remote -v`
3. `git rev-parse HEAD`
4. `test -d extensions -a -d skills -a -d vendor -a -d foundry-output -a -f package.json && echo tree-ok`
5. `test -d node_modules -a -f node_modules/@narumitw/pi-usage/dist/index.ts && echo node_modules-ok`
6. `which pi`
7. `pi --version`
8. `pi list`

Expected `pi --version` output: `0.85.1`

Expected `pi list` output:

```text
User packages:
  ../../olympus/hackmit/hackmit26/Harness
    /Users/dominikbach/olympus/hackmit/hackmit26/Harness
```

## Reinstall the Foundry package

Use this only if `pi list` no longer shows Harness.

1. `cd /Users/dominikbach/olympus/hackmit/hackmit26/Harness`
2. If `node_modules` is absent, run `npm install`
3. `pi install .`
4. `pi list`

If a later child must match the README git source string, run this extra command and quote the new `pi list` line:

```bash
cd /Users/dominikbach/olympus/hackmit/hackmit26/Harness
pi install git:github.com/mit-bach/foundry-harness
pi list
```

This job did not run that extra command.

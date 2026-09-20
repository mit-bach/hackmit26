# STOP

Job: done. Not blocked.

Pi is installed at `/opt/homebrew/bin/pi` as version `0.85.1`. `pi list` from the launch directory shows the Foundry package.

## Product files

These files exist:

1. `/Users/dominikbach/olympus/hackmit/hackmit26/Harness` — git checkout of `https://github.com/mit-bach/foundry-harness` at `391fb843b98bee2448d4f352c6ea9a7f2bc505c2`
2. `/Users/dominikbach/olympus/hackmit/hackmit26/GROK-WORKSHOP/harness-init/engineers/flint/INIT-REPORT.md`
3. `/Users/dominikbach/olympus/hackmit/hackmit26/GROK-WORKSHOP/harness-init/engineers/flint/STOP.md`

## Next operator-visible fact

Launch directory: `/Users/dominikbach/olympus/hackmit/hackmit26/Harness`

`pi list` from that directory:

```text
User packages:
  ../../olympus/hackmit/hackmit26/Harness
    /Users/dominikbach/olympus/hackmit/hackmit26/Harness
```

That line is the local clone, not `git:github.com/mit-bach/foundry-harness`.

Print-mode from the launch directory loads the Foundry package, then fails on host model `openai-codex/gpt-5.4-mini` (`Codex error: The 'gpt-5.4-mini' model is not supported when using Codex with a ChatGPT account.`). That is a model error, not a package-list miss.

Read `INIT-REPORT.md` for commands, quoted output, the missing vendor fallback, and the refuse list.

## Do not do next from this stop

- Do not design the CFO office.
- Do not copy `foundry-output/aegis.json` to `foundry-output.json` as init.
- Do not drive a live Pi TUI as leftover proof.

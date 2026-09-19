import { spawn } from "node:child_process";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

import { awaitTurn } from "./await.ts";
import { initComputer } from "./computer.ts";
import { findHandle } from "./handle.ts";
import { liveStatus } from "./lane-state.ts";
import { extensionEntryPath } from "./pkg.ts";
import { searchProtocol } from "./protocol-log.ts";
import { fireRoutine } from "./routines.ts";
import { searchAgents } from "./search.ts";
import { sendPrompt } from "./send.ts";
import { startServer } from "./server/http.ts";

function takeOption(args: readonly string[], name: string): string | undefined {
  const idx = args.indexOf(name);
  if (idx >= 0) {
    return args[idx + 1];
  }
  const prefixed = args.find((item) => item.startsWith(`${name}=`));
  if (prefixed) {
    return prefixed.slice(name.length + 1);
  }
  return undefined;
}

function positional(args: readonly string[]): string[] {
  const out: string[] = [];
  for (let i = 0; i < args.length; i += 1) {
    const item = args[i];
    if (!item || item.startsWith("--")) {
      if (item === "--computer" || item === "--port") {
        i += 1;
      }
      continue;
    }
    out.push(item);
  }
  return out;
}

function hasFlag(args: readonly string[], name: string): boolean {
  return args.includes(name);
}

export async function runCli(argv: string[]): Promise<void> {
  const [cmd, ...rest] = argv;
  const computerRoot = resolve(
    takeOption(rest, "--computer") ?? process.env.HARNESS_COMPUTER ?? process.cwd(),
  );

  if (!cmd || cmd === "help" || cmd === "--help") {
    process.stdout.write(`harness — named Bots on a shared Computer

Commands:
  serve [--computer DIR] [--port N] [--no-workers] [--lazy] [--fake]
  bot <slug> [--computer DIR]
  send <slug> <prompt...> [--computer DIR]
  stop <slug> [--computer DIR]
  await <handleId> [--computer DIR]
  handle <handleId> [--computer DIR]
  roster [--computer DIR]
  protocol [--computer DIR] [query]
  routine <name> [--computer DIR]
  floor [--computer DIR]

The Operator surface is HTTP JSON on loopback. There is no product UI here.
`);
    return;
  }

  if (cmd === "serve") {
    const port = Number(takeOption(rest, "--port") ?? "8787");
    const started = await startServer({
      computerRoot,
      port: Number.isFinite(port) ? port : 8787,
      workers: !hasFlag(rest, "--no-workers"),
      lazyWorkers: hasFlag(rest, "--lazy"),
      fakeWorkers: hasFlag(rest, "--fake"),
    });
    process.stdout.write(`harness listening ${started.url} computer=${computerRoot}\n`);
    const stop = (): void => {
      void started.stop().then(() => {
        process.exit(0);
      });
    };
    process.on("SIGINT", stop);
    process.on("SIGTERM", stop);
    await new Promise(() => {
      // keep the process up
    });
    return;
  }

  if (cmd === "bot") {
    const slug = positional(rest)[0];
    if (!slug) {
      throw new Error("usage: harness bot <slug>");
    }
    initComputer(computerRoot);
    const child = spawn("pi", ["-e", extensionEntryPath(), "--name", slug], {
      cwd: computerRoot,
      env: { ...process.env, HARNESS_BOT: slug, HARNESS_COMPUTER: computerRoot },
      stdio: "inherit",
    });
    await new Promise<void>((resolvePromise, reject) => {
      child.on("exit", (code) => {
        if (code === 0 || code === null) {
          resolvePromise();
          return;
        }
        reject(new Error(`pi exited ${code}`));
      });
      child.on("error", reject);
    });
    return;
  }

  if (cmd === "send") {
    const parts = positional(rest);
    const slug = parts[0];
    if (!slug) {
      throw new Error("usage: harness send <slug> <prompt>");
    }
    initComputer(computerRoot);
    const result = sendPrompt({
      computerRoot,
      from: "operator",
      to: slug,
      prompt: parts.slice(1).join(" ") || "(empty)",
      kind: "user_dm",
    });
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return;
  }

  if (cmd === "stop") {
    const slug = positional(rest)[0];
    if (!slug) {
      throw new Error("usage: harness stop <slug>");
    }
    initComputer(computerRoot);
    const result = sendPrompt({
      computerRoot,
      from: "operator",
      to: slug,
      prompt: "Stop now",
      kind: "user_stop",
      onBusy: "supersede",
    });
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return;
  }

  if (cmd === "await") {
    const handleId = positional(rest)[0];
    if (!handleId) {
      throw new Error("usage: harness await <handleId>");
    }
    const outcome = await awaitTurn(computerRoot, handleId, { timeoutMs: 120_000 });
    process.stdout.write(`${JSON.stringify(outcome, null, 2)}\n`);
    return;
  }

  if (cmd === "roster") {
    initComputer(computerRoot);
    process.stdout.write(`${JSON.stringify(searchAgents(computerRoot, ""), null, 2)}\n`);
    return;
  }

  if (cmd === "protocol") {
    initComputer(computerRoot);
    const query = positional(rest).join(" ");
    process.stdout.write(`${JSON.stringify(searchProtocol(computerRoot, query), null, 2)}\n`);
    return;
  }

  if (cmd === "routine") {
    const name = positional(rest)[0];
    if (!name) {
      throw new Error("usage: harness routine <name>");
    }
    initComputer(computerRoot);
    process.stdout.write(`${JSON.stringify(fireRoutine(computerRoot, name), null, 2)}\n`);
    return;
  }

  if (cmd === "floor") {
    const roster = initComputer(computerRoot);
    process.stdout.write(`Computer: ${computerRoot}\n`);
    process.stdout.write(`System: ${roster.system}\n`);
    process.stdout.write("Start one pane per Bot:\n");
    for (const bot of roster.bots) {
      process.stdout.write(
        `  HARNESS_BOT=${bot.slug} HARNESS_COMPUTER=${computerRoot} pi -e ${extensionEntryPath()} --name ${bot.slug}\n`,
      );
      process.stdout.write(`    status now: ${liveStatus(computerRoot, bot.id)}\n`);
    }
    process.stdout.write("Or headless: harness serve --computer <dir> [--fake]\n");
    return;
  }

  if (cmd === "handle") {
    const id = positional(rest)[0];
    if (!id) {
      throw new Error("usage: harness handle <handleId>");
    }
    process.stdout.write(`${JSON.stringify(findHandle(computerRoot, id), null, 2)}\n`);
    return;
  }

  throw new Error(`unknown command ${cmd}`);
}

function isCliEntry(): boolean {
  const invoked = process.argv[1];
  if (!invoked) {
    return false;
  }
  return import.meta.url === pathToFileURL(resolve(invoked)).href;
}

if (isCliEntry()) {
  try {
    await runCli(process.argv.slice(2));
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    process.stderr.write(`${message}\n`);
    process.exitCode = 1;
  }
}

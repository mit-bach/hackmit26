import { spawn, type ChildProcess } from "node:child_process";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";

import { pendingCount } from "../inbox.ts";
import { liveStatus } from "../lane-state.ts";
import { extensionEntryPath } from "../pkg.ts";
import { loadRoster } from "../roster.ts";
import { cadenceToMs, fireRoutine } from "../routines.ts";

export interface SupervisorOptions {
  readonly computerRoot: string;
  readonly lazy?: boolean;
}

export interface Supervisor {
  stop: () => Promise<void>;
}

function resolvePiCli(): string | undefined {
  try {
    const require = createRequire(import.meta.url);
    const pkg = require.resolve("@earendil-works/pi-coding-agent/package.json");
    return join(dirname(pkg), "dist", "bundle", "cli.js");
  } catch {
    return undefined;
  }
}

function spawnBot(computerRoot: string, slug: string, cliPath: string): ChildProcess {
  const child = spawn(process.execPath, [cliPath, "--mode", "rpc", "-e", extensionEntryPath(), "--name", slug], {
    cwd: computerRoot,
    env: {
      ...process.env,
      HARNESS_BOT: slug,
      HARNESS_COMPUTER: computerRoot,
    },
    stdio: ["pipe", "pipe", "pipe"],
  });
  return child;
}

export async function startSupervisor(options: SupervisorOptions): Promise<Supervisor> {
  const cliPath = resolvePiCli();
  const children = new Map<string, ChildProcess>();
  const timers: ReturnType<typeof setInterval>[] = [];
  const roster = loadRoster(options.computerRoot);

  const ensure = (slug: string): void => {
    if (!cliPath) {
      return;
    }
    const existing = children.get(slug);
    if (existing && existing.exitCode === null && !existing.killed) {
      return;
    }
    const child = spawnBot(options.computerRoot, slug, cliPath);
    children.set(slug, child);
    child.on("exit", () => {
      children.delete(slug);
    });
  };

  if (!options.lazy) {
    for (const bot of roster.bots) {
      ensure(bot.slug);
    }
  }

  const watch = setInterval(() => {
    for (const bot of roster.bots) {
      const status = liveStatus(options.computerRoot, bot.id);
      const pending = pendingCount(options.computerRoot, bot.id);
      if (status === "offline" && (pending > 0 || !options.lazy)) {
        ensure(bot.slug);
      }
    }
  }, 2000);
  timers.push(watch);

  for (const routine of roster.routines) {
    const ms = cadenceToMs(routine.cadence);
    if (!ms) {
      continue;
    }
    const timer = setInterval(() => {
      try {
        fireRoutine(options.computerRoot, routine.name);
      } catch {
        // keep the supervisor up
      }
    }, ms);
    timers.push(timer);
  }

  return {
    stop: async (): Promise<void> => {
      for (const timer of timers) {
        clearInterval(timer);
      }
      for (const child of children.values()) {
        child.kill("SIGTERM");
      }
      children.clear();
    },
  };
}

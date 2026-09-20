import { spawn, type ChildProcess } from "node:child_process";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";

import { pendingCount } from "../inbox.ts";
import { liveStatus } from "../lane-state.ts";
import { piSessionDir } from "../paths.ts";
import { extensionEntryPath, extraExtensionArgs } from "../pkg.ts";
import { findBot, loadRoster } from "../roster.ts";
import { cadenceToMs, fireRoutine } from "../routines.ts";
import { ensureDir } from "../fs.ts";
import type { EventBus } from "./bus.ts";
import { loadOperatorConfig, piEnvFromConfig, type OperatorConfig } from "./operator-config.ts";

export interface SupervisorOptions {
  readonly computerRoot: string;
  readonly lazy?: boolean;
  readonly bus?: EventBus;
  readonly config?: OperatorConfig;
}

export interface SessionInfo {
  readonly slug: string;
  readonly botId: string;
  readonly pid?: number;
  readonly alive: boolean;
  readonly sessionDir: string;
}

export interface Supervisor {
  stop: () => Promise<void>;
  ensure: (slug: string) => void;
  stopBot: (slug: string) => void;
  sessions: () => SessionInfo[];
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

function foldRpcChunk(bus: EventBus | undefined, slug: string, botId: string, raw: unknown): void {
  if (!bus || typeof raw !== "object" || raw === null) {
    return;
  }
  const rec = raw as Record<string, unknown>;
  bus.publish({
    kind: "runtime",
    slug,
    botId,
    event: rec,
  });
  const type = typeof rec.type === "string" ? rec.type : "";
  const nested =
    rec.event && typeof rec.event === "object" && rec.event !== null
      ? (rec.event as Record<string, unknown>)
      : rec;
  const nestedType = typeof nested.type === "string" ? nested.type : type;
  let text = "";
  if (typeof nested.text === "string") {
    text = nested.text;
  } else if (typeof nested.delta === "string") {
    text = nested.delta;
  } else if (typeof nested.message === "string") {
    text = nested.message;
  }
  if (nestedType.includes("error") || type === "error") {
    const message = typeof nested.message === "string" ? nested.message : JSON.stringify(nested).slice(0, 240);
    bus.publish({
      kind: "message",
      threadId: botId,
      message: {
        id: `rpc-${Date.now()}`,
        at: new Date().toISOString(),
        role: "system",
        kind: "activity",
        text: message,
      },
    });
    return;
  }
  if (text.length > 0 && (nestedType.includes("text") || nestedType.includes("assistant") || nestedType === "agent_end")) {
    bus.publish({
      kind: "message",
      threadId: botId,
      message: {
        id: `rpc-${Date.now()}`,
        at: new Date().toISOString(),
        role: "bot",
        kind: nestedType.includes("tool") ? "activity" : "text",
        text,
      },
    });
  }
}

function attachStdout(child: ChildProcess, slug: string, botId: string, bus: EventBus | undefined): void {
  let buf = "";
  child.stdout?.on("data", (chunk: Buffer | string) => {
    buf += typeof chunk === "string" ? chunk : chunk.toString("utf8");
    for (;;) {
      const nl = buf.indexOf("\n");
      if (nl < 0) {
        break;
      }
      const line = buf.slice(0, nl).replace(/\r$/, "");
      buf = buf.slice(nl + 1);
      if (line.trim().length === 0) {
        continue;
      }
      try {
        foldRpcChunk(bus, slug, botId, JSON.parse(line) as unknown);
      } catch {
        // Non-JSON diagnostic lines from Pi are ignored.
      }
    }
  });
  child.stderr?.on("data", (chunk: Buffer | string) => {
    const text = (typeof chunk === "string" ? chunk : chunk.toString("utf8")).trim();
    if (text.length === 0) {
      return;
    }
    bus?.publish({
      kind: "runtime",
      slug,
      botId,
      event: { type: "stderr", text: text.slice(0, 500) },
    });
  });
}

function spawnBot(
  computerRoot: string,
  slug: string,
  botId: string,
  cliPath: string,
  env: NodeJS.ProcessEnv,
  bus: EventBus | undefined,
): ChildProcess {
  const sessionDir = piSessionDir(computerRoot, botId);
  ensureDir(sessionDir);
  const args = [
    cliPath,
    "--mode",
    "rpc",
    "-e",
    extensionEntryPath(),
    ...extraExtensionArgs(env),
    "--name",
    slug,
    "--session-dir",
    sessionDir,
  ];
  if (env.HARNESS_PI_PROVIDER) {
    args.push("--provider", env.HARNESS_PI_PROVIDER);
  }
  if (env.HARNESS_PI_MODEL) {
    args.push("--model", env.HARNESS_PI_MODEL);
  }
  const child = spawn(process.execPath, args, {
    cwd: computerRoot,
    env: {
      ...env,
      HARNESS_BOT: slug,
      HARNESS_COMPUTER: computerRoot,
    },
    stdio: ["pipe", "pipe", "pipe"],
  });
  attachStdout(child, slug, botId, bus);
  return child;
}

export async function startSupervisor(options: SupervisorOptions): Promise<Supervisor> {
  const cliPath = resolvePiCli();
  const children = new Map<string, ChildProcess>();
  const timers: ReturnType<typeof setInterval>[] = [];
  const config = options.config ?? loadOperatorConfig();
  const env = piEnvFromConfig(config);
  const bus = options.bus;

  const rosterOf = (): ReturnType<typeof loadRoster> => loadRoster(options.computerRoot);

  const ensure = (slug: string): void => {
    if (!cliPath) {
      return;
    }
    const roster = rosterOf();
    const bot = findBot(roster, slug);
    if (!bot) {
      return;
    }
    const existing = children.get(slug);
    if (existing && existing.exitCode === null && !existing.killed) {
      return;
    }
    const child = spawnBot(options.computerRoot, slug, bot.id, cliPath, env, bus);
    children.set(slug, child);
    bus?.publish({ kind: "sessions", sessions: sessions() });
    child.on("exit", () => {
      children.delete(slug);
      bus?.publish({ kind: "sessions", sessions: sessions() });
    });
  };

  const stopBot = (slug: string): void => {
    const child = children.get(slug);
    if (!child) {
      return;
    }
    child.kill("SIGTERM");
    children.delete(slug);
    bus?.publish({ kind: "sessions", sessions: sessions() });
  };

  const sessions = (): SessionInfo[] => {
    const roster = rosterOf();
    return roster.bots.map((bot) => {
      const child = children.get(bot.slug);
      const alive = child !== undefined && child.exitCode === null && !child.killed;
      return {
        slug: bot.slug,
        botId: bot.id,
        pid: child?.pid,
        alive,
        sessionDir: piSessionDir(options.computerRoot, bot.id),
      };
    });
  };

  if (!options.lazy) {
    for (const bot of rosterOf().bots) {
      ensure(bot.slug);
    }
  }

  const watch = setInterval(() => {
    for (const bot of rosterOf().bots) {
      const status = liveStatus(options.computerRoot, bot.id);
      const pending = pendingCount(options.computerRoot, bot.id);
      if (status === "offline" && (pending > 0 || !options.lazy)) {
        ensure(bot.slug);
      }
    }
  }, 2000);
  timers.push(watch);

  for (const routine of rosterOf().routines) {
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
    ensure,
    stopBot,
    sessions,
  };
}

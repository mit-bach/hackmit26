import { spawn, type ChildProcess } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { applyAttachEnv } from "../client-attach.ts";
import { applyClientEnv, loadClientRuntime, overlayOperatorConfig } from "../client-runtime.ts";
import { appendJsonlAtomic, ensureDir } from "../fs.ts";
import { pendingCount } from "../inbox.ts";
import { liveStatus } from "../lane-state.ts";
import { piRpcLogPath, piRuntimePath, piSessionDir } from "../paths.ts";
import { extensionEntryPath, extraExtensionArgs } from "../pkg.ts";
import { findBot, loadRoster } from "../roster.ts";
import { sandboxesEnabled, seatbeltProfilePath } from "../seatbelt.ts";
import { cadenceToMs, fireRoutine } from "../routines.ts";
import type { EventBus } from "./bus.ts";
import { ombAdoptLeaf, ombChainParent } from "./omb-compat.ts";
import { loadOperatorConfig, piEnvFromConfig, type OperatorConfig } from "./operator-config.ts";
import { foldPiRpc, type PiActivityChip, type PiRuntimeEvent } from "./pi-runtime.ts";

export interface SupervisorOptions {
  readonly computerRoot: string;
  readonly lazy?: boolean;
  readonly autoRoutines?: boolean;
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
    const resolved = import.meta.resolve("@earendil-works/pi-coding-agent");
    const cli = join(dirname(fileURLToPath(resolved)), "bundle", "cli.js");
    return existsSync(cli) ? cli : undefined;
  } catch {
    return undefined;
  }
}

const eventSeq = new Map<string, number>();
/** One chip id per Kernel/Pi toolCallId so start and end patch the same row. */
const publishedToolIds = new Map<string, Set<string>>();

function nextEventId(botId: string): string {
  const n = (eventSeq.get(botId) ?? 0) + 1;
  eventSeq.set(botId, n);
  return `pi-${botId}-${n}`;
}

function sendRpc(child: ChildProcess, command: Record<string, unknown>): void {
  const stdin = child.stdin;
  if (!stdin || stdin.destroyed) {
    return;
  }
  stdin.write(`${JSON.stringify(command)}\n`);
}

export function piModelArg(model: string | undefined, thinking: string | undefined): string | undefined {
  const trimmed = model?.trim();
  if (!trimmed) {
    return undefined;
  }
  if (trimmed.includes(":") || !thinking?.trim()) {
    return trimmed;
  }
  return `${trimmed}:${thinking.trim()}`;
}

function publishRuntime(
  computerRoot: string,
  bus: EventBus | undefined,
  slug: string,
  botId: string,
  event: PiRuntimeEvent,
): void {
  appendJsonlAtomic(piRuntimePath(computerRoot, botId), event);
  bus?.publish({ kind: "runtime", slug, botId, event });
}

function toolChipMessageId(chipId: string): string {
  return `tool-${chipId}`;
}

function publishActivity(
  bus: EventBus | undefined,
  _computerRoot: string,
  botId: string,
  chip: PiActivityChip,
): void {
  if (!bus) {
    return;
  }
  const id = toolChipMessageId(chip.id);
  const seen = publishedToolIds.get(botId) ?? new Set<string>();
  const exists = seen.has(id);
  const parentId = exists ? undefined : ombChainParent(botId);
  if (!exists) {
    ombAdoptLeaf(botId, id);
    seen.add(id);
    publishedToolIds.set(botId, seen);
  }
  bus.publish({
    kind: exists ? "message.patch" : "message",
    threadId: botId,
    message: {
      id,
      role: "bot",
      kind: "activity",
      text: chip.spoken,
      at: Date.now(),
      ...(parentId !== undefined ? { parentId } : {}),
      tool: {
        name: chip.name,
        spoken: chip.spoken,
        ...(chip.ok !== undefined ? { ok: chip.ok } : {}),
        ...(chip.summary ? { summary: chip.summary } : {}),
        ...(chip.input ? { input: chip.input } : {}),
        ...(chip.output ? { output: chip.output } : {}),
      },
    },
  });
}

function foldRpcChunk(
  computerRoot: string,
  bus: EventBus | undefined,
  slug: string,
  botId: string,
  raw: unknown,
): void {
  appendJsonlAtomic(piRpcLogPath(computerRoot, botId), raw);
  const folded = foldPiRpc(raw, {
    botId,
    slug,
    now: (): string => new Date().toISOString(),
    nextId: (): string => nextEventId(botId),
  });
  for (const event of folded.events) {
    publishRuntime(computerRoot, bus, slug, botId, event);
  }
  if (folded.activity) {
    publishActivity(bus, computerRoot, botId, folded.activity);
  }
}

function attachStdout(
  computerRoot: string,
  child: ChildProcess,
  slug: string,
  botId: string,
  bus: EventBus | undefined,
): void {
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
        foldRpcChunk(computerRoot, bus, slug, botId, JSON.parse(line) as unknown);
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
    publishRuntime(computerRoot, bus, slug, botId, {
      eventId: nextEventId(botId),
      provider: "pi",
      threadId: botId,
      createdAt: new Date().toISOString(),
      type: "runtime.error",
      message: text.slice(0, 500),
      raw: { source: "pi-stderr", payload: text.slice(0, 500) },
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
  const model = piModelArg(env.HARNESS_PI_MODEL, env.HARNESS_PI_THINKING);
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
  if (model) {
    args.push("--model", model);
  }
  const root = resolve(computerRoot);
  const jailed = sandboxesEnabled(root);
  const cwd = jailed ? join(root, "sandboxes", slug) : root;
  const childEnv = {
    ...env,
    HARNESS_BOT: slug,
    HARNESS_COMPUTER: root,
  };
  let child: ChildProcess;
  if (jailed) {
    if (process.platform !== "darwin") {
      throw new Error("sandboxes/ jail requires sandbox-exec on darwin");
    }
    const profile = seatbeltProfilePath(root, slug, botId);
    child = spawn("sandbox-exec", ["-f", profile, "--", process.execPath, ...args], {
      cwd,
      env: childEnv,
      stdio: ["pipe", "pipe", "pipe"],
    });
  } else {
    child = spawn(process.execPath, args, {
      cwd,
      env: childEnv,
      stdio: ["pipe", "pipe", "pipe"],
    });
  }
  attachStdout(computerRoot, child, slug, botId, bus);
  const thinking = env.HARNESS_PI_THINKING?.trim();
  if (thinking) {
    sendRpc(child, { type: "set_thinking_level", level: thinking });
  }
  return child;
}

export async function startSupervisor(options: SupervisorOptions): Promise<Supervisor> {
  eventSeq.clear();
  publishedToolIds.clear();
  const cliPath = resolvePiCli();
  const children = new Map<string, ChildProcess>();
  const timers: ReturnType<typeof setInterval>[] = [];
  const bus = options.bus;

  const rosterOf = (): ReturnType<typeof loadRoster> => loadRoster(options.computerRoot);
  const envFor = (): NodeJS.ProcessEnv => {
    const client = loadClientRuntime(options.computerRoot);
    const live = overlayOperatorConfig(
      options.computerRoot,
      options.config ?? loadOperatorConfig(),
      client,
    );
    return applyClientEnv(
      applyAttachEnv(piEnvFromConfig(live), options.computerRoot, live),
      options.computerRoot,
      client,
    );
  };

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
    const child = spawnBot(options.computerRoot, slug, bot.id, cliPath, envFor(), bus);
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
    try {
      for (const bot of rosterOf().bots) {
        const status = liveStatus(options.computerRoot, bot.id);
        const pending = pendingCount(options.computerRoot, bot.id);
        if (status === "offline" && (pending > 0 || !options.lazy)) {
          ensure(bot.slug);
        }
      }
    } catch {
      // keep the supervisor up if roster.json is mid-write
    }
  }, 2000);
  timers.push(watch);

  if (options.autoRoutines === true) {
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

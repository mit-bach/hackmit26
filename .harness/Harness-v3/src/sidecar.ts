import { spawn, type ChildProcess } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";

import type { ClientRuntime, ClientSidecarSpec } from "./client-runtime.ts";
import { resolveClientPath } from "./client-runtime.ts";
import { sleep } from "./sleep.ts";

export interface SidecarHandle {
  readonly port: number;
  readonly pid?: number;
  readonly owned: boolean;
  stop: () => Promise<void>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function readSidecarPort(computerRoot: string, spec: ClientSidecarSpec): number | undefined {
  const path = resolveClientPath(computerRoot, spec.portFile);
  if (!existsSync(path)) {
    return undefined;
  }
  const raw = readFileSync(path, "utf8").trim();
  const asNumber = Number(raw);
  if (Number.isFinite(asNumber) && asNumber > 0) {
    return asNumber;
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    if (isRecord(parsed) && typeof parsed.port === "number" && parsed.port > 0) {
      return parsed.port;
    }
  } catch {
    return undefined;
  }
  return undefined;
}

export async function sidecarHealthy(port: number): Promise<boolean> {
  try {
    const response = await fetch(`http://127.0.0.1:${port}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

async function waitForPort(
  computerRoot: string,
  spec: ClientSidecarSpec,
  stderr: { text: string },
): Promise<number> {
  const deadline = Date.now() + spec.readyTimeoutMs;
  while (Date.now() < deadline) {
    const port = readSidecarPort(computerRoot, spec);
    if (port !== undefined && (await sidecarHealthy(port))) {
      return port;
    }
    await sleep(100);
  }
  const extra = stderr.text.trim().length > 0 ? `: ${stderr.text.trim().slice(0, 500)}` : "";
  throw new Error(`sidecar did not publish a healthy port at ${spec.portFile}${extra}`);
}

export function applyServeComputerEnv(computerRoot: string, env: NodeJS.ProcessEnv = process.env): void {
  env.HARNESS_COMPUTER = resolve(computerRoot);
}

function sidecarEnv(computerRoot: string, runtime: ClientRuntime, spec: ClientSidecarSpec): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = { ...process.env };
  delete env.HARNESS_BOT;
  env.HARNESS_COMPUTER = computerRoot;
  env.SIDECAR_PORT_FILE = resolveClientPath(computerRoot, spec.portFile);
  if (runtime.evalPhase) {
    env.HARNESS_EVAL_PHASE = runtime.evalPhase;
  }
  return env;
}

function spawnOwned(
  computerRoot: string,
  spec: ClientSidecarSpec,
  runtime: ClientRuntime,
  stderr: { text: string },
): ChildProcess {
  const command = resolveClientPath(computerRoot, spec.command);
  if (!existsSync(command) && spec.command !== process.execPath) {
    throw new Error(`sidecar command missing: ${command}`);
  }
  const useShell = command.endsWith(".sh") || command.endsWith(".bash");
  const useNode = command.endsWith(".mjs") || command.endsWith(".cjs") || command.endsWith(".js");
  const file = useShell ? "/bin/bash" : useNode ? process.execPath : command;
  const argv = useShell ? [command, ...spec.args] : useNode ? [command, ...spec.args] : [...spec.args];
  const child = spawn(file, argv, {
    cwd: computerRoot,
    env: sidecarEnv(computerRoot, runtime, spec),
    stdio: ["ignore", "pipe", "pipe"],
  });
  child.stderr?.on("data", (chunk: Buffer | string) => {
    const text = typeof chunk === "string" ? chunk : chunk.toString("utf8");
    stderr.text += text;
    if (stderr.text.length > 4000) {
      stderr.text = stderr.text.slice(-2000);
    }
  });
  return child;
}

async function stopChild(child: ChildProcess): Promise<void> {
  if (child.exitCode !== null || child.killed) {
    return;
  }
  child.kill("SIGTERM");
  const deadline = Date.now() + 1500;
  while (Date.now() < deadline && child.exitCode === null && !child.killed) {
    await sleep(50);
  }
  if (child.exitCode === null && !child.killed) {
    child.kill("SIGKILL");
  }
}

export async function startSidecar(
  computerRoot: string,
  runtime: ClientRuntime,
): Promise<SidecarHandle | undefined> {
  const spec = runtime.sidecar;
  if (!spec) {
    return undefined;
  }
  const existing = readSidecarPort(computerRoot, spec);
  if (existing !== undefined && (await sidecarHealthy(existing))) {
    return {
      port: existing,
      owned: false,
      stop: async (): Promise<void> => {
        // Adopted a sidecar this process did not spawn.
      },
    };
  }
  const stderr = { text: "" };
  const child = spawnOwned(computerRoot, spec, runtime, stderr);
  try {
    const port = await waitForPort(computerRoot, spec, stderr);
    return {
      port,
      pid: child.pid,
      owned: true,
      stop: async (): Promise<void> => {
        await stopChild(child);
      },
    };
  } catch (error) {
    await stopChild(child);
    throw error;
  }
}

export function resolveSidecarCommand(computerRoot: string, spec: ClientSidecarSpec): string {
  return resolve(computerRoot, spec.command);
}

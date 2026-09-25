import { existsSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

import { ensureDir } from "./fs.ts";
import { loadLayout } from "./layout.ts";
import { persistProtocolCard } from "./protocol-card.ts";
import { loadRoster } from "./roster.ts";
import {
  approvalDir,
  botDir,
  handleDir,
  inboxPath,
  lanePath,
  leaseDir,
  memoryDir,
  memoryFile,
  piSessionDir,
  protocolLogPath,
  piRpcLogPath,
  piRuntimePath,
  receiptDir,
  roomDir,
  roomLogPath,
  seqPath,
  threadsDir,
  transcriptPath,
} from "./paths.ts";

export interface WipeOptions {
  readonly keepMemory?: boolean;
  readonly keepSidecarPort?: boolean;
  readonly wipeRuns?: boolean;
}

export interface WipeReport {
  readonly computerRoot: string;
  readonly bots: number;
  readonly rooms: number;
  readonly cleared: readonly string[];
}

function clearTree(path: string, cleared: string[], label: string): void {
  if (!existsSync(path)) {
    return;
  }
  rmSync(path, { recursive: true, force: true });
  cleared.push(label);
}

function resetFile(path: string, cleared: string[], label: string): void {
  ensureDir(dirname(path));
  writeFileSync(path, "", "utf8");
  cleared.push(label);
}

function emptyDir(path: string, cleared: string[], label: string): void {
  if (!existsSync(path)) {
    ensureDir(path);
    return;
  }
  for (const name of readdirSync(path)) {
    rmSync(join(path, name), { recursive: true, force: true });
  }
  cleared.push(label);
}

function kernelRuntime(computerRoot: string, options: WipeOptions, cleared: string[]): void {
  const layout = loadLayout(computerRoot);
  for (const rel of layout.wipe) {
    if (options.keepSidecarPort && rel.endsWith("kernel.port")) continue;
    const path = join(computerRoot, rel);
    if (!existsSync(path)) continue;
    if (rel.endsWith(".jsonl") || rel.endsWith(".port")) {
      resetFile(path, cleared, rel);
      continue;
    }
    emptyDir(path, cleared, rel);
  }
}

function wipeRunsTree(computerRoot: string, cleared: string[]): void {
  const runs = join(computerRoot, "runs");
  if (!existsSync(runs)) {
    return;
  }
  emptyDir(runs, cleared, "runs");
}

/**
 * Drop session runtime on this Computer. Roster, skills, Catalog, Grants,
 * intercept, client.json, workspace files, and harness/demo recordings stay.
 * Benchmarks start here. Record a demo before wipe if the Operator still
 * needs to replay this session.
 */
export function wipeRuntime(computerRoot: string, options: WipeOptions = {}): WipeReport {
  const roster = loadRoster(computerRoot);
  const cleared: string[] = [];
  resetFile(protocolLogPath(computerRoot), cleared, "harness/protocol.jsonl");
  writeFileSync(seqPath(computerRoot), "0\n", "utf8");
  cleared.push("harness/seq");
  emptyDir(approvalDir(computerRoot), cleared, "harness/approvals");
  emptyDir(receiptDir(computerRoot), cleared, "harness/receipts");
  emptyDir(leaseDir(computerRoot), cleared, "harness/leases");
  emptyDir(threadsDir(computerRoot), cleared, "harness/threads");
  for (const bot of roster.bots) {
    resetFile(inboxPath(computerRoot, bot.id), cleared, `bots/${bot.slug}/inbox`);
    resetFile(transcriptPath(computerRoot, bot.id), cleared, `bots/${bot.slug}/transcript`);
    resetFile(piRuntimePath(computerRoot, bot.id), cleared, `bots/${bot.slug}/pi-runtime`);
    resetFile(piRpcLogPath(computerRoot, bot.id), cleared, `bots/${bot.slug}/pi-rpc`);
    if (existsSync(lanePath(computerRoot, bot.id))) {
      rmSync(lanePath(computerRoot, bot.id), { force: true });
      cleared.push(`bots/${bot.slug}/lane`);
    }
    emptyDir(handleDir(computerRoot, bot.id), cleared, `bots/${bot.slug}/handles`);
    clearTree(piSessionDir(computerRoot, bot.id), cleared, `bots/${bot.slug}/pi-session`);
    ensureDir(piSessionDir(computerRoot, bot.id));
    ensureDir(handleDir(computerRoot, bot.id));
    ensureDir(botDir(computerRoot, bot.id));
    persistProtocolCard(computerRoot, bot.id);
    if (!options.keepMemory) {
      const memRoot = memoryDir(computerRoot, bot.id);
      if (existsSync(memRoot)) {
        for (const name of readdirSync(memRoot)) {
          if (name === "MEMORY.md") {
            continue;
          }
          rmSync(join(memRoot, name), { recursive: true, force: true });
        }
        writeFileSync(
          memoryFile(computerRoot, bot.id),
          `# ${bot.name}\n\nStanding notes for this Bot. Not shared.\n`,
          "utf8",
        );
        cleared.push(`bots/${bot.slug}/memory`);
      }
    }
  }
  for (const room of roster.rooms) {
    resetFile(roomLogPath(computerRoot, room.id), cleared, `rooms/${room.id}/log`);
    ensureDir(roomDir(computerRoot, room.id));
  }
  kernelRuntime(computerRoot, options, cleared);
  if (options.wipeRuns === true) {
    wipeRunsTree(computerRoot, cleared);
  }
  return {
    computerRoot,
    bots: roster.bots.length,
    rooms: roster.rooms.length,
    cleared,
  };
}

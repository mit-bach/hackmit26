import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

import { isProcessAlive, readJsonIfExists, writeJsonAtomic } from "./fs.ts";
import { nowIso } from "./ids.ts";
import { leaseDir } from "./paths.ts";

interface LeaseRecord {
  readonly path: string;
  readonly botId: string;
  readonly pid: number;
  readonly updatedAt: string;
}

function leaseFile(computerRoot: string, targetPath: string): string {
  const hash = createHash("sha256").update(resolve(computerRoot, targetPath)).digest("hex").slice(0, 16);
  return `${leaseDir(computerRoot)}/${hash}.json`;
}

function parseLease(value: unknown): LeaseRecord | undefined {
  if (typeof value !== "object" || value === null) {
    return undefined;
  }
  const rec = value as Record<string, unknown>;
  if (
    typeof rec.path !== "string" ||
    typeof rec.botId !== "string" ||
    typeof rec.pid !== "number" ||
    typeof rec.updatedAt !== "string"
  ) {
    return undefined;
  }
  return { path: rec.path, botId: rec.botId, pid: rec.pid, updatedAt: rec.updatedAt };
}

export function acquireLease(computerRoot: string, targetPath: string, botId: string): boolean {
  const file = leaseFile(computerRoot, targetPath);
  if (existsSync(file)) {
    const current = parseLease(readJsonIfExists(file));
    if (current && isProcessAlive(current.pid) && current.botId !== botId) {
      const age = Date.now() - Date.parse(current.updatedAt);
      if (Number.isFinite(age) && age < 30_000) {
        return false;
      }
    }
  }
  const lease: LeaseRecord = {
    path: targetPath,
    botId,
    pid: process.pid,
    updatedAt: nowIso(),
  };
  writeJsonAtomic(file, lease);
  return true;
}

export function releaseLease(computerRoot: string, targetPath: string, botId: string): void {
  const file = leaseFile(computerRoot, targetPath);
  const current = parseLease(readJsonIfExists(file));
  if (current && current.botId === botId) {
    writeJsonAtomic(file, { ...current, pid: 0, updatedAt: nowIso() });
  }
}

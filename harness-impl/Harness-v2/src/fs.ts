import {
  closeSync,
  existsSync,
  fsyncSync,
  mkdirSync,
  openSync,
  readFileSync,
  renameSync,
  rmSync,
  statSync,
  unlinkSync,
  writeFileSync,
  writeSync,
} from "node:fs";
import { dirname } from "node:path";

import { shortNonce } from "./ids.ts";

const LOCK_WAIT_MS = 20;
const LOCK_ATTEMPTS = 250;

export function ensureDir(dirPath: string): void {
  mkdirSync(dirPath, { recursive: true });
}

export function writeJsonAtomic(filePath: string, value: unknown): void {
  ensureDir(dirname(filePath));
  const tmp = `${filePath}.tmp.${process.pid}.${shortNonce()}`;
  const data = `${JSON.stringify(value, null, 2)}\n`;
  const fd = openSync(tmp, "w");
  try {
    writeSync(fd, data);
    fsyncSync(fd);
  } finally {
    closeSync(fd);
  }
  renameSync(tmp, filePath);
}

export function readJsonUnknown(filePath: string): unknown {
  const raw = readFileSync(filePath, "utf8");
  return JSON.parse(raw) as unknown;
}

export function readJsonIfExists(filePath: string): unknown | undefined {
  if (!existsSync(filePath)) {
    return undefined;
  }
  return readJsonUnknown(filePath);
}

export function appendJsonlAtomic(filePath: string, value: unknown): void {
  ensureDir(dirname(filePath));
  withFileLock(filePath, () => {
    const line = `${JSON.stringify(value)}\n`;
    const fd = openSync(filePath, "a");
    try {
      writeSync(fd, line);
      fsyncSync(fd);
    } finally {
      closeSync(fd);
    }
  });
}

export function readJsonl(filePath: string): unknown[] {
  if (!existsSync(filePath)) {
    return [];
  }
  const raw = readFileSync(filePath, "utf8");
  const rows: unknown[] = [];
  for (const line of raw.split("\n")) {
    if (line.trim().length === 0) {
      continue;
    }
    try {
      rows.push(JSON.parse(line) as unknown);
    } catch {
      // A torn line is not a protocol event. Skip rather than crash a tail.
    }
  }
  return rows;
}

export function rewriteJsonlAtomic(filePath: string, rows: readonly unknown[]): void {
  ensureDir(dirname(filePath));
  const body = rows.map((row) => JSON.stringify(row)).join("\n");
  const tmp = `${filePath}.tmp.${process.pid}.${shortNonce()}`;
  writeFileSync(tmp, body.length > 0 ? `${body}\n` : "", "utf8");
  const fd = openSync(tmp, "r+");
  try {
    fsyncSync(fd);
  } finally {
    closeSync(fd);
  }
  renameSync(tmp, filePath);
}

const STALE_EMPTY_LOCK_MS = 200;

function stealStaleLock(lockPath: string): boolean {
  try {
    const ageMs = Date.now() - statSync(lockPath).mtimeMs;
    const raw = readFileSync(lockPath, "utf8").trim();
    const pid = Number.parseInt(raw, 10);
    const hasPid = Number.isFinite(pid) && pid > 0;
    if (hasPid && isProcessAlive(pid)) {
      return false;
    }
    if (!hasPid && ageMs < STALE_EMPTY_LOCK_MS) {
      return false;
    }
    unlinkSync(lockPath);
    return true;
  } catch {
    return false;
  }
}

function acquireLockPath(filePath: string): string {
  const lockPath = `${filePath}.lock`;
  ensureDir(dirname(filePath));
  for (let i = 0; i < LOCK_ATTEMPTS; i += 1) {
    try {
      writeFileSync(lockPath, `${process.pid}\n`, { flag: "wx" });
      return lockPath;
    } catch {
      if (stealStaleLock(lockPath)) {
        continue;
      }
      try {
        Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, LOCK_WAIT_MS);
      } catch {
        const end = Date.now() + LOCK_WAIT_MS;
        while (Date.now() < end) {
          // spin
        }
      }
    }
  }
  throw new Error(`timed out waiting for lock ${lockPath}`);
}

function releaseLockPath(lockPath: string): void {
  try {
    unlinkSync(lockPath);
  } catch {
    rmSync(lockPath, { force: true });
  }
}

export function withFileLock<T>(filePath: string, fn: () => T): T {
  const lockPath = acquireLockPath(filePath);
  try {
    return fn();
  } finally {
    releaseLockPath(lockPath);
  }
}

export async function withFileLockAsync<T>(filePath: string, fn: () => Promise<T>): Promise<T> {
  const lockPath = acquireLockPath(filePath);
  try {
    return await fn();
  } finally {
    releaseLockPath(lockPath);
  }
}

export function isProcessAlive(pid: number): boolean {
  if (pid <= 0) {
    return false;
  }
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

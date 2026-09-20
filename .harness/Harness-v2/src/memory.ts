import { existsSync, mkdirSync, readdirSync, readFileSync, renameSync, statSync, writeFileSync } from "node:fs";
import { dirname, relative, resolve, sep } from "node:path";
import { createHash } from "node:crypto";

import { nowIso } from "./ids.ts";
import { memoryDir, memoryFile, memoryLogDir, memoryTopicsDir } from "./paths.ts";

export const MEMORY_MAX_LINES = 200;
export const MEMORY_MAX_BYTES = 24 * 1024;

const SECRET =
  /(\bapi[_-]?key\b\s*[:=]\s*)\S+|(\bpassword\b\s*[:=]\s*)\S+|(\bsecret\b\s*[:=]\s*)\S+|(\btoken\b\s*[:=]\s*)\S+|\bsk-[A-Za-z0-9]{8,}|-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/gi;

export function redactSecrets(text: string): string {
  return text.replace(SECRET, (match) => {
    if (match.includes("BEGIN")) {
      return "«redacted private key»";
    }
    return match.replace(/\S+$/, "«redacted»");
  });
}

function isInside(root: string, candidate: string): boolean {
  const rel = relative(resolve(root), resolve(candidate));
  return rel === "" || (!rel.startsWith(`..${sep}`) && rel !== ".." && !rel.startsWith(".."));
}

export function resolveMemoryRel(computerRoot: string, botId: string, relPath: string): string {
  const root = memoryDir(computerRoot, botId);
  const cleaned = relPath.replaceAll("\\", "/").replace(/^\/+/, "");
  if (cleaned.includes("..")) {
    throw new Error("memory path escapes this Bot");
  }
  const target = resolve(root, cleaned.length === 0 ? "MEMORY.md" : cleaned);
  if (!isInside(root, target)) {
    throw new Error("memory path escapes this Bot");
  }
  return target;
}

export function readMemoryFile(computerRoot: string, botId: string, relPath: string): string {
  const target = resolveMemoryRel(computerRoot, botId, relPath);
  if (!existsSync(target)) {
    return "(empty)";
  }
  return readFileSync(target, "utf8");
}

export function writeMemoryFile(
  computerRoot: string,
  botId: string,
  relPath: string,
  content: string,
): void {
  const target = resolveMemoryRel(computerRoot, botId, relPath);
  mkdirSync(dirname(target), { recursive: true });
  const tmp = `${target}.tmp.${process.pid}`;
  writeFileSync(tmp, redactSecrets(content), "utf8");
  renameSync(tmp, target);
}

export function injectMemoryPrefix(computerRoot: string, botId: string): string {
  const file = memoryFile(computerRoot, botId);
  if (!existsSync(file)) {
    return "";
  }
  const raw = readFileSync(file, "utf8");
  const lines = raw.split("\n");
  let cut = false;
  let text = raw;
  if (lines.length > MEMORY_MAX_LINES) {
    text = lines.slice(0, MEMORY_MAX_LINES).join("\n");
    cut = true;
  }
  const encoded = Buffer.from(text, "utf8");
  if (encoded.length > MEMORY_MAX_BYTES) {
    text = encoded.subarray(0, MEMORY_MAX_BYTES).toString("utf8");
    cut = true;
  }
  if (cut) {
    text += "\n\n[MEMORY.md truncated: only the first 200 lines or 24 KB load each turn]";
  }
  return text;
}

export function appendDailyLog(computerRoot: string, botId: string, line: string): void {
  const day = nowIso().slice(0, 10);
  const file = `${memoryLogDir(computerRoot, botId)}/${day}.md`;
  mkdirSync(dirname(file), { recursive: true });
  const prefix = existsSync(file) ? "" : `# ${day}\n\n`;
  writeFileSync(file, `${prefix}- ${nowIso()} · ${redactSecrets(line)}\n`, { flag: "a" });
}

export interface MemoryFileInfo {
  readonly path: string;
  readonly name: string;
  readonly bytes: number;
  readonly modifiedAt: number;
}

export interface MemoryCapacity {
  readonly lines: number;
  readonly bytes: number;
  readonly maxLines: number;
  readonly maxBytes: number;
  readonly loadedLines: number;
  readonly loadedBytes: number;
  readonly truncated: boolean;
  readonly hash: string;
}

export interface MemoryOverview {
  readonly botId: string;
  readonly workspacePath: string;
  readonly index: MemoryCapacity;
  readonly topics: MemoryFileInfo[];
  readonly logs: MemoryFileInfo[];
}

export interface MemoryDoc {
  readonly path: string;
  readonly text: string;
  readonly hash: string;
  readonly exists: boolean;
}

function hashText(text: string): string {
  return createHash("sha256").update(text).digest("hex");
}

function listDirFiles(dir: string, prefix: string): MemoryFileInfo[] {
  if (!existsSync(dir)) {
    return [];
  }
  const out: MemoryFileInfo[] = [];
  for (const name of readdirSync(dir)) {
    const abs = `${dir}/${name}`;
    try {
      const st = statSync(abs);
      if (!st.isFile()) {
        continue;
      }
      out.push({
        path: `${prefix}${name}`,
        name,
        bytes: st.size,
        modifiedAt: st.mtimeMs,
      });
    } catch {
      continue;
    }
  }
  return out.sort((a, b) => a.name.localeCompare(b.name));
}

function capacityOf(text: string): MemoryCapacity {
  const lines = text.length === 0 ? 0 : text.split("\n").length;
  const bytes = Buffer.byteLength(text, "utf8");
  const truncated = lines > MEMORY_MAX_LINES || bytes > MEMORY_MAX_BYTES;
  return {
    lines,
    bytes,
    maxLines: MEMORY_MAX_LINES,
    maxBytes: MEMORY_MAX_BYTES,
    loadedLines: Math.min(lines, MEMORY_MAX_LINES),
    loadedBytes: Math.min(bytes, MEMORY_MAX_BYTES),
    truncated,
    hash: hashText(text),
  };
}

export function listMemoryOverview(computerRoot: string, botId: string): MemoryOverview {
  const root = memoryDir(computerRoot, botId);
  const indexText = existsSync(memoryFile(computerRoot, botId))
    ? readFileSync(memoryFile(computerRoot, botId), "utf8")
    : "";
  return {
    botId,
    workspacePath: root,
    index: capacityOf(indexText),
    topics: listDirFiles(memoryTopicsDir(computerRoot, botId), "topics/"),
    logs: listDirFiles(memoryLogDir(computerRoot, botId), "log/"),
  };
}

export function readMemoryDoc(computerRoot: string, botId: string, relPath: string): MemoryDoc {
  const path = relPath.trim().length === 0 ? "MEMORY.md" : relPath;
  const target = resolveMemoryRel(computerRoot, botId, path);
  const exists = existsSync(target);
  const text = exists ? readFileSync(target, "utf8") : "";
  return { path, text, hash: hashText(text), exists };
}

export function writeMemoryDoc(
  computerRoot: string,
  botId: string,
  relPath: string,
  content: string,
  expectedHash?: string,
): { readonly ok: true; readonly doc: MemoryDoc; readonly overview: MemoryOverview } | { readonly ok: false; readonly conflict: true; readonly current: string; readonly currentHash: string } {
  const current = readMemoryDoc(computerRoot, botId, relPath);
  if (expectedHash && current.exists && current.hash !== expectedHash) {
    return { ok: false, conflict: true, current: current.text, currentHash: current.hash };
  }
  writeMemoryFile(computerRoot, botId, relPath.trim().length === 0 ? "MEMORY.md" : relPath, content);
  const doc = readMemoryDoc(computerRoot, botId, relPath);
  return { ok: true, doc, overview: listMemoryOverview(computerRoot, botId) };
}

import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname, relative, resolve, sep } from "node:path";

import { nowIso } from "./ids.ts";
import { memoryDir, memoryFile, memoryLogDir } from "./paths.ts";

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

import { existsSync, mkdirSync, readdirSync, readFileSync, renameSync, statSync, writeFileSync } from "node:fs";
import { dirname, extname, relative, resolve, sep } from "node:path";

export interface TreeEntry {
  readonly path: string;
  readonly type: "file" | "dir";
  readonly size?: number;
}

const SKIP_DIR = new Set(["node_modules", ".git", "dist", ".DS_Store"]);
const MAX_ENTRIES = 800;
const MAX_DEPTH = 7;
const MAX_FILE_BYTES = 200_000;

function isInside(root: string, candidate: string): boolean {
  const resolved = resolve(candidate);
  const base = resolve(root);
  return resolved === base || resolved.startsWith(`${base}${sep}`);
}

export function resolveComputerPath(computerRoot: string, rel: string): string {
  const cleaned = rel.replace(/\\/g, "/").replace(/^\/+/, "");
  if (cleaned.includes("..")) {
    throw new Error("path escape");
  }
  const abs = resolve(computerRoot, cleaned);
  if (!isInside(computerRoot, abs)) {
    throw new Error("path escape");
  }
  return abs;
}

export function listComputerTree(computerRoot: string, from = "workspace"): TreeEntry[] {
  const startRel = from.length > 0 ? from : ".";
  const startAbs = resolveComputerPath(computerRoot, startRel);
  if (!existsSync(startAbs)) {
    return [];
  }
  const out: TreeEntry[] = [];
  const walk = (abs: string, depth: number): void => {
    if (out.length >= MAX_ENTRIES || depth > MAX_DEPTH) {
      return;
    }
    let entries;
    try {
      entries = readdirSync(abs, { withFileTypes: true });
    } catch {
      return;
    }
    for (const ent of entries) {
      if (out.length >= MAX_ENTRIES) {
        return;
      }
      if (SKIP_DIR.has(ent.name) || ent.name.endsWith(".lock") || ent.name.includes(".tmp.")) {
        continue;
      }
      const child = resolve(abs, ent.name);
      const rel = relative(computerRoot, child).split(sep).join("/");
      if (ent.isDirectory()) {
        out.push({ path: rel, type: "dir" });
        walk(child, depth + 1);
      } else if (ent.isFile()) {
        let size: number | undefined;
        try {
          size = statSync(child).size;
        } catch {
          size = undefined;
        }
        out.push({ path: rel, type: "file", size });
      }
    }
  };
  const st = statSync(startAbs);
  if (st.isFile()) {
    return [{ path: relative(computerRoot, startAbs).split(sep).join("/"), type: "file", size: st.size }];
  }
  walk(startAbs, 0);
  return out;
}

const TEXT_EXT = new Set([
  ".md",
  ".txt",
  ".json",
  ".jsonl",
  ".ts",
  ".js",
  ".csv",
  ".yml",
  ".yaml",
  ".toml",
  ".xml",
  ".html",
  ".css",
  ".log",
]);

export function readComputerFile(
  computerRoot: string,
  rel: string,
): { readonly path: string; readonly content: string; readonly truncated: boolean } {
  const abs = resolveComputerPath(computerRoot, rel);
  if (!existsSync(abs) || !statSync(abs).isFile()) {
    throw new Error("not a file");
  }
  const ext = extname(abs).toLowerCase();
  if (ext.length > 0 && !TEXT_EXT.has(ext) && !abs.endsWith("MEMORY.md")) {
    throw new Error("not a text file");
  }
  const buf = readFileSync(abs);
  const truncated = buf.length > MAX_FILE_BYTES;
  const slice = truncated ? buf.subarray(0, MAX_FILE_BYTES) : buf;
  return {
    path: rel,
    content: slice.toString("utf8"),
    truncated,
  };
}

export function writeComputerFile(
  computerRoot: string,
  rel: string,
  content: string,
): { readonly path: string; readonly bytes: number } {
  if (content.length > MAX_FILE_BYTES) {
    throw new Error("file too large");
  }
  const abs = resolveComputerPath(computerRoot, rel);
  const ext = extname(abs).toLowerCase();
  if (ext.length > 0 && !TEXT_EXT.has(ext)) {
    throw new Error("not a text file");
  }
  mkdirSync(dirname(abs), { recursive: true });
  const tmp = `${abs}.tmp.${process.pid}`;
  writeFileSync(tmp, content, "utf8");
  renameSync(tmp, abs);
  return { path: rel.replace(/\\/g, "/"), bytes: Buffer.byteLength(content, "utf8") };
}

import {isRecord} from "./load.ts";
import type {PathLeaseBot, PathLeaseFile} from "./types.ts";

export const AUDIT_WRITE_PREFIXES: readonly string[] = [
  "workspace/audit/",
  "runs/audit/",
];

export function posixRel(path: string): string {
  let text = path.replace(/\\/g, "/");
  while (text.startsWith("./")) {
    text = text.slice(2);
  }
  while (text.startsWith("/")) {
    text = text.slice(1);
  }
  if (text.split("/").includes("..")) {
    return "";
  }
  return text;
}

export function writePathAllowed(relPath: string, prefixes: readonly string[]): boolean {
  const rel = posixRel(relPath);
  if (rel.length === 0) {
    return false;
  }
  return prefixes.some((prefix) => {
    const trimmed = prefix.replace(/\/$/, "");
    return rel === trimmed || rel.startsWith(prefix);
  });
}

export function prefixesForSlug(leases: PathLeaseFile, slug: string): readonly string[] {
  return leases.bots[slug]?.writePrefixes ?? [];
}

export function parsePathLeases(value: unknown): PathLeaseFile {
  if (!isRecord(value) || value.version !== "1" || !isRecord(value.bots)) {
    throw new Error("path-leases.json: invalid shape");
  }
  const bots: Record<string, PathLeaseBot> = {};
  for (const [slug, row] of Object.entries(value.bots)) {
    if (!isRecord(row) || !Array.isArray(row.writePrefixes)) {
      throw new Error(`path-leases.json: invalid Bot ${slug}`);
    }
    const prefixes: string[] = [];
    for (const item of row.writePrefixes) {
      if (typeof item !== "string") {
        throw new Error(`path-leases.json: ${slug} writePrefixes must be string[]`);
      }
      prefixes.push(item);
    }
    bots[slug] = {writePrefixes: prefixes};
  }
  return {version: "1", bots};
}

export function writePathFromArgs(args: Readonly<Record<string, unknown>>): string | undefined {
  for (const key of ["path", "dest", "file"] as const) {
    const value = args[key];
    if (typeof value === "string" && value.length > 0) {
      return value;
    }
  }
  return undefined;
}

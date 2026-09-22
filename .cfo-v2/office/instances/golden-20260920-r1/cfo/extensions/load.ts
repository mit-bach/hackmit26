import {readFileSync} from "node:fs";
import {join} from "node:path";

import {
  type BotSlugEntry,
  type CatalogFile,
  type CatalogOp,
  type GrantSet,
  type GrantsFile,
  type Mutability,
  type SlugMapFile,
} from "./types.ts";

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function asBoolean(value: unknown, fallback: boolean): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function asStringArray(value: unknown): string[] | undefined {
  if (!Array.isArray(value)) {
    return undefined;
  }
  const out: string[] = [];
  for (const item of value) {
    if (typeof item !== "string") {
      return undefined;
    }
    out.push(item);
  }
  return out;
}

function asMutability(value: unknown): Mutability | undefined {
  if (value === "read" || value === "write-local" || value === "side-effect-external") {
    return value;
  }
  return undefined;
}

function parseCatalogOp(value: unknown): CatalogOp | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const id = asString(value.id);
  const python = asString(value.python);
  const exportName = asString(value.exportName);
  const mutability = asMutability(value.mutability);
  const sodClass = asString(value.sodClass);
  const ownerPrefixes = asStringArray(value.ownerPrefixes);
  if (!id || !python || !exportName || !mutability || !sodClass || !ownerPrefixes) {
    return undefined;
  }
  if (!isRecord(value.args)) {
    return undefined;
  }
  const args: Record<string, string> = {};
  for (const [key, argType] of Object.entries(value.args)) {
    if (typeof argType !== "string") {
      return undefined;
    }
    args[key] = argType;
  }
  return {
    id,
    python,
    exportName,
    args,
    mutability,
    sodClass,
    evalOnly: asBoolean(value.evalOnly, false),
    ownerPrefixes,
  };
}

export function parseCatalog(value: unknown): CatalogFile {
  if (!isRecord(value) || value.version !== "1" || !Array.isArray(value.ops)) {
    throw new Error("catalog.json: invalid shape");
  }
  const ops: CatalogOp[] = [];
  for (const row of value.ops) {
    const parsed = parseCatalogOp(row);
    if (!parsed) {
      throw new Error("catalog.json: invalid op row");
    }
    ops.push(parsed);
  }
  return {version: "1", ops};
}

function parseGrantSet(value: unknown): GrantSet | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const ops = asStringArray(value.ops);
  const skills = asStringArray(value.skills);
  const outputType = asString(value.outputType);
  if (!ops || !skills || outputType === undefined) {
    return undefined;
  }
  return {ops, skills, outputType};
}

export function parseGrants(value: unknown): GrantsFile {
  if (!isRecord(value) || value.version !== "1" || !isRecord(value.byDisplayName)) {
    throw new Error("grants.json: invalid shape");
  }
  const byDisplayName: Record<string, GrantSet> = {};
  for (const [name, row] of Object.entries(value.byDisplayName)) {
    const parsed = parseGrantSet(row);
    if (!parsed) {
      throw new Error(`grants.json: invalid Grant set for ${name}`);
    }
    byDisplayName[name] = parsed;
  }
  return {version: "1", byDisplayName};
}

export function parseSlugMap(value: unknown): SlugMapFile {
  if (!isRecord(value) || value.version !== "1" || !isRecord(value.bots)) {
    throw new Error("slug-map.json: invalid shape");
  }
  const parsedBots: Record<string, BotSlugEntry> = {};
  for (const [slug, row] of Object.entries(value.bots)) {
    if (Array.isArray(row)) {
      throw new Error(`slug-map.json: ${slug} is a list union; Profiles are required`);
    }
    if (!isRecord(row)) {
      throw new Error(`slug-map.json: invalid Bot ${slug}`);
    }
    if (Array.isArray(row.profiles)) {
      throw new Error(`slug-map.json: ${slug} profiles is a list union; refuse`);
    }
    const defaultProfile = asString(row.defaultProfile);
    if (!defaultProfile) {
      throw new Error(`slug-map.json: ${slug} missing defaultProfile`);
    }
    if (!isRecord(row.profiles)) {
      throw new Error(`slug-map.json: ${slug} profiles must be an object`);
    }
    const profiles: Record<string, string> = {};
    for (const [profile, display] of Object.entries(row.profiles)) {
      if (typeof display !== "string") {
        throw new Error(`slug-map.json: ${slug} profile ${profile} is not one Display name`);
      }
      profiles[profile] = display;
    }
    parsedBots[slug] = {
      defaultProfile,
      profiles,
      allowSodOverlap: asBoolean(row.allowSodOverlap, false),
    };
  }
  return {version: "1", bots: parsedBots};
}

export function readJsonFile(path: string): unknown {
  return JSON.parse(readFileSync(path, "utf8")) as unknown;
}

export function loadCatalog(path: string): CatalogFile {
  return parseCatalog(readJsonFile(path));
}

export function loadGrants(path: string): GrantsFile {
  return parseGrants(readJsonFile(path));
}

export function loadSlugMap(path: string): SlugMapFile {
  return parseSlugMap(readJsonFile(path));
}

export function loadClientFiles(computerRoot: string): {
  readonly catalog: CatalogFile;
  readonly grants: GrantsFile;
  readonly slugMap: SlugMapFile;
} {
  return {
    catalog: loadCatalog(join(computerRoot, "cfo", "catalog.json")),
    grants: loadGrants(join(computerRoot, "cfo", "grants.json")),
    slugMap: loadSlugMap(join(computerRoot, "cfo", "slug-map.json")),
  };
}

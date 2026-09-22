import {existsSync, readFileSync} from "node:fs";
import {join} from "node:path";

import {isRecord} from "./load.ts";
import type {BoundProfile, CatalogFile, CatalogOp, ConnectedToolHit, SearchQuery} from "./types.ts";

export function catalogById(catalog: CatalogFile): ReadonlyMap<string, CatalogOp> {
  const map = new Map<string, CatalogOp>();
  for (const op of catalog.ops) {
    map.set(op.id, op);
  }
  return map;
}

export function catalogByExportName(catalog: CatalogFile): ReadonlyMap<string, CatalogOp> {
  const map = new Map<string, CatalogOp>();
  for (const op of catalog.ops) {
    map.set(op.exportName, op);
  }
  return map;
}

export function resolveOp(catalog: CatalogFile, name: string): CatalogOp | undefined {
  const byId = catalogById(catalog);
  const direct = byId.get(name);
  if (direct) {
    return direct;
  }
  return catalogByExportName(catalog).get(name);
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
}

function denylistFor(bind: BoundProfile): ReadonlySet<string> {
  const path = join(bind.computerRoot, "cfo", "catalog.overrides.json");
  if (!existsSync(path)) {
    return new Set();
  }
  try {
    const raw: unknown = JSON.parse(readFileSync(path, "utf8"));
    if (!isRecord(raw)) {
      return new Set();
    }
    const profileKey = `${bind.slug}/${bind.profile}`;
    const grantDeny = isRecord(raw.grantDenylist) ? raw.grantDenylist : {};
    const profileDeny = isRecord(raw.profileDenylist) ? raw.profileDenylist : {};
    const blocked = [
      ...asStringArray(grantDeny[bind.displayName]),
      ...asStringArray(profileDeny[profileKey]),
    ];
    return new Set(blocked);
  } catch {
    return new Set();
  }
}

export function grantAllows(bind: BoundProfile, op: CatalogOp): boolean {
  if (!bind.connectors) {
    return false;
  }
  if (!bind.grant.ops.includes(op.id)) {
    return false;
  }
  if (op.evalOnly && bind.phase === "operational") {
    return false;
  }
  if (denylistFor(bind).has(op.id)) {
    return false;
  }
  return true;
}

export function visibleOps(bind: BoundProfile, catalog: CatalogFile): CatalogOp[] {
  const out: CatalogOp[] = [];
  for (const op of catalog.ops) {
    if (grantAllows(bind, op)) {
      out.push(op);
    }
  }
  return out;
}

export function searchConnectedTools(
  bind: BoundProfile,
  catalog: CatalogFile,
  query: SearchQuery,
): ConnectedToolHit[] {
  const needle = query.query.trim().toLowerCase();
  const hits: ConnectedToolHit[] = [];
  for (const op of visibleOps(bind, catalog)) {
    if (needle.length > 0) {
      const hay = `${op.id} ${op.exportName}`.toLowerCase();
      if (!hay.includes(needle)) {
        continue;
      }
    }
    hits.push({
      id: op.id,
      exportName: op.exportName,
      args: op.args,
      mutability: op.mutability,
    });
  }
  return hits;
}

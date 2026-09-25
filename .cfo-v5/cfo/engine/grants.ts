import { readFileSync } from "node:fs";
import { join } from "node:path";

export interface CatalogOp {
  readonly id: string;
  readonly mutability: string;
  readonly exportName: string;
}

const WRITE_ALWAYS = new Set([
  "accrual.tools.create_accrual",
  "accrual.tools.reconcile_accrual_with_invoice",
]);

const CONTROLLERS = new Set(["ctl-pay", "ctl-cash", "ctl-books"]);

export function loadStepGrants(computerRoot: string): Record<string, Record<string, string[]>> {
  const raw = readFileSync(join(computerRoot, "cfo", "step-grants.json"), "utf8");
  return JSON.parse(raw) as Record<string, Record<string, string[]>>;
}

export function loadCatalog(computerRoot: string): Map<string, CatalogOp> {
  const raw = JSON.parse(readFileSync(join(computerRoot, "cfo", "catalog.json"), "utf8")) as {
    ops?: Array<Record<string, unknown>>;
  };
  const map = new Map<string, CatalogOp>();
  for (const row of raw.ops ?? []) {
    if (typeof row.id !== "string") continue;
    const op: CatalogOp = {
      id: row.id,
      mutability: typeof row.mutability === "string" ? row.mutability : "read",
      exportName: typeof row.exportName === "string" ? row.exportName : row.id.split(".").pop() ?? row.id,
    };
    map.set(op.id, op);
    map.set(op.exportName, op);
  }
  return map;
}

export function isWrite(op: CatalogOp): boolean {
  return op.mutability !== "read" || WRITE_ALWAYS.has(op.id);
}

export function isController(slug: string): boolean {
  return CONTROLLERS.has(slug);
}

export function opsForStep(
  grants: Record<string, Record<string, string[]>>,
  slug: string,
  step: string,
): string[] {
  return grants[slug]?.[step] ?? [];
}

export function readOpsForBot(grants: Record<string, Record<string, string[]>>, slug: string, catalog: Map<string, CatalogOp>): string[] {
  const found: string[] = [];
  for (const ops of Object.values(grants[slug] ?? {})) {
    for (const id of ops) {
      const meta = catalog.get(id);
      if (meta && !isWrite(meta) && !found.includes(meta.id)) found.push(meta.id);
    }
  }
  return found;
}

export function shortName(op: CatalogOp): string {
  return op.exportName;
}

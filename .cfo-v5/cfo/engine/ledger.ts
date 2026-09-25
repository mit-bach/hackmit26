import { mkdirSync, readdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

import type { Item } from "./types.ts";

export function itemFileName(id: string): string {
  const cut = id.indexOf(":");
  const kind = cut === -1 ? "item" : id.slice(0, cut);
  const business = cut === -1 ? id : id.slice(cut + 1);
  const safe = business.replaceAll(":", "").replaceAll("/", "").replaceAll("..", "");
  return `${kind}-${safe}.json`;
}

export function itemPath(computerRoot: string, id: string): string {
  return join(computerRoot, "runs", "items", itemFileName(id));
}

export function readItem(computerRoot: string, id: string): Item {
  const raw = readFileSync(itemPath(computerRoot, id), "utf8");
  return JSON.parse(raw) as Item;
}

export function writeItem(computerRoot: string, item: Item): void {
  const path = itemPath(computerRoot, item.id);
  mkdirSync(dirname(path), { recursive: true });
  const tmp = `${path}.tmp.${process.pid}`;
  writeFileSync(tmp, `${JSON.stringify(item, null, 2)}\n`);
  renameSync(tmp, path);
}

export function listItems(computerRoot: string): Item[] {
  const dir = join(computerRoot, "runs", "items");
  let names: string[] = [];
  try {
    names = readdirSync(dir);
  } catch {
    return [];
  }
  const items: Item[] = [];
  for (const name of names) {
    if (!name.endsWith(".json") || name.includes(".tmp.")) continue;
    try {
      items.push(JSON.parse(readFileSync(join(dir, name), "utf8")) as Item);
    } catch {
      continue;
    }
  }
  return items;
}

export function seedItem(computerRoot: string, item: Item): Item {
  const next: Item = {
    ...item,
    facts: item.facts ?? {},
    pendingWrite: item.pendingWrite ?? null,
    history: item.history ?? [],
  };
  writeItem(computerRoot, next);
  return next;
}

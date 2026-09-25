import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import { ensureDir } from "./fs.ts";
import { loadLayout } from "./layout.ts";

export function jailTemplate(computerRoot: string): string | undefined {
  const layout = loadLayout(computerRoot);
  if (!layout.jail) return undefined;
  const path = join(resolve(computerRoot), layout.jail.template);
  return existsSync(path) ? path : undefined;
}

export function renderSeatbelt(computerRoot: string, slug: string, botId: string): string {
  const root = resolve(computerRoot);
  const templatePath = jailTemplate(root);
  if (!templatePath) {
    throw new Error("this Computer has no jail template");
  }
  const template = readFileSync(templatePath, "utf8");
  return template.replaceAll("COMPUTER", root).replaceAll("BOTID", botId).replaceAll("SLUG", slug);
}

export function seatbeltProfilePath(computerRoot: string, slug: string, botId: string): string {
  const rendered = renderSeatbelt(computerRoot, slug, botId);
  const dir = join(tmpdir(), "harness-seatbelt");
  ensureDir(dir);
  const file = join(dir, `${slug}.sb`);
  writeFileSync(file, rendered);
  return file;
}

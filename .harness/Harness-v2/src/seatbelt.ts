import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import { ensureDir } from "./fs.ts";

/** v5 Computers jail the Pi process. A v2 Computer has no sandboxes/ directory. */
export function sandboxesEnabled(computerRoot: string): boolean {
  return existsSync(join(resolve(computerRoot), "sandboxes"));
}

/** bot_ctl_pay -> ctl-pay. bot_ap -> ap. */
export function slugForBotId(botId: string): string {
  return botId.replace(/^bot_/, "").replaceAll("_", "-");
}

export function renderSeatbelt(computerRoot: string, slug: string, botId: string): string {
  const root = resolve(computerRoot);
  const templatePath = join(root, "sandbox", "seatbelt.sb");
  const template = readFileSync(templatePath, "utf8");
  return template
    .replaceAll("COMPUTER", root)
    .replaceAll("BOTID", botId)
    .replaceAll("SLUG", slug);
}

/** Write the per-slug profile the spawn uses. Returns the temp file path. */
export function seatbeltProfilePath(computerRoot: string, slug: string, botId: string): string {
  const rendered = renderSeatbelt(computerRoot, slug, botId);
  const dir = join(tmpdir(), "cfo-v5-seatbelt");
  ensureDir(dir);
  const file = join(dir, `${slug}.sb`);
  writeFileSync(file, rendered);
  return file;
}

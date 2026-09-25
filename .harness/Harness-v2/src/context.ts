import { createHash } from "node:crypto";
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { botDir } from "./paths.ts";
import { PROTOCOL_CARD } from "./protocol-card.ts";
import { sandboxesEnabled } from "./seatbelt.ts";
import type { BotRecord, Roster } from "./types.ts";
import { resolveWakeProfile } from "./wake-profile.ts";

export interface ContextLayer {
  readonly name: "office" | "bot";
  readonly hash: string;
  readonly text: string;
}

export interface AssembledContext {
  readonly office: ContextLayer;
  readonly bot: ContextLayer;
  readonly systemSuffix: string;
}

const OFFICE_FALLBACK = `${PROTOCOL_CARD}

## Memory

This Bot's memory/ is the only memory you may read or write. Store a decision you will need on a later wake, with the business id. Do not store a transcript. Do not read another Bot's memory. Call memory_read when the open item is one you have handled before. The file is not pasted into this prompt.

## Finance tools

Finance facts come from the tools this profile is granted. A shell listing of data files is not those tools.
`;

function readIfExists(path: string): string {
  try {
    if (!existsSync(path)) {
      return "";
    }
    return readFileSync(path, "utf8");
  } catch {
    return "";
  }
}

function hashText(text: string): string {
  return createHash("sha256").update(text).digest("hex").slice(0, 16);
}

function layer(name: "office" | "bot", text: string): ContextLayer {
  return { name, hash: hashText(text), text };
}

export function botIdForSlug(slug: string): string {
  return `bot_${slug.replaceAll("-", "_")}`;
}

export function readActiveProfile(computerRoot: string, botId: string, wakeText = ""): string {
  const slug = botId.replace(/^bot_/, "");
  return resolveWakeProfile(computerRoot, slug, wakeText);
}

function officeText(computerRoot: string, roster: Roster): string {
  const fromDisk = readIfExists(join(computerRoot, "office", "system.md")).trim();
  const base = fromDisk.length > 0 ? fromDisk : OFFICE_FALLBACK.trim();
  const peers = roster.bots
    .map((peer) => `- ${peer.slug} (${peer.name}): ${peer.purpose}`)
    .join("\n");
  return `${base}\n\n## Roster\n\n${peers.length > 0 ? peers : "(no other Bots)"}\n`;
}

function skillBodies(computerRoot: string, names: readonly string[]): string {
  const blocks: string[] = [];
  for (const name of names) {
    if (name.includes("/") || name.includes("..")) {
      continue;
    }
    const paths = [join(computerRoot, "skills", name, "SKILL.md")];
    for (const path of paths) {
      const body = readIfExists(path).trim();
      if (body.length > 0) {
        blocks.push(`### Skill ${name}\n\n${body}`);
        break;
      }
    }
  }
  return blocks.join("\n\n");
}

function botText(computerRoot: string, bot: BotRecord, profile: string): string {
  const botMd = readIfExists(join(computerRoot, "office", "bots", bot.slug, "BOT.md")).trim();
  const v5 = sandboxesEnabled(computerRoot);
  const profileMd =
    !v5 && profile.length > 0
      ? readIfExists(join(computerRoot, "office", "bots", bot.slug, "profiles", `${profile}.md`)).trim()
      : "";
  const skills = skillBodies(computerRoot, bot.skills);
  const parts = [
    botMd.length > 0 ? botMd : bot.instructions.trim(),
    profileMd.length > 0 ? `## Active profile ${profile}\n\n${profileMd}` : "",
    skills.length > 0 ? `## Skills\n\n${skills}` : "",
  ].filter((part) => part.length > 0);
  if (parts.length === 0) {
    return `You are Bot ${bot.slug}. ${bot.purpose}`;
  }
  return parts.join("\n\n");
}

function remember(computerRoot: string, botId: string, assembled: AssembledContext): void {
  try {
    const dir = join(botDir(computerRoot, botId), "context");
    mkdirSync(dir, { recursive: true });
    const stamp = join(dir, "current.json");
    const previous = readIfExists(stamp);
    const next = JSON.stringify({
      office: assembled.office.hash,
      bot: assembled.bot.hash,
    });
    if (previous === next) {
      return;
    }
    writeFileSync(join(dir, `office-${assembled.office.hash}.txt`), assembled.office.text);
    writeFileSync(join(dir, `bot-${assembled.bot.hash}.txt`), assembled.bot.text);
    writeFileSync(stamp, next);
    appendFileSync(
      join(dir, "manifest.jsonl"),
      `${JSON.stringify({
        t: new Date().toISOString(),
        office: assembled.office.hash,
        officeBytes: Buffer.byteLength(assembled.office.text),
        bot: assembled.bot.hash,
        botBytes: Buffer.byteLength(assembled.bot.text),
      })}\n`,
    );
  } catch {
    return;
  }
}

export function assembleContext(
  computerRoot: string,
  bot: BotRecord,
  roster: Roster,
  wakeText = "",
): AssembledContext {
  const profile = sandboxesEnabled(computerRoot) ? "" : resolveWakeProfile(computerRoot, bot.slug, wakeText);
  const office = layer("office", officeText(computerRoot, roster));
  const botLayer = layer("bot", botText(computerRoot, bot, profile));
  const assembled: AssembledContext = {
    office,
    bot: botLayer,
    systemSuffix: `${office.text}\n\n${botLayer.text}`,
  };
  remember(computerRoot, bot.id, assembled);
  return assembled;
}

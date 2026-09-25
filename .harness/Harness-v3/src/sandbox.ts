import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { isAbsolute, join, relative, resolve, sep } from "node:path";

import { ensureDir, writeJsonAtomic } from "./fs.ts";
import { deskRel, loadLayout, memoryRel, readInstanceMeta, writePrefixes, type ComputerLayout } from "./layout.ts";
import { loadRoster } from "./roster.ts";

export interface SandboxDecision {
  readonly allowed: boolean;
  readonly reason: string;
}

function botDir(slug: string): string {
  return `bot_${slug.replaceAll("-", "_")}`;
}

export function instanceGroup(instanceId: string, computerRoot?: string): string {
  if (computerRoot) {
    const meta = readInstanceMeta(computerRoot);
    if (meta && meta.id === instanceId && meta.group.length > 0) {
      return meta.group;
    }
  }
  if (instanceId === "live" || instanceId.length === 0) {
    return "deployment";
  }
  const cut = instanceId.indexOf("-");
  return cut > 0 ? instanceId.slice(0, cut) : "desk";
}

export function writePrefixesForSlug(slug: string, computerRoot?: string): readonly string[] {
  return writePrefixes(loadLayout(computerRoot ?? process.cwd()), slug);
}

function slugsToInit(computerRoot: string, slugs: readonly string[], layout: ComputerLayout): readonly string[] {
  if (!layout.jail) return slugs;
  const bound = process.env.HARNESS_BOT?.trim();
  return bound ? slugs.filter((slug) => slug === bound) : slugs;
}

export function ensureSandboxLayout(computerRoot: string, slugs: readonly string[]): void {
  const layout = loadLayout(computerRoot);
  for (const domain of layout.runDomains) {
    if (domain.includes("..") || domain.includes("/")) continue;
    ensureDir(join(computerRoot, "runs", domain));
  }
  for (const slug of slugsToInit(computerRoot, slugs, layout)) {
    const desk = join(computerRoot, deskRel(layout, slug));
    for (const name of layout.deskDirs) {
      if (name.includes("..") || name.includes("/")) continue;
      ensureDir(join(desk, name));
    }
    ensureDir(join(computerRoot, memoryRel(layout, slug)));
  }
}

export function normalizeRel(computerRoot: string, raw: string): string | undefined {
  const text = raw.trim();
  if (text.length === 0) {
    return undefined;
  }
  const abs = isAbsolute(text) ? resolve(text) : resolve(computerRoot, text);
  const root = resolve(computerRoot);
  if (abs !== root && !abs.startsWith(`${root}${sep}`)) {
    return undefined;
  }
  const rel = relative(root, abs).split(sep).join("/");
  if (rel.split("/").includes("..")) {
    return undefined;
  }
  return rel.length === 0 ? "." : rel;
}

function underPrefix(rel: string, prefix: string): boolean {
  const trimmed = prefix.replace(/\/$/, "");
  return rel === trimmed || rel.startsWith(prefix);
}

export function sandboxAllows(
  slug: string,
  kind: "read" | "write",
  computerRoot: string,
  rawPath: string,
): SandboxDecision {
  const layout = loadLayout(computerRoot);
  if (layout.jail) {
    return { allowed: true, reason: "seatbelt" };
  }
  const rel = normalizeRel(computerRoot, rawPath);
  if (rel === undefined) {
    return { allowed: false, reason: "path leaves this Computer" };
  }
  if (kind === "read") {
    const deskRoot = `${layout.desk}/`;
  if (rel.startsWith(deskRoot)) {
      const owner = rel.split("/")[1] ?? "";
      if (owner.length > 0 && owner !== slug) {
        return { allowed: false, reason: `${layout.desk}/${owner} belongs to another Bot` };
      }
    }
    if (rel.startsWith("harness/bots/") && rel.includes("/memory/")) {
      const dir = rel.split("/")[2] ?? "";
      if (dir !== botDir(slug)) {
        return { allowed: false, reason: "memory belongs to another Bot" };
      }
    }
    return { allowed: true, reason: "read" };
  }
  const ok = writePrefixesForSlug(slug, computerRoot).some((prefix) => underPrefix(rel, prefix));
  if (!ok) {
    return { allowed: false, reason: `writes stay in ${deskRel(layout, slug)}/` };
  }
  return { allowed: true, reason: "write" };
}

const ANSWER_KEY_NAMES = new Set(["expected_outcomes.json", "expected_results.json"]);

const ZONE_PATH =
  /^(?:\/|\.\/|\.\.\/|\.\.|workspace\/|sandboxes\/|harness\/|office\/|skills\/|data\/|runs\/|holdout\/|expected_outcomes\.json$|expected_results\.json$)/;

interface CommandPath {
  readonly raw: string;
  readonly kind: "read" | "write";
}

function isAnswerKey(rel: string, layout: ComputerLayout): boolean {
  const parts = rel.split("/");
  if (parts.includes("holdout")) {
    return true;
  }
  const base = parts[parts.length - 1] ?? "";
  if (ANSWER_KEY_NAMES.has(base)) return true;
  return layout.answerKeyNames.includes(base);
}

function bashZoneAllows(
  slug: string,
  computerRoot: string,
  rawPath: string,
  kind: "read" | "write",
): SandboxDecision {
  const rel = normalizeRel(computerRoot, rawPath);
  if (rel === undefined) {
    return { allowed: false, reason: "path leaves this Computer" };
  }
  const layout = loadLayout(computerRoot);
  if (isAnswerKey(rel, layout)) {
    return { allowed: false, reason: "answer key is outside this Bot's desk" };
  }
  const ok = writePrefixesForSlug(slug, computerRoot).some((prefix) => underPrefix(rel, prefix));
  if (!ok) {
    return {
      allowed: false,
      reason: kind === "write" ? `writes stay in ${deskRel(layout, slug)}/` : `reads stay in ${deskRel(layout, slug)}/`,
    };
  }
  return { allowed: true, reason: "bash" };
}

function shellWords(command: string): string[] {
  const words: string[] = [];
  const re = /"([^"]*)"|'([^']*)'|(\S+)/g;
  for (const match of command.matchAll(re)) {
    const word = match[1] ?? match[2] ?? match[3] ?? "";
    if (word.length > 0) {
      words.push(word);
    }
  }
  return words;
}

function isZonePath(token: string): boolean {
  return ZONE_PATH.test(token);
}

function pythonOpens(command: string): CommandPath[] {
  const found: CommandPath[] = [];
  const re = /open\(\s*['"]([^'"]+)['"](?:\s*,\s*['"]([^'"]*)['"])?/g;
  for (const match of command.matchAll(re)) {
    const raw = match[1];
    if (!raw) {
      continue;
    }
    const mode = match[2] ?? "r";
    const write = /[wax+]/.test(mode);
    found.push({ raw, kind: write ? "write" : "read" });
  }
  return found;
}

function cdLeavesComputer(computerRoot: string, command: string): boolean {
  const re = /(?:^|[;&|]\s*)cd\s+([^\s;&|]+)/g;
  for (const match of command.matchAll(re)) {
    const target = match[1];
    if (!target) {
      continue;
    }
    if (normalizeRel(computerRoot, target) === undefined) {
      return true;
    }
  }
  return false;
}

function pathsInCommand(command: string): CommandPath[] {
  const found: CommandPath[] = [...pythonOpens(command)];
  const words = shellWords(command);
  const inPlaceSed = /\bsed\b/.test(command) && /(^|\s)-[A-Za-z]*i\b/.test(command);
  let redirect: "read" | "write" = "read";
  for (const word of words) {
    if (word === ">" || word === ">>") {
      redirect = "write";
      continue;
    }
    if (word.startsWith(">>") || word.startsWith(">")) {
      const rest = word.replace(/^>>?/, "");
      if (rest.length > 0) {
        found.push({ raw: rest, kind: "write" });
      }
      redirect = "read";
      continue;
    }
    if (!isZonePath(word)) {
      redirect = "read";
      continue;
    }
    const kind: "read" | "write" = redirect === "write" || inPlaceSed ? "write" : "read";
    found.push({ raw: word, kind });
    redirect = "read";
  }
  return found;
}

export function sandboxAllowsBash(slug: string, computerRoot: string, command: string): SandboxDecision {
  if (loadLayout(computerRoot).jail) {
    return { allowed: true, reason: "seatbelt" };
  }
  if (cdLeavesComputer(computerRoot, command)) {
    return { allowed: false, reason: "path leaves this Computer" };
  }
  const paths = pathsInCommand(command);
  for (const path of paths) {
    const decision = bashZoneAllows(slug, computerRoot, path.raw, path.kind);
    if (!decision.allowed) {
      return decision;
    }
  }
  const redirectWrite = /(?:>>|>)/.test(command);
  if (redirectWrite && paths.every((path) => path.kind !== "write")) {
    return { allowed: false, reason: "redirect target is not in this Bot's desk" };
  }
  return { allowed: true, reason: "bash" };
}

export function ensureSandboxLeases(computerRoot: string): void {
  if (existsSync(join(computerRoot, "sandboxes"))) {
    return;
  }
  const file = resolve(computerRoot, "harness/path-leases.json");
  const roster = loadRoster(computerRoot);
  const bots: Record<string, { writePrefixes: string[] }> = {};
  if (existsSync(file)) {
    try {
      const parsed: unknown = JSON.parse(readFileSync(file, "utf8"));
      if (typeof parsed === "object" && parsed !== null && "bots" in parsed) {
        const raw = (parsed as { bots?: unknown }).bots;
        if (typeof raw === "object" && raw !== null) {
          for (const [slug, row] of Object.entries(raw)) {
            if (typeof row === "object" && row !== null && "writePrefixes" in row) {
              const prefixes = (row as { writePrefixes?: unknown }).writePrefixes;
              if (Array.isArray(prefixes)) {
                bots[slug] = {
                  writePrefixes: prefixes.filter((item): item is string => typeof item === "string"),
                };
              }
            }
          }
        }
      }
    } catch {
      // replace a broken lease file
    }
  }
  for (const bot of roster.bots) {
    const defaults = [...writePrefixesForSlug(bot.slug, computerRoot)];
    const current = bots[bot.slug]?.writePrefixes ?? [];
    const merged = [...current];
    for (const prefix of defaults) {
      if (!merged.includes(prefix)) {
        merged.push(prefix);
      }
    }
    bots[bot.slug] = { writePrefixes: merged };
  }
  writeJsonAtomic(file, { version: "1", bots });
}

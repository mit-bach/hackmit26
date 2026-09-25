import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { isAbsolute, join, relative, resolve, sep } from "node:path";

import { ensureDir, writeJsonAtomic } from "./fs.ts";
import { loadRoster } from "./roster.ts";

export interface SandboxDecision {
  readonly allowed: boolean;
  readonly reason: string;
}

function botDir(slug: string): string {
  return `bot_${slug.replaceAll("-", "_")}`;
}

export function instanceGroup(instanceId: string): string {
  if (instanceId === "live" || instanceId.length === 0) {
    return "live";
  }
  if (instanceId.startsWith("golden")) {
    return "production";
  }
  const cut = instanceId.indexOf("-");
  return cut > 0 ? instanceId.slice(0, cut) : "desk";
}

export function writePrefixesForSlug(slug: string): readonly string[] {
  return [`workspace/${slug}/`, `harness/bots/${botDir(slug)}/memory/`];
}

const RUN_DOMAINS = [
  "inbox",
  "ap",
  "ar",
  "bank",
  "cash_recon",
  "pay",
  "audit",
  "month_end",
  "accruals",
  "bs_recon",
  "integrations",
  "reporting",
  "ingestion",
] as const;

const DESK_DIRS = ["packets", "handles", "notes"] as const;

export function ensureSandboxLayout(computerRoot: string, slugs: readonly string[]): void {
  if (existsSync(join(computerRoot, "sandboxes"))) {
    const bound = process.env.HARNESS_BOT?.trim();
    const wanted = bound ? slugs.filter((slug) => slug === bound) : slugs;
    for (const slug of wanted) {
      for (const name of ["memory", "packets", "notes"] as const) {
        ensureDir(join(computerRoot, "sandboxes", slug, name));
      }
    }
    return;
  }
  for (const domain of RUN_DOMAINS) {
    ensureDir(join(computerRoot, "runs", domain));
  }
  for (const slug of slugs) {
    const desk = join(computerRoot, "workspace", slug);
    for (const name of DESK_DIRS) {
      ensureDir(join(desk, name));
    }
    const readme = join(desk, "README.md");
    if (!existsSync(readme)) {
      writeFileSync(
        readme,
        `# ${slug}\n\nPackets go in packets/. Handles go in handles/. Notes go in notes/.\nKernel traces live under runs/ and are not yours to invent.\nDo not create extra top-level folders. Do not write data/, office/, cfo/, or another Bot's desk.\n`,
      );
    }
    ensureDir(join(computerRoot, "harness", "bots", botDir(slug), "memory"));
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
  if (existsSync(join(computerRoot, "sandboxes"))) {
    return { allowed: true, reason: "seatbelt" };
  }
  const rel = normalizeRel(computerRoot, rawPath);
  if (rel === undefined) {
    return { allowed: false, reason: "path leaves this Computer" };
  }
  if (kind === "read") {
    if (rel.startsWith("workspace/")) {
      const owner = rel.split("/")[1] ?? "";
      if (owner.length > 0 && owner !== slug) {
        return { allowed: false, reason: `workspace/${owner} belongs to another Bot` };
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
  const ok = writePrefixesForSlug(slug).some((prefix) => underPrefix(rel, prefix));
  if (!ok) {
    return { allowed: false, reason: `writes stay in workspace/${slug}/` };
  }
  return { allowed: true, reason: "write" };
}

const ANSWER_KEY_NAMES = new Set(["expected_outcomes.json", "expected_results.json"]);

const ZONE_PATH =
  /^(?:\/|\.\/|\.\.\/|\.\.|workspace\/|harness\/|office\/|cfo\/|skills\/|data\/|runs\/|world\/|holdout\/|expected_outcomes\.json$|expected_results\.json$)/;

interface CommandPath {
  readonly raw: string;
  readonly kind: "read" | "write";
}

function isAnswerKey(rel: string): boolean {
  const parts = rel.split("/");
  if (parts.includes("holdout")) {
    return true;
  }
  const base = parts[parts.length - 1] ?? "";
  return ANSWER_KEY_NAMES.has(base);
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
  if (isAnswerKey(rel)) {
    return { allowed: false, reason: "answer key is outside this Bot's desk" };
  }
  const ok = writePrefixesForSlug(slug).some((prefix) => underPrefix(rel, prefix));
  if (!ok) {
    return {
      allowed: false,
      reason: kind === "write" ? `writes stay in workspace/${slug}/` : `reads stay in workspace/${slug}/`,
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
  if (existsSync(join(computerRoot, "sandboxes"))) {
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
  const file = resolve(computerRoot, "cfo/path-leases.json");
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
    const defaults = [...writePrefixesForSlug(bot.slug)];
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

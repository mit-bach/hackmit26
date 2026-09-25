/**
 * Per-computer layout. The Harness does not name a client's desks or run
 * domains. A Computer that wants them writes harness/layout.json.
 */
import { existsSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";

export interface JailLayout {
  readonly template: string;
}

export interface ComputerLayout {
  readonly desk: string;
  readonly deskDirs: readonly string[];
  readonly runDomains: readonly string[];
  readonly memory: string;
  readonly jail: JailLayout | null;
  readonly clone: readonly string[];
  readonly wipe: readonly string[];
  readonly answerKeyNames: readonly string[];
  readonly protocolFiles: boolean;
  readonly prompt: "append" | "layers";
  readonly registerSkillDirs: boolean;
}

const DEFAULT_LAYOUT: ComputerLayout = {
  desk: "workspace",
  deskDirs: ["packets", "handles", "notes"],
  runDomains: [],
  memory: "harness/bots/{botId}/memory",
  jail: null,
  clone: ["office", "skills"],
  wipe: [],
  answerKeyNames: [],
  protocolFiles: true,
  prompt: "append",
  registerSkillDirs: true,
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringList(value: unknown): string[] | undefined {
  if (!Array.isArray(value)) return undefined;
  const items = value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
  return items.length > 0 ? items : [];
}

export function layoutPath(computerRoot: string): string {
  return join(resolve(computerRoot), "harness", "layout.json");
}

export function loadLayout(computerRoot: string): ComputerLayout {
  const path = layoutPath(computerRoot);
  if (!existsSync(path)) return DEFAULT_LAYOUT;
  try {
    const raw: unknown = JSON.parse(readFileSync(path, "utf8"));
    if (!isRecord(raw)) return DEFAULT_LAYOUT;
    const jail = isRecord(raw.jail) && typeof raw.jail.template === "string" ? { template: raw.jail.template } : null;
    return {
      desk: typeof raw.desk === "string" && raw.desk.trim().length > 0 ? raw.desk.trim() : DEFAULT_LAYOUT.desk,
      deskDirs: stringList(raw.deskDirs) ?? [...DEFAULT_LAYOUT.deskDirs],
      runDomains: stringList(raw.runDomains) ?? [],
      memory: typeof raw.memory === "string" && raw.memory.trim().length > 0 ? raw.memory.trim() : DEFAULT_LAYOUT.memory,
      jail,
      clone: stringList(raw.clone) ?? [...DEFAULT_LAYOUT.clone],
      wipe: stringList(raw.wipe) ?? [],
      answerKeyNames: stringList(raw.answerKeyNames) ?? [],
      protocolFiles: raw.protocolFiles !== false,
      prompt: raw.prompt === "layers" ? "layers" : "append",
      registerSkillDirs: raw.registerSkillDirs !== false,
    };
  } catch {
    return DEFAULT_LAYOUT;
  }
}

export function applyTemplate(template: string, values: Record<string, string>): string {
  return template.replace(/\{([A-Za-z0-9_]+)\}/g, (token, key: string) => values[key] ?? token);
}

export function botIdForSlug(slug: string): string {
  return `bot_${slug.replaceAll("-", "_")}`;
}

export function memoryRel(layout: ComputerLayout, slug: string): string {
  return applyTemplate(layout.memory, { slug, botId: botIdForSlug(slug) });
}

export function deskRel(layout: ComputerLayout, slug: string): string {
  return `${layout.desk}/${slug}`;
}

export function writePrefixes(layout: ComputerLayout, slug: string): readonly string[] {
  const desk = `${deskRel(layout, slug)}/`;
  const memory = `${memoryRel(layout, slug).replace(/\/$/, "")}/`;
  return memory.startsWith(desk) ? [desk] : [desk, memory];
}

export interface InstanceMeta {
  readonly id: string;
  readonly group: string;
}

export function readInstanceMeta(computerRoot: string): InstanceMeta | undefined {
  const path = join(resolve(computerRoot), "harness", "instance.json");
  if (!existsSync(path)) return undefined;
  try {
    const raw: unknown = JSON.parse(readFileSync(path, "utf8"));
    if (!isRecord(raw) || typeof raw.id !== "string" || typeof raw.group !== "string") return undefined;
    return { id: raw.id, group: raw.group };
  } catch {
    return undefined;
  }
}

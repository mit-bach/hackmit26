import { existsSync } from "node:fs";
import { isAbsolute, resolve, sep } from "node:path";

import { readJsonIfExists, writeJsonAtomic } from "./fs.ts";
import { harnessPackageRoot } from "./pkg.ts";
import { extensionsManifestPath } from "./paths.ts";

export interface AttachConfig {
  readonly extraExtensions?: readonly string[];
  readonly clientSkills?: boolean;
}

export interface ExtensionsManifest {
  readonly extraExtensions: readonly string[];
  readonly clientSkills: boolean;
}

const EMPTY_MANIFEST: ExtensionsManifest = {
  extraExtensions: [],
  clientSkills: false,
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asStringArray(value: unknown): string[] {
  if (typeof value === "string") {
    return value
      .split(/[\n,:;]/)
      .map((item) => item.trim())
      .filter((item) => item.length > 0);
  }
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

export function parseExtensionsManifest(value: unknown): ExtensionsManifest {
  if (!isRecord(value)) {
    return EMPTY_MANIFEST;
  }
  return {
    extraExtensions: asStringArray(value.extraExtensions ?? value.extensions),
    clientSkills: value.clientSkills === true,
  };
}

export function loadExtensionsManifest(computerRoot: string): ExtensionsManifest {
  return parseExtensionsManifest(readJsonIfExists(extensionsManifestPath(computerRoot)));
}

export function saveExtensionsManifest(computerRoot: string, manifest: ExtensionsManifest): void {
  writeJsonAtomic(extensionsManifestPath(computerRoot), manifest);
}

function pathIsInside(root: string, candidate: string): boolean {
  const resolvedRoot = resolve(root);
  const resolvedCandidate = resolve(candidate);
  return resolvedCandidate === resolvedRoot || resolvedCandidate.startsWith(`${resolvedRoot}${sep}`);
}

/** Drop CFO extras that belong to another Computer (office instance switch). */
function keepExtraExtensionPath(computerRoot: string, path: string): boolean {
  if (pathIsInside(computerRoot, path) || pathIsInside(harnessPackageRoot(), path)) {
    return true;
  }
  const posix = path.replaceAll("\\", "/");
  return !posix.includes("/cfo/extensions/");
}

function uniqueResolved(computerRoot: string, items: readonly string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const item of items) {
    const trimmed = item.trim();
    if (trimmed.length === 0) {
      continue;
    }
    const resolved = isAbsolute(trimmed) ? trimmed : resolve(computerRoot, trimmed);
    if (seen.has(resolved)) {
      continue;
    }
    seen.add(resolved);
    out.push(resolved);
  }
  return out;
}

export function collectExtraExtensionPaths(options: {
  readonly computerRoot: string;
  readonly env?: NodeJS.ProcessEnv;
  readonly config?: AttachConfig;
}): string[] {
  const env = options.env ?? process.env;
  const fromEnv = (env.HARNESS_EXTRA_EXTENSIONS ?? "")
    .split(/[:;,]/)
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
  const fromConfig = options.config?.extraExtensions ?? [];
  const fromDisk = loadExtensionsManifest(options.computerRoot).extraExtensions;
  return uniqueResolved(options.computerRoot, [...fromDisk, ...fromConfig, ...fromEnv]).filter(
    (path) => existsSync(path) && keepExtraExtensionPath(options.computerRoot, path),
  );
}

export function extraExtensionArgv(paths: readonly string[]): string[] {
  const args: string[] = [];
  for (const path of paths) {
    args.push("-e", path);
  }
  return args;
}

export function applyAttachEnv(
  env: NodeJS.ProcessEnv,
  computerRoot: string,
  config?: AttachConfig,
): NodeJS.ProcessEnv {
  const next: NodeJS.ProcessEnv = { ...env };
  const paths = collectExtraExtensionPaths({ computerRoot, env: next, config });
  if (paths.length > 0) {
    next.HARNESS_EXTRA_EXTENSIONS = paths.join(":");
  } else {
    delete next.HARNESS_EXTRA_EXTENSIONS;
  }
  const manifest = loadExtensionsManifest(computerRoot);
  const clientSkills =
    next.HARNESS_CLIENT_SKILLS === "1" ||
    config?.clientSkills === true ||
    manifest.clientSkills ||
    (config?.clientSkills !== false && paths.length > 0);
  if (clientSkills) {
    next.HARNESS_CLIENT_SKILLS = "1";
  }
  next.HARNESS_V2_ROOT = harnessPackageRoot();
  next.HARNESS_COMPUTER = next.HARNESS_COMPUTER ?? computerRoot;
  return next;
}

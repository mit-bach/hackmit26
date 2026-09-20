import { existsSync } from "node:fs";
import { isAbsolute, join, resolve } from "node:path";

import { saveExtensionsManifest } from "./client-attach.ts";
import { readJsonIfExists } from "./fs.ts";
import { extensionsManifestPath } from "./paths.ts";
import {
  featuresAreDefault,
  type OperatorConfig,
  type OperatorFeatures,
  type SpawnPolicy,
  type ThinkingLevel,
  type TranscriptVerbosity,
} from "./server/operator-config.ts";

export interface ClientSidecarSpec {
  readonly command: string;
  readonly args: readonly string[];
  readonly portFile: string;
  readonly readyTimeoutMs: number;
}

export interface ClientRuntime {
  readonly system?: string;
  readonly extraExtensions: readonly string[];
  readonly clientSkills: boolean;
  readonly spawnPolicy?: SpawnPolicy;
  readonly autoRoutines: boolean;
  readonly provider?: string;
  readonly model?: string;
  readonly thinkingLevel?: ThinkingLevel;
  readonly evalPhase?: string;
  readonly sidecar?: ClientSidecarSpec;
  readonly features?: Partial<OperatorFeatures>;
}

const DEFAULT_SIDECAR_TIMEOUT_MS = 20_000;

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

export function clientRuntimePath(computerRoot: string): string {
  return join(resolve(computerRoot), "harness", "client.json");
}

function parseSidecar(value: unknown): ClientSidecarSpec | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const command = typeof value.command === "string" ? value.command.trim() : "";
  if (command.length === 0) {
    return undefined;
  }
  const portFile = typeof value.portFile === "string" && value.portFile.trim().length > 0 ? value.portFile.trim() : "cfo/kernel.port";
  const timeoutRaw = value.readyTimeoutMs;
  const readyTimeoutMs =
    typeof timeoutRaw === "number" && Number.isFinite(timeoutRaw) && timeoutRaw > 0
      ? timeoutRaw
      : DEFAULT_SIDECAR_TIMEOUT_MS;
  return {
    command,
    args: asStringArray(value.args),
    portFile,
    readyTimeoutMs,
  };
}

function parseSpawnPolicy(value: unknown): SpawnPolicy | undefined {
  return value === "eager" || value === "lazy" || value === "fake" ? value : undefined;
}

function parseThinkingLevel(value: unknown): ThinkingLevel | undefined {
  return value === "off" ||
    value === "minimal" ||
    value === "low" ||
    value === "medium" ||
    value === "high" ||
    value === "xhigh" ||
    value === "max"
    ? value
    : undefined;
}

function parseClientFeatures(value: unknown): Partial<OperatorFeatures> | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const verbosity: TranscriptVerbosity | undefined =
    value.transcriptVerbosity === "compact" || value.transcriptVerbosity === "tools" || value.transcriptVerbosity === "full"
      ? value.transcriptVerbosity
      : undefined;
  const features: Partial<OperatorFeatures> = {
    ...(typeof value.skillAuthoring === "boolean" ? { skillAuthoring: value.skillAuthoring } : {}),
    ...(typeof value.showToolCalls === "boolean" ? { showToolCalls: value.showToolCalls } : {}),
    ...(typeof value.browser === "boolean" ? { browser: value.browser } : {}),
    ...(verbosity ? { transcriptVerbosity: verbosity } : {}),
  };
  return Object.keys(features).length > 0 ? features : undefined;
}

function discoveredCfoExtension(computerRoot: string): string | undefined {
  const rel = join("cfo", "extensions", "index.ts");
  const abs = join(resolve(computerRoot), rel);
  return existsSync(abs) ? rel : undefined;
}

function discoveredSidecar(computerRoot: string): ClientSidecarSpec | undefined {
  const rel = join("cfo", "bin", "sidecar.sh");
  const abs = join(resolve(computerRoot), rel);
  if (!existsSync(abs)) {
    return undefined;
  }
  return {
    command: rel,
    args: [],
    portFile: join("cfo", "kernel.port"),
    readyTimeoutMs: DEFAULT_SIDECAR_TIMEOUT_MS,
  };
}

export function parseClientRuntime(value: unknown, computerRoot: string): ClientRuntime {
  const discovered = discoveredCfoExtension(computerRoot);
  if (!isRecord(value)) {
    return {
      extraExtensions: discovered ? [discovered] : [],
      clientSkills: Boolean(discovered),
      autoRoutines: false,
      sidecar: discoveredSidecar(computerRoot),
    };
  }
  const extra = asStringArray(value.extraExtensions ?? value.extensions);
  const sidecar =
    value.sidecar === false ? undefined : (parseSidecar(value.sidecar) ?? discoveredSidecar(computerRoot));
  return {
    system: typeof value.system === "string" ? value.system : undefined,
    extraExtensions: extra.length > 0 ? extra : discovered ? [discovered] : [],
    clientSkills:
      value.clientSkills === undefined ? extra.length > 0 || Boolean(discovered) : value.clientSkills === true,
    spawnPolicy: parseSpawnPolicy(value.spawnPolicy),
    autoRoutines: value.autoRoutines === true,
    provider: typeof value.provider === "string" ? value.provider : undefined,
    model: typeof value.model === "string" ? value.model : undefined,
    thinkingLevel: parseThinkingLevel(value.thinkingLevel),
    evalPhase: typeof value.evalPhase === "string" ? value.evalPhase : undefined,
    sidecar,
    features: parseClientFeatures(value.features),
  };
}

export function loadClientRuntime(computerRoot: string): ClientRuntime {
  return parseClientRuntime(readJsonIfExists(clientRuntimePath(computerRoot)), computerRoot);
}

export function resolveClientPath(computerRoot: string, item: string): string {
  const trimmed = item.trim();
  if (trimmed.length === 0) {
    return trimmed;
  }
  return isAbsolute(trimmed) ? trimmed : resolve(computerRoot, trimmed);
}

export function applyClientAttach(computerRoot: string, runtime: ClientRuntime = loadClientRuntime(computerRoot)): void {
  if (runtime.extraExtensions.length === 0 && !runtime.clientSkills) {
    return;
  }
  saveExtensionsManifest(computerRoot, {
    extraExtensions: runtime.extraExtensions.map((item) => resolveClientPath(computerRoot, item)),
    clientSkills: runtime.clientSkills,
  });
}

export function overlayOperatorConfig(
  computerRoot: string,
  operator: OperatorConfig,
  runtime: ClientRuntime = loadClientRuntime(computerRoot),
): OperatorConfig {
  applyClientAttach(computerRoot, runtime);
  const fromClient = runtimeExtensions(computerRoot, runtime);
  const extras = fromClient.length > 0
    ? uniqueStrings(fromClient)
    : uniqueStrings(
        operator.extraExtensions
          .map((item) => resolveClientPath(computerRoot, item))
          .filter((path) => existsSync(path)),
      );
  const clientFeatures = runtime.features;
  const features: OperatorFeatures = featuresAreDefault(operator.features) && clientFeatures
    ? {
        skillAuthoring: clientFeatures.skillAuthoring ?? operator.features.skillAuthoring,
        showToolCalls:
          clientFeatures.showToolCalls === true ||
          clientFeatures.transcriptVerbosity === "tools" ||
          clientFeatures.transcriptVerbosity === "full" ||
          operator.features.showToolCalls,
        browser: clientFeatures.browser ?? operator.features.browser,
        transcriptVerbosity: clientFeatures.transcriptVerbosity ?? operator.features.transcriptVerbosity,
      }
    : operator.features;
  return {
    ...operator,
    spawnPolicy: runtime.spawnPolicy ?? operator.spawnPolicy,
    provider: operator.provider ?? runtime.provider,
    model: operator.model ?? runtime.model,
    thinkingLevel: operator.thinkingLevel ?? runtime.thinkingLevel,
    extraExtensions: extras,
    clientSkills: operator.clientSkills || runtime.clientSkills,
    features,
  };
}

function uniqueStrings(items: readonly string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const item of items) {
    if (item.length === 0 || seen.has(item)) {
      continue;
    }
    seen.add(item);
    out.push(item);
  }
  return out;
}

export function applyClientEnv(
  env: NodeJS.ProcessEnv,
  computerRoot: string,
  runtime: ClientRuntime = loadClientRuntime(computerRoot),
): NodeJS.ProcessEnv {
  const next: NodeJS.ProcessEnv = { ...env };
  next.HARNESS_COMPUTER = next.HARNESS_COMPUTER ?? computerRoot;
  if (runtime.evalPhase) {
    next.CFO_EVAL_PHASE = runtime.evalPhase;
  }
  return next;
}

function runtimeExtensions(computerRoot: string, client: ClientRuntime): string[] {
  return client.extraExtensions.map((item) => resolveClientPath(computerRoot, item)).filter((path) => existsSync(path));
}

export function clientManifestExists(computerRoot: string): boolean {
  return existsSync(clientRuntimePath(computerRoot)) || existsSync(extensionsManifestPath(computerRoot));
}

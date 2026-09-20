import { chmodSync, existsSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

import { readJsonIfExists, writeJsonAtomic } from "../fs.ts";

export type SpawnPolicy = "eager" | "lazy" | "fake";

export type TranscriptVerbosity = "compact" | "tools" | "full";

export type ThinkingLevel = "off" | "minimal" | "low" | "medium" | "high" | "xhigh" | "max";

export const THINKING_LEVELS: readonly ThinkingLevel[] = [
  "off",
  "minimal",
  "low",
  "medium",
  "high",
  "xhigh",
  "max",
];

export interface OperatorFeatures {
  readonly skillAuthoring: boolean;
  readonly showToolCalls: boolean;
  readonly browser: boolean;
  readonly transcriptVerbosity: TranscriptVerbosity;
}

export interface OperatorProfile {
  readonly name: string;
  readonly email: string;
}

export interface OperatorConfig {
  readonly spawnPolicy: SpawnPolicy;
  readonly port: number;
  readonly provider?: string;
  readonly model?: string;
  readonly apiKeys: Readonly<Record<string, string>>;
  readonly openBrowser: boolean;
  readonly extraExtensions: readonly string[];
  readonly clientSkills: boolean;
  readonly features: OperatorFeatures;
  readonly thinkingLevel?: ThinkingLevel;
  readonly profile?: OperatorProfile;
}

export interface PublicOperatorConfig {
  readonly spawnPolicy: SpawnPolicy;
  readonly port: number;
  readonly provider?: string;
  readonly model?: string;
  readonly openBrowser: boolean;
  readonly extraExtensions: readonly string[];
  readonly clientSkills: boolean;
  readonly features: OperatorFeatures;
  readonly thinkingLevel?: ThinkingLevel;
  readonly profile?: OperatorProfile;
  readonly keys: Readonly<Record<string, boolean>>;
  readonly configPath: string;
}

const DEFAULT_FEATURES: OperatorFeatures = {
  skillAuthoring: true,
  showToolCalls: false,
  browser: false,
  transcriptVerbosity: "compact",
};

const DEFAULTS: OperatorConfig = {
  spawnPolicy: "eager",
  port: 8787,
  openBrowser: true,
  apiKeys: {},
  extraExtensions: [],
  clientSkills: false,
  features: DEFAULT_FEATURES,
};

const NESTED_KEY_DEST: Readonly<Record<string, string>> = {
  anthropic: "anthropic",
  openaiCompat: "openai",
  openai: "openai",
  xai: "xai",
  google: "google",
  gemini: "google",
};

const NESTED_DISK_NAMES = ["anthropic", "openai", "xai", "google"] as const;

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

export function operatorConfigPath(): string {
  const override = process.env.HARNESS_CONFIG;
  if (override && override.length > 0) {
    return override;
  }
  return join(homedir(), ".harness", "config.json");
}

function parseThinkingLevel(value: unknown): ThinkingLevel | undefined {
  return typeof value === "string" && (THINKING_LEVELS as readonly string[]).includes(value)
    ? (value as ThinkingLevel)
    : undefined;
}

function parseVerbosity(value: unknown, fallback: TranscriptVerbosity): TranscriptVerbosity {
  return value === "compact" || value === "tools" || value === "full" ? value : fallback;
}

function parseFeatures(value: unknown, fallback: OperatorFeatures): OperatorFeatures {
  if (!isRecord(value)) {
    return fallback;
  }
  const verbosity = parseVerbosity(value.transcriptVerbosity, fallback.transcriptVerbosity);
  const showFromVerbosity = verbosity === "tools" || verbosity === "full";
  return {
    skillAuthoring: value.skillAuthoring === undefined ? fallback.skillAuthoring : value.skillAuthoring !== false,
    showToolCalls:
      value.showToolCalls === undefined ? fallback.showToolCalls || showFromVerbosity : value.showToolCalls === true || showFromVerbosity,
    browser: value.browser === undefined ? fallback.browser : value.browser === true,
    transcriptVerbosity: verbosity,
  };
}

function parseProfile(value: unknown): OperatorProfile | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const name = typeof value.name === "string" ? value.name : "";
  const email = typeof value.email === "string" ? value.email : "";
  if (name.length === 0 && email.length === 0) {
    return undefined;
  }
  return { name, email };
}

function mergeNestedKeys(patch: Record<string, unknown>, apiKeys: Record<string, string>): void {
  for (const [from, dest] of Object.entries(NESTED_KEY_DEST)) {
    const nested = patch[from];
    if (!isRecord(nested) || typeof nested.key !== "string") {
      continue;
    }
    if (nested.key.length === 0) {
      delete apiKeys[dest];
    } else {
      apiKeys[dest] = nested.key;
    }
  }
}

function parseConfig(value: unknown): OperatorConfig {
  if (!isRecord(value)) {
    return DEFAULTS;
  }
  const policy = value.spawnPolicy;
  const spawnPolicy: SpawnPolicy =
    policy === "lazy" || policy === "fake" || policy === "eager" ? policy : "eager";
  const portRaw = value.port;
  const port = typeof portRaw === "number" && Number.isFinite(portRaw) ? portRaw : 8787;
  const keysRaw = value.apiKeys;
  const apiKeys: Record<string, string> = {};
  if (isRecord(keysRaw)) {
    for (const [name, secret] of Object.entries(keysRaw)) {
      if (typeof secret === "string" && secret.length > 0) {
        apiKeys[name] = secret;
      }
    }
  }
  mergeNestedKeys(value, apiKeys);
  return {
    spawnPolicy,
    port,
    provider: typeof value.provider === "string" ? value.provider : undefined,
    model: typeof value.model === "string" ? value.model : undefined,
    apiKeys,
    openBrowser: value.openBrowser !== false,
    extraExtensions: asStringArray(value.extraExtensions),
    clientSkills: value.clientSkills === true,
    features: parseFeatures(value.features, DEFAULT_FEATURES),
    thinkingLevel: parseThinkingLevel(value.thinkingLevel),
    profile: parseProfile(value.profile),
  };
}

export function loadOperatorConfig(): OperatorConfig {
  return parseConfig(readJsonIfExists(operatorConfigPath()));
}

function serializeOperatorConfig(config: OperatorConfig): Record<string, unknown> {
  const body: Record<string, unknown> = {
    spawnPolicy: config.spawnPolicy,
    port: config.port,
    openBrowser: config.openBrowser,
    extraExtensions: [...config.extraExtensions],
    clientSkills: config.clientSkills,
    features: config.features,
  };
  if (config.provider) {
    body.provider = config.provider;
  }
  if (config.model) {
    body.model = config.model;
  }
  if (config.thinkingLevel) {
    body.thinkingLevel = config.thinkingLevel;
  }
  if (config.profile) {
    body.profile = config.profile;
  }
  for (const name of NESTED_DISK_NAMES) {
    const secret = config.apiKeys[name];
    if (secret) {
      body[name] = { key: secret };
    }
  }
  return body;
}

export function saveOperatorConfig(next: OperatorConfig): void {
  const path = operatorConfigPath();
  mkdirSync(dirname(path), { recursive: true });
  writeJsonAtomic(path, serializeOperatorConfig(next));
  try {
    chmodSync(path, 0o600);
  } catch {
    // Windows and some volumes ignore chmod.
  }
}

export function publicOperatorConfig(config: OperatorConfig = loadOperatorConfig()): PublicOperatorConfig {
  const keys: Record<string, boolean> = {};
  for (const name of Object.keys(config.apiKeys)) {
    keys[name] = true;
  }
  return {
    spawnPolicy: config.spawnPolicy,
    port: config.port,
    provider: config.provider,
    model: config.model,
    openBrowser: config.openBrowser,
    extraExtensions: config.extraExtensions,
    clientSkills: config.clientSkills,
    features: config.features,
    thinkingLevel: config.thinkingLevel,
    profile: config.profile,
    keys,
    configPath: operatorConfigPath(),
  };
}

export function patchOperatorConfig(patch: Record<string, unknown>): OperatorConfig {
  const current = loadOperatorConfig();
  const apiKeys = { ...current.apiKeys };
  if (isRecord(patch.apiKeys)) {
    for (const [name, secret] of Object.entries(patch.apiKeys)) {
      if (secret === null || secret === "") {
        delete apiKeys[name];
      } else if (typeof secret === "string") {
        apiKeys[name] = secret;
      }
    }
  }
  mergeNestedKeys(patch, apiKeys);
  const extraExtensions =
    patch.extraExtensions !== undefined ? asStringArray(patch.extraExtensions) : [...current.extraExtensions];
  const next: OperatorConfig = {
    spawnPolicy:
      patch.spawnPolicy === "lazy" || patch.spawnPolicy === "fake" || patch.spawnPolicy === "eager"
        ? patch.spawnPolicy
        : current.spawnPolicy,
    port: typeof patch.port === "number" && Number.isFinite(patch.port) ? patch.port : current.port,
    provider: typeof patch.provider === "string" ? patch.provider : current.provider,
    model: typeof patch.model === "string" ? patch.model : current.model,
    apiKeys,
    openBrowser: typeof patch.openBrowser === "boolean" ? patch.openBrowser : current.openBrowser,
    extraExtensions,
    clientSkills: typeof patch.clientSkills === "boolean" ? patch.clientSkills : current.clientSkills,
    features: parseFeatures(patch.features, current.features),
    thinkingLevel:
      patch.thinkingLevel !== undefined ? parseThinkingLevel(patch.thinkingLevel) : current.thinkingLevel,
    profile: patch.profile !== undefined ? parseProfile(patch.profile) : current.profile,
  };
  saveOperatorConfig(next);
  return next;
}

export function configExists(): boolean {
  return existsSync(operatorConfigPath());
}

export function piEnvFromConfig(config: OperatorConfig): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = { ...process.env };
  const openai = config.apiKeys.openai ?? config.apiKeys.OPENAI_API_KEY;
  const anthropic = config.apiKeys.anthropic ?? config.apiKeys.ANTHROPIC_API_KEY;
  const xai = config.apiKeys.xai ?? config.apiKeys.XAI_API_KEY;
  const google = config.apiKeys.google ?? config.apiKeys.GOOGLE_API_KEY ?? config.apiKeys.gemini;
  if (openai) {
    env.OPENAI_API_KEY = openai;
  }
  if (anthropic) {
    env.ANTHROPIC_API_KEY = anthropic;
  }
  if (xai) {
    env.XAI_API_KEY = xai;
  }
  if (google) {
    env.GOOGLE_API_KEY = google;
    env.GEMINI_API_KEY = google;
  }
  if (config.provider) {
    env.HARNESS_PI_PROVIDER = config.provider;
  }
  if (config.model) {
    env.HARNESS_PI_MODEL = config.model;
  }
  if (config.thinkingLevel) {
    env.HARNESS_PI_THINKING = config.thinkingLevel;
  }
  if (config.extraExtensions.length > 0) {
    env.HARNESS_EXTRA_EXTENSIONS = config.extraExtensions.join(":");
  }
  if (config.clientSkills) {
    env.HARNESS_CLIENT_SKILLS = "1";
  }
  return env;
}

export function featuresAreDefault(features: OperatorFeatures): boolean {
  return (
    features.showToolCalls === DEFAULT_FEATURES.showToolCalls &&
    features.transcriptVerbosity === DEFAULT_FEATURES.transcriptVerbosity
  );
}

export function keyConfigured(config: OperatorConfig, name: string): boolean {
  const aliases: Record<string, readonly string[]> = {
    anthropic: ["anthropic", "ANTHROPIC_API_KEY"],
    openai: ["openai", "OPENAI_API_KEY"],
    openaiCompat: ["openai", "OPENAI_API_KEY"],
    xai: ["xai", "XAI_API_KEY"],
    google: ["google", "GOOGLE_API_KEY", "gemini"],
  };
  const names = aliases[name] ?? [name];
  return names.some((key) => Boolean(config.apiKeys[key]));
}

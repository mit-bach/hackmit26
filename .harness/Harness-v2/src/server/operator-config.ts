import { chmodSync, existsSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

import { readJsonIfExists, writeJsonAtomic } from "../fs.ts";

export type SpawnPolicy = "eager" | "lazy" | "fake";

export interface OperatorConfig {
  readonly spawnPolicy: SpawnPolicy;
  readonly port: number;
  readonly provider?: string;
  readonly model?: string;
  readonly apiKeys: Readonly<Record<string, string>>;
  readonly openBrowser: boolean;
}

export interface PublicOperatorConfig {
  readonly spawnPolicy: SpawnPolicy;
  readonly port: number;
  readonly provider?: string;
  readonly model?: string;
  readonly openBrowser: boolean;
  readonly keys: Readonly<Record<string, boolean>>;
  readonly configPath: string;
}

const DEFAULTS: OperatorConfig = {
  spawnPolicy: "eager",
  port: 8787,
  openBrowser: true,
  apiKeys: {},
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function operatorConfigPath(): string {
  const override = process.env.HARNESS_CONFIG;
  if (override && override.length > 0) {
    return override;
  }
  return join(homedir(), ".harness", "config.json");
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
  return {
    spawnPolicy,
    port,
    provider: typeof value.provider === "string" ? value.provider : undefined,
    model: typeof value.model === "string" ? value.model : undefined,
    apiKeys,
    openBrowser: value.openBrowser !== false,
  };
}

export function loadOperatorConfig(): OperatorConfig {
  return parseConfig(readJsonIfExists(operatorConfigPath()));
}

export function saveOperatorConfig(next: OperatorConfig): void {
  const path = operatorConfigPath();
  mkdirSync(dirname(path), { recursive: true });
  writeJsonAtomic(path, next);
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
  if (openai) {
    env.OPENAI_API_KEY = openai;
  }
  if (anthropic) {
    env.ANTHROPIC_API_KEY = anthropic;
  }
  if (xai) {
    env.XAI_API_KEY = xai;
  }
  if (config.provider) {
    env.HARNESS_PI_PROVIDER = config.provider;
  }
  if (config.model) {
    env.HARNESS_PI_MODEL = config.model;
  }
  return env;
}

import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function harnessPackageRoot(start = fileURLToPath(new URL(".", import.meta.url))): string {
  let dir = start;
  for (;;) {
    const pkg = join(dir, "package.json");
    if (existsSync(pkg)) {
      const parsed: unknown = JSON.parse(readFileSync(pkg, "utf8"));
      if (isRecord(parsed) && typeof parsed.name === "string" && parsed.name.startsWith("harness-")) {
        return dir;
      }
    }
    const parent = dirname(dir);
    if (parent === dir) {
      throw new Error("could not find harness package root");
    }
    dir = parent;
  }
}

export function extensionEntryPath(): string {
  return join(harnessPackageRoot(), "extensions", "index.ts");
}

export function extraExtensionArgs(env: NodeJS.ProcessEnv = process.env): string[] {
  const raw = env.HARNESS_EXTRA_EXTENSIONS?.trim();
  if (!raw) {
    return [];
  }
  const args: string[] = [];
  for (const item of raw.split(/[:;,]/)) {
    const path = item.trim();
    if (path.length > 0) {
      args.push("-e", path);
    }
  }
  return args;
}

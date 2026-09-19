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
      if (isRecord(parsed) && parsed.name === "harness-v2") {
        return dir;
      }
    }
    const parent = dirname(dir);
    if (parent === dir) {
      throw new Error("could not find harness-v2 package root");
    }
    dir = parent;
  }
}

export function extensionEntryPath(): string {
  return join(harnessPackageRoot(), "extensions", "index.ts");
}

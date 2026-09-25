import { readFileSync } from "node:fs";
import { join } from "node:path";

const HEADER_PROFILE = /^profile:\s*([A-Za-z0-9_-]+)\s*$/;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Lines after `[harness wake]` and before the blank line that starts the body. */
export function wakeHeaderLines(text: string): readonly string[] {
  const lines = text.replace(/^\uFEFF/, "").split(/\r?\n/);
  if (lines[0]?.trim() !== "[harness wake]") {
    return [];
  }
  const header: string[] = [];
  for (let i = 1; i < lines.length; i += 1) {
    const line = lines[i] ?? "";
    if (line.trim().length === 0) {
      break;
    }
    header.push(line);
  }
  return header;
}

/** Profile name from the wake header only. A `profile:` line in the body is ignored. */
export function profileFromWakeHeader(text: string): string | undefined {
  for (const line of wakeHeaderLines(text)) {
    const match = HEADER_PROFILE.exec(line.trim());
    const name = match?.[1];
    if (name && name.length > 0) {
      return name;
    }
  }
  return undefined;
}

export function readDefaultProfile(computerRoot: string, slug: string): string {
  try {
    const raw: unknown = JSON.parse(readFileSync(join(computerRoot, "cfo", "slug-map.json"), "utf8"));
    if (!isRecord(raw) || !isRecord(raw.bots)) {
      return "";
    }
    const hyphen = slug.replaceAll("_", "-");
    const entry = raw.bots[slug] ?? raw.bots[hyphen];
    if (!isRecord(entry) || typeof entry.defaultProfile !== "string") {
      return "";
    }
    const name = entry.defaultProfile.trim();
    if (name.length === 0 || name.includes("/") || name.includes("..")) {
      return "";
    }
    return name;
  } catch {
    return "";
  }
}

/** Header profile, otherwise this Bot's defaultProfile. Does not keep the previous wake. */
export function resolveWakeProfile(computerRoot: string, slug: string, wakeText: string): string {
  return profileFromWakeHeader(wakeText) ?? readDefaultProfile(computerRoot, slug);
}

const HEADER_PROFILE = /^profile:\s*([A-Za-z0-9_-]+)\s*$/;

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

export function readDefaultProfile(_computerRoot: string, _slug: string): string {
  return "";
}

/** The Harness does not bind a profile. Clients that need a step read the wake themselves. */
export function resolveWakeProfile(_computerRoot: string, _slug: string, _wakeText: string): string {
  return "";
}

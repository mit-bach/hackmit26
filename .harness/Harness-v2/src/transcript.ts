import { appendJsonlAtomic, readJsonl } from "./fs.ts";
import { transcriptPath } from "./paths.ts";
import type { TranscriptEntry } from "./types.ts";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

export function parseTranscriptEntry(value: unknown): TranscriptEntry | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  if (typeof value.seq !== "number" || typeof value.t !== "string" || typeof value.kind !== "string") {
    return undefined;
  }
  return {
    seq: value.seq,
    t: value.t,
    kind: value.kind,
    text: asString(value.text) ?? "",
    handleId: asString(value.handleId),
    from: asString(value.from),
    to: asString(value.to),
  };
}

export function appendTranscript(
  computerRoot: string,
  botId: string,
  entry: TranscriptEntry,
): void {
  appendJsonlAtomic(transcriptPath(computerRoot, botId), entry);
}

export function readTranscript(
  computerRoot: string,
  botId: string,
  limit: number,
  beforeSeq?: number,
): TranscriptEntry[] {
  const rows: TranscriptEntry[] = [];
  for (const raw of readJsonl(transcriptPath(computerRoot, botId))) {
    const parsed = parseTranscriptEntry(raw);
    if (!parsed) {
      continue;
    }
    if (beforeSeq !== undefined && parsed.seq >= beforeSeq) {
      continue;
    }
    rows.push(parsed);
  }
  return rows.slice(Math.max(0, rows.length - limit));
}

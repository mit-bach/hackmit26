import { readProtocol } from "./protocol-log.ts";
import { readTranscript } from "./transcript.ts";
import type { TranscriptEntry } from "./types.ts";

export function recentWorkBrief(computerRoot: string, botId: string, limit = 10): string {
  const twoDaysAgo = Date.now() - 2 * 24 * 60 * 60 * 1000;
  const lines: string[] = [];
  for (const event of readProtocol(computerRoot)) {
    if (event.to !== botId && event.from !== botId) {
      continue;
    }
    const at = Date.parse(event.t);
    if (!Number.isFinite(at) || at < twoDaysAgo) {
      continue;
    }
    const text = (event.text ?? event.type).slice(0, 120);
    lines.push(`${event.t.slice(11, 16)} · ${event.type} · ${text}`);
  }
  return lines.slice(-limit).join("\n");
}

export function transcriptTail(
  computerRoot: string,
  botId: string,
  limit: number,
  beforeSeq?: number,
): TranscriptEntry[] {
  const fromFile = readTranscript(computerRoot, botId, 10_000, beforeSeq);
  const fromProtocol: TranscriptEntry[] = [];
  for (const event of readProtocol(computerRoot)) {
    if (event.to !== botId && event.from !== botId && event.slug === undefined) {
      continue;
    }
    if (event.to !== botId && event.from !== botId) {
      continue;
    }
    if (beforeSeq !== undefined && event.seq >= beforeSeq) {
      continue;
    }
    fromProtocol.push({
      seq: event.seq,
      t: event.t,
      kind: event.type,
      text: event.text ?? "",
      handleId: event.handleId,
      from: event.from,
      to: event.to,
    });
  }
  const merged = new Map<number, TranscriptEntry>();
  for (const row of fromProtocol) {
    merged.set(row.seq, row);
  }
  for (const row of fromFile) {
    merged.set(row.seq, row);
  }
  return [...merged.values()].sort((a, b) => a.seq - b.seq).slice(-limit);
}

/**
 * Client Handle payloads for Source Bot wakes.
 * Harness core does not learn what an invoice is.
 */

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export interface SourceSendPayload {
  readonly from: string;
  readonly to: string;
  readonly toSlug: string;
  readonly profile: string;
  readonly prompt: string;
  readonly paths: readonly string[];
  readonly kind: "a2a_handoff";
  readonly mode: "async";
  readonly onBusy: "queue";
  readonly idempotencyKey: string;
}

export interface SourceHandleIntent {
  readonly fromSlug: string;
  readonly toSlug: string;
  readonly profile: string;
  readonly paths: readonly string[];
  readonly prompt: string;
  readonly idempotencyKey: string;
}

export function botIdForSlug(slug: string): string {
  return `bot_${slug.replace(/-/g, "_")}`;
}

export function toSendPayload(intent: SourceHandleIntent): SourceSendPayload {
  return {
    from: botIdForSlug(intent.fromSlug),
    to: botIdForSlug(intent.toSlug),
    toSlug: intent.toSlug,
    profile: intent.profile,
    prompt: intent.prompt,
    paths: intent.paths,
    kind: "a2a_handoff",
    mode: "async",
    onBusy: "queue",
    idempotencyKey: intent.idempotencyKey,
  };
}

export function parseSendPayload(value: unknown): SourceSendPayload | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const row = value;
  if (
    typeof row.from !== "string" ||
    typeof row.to !== "string" ||
    typeof row.toSlug !== "string" ||
    typeof row.profile !== "string" ||
    typeof row.prompt !== "string" ||
    typeof row.kind !== "string" ||
    typeof row.mode !== "string" ||
    typeof row.onBusy !== "string" ||
    typeof row.idempotencyKey !== "string" ||
    !Array.isArray(row.paths)
  ) {
    return undefined;
  }
  const paths = row.paths.filter((item): item is string => typeof item === "string");
  if (paths.length !== row.paths.length) {
    return undefined;
  }
  if (row.kind !== "a2a_handoff" || row.mode !== "async" || row.onBusy !== "queue") {
    return undefined;
  }
  return {
    from: row.from,
    to: row.to,
    toSlug: row.toSlug,
    profile: row.profile,
    prompt: row.prompt,
    paths,
    kind: "a2a_handoff",
    mode: "async",
    onBusy: "queue",
    idempotencyKey: row.idempotencyKey,
  };
}

export function stripePacketHasNoInvoiceCandidate(packet: unknown): boolean {
  if (!isRecord(packet)) {
    return false;
  }
  return packet.invoice_candidates === 0;
}

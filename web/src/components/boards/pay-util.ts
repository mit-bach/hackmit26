/** Shared parsing for the pay-desk boards. Kernel values only. */

export const DEFAULT_AP_ID = "INV-003";
export const CLEAN_AP_ID = "INV-001";
export const FEATURED_PAYMENT_ID = "PAY-004";

export const AGING_BUCKETS = ["CURRENT", "1-30", "31-60", "61-90", "90+"] as const;

export type AgingBucketKey = (typeof AGING_BUCKETS)[number];

export function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function asList(value: unknown): readonly unknown[] {
  return Array.isArray(value) ? value : [];
}

export function str(value: unknown): string | undefined {
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed ? trimmed : undefined;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  return undefined;
}

export function num(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return undefined;
}

export function moneyEqual(left: number, right: number): boolean {
  return Math.round(left * 100) === Math.round(right * 100);
}

export function qtyEqual(left: number, right: number): boolean {
  return Math.abs(left - right) < 0.0001;
}

export function artifactRecord(value: unknown): Record<string, unknown> | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  if (isRecord(value.record)) {
    return value.record;
  }
  if (value.invoice_id || value.po_id || value.receipt_id || value.payment_id) {
    return value;
  }
  return undefined;
}

export function workflowInner(result: unknown): Record<string, unknown> | undefined {
  if (!isRecord(result)) {
    return undefined;
  }
  if (isRecord(result.result)) {
    return result.result;
  }
  if (result.stages || result.io || result.decision) {
    return result;
  }
  return undefined;
}

export function decisionToken(result: unknown, fallback?: string): string {
  const inner = workflowInner(result);
  const nested = inner ? inner.decision : undefined;
  if (typeof nested === "string" && nested.trim()) {
    return nested;
  }
  if (isRecord(nested) && typeof nested.decision === "string" && nested.decision.trim()) {
    return nested.decision;
  }
  const outputs = isRecord(inner?.io) ? inner.io.outputs : undefined;
  if (isRecord(outputs) && typeof outputs.decision === "string" && outputs.decision.trim()) {
    return outputs.decision;
  }
  return fallback || "not run";
}

export function appliedInvoiceIds(result: unknown): readonly string[] {
  const inner = workflowInner(result);
  const outputs = isRecord(inner?.io) ? inner.io.outputs : undefined;
  const fromIo = isRecord(outputs) ? asList(outputs.invoice_ids) : [];
  const ids = fromIo
    .map((item) => str(item))
    .filter((item): item is string => Boolean(item));
  return ids;
}

export interface CollectionChip {
  readonly action: string;
  readonly invoiceId?: string;
  readonly draft: boolean;
}

export function collectionChips(result: unknown): readonly CollectionChip[] {
  const rows = decisionRows(result);
  const chips: CollectionChip[] = [];
  const seen = new Set<string>();
  for (const row of rows) {
    const action = str(row.action);
    if (!action) {
      continue;
    }
    const invoiceId = str(row.invoice_id);
    const key = `${action}:${invoiceId || ""}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    chips.push({
      action,
      invoiceId,
      draft: action.startsWith("SEND_"),
    });
  }
  return chips;
}

export function collectionBlockReason(result: unknown): string | undefined {
  const inner = workflowInner(result);
  if (!inner) {
    return undefined;
  }
  const nested = isRecord(inner.result) ? inner.result : inner;
  if (nested.blocked !== true) {
    return undefined;
  }
  return str(nested.block_reason);
}

function decisionRows(value: unknown, depth = 0): Array<Record<string, unknown>> {
  if (depth > 8) {
    return [];
  }
  if (Array.isArray(value)) {
    const found: Array<Record<string, unknown>> = [];
    for (const item of value) {
      found.push(...decisionRows(item, depth + 1));
    }
    return found;
  }
  if (!isRecord(value)) {
    return [];
  }
  if (typeof value.action === "string") {
    return [value];
  }
  const found: Array<Record<string, unknown>> = [];
  found.push(...decisionRows(value.decisions, depth + 1));
  found.push(...decisionRows(value.result, depth + 1));
  found.push(...decisionRows(value.outbox, depth + 1));
  return found;
}

/** Shared Kernel payload readers for remaining-route instruments. */

export function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function asRecord(value: unknown): Record<string, unknown> | null {
  return isRecord(value) ? value : null;
}

export function asUnknownList(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

export function asRecordList(value: unknown): Array<Record<string, unknown>> {
  return asUnknownList(value).flatMap((item) => {
    const rec = asRecord(item);
    return rec ? [rec] : [];
  });
}

export function readString(record: Record<string, unknown> | null, key: string): string | undefined {
  if (!record) {
    return undefined;
  }
  const value = record[key];
  if (typeof value === "string" && value.trim()) {
    return value;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  return undefined;
}

export function readBoolean(record: Record<string, unknown> | null, key: string): boolean | undefined {
  if (!record) {
    return undefined;
  }
  const value = record[key];
  return typeof value === "boolean" ? value : undefined;
}

export function readNumber(record: Record<string, unknown> | null, key: string): number | undefined {
  if (!record) {
    return undefined;
  }
  const value = record[key];
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() && !Number.isNaN(Number(value))) {
    return Number(value);
  }
  return undefined;
}

export function readStringList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => String(item ?? "").trim()).filter(Boolean);
}

/** `useWorkflow` wraps Kernel output in `{ result, workflow, status }`. */
export function workflowInner(result: unknown): Record<string, unknown> | null {
  const root = asRecord(result);
  if (!root) {
    return null;
  }
  const nested = asRecord(root.result);
  return nested ?? root;
}

export function ioOutputs(inner: Record<string, unknown> | null): Record<string, unknown> | null {
  const io = asRecord(inner?.io);
  return asRecord(io?.outputs);
}

export function ioInputs(inner: Record<string, unknown> | null): Record<string, unknown> | null {
  const io = asRecord(inner?.io);
  return asRecord(io?.inputs);
}

export function workflowStages(result: unknown): unknown[] {
  const inner = workflowInner(result);
  const fromInner = asUnknownList(inner?.stages);
  if (fromInner.length) {
    return fromInner;
  }
  const root = asRecord(result);
  return asUnknownList(root?.stages);
}

export interface StageLike {
  readonly id?: string;
  readonly bot?: string;
  readonly slug?: string;
  readonly label?: string;
  readonly status?: string;
  readonly detail?: string;
}

export function asLiveStages(result: unknown): StageLike[] {
  return asRecordList(workflowStages(result)).map((rec) => ({
    id: readString(rec, "id"),
    bot: readString(rec, "bot"),
    slug: readString(rec, "slug") || readString(rec, "bot"),
    label: readString(rec, "label"),
    status: readString(rec, "status"),
    detail: readString(rec, "detail"),
  }));
}

export type DocClass = "invoice" | "quote" | "statement" | "receipt" | "other";

export function classifyKind(raw: unknown): DocClass | null {
  if (raw == null || raw === "") {
    return null;
  }
  const value = String(raw).toLowerCase().replace(/[_-]+/g, " ").trim();
  if (!value) {
    return null;
  }
  if (value.includes("quote") || value.includes("quotation")) {
    return "quote";
  }
  if (value.includes("statement")) {
    return "statement";
  }
  if (value.includes("receipt")) {
    return "receipt";
  }
  if (/\bnot\b/.test(value) && value.includes("invoice")) {
    return "other";
  }
  if (value.includes("invoice") || value === "bill") {
    return "invoice";
  }
  return "other";
}

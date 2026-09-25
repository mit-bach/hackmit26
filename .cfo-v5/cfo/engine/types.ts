export interface StepResult {
  readonly decision: string;
  readonly reason?: string;
  readonly evidence_used?: readonly string[];
  readonly [key: string]: unknown;
}

export interface HistoryEntry {
  readonly step: string;
  readonly by: string;
  readonly result: StepResult;
  readonly t: string;
}

export interface PendingWrite {
  readonly op: string;
  readonly args: Record<string, unknown>;
  readonly idempotencyKey: string;
  readonly verifierHandle: string;
}

export interface Item {
  id: string;
  workflow: string;
  step: string;
  owner: string;
  facts: Record<string, unknown>;
  pendingWrite: PendingWrite | null;
  history: HistoryEntry[];
  terminal?: string;
  channel?: string;
  source?: string;
  counterparty?: string;
  packetKind?: string;
}

export interface NextStep {
  readonly step: string;
  readonly owner: string;
}

export interface EmitStep {
  readonly workflow: string;
  readonly id: string;
  readonly step: string;
  readonly owner: string;
  readonly facts?: Record<string, unknown>;
}

export type Advance =
  | ({ readonly kind: "next" } & NextStep)
  | { readonly kind: "terminal"; readonly terminal: string }
  | { readonly kind: "emit"; readonly emit: EmitStep; readonly terminal?: string };

export interface CompleteOk {
  readonly ok: true;
  readonly next?: NextStep;
  readonly enqueued?: { readonly owner: string; readonly handleId: string };
  readonly terminal?: string;
  readonly item: Item;
}

export interface CompleteErr {
  readonly ok: false;
  readonly error: string;
}

export type CompleteResult = CompleteOk | CompleteErr;

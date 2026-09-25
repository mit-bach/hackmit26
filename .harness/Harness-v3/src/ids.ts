import { randomBytes, randomUUID } from "node:crypto";

export function newId(prefix: string): string {
  return `${prefix}_${randomUUID()}`;
}

export function newHandleId(): string {
  return newId("h");
}

export function newInboxId(): string {
  return newId("in");
}

export function newApprovalId(): string {
  return newId("ap");
}

export function newReceiptId(): string {
  return newId("rc");
}

export function shortNonce(): string {
  return randomBytes(4).toString("hex");
}

export function nowIso(): string {
  return new Date().toISOString();
}

/**
 * Atomic persist of a Kernel cash bind_case file.
 * On-disk keys match Python cash_recon.case_store (snake_case).
 * This module does not reimplement match math.
 */

import {createHash} from 'node:crypto';
import {mkdirSync, readFileSync, renameSync, writeFileSync} from 'node:fs';
import {dirname, join} from 'node:path';

export const CASH_CASE_SCHEMA = 'cfo.cash_recon.case.v1';

export interface CashBoundCaseFile {
  readonly schema: string;
  readonly case_id: string;
  readonly idempotency_key: string;
  readonly content_hash: string;
  readonly bank: readonly Record<string, unknown>[];
  readonly ledger: readonly Record<string, unknown>[];
  readonly fees: readonly Record<string, unknown>[];
  readonly candidates: readonly Record<string, unknown>[];
}

export interface CashCaseParts {
  readonly caseId: string;
  readonly idempotencyKey?: string;
  readonly bank: readonly Record<string, unknown>[];
  readonly ledger: readonly Record<string, unknown>[];
  readonly fees: readonly Record<string, unknown>[];
  readonly candidates: readonly Record<string, unknown>[];
}

export function cashCaseDir(computerRoot: string): string {
  return join(computerRoot, 'runs', 'cash_recon', 'cases');
}

export function cashCasePath(computerRoot: string, caseId: string): string {
  const safe = caseId.replaceAll('/', '_').replaceAll('..', '_');
  return join(cashCaseDir(computerRoot), `${safe}.json`);
}

export function hashCashCase(parts: CashCaseParts): string {
  const payload = {
    bank: parts.bank,
    ledger: parts.ledger,
    fees: parts.fees,
    candidates: parts.candidates,
  };
  return createHash('sha256').update(JSON.stringify(payload)).digest('hex');
}

function isEnoent(error: unknown): boolean {
  return typeof error === 'object' && error !== null && 'code' in error &&
      (error as {readonly code?: string}).code === 'ENOENT';
}

function isPosted(entry: unknown): boolean {
  if (typeof entry !== 'object' || entry === null || !('posted' in entry)) {
    return false;
  }
  return (entry as {readonly posted?: unknown}).posted === true;
}

function assertUnposted(candidates: readonly Record<string, unknown>[]): void {
  for (const candidate of candidates) {
    const entries = candidate['proposed_adjusting_entries'];
    if (!Array.isArray(entries)) {
      continue;
    }
    for (const entry of entries) {
      if (isPosted(entry)) {
        throw new Error('proposed fee journals must stay unposted; refuse persist');
      }
    }
  }
}

export function writeJsonAtomic(filePath: string, payload: unknown): void {
  mkdirSync(dirname(filePath), {recursive: true});
  const tmpPath = `${filePath}.tmp.${process.pid}`;
  writeFileSync(tmpPath, `${JSON.stringify(payload, null, 2)}\n`, {encoding: 'utf8'});
  renameSync(tmpPath, filePath);
}

export function buildCashCaseFile(parts: CashCaseParts): CashBoundCaseFile {
  assertUnposted(parts.candidates);
  const idempotencyKey = parts.idempotencyKey ?? `cash-case:${parts.caseId}`;
  return {
    schema: CASH_CASE_SCHEMA,
    case_id: parts.caseId,
    idempotency_key: idempotencyKey,
    content_hash: hashCashCase(parts),
    bank: parts.bank,
    ledger: parts.ledger,
    fees: parts.fees,
    candidates: parts.candidates,
  };
}

export function persistCashCase(computerRoot: string, parts: CashCaseParts): string {
  const filePath = cashCasePath(computerRoot, parts.caseId);
  const next = buildCashCaseFile(parts);
  try {
    const existingUnknown: unknown =
        JSON.parse(readFileSync(filePath, {encoding: 'utf8'}));
    if (isCashBoundCaseFile(existingUnknown) &&
        existingUnknown.content_hash === next.content_hash &&
        existingUnknown.idempotency_key === next.idempotency_key) {
      return filePath;
    }
  } catch (error: unknown) {
    if (!isEnoent(error) && !(error instanceof SyntaxError)) {
      throw error;
    }
  }
  writeJsonAtomic(filePath, next);
  return filePath;
}

export function readCashCase(computerRoot: string, caseId: string): CashBoundCaseFile | null {
  try {
    const raw: unknown = JSON.parse(
        readFileSync(cashCasePath(computerRoot, caseId), {encoding: 'utf8'}));
    if (!isCashBoundCaseFile(raw)) {
      throw new Error(`cash case ${caseId} must be a JSON object`);
    }
    return raw;
  } catch (error: unknown) {
    if (isEnoent(error)) {
      return null;
    }
    throw error;
  }
}

function isCashBoundCaseFile(value: unknown): value is CashBoundCaseFile {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const row = value as Record<string, unknown>;
  return typeof row['schema'] === 'string' && typeof row['case_id'] === 'string' &&
      typeof row['idempotency_key'] === 'string' && typeof row['content_hash'] === 'string' &&
      Array.isArray(row['bank']) && Array.isArray(row['ledger']) && Array.isArray(row['fees']) &&
      Array.isArray(row['candidates']);
}

import assert from 'node:assert/strict';
import {mkdtempSync, readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {test} from 'node:test';

import {
  CASH_CASE_SCHEMA,
  persistCashCase,
  readCashCase,
} from './cashCase.ts';
import {cashGrantError, cashMayCall} from './cashGrants.ts';

test('persistCashCase is atomic and reloadable', (): void => {
  const root = mkdtempSync(join(tmpdir(), 'cfo-cash-case-'));
  const path = persistCashCase(root, {
    caseId: '2026-09',
    bank: [{transaction_id: 'B5', amount_minor: 1241240}],
    ledger: [{entry_id: 'L5', amount_minor: 1240000}],
    fees: [],
    candidates: [{
      candidate_id: 'UNEXPLAINED_DIFFERENCE:B5:L5',
      match_type: 'UNEXPLAINED_DIFFERENCE',
      difference_minor: 1240,
      proposed_adjusting_entries: [{posted: false}],
    }],
  });
  const raw = JSON.parse(readFileSync(path, {encoding: 'utf8'})) as {schema: string};
  assert.equal(raw.schema, CASH_CASE_SCHEMA);
  const loaded = readCashCase(root, '2026-09');
  assert.ok(loaded);
  assert.equal(loaded.case_id, '2026-09');
  assert.equal(loaded.candidates[0]?.['difference_minor'], 1240);
});

test('persistCashCase refuses posted fee journals', (): void => {
  const root = mkdtempSync(join(tmpdir(), 'cfo-cash-case-posted-'));
  assert.throws((): void => {
    persistCashCase(root, {
      caseId: '2026-09',
      bank: [],
      ledger: [],
      fees: [],
      candidates: [{
        proposed_adjusting_entries: [{posted: true}],
      }],
    });
  }, /unposted/);
});

test('cash cannot create_accrual or touch pay-run ops', (): void => {
  assert.equal(cashMayCall('match', 'cash_recon.tools.get_candidate'), true);
  assert.equal(cashMayCall('investigate', 'cash_recon.tools.get_match_candidates'), true);
  assert.equal(cashMayCall('match', 'accrual.tools.create_accrual'), false);
  assert.equal(cashMayCall('investigate', 'accrual.tools.create_accrual'), false);
  assert.equal(cashMayCall('match', 'scheduling.tools.get_approved_pool'), false);
  assert.ok(cashGrantError('match', 'accrual.tools.create_accrual')?.includes('forbidden'));
});

/**
 * Profile Grant filter for Bot cash.
 * Compiler grants.json is the SoT. This module refuses off-grant names.
 */

export type CashProfile = 'match' | 'investigate';

export const CASH_READ_OPS: readonly string[] = [
  'cash_recon.tools.get_bank_transaction',
  'cash_recon.tools.get_ledger_entry',
  'cash_recon.tools.get_fee_evidence',
  'cash_recon.tools.get_match_candidates',
  'cash_recon.tools.get_candidate',
];

export const CASH_FORBIDDEN_OPS: readonly string[] = [
  'accrual.tools.create_accrual',
  'accrual.tools.reconcile_accrual_with_invoice',
  'scheduling.tools.get_approved_pool',
  'scheduling.tools.get_payment_candidates',
  'scheduling.tools.get_cash_position',
  'scheduling.tools.get_treasury_policies',
];

const CASH_PROFILE_OPS: Readonly<Record<CashProfile, readonly string[]>> = {
  match: CASH_READ_OPS,
  investigate: CASH_READ_OPS,
};

export function cashGrantedOps(profile: CashProfile): readonly string[] {
  return CASH_PROFILE_OPS[profile];
}

export function cashMayCall(profile: CashProfile, opId: string): boolean {
  if (CASH_FORBIDDEN_OPS.includes(opId)) {
    return false;
  }
  return cashGrantedOps(profile).includes(opId);
}

export function cashGrantError(profile: CashProfile, opId: string): string | null {
  if (cashMayCall(profile, opId)) {
    return null;
  }
  return `forbidden: Bot cash profile ${profile} cannot call ${opId}`;
}

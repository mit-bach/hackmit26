import type {CatalogOp, VerifierRoute} from "./types.ts";

const ACCRUAL_WRITES = new Set([
  "accrual.tools.create_accrual",
  "accrual.tools.reconcile_accrual_with_invoice",
]);

const PAY_PATTERN = /pay_run|pay-run|write_off|write-off|send_as_user|send-as-user/i;
const LOCK_PATTERN = /period_lock|period-lock|mark_closed|lock_period/i;
const CASH_PATTERN = /cash_apply|post_match|post_fee|sign_off_rec/i;

export function isConsequentialKernelOp(op: CatalogOp): boolean {
  if (ACCRUAL_WRITES.has(op.id)) {
    return true;
  }
  if (op.mutability === "side-effect-external") {
    return true;
  }
  if (PAY_PATTERN.test(op.id) || LOCK_PATTERN.test(op.id) || CASH_PATTERN.test(op.id)) {
    return true;
  }
  return false;
}

export function routeVerifier(op: CatalogOp): VerifierRoute | undefined {
  if (ACCRUAL_WRITES.has(op.id)) {
    return {
      slug: "ctl-books",
      profile: "review-treatment",
      reason: "close treatment write",
    };
  }
  if (LOCK_PATTERN.test(op.id)) {
    return {slug: "ctl-books", profile: "lock", reason: "period lock"};
  }
  if (CASH_PATTERN.test(op.id)) {
    return {slug: "ctl-cash", profile: "review-rec", reason: "cash identification"};
  }
  if (PAY_PATTERN.test(op.id) || op.mutability === "side-effect-external") {
    return {slug: "ctl-pay", profile: "review-pay", reason: "money-out or external side effect"};
  }
  return undefined;
}

export interface VerifierIntercept {
  readonly error: "verifier_required";
  readonly verifier: string;
  readonly verifierProfile: string;
  readonly reason: string;
  readonly packetPath: string;
  readonly handleId: string | null;
  readonly instruction: string;
}

export function verifierInstruction(route: VerifierRoute, packetPath: string): string {
  return [
    `profile: ${route.profile}`,
    `Concur or refuse this Kernel op. Packet: ${packetPath}`,
    "Do not ask a human. Do not call ask_user. Kernel math still wins.",
  ].join("\n");
}

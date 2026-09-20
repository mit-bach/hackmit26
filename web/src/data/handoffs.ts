import type { AgentSlug } from "./agents";

/** Peer handoffs from `.cfo-v2/office/computer/cfo/handle-map.json`. */
export type Handoff = {
  from: AgentSlug;
  to: AgentSlug;
  when: string;
  profile: string;
  why: string;
};

export const HANDOFFS: Handoff[] = [
  { from: "email", to: "ap", when: "bill", profile: "prepare", why: "A vendor invoice in email is handed to payables so it can be checked before anyone treats it as money owed." },
  { from: "email", to: "apply", when: "remittance", profile: "apply", why: "A customer payment notice is handed to cash application so the money can be matched to invoices." },
  { from: "stripe", to: "cash", when: "deposit", profile: "match", why: "An explained Stripe payout is handed to cash reconciliation so the bank deposit can be tied to the books." },
  { from: "stripe", to: "apply", when: "charges", profile: "apply", why: "Stripe customer charges are handed to cash application because they represent money customers have already paid." },
  { from: "stripe", to: "ctl-cash", when: "waterfall_break", profile: "review-rec", why: "If Stripe's charges, refunds, fees, and payout do not add up, Cash Control rechecks the packet instead of forcing a match." },
  { from: "bank", to: "cash", when: "line", profile: "match", why: "Each bank line is handed to cash reconciliation to look for a matching explanation in the ledger." },
  { from: "books", to: "ap", when: "bill", profile: "prepare", why: "A bill that arrived through the accounting or purchasing system is still checked by payables." },
  { from: "books", to: "collect", when: "open-invoice", profile: "chase", why: "Open customer invoices in the books are handed to collections after payments have been applied." },
  { from: "books", to: "close", when: "lock-state", profile: "coordinate", why: "Whether the period is locked is handed to month-end close so it does not pretend the books are finished." },
  { from: "ap", to: "ctl-pay", when: "approve", profile: "review-match", why: "A bill that looks ready is independently rechecked by Payables Control before it counts as approved." },
  { from: "ap", to: "pay", when: "payable", profile: "schedule", why: "Bills that have cleared payable checks are handed to payments to draft the weekly run." },
  { from: "ap", to: "close", when: "unreceived", profile: "coordinate", why: "If goods or services were billed but not received, month-end close needs that fact for completeness." },
  { from: "pay", to: "ctl-pay", when: "release", profile: "review-pay", why: "The draft payment plan is independently rechecked before any cash would be released." },
  { from: "pay", to: "cash", when: "wires", profile: "match", why: "Once wires are planned, cash reconciliation expects matching bank activity." },
  { from: "apply", to: "cash", when: "identified-deposit", profile: "match", why: "A customer deposit that has been identified is handed to cash reconciliation so the bank line can be explained." },
  { from: "apply", to: "ctl-cash", when: "ambiguous", profile: "review-apply", why: "If the payment cannot be matched with enough evidence, Cash Control reviews it instead of guessing." },
  { from: "collect", to: "ctl-pay", when: "write-off", profile: "review-pay", why: "A proposed write-off or reserve is independently rechecked before it can change what the company claims it is owed." },
  { from: "cash", to: "ctl-cash", when: "sign-off", profile: "review-rec", why: "Material bank-rec proposals are independently rechecked before they are accepted as complete." },
  { from: "cash", to: "close", when: "trusted", profile: "coordinate", why: "Trusted cash status is handed to month-end close. Unresolved bank differences keep the month from finishing." },
  { from: "close", to: "ctl-books", when: "treatment", profile: "review-treatment", why: "Prepaid and similar treatments are independently rechecked before they post as final." },
  { from: "close", to: "ctl-books", when: "assets-treatment", profile: "review-assets", why: "Asset and depreciation treatments are independently rechecked." },
  { from: "close", to: "ctl-books", when: "bs-treatment", profile: "review-bs", why: "Balance-sheet rec packets are independently rechecked." },
  { from: "close", to: "ctl-books", when: "lock", profile: "lock", why: "The period lock is independently rechecked. Close does not mark the month closed on its own." },
  { from: "close", to: "story", when: "pack-story", profile: "flux", why: "Once the close pack exists, reporting explains what changed and updates the cash forecast." },
  { from: "close", to: "audit", when: "pack-audit", profile: "interpret", why: "After operations have recorded the month, audit samples the pack independently." },
];

export const PRINCIPAL_FLOWS = [
  { from: "intake", to: "pay", label: "Vendor bills" },
  { from: "intake", to: "cash", label: "Bank, Stripe, and remittances" },
  { from: "pay", to: "cash", label: "Wires and cash effects" },
  { from: "cash", to: "books-close", label: "Trusted cash, or a block" },
  { from: "books-close", to: "shared", label: "The same books, explained and sampled" },
];

export function handoffsFor(slug: string): { inbound: Handoff[]; outbound: Handoff[] } {
  return {
    inbound: HANDOFFS.filter((edge) => edge.to === slug),
    outbound: HANDOFFS.filter((edge) => edge.from === slug),
  };
}

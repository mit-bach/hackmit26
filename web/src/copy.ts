import { usd } from "./api";

/** Title-case leftover snake/kebab/enum tokens without pretending they are known. */
export function humanizeToken(value: unknown): string {
  const raw = String(value ?? "").trim();
  if (!raw) return "";
  const spaced = raw.replace(/[._-]+/g, " ").replace(/([a-z])([A-Z])/g, "$1 $2");
  return spaced
    .split(/\s+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
}

function lookup(table: Record<string, string>, value: unknown, fallback?: string): string {
  if (value === null || value === undefined || value === "") return fallback || "";
  const key = String(value).trim();
  if (table[key]) return table[key];
  const upper = key.toUpperCase();
  if (table[upper]) return table[upper];
  const lower = key.toLowerCase();
  if (table[lower]) return table[lower];
  return fallback || humanizeToken(key);
}

export const STATUS_COPY: Record<string, string> = {
  HUMAN_REVIEW: "Unresolved — more evidence required",
  NEEDS_REVIEW: "Maximor still needs more evidence before completing this task",
  BLOCKED: "Cannot finish yet",
  OPEN: "Still open",
  CLOSED: "Closed",
  COMPLETE: "Finished",
  COMPLETED: "Finished",
  IN_PROGRESS: "In progress",
  READY: "Ready to run",
  NOT_STARTED: "Not started yet",
  MATCHED: "Matched",
  UNMATCHED: "Not matched yet",
  APPLIED: "Applied to invoices",
  UNAPPLIED: "Not yet matched to an invoice",
  PARTIAL: "Partially applied",
  APPROVE: "Approved",
  APPROVED: "Approved",
  HOLD: "Held for more evidence",
  REJECT: "Rejected",
  REJECTED: "Rejected",
  PASS: "Passed",
  FAIL: "Failed",
  FAILED: "Failed",
  TIED: "Tied out",
  EXCEPTION: "Exception",
  EXPLAINED_EXCEPTION: "Difference found and explained",
  OUTSTANDING_TIMING_ITEM: "Timing difference — expected to clear later",
  RECONCILED: "Bank and ledger agree",
  FAILED_TIE: "Bank and ledger still disagree",
  CONFIRMED: "Confirmed from available records",
  CURRENT: "Not overdue yet",
  PAST_DUE: "Overdue",
  PAID: "Paid",
  AUTO_APPLY: "Matched automatically",
  NEEDS_MORE_EVIDENCE: "More evidence required",
  RESOLVED: "Resolved",
  IN_REVIEW: "Still being evaluated",
  PENDING: "Pending",
  SKIPPED: "Skipped",
  RUNNING: "Running",
  queued: "Queued",
  true: "Yes",
  false: "No",
  invoice: "Invoice",
  quote: "Quote — not a bill",
  statement: "Account statement — not a bill",
  receipt: "Receipt — not a vendor bill",
  reimbursement: "Employee reimbursement",
  other: "Not treated as a vendor invoice",
  not_an_invoice: "Not an invoice",
  duplicate: "Looks like a duplicate bill",
  malformed: "Missing required fields",
};

export const DECISION_COPY: Record<string, string> = {
  AUTO_APPLY: "Maximor matched this payment to customer invoices automatically.",
  HUMAN_REVIEW: "Maximor could not identify a matching invoice with enough evidence.",
  UNAPPLIED: "This customer payment is still unmatched.",
  APPROVE: "Approved — the supporting records agree.",
  HOLD: "Held — Maximor found a problem that must be resolved first.",
  REJECT: "Rejected.",
  APPROVE_CLOSE: "Month-end close can finish.",
  REJECT_CLOSE: "Month-end close cannot finish yet.",
  REQUEST_REVIEW: "Close still needs more evidence.",
  MATCHED: "Bank activity was matched to the ledger.",
  EXPLAINED_EXCEPTION: "A difference was found and Maximor explained it.",
};

export const MATCH_TYPE_COPY: Record<string, string> = {
  EXACT_MATCH: "Exact bank-to-ledger match",
  GROUPED_MATCH: "One payment matched to multiple records",
  FEE_NETTED: "Transfer matched after accounting for the bank fee",
  PROVIDER_PAYOUT: "Stripe payout matched to bank deposit",
  TIMING_DIFFERENCE: "Timing difference between the bank and the ledger",
  POSSIBLE_DUPLICATE_BANK_TXN: "Possible duplicate bank transaction",
  POSSIBLE_DUPLICATE_REFUND: "Possible duplicate refund",
  POSSIBLE_DUPLICATE_LEDGER_ENTRY: "Possible duplicate ledger entry",
  UNEXPLAINED_DIFFERENCE: "Unresolved difference — no supporting evidence found",
  UNMATCHED_BANK: "Bank transaction with no matching ledger entry",
  UNMATCHED_LEDGER: "Ledger entry with no matching bank transaction",
};

export const MATCH_TYPE_SENTENCE: Record<string, string> = {
  EXACT_MATCH: "One bank transaction matches one ledger entry for the same amount.",
  GROUPED_MATCH: "One bank transaction matched to several ledger entries.",
  FEE_NETTED: "Bank transfer matched after accounting for the bank fee.",
  PROVIDER_PAYOUT: "Stripe payout matched to the corresponding bank deposit.",
  TIMING_DIFFERENCE: "The bank and ledger record the same event on different dates.",
  UNEXPLAINED_DIFFERENCE: "The bank and ledger disagree, and Maximor could not find supporting evidence for the difference.",
  UNMATCHED_BANK: "This bank movement has no matching explanation in the accounting records yet.",
  UNMATCHED_LEDGER: "This ledger cash entry has no matching bank movement yet.",
};

export const METHOD_COPY: Record<string, string> = {
  seasonal_prior_year: "Use the comparable season from last year",
  SEASONAL_PRIOR_YEAR: "Use the comparable season from last year",
  last_invoice: "Reuse the most recent bill amount",
  simple_average: "Average of historical bills",
  recent_average: "Average of the most recent bills",
  weighted_recent_average: "Weighted average of recent bills, with later months counting more",
  linear_trend: "Project the recent trend forward",
  contract_commitment: "Use the contracted monthly amount",
  usage_run_rate: "Estimate from usage multiplied by the contract rate",
  goods_receipt: "Use proof that goods or services were received",
  purchase_order: "Use the authorized purchase-order amount",
  conservative_minimum: "Use the most conservative available estimate",
  AMORTIZE: "Spread the prepaid cost across the months it covers",
  DEPRECIATE: "Spread the asset cost across its useful life",
  EXPENSE: "Record the full amount as an expense now",
};

export const TASK_COPY: Record<string, string> = {
  "TASK-AP": "Accounts payable",
  "TASK-AR": "Accounts receivable",
  "TASK-CASH": "Cash reconciliation",
  "TASK-ACCRUAL": "Accrued expenses",
  "TASK-PREPAID": "Prepaid expenses",
  "TASK-FA": "Fixed assets",
  "TASK-BS": "Balance sheet reconciliation",
  "TASK-FINAL": "Final close check",
  ap: "Accounts payable",
  ar: "Accounts receivable",
  cash: "Cash reconciliation",
  accruals: "Accrued expenses",
  prepaid: "Prepaid expenses",
  depreciation: "Fixed assets",
  bs: "Balance sheet reconciliation",
  final: "Final close check",
};

export const AGENT_COPY: Record<
  string,
  { name: string; role: string; example: string; inputs: string; outputs: string; passesTo: string }
> = {
  email: {
    name: "Email Agent",
    role: "Reads incoming finance emails and attachments and identifies what kind of document arrived.",
    example: "If a vendor emails an invoice, the Email Agent identifies it as an invoice, extracts the attachment, and sends the record into accounts payable.",
    inputs: "Emails, attachments, employee uploads, and vendor-portal documents.",
    outputs: "A classification (invoice, quote, statement, receipt, or other) plus extracted fields when the document is a bill.",
    passesTo: "Hands invoices to the Accounts Payable Agent and customer remittances toward cash application.",
  },
  stripe: {
    name: "Stripe Agent",
    role: "Tracks money processed through Stripe. It connects customer charges, refunds, disputes, Stripe fees, and payouts so Maximor can explain exactly how a Stripe payout became a bank deposit.",
    example: "When Stripe sends a payout, this agent reconstructs gross charges minus refunds, chargebacks, and fees, then ties that net amount to the bank deposit.",
    inputs: "Stripe payouts, balance transactions, refunds, disputes, and matching bank deposits.",
    outputs: "A payout waterfall and a yes/no answer for whether the deposit matches Stripe's net.",
    passesTo: "Hands the explained payout to the Bank Agent and Cash Reconciliation Agent.",
  },
  bank: {
    name: "Bank Agent",
    role: "Reads bank activity and provides the cash transactions that Maximor needs to reconcile against the accounting ledger.",
    example: "It lands each deposit and withdrawal from the bank feed so cash reconciliation can look for a matching ledger explanation.",
    inputs: "Bank statement lines and corporate-card charges.",
    outputs: "Canonical bank transactions used by cash reconciliation.",
    passesTo: "Hands bank lines to the Cash Reconciliation Agent. A card charge is not treated as a vendor bill.",
  },
  books: {
    name: "Books Agent",
    role: "Provides the company's accounting records: the general ledger, vendor and customer records, purchase orders, and period-close information.",
    example: "When another agent needs the authorized purchase order or a ledger cash entry, the Books Agent supplies the official record.",
    inputs: "ERP and accounting-system records (ledger, vendors, customers, POs, period lock).",
    outputs: "Read-only accounting records other agents can rely on.",
    passesTo: "Serves every operating agent; it does not close the period itself.",
  },
  ap: {
    name: "Accounts Payable Agent",
    role: "Checks vendor bills before they are paid. It compares invoices with purchase orders and proof that goods or services were received, detects duplicates, and identifies exceptions.",
    example: "A clean Acme invoice that matches its purchase order and receiving record is approved. A second copy of the same Northline bill is held as a duplicate.",
    inputs: "Vendor invoices, purchase orders, goods receipts, and prior vendor decisions.",
    outputs: "Approve or hold decisions, exception reasons, and links to later payment records.",
    passesTo: "Approved bills go to the Payments Agent. Held bills stay with payables until the exception is resolved. Payables Control independently verifies match decisions.",
  },
  pay: {
    name: "Payments Agent",
    role: "Builds the proposed vendor-payment schedule from bills that have already passed Maximor's payable checks.",
    example: "Once invoices are approved, this agent decides which bills belong in this week's payment run based on due dates, cash, and discounts — it does not move money on its own.",
    inputs: "The approved bill pool, cash position, and treasury policies.",
    outputs: "A draft weekly payment plan.",
    passesTo: "Sends the draft plan to the Payables Control Agent for concurrence before any cash is released.",
  },
  apply: {
    name: "Cash Application Agent",
    role: "Matches incoming customer payments to the customer invoices those payments settle.",
    example: "If Lumen Labs sends $5,000 labeled only 'September billing,' this agent tries to determine which Lumen invoices that money belongs to — and leaves it unmatched when the evidence is not strong enough.",
    inputs: "Customer payments, remittance text, open invoices, and prior cash-application precedents.",
    outputs: "Applied, partially applied, or unmatched payment decisions.",
    passesTo: "Hands uncertain applications to Cash Control. Remaining unpaid invoices go to the Collections Agent.",
  },
  collect: {
    name: "Collections Agent",
    role: "Tracks unpaid customer invoices and identifies overdue balances that need collection follow-up.",
    example: "It looks at invoice aging and decides which customers are late enough to chase, after cash application has already applied any incoming payments.",
    inputs: "Open customer invoices, aging, payment history, and collection policy.",
    outputs: "Follow-up recommendations for overdue customers.",
    passesTo: "Works after cash application. Write-off or reserve proposals go to control agents.",
  },
  cash: {
    name: "Cash Reconciliation Agent",
    role: "Matches bank activity to accounting records and explains differences such as grouped payments, bank fees, and unresolved discrepancies.",
    example: "It matches a $30,000 bank withdrawal to three vendor invoices, nets a wire against its bank fee, and leaves the $12.40 Northstar difference unresolved when no evidence exists.",
    inputs: "Bank transactions, ledger cash entries, fee evidence, and Stripe payout explanations.",
    outputs: "Match decisions, explained exceptions, and unresolved differences.",
    passesTo: "Sends material reconciling items to Cash Control. Unresolved cash differences block month-end close.",
  },
  close: {
    name: "Month-End Close Agent",
    role: "Coordinates the work needed to finish a month's books, including accruals, prepaids, fixed assets, reconciliations, and final close checks.",
    example: "When Harbor Electric's September bill has not arrived, this agent estimates the electricity expense so September still includes the cost.",
    inputs: "Close checklist, vendor history, contracts, prepaid schedules, asset records, and cash status.",
    outputs: "Accruals, prepaid treatments, depreciation, close-task status, and journal entries.",
    passesTo: "Hands treatments and the period lock to the Books Control Agent. Asks cash, payables, and receivables agents for current status.",
  },
  story: {
    name: "Reporting Agent",
    role: "Explains what changed in the company's cash and results. It builds the 13-week cash forecast, variance analysis, and board-facing financial narrative.",
    example: "It projects weekly ending cash from expected customer collections, vendor payments, and payroll, then explains why this month's margin moved.",
    inputs: "Ledger actuals, forecast assumptions, collections timing, and payment schedules.",
    outputs: "13-week cash forecast, variance explanations, and board metrics tied to the books.",
    passesTo: "Reads close and cash results; does not move money or own the books.",
  },
  "ctl-pay": {
    name: "Payables Control Agent",
    role: "Independently checks accounts-payable match decisions and proposed payment plans before they become final. It looks for reasons to refuse, not reasons to wave things through.",
    example: "If payables approved a bill, this agent re-checks the invoice, purchase order, and receiving record and only concurs when the packet is complete.",
    inputs: "AP match packets, payment-run drafts, and company policy.",
    outputs: "Concurrence or refusal on match and payment-plan decisions.",
    passesTo: "Returns a verified decision to the Accounts Payable and Payments agents. It does not ask a person to intervene.",
  },
  "ctl-cash": {
    name: "Cash Control Agent",
    role: "Independently checks cash-application and bank-reconciliation decisions before they are accepted as complete.",
    example: "If cash reconciliation claims a fee-netted match, this agent verifies the bank line, ledger entries, and fee evidence before concurring.",
    inputs: "Cash-application packets and bank-reconciliation proposals.",
    outputs: "Concurrence or refusal on cash matches.",
    passesTo: "Returns verified cash decisions to the Cash Application and Cash Reconciliation agents.",
  },
  "ctl-books": {
    name: "Books Control Agent",
    role: "Independently checks month-end accounting treatments and whether the period is actually ready to lock.",
    example: "It reviews the Harbor Electric accrual, prepaid amortization, asset depreciation, and balance-sheet recs, and will not lock the month while cash is still unresolved.",
    inputs: "Accrual, prepaid, asset, and balance-sheet packets plus close-gate results.",
    outputs: "Concurrence on treatments and the period lock.",
    passesTo: "Returns verified close treatments to the Month-End Close Agent.",
  },
  audit: {
    name: "Audit Agent",
    role: "Independently inspects transactions and accounting records for signs that company controls were broken or records do not agree. It does not operate the books.",
    example: "It flags an invoice that the same user requested and approved, two bills that look like the same vendor invoice, and round-number payments that need extra testing.",
    inputs: "Invoices, payments, journals, vendors, and approval records sampled after the fact.",
    outputs: "Control findings with source evidence.",
    passesTo: "Reports independently. It does not fix or re-post the books.",
  },
};

export const WORKFLOW_COPY: Record<string, string> = {
  email: "email intake",
  stripe: "Stripe payout explanation",
  bank: "bank feed",
  books: "accounting records",
  ap: "accounts payable review",
  pay: "vendor payment scheduling",
  apply: "customer cash application",
  collect: "collections follow-up",
  cash: "bank reconciliation",
  close: "month-end close",
  story: "forecast and reporting",
  "ctl-pay": "payables control check",
  "ctl-cash": "cash control check",
  "ctl-books": "books control check",
  audit: "independent audit",
  memory: "decision memory",
  ingest: "document intake",
  "invoice-ingestion": "invoice intake",
  inbox: "inbox handoff",
  "cfo-cycle": "full Office of the CFO cycle",
  evaluate: "evaluation run",
  accrual: "missing-bill accrual",
  forecast: "13-week cash forecast",
};

export const CAPABILITY_COPY: Record<string, string> = {
  "ingestion.classify_document": "Tell invoices apart from quotes, receipts, and other documents",
  "ap.three_way_match": "Compare a vendor bill with its purchase order and receiving record",
  "ap.payment_scheduling": "Decide which approved vendor bills belong in the payment run",
  "ar.aging_collections": "Group unpaid invoices by how late they are and choose follow-up",
  "ar.cash_application": "Match customer payments to the invoices they settle",
  "cash.bank_reconciliation": "Match bank activity to ledger cash entries",
  "close.accruals": "Estimate expenses that belong in the month before the bill arrives",
  "close.prepaids": "Spread prepaid costs across the months they cover",
  "close.fixed_assets": "Record equipment as an asset and spread its cost over time",
  "close.balance_sheet_recs": "Check that balance-sheet accounts agree with supporting records",
  "close.month_end": "Coordinate finishing the month's books",
  "audit.controls": "Re-test whether company controls were followed",
  "reporting.variance_board": "Explain why results changed and prepare board figures",
  "forecast.thirteen_week": "Project cash on hand for the next 13 weeks",
  "memory.cross_period": "Reuse a prior-period decision only when current evidence still supports it",
};

export const EVAL_CASE_COPY: Record<string, { title: string; test: string }> = {
  "AC-EMAIL-CLEAN": {
    title: "Correctly classify a normal invoice",
    test: "A vendor emails a real invoice. Maximor should recognize it as a bill and extract the invoice number.",
  },
  "AC-EMAIL-QUOTE": {
    title: "Reject a quote that looks like an invoice",
    test: "A vendor sends a quotation. Maximor should not treat it as a bill to pay.",
  },
  "AC-AP-PREPARER-CLEAN": {
    title: "Approve a clean three-way match",
    test: "The invoice, purchase order, and receiving record agree. Maximor should approve the bill.",
  },
  "AC-AP-INVESTIGATOR-ALIAS": {
    title: "Approve a known vendor operating under another name",
    test: "The bill uses a vendor alias already established last period. Maximor should reuse that precedent and approve.",
  },
  "AC-AP-DUP": {
    title: "Detect a duplicate invoice",
    test: "Two vendor bills appear to request payment for the same Northline invoice. Maximor should hold the duplicate.",
  },
  "AC-SCHEDULER-DUE": {
    title: "Include a due vendor bill in the payment run",
    test: "An approved bill is due. Maximor should treat it as eligible for this week's payments.",
  },
  "AC-COLLECTIONS": {
    title: "Flag a customer invoice more than 90 days overdue",
    test: "An old unpaid invoice should land in the 90+ aging group and receive collection follow-up, not 'no action.'",
  },
  "AC-CASH-APPLY-EXACT": {
    title: "Apply an exact customer payment",
    test: "A customer payment clearly belongs to one invoice. Maximor should apply it automatically.",
  },
  "AC-CASH-APPLY-AMBIGUOUS": {
    title: "Leave an ambiguous customer payment unmatched",
    test: "Lumen Labs paid $5,000 with only 'September billing' as the description. Maximor should not guess which invoice it belongs to.",
  },
  "AC-CASH-RECON-1240": {
    title: "Detect the unexplained $12.40 bank difference",
    test: "Northstar's bank deposit is $12.40 higher than the invoice. Maximor should leave the difference unresolved rather than invent an explanation.",
  },
  "AC-CASH-RECON-GROUPED": {
    title: "Match one payment to multiple invoices",
    test: "One bank withdrawal pays several vendor invoices. Maximor should group them into a single match.",
  },
  "AC-CASH-INVESTIGATOR": {
    title: "Refuse to invent an explanation for $12.40",
    test: "When evidence is missing, the investigator must not fabricate a fee or adjustment.",
  },
  "AC-CASH-REVIEWER": {
    title: "Match a transfer after subtracting the bank fee",
    test: "A wire lands net of a bank fee. Maximor should match bank, ledger, and fee evidence together.",
  },
  "AC-ACCRUAL": {
    title: "Estimate a missing Harbor Electric bill",
    test: "September electricity was used but the bill has not arrived. Maximor should record an accrual.",
  },
  "AC-PREPAID": {
    title: "Account for a prepaid expense",
    test: "A payment covers future months of coverage. Maximor should spread the cost rather than expense it all at once.",
  },
  "AC-ASSET": {
    title: "Treat a capital purchase as a fixed asset",
    test: "A qualifying equipment purchase should be capitalized and depreciated, not expensed immediately.",
  },
  "AC-BS-RECON": {
    title: "Keep the cash rec open while $12.40 is unexplained",
    test: "Balance-sheet cash cannot be finished while the Northstar difference is still unresolved.",
  },
  "AC-CLOSE-REVIEW": {
    title: "Block month-end close on the $12.40 difference",
    test: "Close should remain incomplete until the unexplained cash difference is resolved.",
  },
  "AC-CLOSE-MANAGER": {
    test: "The close coordinator should see that cash is still blocked and not mark the month closed.",
    title: "Coordinate close without forcing a close",
  },
  "AC-AUDITOR": {
    title: "Detect planted control failures",
    test: "Independent audit should find the duplicate vendor, duplicate invoice, round payment, post-close journal, and self-approval that were planted in the population.",
  },
  "AC-VARIANCE": {
    title: "Explain the gross-margin change",
    test: "September margin moved versus August. Maximor should point at the actual supplier and hosting cost drivers.",
  },
  "AC-FORECAST": {
    title: "Produce a 13-week cash forecast",
    test: "The forecast should contain 13 weekly ending-cash projections.",
  },
  "AC-FORECAST-VAR": {
    title: "Identify why the cash forecast missed",
    test: "A late customer collection and an unexpected vendor payment should be named as miss sources.",
  },
  "AC-BOARD": {
    title: "Tie board metrics to the general ledger",
    test: "Board figures must come from the same ledger accounts as the books, not a separate invented pack.",
  },
};

export const EXCEPTION_COPY: Record<string, string> = {
  duplicate: "This looks like a second copy of a bill Maximor already has.",
  vendor_mismatch: "The vendor name on the bill does not match the purchase order, but a known alias may explain it.",
  quantity_variance: "The quantity billed does not match what was ordered or received.",
  price_variance: "The price billed does not match the authorized purchase order.",
  missing_po: "No purchase order was found for this bill.",
  missing_receipt: "There is no receiving record showing the goods or services arrived.",
  self_approval: "The same person requested and approved this transaction.",
};

export const AGING_COPY: Record<string, string> = {
  CURRENT: "Not overdue yet",
  "1-30": "1–30 days overdue",
  "31-60": "31–60 days overdue",
  "61-90": "61–90 days overdue",
  "90+": "More than 90 days overdue",
};

export const GLOSSARY: Record<string, string> = {
  "Accounts payable": "Money the company owes vendors for bills that have arrived.",
  "Accounts receivable": "Money customers still owe the company for invoices it has already sent.",
  Aging: "Grouping unpaid invoices by how long they have been outstanding.",
  Remittance: "The payment message a customer sends with money, often naming invoices — and sometimes not.",
  "Cash application": "Matching money received from customers to the invoices those customers were paying.",
  Reconciliation: "Checking whether two independent records of the same money tell the same story.",
  "General ledger": "The company's official set of accounting records.",
  Accrual: "Recording an expense in the month it was incurred, before the invoice arrives.",
  "Prepaid expense": "A cost paid up front that should be spread across the months it covers.",
  "Journal entry": "The formal accounting record that increases one account and decreases another by the same amount.",
  Debit: "The left-hand side of a journal entry — here, usually the expense being recorded.",
  Credit: "The right-hand side of a journal entry — here, usually the liability or cash account.",
  Close: "Finishing a month's books so the financial statements include everything that belongs in that month.",
  Variance: "The difference between what was expected and what actually happened.",
  "13-week cash forecast": "A week-by-week estimate of how much money will be in the bank over the next 13 weeks.",
  Chargeback: "A customer dispute that pulls money back out of a card or Stripe payout.",
  "Three-way match": "Comparing a vendor invoice with the purchase order and the record that goods or services were received.",
  "Unapplied cash": "Customer money that has arrived but has not yet been matched to a specific invoice.",
  "Decision memory": "A saved record of how Maximor handled a finance decision, including the evidence and reason, so a later period can reuse or override it.",
};

export const KNOWN_ENUMS = {
  status: Object.keys(STATUS_COPY),
  decision: Object.keys(DECISION_COPY),
  matchType: Object.keys(MATCH_TYPE_COPY),
  method: Object.keys(METHOD_COPY),
  task: Object.keys(TASK_COPY),
  agent: Object.keys(AGENT_COPY),
  capability: Object.keys(CAPABILITY_COPY),
  evalCase: Object.keys(EVAL_CASE_COPY),
  aging: Object.keys(AGING_COPY),
};

export function looksLikeId(value: unknown): boolean {
  const raw = String(value ?? "").trim();
  if (!raw) return false;
  return /^(INV|PAY|TXN|GL|TASK|JE|ACC|HI|CTR|MSG|PO|GR|MEM|CASE|CUST|VEND|APR|PRE|AC|DOC|FEE|USR|CO)-[A-Z0-9._-]+$/i.test(raw);
}

export function formatStatus(value: unknown): string {
  if (value === true) return "Yes";
  if (value === false) return "No";
  if (looksLikeId(value)) return String(value);
  return lookup(STATUS_COPY, value, humanizeToken(value) || "—");
}

export function formatDecision(value: unknown): string {
  return lookup(DECISION_COPY, value, lookup(STATUS_COPY, value, humanizeToken(value) || "—"));
}

export function formatMatchType(value: unknown): string {
  return lookup(MATCH_TYPE_COPY, value, humanizeToken(value) || "—");
}

export function formatMatchSentence(value: unknown): string {
  return lookup(MATCH_TYPE_SENTENCE, value, formatMatchType(value));
}

export function formatAccountingMethod(value: unknown): string {
  return lookup(METHOD_COPY, value, humanizeToken(value) || "—");
}

export function formatControlResult(value: unknown): string {
  return lookup(STATUS_COPY, value, humanizeToken(value) || "—");
}

export function formatWorkflow(value: unknown): string {
  return lookup(WORKFLOW_COPY, value, humanizeToken(value) || "workflow");
}

export function formatAgent(value: unknown): string {
  const key = String(value || "").trim();
  if (AGENT_COPY[key]) return AGENT_COPY[key].name;
  const slug = key.replace(/_/g, "-").replace(/^bot-/, "");
  if (AGENT_COPY[slug]) return AGENT_COPY[slug].name;
  return humanizeToken(key) || "Agent";
}

export function formatRecordType(value: unknown): string {
  const table: Record<string, string> = {
    email: "Email",
    invoice: "Vendor invoice",
    customer_invoice: "Customer invoice",
    purchase_order: "Purchase order",
    goods_receipt: "Receiving record",
    bank_transaction: "Bank transaction",
    ledger_entry: "Ledger cash entry",
    journal_entry: "Journal entry",
    stripe_payout: "Stripe payout",
    stripe_balance_txn: "Stripe balance transaction",
    decision_memory: "Saved decision",
    historical_invoice: "Prior monthly bill",
    payment: "Payment",
    remittance: "Customer payment",
  };
  return lookup(table, value, humanizeToken(value) || "Record");
}

export function formatTask(value: unknown): string {
  return lookup(TASK_COPY, value, humanizeToken(value) || "Close task");
}

export function formatAgingBucket(value: unknown): string {
  return lookup(AGING_COPY, value, humanizeToken(value) || "—");
}

export function formatCapability(value: unknown): string {
  return lookup(CAPABILITY_COPY, value, humanizeToken(value) || "—");
}

export function formatException(value: unknown): string {
  return lookup(EXCEPTION_COPY, value, humanizeToken(value) || "—");
}

export function formatEvalCase(caseId: unknown): { title: string; test: string; id: string } {
  const id = String(caseId || "");
  const known = EVAL_CASE_COPY[id];
  return {
    id,
    title: known?.title || humanizeToken(id.replace(/^AC-/, "")) || id,
    test: known?.test || "This case compares Maximor's result with a known expected outcome.",
  };
}

export function formatWeekDate(value: unknown): string {
  const raw = String(value || "");
  const match = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) return raw || "—";
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const month = months[Number(match[2]) - 1];
  return month ? `${month} ${Number(match[3])}` : raw;
}

export function formatFieldKey(key: string): string {
  const table: Record<string, string> = {
    cash: "Cash in bank",
    ap_outstanding: "Unpaid vendor bills",
    ar_outstanding: "Unpaid customer invoices",
    close_status: "Month-end status",
    exception_count: "Open exceptions",
    journal_count: "Journal entries",
    decision_memory_count: "Saved decisions",
    projected_ending_cash: "Forecast ending cash",
    unreconciled_item: "Unresolved bank item",
    match_status: "Match result",
    duplicate_status: "Duplicate check",
    payment_state: "Payment status",
    accounting_status: "Accounting status",
    invoice_id: "Invoice",
  };
  return table[key] || humanizeToken(key);
}

export function explainCashMatch(item: any): { title: string; body: string } {
  const type = String(item?.match_type || "");
  const bank = usd(item?.bank_amount);
  const ledger = usd(item?.ledger_amount);
  const diff = usd(Math.abs((Number(item?.bank_amount) || 0) - (Number(item?.ledger_amount) || 0)));
  const title = formatMatchType(type);
  if (type === "UNEXPLAINED_DIFFERENCE") {
    return {
      title,
      body: `The bank shows ${bank} while the ledger records ${ledger}. Maximor searched for a fee, adjustment, or invoice difference and could not find evidence for the extra ${diff}.`,
    };
  }
  if (type === "GROUPED_MATCH") {
    const count = (item?.ledger_entry_ids || []).length;
    return {
      title,
      body: `One ${bank} bank movement corresponds to ${count || "several"} ledger entries totaling ${ledger}.`,
    };
  }
  if (type === "FEE_NETTED") {
    return {
      title,
      body: `A ${bank} bank transfer matches ${ledger} in the ledger after accounting for the bank fee.`,
    };
  }
  if (type === "PROVIDER_PAYOUT") {
    return {
      title,
      body: `A Stripe payout of ${bank} matches the bank deposit after charges, refunds, disputes, and fees.`,
    };
  }
  if (type === "EXACT_MATCH") {
    return { title, body: `Bank ${bank} matches ledger ${ledger} exactly.` };
  }
  return { title, body: formatMatchSentence(type) };
}

export function formatHandoff(bots: unknown, workflow?: unknown): string {
  const slugs = Array.isArray(bots) ? bots.map(String).filter(Boolean) : [];
  if (!slugs.length) {
    return workflow ? `${formatAgent(workflow)} completed ${formatWorkflow(workflow)}.` : "";
  }
  if (slugs.length === 1) {
    return `${formatAgent(slugs[0])} completed ${formatWorkflow(workflow || slugs[0])}.`;
  }
  const names = slugs.map(formatAgent);
  const last = names[names.length - 1];
  const lead = names.slice(0, -1).join(", ");
  return `${lead} handed work to ${last} so ${formatWorkflow(workflow || slugs[0])} could continue.`;
}

export function formatStage(stage: any): { label: string; detail?: string } {
  const bot = formatAgent(stage?.bot || stage?.slug);
  const raw = String(stage?.label || stage?.id || "");
  const known: Record<string, string> = {
    memory: `${bot} retrieved the prior-period decision.`,
    ap: `${bot} reviewed featured vendor bills.`,
    ar: `${bot} applied or evaluated customer payments.`,
    cash: `${bot} reconciled bank activity to the ledger.`,
    close: `${bot} ran the month-end close checklist.`,
    reporting: `${bot} refreshed the cash forecast and variance explanation.`,
    audit: `${bot} independently re-tested company controls.`,
    ingest: `${bot} classified the incoming document.`,
    match: `${bot} compared the bill with its purchase order and receiving record.`,
    apply: `${bot} tried to match the customer payment to invoices.`,
  };
  return {
    label: known[stage?.id] || stage?.label || `${bot} ran ${formatWorkflow(raw)}.`,
    detail: stage?.detail,
  };
}

export function friendlyExpected(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value !== "object") return formatStatus(value);
  const row = value as Record<string, unknown>;
  const parts: string[] = [];
  if (row.classification) parts.push(`Treat the document as: ${formatStatus(row.classification)}.`);
  if (row.invoice_number) parts.push(`Extract invoice number ${row.invoice_number}.`);
  if (row.decision) parts.push(formatDecision(row.decision));
  if (Array.isArray(row.exceptions)) {
    parts.push(row.exceptions.length ? `Flag: ${(row.exceptions as string[]).map(formatException).join("; ")}.` : "No exceptions.");
  }
  if (row.aging_bucket) parts.push(`Aging group: ${formatAgingBucket(row.aging_bucket)}.`);
  if (Array.isArray(row.invoice_ids)) parts.push(`Apply to ${(row.invoice_ids as string[]).join(", ")}.`);
  if (row.status) parts.push(formatStatus(row.status));
  if (row.match_type) parts.push(formatMatchType(row.match_type));
  if (row.difference_cents != null) parts.push(`Difference of ${usd(Number(row.difference_cents) / 100)}.`);
  if (row.needed === true) parts.push("An accrual is required.");
  if (row.treatment) parts.push(formatAccountingMethod(row.treatment));
  if (row.period_status) parts.push(`Period status: ${formatStatus(row.period_status)}.`);
  if (row.blocked === true) parts.push("Close remains blocked.");
  if (row.cash_open === true) parts.push("Cash reconciliation is still open.");
  if (row.week_count) parts.push(`Produce ${row.week_count} weekly cash projections.`);
  if (row.invented_explanation === false) parts.push("Do not invent an explanation.");
  if (row.metrics_tie_to_gl === true) parts.push("Board metrics must tie to the general ledger.");
  if (Array.isArray(row.findings_include)) parts.push("Findings must include the planted source records.");
  if (Array.isArray(row.miss_sources)) parts.push("Name the actual forecast-miss sources.");
  if (row.eligible === true) parts.push("The bill is eligible for the payment run.");
  if (row.august != null && row.september != null) parts.push(`Gross margin moves from ${Number(row.august) * 100}% to ${Number(row.september) * 100}%.`);
  if (!parts.length) return "See developer details for the machine-readable fields.";
  return parts.join(" ");
}

export function idsOf(...groups: Array<unknown>): string[] {
  const out: string[] = [];
  for (const group of groups) {
    if (!group) continue;
    if (Array.isArray(group)) {
      for (const item of group) {
        if (typeof item === "string" && item.trim()) out.push(item);
        else if (item && typeof item === "object") {
          const row = item as Record<string, unknown>;
          const id = row.id || row.invoice_id || row.payment_id || row.artifact_id || row.transaction_id;
          if (typeof id === "string") out.push(id);
        }
      }
    } else if (typeof group === "string") {
      out.push(group);
    }
  }
  return Array.from(new Set(out.filter(Boolean)));
}

export const GRAIN_SLUGS = Object.keys(AGENT_COPY);

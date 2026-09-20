import type { AgentSlug } from "./agents";

export type Simulation = {
  id: string;
  title: string;
  scenario: string;
  difficulty: string;
  agents: AgentSlug[];
  process: string[];
  expected: string;
  href: string;
  runner?: string;
  evalCases?: string[];
  featured?: boolean;
};

export const SIMULATIONS: Simulation[] = [
  {
    id: "duplicate-invoice",
    title: "Duplicate vendor invoice",
    scenario: "A vendor sends the same invoice twice with slightly different files.",
    difficulty: "The system must recognize that the underlying obligation already exists rather than paying twice.",
    agents: ["ap", "ctl-pay"],
    process: [
      "The second Northline bill arrives in payables.",
      "Payables compares vendor, amount, and invoice identity with bills already on file.",
      "Payables Control can recheck the hold before the bill would enter a payment run.",
    ],
    expected: "The second bill is held as a duplicate rather than approved for payment.",
    href: "/ap",
    runner: "ap",
    evalCases: ["AC-AP-DUP"],
    featured: true,
  },
  {
    id: "messy-invoice",
    title: "Messy scanned invoice",
    scenario: "A poorly scanned Northline invoice lands in finance email.",
    difficulty: "The document must be identified as a bill and its fields read before anyone books an amount owed.",
    agents: ["email", "ap"],
    process: [
      "Email intake classifies the attachment.",
      "Invoice fields are extracted.",
      "Payables then checks the bill against company records.",
    ],
    expected: "The document is treated as an invoice only if it actually is one, with extracted invoice identity.",
    href: "/inbox",
    runner: "inbox",
    evalCases: ["AC-EMAIL-CLEAN"],
    featured: true,
  },
  {
    id: "document-trap",
    title: "Quote that looks like a bill",
    scenario: "A vendor sends a quotation, or a voided invoice, that resembles a bill.",
    difficulty: "A naive system books anything that says 'invoice' in the filename.",
    agents: ["email", "ap", "ctl-pay"],
    process: [
      "Inbox classifies the document.",
      "Quotes and voided files are not treated as money owed.",
      "Payables never receives a fake obligation from a quote.",
    ],
    expected: "The document is not treated as a vendor invoice to pay.",
    href: "/evaluations",
    evalCases: ["AC-EMAIL-QUOTE"],
    featured: true,
  },
  {
    id: "three-way-match",
    title: "Bill that does not match the order",
    scenario: "An invoice disagrees with the purchase order or the receiving record.",
    difficulty: "Paying it would send cash for the wrong quantity, price, or goods that never arrived.",
    agents: ["ap", "ctl-pay"],
    process: [
      "Payables compares the bill, the purchase order, and the receiving record.",
      "Mismatches are held.",
      "Payables Control rechecks the packet.",
    ],
    expected: "The bill is held until the mismatch is resolved, not approved.",
    href: "/ap",
    runner: "ap",
    evalCases: ["AC-AP-PREPARER-CLEAN"],
  },
  {
    id: "payment-decision",
    title: "Weekly vendor payment plan",
    scenario: "Approved bills sit in a pool. Cash on hand and due dates decide what belongs in this week's run.",
    difficulty: "The planner must not pay held bills, and it must not move money on its own.",
    agents: ["pay", "ctl-pay"],
    process: [
      "Payments reads the approved pool and cash position.",
      "It drafts invoice IDs for this week's run.",
      "Payables Control rechecks the draft before any cash would be released.",
    ],
    expected: "Due, already-approved bills are eligible; the draft is independently rechecked.",
    href: "/ap",
    runner: "ap",
    evalCases: ["AC-SCHEDULER-DUE"],
  },
  {
    id: "bank-exception",
    title: "Unexplained $12.40 bank difference",
    scenario: "Northstar's bank deposit is $12.40 higher than the invoice. Other lines include grouped payments and fee-netted wires.",
    difficulty: "The system must match what it can explain and refuse to invent a story for the rest.",
    agents: ["cash", "ctl-cash"],
    process: [
      "Cash reconciliation matches grouped payments and fee-netted wires.",
      "It searches for a fee, adjustment, or invoice difference for the extra $12.40.",
      "With no evidence, the difference stays unresolved and Cash Control can recheck the packet.",
    ],
    expected: "The $12.40 difference remains unresolved. Month-end close stays blocked.",
    href: "/cash",
    runner: "cash",
    evalCases: ["AC-CASH-RECON-1240", "AC-CASH-INVESTIGATOR", "AC-CLOSE-REVIEW"],
    featured: true,
  },
  {
    id: "stripe-payout",
    title: "Stripe payout to the bank",
    scenario: "A Stripe payout includes charges, refunds, disputes, and fees, then lands as one bank deposit.",
    difficulty: "The net must be reconstructed. A naive match of 'Stripe paid us X' hides refunds and chargebacks.",
    agents: ["stripe", "cash"],
    process: [
      "The Stripe Agent unpacks the payout waterfall.",
      "Cash reconciliation matches the explained net to the bank deposit.",
      "A broken waterfall is handed to Cash Control.",
    ],
    expected: "Gross charges minus refunds, disputes, and fees equal the bank deposit.",
    href: "/stripe",
    runner: "stripe",
  },
  {
    id: "stripe-to-books",
    title: "Stripe charges onto the books",
    scenario: "The same payout must also be understandable as ledger cash, not only as a processor report.",
    difficulty: "Processor activity, the bank, and the general ledger have to tell one story.",
    agents: ["stripe", "cash", "close"],
    process: [
      "Stripe explains charges, refunds, fees, and chargebacks.",
      "Cash reconciliation consumes that explanation.",
      "Close later sees the cash interpretation for the period.",
    ],
    expected: "One payout, one bank deposit, one cash interpretation.",
    href: "/stripe",
    runner: "stripe",
  },
  {
    id: "month-end-accrual",
    title: "Missing Harbor Electric bill",
    scenario: "September electricity was used. The bill has not arrived.",
    difficulty: "Leaving it out would understate the month. Inventing a random number would overstate it.",
    agents: ["close", "ctl-books"],
    process: [
      "Close looks for a missing recurring cost.",
      "It estimates from the contract and recent bills, and can retrieve last month's saved decision.",
      "Books Control rechecks the treatment before it is treated as final.",
    ],
    expected: "An accrual is recorded so September includes the electricity cost.",
    href: "/close",
    runner: "close",
    evalCases: ["AC-ACCRUAL"],
    featured: true,
  },
  {
    id: "cross-period-memory",
    title: "Memory across August and September",
    scenario: "Harbor Electric was estimated in August. September is missing the bill again.",
    difficulty: "September should not be a blank slate, and it also should not paste last month's number without looking.",
    agents: ["close", "ctl-books"],
    process: [
      "August's evidence, method, amount, and reason were saved.",
      "September retrieves that decision.",
      "Current evidence is re-checked before the method is reused or changed.",
    ],
    expected: "September references August, then re-evaluates. The saved reason stays inspectable.",
    href: "/memory",
    runner: "memory",
    featured: true,
  },
  {
    id: "self-correction",
    title: "Later evidence corrects an estimate",
    scenario: "August estimated Harbor Electric. A later actual bill arrives.",
    difficulty: "An estimate that was reasonable in August may need a correcting entry once the real bill exists.",
    agents: ["close", "ctl-books"],
    process: [
      "The original estimate and reason are still on file.",
      "The later bill is compared with that estimate.",
      "Close records the correction instead of pretending the estimate was the final truth.",
    ],
    expected: "The books are corrected from the new evidence, with the original decision still visible.",
    href: "/memory",
    runner: "memory",
  },
  {
    id: "audit-controls",
    title: "Planted control failures",
    scenario: "After operations have recorded the books, independent audit samples the population.",
    difficulty: "Audit must find the duplicate vendor, duplicate invoice, round payment, post-close journal, and self-approval that were planted — without being the team that booked them.",
    agents: ["audit"],
    process: [
      "Operations have already recorded invoices, payments, and journals.",
      "Audit samples and re-performs.",
      "Findings are written with source evidence. Audit does not fix the books.",
    ],
    expected: "Planted control failures are reported as findings.",
    href: "/audit",
    runner: "audit",
    evalCases: ["AC-AUDITOR"],
  },
  {
    id: "forecast-miss",
    title: "Why the cash forecast missed",
    scenario: "Ending cash and gross margin moved. The system has to name the actual transactions, not a vibe.",
    difficulty: "A late customer collection and an unexpected vendor payment should be traceable from the same books.",
    agents: ["story"],
    process: [
      "Reporting reads ledger actuals, collections timing, and payment schedules.",
      "It projects 13 weekly ending-cash figures.",
      "A miss is traced to source transactions.",
    ],
    expected: "A 13-week forecast exists, and named miss sources match the books.",
    href: "/forecast",
    runner: "forecast",
    evalCases: ["AC-FORECAST", "AC-FORECAST-VAR"],
  },
  {
    id: "cfo-cycle",
    title: "Connected Office of the CFO cycle",
    scenario: "Vendor bills, customer payments, bank activity, month-end close, forecast, audit, and memory run against one company picture.",
    difficulty: "Every workflow has to agree on the same bills, the same cash, and the same unresolved $12.40.",
    agents: ["email", "ap", "pay", "apply", "cash", "close", "story", "audit"],
    process: [
      "Payables, receivables, and cash run against the live demo books.",
      "Close, forecast, and audit consume those results.",
      "Saved decisions persist for the next period.",
    ],
    expected: "Company state changes only where the agents actually posted. Close stays blocked on the unexplained bank difference.",
    href: "/",
    runner: "cfo-cycle",
    featured: true,
  },
];

export const SIMULATIONS_BY_ID = Object.fromEntries(SIMULATIONS.map((item) => [item.id, item]));

export const LIVE_RUNNERS = [
  { id: "inbox", href: "/inbox", title: "Inbox", agents: ["email"] as AgentSlug[] },
  { id: "ap", href: "/ap", title: "Accounts payable", agents: ["ap", "pay", "ctl-pay"] as AgentSlug[] },
  { id: "ar", href: "/ar", title: "Accounts receivable", agents: ["apply", "collect"] as AgentSlug[] },
  { id: "cash", href: "/cash", title: "Cash reconciliation", agents: ["cash", "ctl-cash"] as AgentSlug[] },
  { id: "stripe", href: "/stripe", title: "Stripe", agents: ["stripe", "cash"] as AgentSlug[] },
  { id: "close", href: "/close", title: "Month-end close", agents: ["close", "ctl-books"] as AgentSlug[] },
  { id: "forecast", href: "/forecast", title: "Cash forecast", agents: ["story"] as AgentSlug[] },
  { id: "audit", href: "/audit", title: "Audit", agents: ["audit"] as AgentSlug[] },
  { id: "memory", href: "/memory", title: "Decision memory", agents: ["close"] as AgentSlug[] },
];

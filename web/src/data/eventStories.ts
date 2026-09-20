import type { FlowEdge, FlowNode, FlowStep } from "../components/FlowPlay";

export interface EventStory {
  readonly id: string;
  readonly label: string;
  readonly nodes: readonly FlowNode[];
  readonly edges: readonly FlowEdge[];
  readonly steps: readonly FlowStep[];
}

export const DEFAULT_HOME_EVENT = "vendor-invoice";

const VENDOR_INVOICE: EventStory = {
  id: "vendor-invoice",
  label: "Vendor invoice PDF",
  nodes: [
    { id: "event", label: "Vendor invoice PDF", kind: "event", column: 0 },
    { id: "email", label: "Email", kind: "source", room: "intake", column: 1 },
    { id: "ap", label: "AP", kind: "operator", room: "pay", column: 2 },
    { id: "ctl-pay", label: "ctl-pay", kind: "verifier", room: "pay", column: 3 },
    { id: "pay", label: "Pay", kind: "operator", room: "pay", column: 4 },
  ],
  edges: [
    { id: "e-event-email", from: "event", to: "email", label: "bill" },
    { id: "e-email-ap", from: "email", to: "ap", label: "bill" },
    { id: "e-ap-ctl", from: "ap", to: "ctl-pay", label: "approve" },
    { id: "e-ctl-pay", from: "ctl-pay", to: "pay", label: "payable" },
  ],
  steps: [
    {
      id: "vi-event",
      title: "Vendor emails a bill",
      nodeId: "event",
      body: "A vendor invoice PDF lands in finance mail. Nothing is booked yet.",
      manipulations: ["land document"],
    },
    {
      id: "vi-email",
      title: "Email classifies the attachment",
      nodeId: "email",
      body: "This is a bill, not a quote, statement, or receipt.",
      manipulations: ["classify document", "extract fields", "refuse to treat a quote as a bill"],
      handoff: {
        to: "ap",
        why: "A vendor invoice in email is handed to payables so it can be checked before anyone treats it as money owed.",
      },
    },
    {
      id: "vi-ap",
      title: "AP checks the packet",
      nodeId: "ap",
      body: "Invoice, purchase order, and receiving record must agree. A second copy of the same bill is held.",
      manipulations: ["three-way match invoice / PO / GR", "duplicate check"],
      handoff: {
        to: "ctl-pay",
        why: "A bill that looks ready is independently rechecked by Payables Control before it counts as approved.",
      },
      artifactIds: ["INV-001"],
    },
    {
      id: "vi-ctl-pay",
      title: "ctl-pay concurs or refuses",
      nodeId: "ctl-pay",
      body: "Payables Control looks for reasons to refuse. Unresolved evidence stays with this verifier — not a person.",
      manipulations: ["concur or refuse", "never ask a person"],
      artifactIds: ["INV-001"],
    },
    {
      id: "vi-pay",
      title: "Pay drafts the weekly run",
      nodeId: "pay",
      body: "Approved bills can enter this week's draft. Cash still does not move.",
      manipulations: ["draft weekly run", "still does not move money"],
      handoff: {
        to: "pay",
        why: "Bills that have cleared payable checks are handed to payments to draft the weekly run.",
      },
      artifactIds: ["INV-001"],
    },
  ],
};

const CUSTOMER_REMITTANCE: EventStory = {
  id: "customer-remittance",
  label: "Customer remittance",
  nodes: [
    { id: "event", label: "Remittance", kind: "event", column: 0 },
    { id: "email", label: "Email", kind: "source", room: "intake", column: 1 },
    { id: "apply", label: "Apply", kind: "operator", room: "cash", column: 2 },
    { id: "ctl-cash", label: "ctl-cash", kind: "verifier", room: "cash", column: 3 },
  ],
  edges: [
    { id: "e-event-email", from: "event", to: "email", label: "remittance" },
    { id: "e-email-apply", from: "email", to: "apply", label: "remittance" },
    { id: "e-apply-ctl", from: "apply", to: "ctl-cash", label: "ambiguous" },
  ],
  steps: [
    {
      id: "cr-event",
      title: "Payment notice with a weak memo",
      nodeId: "event",
      body: "Lumen $5,000 labeled only “September billing”. That notice is PAY-004.",
      manipulations: ["land remittance"],
      artifactIds: ["PAY-004"],
    },
    {
      id: "cr-email",
      title: "Email routes customer cash, not a vendor bill",
      nodeId: "email",
      body: "The attachment is a remittance. It is not handed to payables.",
      manipulations: ["classify remittance, not a vendor bill"],
      handoff: {
        to: "apply",
        why: "A customer payment notice is handed to cash application so the money can be matched to invoices.",
      },
      artifactIds: ["PAY-004"],
    },
    {
      id: "cr-apply",
      title: "Apply chooses among Kernel candidates",
      nodeId: "apply",
      body: "PAY-004 must not auto-apply. The memo does not identify which Lumen invoices to settle.",
      manipulations: ["choose among Kernel candidates", "do not invent a combination"],
      handoff: {
        to: "ctl-cash",
        why: "If the payment cannot be matched with enough evidence, Cash Control reviews it instead of guessing.",
      },
      artifactIds: ["PAY-004"],
    },
    {
      id: "cr-ctl-cash",
      title: "ctl-cash fail-closes the ambiguous match",
      nodeId: "ctl-cash",
      body: "HUMAN_REVIEW here means unresolved — more evidence required. The $5,000 stays unapplied.",
      manipulations: ["fail-closed", "do not auto-apply PAY-004"],
      artifactIds: ["PAY-004"],
    },
  ],
};

const STRIPE_PAYOUT: EventStory = {
  id: "stripe-payout",
  label: "Stripe payout.paid",
  nodes: [
    { id: "event", label: "payout.paid", kind: "event", column: 0 },
    { id: "stripe", label: "Stripe", kind: "source", room: "intake", column: 1 },
    { id: "cash", label: "Cash", kind: "operator", room: "cash", column: 2, row: 0 },
    { id: "apply", label: "Apply", kind: "operator", room: "cash", column: 2, row: 1 },
    { id: "ctl-cash", label: "ctl-cash", kind: "verifier", room: "cash", column: 3, row: 1 },
  ],
  edges: [
    { id: "e-event-stripe", from: "event", to: "stripe", label: "payout" },
    { id: "e-stripe-cash", from: "stripe", to: "cash", label: "deposit" },
    { id: "e-stripe-apply", from: "stripe", to: "apply", label: "charges" },
    { id: "e-stripe-ctl", from: "stripe", to: "ctl-cash", label: "waterfall_break" },
  ],
  steps: [
    {
      id: "sp-event",
      title: "Processor payout",
      nodeId: "event",
      body: "Stripe emits payout.paid. The office must explain the deposit, not book a vendor bill.",
      manipulations: ["land payout"],
    },
    {
      id: "sp-stripe",
      title: "Stripe unpacks the waterfall",
      nodeId: "stripe",
      body: "Charges minus refunds minus disputes minus fees equal the deposit. This is not an InvoiceCandidate.",
      manipulations: ["unpack charges − refunds − disputes − fees = deposit", "not an InvoiceCandidate"],
      handoff: {
        to: "cash",
        why: "An explained Stripe payout is handed to cash reconciliation so the bank deposit can be tied to the books.",
      },
    },
    {
      id: "sp-cash",
      title: "Cash ties the deposit to the bank",
      nodeId: "cash",
      body: "The explained net is matched to the bank line. A broken waterfall would have already gone to ctl-cash.",
      manipulations: ["tie explained deposit to bank"],
      handoff: {
        to: "ctl-cash",
        why: "If Stripe's charges, refunds, fees, and payout do not add up, Cash Control rechecks the packet instead of forcing a match.",
      },
    },
    {
      id: "sp-apply",
      title: "Apply uses charge-level facts",
      nodeId: "apply",
      body: "Customer cash is applied from Stripe charges, not from inventing an invoice.",
      manipulations: ["charge-level facts for customer cash"],
      handoff: {
        to: "apply",
        why: "Stripe customer charges are handed to cash application because they represent money customers have already paid.",
      },
    },
  ],
};

const BANK_LINE: EventStory = {
  id: "bank-line",
  label: "Bank line",
  nodes: [
    { id: "event", label: "Bank line", kind: "event", column: 0 },
    { id: "bank", label: "Bank", kind: "source", room: "intake", column: 1 },
    { id: "cash", label: "Cash", kind: "operator", room: "cash", column: 2 },
    { id: "ctl-cash", label: "ctl-cash", kind: "verifier", room: "cash", column: 3 },
  ],
  edges: [
    { id: "e-event-bank", from: "event", to: "bank", label: "line" },
    { id: "e-bank-cash", from: "bank", to: "cash", label: "line" },
    { id: "e-cash-ctl", from: "cash", to: "ctl-cash", label: "sign-off" },
  ],
  steps: [
    {
      id: "bl-event",
      title: "Bank feed line",
      nodeId: "event",
      body: "A statement line arrives from the bank feed.",
      manipulations: ["land feed"],
    },
    {
      id: "bl-bank",
      title: "Bank lands the line",
      nodeId: "bank",
      body: "A card charge is not a vendor bill. The line is cash activity, nothing more.",
      manipulations: ["land the line", "a card charge is not a bill"],
      handoff: {
        to: "cash",
        why: "Each bank line is handed to cash reconciliation to look for a matching explanation in the ledger.",
      },
    },
    {
      id: "bl-cash",
      title: "Cash matches only with evidence",
      nodeId: "cash",
      body: "Bank-to-ledger matching requires evidence. No invented fee, no forced MATCHED.",
      manipulations: ["match bank to ledger only with evidence"],
      handoff: {
        to: "ctl-cash",
        why: "Material bank-rec proposals are independently rechecked before they are accepted as complete.",
      },
    },
    {
      id: "bl-ctl-cash",
      title: "ctl-cash sign-off",
      nodeId: "ctl-cash",
      body: "This line can be the unexplained $12.40 (TXN-2026-09-015). It is not marked matched.",
      manipulations: ["sign-off", "leave unexplained cash unresolved"],
      artifactIds: ["TXN-2026-09-015"],
    },
  ],
};

const DAILY_AGING: EventStory = {
  id: "daily-aging",
  label: "Daily aging",
  nodes: [
    { id: "event", label: "Aging routine", kind: "event", column: 0 },
    { id: "collect", label: "Collect", kind: "operator", room: "cash", column: 1 },
    { id: "apply", label: "Apply", kind: "operator", room: "cash", column: 2 },
    { id: "ctl-pay", label: "ctl-pay", kind: "verifier", room: "pay", column: 2 },
    { id: "world", label: "World", kind: "source", column: 3, row: 1, status: "not-attached" },
  ],
  edges: [
    { id: "e-event-collect", from: "event", to: "collect", label: "daily-aging" },
    { id: "e-collect-apply", from: "collect", to: "apply", label: "dirty cash" },
    { id: "e-collect-ctl", from: "collect", to: "ctl-pay", label: "write-off" },
    {
      id: "e-collect-world",
      from: "collect",
      to: "world",
      label: "dun / send_office_outbound",
      attached: false,
    },
  ],
  steps: [
    {
      id: "da-event",
      title: "Daily aging after apply has drained deposits",
      nodeId: "event",
      body: "The unpaid-invoice routine runs only after cash application has already taken the deposits it can.",
      manipulations: ["wake collect"],
    },
    {
      id: "da-collect",
      title: "Collect enforces the decision",
      nodeId: "collect",
      body: "Do not chase a customer if unapplied cash might already be theirs.",
      manipulations: ["enforce_collection_decision", "do not chase if unapplied cash might be theirs"],
    },
    {
      id: "da-apply",
      title: "Dirty cash goes back to apply",
      nodeId: "apply",
      body: "Unapplied deposits are not treated as overdue. They return to cash application.",
      manipulations: ["return dirty cash"],
    },
    {
      id: "da-ctl-pay",
      title: "Write-off proposals hit ctl-pay",
      nodeId: "ctl-pay",
      body: "A proposed write-off is independently rechecked before the company changes what it claims it is owed.",
      manipulations: ["review write-off"],
      handoff: {
        to: "ctl-pay",
        why: "A proposed write-off or reserve is independently rechecked before it can change what the company claims it is owed.",
      },
    },
    {
      id: "da-world",
      title: "World send is not attached",
      nodeId: "world",
      body: "No collection email is sent. dun / send_office_outbound is not on the live Computer roster.",
      manipulations: ["not attached"],
      status: "not-attached",
    },
  ],
};

const MONTH_END: EventStory = {
  id: "month-end",
  label: "Month-end",
  nodes: [
    { id: "event", label: "Month-end routine", kind: "event", column: 0 },
    { id: "close", label: "Close", kind: "operator", room: "books-close", column: 1 },
    { id: "ctl-books", label: "ctl-books", kind: "verifier", room: "books-close", column: 2, status: "blocked" },
    { id: "story", label: "Story", kind: "assurance", room: "books-close", column: 3 },
    { id: "audit", label: "Audit", kind: "assurance", room: "books-close", column: 3 },
  ],
  edges: [
    { id: "e-event-close", from: "event", to: "close", label: "month-end" },
    { id: "e-close-ctl", from: "close", to: "ctl-books", label: "lock" },
    { id: "e-ctl-story", from: "ctl-books", to: "story", label: "pack-story" },
    { id: "e-ctl-audit", from: "ctl-books", to: "audit", label: "pack-audit" },
  ],
  steps: [
    {
      id: "me-event",
      title: "Month-end routine",
      nodeId: "event",
      body: "Close coordinates completeness work. It does not declare the period finished.",
      manipulations: ["wake close"],
    },
    {
      id: "me-close",
      title: "Close runs treatments",
      nodeId: "close",
      body: "Accrue, prepaid, assets, and balance-sheet recs. Close does not mark the month CLOSED.",
      manipulations: ["accrue", "prepaid", "assets", "BS", "do not mark CLOSED"],
      handoff: {
        to: "ctl-books",
        why: "The period lock is independently rechecked. Close does not mark the month closed on its own.",
      },
    },
    {
      id: "me-ctl-books",
      title: "ctl-books checks close gates",
      nodeId: "ctl-books",
      body: "Lock only if evaluate_close_gates passed. Unexplained cash is still a gate.",
      manipulations: ["evaluate_close_gates", "lock only if gates passed"],
    },
    {
      id: "me-block",
      title: "Period lock blocked",
      nodeId: "ctl-books",
      body: "Unexplained cash $12.40 on TXN-2026-09-015 keeps the lock refused. The month is not closed.",
      manipulations: ["refuse lock", "unexplained cash $12.40"],
      artifactIds: ["TXN-2026-09-015"],
      status: "blocked",
    },
  ],
};

export const HOME_EVENTS: readonly EventStory[] = [
  VENDOR_INVOICE,
  CUSTOMER_REMITTANCE,
  STRIPE_PAYOUT,
  BANK_LINE,
  DAILY_AGING,
  MONTH_END,
];

export function eventStoryById(id: string): EventStory {
  return HOME_EVENTS.find((item) => item.id === id) ?? VENDOR_INVOICE;
}

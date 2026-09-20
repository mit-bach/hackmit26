import { CAPABILITY_COPY } from "../copy";

/** Wall status compressed from CAPABILITIES.md Now, plus required honesty overrides. */
export type CapabilityStatus = "kernel-live" | "office-live" | "partial" | "not-built";

export type CapabilityPipe = "intake" | "pay" | "cash" | "close" | "rest";

export type CapabilityFilter = "all" | "office-live" | "partial" | "not-built";

export interface CapabilityLink {
  readonly href: string;
  readonly label: string;
}

export interface CapabilityRow {
  readonly id: string;
  readonly title: string;
  readonly pipe: CapabilityPipe;
  readonly status: CapabilityStatus;
  readonly sentence: string;
  readonly agents: readonly string[];
  readonly caption?: string;
  readonly notice?: string;
  readonly links: readonly CapabilityLink[];
}

export interface PipeBand {
  readonly id: CapabilityPipe;
  readonly label: string;
}

export interface PipeCount {
  readonly pipe: CapabilityPipe;
  readonly label: string;
  readonly live: number;
  readonly notBuilt: number;
}

export const CAPABILITY_PIPES: readonly PipeBand[] = [
  { id: "intake", label: "Intake" },
  { id: "pay", label: "Pay" },
  { id: "cash", label: "Cash" },
  { id: "close", label: "Close" },
  { id: "rest", label: "Rest" },
];

export const CAPABILITY_STATUSES: readonly CapabilityStatus[] = [
  "kernel-live",
  "office-live",
  "partial",
  "not-built",
];

const COMPACT_PIPE_IDS: readonly CapabilityPipe[] = ["intake", "pay", "cash", "close"];

function sentence(id: string, fallback: string): string {
  return CAPABILITY_COPY[id] ?? fallback;
}

export const CAPABILITY_ROWS: readonly CapabilityRow[] = [
  {
    id: "inbox.counterparty_to_ap",
    title: "World role-plays a vendor or customer and delivers mail",
    pipe: "intake",
    status: "partial",
    sentence: "Kernel tools can compose, send, and classify; World is not on the live roster.",
    agents: ["email"],
    notice: "World Bot not on live roster",
    links: [{ href: "/inbox", label: "Inbox" }],
  },
  {
    id: "ingestion.classify_document",
    title: "Tell a vendor invoice from a quote, PO, receipt, statement, marketing, or duplicate copy",
    pipe: "intake",
    status: "office-live",
    sentence: sentence(
      "ingestion.classify_document",
      "Tell invoices apart from quotes, receipts, and other documents",
    ),
    agents: ["email"],
    links: [],
  },
  {
    id: "ingestion.structured_parse",
    title: "Parse ERP / Coupa / EDI into an invoice candidate",
    pipe: "intake",
    status: "office-live",
    sentence: "Books lands ERP, Coupa, and EDI files as invoice candidates, with no live NetSuite post.",
    agents: ["books"],
    links: [],
  },
  {
    id: "ingestion.bank_card_discovery",
    title: "A card charge is not a bill",
    pipe: "intake",
    status: "office-live",
    sentence: "Bank recovers an invoice from a card charge only when supporting documents exist.",
    agents: ["bank"],
    links: [],
  },
  {
    id: "ap.three_way_match",
    title: "Match invoice to PO and goods receipt",
    pipe: "pay",
    status: "office-live",
    sentence: sentence(
      "ap.three_way_match",
      "Compare a vendor bill with its purchase order and receiving record",
    ),
    agents: ["ap", "ctl-pay"],
    links: [
      { href: "/workflow?story=clean", label: "Clean story" },
      { href: "/ap", label: "Payables" },
    ],
  },
  {
    id: "ap.payment_scheduling",
    title: "Rank the approved pool for this week",
    pipe: "pay",
    status: "office-live",
    sentence: sentence(
      "ap.payment_scheduling",
      "Decide which approved vendor bills belong in the payment run",
    ),
    agents: ["pay", "ctl-pay"],
    links: [],
  },
  {
    id: "ap.self_improvement",
    title: "Write a vendor alias into operational AP memory",
    pipe: "pay",
    status: "not-built",
    sentence: "Not built as an office path; a Kernel seed file is not a standing Bot writing aliases.",
    agents: ["ap"],
    links: [],
  },
  {
    id: "ap.vendor_bank_change",
    title: "Flag a vendor payment-instruction change",
    pipe: "pay",
    status: "not-built",
    sentence: "Not built: vendor master has bank fields, and there is no control engine.",
    agents: ["ap"],
    links: [],
  },
  {
    id: "ar.aging_collections",
    title: "Age open invoices",
    pipe: "cash",
    status: "partial",
    sentence: sentence(
      "ar.aging_collections",
      "Group unpaid invoices by how late they are and choose follow-up",
    ),
    agents: ["collect"],
    notice: "Collect is office-live. World reply is not attached.",
    links: [],
  },
  {
    id: "ar.cash_application",
    title: "Apply a remittance",
    pipe: "cash",
    status: "office-live",
    sentence: sentence(
      "ar.cash_application",
      "Match customer payments to the invoices they settle",
    ),
    agents: ["apply", "ctl-cash"],
    links: [{ href: "/ar", label: "Receivables" }],
  },
  {
    id: "memory.self_improvement",
    title: "Learn from a structured AR correction",
    pipe: "cash",
    status: "kernel-live",
    sentence: "Kernel stores AR correction precedents and is not office-live Pi on 8800.",
    agents: ["apply"],
    links: [],
  },
  {
    id: "cash.bank_reconciliation",
    title: "Match bank to ledger only when evidence supports it",
    pipe: "cash",
    status: "office-live",
    sentence: sentence(
      "cash.bank_reconciliation",
      "Match bank activity to ledger cash entries",
    ),
    agents: ["cash", "ctl-cash"],
    links: [
      { href: "/workflow?story=unresolved", label: "Unresolved story" },
      { href: "/cash", label: "Cash" },
    ],
  },
  {
    id: "cash.stripe_reconciliation",
    title: "Unpack charges − fees − refunds − disputes = bank deposit",
    pipe: "cash",
    status: "kernel-live",
    sentence: "Kernel unpacks simulated Stripe charges, fees, refunds, and disputes into a deposit.",
    agents: ["stripe"],
    links: [{ href: "/stripe", label: "Stripe" }],
  },
  {
    id: "close.accruals",
    title: "Accrue missing bills from history, contract, usage, POs",
    pipe: "close",
    status: "office-live",
    sentence: sentence(
      "close.accruals",
      "Estimate expenses that belong in the month before the bill arrives",
    ),
    agents: ["close"],
    links: [],
  },
  {
    id: "close.prepaids",
    title: "Spread prepaid software / insurance over the service period",
    pipe: "close",
    status: "kernel-live",
    sentence: sentence(
      "close.prepaids",
      "Spread prepaid costs across the months they cover",
    ),
    agents: ["close"],
    links: [],
  },
  {
    id: "close.fixed_assets",
    title: "Capital vs expense. Straight-line depreciation",
    pipe: "close",
    status: "kernel-live",
    sentence: sentence(
      "close.fixed_assets",
      "Record equipment as an asset and spread its cost over time",
    ),
    agents: ["close"],
    links: [],
  },
  {
    id: "close.balance_sheet_recs",
    title: "Tie cash, AP, AR, accruals, prepaids, assets to evidence",
    pipe: "close",
    status: "kernel-live",
    sentence: sentence(
      "close.balance_sheet_recs",
      "Check that balance-sheet accounts agree with supporting records",
    ),
    agents: ["close"],
    links: [],
  },
  {
    id: "close.month_end",
    title: "Coordinate tasks. Gate the lock",
    pipe: "close",
    status: "partial",
    sentence: sentence("close.month_end", "Coordinate finishing the month's books"),
    agents: ["close", "ctl-books"],
    notice: "Close Manager SDK path is partial. Lock owner is ctl-books.",
    links: [{ href: "/close", label: "Close" }],
  },
  {
    id: "audit.controls",
    title: "Independent sample, re-perform, control test, write findings",
    pipe: "rest",
    status: "office-live",
    sentence: sentence("audit.controls", "Re-test whether company controls were followed"),
    agents: ["audit"],
    links: [{ href: "/audit", label: "Audit" }],
  },
  {
    id: "reporting.variance_board",
    title: "Explain GM 64% → 61% from source txs",
    pipe: "rest",
    status: "office-live",
    sentence: sentence(
      "reporting.variance_board",
      "Explain why results changed and prepare board figures",
    ),
    agents: ["story"],
    links: [],
  },
  {
    id: "forecast.thirteen_week",
    title: "Build 13 weeks from AP, AR, payroll",
    pipe: "rest",
    status: "kernel-live",
    sentence: sentence(
      "forecast.thirteen_week",
      "Project cash on hand for the next 13 weeks",
    ),
    agents: ["story"],
    links: [{ href: "/forecast", label: "Forecast" }],
  },
  {
    id: "memory.cross_period",
    title: "Retrieve August precedent",
    pipe: "rest",
    status: "kernel-live",
    sentence: sentence(
      "memory.cross_period",
      "Reuse a prior-period decision only when current evidence still supports it",
    ),
    agents: ["ap", "stripe", "close"],
    links: [],
  },
  {
    id: "orchestration.cfo",
    title: "One September run: intake → AP/AR/cash → close blocked → story",
    pipe: "rest",
    status: "kernel-live",
    sentence: "Kernel can run one September cycle from intake through close blocked.",
    agents: ["email", "ap", "apply", "cash", "close", "story"],
    links: [
      { href: "/", label: "Home" },
      { href: "/simulations", label: "Simulations" },
    ],
  },
  {
    id: "evaluation.finance_gauntlet",
    title: "Same production workflows, public fixtures, hidden gold",
    pipe: "rest",
    status: "kernel-live",
    sentence: "Kernel runs the same production workflows against public fixtures and hidden gold.",
    agents: [],
    caption: "Kernel measure, not the office score",
    links: [{ href: "/evaluations", label: "Evaluations" }],
  },
];

export function capabilityById(id: string): CapabilityRow | undefined {
  return CAPABILITY_ROWS.find((row) => row.id === id);
}

export function filterCapabilities(filter: CapabilityFilter): readonly CapabilityRow[] {
  if (filter === "all") {
    return CAPABILITY_ROWS;
  }
  return CAPABILITY_ROWS.filter((row) => row.status === filter);
}

export function rowsInPipe(
  pipe: CapabilityPipe,
  rows: readonly CapabilityRow[] = CAPABILITY_ROWS,
): readonly CapabilityRow[] {
  return rows.filter((row) => row.pipe === pipe);
}

export function compactPipeCounts(): readonly PipeCount[] {
  return COMPACT_PIPE_IDS.map((pipe) => {
    const band = CAPABILITY_PIPES.find((item) => item.id === pipe);
    const rows = rowsInPipe(pipe);
    return {
      pipe,
      label: band?.label ?? pipe,
      live: rows.filter((row) => row.status === "office-live").length,
      notBuilt: rows.filter((row) => row.status === "not-built").length,
    };
  });
}

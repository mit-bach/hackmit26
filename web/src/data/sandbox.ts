export interface SandboxPersona {
  readonly id: "vendor" | "customer" | "bank" | "employee";
  readonly title: string;
  readonly does: string;
}

export interface SandboxLanding {
  readonly slug: string;
  readonly title: string;
  readonly source: string;
}

export interface SandboxFixture {
  readonly id: string;
  readonly title: string;
  readonly what: string;
  readonly href: string;
  readonly recordId: string;
}

export interface SandboxBound {
  readonly title: string;
  readonly body: string;
}

export const SANDBOX_PERSONAS: readonly SandboxPersona[] = [
  {
    id: "vendor",
    title: "Vendor",
    does: "Sends bills, quotes, and replies about missing invoice fields.",
  },
  {
    id: "customer",
    title: "Customer",
    does: "Sends remittances and would answer a collections follow-up.",
  },
  {
    id: "bank",
    title: "Bank",
    does: "Would send bank notices. Statement lines in this demo are fixture records.",
  },
  {
    id: "employee",
    title: "Employee",
    does: "Sends receipts and internal mail into the finance inbox.",
  },
];

export const SANDBOX_LANDINGS: readonly SandboxLanding[] = [
  { slug: "email", title: "Email", source: "Simulated mailbox and fixture PDFs" },
  { slug: "stripe", title: "Stripe", source: "Simulated payout events, not a live Stripe account" },
  { slug: "bank", title: "Bank", source: "Fixture statement lines, not a live bank feed" },
  { slug: "books", title: "Books", source: "Fixture ledger, purchase orders, and receiving records" },
];

export const SANDBOX_NOT_CONNECTED: readonly SandboxBound[] = [
  {
    title: "Live Stripe",
    body: "The top bar says Stripe Simulated. Payouts are reconstructed from fixture events, not from Maximor's real Stripe account.",
  },
  {
    title: "Live bank",
    body: "There is no live bank connection. Deposits, wires, and fees are records we wrote for Maximor Demo Corp.",
  },
  {
    title: "Live Gmail",
    body: "The finance inbox is not a company mailbox. Incoming mail is fixture documents, or World delivering into a simulated inbox.",
  },
  {
    title: "World on this demo roster",
    body: "World is the outside-world role-player: vendor, customer, bank, or employee. On this Computer it is not attached. Outbound dunning and missing-info mail do not leave through World. Inbound mail you click through is fixture data.",
  },
];

export const SANDBOX_IS_SIMULATED: readonly SandboxBound[] = [
  {
    title: "Maximor Demo Corp, September 2026",
    body: "One constructed company picture: cash, open bills, unpaid invoices, journals, and saved decisions from August. Company id CO-MAXIMOR.",
  },
  {
    title: "World personas",
    body: "When World is bound, it role-plays whoever finance mailed. It delivers into a simulated mailbox. It does not post bills, move cash, or lock the month. It must not live-connect Gmail or Stripe.",
  },
  {
    title: "Fifteen standing finance agents",
    body: "Email, payables, payments, cash, close, reporting, control, and audit work this company picture as if the records were real. They share books, memory, and evidence. They do not invent a live bank or a live Stripe.",
  },
];

export const SANDBOX_FIXTURES: readonly SandboxFixture[] = [
  {
    id: "acme",
    title: "Acme warehouse bill",
    what: "A clean vendor invoice against PO-101. The packet should three-way match.",
    href: "/inbox",
    recordId: "INV-001",
  },
  {
    id: "quote",
    title: "Quote that looks like a bill",
    what: "Harbor Build Co. sent a quotation. It must not be booked as money owed.",
    href: "/inbox",
    recordId: "Q-8891",
  },
  {
    id: "lumen",
    title: "Lumen $5,000 remittance",
    what: "The payment message only says “September billing.” Cash application must not guess the invoices.",
    href: "/ar",
    recordId: "PAY-004",
  },
  {
    id: "northstar",
    title: "Northstar $12.40 difference",
    what: "The bank deposit is $12.40 above the invoice. Close stays blocked until that line is explained. We do not invent a fee.",
    href: "/cash",
    recordId: "TXN-2026-09-015",
  },
  {
    id: "harbor",
    title: "Missing Harbor Electric bill",
    what: "September electricity was used. The bill has not arrived, so close needs an estimate rather than a blank.",
    href: "/close",
    recordId: "ACC-HE-2026-09",
  },
  {
    id: "stripe",
    title: "Simulated Stripe payout",
    what: "Charges, fees, and the net deposit are fixture events. The waterfall must add up without a live Stripe key.",
    href: "/stripe",
    recordId: "po_1MaximorFees",
  },
];

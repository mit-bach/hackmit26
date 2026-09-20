export type Capability = {
  id: string;
  title: string;
  finance: string;
  maximor: string;
  agents: string[];
};

export const CAPABILITIES: Capability[] = [
  {
    id: "ap",
    title: "Accounts payable",
    finance: "Checks vendor bills, resolves discrepancies, gets approvals, and determines what should be paid.",
    maximor: "Reviews incoming invoices, compares them with purchase orders and receiving records, detects duplicates, applies earlier-period decisions, and sends uncertain packets to Payables Control.",
    agents: ["email", "books", "ap", "pay", "ctl-pay"],
  },
  {
    id: "ar",
    title: "Accounts receivable",
    finance: "Sends customer invoices, matches incoming payments to those invoices, and follows balances that stay unpaid.",
    maximor: "Applies customer payments when the evidence is clear, leaves ambiguous remittances unmatched, and watches aging after cash application has already drained new deposits.",
    agents: ["email", "apply", "collect", "ctl-cash"],
  },
  {
    id: "cash",
    title: "Cash and reconciliation",
    finance: "Checks that the bank, the processor, and the ledger tell the same story, then investigates anything that does not.",
    maximor: "Matches bank lines to ledger cash, explains grouped payments and fees, reconstructs Stripe payouts, and refuses to invent an explanation for an unresolved difference.",
    agents: ["bank", "stripe", "cash", "ctl-cash"],
  },
  {
    id: "close",
    title: "Month-end close",
    finance: "Makes sure every cost that belongs in the month is recorded, even if the bill has not arrived, then locks the period.",
    maximor: "Estimates missing bills, spreads prepaid costs, depreciates assets, coordinates the checklist, and will not lock the month while cash is still unresolved.",
    agents: ["close", "ctl-books", "cash", "ap"],
  },
  {
    id: "audit",
    title: "Audit and controls",
    finance: "Independently samples the books after the fact and tests whether company controls were followed.",
    maximor: "Samples invoices, payments, journals, and approvals, re-performs reconciliations, and writes findings. It does not operate the books or approve payments.",
    agents: ["audit"],
  },
  {
    id: "forecast",
    title: "Forecasting and reporting",
    finance: "Projects cash, explains why results moved, and prepares figures the board can trust.",
    maximor: "Builds a 13-week cash forecast from the same books, names the transactions that caused a miss, and ties board metrics to the general ledger.",
    agents: ["story", "close", "apply", "pay"],
  },
];

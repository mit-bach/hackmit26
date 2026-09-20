import type { AgentSlug } from "./agents";

export type StoryStep = {
  n: number;
  title: string;
  body: string;
  agent: AgentSlug;
  handoff?: string;
};

/** Vendor-invoice path supported by handle-map + kernel workflows. */
export const INVOICE_STORY: StoryStep[] = [
  {
    n: 1,
    title: "A vendor invoice arrives",
    body: "A vendor emails a bill, or the same document lands from a portal, a scan, or the accounting system. Nothing has been booked yet.",
    agent: "email",
  },
  {
    n: 2,
    title: "The document is identified",
    body: "The Email Agent decides whether this is a real invoice, a quote, a statement, or a receipt. Quotes are not treated as money the company owes.",
    agent: "email",
    handoff: "If it is a bill, work is handed to Accounts Payable.",
  },
  {
    n: 3,
    title: "The bill is checked against company records",
    body: "Payables compares the invoice with the purchase order and the record that goods or services were received. It also looks for a second copy of the same bill.",
    agent: "ap",
  },
  {
    n: 4,
    title: "Earlier decisions are consulted",
    body: "If this vendor or situation has been seen before, payables can retrieve the saved decision — including the evidence and the reason — instead of starting from a blank page.",
    agent: "ap",
  },
  {
    n: 5,
    title: "Uncertain packets are rechecked",
    body: "A bill that looks ready is not final yet. Payables Control independently looks for reasons to refuse. Weak evidence stays unresolved; it is not sent to a person to rubber-stamp.",
    agent: "ctl-pay",
    handoff: "Concurrence is a second agent, not a human approval queue.",
  },
  {
    n: 6,
    title: "Approved bills enter the payment plan",
    body: "The Payments Agent drafts which bills belong in this week's run from due dates, cash on hand, and discounts. It still does not move money.",
    agent: "pay",
    handoff: "The draft plan is handed back to Payables Control before any cash would be released.",
  },
  {
    n: 7,
    title: "The same bill shows up in later finance work",
    body: "Planned wires are handed to cash reconciliation. If goods were billed but not received, month-end close is told. The unpaid amount also changes the cash forecast.",
    agent: "cash",
  },
  {
    n: 8,
    title: "Close records the accounting effect",
    body: "If the bill belongs in this month, close includes it. If the bill has not arrived but the cost was incurred, close estimates an accrual so the month is still complete.",
    agent: "close",
  },
  {
    n: 9,
    title: "Reporting and audit can inspect the history",
    body: "The Reporting Agent projects the cash effect. After the month is recorded, the Audit Agent can sample the same bill, the match packet, and the saved reason.",
    agent: "audit",
  },
];

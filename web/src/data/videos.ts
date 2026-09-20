import type { AgentSlug } from "./agents";

export type Video = {
  id: string;
  title: string;
  description: string;
  thumbnail?: string;
  src?: string;
  embedUrl?: string;
  duration?: string;
  processes: string[];
  agents: AgentSlug[];
  featured?: boolean;
};

/**
 * Add a recording by filling `src` (local MP4 under /public or a hosted file)
 * or `embedUrl` (YouTube / Vimeo). Thumbnails are optional image paths.
 */
export const VIDEOS: Video[] = [
  {
    id: "invoice-to-close",
    title: "Invoice → payment → close",
    description: "Follow one vendor bill from email intake through payables, the payment draft, and the month-end effect.",
    processes: ["Inbox", "Accounts payable", "Payments", "Month-end close"],
    agents: ["email", "ap", "pay", "ctl-pay", "close"],
    featured: true,
  },
  {
    id: "stripe-reconciliation",
    title: "Stripe reconciliation",
    description: "Unpack a payout into charges, refunds, fees, and chargebacks, then tie the net to the bank.",
    processes: ["Stripe", "Cash reconciliation"],
    agents: ["stripe", "cash", "ctl-cash"],
  },
  {
    id: "month-end-across-periods",
    title: "Month-end close across periods",
    description: "Harbor Electric in August versus September: the same recurring cost, a missing bill, and a lock that waits on cash.",
    processes: ["Month-end close", "Decision memory"],
    agents: ["close", "ctl-books", "cash"],
  },
  {
    id: "agent-memory",
    title: "Agent memory",
    description: "September retrieves August's saved decision, then re-checks current evidence instead of pasting last month's number.",
    processes: ["Decision memory", "Accruals"],
    agents: ["close", "ctl-books"],
  },
  {
    id: "bad-invoice",
    title: "Finding a bad invoice",
    description: "A duplicate Northline bill and a quote that looks like an invoice are stopped before they become money owed.",
    processes: ["Inbox", "Accounts payable"],
    agents: ["email", "ap", "ctl-pay"],
  },
  {
    id: "control-escalation",
    title: "When evidence is not enough",
    description: "Ambiguous cash application and the unexplained $12.40 are handed to control agents instead of guessed.",
    processes: ["Cash application", "Bank reconciliation"],
    agents: ["apply", "cash", "ctl-cash"],
  },
];

export function videoHasMedia(video: Video): boolean {
  return Boolean(video.src || video.embedUrl);
}

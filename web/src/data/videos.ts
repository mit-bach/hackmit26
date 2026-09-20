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
 * Cuts from golden-20260920-r1 Demo tape. Titles follow what the desk did.
 * Acme was not paid. September is not CLOSED. Harbor September is $4,650.
 */
export const VIDEOS: Video[] = [
  {
    id: "invoice-to-close",
    title: "INV-001 reaches control",
    description: "AP maps NS-4410 to INV-001 and hands ctl-pay a clean three-way. ctl-pay concurs. AP does not pay.",
    src: "/videos/invoice-to-close.mp4",
    thumbnail: "/videos/invoice-to-close.jpg",
    duration: "0:14",
    processes: ["Accounts payable", "Control"],
    agents: ["ap", "ctl-pay", "books"],
    featured: true,
  },
  {
    id: "stripe-reconciliation",
    title: "Stripe payout unpack",
    description: "Stripe unpacks charges, refunds, fees, and chargebacks on the Golden tape. The net is not closed to the bank on this cut.",
    src: "/videos/stripe-reconciliation.mp4",
    thumbnail: "/videos/stripe-reconciliation.jpg",
    duration: "0:14",
    processes: ["Stripe", "Cash"],
    agents: ["stripe", "apply", "cash"],
  },
  {
    id: "month-end-across-periods",
    title: "Harbor Electric, two periods",
    description: "September retrieves August's seasonal method at $7,800, re-checks current evidence, and books $4,650. The lock stays BLOCKED on $12.40.",
    src: "/videos/month-end-across-periods.mp4",
    thumbnail: "/videos/month-end-across-periods.jpg",
    duration: "0:14",
    processes: ["Month-end close", "Decision memory"],
    agents: ["close", "ctl-books"],
  },
  {
    id: "agent-memory",
    title: "September reads August",
    description: "Close calls memory_read, then memory_write. ctl-books concurs the method and still rejects the lock.",
    src: "/videos/agent-memory.mp4",
    thumbnail: "/videos/agent-memory.jpg",
    duration: "0:17",
    processes: ["Decision memory", "Accruals"],
    agents: ["close", "ctl-books"],
  },
  {
    id: "bad-invoice",
    title: "Inbox traps stay off the books",
    description: "Nineteen threads classified. A quote, a statement, and a newsletter never become payables. HOLDs stay HOLDs.",
    src: "/videos/bad-invoice.mp4",
    thumbnail: "/videos/bad-invoice.jpg",
    duration: "0:14",
    processes: ["Inbox", "Accounts payable"],
    agents: ["email", "ap", "ctl-pay"],
  },
  {
    id: "control-escalation",
    title: "$12.40 stays unexplained",
    description: "Bank lines including TXN-2026-09-015 reach cash as HUMAN_REVIEW. ctl-cash does not guess. The month does not close.",
    src: "/videos/control-escalation.mp4",
    thumbnail: "/videos/control-escalation.jpg",
    duration: "0:14",
    processes: ["Bank reconciliation", "Control"],
    agents: ["bank", "cash", "ctl-cash"],
  },
];

export function videoHasMedia(video: Video): boolean {
  return Boolean(video.src || video.embedUrl);
}

import type { FlowEdge, FlowNode, FlowStep } from "../components/FlowPlay";
import { formatMatchType } from "../copy";

export type ShowStoryId = "clean" | "resolved" | "unresolved";

export interface ShowExit {
  readonly href: string;
  readonly label: string;
  readonly ids: readonly string[];
}

export interface ShowStory {
  readonly id: ShowStoryId;
  readonly label: string;
  readonly vendor: string;
  readonly outcome: string;
  readonly amount?: string;
  readonly ids: readonly string[];
  readonly previewIds: readonly string[];
  readonly nodes: readonly FlowNode[];
  readonly edges: readonly FlowEdge[];
  readonly steps: readonly FlowStep[];
  readonly exits: readonly ShowExit[];
}

const FEE_NETTED_LABEL = formatMatchType("FEE_NETTED");

const CLEAN_STORY: ShowStory = {
  id: "clean",
  label: "CLEAN",
  vendor: "Acme",
  outcome: "MATCHED",
  ids: ["INV-001", "PO-101", "GR-101", "PAY-AP-001", "TXN-2026-09-018A"],
  previewIds: ["INV-001", "PAY-AP-001", "TXN-2026-09-018A"],
  nodes: [
    { id: "event", label: "Vendor email", kind: "event", column: 0 },
    { id: "email", label: "Email", kind: "source", room: "intake", column: 1 },
    { id: "ap", label: "AP", kind: "operator", room: "pay", column: 2 },
    { id: "ctl-pay", label: "ctl-pay", kind: "verifier", room: "pay", column: 3 },
    { id: "pay", label: "Pay", kind: "operator", room: "pay", column: 4 },
    { id: "cash", label: "Cash", kind: "operator", room: "cash", column: 5 },
    { id: "story", label: "Story", kind: "operator", room: "books-close", column: 6 },
    { id: "audit", label: "Audit", kind: "assurance", room: "books-close", column: 7 },
  ],
  edges: [
    { id: "clean-e-event-email", from: "event", to: "email", label: "bill" },
    { id: "clean-e-email-ap", from: "email", to: "ap", label: "classify" },
    { id: "clean-e-ap-ctl", from: "ap", to: "ctl-pay", label: "APPROVE" },
    { id: "clean-e-ctl-pay", from: "ctl-pay", to: "pay", label: "concur" },
    { id: "clean-e-pay-cash", from: "pay", to: "cash", label: "payable" },
    { id: "clean-e-cash-story", from: "cash", to: "story", label: "MATCHED" },
    { id: "clean-e-story-audit", from: "story", to: "audit", label: "sample" },
  ],
  steps: [
    {
      id: "clean-event",
      title: "Acme emails a vendor bill",
      nodeId: "event",
      body: "A vendor invoice lands in finance mail. Nothing is booked yet.",
      manipulations: ["land document"],
      artifactIds: ["INV-001"],
    },
    {
      id: "clean-email",
      title: "Email classifies INV-001 as a bill",
      nodeId: "email",
      body: "This is a vendor invoice, not a quote, statement, or receipt.",
      manipulations: ["classify document", "extract fields"],
      handoff: {
        to: "ap",
        why: "A classified vendor bill is handed to payables to match before it counts as money owed.",
      },
      artifactIds: ["INV-001"],
    },
    {
      id: "clean-ap",
      title: "AP three-way matches and APPROVE",
      nodeId: "ap",
      body: "INV-001 agrees with PO-101 and GR-101. The packet is ready for concurrence.",
      manipulations: ["match three-way", "approve packet"],
      handoff: {
        to: "ctl-pay",
        why: "A bill that looks ready is independently rechecked by Payables Control.",
      },
      artifactIds: ["INV-001", "PO-101", "GR-101"],
    },
    {
      id: "clean-ctl-pay",
      title: "ctl-pay concurs on the match",
      nodeId: "ctl-pay",
      body: "Payables Control finds no reason to refuse. Unresolved evidence would stay here, not with a person.",
      manipulations: ["concur match"],
      handoff: {
        to: "pay",
        why: "A concurred payable is handed to payments to enter the weekly run.",
      },
      artifactIds: ["INV-001", "PO-101", "GR-101"],
    },
    {
      id: "clean-pay",
      title: "Pay includes PAY-AP-001",
      nodeId: "pay",
      body: "The weekly draft includes PAY-AP-001. Cash still does not move.",
      manipulations: ["draft weekly run", "include approved bill"],
      handoff: {
        to: "cash",
        why: "A planned payment is handed to cash so the later bank line can be tied to the same identity.",
      },
      artifactIds: ["INV-001", "PAY-AP-001"],
    },
    {
      id: "clean-cash",
      title: "Cash MATCHED TXN-2026-09-018A",
      nodeId: "cash",
      body: "Bank line TXN-2026-09-018A matches PAY-AP-001. Same identity as INV-001.",
      manipulations: ["match bank to ledger"],
      handoff: {
        to: "story",
        why: "A matched payment is handed to reporting so the forecast uses the same IDs.",
      },
      artifactIds: ["PAY-AP-001", "TXN-2026-09-018A"],
    },
    {
      id: "clean-story",
      title: "Story forecasts the same IDs",
      nodeId: "story",
      body: "Forecast actuals keep INV-001, PAY-AP-001, and TXN-2026-09-018A.",
      manipulations: ["project cash effect"],
      handoff: {
        to: "audit",
        why: "After the path is recorded, audit can sample the same packet.",
      },
      artifactIds: ["INV-001", "PAY-AP-001", "TXN-2026-09-018A"],
    },
    {
      id: "clean-audit",
      title: "Audit can sample the packet",
      nodeId: "audit",
      body: "Audit re-performs the three-way match and the bank match on the same identities.",
      manipulations: ["sample packet", "re-perform match"],
      artifactIds: ["INV-001", "PO-101", "GR-101", "PAY-AP-001", "TXN-2026-09-018A"],
      status: "done",
    },
  ],
  exits: [
    { href: "/ap", label: "Open payables for INV-001", ids: ["INV-001"] },
    { href: "/cash", label: "Open cash for TXN-2026-09-018A", ids: ["TXN-2026-09-018A"] },
  ],
};

const RESOLVED_STORY: ShowStory = {
  id: "resolved",
  label: "RESOLVED",
  vendor: "Helios",
  outcome: "FEE_NETTED",
  ids: ["INV-017", "TXN-2026-09-011", "FEE-729103"],
  previewIds: ["INV-017", "TXN-2026-09-011", "FEE-729103"],
  nodes: [
    { id: "event", label: "Helios wire", kind: "event", column: 0 },
    { id: "bank", label: "Bank", kind: "source", room: "intake", column: 1 },
    { id: "cash", label: "Cash", kind: "operator", room: "cash", column: 2 },
    { id: "ctl-cash", label: "ctl-cash", kind: "verifier", room: "cash", column: 3 },
    { id: "close", label: "Close", kind: "operator", room: "books-close", column: 4 },
  ],
  edges: [
    { id: "res-e-event-bank", from: "event", to: "bank", label: "wire" },
    { id: "res-e-bank-cash", from: "bank", to: "cash", label: "$25 over" },
    { id: "res-e-cash-ctl", from: "cash", to: "ctl-cash", label: "FEE_NETTED" },
    { id: "res-e-ctl-close", from: "ctl-cash", to: "close", label: "explained" },
  ],
  steps: [
    {
      id: "res-event",
      title: "Helios bank line is $25 over books",
      nodeId: "event",
      body: "INV-017 meets bank TXN-2026-09-011. The wire is $25 over the Helios bill.",
      manipulations: ["read bank vs books"],
      artifactIds: ["INV-017", "TXN-2026-09-011"],
    },
    {
      id: "res-bank",
      title: "Bank reports the Helios wire",
      nodeId: "bank",
      body: "Bank lands TXN-2026-09-011. A bank line is not a new vendor bill.",
      manipulations: ["land bank line"],
      handoff: {
        to: "cash",
        why: "An unmatched Helios wire is handed to cash to test fee evidence before anyone forces a match.",
      },
      artifactIds: ["INV-017", "TXN-2026-09-011"],
    },
    {
      id: "res-cash",
      title: "Cash nets FEE-729103 as FEE_NETTED",
      nodeId: "cash",
      body: `Fee evidence FEE-729103 supports FEE_NETTED. ${FEE_NETTED_LABEL}.`,
      manipulations: ["net bank fee", "match with evidence"],
      handoff: {
        to: "ctl-cash",
        why: "A fee-netted match is handed to Cash Control for sign-off.",
      },
      artifactIds: ["INV-017", "TXN-2026-09-011", "FEE-729103"],
    },
    {
      id: "res-ctl-cash",
      title: "ctl-cash signs off the explained exception",
      nodeId: "ctl-cash",
      body: "Cash Control accepts FEE_NETTED on TXN-2026-09-011. This is an explained exception.",
      manipulations: ["sign off rec"],
      handoff: {
        to: "close",
        why: "An explained bank exception is handed to close so the month can keep this item.",
      },
      artifactIds: ["FEE-729103", "TXN-2026-09-011"],
    },
    {
      id: "res-close",
      title: "Close accepts the explained exception",
      nodeId: "close",
      body: "Close keeps the Helios FEE_NETTED item. This $25 does not block the month.",
      manipulations: ["accept explained exception"],
      artifactIds: ["INV-017", "FEE-729103", "TXN-2026-09-011"],
      status: "done",
    },
  ],
  exits: [
    {
      href: "/cash",
      label: "Open cash for TXN-2026-09-011 and FEE-729103",
      ids: ["TXN-2026-09-011", "FEE-729103"],
    },
    { href: "/close", label: "Open close for the explained Helios exception", ids: ["INV-017"] },
  ],
};

const UNRESOLVED_STORY: ShowStory = {
  id: "unresolved",
  label: "UNRESOLVED",
  vendor: "Northstar",
  outcome: "BLOCKED",
  amount: "$12.40",
  ids: ["PAY-006", "INV-AR-013", "TXN-2026-09-015"],
  previewIds: ["PAY-006", "INV-AR-013", "TXN-2026-09-015"],
  nodes: [
    { id: "event", label: "Northstar pair", kind: "event", column: 0 },
    { id: "bank", label: "Bank", kind: "source", room: "intake", column: 1 },
    { id: "cash", label: "Cash", kind: "operator", room: "cash", column: 2 },
    { id: "close", label: "Close", kind: "operator", room: "books-close", column: 3, status: "blocked" },
    { id: "ctl-books", label: "ctl-books", kind: "verifier", room: "books-close", column: 4, status: "blocked" },
  ],
  edges: [
    { id: "unr-e-event-bank", from: "event", to: "bank", label: "pair" },
    { id: "unr-e-bank-cash", from: "bank", to: "cash", label: "$12.40" },
    { id: "unr-e-cash-close", from: "cash", to: "close", label: "unexplained" },
    { id: "unr-e-close-ctl", from: "close", to: "ctl-books", label: "hold lock" },
  ],
  steps: [
    {
      id: "unr-event",
      title: "Books $12,400.00 vs bank $12,412.40",
      nodeId: "event",
      body: "PAY-006 / INV-AR-013 books $12,400.00. Bank TXN-2026-09-015 is $12,412.40.",
      manipulations: ["pair bank to books"],
      artifactIds: ["PAY-006", "INV-AR-013", "TXN-2026-09-015"],
    },
    {
      id: "unr-bank",
      title: "Bank shows TXN-2026-09-015 at $12,412.40",
      nodeId: "bank",
      body: "The operating bank reports $12,412.40 on TXN-2026-09-015. There is no fee ticket.",
      manipulations: ["land bank line"],
      handoff: {
        to: "cash",
        why: "A Northstar bank line that does not equal the books is handed to cash to test for evidence.",
      },
      artifactIds: ["TXN-2026-09-015"],
    },
    {
      id: "unr-cash",
      title: "Cash refuses the $12.40 gap",
      nodeId: "cash",
      body: "Cash records an unexplained difference of $12.40. Maximor will not invent a $12.40 fee.",
      manipulations: ["refuse unexplained"],
      handoff: {
        to: "close",
        why: "An unexplained bank difference is handed to close. Close cannot treat it as explained.",
      },
      artifactIds: ["PAY-006", "TXN-2026-09-015"],
    },
    {
      id: "unr-close",
      title: "Close gates fail; the month cannot finish",
      nodeId: "close",
      body: "Close evaluates gates and fails on TXN-2026-09-015. The month cannot finish.",
      manipulations: ["evaluate gates", "hold lock"],
      handoff: {
        to: "ctl-books",
        why: "A failed close gate is handed to Books Control. The period stays open.",
      },
      artifactIds: ["TXN-2026-09-015"],
      status: "blocked",
    },
    {
      id: "unr-ctl-books",
      title: "ctl-books does not lock",
      nodeId: "ctl-books",
      body: "ctl-books will not lock September. Unresolved — more evidence required for the $12.40.",
      manipulations: ["hold lock", "refuse unexplained"],
      artifactIds: ["TXN-2026-09-015"],
      status: "blocked",
    },
  ],
  exits: [
    { href: "/cash", label: "Open cash for TXN-2026-09-015", ids: ["TXN-2026-09-015"] },
    { href: "/close", label: "Month cannot finish — open close", ids: [] },
  ],
};

export const SHOW_STORIES: readonly ShowStory[] = [CLEAN_STORY, RESOLVED_STORY, UNRESOLVED_STORY];

export function parseShowStory(raw: string | null | undefined): ShowStoryId {
  if (raw === "resolved" || raw === "unresolved") {
    return raw;
  }
  return "clean";
}

export function showStoryById(raw: string | null | undefined): ShowStory {
  const id = parseShowStory(raw);
  return SHOW_STORIES.find((item) => item.id === id) ?? CLEAN_STORY;
}

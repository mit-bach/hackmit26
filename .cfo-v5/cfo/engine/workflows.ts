import { cashSignOffRequired, readBillFacts, type BillFacts } from "./kernel.ts";
import type { Advance, Item, StepResult } from "./types.ts";

export const DECISIONS: Record<string, Record<string, readonly string[]>> = {
  open_bill: {
    match: ["APPROVE", "HOLD", "INVESTIGATE"],
    investigate: ["APPROVE", "HOLD"],
    "review-match": ["CONCUR", "REFUSE"],
  },
  pay_run: {
    schedule: ["PROPOSE", "HOLD"],
    "review-pay": ["CONCUR", "REFUSE"],
  },
  intake: { triage: ["ROUTE", "REJECT"] },
  books_intake: { capture: ["ROUTE", "REJECT"] },
  world_reply: { reply: ["SENT", "HOLD"] },
  stripe_payout: { unpack: ["DONE", "HOLD"] },
  bank_line: { land: ["DONE", "HOLD"] },
  cash_line: {
    reconcile: ["MATCHED", "EXPLAINED", "UNEXPLAINED"],
    "review-rec": ["CONCUR", "REFUSE"],
  },
  ar_apply: {
    apply: ["PROPOSE", "HOLD"],
    "review-apply": ["CONCUR", "REFUSE"],
  },
  collect: { chase: ["SENT", "HOLD"] },
  month_end: {
    accrue: ["PROPOSE", "NONE"],
    prepaid: ["PROPOSE", "NONE"],
    assets: ["PROPOSE", "NONE"],
    bs: ["PROPOSE", "NONE"],
    "review-treatment": ["CONCUR", "REFUSE"],
    "review-assets": ["CONCUR", "REFUSE"],
    "review-bs": ["CONCUR", "REFUSE"],
    lock: ["CONCUR", "REFUSE"],
  },
  story: {
    flux: ["DRAFT", "HOLD"],
    forecast: ["DRAFT", "HOLD"],
  },
  audit: {
    interpret: ["FINDING", "NONE"],
    report: ["DRAFT"],
  },
};

export function allowedDecisions(workflow: string, step: string): readonly string[] {
  return DECISIONS[workflow]?.[step] ?? [];
}

function invoiceOf(item: Item): string {
  const fromFacts = item.facts.invoice_id;
  if (typeof fromFacts === "string" && fromFacts.length > 0) return fromFacts;
  const cut = item.id.indexOf(":");
  return cut === -1 ? item.id : item.id.slice(cut + 1);
}

function billFacts(computerRoot: string, item: Item): BillFacts {
  return readBillFacts(computerRoot, invoiceOf(item));
}

function next(step: string, owner: string): Advance {
  return { kind: "next", step, owner };
}

function terminal(name: string): Advance {
  return { kind: "terminal", terminal: name };
}

function emit(workflow: string, id: string, step: string, owner: string, facts: Record<string, unknown> = {}): Advance {
  return { kind: "emit", emit: { workflow, id, step, owner, facts }, terminal: "emitted" };
}

function openBill(computerRoot: string, item: Item, result: StepResult): Advance {
  const facts = billFacts(computerRoot, item);
  const held = result.decision === "HOLD" || facts.must_hold.length > 0;
  if (item.step === "match") {
    if (held) return terminal("hold");
    if (result.decision === "INVESTIGATE" || facts.exception_types.length > 0) return next("investigate", "ap");
    if (result.decision === "APPROVE" && facts.clean) return next("review-match", "ctl-pay");
    return terminal("hold");
  }
  if (item.step === "investigate") {
    if (result.decision === "APPROVE" && facts.must_hold.length === 0) return next("review-match", "ctl-pay");
    return terminal("hold");
  }
  if (item.step === "review-match") {
    if (result.decision === "CONCUR" && facts.must_hold.length === 0) {
      const invoiceId = invoiceOf(item);
      return emit("pay_run", `pay:${invoiceId}`, "schedule", "pay", {
        invoice_id: invoiceId,
        amount: facts.amount,
        po_id: facts.po_id,
        receipt_id: facts.receipt_id,
      });
    }
    return terminal("hold");
  }
  return terminal("hold");
}

function payRun(item: Item, result: StepResult): Advance {
  if (item.step === "schedule") {
    if (result.decision === "PROPOSE") return next("review-pay", "ctl-pay");
    return terminal("hold");
  }
  if (item.step === "review-pay") {
    if (result.decision === "CONCUR") return terminal("decided");
    return terminal("hold");
  }
  return terminal("hold");
}

function intake(item: Item, result: StepResult, workflow: "intake" | "books_intake"): Advance {
  if (result.decision === "REJECT") return terminal("rejected");
  const created = item.facts.billCreated === true;
  if (!created) return terminal("no-bill");
  const invoiceId = invoiceOf(item);
  return emit("open_bill", `bill:${invoiceId}`, "match", "ap", {
    invoice_id: invoiceId,
    channel: item.channel,
    source: item.source,
  });
}

function worldReply(result: StepResult): Advance {
  return result.decision === "SENT" ? terminal("sent") : terminal("hold");
}

function cashEmit(item: Item, kind: string): Advance {
  const id = typeof item.facts.line_id === "string" ? item.facts.line_id : item.id.slice(item.id.indexOf(":") + 1);
  return emit("cash_line", `cash:${id}`, "reconcile", "cash", { line_id: id, origin: kind });
}

function cashLine(computerRoot: string, item: Item, result: StepResult): Advance {
  if (item.step === "reconcile") {
    if (result.decision === "UNEXPLAINED") return next("review-rec", "ctl-cash");
    const amount = typeof item.facts.amount === "number" ? item.facts.amount : 0;
    if (cashSignOffRequired(computerRoot, amount, result.decision)) return next("review-rec", "ctl-cash");
    return terminal("reconciled");
  }
  if (item.step === "review-rec") {
    const unexplained = result.decision === "REFUSE" || item.facts.unexplained === true;
    if (unexplained) return terminal("open");
    return terminal("signed");
  }
  return terminal("open");
}

function monthEnd(item: Item, result: StepResult): Advance {
  if (result.decision === "NONE") return terminal("none");
  if (item.step === "accrue" || item.step === "prepaid") {
    if (result.decision === "PROPOSE") return next("review-treatment", "ctl-books");
  }
  if (item.step === "assets" && result.decision === "PROPOSE") return next("review-assets", "ctl-books");
  if (item.step === "bs" && result.decision === "PROPOSE") return next("review-bs", "ctl-books");
  if (item.step === "lock") {
    return terminal(result.decision === "CONCUR" ? "lock-proposed" : "lock-refused");
  }
  if (result.decision === "CONCUR" || result.decision === "REFUSE") {
    return terminal(result.decision === "CONCUR" ? "concurred" : "refused");
  }
  return terminal("hold");
}

export function advance(computerRoot: string, item: Item, result: StepResult): Advance {
  switch (item.workflow) {
    case "open_bill":
      return openBill(computerRoot, item, result);
    case "pay_run":
      return payRun(item, result);
    case "intake":
      return intake(item, result, "intake");
    case "books_intake":
      return intake(item, result, "books_intake");
    case "world_reply":
      return worldReply(result);
    case "stripe_payout":
      return result.decision === "DONE" ? cashEmit(item, "stripe") : terminal("hold");
    case "bank_line":
      return result.decision === "DONE" ? cashEmit(item, "bank") : terminal("hold");
    case "cash_line":
      return cashLine(computerRoot, item, result);
    case "ar_apply":
      if (item.step === "apply") return result.decision === "PROPOSE" ? next("review-apply", "ctl-cash") : terminal("hold");
      return terminal(result.decision === "CONCUR" ? "concurred" : "refused");
    case "collect":
      return terminal(result.decision === "SENT" ? "sent" : "hold");
    case "month_end":
      return monthEnd(item, result);
    case "story":
      return terminal(result.decision === "DRAFT" ? "draft" : "hold");
    case "audit":
      if (item.step === "interpret") return next("report", "audit");
      return terminal("draft");
    default:
      return terminal("unknown-workflow");
  }
}

import { GRAIN_SLUGS } from "./agents";
import { CAPABILITIES } from "./capabilities";
import {
  CAPABILITY_ROWS,
  capabilityById,
  compactPipeCounts,
  filterCapabilities,
} from "./capabilityMatrix";

const WALL_IDS = [
  "inbox.counterparty_to_ap",
  "ingestion.classify_document",
  "ingestion.structured_parse",
  "ingestion.bank_card_discovery",
  "ap.three_way_match",
  "ap.payment_scheduling",
  "ap.self_improvement",
  "ap.vendor_bank_change",
  "ar.aging_collections",
  "ar.cash_application",
  "memory.self_improvement",
  "cash.bank_reconciliation",
  "cash.stripe_reconciliation",
  "close.accruals",
  "close.prepaids",
  "close.fixed_assets",
  "close.balance_sheet_recs",
  "close.month_end",
  "audit.controls",
  "reporting.variance_board",
  "forecast.thirteen_week",
  "memory.cross_period",
  "orchestration.cfo",
  "evaluation.finance_gauntlet",
] as const;

test("matrix ids match CAPABILITIES.md and are not invented", () => {
  expect(CAPABILITY_ROWS.map((row) => row.id)).toEqual([...WALL_IDS]);
  expect(CAPABILITY_ROWS).toHaveLength(24);
});

test("honesty statuses match the Now column and required overrides", () => {
  expect(capabilityById("ap.self_improvement")?.status).toBe("not-built");
  expect(capabilityById("ap.vendor_bank_change")?.status).toBe("not-built");
  expect(capabilityById("inbox.counterparty_to_ap")?.status).toBe("partial");
  expect(capabilityById("ar.aging_collections")?.status).toBe("partial");
  expect(capabilityById("close.month_end")?.status).toBe("partial");
  expect(capabilityById("evaluation.finance_gauntlet")?.status).toBe("kernel-live");
  expect(capabilityById("evaluation.finance_gauntlet")?.caption).toMatch(/Kernel measure, not the office score/);
  expect(capabilityById("memory.cross_period")?.status).toBe("kernel-live");
});

test("matrix blob does not contain 100% accurate", () => {
  expect(JSON.stringify(CAPABILITY_ROWS)).not.toMatch(/100% accurate/i);
});

test("CAPABILITIES rows keep grain-slug agents arrays", () => {
  const slugs = new Set<string>(GRAIN_SLUGS);
  expect(CAPABILITIES).toBe(CAPABILITY_ROWS);
  for (const item of CAPABILITIES) {
    expect(Array.isArray(item.agents)).toBe(true);
    for (const slug of item.agents) {
      expect(slugs.has(slug)).toBe(true);
    }
  }
});

test("World is not claimed as a live grain agent", () => {
  for (const row of CAPABILITY_ROWS) {
    expect(row.agents).not.toContain("world");
  }
  expect(capabilityById("inbox.counterparty_to_ap")?.notice).toMatch(/World Bot not on live roster/);
});

test("Not built filter returns only not-built ids", () => {
  const rows = filterCapabilities("not-built");
  expect(rows.map((row) => row.id)).toEqual(["ap.self_improvement", "ap.vendor_bank_change"]);
});

test("compact pipe counts cover four pipes", () => {
  const counts = compactPipeCounts();
  expect(counts.map((item) => item.pipe)).toEqual(["intake", "pay", "cash", "close"]);
  const pay = counts.find((item) => item.pipe === "pay");
  expect(pay?.live).toBe(2);
  expect(pay?.notBuilt).toBe(2);
});

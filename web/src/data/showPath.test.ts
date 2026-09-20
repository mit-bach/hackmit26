import { GRAIN_SLUGS } from "./agents";
import { formatMatchType } from "../copy";
import { INVOICE_STORY } from "./workflowStory";
import { SHOW_STORIES, parseShowStory, showStoryById } from "./showPath";

test("parseShowStory maps known keys and falls back to clean", () => {
  expect(parseShowStory("clean")).toBe("clean");
  expect(parseShowStory("resolved")).toBe("resolved");
  expect(parseShowStory("unresolved")).toBe("unresolved");
  expect(parseShowStory("nope")).toBe("clean");
  expect(parseShowStory(null)).toBe("clean");
});

test("CLEAN ticker IDs travel from AP to bank", () => {
  const clean = showStoryById("clean");
  expect(clean.ids).toEqual(["INV-001", "PO-101", "GR-101", "PAY-AP-001", "TXN-2026-09-018A"]);
  expect(clean.nodes.some((node) => node.id === "world")).toBe(false);
  expect(clean.steps[clean.steps.length - 1]?.status).toBe("done");
  expect(JSON.stringify(clean)).not.toMatch(/ADV-CASH-014|SL-ADV-RESIDUAL/);
});

test("RESOLVED names FEE-729103 and FEE_NETTED", () => {
  const resolved = showStoryById("resolved");
  const blob = JSON.stringify(resolved);
  expect(resolved.ids).toEqual(expect.arrayContaining(["FEE-729103", "TXN-2026-09-011", "INV-017"]));
  expect(blob).toContain("FEE_NETTED");
  expect(blob).toContain(formatMatchType("FEE_NETTED"));
  expect(blob.toLowerCase()).not.toMatch(/unexplained/);
  expect(resolved.steps.some((step) => step.nodeId === "close" && step.status === "blocked")).toBe(
    false
  );
});

test("UNRESOLVED keeps the $12.40 gap and does not finish close", () => {
  const unresolved = showStoryById("unresolved");
  const blob = JSON.stringify(unresolved);
  expect(blob).toMatch(/12\.40|\$12,412\.40/);
  expect(blob).not.toMatch(/\bCLOSED\b/);
  expect(blob).not.toMatch(/ADV-CASH-014|SL-ADV-RESIDUAL/);
  expect(unresolved.steps.some((step) => step.nodeId === "close" && step.status === "blocked")).toBe(
    true
  );
  expect(unresolved.outcome).toBe("BLOCKED");
});

test("INVOICE_STORY is the CLEAN spine with grain slugs", () => {
  const slugs = new Set<string>(GRAIN_SLUGS);
  expect(INVOICE_STORY.length).toBeGreaterThan(0);
  for (const step of INVOICE_STORY) {
    expect(slugs.has(step.agent)).toBe(true);
  }
});

test("three public stories exist", () => {
  expect(SHOW_STORIES.map((item) => item.id)).toEqual(["clean", "resolved", "unresolved"]);
});

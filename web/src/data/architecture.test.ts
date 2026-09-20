import { AGENTS, GRAIN_SLUGS } from "./agents";
import { CAPABILITIES } from "./capabilities";
import { HANDOFFS } from "./handoffs";
import { SIMULATIONS } from "./simulations";
import { videoHasMedia, VIDEOS } from "./videos";
import { INVOICE_STORY } from "./workflowStory";

test("architecture data matches the 15 grain slugs", () => {
  expect([...GRAIN_SLUGS]).toEqual([
    "email",
    "stripe",
    "bank",
    "books",
    "ap",
    "pay",
    "apply",
    "collect",
    "cash",
    "close",
    "story",
    "ctl-pay",
    "ctl-cash",
    "ctl-books",
    "audit",
  ]);
  expect(AGENTS.map((agent) => agent.slug)).toEqual([...GRAIN_SLUGS]);
});

test("every handoff and simulation agent exists", () => {
  const slugs = new Set<string>(GRAIN_SLUGS);
  for (const edge of HANDOFFS) {
    expect(slugs.has(edge.from)).toBe(true);
    expect(slugs.has(edge.to)).toBe(true);
    expect(edge.why.length).toBeGreaterThan(20);
  }
  for (const item of SIMULATIONS) {
    for (const slug of item.agents) expect(slugs.has(slug)).toBe(true);
  }
  for (const item of CAPABILITIES) {
    for (const slug of item.agents) expect(slugs.has(slug)).toBe(true);
  }
  for (const step of INVOICE_STORY) {
    expect(slugs.has(step.agent)).toBe(true);
  }
  for (const video of VIDEOS) {
    for (const slug of video.agents) expect(slugs.has(slug)).toBe(true);
    expect(videoHasMedia(video)).toBe(true);
    expect(video.src).toMatch(/^\/videos\/.+\.mp4$/);
  }
});

test("does not claim fabricated pass rates in static catalogs", () => {
  const blob = JSON.stringify({ SIMULATIONS, VIDEOS, CAPABILITIES });
  expect(blob).not.toMatch(/100% accurate/i);
  expect(blob).not.toMatch(/HARDCODED_PASS/);
});

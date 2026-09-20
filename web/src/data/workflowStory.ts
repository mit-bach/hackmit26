import type { AgentSlug } from "./agents";
import { GRAIN_SLUGS } from "./agents";
import { showStoryById } from "./showPath";

export interface StoryStep {
  n: number;
  title: string;
  body: string;
  agent: AgentSlug;
  handoff?: string;
}

function isGrainSlug(value: string): value is AgentSlug {
  return (GRAIN_SLUGS as readonly string[]).includes(value);
}

const CLEAN = showStoryById("clean");

const CLEAN_STEPS = CLEAN.steps.filter((step) => isGrainSlug(step.nodeId));

/** CLEAN spine — grain slugs only, derived from show-path steps. */
export const INVOICE_STORY: StoryStep[] = CLEAN_STEPS.map((step, index) => ({
  n: index + 1,
  title: step.title,
  body: step.body ?? "",
  agent: step.nodeId,
  handoff: step.handoff ? `Handle to ${step.handoff.to}: ${step.handoff.why}` : undefined,
}));

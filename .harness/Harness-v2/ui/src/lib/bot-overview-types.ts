import type { BotSettingsSection } from "@/state/store";

export interface BotOverview {
  who: { name: string; title: string; blurb: string; soulLead: string };
  does: string[];
  reaches: string[];
  wont: string[];
  recent: Array<{ at: number; summary: string }>;
  /** Setup checklist; absent from servers older than this field. */
  setup?: SetupStep[];
}

export interface SetupStep {
  id: "identity" | "soul" | "folder" | "apps" | "schedule";
  label: string;
  done: boolean;
  section?: BotSettingsSection;
}

import { BookOpen, Brain, CalendarClock, LayoutDashboard, type LucideIcon, ShieldCheck, User } from "lucide-react";

import type { BotSettingsSection } from "@/state/store";

export const BOT_SECTIONS: Array<{
  id: BotSettingsSection;
  label: string;
  icon: LucideIcon;
  keywords: string[];
}> = [
  { id: "overview", label: "Overview", icon: LayoutDashboard, keywords: ["summary", "status", "purpose", "slug"] },
  { id: "identity", label: "Identity", icon: User, keywords: ["name", "slug", "purpose", "instructions", "avatar"] },
  { id: "skills", label: "Skills", icon: BookOpen, keywords: ["skills", "SKILL.md", "grant"] },
  { id: "memory", label: "Memory", icon: Brain, keywords: ["memory", "notes", "MEMORY.md"] },
  { id: "routines", label: "Routines", icon: CalendarClock, keywords: ["schedule", "routines", "cadence"] },
  { id: "permissions", label: "Approvals", icon: ShieldCheck, keywords: ["approval", "ask", "always", "never"] },
];

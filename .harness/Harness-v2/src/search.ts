import { liveStatus } from "./lane-state.ts";
import { loadRoster } from "./roster.ts";
import type { BotStatus, SearchHit } from "./types.ts";

export function searchAgents(
  computerRoot: string,
  query: string,
  status?: BotStatus,
): SearchHit[] {
  const roster = loadRoster(computerRoot);
  const needle = query.trim().toLowerCase();
  const hits: SearchHit[] = [];
  for (const bot of roster.bots) {
    const hay = `${bot.id} ${bot.slug} ${bot.name} ${bot.purpose}`.toLowerCase();
    if (needle.length > 0 && !hay.includes(needle)) {
      continue;
    }
    const live = liveStatus(computerRoot, bot.id);
    if (status && live !== status) {
      continue;
    }
    hits.push({
      id: bot.id,
      slug: bot.slug,
      name: bot.name,
      purpose: bot.purpose,
      status: live,
    });
  }
  return hits;
}

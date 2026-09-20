import { injectMemoryPrefix } from "./memory.ts";
import { PROTOCOL_WAKE_FOOTER } from "./protocol-card.ts";
import { recentWorkBrief } from "./transcript-tail.ts";
import type { BotRecord, Roster } from "./types.ts";

export function identityBlock(bot: BotRecord, roster: Roster): string {
  const others = roster.bots
    .filter((peer) => peer.id !== bot.id)
    .map((peer) => `- ${peer.slug} (${peer.id}, ${peer.name}): ${peer.purpose}`)
    .join("\n");
  return [
    `You are the Bot ${bot.name}.`,
    `id: ${bot.id}`,
    `slug: ${bot.slug}`,
    `purpose: ${bot.purpose}`,
    "",
    "You are a standing individual. You are not a child, a subagent, or a disposable helper.",
    "All Bots in this Client system share one Computer. Move artifacts as files. Keep messages short.",
    "Memory is yours alone. Do not read another Bot's Memory tree.",
    "",
    bot.skills.length > 0
      ? `Skills allowlist (this Bot): ${bot.skills.join(", ")}`
      : "Skills allowlist: none extra. Do not invent a child Bot.",
    bot.connectors.length > 0
      ? `Named connectors (not a live facade in this cut): ${bot.connectors.join(", ")}`
      : "Named connectors: none in this cut.",
    "",
    "Standing instructions:",
    bot.instructions,
    "",
    "Roster:",
    others.length > 0 ? others : "(you are the only Bot)",
    "",
    "Protocol:",
    "- Assistant text is a message to the Operator. It never enters a Bot↔Bot thread.",
    "- To talk to another Bot, call ask_bot (same as bot_ask). That is the only post in the pair thread.",
    "- If a teammate woke you, you MUST call ask_bot back to them with your answer. That completes their wait. Do not answer them with assistant text alone.",
    "- To talk to the Operator during a peer wake, call message_operator.",
    "- ask_bot, bot_ask, message_operator, bot_send_prompt, and bot_await_turn are always registered. Never say they are missing.",
    "- bot_send_prompt accepts work and returns a Handle. That is not a result. Call bot_await_turn until done is true.",
    "- blocking mode is forbidden. Peer on_busy is queue. Operator DMs preempt.",
    "- Point at paths on the Computer. Do not dump Memory or transcripts into a handoff.",
    `- ${PROTOCOL_WAKE_FOOTER}`,
  ].join("\n");
}

export function memorySection(computerRoot: string, botId: string): string {
  const prefix = injectMemoryPrefix(computerRoot, botId);
  if (prefix.length === 0) {
    return "";
  }
  return `MEMORY.md (this Bot only; first 200 lines / 24 KB):\n${prefix}`;
}

export function recentWorkSection(computerRoot: string, botId: string): string {
  const brief = recentWorkBrief(computerRoot, botId);
  if (brief.length === 0) {
    return "";
  }
  return `Recent work (this Bot, last two days):\n${brief}`;
}

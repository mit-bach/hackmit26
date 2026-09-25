/**
 * GrokBot conversation kind 2: Bot↔Bot direct handoff.
 *
 * The pair UI renders harness/threads/*.json — only ask_bot / bot_ask posts.
 * Session thinking and Kernel tools stay on each Bot's operator desk.
 */
import { findBot, loadRoster } from "../roster.ts";
import { readProtocol } from "../protocol-log.ts";
import type { Roster } from "../types.ts";
import { isPairChannelId, pairChannelId, parsePairChannelId } from "./pair-id.ts";
import { listThreadFiles, readThread, seedThreadsFromProtocol, type ThreadFile } from "./thread-log.ts";

export { isPairChannelId, pairChannelId, parsePairChannelId } from "./pair-id.ts";

const MAUS_COLORS = [
  "teal",
  "blue",
  "purple",
  "pink",
  "orange",
  "cyan",
  "green",
  "coral",
  "yellow",
  "red",
] as const;

type MausColor = (typeof MAUS_COLORS)[number];

export interface PairSpeaker {
  readonly botId: string;
  readonly name: string;
  readonly color: MausColor;
}

export interface PairMessage {
  readonly id: string;
  readonly role: "bot";
  readonly kind: "text" | "activity";
  readonly text: string;
  readonly at: number;
  readonly from: PairSpeaker;
  readonly parentId: string | null;
  readonly handleId?: string;
  readonly reasoning?: string;
  readonly tool?: {
    readonly name: string;
    readonly ok?: boolean;
    readonly spoken?: string;
    readonly summary?: string;
    readonly input?: string;
    readonly output?: string;
  };
}

export interface PairChannel {
  readonly id: string;
  readonly threadId: string;
  readonly name: string;
  readonly memberIds: readonly string[];
  readonly defaultResponder: { readonly kind: "mentions" };
  readonly bulletin: string;
  readonly unread: false;
  readonly createdAt: number;
  readonly dm: true;
  readonly setupCompletedAt: number;
  readonly messages: readonly PairMessage[];
  readonly activeLeafId: string | null;
}

function colorFor(index: number): MausColor {
  return MAUS_COLORS[index % MAUS_COLORS.length] ?? "teal";
}

function speakerOf(roster: Roster, botId: string): PairSpeaker | undefined {
  const bot = findBot(roster, botId);
  if (!bot) {
    return undefined;
  }
  const index = roster.bots.findIndex((row) => row.id === bot.id);
  return { botId: bot.id, name: bot.name, color: colorFor(index) };
}

/** True when this Handle is Bot↔Bot, not Operator DM or a Room. */
export function isPeerHandoff(
  roster: Roster,
  fromId: string | undefined,
  toId: string | undefined,
): boolean {
  if (!fromId || !toId || fromId === "operator" || fromId === "harness") {
    return false;
  }
  const from = speakerOf(roster, fromId);
  const to = speakerOf(roster, toId);
  return Boolean(from && to && from.botId !== to.botId);
}

function toPairChannel(file: ThreadFile): PairChannel {
  const messages: PairMessage[] = file.messages.map((row, index) => ({
    id: row.id,
    role: "bot",
    kind: "text",
    text: row.text,
    at: row.at,
    from: row.from,
    parentId: index === 0 ? null : file.messages[index - 1]?.id ?? null,
    handleId: row.handleId,
  }));
  return {
    id: file.id,
    threadId: file.threadId,
    name: file.name,
    memberIds: file.memberIds,
    defaultResponder: { kind: "mentions" },
    bulletin: "",
    unread: false,
    createdAt: file.createdAt,
    dm: true,
    setupCompletedAt: file.createdAt,
    messages,
    activeLeafId: messages.at(-1)?.id ?? null,
  };
}

/** All Bot↔Bot handoff logs on this Computer, newest pair last. */
export function listPairChannels(computerRoot: string, roster?: Roster): PairChannel[] {
  const liveRoster = roster ?? loadRoster(computerRoot);
  seedThreadsFromProtocol(computerRoot, readProtocol(computerRoot), liveRoster);
  return listThreadFiles(computerRoot)
    .map(toPairChannel)
    .filter((row) => {
      const parsed = parsePairChannelId(row.id);
      if (!parsed) {
        return false;
      }
      return Boolean(findBot(liveRoster, parsed.a) && findBot(liveRoster, parsed.b));
    });
}

export function getPairChannel(
  computerRoot: string,
  pairId: string,
  roster?: Roster,
): PairChannel | undefined {
  const liveRoster = roster ?? loadRoster(computerRoot);
  seedThreadsFromProtocol(computerRoot, readProtocol(computerRoot), liveRoster);
  const file = readThread(computerRoot, pairId);
  return file ? toPairChannel(file) : listPairChannels(computerRoot, liveRoster).find((row) => row.id === pairId);
}

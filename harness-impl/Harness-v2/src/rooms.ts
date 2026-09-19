import { awaitTurn } from "./await.ts";
import { appendJsonlAtomic, readJsonl, withFileLockAsync } from "./fs.ts";
import { nowIso } from "./ids.ts";
import { isLaneBusy } from "./lane-state.ts";
import { roomLockPath, roomLogPath } from "./paths.ts";
import { appendProtocol } from "./protocol-log.ts";
import { findBot, findRoom, loadRoster, requireBot } from "./roster.ts";
import { sendPrompt } from "./send.ts";
import { sleep } from "./sleep.ts";
import type { Conversation, MessageKind } from "./types.ts";

export interface RoomPost {
  readonly t: string;
  readonly from: string;
  readonly text: string;
  readonly mentions: readonly string[];
  readonly kind: "post" | "chip";
}

export interface RoomPostOptions {
  readonly computerRoot: string;
  readonly roomId: string;
  readonly from: string;
  readonly text: string;
  readonly waitCapMs?: number;
  readonly awaitTimeoutMs?: number;
}

function parseMentions(text: string, members: readonly string[]): string[] {
  const found: string[] = [];
  for (const member of members) {
    const re = new RegExp(`@${member}\\b`, "i");
    if (re.test(text)) {
      found.push(member);
    }
  }
  return found;
}

function parseRoomPost(value: unknown): RoomPost | undefined {
  if (typeof value !== "object" || value === null) {
    return undefined;
  }
  const rec = value as Record<string, unknown>;
  if (typeof rec.t !== "string" || typeof rec.from !== "string" || typeof rec.text !== "string") {
    return undefined;
  }
  const kind = rec.kind === "chip" ? "chip" : "post";
  const mentions = Array.isArray(rec.mentions)
    ? rec.mentions.filter((item): item is string => typeof item === "string")
    : [];
  return { t: rec.t, from: rec.from, text: rec.text, mentions, kind };
}

export function readRoomLog(computerRoot: string, roomId: string): RoomPost[] {
  const rows: RoomPost[] = [];
  for (const raw of readJsonl(roomLogPath(computerRoot, roomId))) {
    const parsed = parseRoomPost(raw);
    if (parsed) {
      rows.push(parsed);
    }
  }
  return rows;
}

function appendRoomLog(computerRoot: string, roomId: string, post: RoomPost): void {
  appendJsonlAtomic(roomLogPath(computerRoot, roomId), post);
}

export async function roomPost(options: RoomPostOptions): Promise<{ readonly handles: readonly string[] }> {
  const roster = loadRoster(options.computerRoot);
  const room = findRoom(roster, options.roomId);
  if (!room) {
    throw new Error(`unknown room ${options.roomId}`);
  }
  const fromBot = options.from === "operator" || options.from === "harness"
    ? undefined
    : findBot(roster, options.from);
  const fromId = fromBot?.id ?? options.from;
  const mentions = parseMentions(options.text, room.members);
  const wakeSlugs = mentions.length > 0 ? mentions : [...room.members];
  const kind: MessageKind = mentions.length > 0 ? "group_mention" : "group_post";
  const waitCapMs = options.waitCapMs ?? 60_000;
  const handles: string[] = [];

  return await withFileLockAsync(roomLockPath(options.computerRoot, options.roomId), async () => {
    const post: RoomPost = {
      t: nowIso(),
      from: fromId,
      text: options.text,
      mentions,
      kind: "post",
    };
    appendRoomLog(options.computerRoot, options.roomId, post);
    appendProtocol(options.computerRoot, {
      type: "room.post",
      from: fromId,
      roomId: room.id,
      text: options.text,
    });

    for (const slug of room.members) {
      if (!wakeSlugs.includes(slug)) {
        continue;
      }
      const bot = requireBot(roster, slug);
      const busyStarted = Date.now();
      while (isLaneBusy(options.computerRoot, bot.id) && Date.now() - busyStarted < waitCapMs) {
        await sleep(50);
      }
      if (isLaneBusy(options.computerRoot, bot.id)) {
        const chip: RoomPost = {
          t: nowIso(),
          from: "harness",
          text: `${slug} still busy, round continued`,
          mentions: [],
          kind: "chip",
        };
        appendRoomLog(options.computerRoot, options.roomId, chip);
        appendProtocol(options.computerRoot, {
          type: "room.chip",
          to: bot.id,
          slug,
          roomId: room.id,
          text: chip.text,
        });
        continue;
      }
      const conversation: Conversation = { kind: "room", roomId: room.id };
      const sent = sendPrompt({
        computerRoot: options.computerRoot,
        from: fromId,
        to: bot.id,
        prompt: options.text,
        kind,
        mentions: wakeSlugs,
        conversation,
      });
      if (!sent.accepted || !sent.handleId) {
        continue;
      }
      handles.push(sent.handleId);
      await awaitTurn(options.computerRoot, sent.handleId, {
        timeoutMs: options.awaitTimeoutMs ?? waitCapMs + 30_000,
      });
    }
    return { handles };
  });
}

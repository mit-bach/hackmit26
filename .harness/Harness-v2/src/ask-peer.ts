import { awaitTurn } from "./await.ts";
import { findHandle, isTerminalStatus, readHandle, transitionHandle } from "./handle.ts";
import { nowIso } from "./ids.ts";
import { appendProtocol } from "./protocol-log.ts";
import { findBot, loadRoster } from "./roster.ts";
import { sendPrompt } from "./send.ts";
import { appendThreadReply } from "./server/thread-log.ts";
import { appendTranscript } from "./transcript.ts";
import type { AskPeerResult, BotRecord, InboxItem, ParsedAsk, Roster, TurnResult } from "./types.ts";

export interface AskPeerRequest {
  readonly computerRoot: string;
  readonly from: string;
  readonly to: string;
  readonly prompt: string;
  readonly timeoutMs?: number;
  readonly inbound?: InboxItem;
}

export interface ReplyPeerRequest {
  readonly computerRoot: string;
  readonly fromId: string;
  readonly inbound: InboxItem;
  readonly text: string;
}

const UNNAMED_ASK =
  /^ask\s+(?:one of(?: your)?|another|a|any)\s+(?:agents?|bots?|teammates?|peers?)\s+(.+)$/i;
const ASK_LEAD = /^(?:ask|tell|ping|message)\s+(?:the\s+)?(.+)$/i;
const AT_TOKEN = /@([A-Za-z][A-Za-z0-9_-]*)/g;

function normalizeKey(value: string): string {
  return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, "");
}

function editDistance(left: string, right: string): number {
  if (left === right) {
    return 0;
  }
  if (left.length === 0) {
    return right.length;
  }
  if (right.length === 0) {
    return left.length;
  }
  const row: number[] = [];
  for (let i = 0; i <= right.length; i += 1) {
    row.push(i);
  }
  for (let i = 1; i <= left.length; i += 1) {
    let prev = row[0] ?? 0;
    row[0] = i;
    for (let j = 1; j <= right.length; j += 1) {
      const cur = row[j] ?? 0;
      const cost = left[i - 1] === right[j - 1] ? 0 : 1;
      row[j] = Math.min((row[j] ?? 0) + 1, (row[j - 1] ?? 0) + 1, prev + cost);
      prev = cur;
    }
  }
  return row[right.length] ?? Math.max(left.length, right.length);
}

function firstOther(roster: Roster, fromId: string | undefined): BotRecord | undefined {
  return roster.bots.find((bot) => bot.id !== fromId);
}

export function resolvePeer(key: string, roster: Roster, fromKey?: string): BotRecord | undefined {
  const from = fromKey ? findBot(roster, fromKey) : undefined;
  const exact = findBot(roster, key);
  if (exact && exact.id !== from?.id) {
    return exact;
  }
  const query = normalizeKey(key);
  if (query.length < 3) {
    return undefined;
  }
  let best: BotRecord | undefined;
  let bestDistance = 99;
  for (const bot of roster.bots) {
    if (bot.id === from?.id) {
      continue;
    }
    for (const label of [bot.slug, bot.name, bot.id]) {
      const normalized = normalizeKey(label);
      if (normalized.length === 0) {
        continue;
      }
      if (normalized === query || (normalized.length >= 3 && (normalized.includes(query) || query.includes(normalized)))) {
        return bot;
      }
      const distance = editDistance(query, normalized);
      const max = normalized.length >= 6 ? 2 : 1;
      if (distance <= max && distance < bestDistance) {
        best = bot;
        bestDistance = distance;
      }
    }
  }
  return best;
}

function matchPeerPrefix(rest: string, roster: Roster, fromId: string | undefined): ParsedAsk | undefined {
  const labels: Array<{ readonly bot: BotRecord; readonly label: string }> = [];
  for (const bot of roster.bots) {
    if (bot.id === fromId) {
      continue;
    }
    labels.push({ bot, label: bot.name }, { bot, label: bot.slug }, { bot, label: bot.id });
  }
  labels.sort((left, right) => right.label.length - left.label.length);
  const lowered = rest.toLowerCase();
  for (const { bot, label } of labels) {
    if (!lowered.startsWith(label.toLowerCase())) {
      continue;
    }
    let after = rest.slice(label.length).trim().replace(/^(agent|bot)\b\s*/i, "");
    if (after.length === 0) {
      continue;
    }
    return { slug: bot.slug, botId: bot.id, question: after };
  }
  const token = rest.split(/\s+/)[0] ?? "";
  const fuzzy = resolvePeer(token, roster, fromId);
  if (!fuzzy) {
    return undefined;
  }
  let after = rest.slice(token.length).trim().replace(/^(agent|bot)\b\s*/i, "");
  if (after.length === 0) {
    return undefined;
  }
  return { slug: fuzzy.slug, botId: fuzzy.id, question: after };
}

export function parseAskPeer(text: string, roster: Roster, fromKey: string): ParsedAsk | undefined {
  const trimmed = text.trim();
  if (trimmed.length === 0) {
    return undefined;
  }
  const from = findBot(roster, fromKey);
  const fromId = from?.id;

  AT_TOKEN.lastIndex = 0;
  let atMatch = AT_TOKEN.exec(trimmed);
  while (atMatch) {
    const token = atMatch[1] ?? "";
    const peer = resolvePeer(token, roster, fromKey);
    if (peer) {
      const question = trimmed.replace(atMatch[0], "").trim();
      if (question.length > 0) {
        return { slug: peer.slug, botId: peer.id, question };
      }
    }
    atMatch = AT_TOKEN.exec(trimmed);
  }

  const unnamed = UNNAMED_ASK.exec(trimmed);
  if (unnamed) {
    const peer = firstOther(roster, fromId);
    const question = unnamed[1]?.trim() ?? "";
    if (peer && question.length > 0) {
      return { slug: peer.slug, botId: peer.id, question };
    }
  }

  const lead = ASK_LEAD.exec(trimmed);
  if (lead) {
    return matchPeerPrefix(lead[1] ?? "", roster, fromId);
  }
  return undefined;
}

export async function askPeer(request: AskPeerRequest): Promise<AskPeerResult> {
  const sent = sendPrompt({
    computerRoot: request.computerRoot,
    from: request.from,
    to: request.to,
    prompt: request.prompt,
    kind: "a2a_handoff",
    mode: "async",
  });
  if (!sent.accepted || !sent.handleId) {
    return { accepted: false, reason: sent.reason ?? "not accepted" };
  }
  const done = await awaitTurn(request.computerRoot, sent.handleId, {
    timeoutMs: request.timeoutMs ?? 90_000,
  });
  const handle = findHandle(request.computerRoot, sent.handleId);
  return {
    accepted: true,
    handleId: sent.handleId,
    status: done.status,
    done: done.done,
    result: done.result ?? handle?.result,
    error: handle?.error,
    reason: done.done ? undefined : (handle?.error ?? "peer still running"),
  };
}

/** Receiver posts in the pair thread and completes the inbound Handle. Does not wait. */
export function replyPeerMessage(request: ReplyPeerRequest): AskPeerResult {
  const trimmed = request.text.trim();
  if (trimmed.length === 0) {
    return { accepted: false, reason: "empty reply" };
  }
  const inbound = request.inbound;
  if (inbound.kind !== "a2a_handoff") {
    return { accepted: false, reason: "not a peer wake" };
  }
  const roster = loadRoster(request.computerRoot);
  const self = findBot(roster, request.fromId);
  const peer = findBot(roster, inbound.from);
  if (!self || !peer) {
    return { accepted: false, reason: "unknown bot" };
  }
  const handle = readHandle(request.computerRoot, inbound.to, inbound.handleId);
  if (!handle) {
    return { accepted: false, reason: "unknown handle" };
  }
  if (isTerminalStatus(handle.status)) {
    appendThreadReply(
      request.computerRoot,
      self.id,
      peer.id,
      inbound.handleId,
      trimmed,
      nowIso(),
    );
    return {
      accepted: true,
      handleId: inbound.handleId,
      status: handle.status,
      done: true,
      result: handle.result ?? trimmed,
    };
  }
  if (handle.status === "accepted" || handle.status === "queued") {
    transitionHandle(request.computerRoot, inbound.to, inbound.handleId, "running");
  }
  const createdAt = nowIso();
  appendThreadReply(request.computerRoot, self.id, peer.id, inbound.handleId, trimmed, createdAt);
  const event = appendProtocol(request.computerRoot, {
    type: "thread.reply",
    from: self.id,
    to: peer.id,
    handleId: inbound.handleId,
    slug: self.slug,
    status: "completed",
    text: trimmed,
  });
  appendProtocol(request.computerRoot, {
    type: "turn.end",
    from: inbound.from,
    to: inbound.to,
    handleId: inbound.handleId,
    slug: self.slug,
    status: "completed",
    text: trimmed,
  });
  const updated = transitionHandle(request.computerRoot, inbound.to, inbound.handleId, "completed", {
    result: trimmed,
    seq: event.seq,
  });
  appendTranscript(request.computerRoot, self.id, {
    seq: event.seq,
    t: event.t,
    kind: "handoff.done",
    text: `${self.slug} replied to ${peer.slug} on handle ${inbound.handleId}`.slice(0, 500),
    handleId: inbound.handleId,
    from: self.id,
    to: peer.id,
  });
  appendTranscript(request.computerRoot, peer.id, {
    seq: event.seq,
    t: event.t,
    kind: "handoff.done",
    text: `${self.slug} replied to ${peer.slug} on handle ${inbound.handleId}`.slice(0, 500),
    handleId: inbound.handleId,
    from: self.id,
    to: peer.id,
  });
  return {
    accepted: true,
    handleId: inbound.handleId,
    status: updated.status,
    done: true,
    result: trimmed,
  };
}

/**
 * ask_bot: reply if this turn is a peer wake from that Bot, otherwise send and wait.
 */
export async function sendBotMessage(request: AskPeerRequest): Promise<AskPeerResult> {
  const roster = loadRoster(request.computerRoot);
  const self = findBot(roster, request.from);
  const peer = findBot(roster, request.to);
  if (!self || !peer) {
    return { accepted: false, reason: "unknown bot" };
  }
  if (self.id === peer.id) {
    return { accepted: false, reason: "cannot message self" };
  }
  const inbound = request.inbound;
  if (inbound && inbound.kind === "a2a_handoff") {
    const sender = findBot(roster, inbound.from);
    if (sender && sender.id === peer.id) {
      return replyPeerMessage({
        computerRoot: request.computerRoot,
        fromId: self.id,
        inbound,
        text: request.prompt,
      });
    }
  }
  return askPeer(request);
}

export async function tryOperatorAskHandoff(
  computerRoot: string,
  fromKey: string,
  item: InboxItem,
  timeoutMs = 90_000,
): Promise<TurnResult | undefined> {
  if (item.kind !== "user_dm") {
    return undefined;
  }
  const roster = loadRoster(computerRoot);
  const parsed = parseAskPeer(item.prompt, roster, fromKey);
  if (!parsed) {
    return undefined;
  }
  const answered = await askPeer({
    computerRoot,
    from: fromKey,
    to: parsed.slug,
    prompt: parsed.question,
    timeoutMs,
  });
  const peerText = answered.result?.trim() || answered.error || answered.reason || "peer did not answer";
  return { text: peerText, paths: item.paths };
}

export async function executeFakeTurn(
  computerRoot: string,
  slug: string,
  item: InboxItem,
  timeoutMs = 8_000,
): Promise<TurnResult> {
  const handed = await tryOperatorAskHandoff(computerRoot, slug, item, timeoutMs);
  if (handed) {
    return handed;
  }
  const text = `[${slug}] ${item.prompt}`.slice(0, 500);
  if (item.kind === "a2a_handoff") {
    const roster = loadRoster(computerRoot);
    const self = findBot(roster, slug);
    if (self) {
      replyPeerMessage({
        computerRoot,
        fromId: self.id,
        inbound: item,
        text,
      });
    }
  }
  return { text, paths: item.paths };
}

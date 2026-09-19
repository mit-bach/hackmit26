import { appendInbox } from "./inbox.ts";
import { newHandleId, newInboxId, nowIso } from "./ids.ts";
import { isLaneBusy, liveStatus } from "./lane-state.ts";
import { writeHandle } from "./handle.ts";
import { appendProtocol } from "./protocol-log.ts";
import { findBot, loadRoster } from "./roster.ts";
import { appendTranscript } from "./transcript.ts";
import type {
  Conversation,
  HandleRecord,
  InboxItem,
  MessageKind,
  SendRequest,
  SendResult,
} from "./types.ts";

function conversationFor(request: SendRequest, fromId: string, toId: string): Conversation {
  if (request.conversation) {
    return request.conversation;
  }
  if (fromId === "operator") {
    return { kind: "operator_dm", botId: toId };
  }
  return { kind: "peer_dm", fromId, toId };
}

export function sendPrompt(request: SendRequest): SendResult {
  if (request.mode === "blocking") {
    return { accepted: false, reason: "blocking forbidden" };
  }
  const roster = loadRoster(request.computerRoot);
  const target = findBot(roster, request.to);
  if (!target) {
    return { accepted: false, reason: "unknown" };
  }
  const fromBot =
    request.from === "operator" || request.from === "harness"
      ? undefined
      : findBot(roster, request.from);
  const fromId = fromBot?.id ?? request.from;
  const kind: MessageKind =
    request.kind ?? (fromId === "operator" ? "user_dm" : "a2a_handoff");
  const onBusy =
    request.onBusy ?? (kind === "user_dm" || kind === "user_stop" ? "supersede" : "queue");
  if (onBusy === "reject" && isLaneBusy(request.computerRoot, target.id)) {
    return { accepted: false, reason: "busy" };
  }

  const handleId = newHandleId();
  const conversation = conversationFor(request, fromId, target.id);
  const createdAt = nowIso();
  const handle: HandleRecord = {
    id: handleId,
    from: fromId,
    to: target.id,
    toSlug: target.slug,
    prompt: request.prompt,
    paths: request.paths ?? [],
    conversation,
    kind,
    status: "accepted",
    createdAt,
    updatedAt: createdAt,
  };
  writeHandle(request.computerRoot, target.id, handle);

  const item: InboxItem = {
    id: newInboxId(),
    handleId,
    kind,
    from: fromId,
    to: target.id,
    conversation,
    prompt: request.prompt,
    paths: request.paths ?? [],
    mentions: request.mentions ?? [],
    createdAt,
    status: "pending",
  };
  appendInbox(request.computerRoot, target.id, item);

  const acceptedEvent = appendProtocol(request.computerRoot, {
    type: "send.accepted",
    from: fromId,
    to: target.id,
    handleId,
    slug: target.slug,
    text: request.prompt,
    paths: request.paths,
    status: "accepted",
  });

  if (fromBot) {
    appendTranscript(request.computerRoot, fromBot.id, {
      seq: acceptedEvent.seq,
      t: acceptedEvent.t,
      kind: "handoff.sent",
      text: `handed to ${target.slug}, handle ${handleId}`,
      handleId,
      from: fromId,
      to: target.id,
    });
  }

  const live = liveStatus(request.computerRoot, target.id);
  if (live === "running" || live === "blocked") {
    appendProtocol(request.computerRoot, {
      type: "send.queued",
      from: fromId,
      to: target.id,
      handleId,
      slug: target.slug,
      status: "queued",
    });
  } else if (live === "idle") {
    appendProtocol(request.computerRoot, {
      type: "poke",
      from: fromId,
      to: target.id,
      handleId,
      slug: target.slug,
    });
  }

  if (request.mode === "fire_and_forget") {
    return {
      accepted: true,
      botId: target.id,
      slug: target.slug,
      status: "accepted",
    };
  }

  return {
    accepted: true,
    handleId,
    botId: target.id,
    slug: target.slug,
    status: "accepted",
  };
}

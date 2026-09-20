import { existsSync, watch, writeFileSync, type FSWatcher } from "node:fs";
import { dirname, join } from "node:path";

import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { isToolCallEventType } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

import {
  createApproval,
  isConsequential,
  resolveApproval,
  waitForApproval,
} from "../src/approvals.ts";
import { sendBotMessage } from "../src/ask-peer.ts";
import { awaitTurn } from "../src/await.ts";
import { resolveBind, type BindResult } from "../src/bind.ts";
import { findHandle, listHandles } from "../src/handle.ts";
import { inboxPath } from "../src/paths.ts";
import {
  bindLane,
  cancelTurn,
  completeTurn,
  formatWake,
  interruptIfStop,
  noteBusyQueue,
  preemptPeerForUser,
  startNextTurn,
  blockTurn,
  resumeTurn,
  type BoundLane,
} from "../src/lane.ts";
import { readMemoryFile, writeMemoryFile } from "../src/memory.ts";
import { identityBlock, memorySection, recentWorkSection } from "../src/prompt.ts";
import { persistProtocolCard, PROTOCOL_CARD } from "../src/protocol-card.ts";
import { appendProtocol, searchProtocol } from "../src/protocol-log.ts";
import { fireRoutine } from "../src/routines.ts";
import { readRoomLog, roomPost } from "../src/rooms.ts";
import { findBot } from "../src/roster.ts";
import { searchAgents } from "../src/search.ts";
import { sendPrompt } from "../src/send.ts";
import { liveStatus, touchLane } from "../src/lane-state.ts";
import { transcriptTail } from "../src/transcript-tail.ts";
import { acquireLease, releaseLease } from "../src/leases.ts";
import { harnessPackageRoot } from "../src/pkg.ts";
import { notifyIntercept } from "../src/intercept.ts";

interface BoundSession {
  readonly bind: Extract<BindResult, { ok: true }>;
  readonly lane: BoundLane;
  readonly pi: ExtensionAPI;
}

function showNote(
  pi: ExtensionAPI,
  ctx: {
    ui: {
      notify: (message: string, level?: "info" | "warning" | "error") => void;
      setStatus: (key: string, text: string | undefined) => void;
    };
  },
  text: string,
  level: "info" | "warning" | "error" = "info",
  computerRoot?: string,
  slug?: string,
): void {
  ctx.ui.notify(text, level);
  ctx.ui.setStatus("note", text.replace(/\s+/g, " ").slice(0, 160));
  if (computerRoot) {
    writeFileSync(join(computerRoot, "harness", "last-note.txt"), `${slug ?? "unbound"}\n${text}\n`);
    appendProtocol(computerRoot, {
      type: "note",
      from: slug,
      slug,
      text,
      status: level,
    });
  }
  pi.sendMessage(
    {
      customType: "harness-note",
      content: text,
      display: true,
      details: { text },
    },
    { triggerTurn: false },
  );
}

function toolText(payload: unknown): {
  content: Array<{ type: "text"; text: string }>;
  details: unknown;
} {
  return {
    content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
    details: payload,
  };
}

function kickWake(session: BoundSession): void {
  void kickWakeAsync(session);
}

async function kickWakeAsync(session: BoundSession): Promise<void> {
  if (session.lane.drainLock) {
    return;
  }
  try {
    interruptIfStop(session.lane);
    const item = startNextTurn(session.lane);
    if (!item) {
      return;
    }
    session.pi.sendUserMessage(formatWake(item, session.bind.roster, session.bind.bot.slug), {
      deliverAs: "followUp",
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    process.stderr.write(`harness kickWake ${session.bind.bot.slug}: ${message}\n`);
  }
}

export default function harnessExtension(pi: ExtensionAPI): void {
  const bind = resolveBind(process.cwd());

  pi.on("project_trust", () => {
    if (process.env.HARNESS_BOT) {
      return { trusted: "yes" as const, remember: true };
    }
    return { trusted: "undecided" as const };
  });

  pi.registerCommand("bot", {
    description: "Show this process's bound Bot",
    handler: async (_args, ctx): Promise<void> => {
      if (!bind.ok) {
        showNote(pi, ctx, `unbound (${bind.reason})`, "warning", bind.computerRoot);
        return;
      }
      showNote(
        pi,
        ctx,
        `${bind.bot.slug} ${bind.bot.id} ${liveStatus(bind.computerRoot, bind.bot.id)}`,
        "info",
        bind.computerRoot,
        bind.bot.slug,
      );
    },
  });

  pi.registerCommand("whoami", {
    description: "Show this process's bound Bot (alias of /bot)",
    handler: async (_args, ctx): Promise<void> => {
      if (!bind.ok) {
        showNote(pi, ctx, `unbound (${bind.reason})`, "warning", bind.computerRoot);
        return;
      }
      showNote(
        pi,
        ctx,
        `${bind.bot.slug} ${bind.bot.id} ${liveStatus(bind.computerRoot, bind.bot.id)}`,
        "info",
        bind.computerRoot,
        bind.bot.slug,
      );
    },
  });

  if (!bind.ok) {
    return;
  }

  const lane = bindLane(bind.computerRoot, bind.bot);
  const session: BoundSession = { bind, lane, pi };
  let heartbeat: ReturnType<typeof setInterval> | undefined;
  let watcher: FSWatcher | undefined;
  let poll: ReturnType<typeof setInterval> | undefined;
  let lastAssistant = "";
  let lastError: string | undefined;

  pi.on("resources_discover", () => {
    const skillPaths = [`${harnessPackageRoot()}/skills`];
    const computerSkills = join(bind.computerRoot, "skills");
    if (process.env.HARNESS_CLIENT_SKILLS === "1") {
      for (const name of bind.bot.skills) {
        const dir = join(computerSkills, name);
        if (existsSync(join(dir, "SKILL.md"))) {
          skillPaths.push(dir);
        }
      }
    } else if (existsSync(computerSkills)) {
      skillPaths.push(computerSkills);
    }
    return { skillPaths };
  });

  pi.on("session_start", (_event, ctx) => {
    persistProtocolCard(bind.computerRoot, bind.bot.id);
    ctx.ui.setStatus("harness", `bot:${bind.bot.slug}`);
    heartbeat = setInterval(() => {
      const busy = lane.currentInbox !== undefined;
      const blocked =
        busy &&
        findHandle(bind.computerRoot, lane.currentInbox?.handleId ?? "")?.status === "blocked";
      touchLane(
        bind.computerRoot,
        bind.bot.id,
        bind.bot.slug,
        blocked ? "blocked" : busy ? "running" : "idle",
        lane.currentInbox?.handleId,
      );
    }, 2000);
    try {
      watcher = watch(dirname(inboxPath(bind.computerRoot, bind.bot.id)), () => {
        if (ctx.isIdle()) {
          kickWake(session);
        } else {
          noteBusyQueue(lane);
        }
      });
    } catch {
      watcher = undefined;
    }
    poll = setInterval(() => {
      interruptIfStop(lane);
      if (ctx.isIdle()) {
        kickWake(session);
      } else {
        noteBusyQueue(lane);
      }
    }, 1000);
    kickWake(session);
  });

  pi.on("session_shutdown", () => {
    if (heartbeat) {
      clearInterval(heartbeat);
    }
    if (poll) {
      clearInterval(poll);
    }
    watcher?.close();
  });

  pi.on("before_agent_start", (event) => {
    const extra = [
      identityBlock(bind.bot, bind.roster),
      PROTOCOL_CARD,
      memorySection(bind.computerRoot, bind.bot.id),
      recentWorkSection(bind.computerRoot, bind.bot.id),
    ]
      .filter((block) => block.length > 0)
      .join("\n\n");
    return { systemPrompt: `${event.systemPrompt}\n\n${extra}` };
  });

  pi.on("agent_end", (event) => {
    lastAssistant = assistantTextFromMessages(event.messages) ?? lastAssistant;
    lastError = assistantErrorFromMessages(event.messages) ?? lastError;
  });

  pi.on("input", (event) => {
    if (event.source !== "interactive" && event.source !== "rpc") {
      return { action: "continue" as const };
    }
    if (event.text.startsWith("/")) {
      return { action: "continue" as const };
    }
    if (event.text.startsWith("[harness wake]")) {
      return { action: "continue" as const };
    }
    if (/^stop now\.?$/i.test(event.text.trim())) {
      cancelTurn(lane, "operator stop");
      return { action: "handled" as const };
    }
    preemptPeerForUser(lane);
    return { action: "continue" as const };
  });

  pi.on("agent_settled", () => {
    if (!lane.currentInbox) {
      kickWake(session);
      return;
    }
    const handle = findHandle(bind.computerRoot, lane.currentInbox.handleId);
    if (handle?.status === "blocked") {
      return;
    }
    const text =
      lastAssistant.trim().length > 0
        ? lastAssistant
        : (lastError ?? "Pi finished this turn with no assistant text");
    completeTurn(lane, {
      text,
      paths: [],
      error: lastAssistant.trim().length > 0 ? undefined : lastError,
    });
    lastAssistant = "";
    lastError = undefined;
    kickWake(session);
  });

  pi.on("tool_call", async (event, ctx) => {
    const input: unknown = event.input;
    if (isToolCallEventType("write", event) || isToolCallEventType("edit", event)) {
      const path = typeof event.input.path === "string" ? event.input.path : "";
      if (path.length > 0 && !acquireLease(bind.computerRoot, path, bind.bot.id)) {
        return { block: true, reason: "another Bot holds a lease on this path" };
      }
    }
    if (!isConsequential(event.toolName, input, bind.bot.approvalLevel)) {
      return;
    }
    const approval = createApproval(bind.computerRoot, {
      botId: bind.bot.id,
      handleId: lane.currentInbox?.handleId,
      toolName: event.toolName,
      detail: JSON.stringify(input),
    });
    notifyIntercept(bind.computerRoot, approval);
    blockTurn(lane, `${event.toolName} requires Operator approval ${approval.id}`);
    let allowed = false;
    try {
      if (ctx.mode === "tui" && ctx.hasUI) {
        allowed = await ctx.ui.confirm("Harness approval", `${event.toolName}\n${approval.detail}`);
        resolveApproval(bind.computerRoot, approval.id, allowed);
      } else {
        const decided = await waitForApproval(bind.computerRoot, approval.id);
        allowed = decided.status === "allowed";
      }
    } catch {
      allowed = false;
      resolveApproval(bind.computerRoot, approval.id, false);
    }
    if (!allowed) {
      cancelTurn(lane, `denied by Operator (${approval.id})`);
      return { block: true, reason: `denied by Operator (${approval.id})`, terminate: true };
    }
    resumeTurn(lane);
    return;
  });

  pi.on("tool_result", (event) => {
    if (event.toolName === "write" || event.toolName === "edit") {
      const path = typeof event.input.path === "string" ? event.input.path : "";
      if (path.length > 0) {
        releaseLease(bind.computerRoot, path, bind.bot.id);
      }
    }
  });

  registerTools(pi, session);
  registerCommands(pi, session);
}

function assistantTextFromMessages(messages: readonly unknown[]): string | undefined {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const rec = asRecord(messages[i]);
    if (!rec || rec.role !== "assistant") {
      continue;
    }
    const content = rec.content;
    if (typeof content === "string" && content.trim().length > 0) {
      return content;
    }
    if (!Array.isArray(content)) {
      continue;
    }
    const parts: string[] = [];
    const thinking: string[] = [];
    for (const part of content) {
      const typed = asRecord(part);
      if (!typed) {
        continue;
      }
      if ((typed.type === "text" || typed.type === "output_text") && typeof typed.text === "string" && typed.text.trim().length > 0) {
        parts.push(typed.text);
      }
      if (typed.type === "thinking") {
        const thought = typeof typed.thinking === "string" ? typed.thinking : typeof typed.text === "string" ? typed.text : "";
        if (thought.trim().length > 0) {
          thinking.push(thought);
        }
      }
    }
    if (parts.length > 0) {
      return parts.join("\n");
    }
    if (thinking.length > 0) {
      return thinking.join("\n");
    }
  }
  return undefined;
}

function assistantErrorFromMessages(messages: readonly unknown[]): string | undefined {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const rec = asRecord(messages[i]);
    if (!rec || rec.role !== "assistant") {
      continue;
    }
    if (typeof rec.errorMessage === "string" && rec.errorMessage.trim().length > 0) {
      return rec.errorMessage;
    }
    if (rec.stopReason === "error" && typeof rec.error === "string" && rec.error.trim().length > 0) {
      return rec.error;
    }
  }
  return undefined;
}

function asRecord(value: unknown): Record<string, unknown> | undefined {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return undefined;
  }
  return value as Record<string, unknown>;
}

function registerTools(pi: ExtensionAPI, session: BoundSession): void {
  const { bind, lane } = session;

  pi.registerTool({
    name: "bot_search_agents",
    label: "Search Bots",
    description: "Search the Roster by name, slug, or purpose. Optional live status filter.",
    promptSnippet: "Find named Bots on this Client system",
    promptGuidelines: [
      "Use bot_search_agents to find a standing Bot by purpose. It returns Roster ids and live status, never child ids.",
    ],
    parameters: Type.Object({
      query: Type.String({ description: "Substring over name, slug, purpose" }),
      status: Type.Optional(Type.String({ description: "offline | idle | running | blocked" })),
    }),
    execute: async (_id, params) => {
      const status =
        params.status === "offline" ||
        params.status === "idle" ||
        params.status === "running" ||
        params.status === "blocked"
          ? params.status
          : undefined;
      return toolText(searchAgents(bind.computerRoot, params.query, status));
    },
  });

  pi.registerTool({
    name: "bot_get_profile",
    label: "Bot profile",
    description: "Return one Bot record from the Roster.",
    promptSnippet: "Look up a teammate by slug, id, or name before you talk to them",
    promptGuidelines: [
      "bot_get_profile is always registered. Use it to confirm a teammate exists, then call bot_ask.",
    ],
    parameters: Type.Object({
      bot_id: Type.String({ description: "Bot id, slug, or name" }),
    }),
    execute: async (_id, params) => {
      const bot = findBot(bind.roster, params.bot_id);
      if (!bot) {
        return toolText({ error: "unknown bot" });
      }
      return toolText({ ...bot, status: liveStatus(bind.computerRoot, bot.id) });
    },
  });

  const askParams = Type.Object({
    bot_id: Type.String({ description: "Teammate slug, id, or name" }),
    prompt: Type.String({ description: "Question or task for that Bot" }),
  });
  const runAsk = async (
    _id: string,
    params: { bot_id: string; prompt: string },
  ): Promise<{ content: Array<{ type: "text"; text: string }>; details: unknown }> =>
    toolText(
      await sendBotMessage({
        computerRoot: bind.computerRoot,
        from: bind.bot.id,
        to: params.bot_id,
        prompt: params.prompt,
        timeoutMs: 120_000,
        inbound: lane.currentInbox,
      }),
    );

  pi.registerTool({
    name: "ask_bot",
    label: "Ask a Bot",
    description:
      "Send or reply to another Bot. This is the only way words enter the pair thread. If a teammate woke you, call this back to them with your answer. That completes their wait. Assistant text is not the thread and is not the Operator.",
    promptSnippet: "Send or reply in the pair thread, then tell the Operator what they said",
    promptGuidelines: [
      "ask_bot posts in the pair thread. Call it to send. Call it back to reply. Then tell the Operator with assistant text. Never say this tool is missing.",
    ],
    parameters: askParams,
    execute: runAsk,
  });

  pi.registerTool({
    name: "bot_ask",
    label: "Ask a Bot",
    description:
      "Same as ask_bot: send or reply in the pair thread. If a teammate woke you, call this back to them. Always registered.",
    promptSnippet: "Send or reply in the pair thread",
    promptGuidelines: [
      "bot_ask is the Harness name for ask_bot. Use either. Do not claim it is disabled. A peer wake requires you to call this back.",
    ],
    parameters: askParams,
    execute: runAsk,
  });

  pi.registerTool({
    name: "message_operator",
    label: "Message Operator",
    description:
      "Send a message to the Operator. Use this during a peer wake when the Operator should hear you. During Operator DM, assistant text already goes to the Operator.",
    promptSnippet: "Tell the Operator something without posting in a Bot thread",
    promptGuidelines: [
      "message_operator is for the Operator. It does not enter a pair thread. During a peer wake, assistant text is not the Operator — call this instead.",
    ],
    parameters: Type.Object({
      text: Type.String({ description: "What the Operator should read" }),
    }),
    execute: async (_id, params) => {
      const text = params.text.trim();
      appendProtocol(bind.computerRoot, {
        type: "operator.message",
        from: bind.bot.id,
        to: "operator",
        handleId: lane.currentInbox?.handleId,
        slug: bind.bot.slug,
        text,
      });
      return toolText({ ok: true, to: "operator", text });
    },
  });

  pi.registerTool({
    name: "bot_send_prompt",
    label: "Send to Bot",
    description: "Accept work onto another Bot's inbox. Returns a Handle, not a result.",
    promptSnippet: "Hand work to another Bot asynchronously, then call bot_await_turn",
    promptGuidelines: [
      "Use bot_send_prompt to hand work to another Bot. The JSON is a Handle (accepted), not a result. Call bot_await_turn to learn if it finished. Prefer ask_bot when you need the peer's answer in this turn.",
    ],
    parameters: Type.Object({
      bot_id: Type.String(),
      prompt: Type.String(),
      mode: Type.Optional(Type.String({ description: "async | fire_and_forget. blocking is refused." })),
      on_busy: Type.Optional(Type.String({ description: "queue | reject. Default queue." })),
      paths: Type.Optional(Type.Array(Type.String())),
    }),
    execute: async (_id, params) => {
      const mode = params.mode === "fire_and_forget" || params.mode === "blocking" ? params.mode : "async";
      const onBusy = params.on_busy === "reject" || params.on_busy === "supersede" ? params.on_busy : "queue";
      return toolText(
        sendPrompt({
          computerRoot: bind.computerRoot,
          from: bind.bot.id,
          to: params.bot_id,
          prompt: params.prompt,
          mode,
          onBusy,
          paths: params.paths,
        }),
      );
    },
  });

  pi.registerTool({
    name: "bot_await_turn",
    label: "Await Handle",
    description: "Watch a Handle file until the receiver's turn ends or parks on the Operator.",
    promptSnippet: "Wait until a teammate's Handle is done",
    promptGuidelines: [
      "Use bot_await_turn on a handle_id from bot_send_prompt. done is true only for completed, failed, or cancelled. blocked is not done.",
    ],
    parameters: Type.Object({
      handle_id: Type.String(),
    }),
    execute: async (_id, params) =>
      toolText(await awaitTurn(bind.computerRoot, params.handle_id, { timeoutMs: 120_000 })),
  });

  pi.registerTool({
    name: "bot_get_agent_transcript_tail",
    label: "Transcript tail",
    description: "Tail protocol + this or another Bot's transcript by seq.",
    promptSnippet: "Read recent protocol or a teammate transcript tail",
    parameters: Type.Object({
      bot_id: Type.String(),
      limit: Type.Optional(Type.Number()),
      before_seq: Type.Optional(Type.Number()),
      query: Type.Optional(Type.String()),
    }),
    execute: async (_id, params) => {
      const bot = findBot(bind.roster, params.bot_id);
      if (!bot) {
        return toolText({ error: "unknown bot" });
      }
      if (params.query && params.query.length > 0) {
        return toolText(searchProtocol(bind.computerRoot, params.query, bot.id));
      }
      return toolText(transcriptTail(bind.computerRoot, bot.id, params.limit ?? 20, params.before_seq));
    },
  });

  pi.registerTool({
    name: "room_post",
    label: "Room post",
    description: "Append to a Room log. The Host wakes members in roster order.",
    promptSnippet: "Post to a Room so the Host wakes members in roster order",
    parameters: Type.Object({
      room_id: Type.String(),
      text: Type.String(),
    }),
    execute: async (_id, params) =>
      toolText(
        await roomPost({
          computerRoot: bind.computerRoot,
          roomId: params.room_id,
          from: bind.bot.id,
          text: params.text,
        }),
      ),
  });

  pi.registerTool({
    name: "room_read_log",
    label: "Room log",
    description: "Read a Room log.",
    promptSnippet: "Read what was said in a Room",
    parameters: Type.Object({
      room_id: Type.String(),
    }),
    execute: async (_id, params) => toolText(readRoomLog(bind.computerRoot, params.room_id)),
  });

  pi.registerTool({
    name: "memory_read",
    label: "Read Memory",
    description: "Read this Bot's Memory tree. Cannot read another Bot.",
    promptSnippet: "Read this Bot's Memory only",
    parameters: Type.Object({
      path: Type.Optional(Type.String({ description: "Relative to this Bot's memory/. Default MEMORY.md" })),
    }),
    execute: async (_id, params) =>
      toolText({
        path: params.path ?? "MEMORY.md",
        content: readMemoryFile(bind.computerRoot, bind.bot.id, params.path ?? "MEMORY.md"),
      }),
  });

  pi.registerTool({
    name: "memory_write",
    label: "Write Memory",
    description: "Write this Bot's Memory tree. Secrets are redacted. Writes are atomic.",
    promptSnippet: "Write this Bot's Memory only",
    parameters: Type.Object({
      path: Type.String(),
      content: Type.String(),
    }),
    execute: async (_id, params) => {
      writeMemoryFile(bind.computerRoot, bind.bot.id, params.path, params.content);
      return toolText({ ok: true, path: params.path });
    },
  });

  pi.registerTool({
    name: "bot_resolve_approval",
    label: "Resolve approval",
    description: "Allow or deny a parked approval. Used by a Verifier Bot named in harness/intercept.json.",
    promptSnippet: "Allow or deny a parked Operator approval",
    parameters: Type.Object({
      approval_id: Type.String(),
      allowed: Type.Boolean(),
    }),
    execute: async (_id, params) =>
      toolText(resolveApproval(bind.computerRoot, params.approval_id, params.allowed)),
  });

  pi.registerTool({
    name: "ask_user",
    label: "Ask Operator",
    description: "Ask the Operator. A peer Handle is not approval.",
    promptSnippet: "Ask the Operator; a peer Handle is not approval",
    parameters: Type.Object({
      action: Type.String(),
      detail: Type.String(),
    }),
    execute: async (_id, params, _signal, _update, ctx: ExtensionContext) => {
      const approval = createApproval(bind.computerRoot, {
        botId: bind.bot.id,
        handleId: lane.currentInbox?.handleId,
        toolName: "ask_user",
        detail: `${params.action}: ${params.detail}`,
      });
      notifyIntercept(bind.computerRoot, approval);
      blockTurn(lane, params.action);
      let allowed = false;
      try {
        if (ctx.mode === "tui" && ctx.hasUI) {
          allowed = await ctx.ui.confirm("Harness approval", `${params.action}\n${params.detail}`);
          resolveApproval(bind.computerRoot, approval.id, allowed);
        } else {
          const decided = await waitForApproval(bind.computerRoot, approval.id);
          allowed = decided.status === "allowed";
        }
      } catch {
        allowed = false;
        resolveApproval(bind.computerRoot, approval.id, false);
      }
      if (allowed) {
        resumeTurn(lane);
      } else {
        cancelTurn(lane, `denied by Operator (${approval.id})`);
      }
      return toolText({ allowed, action: params.action, detail: params.detail, approvalId: approval.id });
    },
  });
}

function registerCommands(pi: ExtensionAPI, session: BoundSession): void {
  const { bind, lane } = session;

  pi.registerCommand("roster", {
    description: "Print Bots and live status",
    handler: async (_args, ctx): Promise<void> => {
      const hits = searchAgents(bind.computerRoot, "");
      const line = hits.map((hit) => `${hit.slug}:${hit.status}`).join(", ");
      showNote(pi, ctx, line, "info", bind.computerRoot, bind.bot.slug);
    },
  });

  pi.registerCommand("handles", {
    description: "Open Handles for this Bot",
    handler: async (_args, ctx): Promise<void> => {
      const rows = listHandles(bind.computerRoot, bind.bot.id);
      const line =
        rows.length === 0
          ? "no handles"
          : rows.map((row) => `${row.id} ${row.status}`).join(" | ");
      showNote(pi, ctx, line, "info", bind.computerRoot, bind.bot.slug);
    },
  });

  pi.registerCommand("room", {
    description: "Show Roster rooms this Bot belongs to",
    handler: async (_args, ctx): Promise<void> => {
      const rooms = bind.roster.rooms.filter((room) => room.members.includes(bind.bot.slug));
      showNote(
        pi,
        ctx,
        rooms.length === 0 ? "no rooms" : rooms.map((room) => `${room.id}:${room.members.join(",")}`).join(" | "),
        "info",
        bind.computerRoot,
        bind.bot.slug,
      );
    },
  });

  pi.registerCommand("stop", {
    description: "End the current turn. Does not undo finished work.",
    handler: async (_args, ctx): Promise<void> => {
      cancelTurn(lane, "operator stop");
      showNote(pi, ctx, "stopped", "info", bind.computerRoot, bind.bot.slug);
    },
  });

  pi.registerCommand("protocol", {
    description: "Show recent protocol events for this Bot",
    handler: async (_args, ctx): Promise<void> => {
      const rows = searchProtocol(bind.computerRoot, "", bind.bot.id).slice(-8);
      const line =
        rows.length === 0
          ? "no protocol yet"
          : rows.map((row) => `${row.seq} ${row.type} ${row.handleId ?? ""}`).join(" | ");
      showNote(pi, ctx, line, "info", bind.computerRoot, bind.bot.slug);
    },
  });

  pi.registerCommand("routine", {
    description: "Fire a Routine onto its owning Bot's inbox: /routine run <name>",
    handler: async (args, ctx): Promise<void> => {
      const trimmed = args.trim();
      const match = /^run\s+(.+)$/.exec(trimmed);
      const name = match?.[1] ?? trimmed;
      if (name.length === 0) {
        showNote(pi, ctx, "usage: /routine run <name>", "warning", bind.computerRoot, bind.bot.slug);
        return;
      }
      try {
        const receipt = fireRoutine(bind.computerRoot, name);
        showNote(pi, ctx, `routine ${receipt.name} → ${receipt.bot} ${receipt.handleId ?? ""}`, "info", bind.computerRoot, bind.bot.slug);
        if (ctx.isIdle()) {
          kickWake(session);
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        showNote(pi, ctx, message, "error", bind.computerRoot, bind.bot.slug);
      }
    },
  });
}

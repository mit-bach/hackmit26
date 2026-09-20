import { listApprovals, readApproval, resolveApproval } from "../approvals.ts";
import { awaitTurn } from "../await.ts";
import { loadExtensionsManifest } from "../client-attach.ts";
import { loadClientRuntime, overlayOperatorConfig } from "../client-runtime.ts";
import { initComputer } from "../computer.ts";
import { findHandle, listHandles } from "../handle.ts";
import { listInbox, pendingCount } from "../inbox.ts";
import { loadIntercept } from "../intercept.ts";
import { liveStatus, readLane } from "../lane-state.ts";
import { readMemoryFile } from "../memory.ts";
import { piSessionDir } from "../paths.ts";
import { readProtocol, searchProtocol } from "../protocol-log.ts";
import { findBot, findRoom, loadRoster, saveRoster } from "../roster.ts";
import { readRoomLog, roomPost } from "../rooms.ts";
import { fireRoutine, listReceipts } from "../routines.ts";
import { sendPrompt } from "../send.ts";
import type { SidecarHandle } from "../sidecar.ts";
import { transcriptTail } from "../transcript-tail.ts";
import type { ApprovalLevel, BotRecord, ProtocolEvent, Roster } from "../types.ts";
import { wipeRuntime } from "../wipe.ts";
import type { EventBus } from "./bus.ts";
import { listComputerTree, readComputerFile, writeComputerFile } from "./computer-tree.ts";
import { loadOperatorConfig, publicOperatorConfig } from "./operator-config.ts";
import type { Supervisor } from "./supervisor.ts";

const BOT_COLORS = ["teal", "amber", "violet", "rose", "sky", "lime"] as const;

export interface OperatorBot {
  readonly id: string;
  readonly slug: string;
  readonly name: string;
  readonly purpose: string;
  readonly instructions: string;
  readonly approvalLevel: ApprovalLevel;
  readonly skills: readonly string[];
  readonly status: string;
  readonly pending: number;
  readonly busy: boolean;
  readonly color: string;
  readonly threadId: string;
}

export interface OperatorMessage {
  readonly id: string;
  readonly at: string;
  readonly role: "user" | "bot" | "system";
  readonly kind: "text" | "activity" | "options";
  readonly text: string;
  readonly handleId?: string;
  readonly from?: string;
  readonly to?: string;
  readonly card?: {
    readonly title: string;
    readonly subtitle: string;
    readonly options: readonly string[];
    readonly requestId: string;
    readonly tool?: string;
    readonly answered?: string;
  };
}

export interface OperatorSnapshot {
  readonly system: string;
  readonly description: string;
  readonly computerRoot: string;
  readonly fakeWorkers: boolean;
  readonly bots: readonly OperatorBot[];
  readonly rooms: readonly {
    readonly id: string;
    readonly title: string;
    readonly members: readonly string[];
    readonly threadId: string;
  }[];
  readonly routines: Roster["routines"];
  readonly approvals: ReturnType<typeof listApprovals>;
  readonly receipts: ReturnType<typeof listReceipts>;
  readonly config: ReturnType<typeof publicOperatorConfig>;
  readonly sessions: readonly { readonly slug: string; readonly pid?: number; readonly alive: boolean }[];
  readonly protocol: readonly ProtocolEvent[];
  readonly sidecar: { readonly port: number; readonly owned: boolean } | null;
}

function colorFor(index: number): string {
  return BOT_COLORS[index % BOT_COLORS.length] ?? "teal";
}

export function toOperatorBot(computerRoot: string, bot: BotRecord, index: number): OperatorBot {
  const status = liveStatus(computerRoot, bot.id);
  return {
    id: bot.id,
    slug: bot.slug,
    name: bot.name,
    purpose: bot.purpose,
    instructions: bot.instructions,
    approvalLevel: bot.approvalLevel,
    skills: bot.skills,
    status,
    pending: pendingCount(computerRoot, bot.id),
    busy: status === "running" || status === "blocked",
    color: colorFor(index),
    threadId: bot.id,
  };
}

export function messagesForBot(computerRoot: string, botId: string, limit = 200): OperatorMessage[] {
  const rows = transcriptTail(computerRoot, botId, limit);
  const messages: OperatorMessage[] = [];
  const seenUser = new Set<string>();
  for (const row of rows) {
    if (row.kind === "poke" || row.kind === "send.queued") {
      continue;
    }
    let role: OperatorMessage["role"] = "bot";
    let kind: OperatorMessage["kind"] = "text";
    let text = row.text;
    if (row.kind === "user_dm" || row.kind === "send.accepted") {
      role = "user";
      const key = `${row.handleId ?? ""}:${text}`;
      if (text.trim().length === 0 || seenUser.has(key)) {
        continue;
      }
      seenUser.add(key);
    } else if (row.kind === "turn.start") {
      role = "system";
      kind = "activity";
      text = "running";
    } else if (
      row.kind === "turn.end" ||
      row.kind === "result" ||
      row.kind === "send.completed" ||
      row.kind === "handoff.done"
    ) {
      role = "bot";
      const stripped = text.replace(/^[^\n]*finished handle \S+:\s*/i, "").replace(/^[^\n]*cancelled handle \S+:\s*/i, "");
      text = stripped.length > 0 ? stripped : text;
    } else if (row.kind === "handoff.sent") {
      continue;
    } else if (row.kind.startsWith("send.") || row.kind === "activity") {
      role = "system";
      kind = "activity";
      if (text.trim().length === 0) {
        continue;
      }
    } else if (row.from === "operator") {
      role = "user";
      if (text.trim().length === 0) {
        continue;
      }
    }
    if (text.trim().length === 0) {
      continue;
    }
    messages.push({
      id: `seq-${row.seq}`,
      at: row.t,
      role,
      kind,
      text,
      handleId: row.handleId,
      from: row.from,
      to: row.to,
    });
  }
  const pending = listApprovals(computerRoot).filter(
    (row) => row.botId === botId && row.status === "pending",
  );
  for (const approval of pending) {
    messages.push({
      id: approval.id,
      at: approval.createdAt,
      role: "bot",
      kind: "options",
      text: approval.detail,
      handleId: approval.handleId,
      card: {
        title: "Approval needed",
        subtitle: `${approval.toolName} · ${approval.detail.slice(0, 180)}`,
        options: ["Allow", "Deny"],
        requestId: approval.id,
        tool: approval.toolName,
      },
    });
  }
  return messages;
}

export function buildSnapshot(
  computerRoot: string,
  fakeWorkers: boolean,
  supervisor?: Supervisor,
  sidecar?: SidecarHandle,
): OperatorSnapshot {
  const roster = loadRoster(computerRoot);
  return {
    system: roster.system,
    description: roster.description,
    computerRoot,
    fakeWorkers,
    bots: roster.bots.map((bot, index) => toOperatorBot(computerRoot, bot, index)),
    rooms: roster.rooms.map((room) => ({
      id: room.id,
      title: room.title,
      members: room.members,
      threadId: `room:${room.id}`,
    })),
    routines: roster.routines,
    approvals: listApprovals(computerRoot),
    receipts: listReceipts(computerRoot),
    config: publicOperatorConfig(overlayOperatorConfig(computerRoot, loadOperatorConfig(), loadClientRuntime(computerRoot))),
    sessions: supervisor?.sessions() ?? [],
    protocol: readProtocol(computerRoot).slice(-120),
    sidecar: sidecar ? { port: sidecar.port, owned: sidecar.owned } : null,
  };
}

export interface ApiContext {
  readonly computerRoot: string;
  readonly fakeWorkers: boolean;
  readonly supervisor?: Supervisor;
  readonly bus?: EventBus;
  readonly sidecar?: SidecarHandle;
}

function snap(ctx: ApiContext): OperatorSnapshot {
  return buildSnapshot(ctx.computerRoot, ctx.fakeWorkers, ctx.supervisor, ctx.sidecar);
}

function emit(ctx: ApiContext, frame: { readonly kind: string; readonly [key: string]: unknown }): void {
  ctx.bus?.publish(frame);
}

function fail(error: unknown): { readonly status: number; readonly body: unknown } {
  const message = error instanceof Error ? error.message : String(error);
  const status = message === "path escape" || message === "not a file" || message === "not a text file" || message === "file too large" ? 400 : 500;
  return { status, body: { error: message } };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export async function handleOperatorApi(
  method: string,
  path: string,
  url: URL,
  body: unknown,
  ctx: ApiContext,
): Promise<{ readonly status: number; readonly body: unknown } | undefined> {
  const computerRoot = ctx.computerRoot;

  if (method === "GET" && path === "/api/snapshot") {
    return { status: 200, body: snap(ctx) };
  }

  if (method === "GET" && path === "/api/bots") {
    const roster = loadRoster(computerRoot);
    return {
      status: 200,
      body: roster.bots.map((bot, index) => toOperatorBot(computerRoot, bot, index)),
    };
  }

  const botMatch = /^\/api\/bots\/([^/]+)(\/.*)?$/.exec(path);
  if (botMatch) {
    const key = decodeURIComponent(botMatch[1] ?? "");
    const rest = botMatch[2] ?? "";
    const roster = loadRoster(computerRoot);
    const bot = findBot(roster, key);
    if (!bot) {
      return { status: 404, body: { error: "unknown" } };
    }
    const index = roster.bots.findIndex((row) => row.id === bot.id);
    if (method === "GET" && rest === "") {
      return {
        status: 200,
        body: {
          ...toOperatorBot(computerRoot, bot, index),
          lane: readLane(computerRoot, bot.id),
          handles: listHandles(computerRoot, bot.id),
          inbox: listInbox(computerRoot, bot.id),
          sessionDir: piSessionDir(computerRoot, bot.id),
        },
      };
    }
    if (method === "GET" && rest === "/messages") {
      const limit = Number(url.searchParams.get("limit") ?? "200");
      return { status: 200, body: messagesForBot(computerRoot, bot.id, Number.isFinite(limit) ? limit : 200) };
    }
    if (method === "POST" && rest === "/messages") {
      const text = isRecord(body) && typeof body.text === "string" ? body.text : "";
      if (text.length === 0) {
        return { status: 400, body: { error: "text required" } };
      }
      const sent = sendPrompt({
        computerRoot,
        from: "operator",
        to: bot.id,
        prompt: text,
        kind: "user_dm",
      });
      emit(ctx, { kind: "bot", bot: { ...toOperatorBot(computerRoot, bot, index), computer: "off" } });
      return { status: 200, body: sent };
    }
    if (method === "POST" && (rest === "/interrupt" || rest === "/stop")) {
      const stopped = sendPrompt({
        computerRoot,
        from: "operator",
        to: bot.id,
        prompt: "Stop now",
        kind: "user_stop",
        onBusy: "supersede",
      });
      emit(ctx, { kind: "bot", bot: { ...toOperatorBot(computerRoot, bot, index), computer: "off" } });
      return { status: 200, body: stopped };
    }
    if (method === "POST" && rest === "/spawn") {
      ctx.supervisor?.ensure(bot.slug);
      emit(ctx, { kind: "sessions", sessions: ctx.supervisor?.sessions() ?? [] });
      return { status: 200, body: { ok: true, slug: bot.slug } };
    }
    if (method === "POST" && rest === "/kill") {
      ctx.supervisor?.stopBot(bot.slug);
      emit(ctx, { kind: "sessions", sessions: ctx.supervisor?.sessions() ?? [] });
      return { status: 200, body: { ok: true, slug: bot.slug } };
    }
    if (method === "GET" && rest === "/memory") {
      const rel = url.searchParams.get("path") ?? "MEMORY.md";
      return { status: 200, body: { path: rel, content: readMemoryFile(computerRoot, bot.id, rel) } };
    }
    if (method === "PATCH" && rest === "") {
      if (!isRecord(body)) {
        return { status: 400, body: { error: "object required" } };
      }
      const nextBots = roster.bots.map((row) => {
        if (row.id !== bot.id) {
          return row;
        }
        const approval =
          body.approvalLevel === "ask" || body.approvalLevel === "always" || body.approvalLevel === "never"
            ? body.approvalLevel
            : row.approvalLevel;
        return {
          ...row,
          name: typeof body.name === "string" && body.name.length > 0 ? body.name : row.name,
          slug:
            typeof body.slug === "string" && body.slug.trim().length > 0
              ? body.slug.trim().toLowerCase().replace(/[^a-z0-9-]/g, "-")
              : row.slug,
          purpose: typeof body.purpose === "string" ? body.purpose : row.purpose,
          instructions: typeof body.instructions === "string" ? body.instructions : row.instructions,
          approvalLevel: approval,
          skills: Array.isArray(body.skills)
            ? body.skills.filter((item): item is string => typeof item === "string")
            : row.skills,
          connectors: Array.isArray(body.connectors)
            ? body.connectors.filter((item): item is string => typeof item === "string")
            : row.connectors,
        };
      });
      const next: Roster = { ...roster, bots: nextBots };
      saveRoster(computerRoot, next);
      initComputer(computerRoot, next);
      emit(ctx, { kind: "hello", snapshot: snap(ctx) });
      return { status: 200, body: findBot(next, bot.id) };
    }
  }

  if (method === "POST" && path === "/api/bots") {
    if (!isRecord(body) || typeof body.slug !== "string" || typeof body.name !== "string") {
      return { status: 400, body: { error: "slug and name required" } };
    }
    const slug = body.slug.trim().toLowerCase().replace(/[^a-z0-9-]/g, "-");
    const roster = loadRoster(computerRoot);
    if (findBot(roster, slug)) {
      return { status: 409, body: { error: "exists" } };
    }
    const created: BotRecord = {
      id: `bot_${slug}`,
      name: body.name,
      slug,
      purpose: typeof body.purpose === "string" ? body.purpose : "",
      instructions: typeof body.instructions === "string" ? body.instructions : "",
      skills: [],
      connectors: [],
      approvalLevel:
        body.approvalLevel === "always" || body.approvalLevel === "never" || body.approvalLevel === "ask"
          ? body.approvalLevel
          : "ask",
    };
    const next: Roster = { ...roster, bots: [...roster.bots, created] };
    saveRoster(computerRoot, next);
    initComputer(computerRoot, next);
    ctx.supervisor?.ensure(created.slug);
    emit(ctx, { kind: "hello", snapshot: snap(ctx) });
    return { status: 200, body: created };
  }

  if (method === "GET" && path === "/api/rooms") {
    const roster = loadRoster(computerRoot);
    return { status: 200, body: roster.rooms };
  }

  const roomMatch = /^\/api\/rooms\/([^/]+)(\/.*)?$/.exec(path);
  if (roomMatch) {
    const roomId = decodeURIComponent(roomMatch[1] ?? "");
    const rest = roomMatch[2] ?? "";
    const roster = loadRoster(computerRoot);
    const room = findRoom(roster, roomId);
    if (!room) {
      return { status: 404, body: { error: "unknown room" } };
    }
    if (method === "GET" && rest === "") {
      return { status: 200, body: { ...room, log: readRoomLog(computerRoot, roomId) } };
    }
    if (method === "POST" && (rest === "/messages" || rest === "/post")) {
      const text = isRecord(body) && typeof body.text === "string" ? body.text : "";
      if (text.length === 0) {
        return { status: 400, body: { error: "text required" } };
      }
      const posted = await roomPost({
        computerRoot,
        roomId,
        from: "operator",
        text,
        waitCapMs: ctx.fakeWorkers ? 400 : 60_000,
        awaitTimeoutMs: ctx.fakeWorkers ? 8_000 : 90_000,
      });
      emit(ctx, {
        kind: "room",
        roomId,
        log: readRoomLog(computerRoot, roomId),
      });
      return { status: 200, body: posted };
    }
  }

  if (method === "GET" && path === "/api/approvals") {
    return { status: 200, body: listApprovals(computerRoot) };
  }

  const approvalMatch = /^\/api\/approvals\/([^/]+)$/.exec(path);
  if (approvalMatch) {
    const id = decodeURIComponent(approvalMatch[1] ?? "");
    if (method === "GET") {
      const row = readApproval(computerRoot, id);
      return row ? { status: 200, body: row } : { status: 404, body: { error: "unknown approval" } };
    }
    if (method === "POST") {
      const allowed = isRecord(body) && body.allow === true;
      const resolved = resolveApproval(computerRoot, id, allowed);
      emit(ctx, { kind: "approvals", approvals: listApprovals(computerRoot) });
      return { status: 200, body: resolved };
    }
  }

  if (method === "GET" && path === "/api/routines") {
    return {
      status: 200,
      body: { routines: loadRoster(computerRoot).routines, receipts: listReceipts(computerRoot) },
    };
  }

  const routineMatch = /^\/api\/routines\/([^/]+)\/run$/.exec(path);
  if (routineMatch && method === "POST") {
    const name = decodeURIComponent(routineMatch[1] ?? "");
    const fired = fireRoutine(computerRoot, name);
    emit(ctx, { kind: "hello", snapshot: snap(ctx) });
    return { status: 200, body: fired };
  }

  if (method === "GET" && path === "/api/protocol") {
    const after = Number(url.searchParams.get("after") ?? "0");
    const query = url.searchParams.get("query") ?? "";
    const events =
      query.length > 0
        ? searchProtocol(computerRoot, query)
        : readProtocol(computerRoot, Number.isFinite(after) ? after : 0);
    return { status: 200, body: events };
  }

  if (method === "GET" && path === "/api/handles") {
    const roster = loadRoster(computerRoot);
    const slug = url.searchParams.get("bot");
    const bots = slug
      ? [findBot(roster, slug)].filter((row): row is BotRecord => row !== undefined)
      : [...roster.bots];
    return { status: 200, body: bots.flatMap((bot) => listHandles(computerRoot, bot.id)) };
  }

  const handleAwait = /^\/api\/handles\/([^/]+)\/await$/.exec(path);
  if (handleAwait && method === "POST") {
    const handleId = decodeURIComponent(handleAwait[1] ?? "");
    const timeoutMs = Number(url.searchParams.get("timeoutMs") ?? "30000");
    return { status: 200, body: await awaitTurn(computerRoot, handleId, { timeoutMs }) };
  }

  const handleGet = /^\/api\/handles\/([^/]+)$/.exec(path);
  if (handleGet && method === "GET") {
    const handleId = decodeURIComponent(handleGet[1] ?? "");
    const handle = findHandle(computerRoot, handleId);
    return handle ? { status: 200, body: handle } : { status: 404, body: { error: "unknown handle" } };
  }

  if (method === "GET" && path === "/api/computer/tree") {
    const from = url.searchParams.get("from") ?? "workspace";
    try {
      return { status: 200, body: listComputerTree(computerRoot, from) };
    } catch (error) {
      return fail(error);
    }
  }

  if (method === "GET" && path === "/api/computer/file") {
    const rel = url.searchParams.get("path") ?? "";
    if (rel.length === 0) {
      return { status: 400, body: { error: "path required" } };
    }
    try {
      return { status: 200, body: readComputerFile(computerRoot, rel) };
    } catch (error) {
      return fail(error);
    }
  }

  if ((method === "POST" || method === "PUT") && path === "/api/computer/file") {
    if (!isRecord(body) || typeof body.path !== "string" || typeof body.content !== "string") {
      return { status: 400, body: { error: "path and content required" } };
    }
    try {
      const written = writeComputerFile(computerRoot, body.path, body.content);
      emit(ctx, { kind: "tree", from: "workspace" });
      return { status: 200, body: written };
    } catch (error) {
      return fail(error);
    }
  }

  if (method === "GET" && path === "/api/sessions") {
    return { status: 200, body: ctx.supervisor?.sessions() ?? [] };
  }

  if (method === "GET" && path === "/api/office") {
    const roster = loadRoster(computerRoot);
    const client = loadClientRuntime(computerRoot);
    return {
      status: 200,
      body: {
        system: roster.system,
        computerRoot,
        bots: roster.bots.length,
        rooms: roster.rooms.length,
        routines: roster.routines.length,
        client: {
          extraExtensions: client.extraExtensions,
          clientSkills: client.clientSkills,
          spawnPolicy: client.spawnPolicy ?? null,
          autoRoutines: client.autoRoutines,
          provider: client.provider ?? null,
          model: client.model ?? null,
          thinkingLevel: client.thinkingLevel ?? null,
          features: client.features ?? null,
          evalPhase: client.evalPhase ?? null,
          sidecar: client.sidecar
            ? { command: client.sidecar.command, portFile: client.sidecar.portFile }
            : null,
        },
        attach: loadExtensionsManifest(computerRoot),
        intercept: loadIntercept(computerRoot),
        sidecar: ctx.sidecar ? { port: ctx.sidecar.port, owned: ctx.sidecar.owned } : null,
        fakeWorkers: ctx.fakeWorkers,
      },
    };
  }

  if (method === "POST" && path === "/api/wipe") {
    const keepMemory = isRecord(body) && body.keepMemory === true;
    const wipeRuns = isRecord(body) && body.wipeRuns === true;
    for (const session of ctx.supervisor?.sessions() ?? []) {
      if (session.alive) {
        ctx.supervisor?.stopBot(session.slug);
      }
    }
    const report = wipeRuntime(computerRoot, {
      keepMemory,
      keepSidecarPort: true,
      wipeRuns,
    });
    initComputer(computerRoot);
    emit(ctx, { kind: "hello", snapshot: snap(ctx) });
    return { status: 200, body: report };
  }

  return undefined;
}

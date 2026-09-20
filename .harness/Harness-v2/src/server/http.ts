import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { URL } from "node:url";

import { listApprovals, readApproval, resolveApproval } from "../approvals.ts";
import { awaitTurn } from "../await.ts";
import { loadClientRuntime, overlayOperatorConfig } from "../client-runtime.ts";
import { initComputer } from "../computer.ts";
import { findHandle, listHandles } from "../handle.ts";
import { listInbox, pendingCount } from "../inbox.ts";
import { liveStatus, readLane } from "../lane-state.ts";
import { readMemoryFile } from "../memory.ts";
import { readProtocol, searchProtocol } from "../protocol-log.ts";
import { findBot, loadRoster } from "../roster.ts";
import { readRoomLog, roomPost } from "../rooms.ts";
import { fireRoutine, listReceipts } from "../routines.ts";
import { searchAgents } from "../search.ts";
import { executeFakeTurn } from "../ask-peer.ts";
import { sendPrompt } from "../send.ts";
import { startSidecar, type SidecarHandle } from "../sidecar.ts";
import { startFakeWorkers } from "../worker.ts";
import { wipeRuntime } from "../wipe.ts";
import { transcriptTail } from "../transcript-tail.ts";
import { buildSnapshot, handleOperatorApi } from "./api.ts";
import { EventBus } from "./bus.ts";
import { handleOmbCompat } from "./omb-compat.ts";
import { loadOperatorConfig, type OperatorConfig } from "./operator-config.ts";
import { startPumps } from "./pump.ts";
import { tryServeStatic } from "./static.ts";
import { startSupervisor, type Supervisor } from "./supervisor.ts";

export interface ServeOptions {
  readonly computerRoot: string;
  readonly host?: string;
  readonly port?: number;
  readonly workers?: boolean;
  readonly lazyWorkers?: boolean;
  readonly fakeWorkers?: boolean;
  readonly autoRoutines?: boolean;
  readonly wipe?: boolean;
  readonly keepMemory?: boolean;
  readonly wipeRuns?: boolean;
  readonly sidecar?: boolean;
  readonly config?: OperatorConfig;
}

interface RequestContext {
  readonly computerRoot: string;
  readonly fakeWorkers: boolean;
  readonly bus: EventBus;
  readonly supervisor?: Supervisor;
  readonly sidecar?: SidecarHandle;
}

function actualPort(server: Server, fallback: number): number {
  const addr = server.address();
  if (typeof addr === "object" && addr) {
    return addr.port;
  }
  return fallback;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

async function readBody(req: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  const raw = Buffer.concat(chunks).toString("utf8");
  if (raw.trim().length === 0) {
    return {};
  }
  return JSON.parse(raw) as unknown;
}

function sendJson(res: ServerResponse, status: number, body: unknown): void {
  const data = `${JSON.stringify(body, null, 2)}\n`;
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "access-control-allow-origin": "*",
  });
  res.end(data);
}

function notFound(res: ServerResponse): void {
  sendJson(res, 404, { error: "not found" });
}

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
  "access-control-allow-headers": "content-type",
} as const;

export async function startServer(options: ServeOptions): Promise<{
  readonly server: Server;
  readonly url: string;
  readonly supervisor: Supervisor | undefined;
  readonly bus: EventBus;
  readonly sidecar?: SidecarHandle;
  stop: () => Promise<void>;
}> {
  const computerRoot = options.computerRoot;
  if (options.wipe) {
    wipeRuntime(computerRoot, {
      keepMemory: options.keepMemory,
      keepSidecarPort: true,
      wipeRuns: options.wipeRuns === true,
    });
  }
  const roster = initComputer(computerRoot);
  const client = loadClientRuntime(computerRoot);
  const home = options.config ?? loadOperatorConfig();
  const merged = overlayOperatorConfig(computerRoot, home, client);
  const host = options.host ?? "127.0.0.1";
  const port = options.port ?? merged.port;
  const bus = new EventBus();
  const fake =
    options.fakeWorkers === true
      ? startFakeWorkers(computerRoot, roster.bots.map((bot) => bot.slug), (slug, item) =>
          executeFakeTurn(computerRoot, slug, item, 8_000),
        )
      : undefined;
  const wantSidecar = options.sidecar !== false && fake === undefined && client.sidecar !== undefined;
  const sidecar = wantSidecar ? await startSidecar(computerRoot, client) : undefined;
  const lazy = options.lazyWorkers ?? merged.spawnPolicy === "lazy";
  const autoRoutines = options.autoRoutines ?? client.autoRoutines;
  const supervisor =
    options.workers === false || fake !== undefined
      ? undefined
      : await startSupervisor({
          computerRoot,
          lazy,
          autoRoutines,
          bus,
          config: merged,
        });
  const pumps = startPumps(computerRoot, bus);

  const server = createServer((req, res) => {
    void handleRequest(req, res, {
      computerRoot,
      fakeWorkers: fake !== undefined,
      bus,
      supervisor,
      sidecar,
    });
  });

  await new Promise<void>((resolve, reject) => {
    server.listen(port, host, () => {
      resolve();
    });
    server.on("error", reject);
  });

  const url = `http://${host}:${actualPort(server, port)}`;
  return {
    server,
    url,
    supervisor,
    bus,
    sidecar,
    stop: async (): Promise<void> => {
      pumps.stop();
      fake?.stop();
      await supervisor?.stop();
      await sidecar?.stop();
      await new Promise<void>((resolve, reject) => {
        server.close((err) => {
          if (err) {
            reject(err);
            return;
          }
          resolve();
        });
      });
    },
  };
}

function attachSse(res: ServerResponse, ctx: RequestContext): void {
  res.writeHead(200, {
    "content-type": "text/event-stream",
    "cache-control": "no-cache",
    connection: "keep-alive",
    ...CORS,
  });
  const hello = {
    kind: "hello",
    cursor: "h:0",
    resumed: false,
    snapshot: buildSnapshot(ctx.computerRoot, ctx.fakeWorkers, ctx.supervisor, ctx.sidecar),
  };
  res.write(`id: h:0\ndata: ${JSON.stringify(hello)}\n\n`);
  ctx.bus.subscribe(res);
  const ping = setInterval(() => {
    try {
      res.write(`data: ${JSON.stringify({ kind: "ping" })}\n\n`);
    } catch {
      clearInterval(ping);
    }
  }, 15_000);
  ping.unref();
  res.on("close", () => {
    clearInterval(ping);
  });
}

async function handleRequest(
  req: IncomingMessage,
  res: ServerResponse,
  ctx: RequestContext,
): Promise<void> {
  const computerRoot = ctx.computerRoot;
  try {
    if (req.method === "OPTIONS") {
      res.writeHead(204, CORS);
      res.end();
      return;
    }
    const url = new URL(req.url ?? "/", "http://127.0.0.1");
    const path = url.pathname;
    const method = req.method ?? "GET";

    if (method === "GET" && (path === "/api/events" || path === "/v1/events")) {
      attachSse(res, ctx);
      return;
    }

    if (path.startsWith("/api/") || path.startsWith("/.well-known/")) {
      const body = method === "GET" || method === "HEAD" ? {} : await readBody(req);
      const apiCtx = {
        computerRoot,
        fakeWorkers: ctx.fakeWorkers,
        supervisor: ctx.supervisor,
        bus: ctx.bus,
        sidecar: ctx.sidecar,
      };
      const omb = await handleOmbCompat(method, path, url, body, apiCtx);
      if (omb) {
        sendJson(res, omb.status, omb.body);
        return;
      }
      if (path.startsWith("/api/")) {
        const result = await handleOperatorApi(method, path, url, body, apiCtx);
        if (result) {
          sendJson(res, result.status, result.body);
          return;
        }
      }
    }

    if (method === "GET" && (path === "/health" || path === "/v1/health")) {
      const live = loadRoster(computerRoot);
      sendJson(res, 200, {
        ok: true,
        system: live.system,
        bots: live.bots.length,
        fakeWorkers: ctx.fakeWorkers,
        ui: true,
        sidecar: ctx.sidecar ? { port: ctx.sidecar.port, owned: ctx.sidecar.owned } : null,
      });
      return;
    }

    if (method === "GET" && path === "/v1/roster") {
      const roster = loadRoster(computerRoot);
      sendJson(res, 200, {
        ...roster,
        bots: roster.bots.map((bot) => ({
          ...bot,
          status: liveStatus(computerRoot, bot.id),
          pending: pendingCount(computerRoot, bot.id),
        })),
      });
      return;
    }

    if (method === "GET" && path === "/v1/bots") {
      const query = url.searchParams.get("query") ?? "";
      const status = url.searchParams.get("status") ?? undefined;
      sendJson(
        res,
        200,
        searchAgents(
          computerRoot,
          query,
          status === "offline" || status === "idle" || status === "running" || status === "blocked"
            ? status
            : undefined,
        ),
      );
      return;
    }

    const botMatch = /^\/v1\/bots\/([^/]+)(\/.*)?$/.exec(path);
    if (botMatch) {
      const slug = decodeURIComponent(botMatch[1] ?? "");
      const rest = botMatch[2] ?? "";
      const roster = loadRoster(computerRoot);
      const bot = findBot(roster, slug);
      if (!bot) {
        sendJson(res, 404, { error: "unknown" });
        return;
      }
      if (method === "GET" && rest === "") {
        sendJson(res, 200, {
          ...bot,
          status: liveStatus(computerRoot, bot.id),
          lane: readLane(computerRoot, bot.id),
          handles: listHandles(computerRoot, bot.id),
        });
        return;
      }
      if (method === "GET" && rest === "/transcript") {
        const limit = Number(url.searchParams.get("limit") ?? "20");
        const before = url.searchParams.get("before");
        sendJson(
          res,
          200,
          transcriptTail(
            computerRoot,
            bot.id,
            Number.isFinite(limit) ? limit : 20,
            before ? Number(before) : undefined,
          ),
        );
        return;
      }
      if (method === "GET" && rest === "/inbox") {
        sendJson(res, 200, listInbox(computerRoot, bot.id));
        return;
      }
      if (method === "POST" && rest === "/prompt") {
        const body = await readBody(req);
        const text = isRecord(body) && typeof body.text === "string" ? body.text : "";
        if (text.length === 0) {
          sendJson(res, 400, { error: "text required" });
          return;
        }
        sendJson(
          res,
          200,
          sendPrompt({
            computerRoot,
            from: "operator",
            to: bot.id,
            prompt: text,
            kind: "user_dm",
          }),
        );
        return;
      }
      if (method === "POST" && rest === "/stop") {
        sendJson(
          res,
          200,
          sendPrompt({
            computerRoot,
            from: "operator",
            to: bot.id,
            prompt: "Stop now",
            kind: "user_stop",
            onBusy: "supersede",
          }),
        );
        return;
      }
    }

    if (method === "GET" && path === "/v1/handles") {
      const roster = loadRoster(computerRoot);
      const slug = url.searchParams.get("bot");
      const bots = slug
        ? [findBot(roster, slug)].filter((bot): bot is NonNullable<typeof bot> => bot !== undefined)
        : [...roster.bots];
      sendJson(
        res,
        200,
        bots.flatMap((bot) => listHandles(computerRoot, bot.id)),
      );
      return;
    }

    const handleMatch = /^\/v1\/handles\/([^/]+)(\/await)?$/.exec(path);
    if (handleMatch) {
      const handleId = decodeURIComponent(handleMatch[1] ?? "");
      if (method === "GET" && !handleMatch[2]) {
        const handle = findHandle(computerRoot, handleId);
        if (!handle) {
          sendJson(res, 404, { error: "unknown handle" });
          return;
        }
        sendJson(res, 200, handle);
        return;
      }
      if (method === "POST" && handleMatch[2] === "/await") {
        const timeoutMs = Number(url.searchParams.get("timeoutMs") ?? "30000");
        sendJson(res, 200, await awaitTurn(computerRoot, handleId, { timeoutMs }));
        return;
      }
    }

    if (method === "GET" && path === "/v1/protocol") {
      const after = Number(url.searchParams.get("after") ?? "0");
      const query = url.searchParams.get("query") ?? "";
      const events =
        query.length > 0
          ? searchProtocol(computerRoot, query)
          : readProtocol(computerRoot, Number.isFinite(after) ? after : 0);
      sendJson(res, 200, events);
      return;
    }

    if (method === "GET" && path === "/v1/protocol/stream") {
      attachSse(res, ctx);
      return;
    }

    const roomMatch = /^\/v1\/rooms\/([^/]+)(\/post)?$/.exec(path);
    if (roomMatch) {
      const roomId = decodeURIComponent(roomMatch[1] ?? "");
      if (method === "GET" && !roomMatch[2]) {
        sendJson(res, 200, readRoomLog(computerRoot, roomId));
        return;
      }
      if (method === "POST" && roomMatch[2] === "/post") {
        const body = await readBody(req);
        const text = isRecord(body) && typeof body.text === "string" ? body.text : "";
        const from = isRecord(body) && typeof body.from === "string" ? body.from : "operator";
        sendJson(res, 200, await roomPost({ computerRoot, roomId, from, text }));
        return;
      }
    }

    if (method === "GET" && path === "/v1/approvals") {
      sendJson(res, 200, listApprovals(computerRoot));
      return;
    }

    const approvalMatch = /^\/v1\/approvals\/([^/]+)$/.exec(path);
    if (approvalMatch && method === "POST") {
      const id = decodeURIComponent(approvalMatch[1] ?? "");
      const body = await readBody(req);
      const allowed = isRecord(body) && body.allow === true;
      sendJson(res, 200, resolveApproval(computerRoot, id, allowed));
      return;
    }
    if (approvalMatch && method === "GET") {
      const id = decodeURIComponent(approvalMatch[1] ?? "");
      const row = readApproval(computerRoot, id);
      if (!row) {
        sendJson(res, 404, { error: "unknown approval" });
        return;
      }
      sendJson(res, 200, row);
      return;
    }

    const routineMatch = /^\/v1\/routines\/([^/]+)\/run$/.exec(path);
    if (routineMatch && method === "POST") {
      const name = decodeURIComponent(routineMatch[1] ?? "");
      sendJson(res, 200, fireRoutine(computerRoot, name));
      return;
    }

    if (method === "GET" && path === "/v1/receipts") {
      sendJson(res, 200, listReceipts(computerRoot));
      return;
    }

    const memMatch = /^\/v1\/memory\/([^/]+)$/.exec(path);
    if (memMatch && method === "GET") {
      const slug = decodeURIComponent(memMatch[1] ?? "");
      const roster = loadRoster(computerRoot);
      const bot = findBot(roster, slug);
      if (!bot) {
        sendJson(res, 404, { error: "unknown" });
        return;
      }
      const rel = url.searchParams.get("path") ?? "MEMORY.md";
      sendJson(res, 200, { path: rel, content: readMemoryFile(computerRoot, bot.id, rel) });
      return;
    }

    if (tryServeStatic(req, res)) {
      return;
    }

    if (path.startsWith("/api/")) {
      sendJson(res, 404, { error: `no ${method} ${path}` });
      return;
    }

    if (method === "GET" && (path === "/" || !path.startsWith("/v1/"))) {
      sendJson(res, 503, {
        error: "operator ui is not built",
        hint: "cd ui && npm install && npm run build, then restart harness serve",
      });
      return;
    }

    notFound(res);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    sendJson(res, 500, { error: message });
  }
}

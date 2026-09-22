import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { resolve } from "node:path";
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
import { sidecarHealthy, startSidecar, type SidecarHandle } from "../sidecar.ts";
import { startFakeWorkers } from "../worker.ts";
import { wipeRuntime } from "../wipe.ts";
import { transcriptTail } from "../transcript-tail.ts";
import { buildSnapshot, handleOperatorApi } from "./api.ts";
import { EventBus } from "./bus.ts";
import { handleOmbCompat, resetOmbLiveChain } from "./omb-compat.ts";
import { bindRunningComputer, handleOfficeInstanceRequest, officePublicState, resolveServeComputer } from "./office-instances.ts";
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

/**
 * Mutable serve context. computerRoot changes when the operator selects a
 * saved office desk. handleRequest reads these fields on every request.
 */
export interface LiveOffice {
  computerRoot: string;
  supervisor?: Supervisor;
  pumps: { stop: () => void };
  fake?: { stop: () => void };
  sidecar?: SidecarHandle;
  readonly bus: EventBus;
  readonly fakeWorkers: boolean;
  readonly workersEnabled: boolean;
  readonly lazy: boolean;
  readonly autoRoutines: boolean;
  readonly wantSidecar: boolean;
  config?: OperatorConfig;
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

function publishOfficeHello(live: LiveOffice): void {
  live.bus.publish({
    kind: "hello",
    cursor: "h:0",
    resumed: false,
  });
  live.bus.publish({
    kind: "office",
    ...officePublicState(live.computerRoot),
  });
}

async function bootRuntime(live: LiveOffice): Promise<void> {
  const computerRoot = live.computerRoot;
  if (live.fakeWorkers) {
    const roster = loadRoster(computerRoot);
    live.fake = startFakeWorkers(
      computerRoot,
      roster.bots.map((bot) => bot.slug),
      (slug, item) => executeFakeTurn(computerRoot, slug, item, 8_000),
    );
  }
  if (live.wantSidecar && live.sidecar === undefined) {
    const client = loadClientRuntime(computerRoot);
    live.sidecar = await startSidecar(computerRoot, client);
  }
  if (live.workersEnabled) {
    live.supervisor = await startSupervisor({
      computerRoot,
      lazy: live.lazy,
      autoRoutines: live.autoRoutines,
      bus: live.bus,
      config: live.config,
    });
  }
  live.pumps = startPumps(computerRoot, live.bus);
}

async function stopRuntime(live: LiveOffice, options: { readonly keepSidecar?: boolean } = {}): Promise<void> {
  await live.supervisor?.stop();
  live.supervisor = undefined;
  live.pumps.stop();
  live.fake?.stop();
  live.fake = undefined;
  if (options.keepSidecar && live.sidecar) {
    const healthy = await sidecarHealthy(live.sidecar.port);
    if (healthy) {
      return;
    }
  }
  if (live.sidecar?.owned) {
    await live.sidecar.stop();
    live.sidecar = undefined;
  } else {
    live.sidecar = undefined;
  }
}

async function applyOfficeSelect(live: LiveOffice, nextRoot: string): Promise<void> {
  const resolved = resolve(nextRoot);
  if (resolve(live.computerRoot) === resolved) {
    return;
  }
  const previous = live.computerRoot;
  // Sidecar binds HARNESS_COMPUTER. Keep it only on the same Computer, never across desks.
  await stopRuntime(live);
  resetOmbLiveChain();
  try {
    live.computerRoot = resolved;
    bindRunningComputer(resolved);
    const client = loadClientRuntime(resolved);
    live.config = overlayOperatorConfig(resolved, loadOperatorConfig(), client);
    await bootRuntime(live);
    publishOfficeHello(live);
  } catch (error) {
    await stopRuntime(live);
    live.computerRoot = previous;
    bindRunningComputer(previous);
    const previousClient = loadClientRuntime(previous);
    live.config = overlayOperatorConfig(previous, loadOperatorConfig(), previousClient);
    await bootRuntime(live);
    throw error;
  }
}

export async function startServer(options: ServeOptions): Promise<{
  readonly server: Server;
  readonly url: string;
  readonly supervisor: Supervisor | undefined;
  readonly bus: EventBus;
  readonly sidecar?: SidecarHandle;
  stop: () => Promise<void>;
}> {
  const computerRoot = resolveServeComputer(options.computerRoot);
  if (options.wipe) {
    wipeRuntime(computerRoot, {
      keepMemory: options.keepMemory,
      keepSidecarPort: true,
      wipeRuns: options.wipeRuns === true,
    });
  }
  initComputer(computerRoot);
  bindRunningComputer(computerRoot);
  const client = loadClientRuntime(computerRoot);
  const home = options.config ?? loadOperatorConfig();
  const merged = overlayOperatorConfig(computerRoot, home, client);
  const host = options.host ?? "127.0.0.1";
  const port = options.port ?? merged.port;
  const bus = new EventBus();
  const fakeWorkers = options.fakeWorkers === true;
  const live: LiveOffice = {
    computerRoot,
    pumps: { stop: (): void => undefined },
    bus,
    fakeWorkers,
    workersEnabled: options.workers !== false && !fakeWorkers,
    lazy: options.lazyWorkers ?? merged.spawnPolicy === "lazy",
    autoRoutines: options.autoRoutines ?? client.autoRoutines,
    wantSidecar: options.sidecar !== false && !fakeWorkers && client.sidecar !== undefined,
    config: merged,
  };
  await bootRuntime(live);

  const server = createServer((req, res) => {
    void handleRequest(req, res, live);
  });

  await new Promise<void>((resolveListen, reject) => {
    server.listen(port, host, () => {
      resolveListen();
    });
    server.on("error", reject);
  });

  const url = `http://${host}:${actualPort(server, port)}`;
  return {
    server,
    url,
    get supervisor(): Supervisor | undefined {
      return live.supervisor;
    },
    bus,
    get sidecar(): SidecarHandle | undefined {
      return live.sidecar;
    },
    stop: async (): Promise<void> => {
      live.pumps.stop();
      live.fake?.stop();
      await live.supervisor?.stop();
      await live.sidecar?.stop();
      await new Promise<void>((resolveClose, rejectClose) => {
        server.close((err) => {
          if (err) {
            rejectClose(err);
            return;
          }
          resolveClose();
        });
      });
    },
  };
}

function attachSse(res: ServerResponse, ctx: LiveOffice): void {
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
  live: LiveOffice,
): Promise<void> {
  const computerRoot = live.computerRoot;
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
      attachSse(res, live);
      return;
    }

    if (path.startsWith("/api/") || path.startsWith("/.well-known/")) {
      const body = method === "GET" || method === "HEAD" ? {} : await readBody(req);
      if (path === "/api/office-instances" || path.startsWith("/api/office-instances/")) {
        const office = await handleOfficeInstanceRequest(
          method,
          path,
          body,
          live.computerRoot,
          (nextRoot) => applyOfficeSelect(live, nextRoot),
        );
        if (office) {
          sendJson(res, office.status, office.body);
          return;
        }
      }
      const apiCtx = {
        computerRoot: live.computerRoot,
        fakeWorkers: live.fakeWorkers,
        supervisor: live.supervisor,
        bus: live.bus,
        sidecar: live.sidecar,
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
      const roster = loadRoster(computerRoot);
      sendJson(res, 200, {
        ok: true,
        system: roster.system,
        bots: roster.bots.length,
        fakeWorkers: live.fakeWorkers,
        ui: true,
        sidecar: live.sidecar ? { port: live.sidecar.port, owned: live.sidecar.owned } : null,
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
      attachSse(res, live);
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

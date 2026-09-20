import { liveStatus } from "../lane-state.ts";
import { findBot, findRoom, loadRoster } from "../roster.ts";
import { readRoomLog, roomPost } from "../rooms.ts";
import { fireRoutine } from "../routines.ts";
import type { ApprovalLevel, BotRecord, Roster } from "../types.ts";
import { handleOperatorApi, messagesForBot, type ApiContext, type OperatorMessage } from "./api.ts";
import { loadOperatorConfig, patchOperatorConfig, publicOperatorConfig } from "./operator-config.ts";

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

interface OmbMessage {
  readonly id: string;
  readonly role: "bot" | "user";
  readonly kind: "text" | "options" | "activity";
  readonly text?: string;
  readonly at: number;
  readonly sendId?: string;
  readonly from?: { readonly botId: string; readonly name: string; readonly color: MausColor };
  readonly card?: {
    readonly title: string;
    readonly subtitle: string;
    readonly options: readonly string[];
    readonly requestId?: string;
  };
}

interface OmbOnboarding {
  completedAt: string;
  version: number;
  reelSeen: boolean;
  hintsSeen: string[];
}

interface JsonResult {
  readonly status: number;
  readonly body: unknown;
}

const ombUi = {
  onboarding: {
    completedAt: "2026-01-01T00:00:00.000Z",
    version: 1,
    reelSeen: true,
    hintsSeen: [] as string[],
  } satisfies OmbOnboarding,
  profile: { name: "", email: "" },
  language: "",
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function slugify(name: string): string {
  const slug = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug.length > 0 ? slug : "bot";
}

function colorFor(index: number): MausColor {
  return MAUS_COLORS[index % MAUS_COLORS.length] ?? "teal";
}

function activityFor(status: string): "working" | "waiting-on-you" | "idle" | "no-signal" {
  if (status === "running") {
    return "working";
  }
  if (status === "blocked") {
    return "waiting-on-you";
  }
  if (status === "offline") {
    return "no-signal";
  }
  return "idle";
}

function approvalModeFor(level: ApprovalLevel): "ask" | "auto" {
  return level === "never" ? "auto" : "ask";
}

function epoch(iso: string): number {
  const parsed = Date.parse(iso);
  return Number.isFinite(parsed) ? parsed : Date.now();
}

function toOmbMessage(row: OperatorMessage): OmbMessage {
  const role: OmbMessage["role"] = row.role === "user" ? "user" : "bot";
  const kind: OmbMessage["kind"] =
    row.kind === "options" ? "options" : row.kind === "activity" ? "activity" : "text";
  return {
    id: row.id,
    role,
    kind,
    text: row.text,
    at: epoch(row.at),
    ...(row.card
      ? {
          card: {
            title: row.card.title,
            subtitle: row.card.subtitle,
            options: row.card.options,
            requestId: row.card.requestId,
          },
        }
      : {}),
  };
}

function defaultModel(): string {
  return loadOperatorConfig().model ?? "default";
}

function toWireBot(computerRoot: string, roster: Roster, bot: BotRecord, index: number): Record<string, unknown> {
  const status = liveStatus(computerRoot, bot.id);
  const activity = activityFor(status);
  const busy = activity === "working" || activity === "waiting-on-you";
  const messages = messagesForBot(computerRoot, bot.id).map(toOmbMessage);
  const model = defaultModel();
  const createdAt = messages[0]?.at ?? Date.now();
  return {
    id: bot.id,
    threadId: bot.id,
    tasks: [
      {
        threadId: bot.id,
        title: bot.purpose.length > 0 ? bot.purpose : bot.name,
        createdAt,
        activity,
        busy,
        unread: false,
      },
    ],
    name: bot.name,
    title: bot.purpose.length > 0 ? bot.purpose : bot.slug,
    description: bot.purpose,
    soul: bot.instructions,
    notifications: true,
    color: colorFor(index),
    avatarUrl: null,
    unread: false,
    busy,
    activity,
    modelSelection: { instanceId: "pi", model },
    computer: "off",
    approvalMode: approvalModeFor(bot.approvalLevel),
    autoApprove: bot.approvalLevel === "never",
    section: roster.system,
    messages,
    createdAt,
  };
}

function memberIds(roster: Roster, members: readonly string[]): string[] {
  const ids: string[] = [];
  for (const member of members) {
    const bot = findBot(roster, member);
    if (bot) {
      ids.push(bot.id);
    }
  }
  return ids;
}

function toWireGroup(computerRoot: string, roster: Roster, roomId: string): Record<string, unknown> | undefined {
  const room = findRoom(roster, roomId);
  if (!room) {
    return undefined;
  }
  const ids = memberIds(roster, room.members);
  const lead = ids[0] ?? roster.bots[0]?.id ?? "";
  const messages: OmbMessage[] = readRoomLog(computerRoot, room.id).map((row, index) => {
    const speaker = findBot(roster, row.from);
    const speakerIndex = speaker ? roster.bots.findIndex((bot) => bot.id === speaker.id) : 0;
    return {
      id: `room-${room.id}-${index}`,
      role: row.from === "operator" ? "user" : "bot",
      kind: "text",
      text: row.text,
      at: epoch(row.t),
      ...(speaker
        ? { from: { botId: speaker.id, name: speaker.name, color: colorFor(speakerIndex) } }
        : {}),
    };
  });
  return {
    id: room.id,
    threadId: `room-${room.id}`,
    name: room.title,
    memberIds: ids,
    defaultResponder: { kind: "member", botId: lead },
    bulletin: "",
    unread: false,
    createdAt: messages[0]?.at ?? Date.now(),
    setupCompletedAt: Date.now(),
    section: roster.system,
    messages,
  };
}

function piInstance(): Record<string, unknown> {
  const model = defaultModel();
  return {
    instanceId: "pi",
    driverKind: "pi",
    displayName: "Pi",
    snapshot: {
      state: "available",
      authenticated: true,
      version: null,
    },
    models: {
      default: model,
      options: [{ id: model, label: model }],
    },
    capabilities: { queueing: true },
    cliDefault: "pi",
    access: "custom",
  };
}

function configStatus(): Record<string, unknown> {
  const publicCfg = publicOperatorConfig();
  const keys = publicCfg.keys;
  return {
    xai: { configured: Boolean(keys.xai || keys.XAI_API_KEY) },
    anthropic: { configured: Boolean(keys.anthropic || keys.ANTHROPIC_API_KEY) },
    openaiCompat: { configured: Boolean(keys.openai || keys.OPENAI_API_KEY), url: "" },
    edition: { edition: "oss", features: [] },
    fleet: { available: false },
    composio: { configured: false, mode: "unavailable" },
    box: { configured: false },
    vps: { configured: false, sshAlias: "" },
    rooms: { turnTimeoutMinutes: 30 },
    threads: { maxConcurrentPerBot: 1 },
    localVm: { mode: "shared", maxInstances: 1 },
    opencodeGo: { configured: false },
    tts: { configured: false, ready: false, voice: "" },
    profile: ombUi.profile,
    language: ombUi.language,
    features: {
      skillAuthoring: false,
      showToolCalls: true,
      browser: false,
      sharedComputers: false,
      claudeUserMcp: false,
    },
    onboarding: ombUi.onboarding,
    browserEngine: { kind: "unavailable", reason: "browser is not part of this host" },
    browserProfiles: [],
    signIn: { admins: [], members: [] },
    spawnPolicy: publicCfg.spawnPolicy,
    model: publicCfg.model,
    provider: publicCfg.provider,
    keys: publicCfg.keys,
    configPath: publicCfg.configPath,
  };
}

function mergeOnboarding(patch: unknown): void {
  if (!isRecord(patch)) {
    return;
  }
  if (typeof patch.completedAt === "string") {
    ombUi.onboarding.completedAt = patch.completedAt;
  }
  if (typeof patch.version === "number") {
    ombUi.onboarding.version = patch.version;
  }
  if (typeof patch.reelSeen === "boolean") {
    ombUi.onboarding.reelSeen = patch.reelSeen;
  }
  if (Array.isArray(patch.hintsSeen)) {
    ombUi.onboarding.hintsSeen = patch.hintsSeen.filter((row): row is string => typeof row === "string");
  }
}

function applyConfigPatch(body: unknown, ctx: ApiContext): JsonResult {
  if (!isRecord(body)) {
    return { status: 400, body: { error: "object required" } };
  }
  const harnessPatch: Record<string, unknown> = {};
  if (body.spawnPolicy !== undefined) {
    harnessPatch.spawnPolicy = body.spawnPolicy;
  }
  if (body.model !== undefined) {
    harnessPatch.model = body.model;
  }
  if (body.provider !== undefined) {
    harnessPatch.provider = body.provider;
  }
  if (body.apiKeys !== undefined) {
    harnessPatch.apiKeys = body.apiKeys;
  }
  if (body.openBrowser !== undefined) {
    harnessPatch.openBrowser = body.openBrowser;
  }
  if (Object.keys(harnessPatch).length > 0) {
    const next = patchOperatorConfig(harnessPatch);
    ctx.bus?.publish({ kind: "config", ...configStatus(), spawnPolicy: next.spawnPolicy });
  }
  if (isRecord(body.profile)) {
    ombUi.profile = {
      name: typeof body.profile.name === "string" ? body.profile.name : ombUi.profile.name,
      email: typeof body.profile.email === "string" ? body.profile.email : ombUi.profile.email,
    };
  }
  if (typeof body.language === "string") {
    ombUi.language = body.language;
  }
  if (body.onboarding !== undefined) {
    mergeOnboarding(body.onboarding);
  }
  const status = configStatus();
  ctx.bus?.publish({ kind: "config", ...status });
  return { status: 200, body: status };
}

function environmentBody(): Record<string, unknown> {
  return {
    environmentId: "local",
    label: "OpenMausBot",
    platform: process.platform,
    version: "2.0.0",
    capabilities: { remoteSessions: true, selfUpdate: "operator" },
  };
}

function toRoutine(roster: Roster, name: string, botSlug: string, cadence: string, prompt: string): Record<string, unknown> {
  const owner = findBot(roster, botSlug);
  const now = Date.now();
  return {
    id: name,
    name,
    prompt,
    target: "bot",
    botId: owner?.id ?? botSlug,
    runOn: "maus",
    enabled: true,
    schedule:
      cadence === "daily"
        ? { type: "daily", time: "09:00", weekdays: [1, 2, 3, 4, 5] }
        : { type: "interval", everyMinutes: 60, anchorAt: now },
    durationMinutes: 15,
    nextRunAt: null,
    createdAt: now,
    updatedAt: now,
  };
}

async function wrapBotMutation(
  method: string,
  path: string,
  url: URL,
  body: unknown,
  ctx: ApiContext,
): Promise<JsonResult | undefined> {
  const inner = await handleOperatorApi(method, path, url, body, ctx);
  if (!inner) {
    return undefined;
  }
  if (inner.status >= 400) {
    return inner;
  }
  const roster = loadRoster(ctx.computerRoot);
  const record = inner.body;
  const id = isRecord(record) && typeof record.id === "string" ? record.id : undefined;
  const bot = id ? findBot(roster, id) : undefined;
  if (!bot) {
    return inner;
  }
  const index = roster.bots.findIndex((row) => row.id === bot.id);
  return {
    status: method === "POST" && path === "/api/bots" ? 201 : inner.status,
    body: { bot: toWireBot(ctx.computerRoot, roster, bot, index) },
  };
}

export async function handleOmbCompat(
  method: string,
  path: string,
  url: URL,
  body: unknown,
  ctx: ApiContext,
): Promise<JsonResult | undefined> {
  const computerRoot = ctx.computerRoot;

  if (method === "GET" && path === "/.well-known/openmausbot/environment") {
    return { status: 200, body: environmentBody() };
  }

  if (method === "GET" && path === "/api/auth/session") {
    return {
      status: 200,
      body: { kind: "loopback", scopes: ["admin"], environmentId: "local" },
    };
  }

  if (method === "POST" && path === "/api/auth/stream-ticket") {
    return { status: 200, body: { ticket: null, reason: "loopback needs no ticket" } };
  }

  if (method === "GET" && path === "/api/brand") {
    return {
      status: 200,
      body: { brand: { name: "OpenMausBot" }, source: "default", file: "" },
    };
  }

  if (method === "GET" && path === "/api/config") {
    return { status: 200, body: configStatus() };
  }

  if ((method === "PUT" || method === "PATCH") && path === "/api/config") {
    return applyConfigPatch(body, ctx);
  }

  if (method === "GET" && path === "/api/instances") {
    return { status: 200, body: { instances: [piInstance()] } };
  }

  const refreshModels = /^\/api\/instances\/([^/]+)\/refresh-models$/.exec(path);
  if (refreshModels && method === "POST") {
    return { status: 200, body: { instances: [piInstance()] } };
  }

  if (method === "GET" && path === "/api/webhooks") {
    return {
      status: 200,
      body: { webhooks: [], attempts: [], ingress: { available: false, baseUrl: "" } },
    };
  }

  if (method === "GET" && path === "/api/connectors/connected") {
    return { status: 200, body: { services: {}, credentialStore: "unavailable" } };
  }

  if (method === "GET" && path === "/api/connectors/catalog") {
    return { status: 200, body: { toolkits: [] } };
  }

  if (method === "GET" && path === "/api/routines") {
    const roster = loadRoster(computerRoot);
    return {
      status: 200,
      body: {
        routines: roster.routines.map((row) => toRoutine(roster, row.name, row.bot, row.cadence, row.prompt)),
        runs: [],
      },
    };
  }

  const routineRun = /^\/api\/routines\/([^/]+)\/run$/.exec(path);
  if (routineRun && method === "POST") {
    const name = decodeURIComponent(routineRun[1] ?? "");
    let fired: ReturnType<typeof fireRoutine>;
    try {
      fired = fireRoutine(computerRoot, name);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      return { status: 404, body: { error: message } };
    }
    const roster = loadRoster(computerRoot);
    const routine = roster.routines.find((row) => row.name === fired.name);
    return {
      status: 201,
      body: {
        run: {
          id: fired.id,
          routineId: fired.name,
          routineName: fired.name,
          prompt: routine?.prompt,
          target: "bot",
          botId: findBot(roster, fired.bot)?.id ?? fired.bot,
          runOn: "maus",
          scheduledFor: epoch(fired.at),
          status: fired.status === "queued" ? "queued" : fired.status === "running" ? "running" : "completed",
          manual: true,
          createdAt: epoch(fired.at),
        },
        ...fired,
      },
    };
  }

  if (method === "GET" && path === "/api/bots") {
    const roster = loadRoster(computerRoot);
    return {
      status: 200,
      body: {
        bots: roster.bots.map((bot, index) => toWireBot(computerRoot, roster, bot, index)),
        groups: roster.rooms
          .map((room) => toWireGroup(computerRoot, roster, room.id))
          .filter((row): row is Record<string, unknown> => row !== undefined),
        sections: [roster.system],
        computerControl: {},
        botQueuedMessages: {},
      },
    };
  }

  if (method === "POST" && path === "/api/bots") {
    const name = isRecord(body) && typeof body.name === "string" ? body.name : "";
    const slug =
      isRecord(body) && typeof body.slug === "string" && body.slug.trim().length > 0
        ? body.slug
        : slugify(name);
    const purpose =
      (isRecord(body) && asString(body.title)) ?? (isRecord(body) && asString(body.description)) ?? "";
    const instructions = isRecord(body) && asString(body.description) ? body.description : "";
    return wrapBotMutation(
      method,
      path,
      url,
      { slug, name: name.length > 0 ? name : slug, purpose, instructions },
      ctx,
    );
  }

  const botMatch = /^\/api\/bots\/([^/]+)(\/.*)?$/.exec(path);
  if (botMatch) {
    const key = decodeURIComponent(botMatch[1] ?? "");
    const rest = botMatch[2] ?? "";
    const roster = loadRoster(computerRoot);
    const bot = findBot(roster, key);
    if (!bot) {
      return { status: 404, body: { error: "no such bot" } };
    }
    const index = roster.bots.findIndex((row) => row.id === bot.id);

    if (method === "POST" && rest === "/messages") {
      const inner = await handleOperatorApi(method, path, url, body, ctx);
      if (!inner) {
        return { status: 404, body: { error: "unknown" } };
      }
      if (inner.status >= 400) {
        return inner;
      }
      const text = isRecord(body) && typeof body.text === "string" ? body.text : "";
      const sendId = isRecord(body) && typeof body.sendId === "string" ? body.sendId : undefined;
      const sent = isRecord(inner.body) ? inner.body : {};
      const handleId = typeof sent.handleId === "string" ? sent.handleId : undefined;
      return {
        status: 200,
        body: {
          ...sent,
          ok: true,
          threadId: bot.id,
          message: {
            id: handleId ?? sendId ?? `msg-${Date.now()}`,
            role: "user",
            kind: "text",
            text,
            at: Date.now(),
            sendId,
          },
        },
      };
    }

    if (method === "POST" && (rest === "/read" || rest === "/interrupt" || rest === "/stop")) {
      if (rest === "/read") {
        return { status: 200, body: { ok: true } };
      }
      return handleOperatorApi(method, path, url, body, ctx);
    }

    if (method === "POST" && rest === "/tasks") {
      return { status: 200, body: { bot: toWireBot(computerRoot, roster, bot, index) } };
    }

    if (method === "PATCH" && rest === "") {
      return wrapBotMutation(method, path, url, body, ctx);
    }

    if (method === "GET" && rest === "") {
      return { status: 200, body: toWireBot(computerRoot, roster, bot, index) };
    }
  }

  const groupRead = /^\/api\/groups\/([^/]+)\/read$/.exec(path);
  if (groupRead && method === "POST") {
    return { status: 200, body: { ok: true } };
  }

  const groupInterrupt = /^\/api\/groups\/([^/]+)\/interrupt$/.exec(path);
  if (groupInterrupt && method === "POST") {
    return { status: 200, body: { ok: true } };
  }

  const groupMessages = /^\/api\/groups\/([^/]+)\/messages$/.exec(path);
  if (groupMessages && method === "POST") {
    const roomId = decodeURIComponent(groupMessages[1] ?? "");
    const roster = loadRoster(computerRoot);
    const room = findRoom(roster, roomId);
    if (!room) {
      return { status: 404, body: { error: "no such group" } };
    }
    const text = isRecord(body) && typeof body.text === "string" ? body.text.trim() : "";
    if (text.length === 0) {
      return { status: 400, body: { error: "text required" } };
    }
    const sendId = isRecord(body) && typeof body.sendId === "string" ? body.sendId : undefined;
    await roomPost({
      computerRoot,
      roomId,
      from: "operator",
      text,
      waitCapMs: ctx.fakeWorkers ? 400 : 60_000,
      awaitTimeoutMs: ctx.fakeWorkers ? 8_000 : 90_000,
    });
    const threadId = `room-${room.id}`;
    const message: OmbMessage = {
      id: sendId ?? `room-${room.id}-${Date.now()}`,
      role: "user",
      kind: "text",
      text,
      at: Date.now(),
      sendId,
    };
    ctx.bus?.publish({ kind: "message", threadId, message });
    ctx.bus?.publish({ kind: "group", group: toWireGroup(computerRoot, roster, room.id) });
    return { status: 200, body: { ok: true, threadId, message } };
  }

  return undefined;
}

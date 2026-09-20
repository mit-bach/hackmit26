import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import {
  listMemoryOverview,
  readMemoryDoc,
  writeMemoryDoc,
} from "../memory.ts";
import {
  DemoRecordingMissingError,
  demoMeta,
  loadDemoBundle,
  parseDemoSourceQuery,
  projectFrame,
  recordDemoSession,
  removeDemoRecording,
} from "../demo-replay.ts";
import { computerSkillsRoot, piRpcLogPath, piRuntimePath, protocolLogPath, rosterPath } from "../paths.ts";
import { readProtocol, searchProtocol } from "../protocol-log.ts";
import { findBot, findRoom, loadRoster, saveRoster } from "../roster.ts";
import { initComputer } from "../computer.ts";
import { fireRoutine, listReceipts } from "../routines.ts";
import { searchAgents } from "../search.ts";
import { identityBlock, memorySection, recentWorkSection } from "../prompt.ts";
import { readTranscript } from "../transcript.ts";
import { readJsonl } from "../fs.ts";
import type { BotRecord, ProtocolEvent, ReceiptRecord, Roster, RoutineRecord } from "../types.ts";
import { loadIntercept, parseIntercept, saveIntercept } from "../intercept.ts";
import {
  collectExtraExtensionPaths,
  loadExtensionsManifest,
  saveExtensionsManifest,
} from "../client-attach.ts";
import {
  keyConfigured,
  loadOperatorConfig,
  operatorConfigPath,
  patchOperatorConfig,
  publicOperatorConfig,
} from "./operator-config.ts";
import { buildSnapshot, type ApiContext } from "./api.ts";
import { isPairChannelId } from "./pair-id.ts";

export interface DeskResult {
  readonly status: number;
  readonly body: unknown;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function slugify(name: string, fallback: string): string {
  const slug = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug.length > 0 ? slug : fallback;
}

function publishHello(ctx: ApiContext): void {
  ctx.bus?.publish({
    kind: "hello",
    snapshot: buildSnapshot(ctx.computerRoot, ctx.fakeWorkers, ctx.supervisor),
  });
}

function epoch(iso: string): number {
  const parsed = Date.parse(iso);
  return Number.isFinite(parsed) ? parsed : Date.now();
}

function skillDescription(dir: string): string {
  const file = join(dir, "SKILL.md");
  if (!existsSync(file)) {
    return "";
  }
  const text = readFileSync(file, "utf8");
  const body = text.replace(/^---[\s\S]*?---\s*/, "");
  const line = body
    .split("\n")
    .map((row) => row.replace(/^#+\s*/, "").trim())
    .find((row) => row.length > 0);
  return (line ?? "").slice(0, 240);
}

function listSkillDirs(computerRoot: string): string[] {
  const root = computerSkillsRoot(computerRoot);
  if (!existsSync(root)) {
    return [];
  }
  const names: string[] = [];
  for (const name of readdirSync(root)) {
    if (existsSync(join(root, name, "SKILL.md"))) {
      names.push(name);
    }
  }
  return names.sort();
}

export function listBotSkills(computerRoot: string, bot: BotRecord): {
  readonly skills: readonly {
    readonly name: string;
    readonly description: string;
    readonly enabled: boolean;
    readonly source: string;
    readonly warnings: readonly string[];
  }[];
  readonly staged: readonly unknown[];
} {
  const granted = new Set(bot.skills);
  const disk = listSkillDirs(computerRoot);
  const names = [...new Set([...bot.skills, ...disk])];
  const root = computerSkillsRoot(computerRoot);
  const skills = names.map((name) => {
    const dir = join(root, name);
    const hasFile = existsSync(join(dir, "SKILL.md"));
    const warnings: string[] = [];
    if (granted.has(name) && !hasFile) {
      warnings.push(`roster grants ${name} but Computer/skills/${name}/SKILL.md is missing`);
    }
    return {
      name,
      description: hasFile ? skillDescription(dir) : "Granted on the Roster. File is not on this Computer.",
      enabled: granted.has(name),
      source: "roster",
      warnings,
    };
  });
  return { skills, staged: [] };
}

function setSkillEnabled(computerRoot: string, bot: BotRecord, name: string, enabled: boolean): BotRecord {
  const roster = loadRoster(computerRoot);
  const current = findBot(roster, bot.id);
  if (!current) {
    return bot;
  }
  const nextSkills = enabled
    ? [...new Set([...current.skills, name])]
    : current.skills.filter((item) => item !== name);
  const nextBots = roster.bots.map((row) => (row.id === current.id ? { ...row, skills: nextSkills } : row));
  const next: Roster = { ...roster, bots: nextBots };
  saveRoster(computerRoot, next);
  return findBot(next, current.id) ?? current;
}

function cadenceFromSchedule(schedule: unknown): string {
  if (!isRecord(schedule)) {
    return "daily";
  }
  if (schedule.type === "daily") {
    return "daily";
  }
  if (schedule.type === "interval" && typeof schedule.everyMinutes === "number") {
    const minutes = schedule.everyMinutes;
    if (minutes === 60) {
      return "hourly";
    }
    if (minutes === 24 * 60) {
      return "daily";
    }
    if (minutes === 7 * 24 * 60) {
      return "weekly";
    }
    if (minutes % (24 * 60) === 0) {
      return `every ${minutes / (24 * 60)} d`;
    }
    if (minutes % 60 === 0) {
      return `every ${minutes / 60} h`;
    }
    return `every ${minutes} m`;
  }
  if (schedule.type === "cron" && typeof schedule.expression === "string") {
    if (schedule.expression.includes("1 * *")) {
      return "monthly";
    }
  }
  return "daily";
}

function scheduleFromCadence(cadence: string, now: number): Record<string, unknown> {
  const trimmed = cadence.trim().toLowerCase();
  if (trimmed === "hourly") {
    return { type: "interval", everyMinutes: 60, anchorAt: now };
  }
  if (trimmed === "weekly") {
    return { type: "daily", time: "09:00", weekdays: [1] };
  }
  if (trimmed === "monthly") {
    return { type: "cron", expression: "0 9 1 * *", timeZone: "UTC" };
  }
  const every = /^every\s+(\d+)\s*(s|m|h|ms|d)$/.exec(trimmed);
  if (every) {
    const n = Number(every[1]);
    const unit = every[2];
    let minutes = n;
    if (unit === "h") {
      minutes = n * 60;
    } else if (unit === "d") {
      minutes = n * 24 * 60;
    } else if (unit === "s" || unit === "ms") {
      minutes = Math.max(1, Math.round(n / 60));
    }
    return { type: "interval", everyMinutes: minutes, anchorAt: now };
  }
  return { type: "daily", time: "09:00", weekdays: [0, 1, 2, 3, 4, 5, 6] };
}

export function wireRoutine(roster: Roster, row: RoutineRecord): Record<string, unknown> {
  const owner = findBot(roster, row.bot);
  const now = Date.now();
  const roomId = row.conversation.startsWith("room:") ? row.conversation.slice("room:".length) : undefined;
  return {
    id: row.name,
    name: row.name,
    prompt: row.prompt,
    target: roomId ? "room-goal" : "bot",
    botId: owner?.id ?? row.bot,
    groupId: roomId,
    runOn: "harness",
    enabled: true,
    schedule: scheduleFromCadence(row.cadence, now),
    durationMinutes: 15,
    nextRunAt: null,
    createdAt: now,
    updatedAt: now,
  };
}

export function wireRun(roster: Roster, receipt: ReceiptRecord): Record<string, unknown> {
  const owner = findBot(roster, receipt.bot);
  const status =
    receipt.status === "queued" ||
    receipt.status === "running" ||
    receipt.status === "completed" ||
    receipt.status === "failed" ||
    receipt.status === "missed"
      ? receipt.status === "missed"
        ? "missed"
        : receipt.status
      : "queued";
  return {
    id: receipt.id,
    routineId: receipt.name,
    routineName: receipt.name,
    prompt: undefined,
    target: "bot",
    botId: owner?.id ?? receipt.bot,
    runOn: "harness",
    scheduledFor: epoch(receipt.at),
    status,
    manual: false,
    createdAt: epoch(receipt.at),
    finishedAt: receipt.status === "completed" || receipt.status === "failed" ? epoch(receipt.updatedAt) : undefined,
    output: receipt.result,
  };
}

function runtimeEntry(event: ProtocolEvent, threadId: string): Record<string, unknown> {
  const failed = event.type.includes("fail") || event.status === "failed" || event.status === "cancelled";
  const completed = event.type.includes("completed") || event.type.includes("result") || event.status === "completed";
  const started = event.type.includes("accepted") || event.type.includes("running") || event.type.includes("queued");
  const type = completed || failed ? "turn.completed" : started ? "turn.started" : "session.started";
  const base = {
    eventId: `seq-${event.seq}`,
    provider: "harness",
    threadId,
    createdAt: event.t,
    turnId: event.handleId,
    raw: { source: "protocol.jsonl", payload: event },
    type,
  };
  if (type === "turn.completed") {
    return { ...base, ok: !failed, stopReason: event.status ?? event.type };
  }
  if (type === "session.started") {
    return { ...base, sessionId: event.handleId ?? null, model: null };
  }
  return base;
}

export function inspectorPage(computerRoot: string, threadId: string, limit: number): Record<string, unknown> {
  const roster = loadRoster(computerRoot);
  const bot = findBot(roster, threadId) ?? (threadId.startsWith("room-") ? undefined : findBot(roster, threadId));
  const roomId = threadId.startsWith("room-") ? threadId.slice("room-".length) : threadId.startsWith("room:") ? threadId.slice("room:".length) : undefined;
  const protocol = bot
    ? searchProtocol(computerRoot, "", bot.id).concat(searchProtocol(computerRoot, "", bot.slug))
    : roomId
      ? readProtocol(computerRoot).filter((event) => event.roomId === roomId)
      : readProtocol(computerRoot);
  const unique = new Map<number, ProtocolEvent>();
  for (const event of protocol) {
    unique.set(event.seq, event);
  }
  const events = [...unique.values()].sort((a, b) => a.seq - b.seq);
  const runtime = events.slice(-limit).map((event) => ({
    kind: "runtime" as const,
    at: event.t,
    data: runtimeEntry(event, threadId),
  }));
  const piRuntime = bot
    ? readJsonl(piRuntimePath(computerRoot, bot.id)).flatMap((row) => {
        if (!isRecord(row) || typeof row.type !== "string") {
          return [];
        }
        const createdAt = typeof row.createdAt === "string" ? row.createdAt : new Date().toISOString();
        return [
          {
            kind: "runtime" as const,
            at: createdAt,
            data: { threadId, provider: "pi", ...row },
          },
        ];
      })
    : [];
  const native = bot
    ? [
        ...readTranscript(computerRoot, bot.id, limit).map((row) => ({
          kind: "native" as const,
          at: row.t,
          data: {
            at: row.t,
            dir: row.from === "operator" || row.kind === "user_dm" ? "in" : "out",
            source: "transcript.jsonl",
            msg: row,
          },
        })),
        ...readJsonl(piRpcLogPath(computerRoot, bot.id)).flatMap((row) => {
          if (!isRecord(row)) {
            return [];
          }
          const at = typeof row.timestamp === "number" ? new Date(row.timestamp).toISOString() : new Date().toISOString();
          return [
            {
              kind: "native" as const,
              at,
              data: {
                at,
                dir: "in" as const,
                source: "pi-rpc.jsonl",
                msg: row,
              },
            },
          ];
        }),
      ]
    : [];
  const mergedRuntime = [...runtime, ...piRuntime].slice(-limit);
  return {
    entries: [...mergedRuntime, ...native].sort((a, b) => a.at.localeCompare(b.at)).slice(-limit),
    total: { runtime: runtime.length + piRuntime.length, native: native.length },
  };
}

function snippetHit(
  hay: string,
  needle: string,
): { readonly snippet: string; readonly matchStart: number; readonly matchLength: number } {
  const lower = hay.toLowerCase();
  const at = lower.indexOf(needle);
  const start = Math.max(0, at - 40);
  const snippet = hay.slice(start, start + 160);
  return {
    snippet,
    matchStart: at < 0 ? 0 : at - start,
    matchLength: needle.length,
  };
}

export function deskSearch(computerRoot: string, query: string, limit: number): { readonly hits: readonly Record<string, unknown>[] } {
  const roster = loadRoster(computerRoot);
  const needle = query.trim().toLowerCase();
  const hits: Record<string, unknown>[] = [];
  if (needle.length === 0) {
    return { hits };
  }
  for (const bot of searchAgents(computerRoot, query)) {
    const record = findBot(roster, bot.id);
    if (!record) {
      continue;
    }
    const hay = `${record.name} ${record.slug} ${record.purpose}`;
    const clip = snippetHit(hay, needle);
    hits.push({
      botId: record.id,
      name: record.name,
      threadId: record.id,
      messageId: `bot-${record.id}`,
      role: "bot",
      kind: "text",
      from: record.name,
      at: Date.now(),
      snippet: clip.snippet,
      matchStart: clip.matchStart,
      matchLength: clip.matchLength,
      onActivePath: true,
    });
    if (hits.length >= limit) {
      return { hits };
    }
  }
  for (const event of searchProtocol(computerRoot, query)) {
    const hay = `${event.type} ${event.text ?? ""} ${event.from ?? ""} ${event.to ?? ""}`;
    const clip = snippetHit(hay, needle);
    const owner = findBot(roster, event.to ?? "") ?? findBot(roster, event.from ?? "") ?? findBot(roster, event.slug ?? "");
    const roomId = event.roomId;
    hits.push({
      botId: owner?.id,
      groupId: roomId,
      name: owner?.name ?? roomId ?? "protocol",
      threadId: roomId ? `room-${roomId}` : owner?.id ?? "protocol",
      messageId: event.handleId ?? `seq-${event.seq}`,
      role: event.from === "operator" ? "user" : "bot",
      kind: "text",
      from: event.from,
      at: epoch(event.t),
      snippet: clip.snippet,
      matchStart: clip.matchStart,
      matchLength: clip.matchLength,
      onActivePath: true,
    });
    if (hits.length >= limit) {
      break;
    }
  }
  return { hits };
}

function memberSlugs(roster: Roster, memberIds: readonly string[]): string[] {
  const slugs: string[] = [];
  for (const key of memberIds) {
    const bot = findBot(roster, key);
    if (bot && !slugs.includes(bot.slug)) {
      slugs.push(bot.slug);
    }
  }
  return slugs;
}

function wireGroup(_computerRoot: string, roster: Roster, roomId: string): Record<string, unknown> | undefined {
  const room = findRoom(roster, roomId);
  if (!room) {
    return undefined;
  }
  const ids: string[] = [];
  for (const member of room.members) {
    const bot = findBot(roster, member);
    if (bot) {
      ids.push(bot.id);
    }
  }
  return {
    id: room.id,
    threadId: `room-${room.id}`,
    name: room.title,
    memberIds: ids,
    defaultResponder: { kind: "everyone" },
    bulletin: "",
    unread: false,
    createdAt: Date.now(),
    messages: [],
    setupCompletedAt: Date.now(),
  };
}

function connectorCards(computerRoot: string): readonly Record<string, unknown>[] {
  const roster = loadRoster(computerRoot);
  const config = loadOperatorConfig();
  const base: Record<string, { label: string; blurb: string; domain: string }> = {
    anthropic: { label: "Anthropic", blurb: "Claude API key. Paste it in Settings → Connections.", domain: "anthropic.com" },
    openai: { label: "OpenAI-compatible", blurb: "OpenAI or a compatible base URL. Paste the key in Settings.", domain: "openai.com" },
    xai: { label: "xAI", blurb: "Grok API key. Paste it in Settings → Connections.", domain: "x.ai" },
    google: { label: "Google", blurb: "Gemini API key for Pi's Google provider.", domain: "google.com" },
  };
  const extra = new Set<string>();
  for (const bot of roster.bots) {
    for (const name of bot.connectors) {
      extra.add(name);
    }
  }
  const cards: Record<string, unknown>[] = [];
  for (const [slug, meta] of Object.entries(base)) {
    cards.push({
      slug,
      label: meta.label,
      blurb: meta.blurb,
      logo: null,
      noAuth: false,
      domain: meta.domain,
      connected: keyConfigured(config, slug === "openai" ? "openaiCompat" : slug),
    });
  }
  for (const slug of extra) {
    if (base[slug]) {
      continue;
    }
    cards.push({
      slug,
      label: slug,
      blurb: "Named on the Roster as a Bot connector. Client extensions honor this grant.",
      logo: null,
      noAuth: true,
      domain: null,
    });
  }
  return cards;
}

function connectorServices(computerRoot: string, slugs?: readonly string[]): Record<string, unknown> {
  const config = loadOperatorConfig();
  const roster = loadRoster(computerRoot);
  const granted = new Set<string>();
  for (const bot of roster.bots) {
    for (const name of bot.connectors) {
      granted.add(name);
    }
  }
  const all = slugs && slugs.length > 0 ? slugs : ["anthropic", "openai", "xai", "google", ...granted];
  const services: Record<string, unknown> = {};
  for (const slug of all) {
    const connected =
      keyConfigured(config, slug === "openai" ? "openaiCompat" : slug) || granted.has(slug);
    services[slug] = {
      connected,
      pending: false,
      status: connected ? "connected" : "not_connected",
      accounts: connected ? [{ id: slug, alias: slug, status: "ACTIVE" }] : [],
    };
  }
  return services;
}

function commsBody(computerRoot: string): Record<string, unknown> {
  const manifest = loadExtensionsManifest(computerRoot);
  const extra = collectExtraExtensionPaths({ computerRoot, config: loadOperatorConfig() });
  return {
    computerRoot,
    roster: rosterPath(computerRoot),
    protocol: protocolLogPath(computerRoot),
    bots: "harness/bots/<botId>/{inbox.jsonl,handles/*.json,transcript.jsonl,pi-session/*.jsonl,pi-rpc.jsonl,memory/}",
    rooms: "harness/rooms/<roomId>/log.jsonl",
    intercept: "harness/intercept.json",
    extensions: "harness/extensions.json",
    operatorConfig: operatorConfigPath(),
    extraExtensions: extra,
    clientSkills: manifest.clientSkills || loadOperatorConfig().clientSkills,
  };
}

function deleteBot(ctx: ApiContext, key: string): DeskResult {
  const roster = loadRoster(ctx.computerRoot);
  const bot = findBot(roster, key);
  if (!bot) {
    return { status: 404, body: { error: "no such bot" } };
  }
  if (roster.bots.length <= 1) {
    return { status: 409, body: { error: "roster must keep at least one Bot" } };
  }
  const rooms = roster.rooms
    .map((room) => ({
      ...room,
      members: room.members.filter((member) => member !== bot.slug && member !== bot.id),
    }))
    .filter((room) => room.members.length >= 2 && room.members.length <= 6);
  const next: Roster = {
    ...roster,
    bots: roster.bots.filter((row) => row.id !== bot.id),
    rooms,
    routines: roster.routines.filter((row) => row.bot !== bot.slug && row.bot !== bot.id),
  };
  saveRoster(ctx.computerRoot, next);
  initComputer(ctx.computerRoot, next);
  ctx.supervisor?.stopBot(bot.slug);
  publishHello(ctx);
  return { status: 200, body: { ok: true, id: bot.id } };
}

function upsertRoutine(ctx: ApiContext, body: unknown, existingName?: string): DeskResult {
  if (!isRecord(body)) {
    return { status: 400, body: { error: "object required" } };
  }
  const roster = loadRoster(ctx.computerRoot);
  const name = (asString(body.name) ?? existingName ?? "").trim();
  if (name.length === 0) {
    return { status: 400, body: { error: "name required" } };
  }
  const botKey = asString(body.botId) ?? asString(body.bot) ?? "";
  const owner = findBot(roster, botKey);
  if (!owner) {
    return { status: 400, body: { error: "botId required" } };
  }
  const cadence = asString(body.cadence) ?? cadenceFromSchedule(body.schedule);
  const prompt = asString(body.prompt) ?? "";
  const conversation =
    asString(body.conversation) ??
    (typeof body.groupId === "string" && body.groupId.length > 0 ? `room:${body.groupId}` : "operator_dm");
  const record: RoutineRecord = {
    name,
    bot: owner.slug,
    cadence,
    prompt,
    conversation,
  };
  const without = roster.routines.filter((row) => row.name !== (existingName ?? name) && row.name !== name);
  const next: Roster = { ...roster, routines: [...without, record] };
  saveRoster(ctx.computerRoot, next);
  publishHello(ctx);
  return { status: 200, body: { ok: true, routine: wireRoutine(next, record) } };
}

function firstNonEmptyLine(text: string): string {
  return (
    text
      .split("\n")
      .map((row) => row.trim())
      .find((row) => row.length > 0) ?? ""
  );
}

function botOverviewBody(computerRoot: string, bot: BotRecord, roster: Roster): Record<string, unknown> {
  const seen = new Set<number>();
  const recent = searchProtocol(computerRoot, "", bot.id)
    .concat(searchProtocol(computerRoot, "", bot.slug))
    .filter((event) => {
      if (seen.has(event.seq)) {
        return false;
      }
      seen.add(event.seq);
      return true;
    })
    .sort((left, right) => right.seq - left.seq)
    .slice(0, 8)
    .map((event) => ({
      at: epoch(event.t),
      summary: [event.type, event.from, event.to, event.text].filter((part) => Boolean(part)).join(" · ").slice(0, 160),
    }));
  const rooms = roster.rooms.filter((room) => room.members.includes(bot.id) || room.members.includes(bot.slug));
  const config = loadOperatorConfig();
  const hasKey =
    keyConfigured(config, "anthropic") ||
    keyConfigured(config, "openai") ||
    keyConfigured(config, "xai") ||
    keyConfigured(config, "google");
  const hasRoutine = roster.routines.some((row) => row.bot === bot.id || row.bot === bot.slug);
  return {
    who: {
      name: bot.name,
      title: bot.purpose.length > 0 ? bot.purpose : bot.slug,
      blurb: bot.purpose,
      soulLead: firstNonEmptyLine(bot.instructions),
    },
    does: [
      bot.purpose,
      bot.skills.length > 0 ? `skills: ${bot.skills.join(", ")}` : "",
      bot.connectors.length > 0 ? `connectors: ${bot.connectors.join(", ")}` : "",
    ].filter((row) => row.length > 0),
    reaches: rooms.map((room) => room.title),
    wont:
      bot.approvalLevel === "never"
        ? ["will not run consequential tools"]
        : bot.approvalLevel === "ask"
          ? ["pauses for Operator or Verifier on consequential tools"]
          : [],
    recent,
    setup: [
      {
        id: "identity",
        label: "Name and purpose on roster.json",
        done: bot.name.trim().length > 0 && bot.purpose.trim().length > 0,
        section: "identity",
      },
      {
        id: "soul",
        label: "Standing instructions",
        done: bot.instructions.trim().length > 0,
        section: "identity",
      },
      {
        id: "folder",
        label: "Computer is the shared workspace",
        done: true,
        section: "identity",
      },
      { id: "apps", label: "Operator API key", done: hasKey },
      { id: "schedule", label: "At least one Routine", done: hasRoutine, section: "routines" },
    ],
  };
}

function promptPreviewBody(computerRoot: string, bot: BotRecord, roster: Roster): Record<string, unknown> {
  const identity = identityBlock(bot, roster);
  const memory = memorySection(computerRoot, bot.id);
  const recent = recentWorkSection(computerRoot, bot.id);
  const sections = [
    { id: "identity", label: "Identity", text: identity, bytes: Buffer.byteLength(identity) },
    ...(memory.length > 0
      ? [{ id: "memory", label: "Memory", text: memory, bytes: Buffer.byteLength(memory) }]
      : []),
    ...(recent.length > 0
      ? [{ id: "recent", label: "Recent work", text: recent, bytes: Buffer.byteLength(recent) }]
      : []),
  ];
  const totalBytes = sections.reduce((sum, section) => sum + section.bytes, 0);
  return {
    sections,
    totalBytes,
    approxTokens: Math.max(1, Math.round(totalBytes / 4)),
    note: "Harness identity block plus this Bot's Memory and recent work.",
  };
}

function memoryJournalBody(computerRoot: string, botId: string): { readonly entries: readonly Record<string, unknown>[] } {
  const overview = listMemoryOverview(computerRoot, botId);
  const files = [...overview.topics, ...overview.logs];
  return {
    entries: files.map((file) => ({
      id: file.path,
      at: file.modifiedAt,
      botId,
      path: file.path,
      actor: "bot",
      via: "file",
      kind: "edited",
      beforeHash: null,
      afterHash: null,
      diff: "",
      added: 0,
      removed: 0,
      canRevert: false,
      revertUnavailableReason: "Harness stores Memory as files, not a revert journal",
    })),
  };
}

export function handleDeskCompat(
  method: string,
  path: string,
  url: URL,
  body: unknown,
  ctx: ApiContext,
): DeskResult | undefined {
  const computerRoot = ctx.computerRoot;

  if (method === "GET" && path === "/api/comms") {
    return { status: 200, body: commsBody(computerRoot) };
  }

  if (method === "GET" && path === "/api/intercept") {
    return { status: 200, body: loadIntercept(computerRoot) };
  }

  if ((method === "PUT" || method === "PATCH") && path === "/api/intercept") {
    const parsed = parseIntercept(body);
    saveIntercept(computerRoot, parsed);
    return { status: 200, body: parsed };
  }

  if (method === "GET" && path === "/api/search") {
    const q = url.searchParams.get("q") ?? url.searchParams.get("query") ?? "";
    const limit = Number(url.searchParams.get("limit") ?? "40");
    return { status: 200, body: deskSearch(computerRoot, q, Number.isFinite(limit) ? limit : 40) };
  }

  if (method === "GET" && path === "/api/cli-candidates") {
    const candidates = ["/opt/homebrew/bin/pi", "/usr/local/bin/pi", "/opt/homebrew/bin/claude"].filter((item) =>
      existsSync(item),
    );
    return { status: 200, body: { candidates } };
  }

  const instancePatch = /^\/api\/instances\/([^/]+)$/.exec(path);
  if (instancePatch && method === "PATCH") {
    if (!isRecord(body)) {
      return { status: 400, body: { error: "object required" } };
    }
    const patch: Record<string, unknown> = {};
    if (typeof body.model === "string") {
      patch.model = body.model;
    }
    if (typeof body.provider === "string") {
      patch.provider = body.provider;
    }
    if (Object.keys(patch).length > 0) {
      patchOperatorConfig(patch);
    }
    return { status: 200, body: { ok: true } };
  }

  if (method === "POST" && path === "/api/keys/test") {
    if (!isRecord(body)) {
      return { status: 400, body: { error: "object required" } };
    }
    const provider = asString(body.provider) ?? "anthropic";
    const draft = asString(body.key) ?? "";
    if (draft.length > 0) {
      if (draft.length < 8) {
        return { status: 200, body: { ok: false, message: "key looks too short" } };
      }
      return {
        status: 200,
        body: {
          ok: false,
          message: "Test does not save and does not call the provider. Save the key, then Test checks that a key is stored.",
        },
      };
    }
    const stored = keyConfigured(loadOperatorConfig(), provider);
    return {
      status: 200,
      body: {
        ok: stored,
        message: stored
          ? "a key is stored for this provider (secret not echoed; not a live API call)"
          : "no key stored for this provider",
      },
    };
  }

  const threadEvents = /^\/api\/threads\/([^/]+)\/events$/.exec(path);
  if (threadEvents && method === "GET") {
    const threadId = decodeURIComponent(threadEvents[1] ?? "");
    const limit = Number(url.searchParams.get("limit") ?? "400");
    return { status: 200, body: inspectorPage(computerRoot, threadId, Number.isFinite(limit) ? limit : 400) };
  }

  if (method === "GET" && path === "/api/connectors/catalog") {
    return {
      status: 200,
      body: {
        cards: connectorCards(computerRoot),
        source: "harness",
        configured: true,
        mode: "self-hosted",
      },
    };
  }

  if (method === "GET" && path === "/api/connectors/connected") {
    return {
      status: 200,
      body: { services: connectorServices(computerRoot), credentialStore: "operator-config", authoritative: true },
    };
  }

  if (method === "GET" && path === "/api/connectors") {
    const services = url.searchParams.get("services") ?? "";
    const slugs = services.split(",").map((item) => item.trim()).filter((item) => item.length > 0);
    return { status: 200, body: { services: connectorServices(computerRoot, slugs) } };
  }

  const authorize = /^\/api\/connectors\/([^/]+)\/authorize$/.exec(path);
  if (authorize && method === "POST") {
    return {
      status: 400,
      body: { error: "Harness connectors are API keys. Paste the key in Settings → Connections." },
    };
  }

  if (method === "GET" && path === "/api/routines") {
    const roster = loadRoster(computerRoot);
    return {
      status: 200,
      body: {
        routines: roster.routines.map((row) => wireRoutine(roster, row)),
        runs: listReceipts(computerRoot).map((row) => wireRun(roster, row)),
      },
    };
  }

  if (method === "POST" && path === "/api/routines") {
    return upsertRoutine(ctx, body);
  }

  const routineOne = /^\/api\/routines\/([^/]+)$/.exec(path);
  if (routineOne) {
    const name = decodeURIComponent(routineOne[1] ?? "");
    if (method === "PATCH") {
      return upsertRoutine(ctx, isRecord(body) ? { ...body, name: asString(body.name) ?? name } : { name }, name);
    }
    if (method === "DELETE") {
      const roster = loadRoster(computerRoot);
      const next: Roster = { ...roster, routines: roster.routines.filter((row) => row.name !== name) };
      saveRoster(computerRoot, next);
      publishHello(ctx);
      return { status: 200, body: { ok: true } };
    }
  }

  if (method === "POST" && path === "/api/groups") {
    if (!isRecord(body) || !Array.isArray(body.memberIds)) {
      return { status: 400, body: { error: "memberIds required" } };
    }
    const roster = loadRoster(computerRoot);
    const members = memberSlugs(roster, body.memberIds.filter((item): item is string => typeof item === "string"));
    if (members.length < 2 || members.length > 6) {
      return { status: 400, body: { error: "a Room has 2–6 members" } };
    }
    const title = asString(body.name) ?? members.join(" · ");
    const id = slugify(asString(body.id) ?? title, `room-${members[0] ?? "floor"}`);
    if (findRoom(roster, id)) {
      return { status: 409, body: { error: "room exists" } };
    }
    const next: Roster = { ...roster, rooms: [...roster.rooms, { id, title, members }] };
    saveRoster(computerRoot, next);
    initComputer(computerRoot, next);
    publishHello(ctx);
    return { status: 200, body: { group: wireGroup(computerRoot, next, id) } };
  }

  const groupOne = /^\/api\/groups\/([^/]+)$/.exec(path);
  if (groupOne) {
    const roomId = decodeURIComponent(groupOne[1] ?? "");
    if (isPairChannelId(roomId)) {
      return undefined;
    }
    const roster = loadRoster(computerRoot);
    const room = findRoom(roster, roomId);
    if (!room) {
      return { status: 404, body: { error: "no such group" } };
    }
    if (method === "PATCH" && isRecord(body)) {
      const members = Array.isArray(body.memberIds)
        ? memberSlugs(roster, body.memberIds.filter((item): item is string => typeof item === "string"))
        : [...room.members];
      if (members.length < 2 || members.length > 6) {
        return { status: 400, body: { error: "a Room has 2–6 members" } };
      }
      const title = asString(body.name) ?? room.title;
      const nextRooms = roster.rooms.map((row) => (row.id === room.id ? { ...row, title, members } : row));
      const next: Roster = { ...roster, rooms: nextRooms };
      saveRoster(computerRoot, next);
      publishHello(ctx);
      return { status: 200, body: { group: wireGroup(computerRoot, next, room.id) } };
    }
    if (method === "DELETE") {
      const next: Roster = { ...roster, rooms: roster.rooms.filter((row) => row.id !== room.id) };
      saveRoster(computerRoot, next);
      publishHello(ctx);
      return { status: 200, body: { ok: true } };
    }
  }

  if (method === "POST" && path === "/api/rooms") {
    return handleDeskCompat("POST", "/api/groups", url, body, ctx);
  }

  const botSkill = /^\/api\/bots\/([^/]+)\/skills(?:\/([^/]+))?$/.exec(path);
  if (botSkill) {
    const key = decodeURIComponent(botSkill[1] ?? "");
    const skillName = botSkill[2] ? decodeURIComponent(botSkill[2]) : undefined;
    const roster = loadRoster(computerRoot);
    const bot = findBot(roster, key);
    if (!bot) {
      return { status: 404, body: { error: "no such bot" } };
    }
    if (method === "GET" && !skillName) {
      return { status: 200, body: listBotSkills(computerRoot, bot) };
    }
    if (method === "GET" && skillName) {
      const file = join(computerSkillsRoot(computerRoot), skillName, "SKILL.md");
      if (!existsSync(file)) {
        return { status: 404, body: { error: "no such skill file" } };
      }
      return { status: 200, body: { text: readFileSync(file, "utf8") } };
    }
    if (method === "PATCH" && skillName) {
      const enabled = isRecord(body) ? body.enabled !== false : true;
      const next = setSkillEnabled(computerRoot, bot, skillName, enabled);
      publishHello(ctx);
      return { status: 200, body: { ok: true, skills: listBotSkills(computerRoot, next).skills } };
    }
    if (method === "DELETE" && skillName) {
      const next = setSkillEnabled(computerRoot, bot, skillName, false);
      publishHello(ctx);
      return { status: 200, body: { ok: true, skills: listBotSkills(computerRoot, next).skills } };
    }
    if (method === "POST" && !skillName) {
      const source = isRecord(body) ? asString(body.source) ?? asString(body.name) ?? "" : "";
      const name = slugify(source.split("/").filter(Boolean).at(-1) ?? source, "");
      if (name.length === 0) {
        return { status: 400, body: { error: "source required" } };
      }
      if (source.startsWith("http://") || source.startsWith("https://")) {
        return {
          status: 400,
          body: { error: "copy the skill into Computer/skills/<name>/SKILL.md, then enable it here" },
        };
      }
      const dir = join(computerSkillsRoot(computerRoot), name);
      if (!existsSync(join(dir, "SKILL.md"))) {
        return { status: 404, body: { error: `no SKILL.md at skills/${name}` } };
      }
      const next = setSkillEnabled(computerRoot, bot, name, true);
      publishHello(ctx);
      return { status: 200, body: { installed: [{ name }], skills: listBotSkills(computerRoot, next).skills } };
    }
  }

  const botOverview = /^\/api\/bots\/([^/]+)\/overview$/.exec(path);
  if (botOverview && method === "GET") {
    const key = decodeURIComponent(botOverview[1] ?? "");
    const roster = loadRoster(computerRoot);
    const bot = findBot(roster, key);
    if (!bot) {
      return { status: 404, body: { error: "no such bot" } };
    }
    return { status: 200, body: botOverviewBody(computerRoot, bot, roster) };
  }

  const botPrompt = /^\/api\/bots\/([^/]+)\/system-prompt$/.exec(path);
  if (botPrompt && method === "GET") {
    const key = decodeURIComponent(botPrompt[1] ?? "");
    const roster = loadRoster(computerRoot);
    const bot = findBot(roster, key);
    if (!bot) {
      return { status: 404, body: { error: "no such bot" } };
    }
    return { status: 200, body: promptPreviewBody(computerRoot, bot, roster) };
  }

  const botJournal = /^\/api\/bots\/([^/]+)\/memory\/journal$/.exec(path);
  if (botJournal && method === "GET") {
    const key = decodeURIComponent(botJournal[1] ?? "");
    const roster = loadRoster(computerRoot);
    const bot = findBot(roster, key);
    if (!bot) {
      return { status: 404, body: { error: "no such bot" } };
    }
    return { status: 200, body: memoryJournalBody(computerRoot, bot.id) };
  }

  const botOpen = /^\/api\/bots\/([^/]+)\/memory\/open$/.exec(path);
  if (botOpen && method === "POST") {
    const key = decodeURIComponent(botOpen[1] ?? "");
    const roster = loadRoster(computerRoot);
    const bot = findBot(roster, key);
    if (!bot) {
      return { status: 404, body: { error: "no such bot" } };
    }
    return { status: 200, body: { ok: true, workspacePath: listMemoryOverview(computerRoot, bot.id).workspacePath } };
  }

  const botMemory = /^\/api\/bots\/([^/]+)\/memory(?:\/file)?$/.exec(path);
  if (botMemory) {
    const key = decodeURIComponent(botMemory[1] ?? "");
    const roster = loadRoster(computerRoot);
    const bot = findBot(roster, key);
    if (!bot) {
      return { status: 404, body: { error: "no such bot" } };
    }
    if (method === "GET" && !path.endsWith("/file") && !url.searchParams.get("path")) {
      return { status: 200, body: listMemoryOverview(computerRoot, bot.id) };
    }
    const rel = url.searchParams.get("path") ?? (isRecord(body) ? asString(body.path) : undefined) ?? "MEMORY.md";
    if (method === "GET") {
      return { status: 200, body: readMemoryDoc(computerRoot, bot.id, rel) };
    }
    if (method === "PUT" || method === "POST") {
      if (!isRecord(body) || typeof body.text !== "string") {
        return { status: 400, body: { error: "text required" } };
      }
      const expected = typeof body.expectedHash === "string" ? body.expectedHash : undefined;
      const written = writeMemoryDoc(computerRoot, bot.id, rel, body.text, expected);
      if (!written.ok) {
        return { status: 409, body: written };
      }
      return {
        status: 200,
        body: {
          ok: true,
          path: written.doc.path,
          text: written.doc.text,
          hash: written.doc.hash,
          exists: written.doc.exists,
          doc: written.doc,
          overview: written.overview,
        },
      };
    }
    if (method === "DELETE") {
      return { status: 400, body: { error: "edit the Memory file instead of deleting it" } };
    }
  }

  const botRoot = /^\/api\/bots\/([^/]+)$/.exec(path);
  if (botRoot && method === "DELETE") {
    return deleteBot(ctx, decodeURIComponent(botRoot[1] ?? ""));
  }

  if ((method === "PUT" || method === "PATCH") && path === "/api/attach") {
    if (!isRecord(body)) {
      return { status: 400, body: { error: "object required" } };
    }
    const extra = Array.isArray(body.extraExtensions)
      ? body.extraExtensions.filter((item): item is string => typeof item === "string")
      : typeof body.extraExtensions === "string"
        ? body.extraExtensions.split("\n").map((item) => item.trim()).filter((item) => item.length > 0)
        : undefined;
    if (extra) {
      patchOperatorConfig({ extraExtensions: extra });
    }
    if (typeof body.clientSkills === "boolean") {
      patchOperatorConfig({ clientSkills: body.clientSkills });
    }
    if (extra || typeof body.clientSkills === "boolean") {
      const next = loadOperatorConfig();
      saveExtensionsManifest(computerRoot, {
        extraExtensions: extra ?? [...next.extraExtensions],
        clientSkills: typeof body.clientSkills === "boolean" ? body.clientSkills : next.clientSkills,
      });
    }
    return { status: 200, body: { ...publicOperatorConfig(), extra: collectExtraExtensionPaths({ computerRoot, config: loadOperatorConfig() }) } };
  }

  if (method === "GET" && path === "/api/demo/meta") {
    return { status: 200, body: demoMeta(computerRoot, parseDemoSourceQuery(url.searchParams.get("source"))) };
  }

  if (method === "GET" && path === "/api/demo/frame") {
    try {
      const bundle = loadDemoBundle(computerRoot, parseDemoSourceQuery(url.searchParams.get("source")));
      const seq = Number(url.searchParams.get("seq") ?? "0");
      return { status: 200, body: projectFrame(bundle, Number.isFinite(seq) ? seq : 0) };
    } catch (cause) {
      if (cause instanceof DemoRecordingMissingError) {
        return { status: 404, body: { error: cause.message } };
      }
      throw cause;
    }
  }

  if (method === "GET" && path === "/api/demo") {
    try {
      return { status: 200, body: loadDemoBundle(computerRoot, parseDemoSourceQuery(url.searchParams.get("source"))) };
    } catch (cause) {
      if (cause instanceof DemoRecordingMissingError) {
        return { status: 404, body: { error: cause.message } };
      }
      throw cause;
    }
  }

  if (method === "POST" && path === "/api/demo/record") {
    return { status: 200, body: recordDemoSession(computerRoot) };
  }

  if (method === "DELETE" && path === "/api/demo/record") {
    return { status: 200, body: { ok: removeDemoRecording(computerRoot) } };
  }

  return undefined;
}

/**
 * Saved office desks: named Computer snapshots beside the live sky/grass tree.
 * office.json lives next to computer/, never inside harness/.
 */
import {
  copyFileSync,
  cpSync,
  existsSync,
  lstatSync,
  mkdirSync,
  readdirSync,
  readlinkSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { basename, dirname, join, relative, resolve, sep } from "node:path";

import { initComputer } from "../computer.ts";
import { loadLayout } from "../layout.ts";
import { instanceGroup } from "../sandbox.ts";
import { readJsonIfExists, writeJsonAtomic } from "../fs.ts";
import { nowIso, shortNonce } from "../ids.ts";
import { wipeRuntime } from "../wipe.ts";

export const LIVE_INSTANCE_ID = "live";
export const LIVE_INSTANCE_NAME = "Live";

const TEMPLATE_HARNESS_FILES = [
  "roster.json",
  "client.json",
  "intercept.json",
  "extensions.json",
  "layout.json",
] as const;

export interface OfficeInstanceRecord {
  readonly id: string;
  readonly name: string;
  readonly computerRel: string;
  readonly createdAt: string;
}

export interface OfficeState {
  readonly currentId: string;
  readonly instances: readonly OfficeInstanceRecord[];
}

export interface OfficeInstanceResult {
  readonly office: OfficeState;
  readonly instance: OfficeInstanceRecord;
  readonly computerRoot: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function posixRel(from: string, to: string): string {
  const rel = relative(from, resolve(to));
  const normalized = rel.split(sep).join("/");
  return normalized.length > 0 ? normalized : ".";
}

export function officeJsonPath(officeParent: string): string {
  return join(officeParent, "office.json");
}

function officeListsComputer(officeParent: string, computerRoot: string): boolean {
  const state = readOffice(officeParent);
  if (!state) {
    return false;
  }
  const resolved = resolve(computerRoot);
  return state.instances.some((row) => resolve(officeParent, row.computerRel) === resolved);
}

function findListingOffice(computerRoot: string): string | undefined {
  const resolved = resolve(computerRoot);
  let dir = dirname(resolved);
  for (let hop = 0; hop < 8; hop += 1) {
    if (existsSync(join(dir, "office.json")) && officeListsComputer(dir, resolved)) {
      return dir;
    }
    const parent = dirname(dir);
    if (parent === dir) {
      break;
    }
    dir = parent;
  }
  return undefined;
}

/**
 * Office metadata sits beside computer/ when the live tree uses that name.
 * Instance roots under instances/<id> still resolve to the same parent.
 * This Computer keeps one registry. A parent .cfo-v2/office is not that registry.
 * Any other Computer (tests, odd --computer paths) uses a .office folder
 * inside that tree so office.json does not leak into /tmp.
 */
export function resolveOfficeParent(computerRoot: string): string {
  const resolved = resolve(computerRoot);
  const listed = findListingOffice(resolved);
  if (listed) {
    return listed;
  }
  const parent = dirname(resolved);
  if (basename(resolved) === "computer" || resolve(parent, "computer") === resolved) {
    return parent;
  }
  if (existsSync(join(parent, "office.json"))) {
    return parent;
  }
  const grand = dirname(parent);
  if (basename(parent) === "instances" && existsSync(join(grand, "office.json"))) {
    return grand;
  }
  return join(resolved, ".office");
}

function parseInstance(value: unknown): OfficeInstanceRecord | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const id = typeof value.id === "string" ? value.id.trim() : "";
  const name = typeof value.name === "string" ? value.name.trim() : "";
  const computerRel = typeof value.computerRel === "string" ? value.computerRel.trim() : "";
  const createdAt = typeof value.createdAt === "string" ? value.createdAt : "";
  if (id.length === 0 || name.length === 0 || computerRel.length === 0) {
    return undefined;
  }
  return {
    id,
    name,
    computerRel,
    createdAt: createdAt.length > 0 ? createdAt : nowIso(),
  };
}

function parseOfficeState(value: unknown): OfficeState | undefined {
  if (!isRecord(value) || !Array.isArray(value.instances)) {
    return undefined;
  }
  const instances = value.instances
    .map(parseInstance)
    .filter((row): row is OfficeInstanceRecord => row !== undefined);
  if (instances.length === 0) {
    return undefined;
  }
  const currentId = typeof value.currentId === "string" ? value.currentId : "";
  const known = instances.some((row) => row.id === currentId);
  return {
    currentId: known ? currentId : (instances[0]?.id ?? LIVE_INSTANCE_ID),
    instances,
  };
}

function liveRecord(officeParent: string, liveRoot: string): OfficeInstanceRecord {
  return {
    id: LIVE_INSTANCE_ID,
    name: LIVE_INSTANCE_NAME,
    computerRel: posixRel(officeParent, liveRoot),
    createdAt: nowIso(),
  };
}

function saveOffice(officeParent: string, office: OfficeState): void {
  writeJsonAtomic(officeJsonPath(officeParent), office);
}

function readOffice(officeParent: string): OfficeState | undefined {
  return parseOfficeState(readJsonIfExists(officeJsonPath(officeParent)));
}

function withLiveInstance(officeParent: string, liveRoot: string, office: OfficeState): OfficeState {
  const livePath = resolve(liveRoot);
  const existingLive = office.instances.find((row) => row.id === LIVE_INSTANCE_ID);
  if (existingLive && resolve(officeParent, existingLive.computerRel) === livePath) {
    return office;
  }
  const matching = office.instances.find((row) => resolve(officeParent, row.computerRel) === livePath);
  if (matching) {
    return office;
  }
  const live = existingLive
    ? { ...existingLive, computerRel: posixRel(officeParent, liveRoot) }
    : liveRecord(officeParent, liveRoot);
  const instances = existingLive
    ? office.instances.map((row) => (row.id === LIVE_INSTANCE_ID ? live : row))
    : [live, ...office.instances];
  return { ...office, instances };
}

/**
 * First load creates office.json pointing at the existing computer/ tree.
 * Never moves or copies that live Computer.
 */
export function ensureOfficeState(computerRoot: string): OfficeState {
  const liveRoot = resolve(computerRoot);
  const officeParent = resolveOfficeParent(liveRoot);
  const existing = readOffice(officeParent);
  if (!existing) {
    const live = liveRecord(officeParent, liveRoot);
    const created: OfficeState = { currentId: LIVE_INSTANCE_ID, instances: [live] };
    saveOffice(officeParent, created);
    return created;
  }
  const withLive = withLiveInstance(officeParent, liveRoot, existing);
  const running = withLive.instances.find((row) => resolve(officeParent, row.computerRel) === liveRoot);
  const currentKnown = withLive.instances.some((row) => row.id === withLive.currentId);
  const next: OfficeState = {
    currentId: currentKnown ? withLive.currentId : (running?.id ?? LIVE_INSTANCE_ID),
    instances: withLive.instances,
  };
  if (
    next.currentId !== existing.currentId ||
    next.instances.length !== existing.instances.length ||
    next.instances.some((row, index) => {
      const prev = existing.instances[index];
      return !prev || prev.id !== row.id || prev.computerRel !== row.computerRel;
    })
  ) {
    saveOffice(officeParent, next);
  }
  return next;
}

export function listOfficeState(computerRoot: string): OfficeState {
  return ensureOfficeState(computerRoot);
}

/** Public office payload for GET /api/bots and SSE switch frames. */
export function officePublicState(computerRoot: string): {
  readonly currentId: string;
  readonly group: string;
  readonly instances: readonly (OfficeInstanceRecord & { readonly group: string })[];
  readonly groups: readonly string[];
  readonly computerRoot: string;
} {
  const office = listOfficeState(computerRoot);
  const officeParent = resolveOfficeParent(computerRoot);
  const instances = office.instances.map((row) => {
    const root = instanceComputerRoot(officeParent, row);
    return {
      ...row,
      group: instanceGroup(row.id, root),
    };
  });
  const groups = [...new Set(instances.map((row) => row.group))];
  const currentRoot = instances.find((row) => row.id === office.currentId);
  return {
    currentId: office.currentId,
    group: currentRoot?.group ?? instanceGroup(office.currentId),
    instances,
    groups,
    computerRoot: resolve(computerRoot),
  };
}

/** Point currentId at the Computer this process is actually serving. */
export function bindRunningComputer(computerRoot: string): OfficeState {
  const office = ensureOfficeState(computerRoot);
  const officeParent = resolveOfficeParent(computerRoot);
  const running = resolve(computerRoot);
  const match = office.instances.find((row) => instanceComputerRoot(officeParent, row) === running);
  if (!match || match.id === office.currentId) {
    return office;
  }
  const next: OfficeState = { ...office, currentId: match.id };
  saveOffice(officeParent, next);
  return next;
}

export function instanceComputerRoot(officeParent: string, instance: OfficeInstanceRecord): string {
  return resolve(officeParent, instance.computerRel);
}

/** One office root. Walk up from the process cwd until office.json. --computer still wins. */
export function resolveOfficeLaunch(start: string): string {
  const flagged = resolve(start);
  if (existsSync(join(flagged, "harness", "roster.json"))) {
    return resolveServeComputer(flagged);
  }
  let dir = flagged;
  for (let hop = 0; hop < 8; hop += 1) {
    if (existsSync(join(dir, "office.json"))) {
      return resolveServeComputer(join(dir, "computer"));
    }
    const parent = dirname(dir);
    if (parent === dir) {
      break;
    }
    dir = parent;
  }
  return resolveServeComputer(flagged);
}

/** Honor office.json currentId so a restart keeps the selected desk. */
export function resolveServeComputer(flagComputerRoot: string): string {
  const flagRoot = resolve(flagComputerRoot);
  const office = ensureOfficeState(flagRoot);
  const officeParent = resolveOfficeParent(flagRoot);
  const current = office.instances.find((row) => row.id === office.currentId);
  if (!current) {
    return flagRoot;
  }
  return instanceComputerRoot(officeParent, current);
}

export function getOfficeInstance(computerRoot: string, id: string): OfficeInstanceResult {
  const office = ensureOfficeState(computerRoot);
  const officeParent = resolveOfficeParent(computerRoot);
  const instance = office.instances.find((row) => row.id === id);
  if (!instance) {
    throw new Error("unknown office instance");
  }
  return {
    office,
    instance,
    computerRoot: instanceComputerRoot(officeParent, instance),
  };
}

function slugInstanceId(name: string, taken: ReadonlySet<string>): string {
  const slug = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  const base = slug.length > 0 && slug !== LIVE_INSTANCE_ID ? slug : "desk";
  if (!taken.has(base)) {
    return base;
  }
  let candidate = `${base}-${shortNonce()}`;
  while (taken.has(candidate)) {
    candidate = `${base}-${shortNonce()}`;
  }
  return candidate;
}

function copyIfPresent(from: string, to: string): void {
  if (!existsSync(from)) {
    return;
  }
  mkdirSync(dirname(to), { recursive: true });
  copyFileSync(from, to);
}

function copyTreeIfPresent(from: string, to: string, filter?: (source: string) => boolean): void {
  if (!existsSync(from)) {
    return;
  }
  if (filter) {
    cpSync(from, to, {
      recursive: true,
      filter: (source: string): boolean => filter(source),
    });
    return;
  }
  cpSync(from, to, { recursive: true });
}

/** Retarget a symlink so the clone still points at the original absolute path. */
function cloneRetargetedSymlink(fromPath: string, toPath: string): boolean {
  try {
    const stat = lstatSync(fromPath);
    if (!stat.isSymbolicLink()) {
      return false;
    }
    const raw = readlinkSync(fromPath);
    const absolute = resolve(dirname(fromPath), raw);
    mkdirSync(dirname(toPath), { recursive: true });
    const nextRel = relative(dirname(toPath), absolute);
    symlinkSync(nextRel.length > 0 ? nextRel : absolute, toPath);
    return true;
  } catch {
    return false;
  }
}

function cloneDataSymlink(fromRoot: string, toRoot: string): void {
  cloneRetargetedSymlink(join(fromRoot, "data"), join(toRoot, "data"));
}

/**
 * Copy Computer cwd identity (`office/bots`, constitution) onto a new instance.
 * Live uses relative symlinks into the office parent; a naive copy would break.
 */
function cloneOfficeIdentity(fromRoot: string, toRoot: string): void {
  const from = join(fromRoot, "office");
  if (!existsSync(from)) {
    return;
  }
  const to = join(toRoot, "office");
  mkdirSync(to, { recursive: true });
  for (const name of readdirSync(from)) {
    const source = join(from, name);
    const dest = join(to, name);
    if (cloneRetargetedSymlink(source, dest)) {
      continue;
    }
    const stat = lstatSync(source);
    if (stat.isDirectory()) {
      copyTreeIfPresent(source, dest);
      continue;
    }
    copyIfPresent(source, dest);
  }
}

function cloneNamed(fromRoot: string, toRoot: string, spec: string): void {
  const link = spec.endsWith("@");
  const name = link ? spec.slice(0, -1) : spec;
  if (name === "data") {
    cloneDataSymlink(fromRoot, toRoot);
    return;
  }
  if (name === "office" && !link) {
    cloneOfficeIdentity(fromRoot, toRoot);
    return;
  }
  if (link) {
    const from = join(fromRoot, name);
    if (!existsSync(from)) return;
    const to = join(toRoot, name);
    mkdirSync(dirname(to), { recursive: true });
    const next = relative(dirname(to), from);
    symlinkSync(next.length > 0 ? next : ".", to);
    return;
  }
  const from = join(fromRoot, name);
  if (!existsSync(from)) return;
  copyTreeIfPresent(from, join(toRoot, name), (source: string): boolean => {
    const base = basename(source);
    if (base === "kernel.port" || base === "kernel.log.jsonl" || base === "__pycache__" || base === ".venv") {
      return false;
    }
    return !base.endsWith(".pyc");
  });
}

function cloneTemplateComputer(fromRoot: string, toRoot: string): void {
  mkdirSync(join(toRoot, "harness"), { recursive: true });
  for (const file of TEMPLATE_HARNESS_FILES) {
    copyIfPresent(join(fromRoot, "harness", file), join(toRoot, "harness", file));
  }
  for (const name of loadLayout(fromRoot).clone) {
    cloneNamed(fromRoot, toRoot, name);
  }
}

function liveTemplateRoot(officeParent: string, office: OfficeState): string {
  const live = office.instances.find((row) => row.id === LIVE_INSTANCE_ID) ?? office.instances[0];
  if (!live) {
    throw new Error("no live office instance");
  }
  return instanceComputerRoot(officeParent, live);
}

/**
 * Clone template files from the live Computer into instances/<id>/.
 * Does not copy Pi sessions, protocol, threads, inboxes, or other runtime.
 */
export function createOfficeInstance(computerRoot: string, name: string): OfficeInstanceResult {
  const trimmed = name.trim();
  if (trimmed.length === 0) {
    throw new Error("name required");
  }
  const office = ensureOfficeState(computerRoot);
  const officeParent = resolveOfficeParent(computerRoot);
  const taken = new Set(office.instances.map((row) => row.id));
  const id = slugInstanceId(trimmed, taken);
  const destRoot = join(officeParent, "instances", id);
  const templateRoot = liveTemplateRoot(officeParent, office);
  if (existsSync(destRoot)) {
    rmSync(destRoot, { recursive: true, force: true });
  }
  mkdirSync(destRoot, { recursive: true });
  try {
    cloneTemplateComputer(templateRoot, destRoot);
    initComputer(destRoot);
    wipeRuntime(destRoot);
  } catch (error) {
    rmSync(destRoot, { recursive: true, force: true });
    throw error;
  }
  const instance: OfficeInstanceRecord = {
    id,
    name: trimmed,
    computerRel: posixRel(officeParent, destRoot),
    createdAt: nowIso(),
  };
  const next: OfficeState = {
    currentId: office.currentId,
    instances: [...office.instances, instance],
  };
  saveOffice(officeParent, next);
  return { office: next, instance, computerRoot: destRoot };
}

/** Persist currentId. Serve switch is the HTTP layer's job. */
export function selectOfficeInstance(computerRoot: string, id: string): OfficeInstanceResult {
  const found = getOfficeInstance(computerRoot, id);
  const officeParent = resolveOfficeParent(computerRoot);
  const next: OfficeState = { ...found.office, currentId: id };
  saveOffice(officeParent, next);
  return { ...found, office: next };
}

export async function handleOfficeInstanceRequest(
  method: string,
  path: string,
  body: unknown,
  computerRoot: string,
  switchTo: (nextRoot: string) => Promise<void>,
): Promise<{ readonly status: number; readonly body: unknown } | undefined> {
  if (method === "GET" && path === "/api/office-instances") {
    return {
      status: 200,
      body: officePublicState(computerRoot),
    };
  }

  if (method === "POST" && path === "/api/office-instances") {
    const name = isRecord(body) && typeof body.name === "string" ? body.name : "";
    try {
      const created = createOfficeInstance(computerRoot, name);
      return {
        status: 200,
        body: {
          instance: created.instance,
          currentId: created.office.currentId,
          instances: created.office.instances,
          computerRoot: created.computerRoot,
        },
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const status = message === "name required" ? 400 : 500;
      return { status, body: { error: message } };
    }
  }

  const selectMatch = /^\/api\/office-instances\/([^/]+)\/select$/.exec(path);
  if (selectMatch && method === "POST") {
    const id = decodeURIComponent(selectMatch[1] ?? "");
    try {
      const found = getOfficeInstance(computerRoot, id);
      const previousId = listOfficeState(computerRoot).currentId;
      if (previousId !== id) {
        selectOfficeInstance(computerRoot, id);
      }
      try {
        await switchTo(found.computerRoot);
      } catch (error) {
        if (previousId !== id) {
          selectOfficeInstance(computerRoot, previousId);
        }
        throw error;
      }
      const selected = getOfficeInstance(computerRoot, id);
      return {
        status: 200,
        body: {
          instance: selected.instance,
          ...officePublicState(selected.computerRoot),
        },
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const status = message === "unknown office instance" ? 404 : 500;
      return { status, body: { error: message } };
    }
  }

  return undefined;
}

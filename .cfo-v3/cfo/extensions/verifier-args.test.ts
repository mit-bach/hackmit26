import assert from "node:assert/strict";
import {copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync} from "node:fs";
import {registerHooks} from "node:module";
import {tmpdir} from "node:os";
import {dirname, join} from "node:path";
import {describe, it} from "node:test";
import {fileURLToPath} from "node:url";

import {harnessHandlePath, pendingIndexPath} from "./intercept.ts";
import {isRecord} from "./load.ts";
import type {PiExtensionApi, PiToolResult} from "./pi-api.ts";
import {botIdForSlug} from "./profile.ts";

// index.ts imports typebox. Use the real package when installed; otherwise a
// schema-shaped stub so the Pi registration path still loads.
const TYPEBOX_STUB = `data:text/javascript,${encodeURIComponent(`
export const Type = {
  Object: (properties) => ({type: "object", properties}),
  String: (options = {}) => ({type: "string", ...options}),
  Optional: (schema) => ({...schema, optional: true}),
  Any: () => ({}),
};
`)}`;

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier !== "typebox") {
      return nextResolve(specifier, context);
    }
    try {
      return nextResolve(specifier, context);
    } catch {
      return {url: TYPEBOX_STUB, shortCircuit: true};
    }
  },
});

const {default: cfoExtension} = await import("./index.ts");

interface RegisteredTool {
  readonly name: string;
  readonly execute: (id: string, params: Record<string, unknown>) => Promise<PiToolResult>;
}

interface Scratch {
  readonly root: string;
  readonly harness: string;
}

function findComputerRoot(start: string): string {
  let dir = start;
  for (let i = 0; i < 10; i += 1) {
    if (existsSync(join(dir, "cfo", "catalog.json")) && existsSync(join(dir, "cfo", "grants.json"))) {
      return dir;
    }
    const parent = dirname(dir);
    if (parent === dir) {
      break;
    }
    dir = parent;
  }
  throw new Error("Computer root with cfo/catalog.json not found");
}

const computerRoot = findComputerRoot(dirname(fileURLToPath(import.meta.url)));

const ACCRUAL = "accrual.tools.create_accrual";
const ARGS_A = {vendor: "Acme", amount: 1000, lines: [{account: "6000", memo: "rent"}]};
const ARGS_B = {vendor: "Acme", amount: 900000, lines: [{account: "6000", memo: "rent"}]};

/** Scratch Computer with the real Client files and a fake Harness `sendPrompt`. */
function scratchComputer(): Scratch {
  const root = mkdtempSync(join(tmpdir(), "cfo-args-"));
  mkdirSync(join(root, "cfo"), {recursive: true});
  for (const name of ["catalog.json", "grants.json", "slug-map.json"]) {
    copyFileSync(join(computerRoot, "cfo", name), join(root, "cfo", name));
  }
  const harness = join(root, "harness-v2");
  mkdirSync(join(harness, "src"), {recursive: true});
  writeFileSync(
    join(harness, "src", "send.ts"),
    [`let count = 0;`, `export function sendPrompt() {`, `  count += 1;`, `  return {handleId: "h-osprey-" + count};`, `}`, ``].join(
      "\n",
    ),
  );
  return {root, harness};
}

function withEnv<T>(env: Readonly<Record<string, string | undefined>>, run: () => T): T {
  const saved: Record<string, string | undefined> = {};
  for (const [key, value] of Object.entries(env)) {
    saved[key] = process.env[key];
    if (value === undefined) {
      delete process.env[key];
    } else {
      process.env[key] = value;
    }
  }
  try {
    return run();
  } finally {
    for (const [key, value] of Object.entries(saved)) {
      if (value === undefined) {
        delete process.env[key];
      } else {
        process.env[key] = value;
      }
    }
  }
}

/** Load index.ts the way Pi does and return the registered `call_connected_tool`. */
function connectedTool(scratch: Scratch): RegisteredTool {
  const tools = new Map<string, RegisteredTool>();
  const pi: PiExtensionApi = {
    registerTool(tool) {
      tools.set(tool.name, tool);
    },
    on() {},
  };
  withEnv(
    {HARNESS_BOT: "close", HARNESS_PROFILE: "accrue", HARNESS_COMPUTER: scratch.root, CFO_EVAL_PHASE: undefined},
    () => cfoExtension(pi),
  );
  const tool = tools.get("call_connected_tool");
  assert.ok(tool, "index.ts must register call_connected_tool");
  return tool;
}

async function callTool(
  tool: RegisteredTool,
  scratch: Scratch,
  params: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  const saved = process.env.HARNESS_V2_ROOT;
  process.env.HARNESS_V2_ROOT = scratch.harness;
  try {
    const out = await tool.execute("call-1", params);
    assert.ok(isRecord(out.details));
    return out.details;
  } finally {
    if (saved === undefined) {
      delete process.env.HARNESS_V2_ROOT;
    } else {
      process.env.HARNESS_V2_ROOT = saved;
    }
  }
}

function interceptHandleId(details: Record<string, unknown>): string {
  assert.equal(details.error, "verifier_required");
  assert.ok(isRecord(details.result));
  const handleId = details.result.handleId;
  assert.equal(typeof handleId, "string");
  return String(handleId);
}

function concur(root: string, handleId: string): void {
  const path = harnessHandlePath(root, botIdForSlug("ctl-books"), handleId);
  mkdirSync(dirname(path), {recursive: true});
  writeFileSync(path, `${JSON.stringify({id: handleId, status: "completed", result: "CONCUR", op: ACCRUAL})}\n`);
}

function readPending(root: string, handleId: string): Record<string, unknown> {
  const raw: unknown = JSON.parse(readFileSync(pendingIndexPath(root, handleId), "utf8"));
  assert.ok(isRecord(raw));
  return raw;
}

function call(args: unknown, extra: Record<string, unknown> = {}): Record<string, unknown> {
  return {name: ACCRUAL, args, idempotency_key: "accrual-args-1", ...extra};
}

describe("Verifier concurrence binds the call's arguments", () => {
  it("CONCUR on args A does not unlock args B with the same idempotency_key", async () => {
    const scratch = scratchComputer();
    try {
      const tool = connectedTool(scratch);
      const handleA = interceptHandleId(await callTool(tool, scratch, call(ARGS_A)));
      concur(scratch.root, handleA);

      const swapped = await callTool(tool, scratch, call(ARGS_B));
      const handleB = interceptHandleId(swapped);
      assert.notEqual(handleB, handleA, "a mismatch opens a new pending Verifier record");
      assert.equal(typeof readPending(scratch.root, handleA).argsHash, "string");
      assert.notEqual(readPending(scratch.root, handleB).argsHash, readPending(scratch.root, handleA).argsHash);

      const explicit = await callTool(tool, scratch, call(ARGS_B, {handle_id: handleA}));
      assert.equal(explicit.error, "verifier_required", "an explicit handle_id for args A does not unlock args B");

      const original = await callTool(tool, scratch, call(ARGS_A));
      assert.equal(original.error, "sidecar_unavailable", "args A still unlock on the args A concurrence");

      concur(scratch.root, handleB);
      const concurredB = await callTool(tool, scratch, call(ARGS_B));
      assert.equal(concurredB.error, "sidecar_unavailable", "args B unlock on their own concurrence");
    } finally {
      rmSync(scratch.root, {recursive: true, force: true});
    }
  });

  it("the args A packet the Verifier reads is not overwritten by an args B call", async () => {
    const scratch = scratchComputer();
    try {
      const tool = connectedTool(scratch);
      const handleA = interceptHandleId(await callTool(tool, scratch, call(ARGS_A)));
      interceptHandleId(await callTool(tool, scratch, call(ARGS_B)));

      const packetPath = readPending(scratch.root, handleA).packetPath;
      assert.equal(typeof packetPath, "string");
      const packet: unknown = JSON.parse(readFileSync(String(packetPath), "utf8"));
      assert.ok(isRecord(packet));
      assert.deepEqual(packet.args, ARGS_A);
    } finally {
      rmSync(scratch.root, {recursive: true, force: true});
    }
  });

  it("a pending record without an argument hash does not unlock", async () => {
    const scratch = scratchComputer();
    try {
      const tool = connectedTool(scratch);
      const handleA = interceptHandleId(await callTool(tool, scratch, call(ARGS_A)));
      const legacy = readPending(scratch.root, handleA);
      delete legacy.argsHash;
      writeFileSync(pendingIndexPath(scratch.root, handleA), `${JSON.stringify(legacy, null, 2)}\n`);
      concur(scratch.root, handleA);

      const retry = await callTool(tool, scratch, call(ARGS_A));
      assert.notEqual(interceptHandleId(retry), handleA);
    } finally {
      rmSync(scratch.root, {recursive: true, force: true});
    }
  });

  it("object key order does not change the argument hash", async () => {
    const scratch = scratchComputer();
    try {
      const tool = connectedTool(scratch);
      const handleA = interceptHandleId(await callTool(tool, scratch, call(ARGS_A)));
      concur(scratch.root, handleA);
      const reordered = {lines: [{memo: "rent", account: "6000"}], amount: 1000, vendor: "Acme"};
      const retry = await callTool(tool, scratch, call(reordered));
      assert.equal(retry.error, "sidecar_unavailable");
    } finally {
      rmSync(scratch.root, {recursive: true, force: true});
    }
  });
});

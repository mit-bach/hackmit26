import assert from "node:assert/strict";
import {copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync} from "node:fs";
import {registerHooks} from "node:module";
import {tmpdir} from "node:os";
import {dirname, join} from "node:path";
import {describe, it} from "node:test";
import {fileURLToPath} from "node:url";

import {completedHandleAllowsOp, handleConcurrence, harnessHandlePath} from "./intercept.ts";
import {isRecord, loadClientFiles} from "./load.ts";
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
  readonly parameters: unknown;
  readonly execute: (id: string, params: Record<string, unknown>) => Promise<PiToolResult>;
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

/** Scratch Computer with the real Client files and a fake Harness `sendPrompt`. */
function scratchComputer(): {readonly root: string; readonly harness: string; readonly sent: string} {
  const root = mkdtempSync(join(tmpdir(), "cfo-wiring-"));
  mkdirSync(join(root, "cfo"), {recursive: true});
  for (const name of ["catalog.json", "grants.json", "slug-map.json"]) {
    copyFileSync(join(computerRoot, "cfo", name), join(root, "cfo", name));
  }
  const harness = join(root, "harness-v2");
  const sent = join(root, "sent.jsonl");
  mkdirSync(join(harness, "src"), {recursive: true});
  writeFileSync(
    join(harness, "src", "send.ts"),
    [
      `import {appendFileSync} from "node:fs";`,
      `let count = 0;`,
      `export function sendPrompt(input) {`,
      `  count += 1;`,
      `  const handleId = "h-wren-" + count;`,
      `  appendFileSync(${JSON.stringify(sent)}, JSON.stringify({handleId, to: input.to}) + "\\n");`,
      `  return {handleId};`,
      `}`,
      ``,
    ].join("\n"),
  );
  return {root, harness, sent};
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

/** Load index.ts the way Pi does and return the registered tools. */
function registerClose(scratch: {readonly root: string; readonly harness: string}): Map<string, RegisteredTool> {
  const tools = new Map<string, RegisteredTool>();
  const pi: PiExtensionApi = {
    registerTool(tool) {
      tools.set(tool.name, tool);
    },
    on() {},
  };
  withEnv(
    {
      HARNESS_BOT: "close",
      HARNESS_PROFILE: "accrue",
      HARNESS_COMPUTER: scratch.root,
      CFO_EVAL_PHASE: undefined,
    },
    () => cfoExtension(pi),
  );
  return tools;
}

async function callTool(
  tool: RegisteredTool,
  harness: string,
  params: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  const saved = process.env.HARNESS_V2_ROOT;
  process.env.HARNESS_V2_ROOT = harness;
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

function completeHandle(root: string, handleId: string, result: string): void {
  const path = harnessHandlePath(root, botIdForSlug("ctl-books"), handleId);
  mkdirSync(dirname(path), {recursive: true});
  writeFileSync(path, `${JSON.stringify({id: handleId, status: "completed", result, op: ACCRUAL})}\n`);
}

function callTool_(tools: Map<string, RegisteredTool>): RegisteredTool {
  const tool = tools.get("call_connected_tool");
  assert.ok(tool, "index.ts must register call_connected_tool");
  return tool;
}

describe("Verifier concurrence parse", () => {
  it("prose that mentions CONCUR is not CONCUR", () => {
    for (const text of [
      "I do not concur",
      "I do not CONCUR with this accrual.",
      "CONCUR is not possible",
      "CONCURRENCE withheld",
      "Looks fine, concur.",
      "concur",
      "REFUSE? No. CONCUR.",
    ]) {
      assert.notEqual(handleConcurrence(text), "CONCUR", text);
    }
  });

  it("accepts only a structured decision", () => {
    assert.equal(handleConcurrence("CONCUR"), "CONCUR");
    assert.equal(handleConcurrence("  CONCUR  \npacket complete"), "CONCUR");
    assert.equal(handleConcurrence("REFUSE\namount unsupported"), "REFUSE");
    assert.equal(handleConcurrence(`{"decision": "CONCUR", "note": "ok"}`), "CONCUR");
    assert.equal(handleConcurrence(`{"decision": "REFUSE"}`), "REFUSE");
    assert.equal(handleConcurrence(`{"decision": "I do not CONCUR"}`), "none");
    assert.equal(handleConcurrence(`{"decision": true}`), "none");
    assert.equal(handleConcurrence(""), "none");
  });

  it("a completed Handle whose result says 'I do not concur' does not unlock", () => {
    const scratch = mkdtempSync(join(tmpdir(), "cfo-parse-"));
    try {
      const op = loadClientFiles(computerRoot).catalog.ops.find((row) => row.id === ACCRUAL);
      assert.ok(op);
      completeHandle(scratch, "h-prose", "I do not concur");
      assert.equal(completedHandleAllowsOp(scratch, "h-prose", op), false);
      completeHandle(scratch, "h-prose-2", "CONCUR is not possible");
      assert.equal(completedHandleAllowsOp(scratch, "h-prose-2", op), false);
    } finally {
      rmSync(scratch, {recursive: true, force: true});
    }
  });
});

describe("call_connected_tool through the Pi registration path", () => {
  it("unlocks a consequential op after CONCUR when the model retries with the same idempotency_key", async () => {
    const scratch = scratchComputer();
    try {
      const tool = callTool_(registerClose(scratch));
      const params = {name: ACCRUAL, args: {vendor: "Acme"}, idempotency_key: "accrual-wiring-1"};

      const first = await callTool(tool, scratch.harness, params);
      const firstHandle = interceptHandleId(first);
      assert.equal(firstHandle, "h-wren-1");
      assert.notEqual(firstHandle, params.idempotency_key);

      completeHandle(scratch.root, firstHandle, "I do not concur");
      const refused = await callTool(tool, scratch.harness, params);
      const secondHandle = interceptHandleId(refused);
      assert.equal(secondHandle, "h-wren-2");

      completeHandle(scratch.root, secondHandle, "CONCUR\npacket complete");
      const unlocked = await callTool(tool, scratch.harness, params);
      assert.notEqual(unlocked.error, "verifier_required");
      assert.equal(unlocked.error, "sidecar_unavailable");

      const otherKey = await callTool(tool, scratch.harness, {...params, idempotency_key: "accrual-wiring-2"});
      assert.equal(otherKey.error, "verifier_required");

      const sent = readFileSync(scratch.sent, "utf8").trim().split("\n").map((line): unknown => JSON.parse(line));
      assert.equal(sent.length, 3);
      for (const row of sent) {
        assert.ok(isRecord(row));
        assert.equal(row.to, "ctl-books");
      }
    } finally {
      rmSync(scratch.root, {recursive: true, force: true});
    }
  });

  it("honors an explicit handle_id the model passes", async () => {
    const scratch = scratchComputer();
    try {
      const tool = callTool_(registerClose(scratch));
      assert.ok(isRecord(tool.parameters) && isRecord(tool.parameters.properties));
      assert.ok(tool.parameters.properties.handle_id, "call_connected_tool must declare handle_id");

      const first = await callTool(tool, scratch.harness, {
        name: ACCRUAL,
        args: {vendor: "Acme"},
        idempotency_key: "accrual-wiring-3",
      });
      const handleId = interceptHandleId(first);
      completeHandle(scratch.root, handleId, `{"decision": "CONCUR"}`);

      const unlocked = await callTool(tool, scratch.harness, {
        name: ACCRUAL,
        args: {vendor: "Acme"},
        idempotency_key: "accrual-wiring-3",
        handle_id: handleId,
      });
      assert.equal(unlocked.error, "sidecar_unavailable");
    } finally {
      rmSync(scratch.root, {recursive: true, force: true});
    }
  });
});

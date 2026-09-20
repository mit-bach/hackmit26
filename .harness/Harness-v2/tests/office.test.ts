import assert from "node:assert/strict";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

import { applyClientAttach, loadClientRuntime, overlayOperatorConfig, parseClientRuntime } from "../src/client-runtime.ts";
import { applyAttachEnv, collectExtraExtensionPaths, loadExtensionsManifest } from "../src/client-attach.ts";
import {
  loadIntercept,
  operatorCompletesIntercept,
  resolveIntercept,
  saveIntercept,
  seedVerifierIntercept,
} from "../src/intercept.ts";
import { extraExtensionArgs } from "../src/pkg.ts";
import { handlePath } from "../src/paths.ts";
import { writeJsonAtomic } from "../src/fs.ts";
import { startSidecar } from "../src/sidecar.ts";
import { startServer } from "../src/server/http.ts";
import { MAX_SAFE_INTERVAL_MS, cadenceToMs } from "../src/routines.ts";
import { loadRoster, saveRoster } from "../src/roster.ts";
import { makeComputer } from "./helpers.ts";

const here = dirname(fileURLToPath(import.meta.url));
const sidecarFixture = join(here, "..", "..", "tests", "fixtures", "sidecar.mjs");

test("monthly cadence is clamped to a 32-bit-safe interval", () => {
  assert.equal(cadenceToMs("weekly"), 7 * 24 * 60 * 60 * 1000);
  assert.ok((30 * 24 * 60 * 60 * 1000) > MAX_SAFE_INTERVAL_MS);
  assert.equal(cadenceToMs("monthly"), MAX_SAFE_INTERVAL_MS);
  assert.ok((cadenceToMs("monthly") ?? 0) <= MAX_SAFE_INTERVAL_MS);
});

test("client.json attaches extra extensions and can disable the sidecar", () => {
  const computer = makeComputer();
  mkdirSync(join(computer, "cfo", "extensions"), { recursive: true });
  writeFileSync(join(computer, "cfo", "extensions", "index.ts"), "export default function () {}\n");
  writeJsonAtomic(join(computer, "harness", "client.json"), {
    extraExtensions: ["./cfo/extensions/index.ts"],
    clientSkills: true,
    spawnPolicy: "lazy",
    autoRoutines: false,
    sidecar: false,
  });
  const runtime = loadClientRuntime(computer);
  assert.equal(runtime.clientSkills, true);
  assert.equal(runtime.spawnPolicy, "lazy");
  assert.equal(runtime.autoRoutines, false);
  assert.equal(runtime.sidecar, undefined);
  applyClientAttach(computer, runtime);
  const manifest = loadExtensionsManifest(computer);
  assert.equal(manifest.clientSkills, true);
  assert.ok(manifest.extraExtensions.some((item) => item.endsWith("cfo/extensions/index.ts")));
});

test("missing client.json still discovers a CFO extension on the Computer", () => {
  const computer = makeComputer();
  mkdirSync(join(computer, "cfo", "extensions"), { recursive: true });
  writeFileSync(join(computer, "cfo", "extensions", "index.ts"), "export default function () {}\n");
  const runtime = parseClientRuntime(undefined, computer);
  assert.deepEqual(runtime.extraExtensions, ["cfo/extensions/index.ts"]);
  assert.equal(runtime.clientSkills, true);
});

test("client.json thinking and transcript verbosity overlay onto default operator features", () => {
  const computer = makeComputer();
  writeJsonAtomic(join(computer, "harness", "client.json"), {
    extraExtensions: [],
    thinkingLevel: "low",
    features: { showToolCalls: true, transcriptVerbosity: "full" },
  });
  const runtime = loadClientRuntime(computer);
  assert.equal(runtime.thinkingLevel, "low");
  assert.equal(runtime.features?.transcriptVerbosity, "full");
  const live = overlayOperatorConfig(computer, {
    spawnPolicy: "eager",
    port: 8787,
    openBrowser: false,
    apiKeys: {},
    extraExtensions: [],
    clientSkills: false,
    features: { skillAuthoring: true, showToolCalls: false, browser: false, transcriptVerbosity: "compact" },
  });
  assert.equal(live.thinkingLevel, "low");
  assert.equal(live.features.transcriptVerbosity, "full");
  assert.equal(live.features.showToolCalls, true);
});

test("seedVerifierIntercept does not invent ctl-* Bot maps", () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  saveRoster(computer, {
    ...roster,
    bots: [
      ...roster.bots,
      {
        id: "bot_ap",
        slug: "ap",
        name: "AP",
        purpose: "draft",
        instructions: "",
        skills: [],
        connectors: [],
        approvalLevel: "never",
      },
      {
        id: "bot_ctl_pay",
        slug: "ctl-pay",
        name: "ctl-pay",
        purpose: "verify",
        instructions: "",
        skills: [],
        connectors: [],
        approvalLevel: "never",
      },
    ],
  });
  writeJsonAtomic(join(computer, "harness", "intercept.json"), { default: { kind: "operator" }, bots: {} });
  const seeded = seedVerifierIntercept(computer);
  assert.deepEqual(seeded.bots, {});
  assert.equal(seeded.default.kind, "operator");
});

test("resolveIntercept honors Computer-owned kind bot over default operator", () => {
  const computer = makeComputer();
  saveIntercept(computer, {
    default: { kind: "bot", bot: "ctl-pay" },
    bots: {
      collect: { kind: "bot", bot: "ctl-pay" },
      apply: { kind: "bot", bot: "ctl-cash" },
    },
  });
  const map = loadIntercept(computer);
  assert.equal(operatorCompletesIntercept(map.default), false);
  assert.deepEqual(resolveIntercept(map, "collect"), { kind: "bot", bot: "ctl-pay" });
  assert.deepEqual(resolveIntercept(map, "apply"), { kind: "bot", bot: "ctl-cash" });
  assert.equal(operatorCompletesIntercept(resolveIntercept(map, "collect")), false);
});

test("Handle complete path is harness/bots/<botId>/handles/<id>.json", () => {
  const computer = makeComputer();
  assert.equal(
    handlePath(computer, "bot_alpha", "h1"),
    join(computer, "harness", "bots", "bot_alpha", "handles", "h1.json"),
  );
});

test("startSidecar waits for a healthy loopback port", async () => {
  const computer = makeComputer();
  const portFile = join(computer, "cfo", "kernel.port");
  mkdirSync(join(computer, "cfo"), { recursive: true });
  const handle = await startSidecar(computer, {
    extraExtensions: [],
    clientSkills: false,
    autoRoutines: false,
    sidecar: {
      command: sidecarFixture,
      args: [],
      portFile: "cfo/kernel.port",
      readyTimeoutMs: 8_000,
    },
  });
  assert.ok(handle);
  assert.ok(handle.port > 0);
  const health = await fetch(`http://127.0.0.1:${handle.port}/health`);
  assert.equal(health.ok, true);
  assert.equal(JSON.parse(readUtf(portFile)).port, handle.port);
  await handle.stop();
});

test("serve loads client.json, boots sidecar, and POST /api/wipe clears inboxes", async () => {
  const computer = makeComputer();
  mkdirSync(join(computer, "cfo"), { recursive: true });
  writeJsonAtomic(join(computer, "harness", "client.json"), {
    extraExtensions: [],
    clientSkills: false,
    spawnPolicy: "lazy",
    autoRoutines: false,
    sidecar: {
      command: sidecarFixture,
      args: [],
      portFile: "cfo/kernel.port",
      readyTimeoutMs: 8_000,
    },
  });
  const started = await startServer({
    computerRoot: computer,
    port: 0,
    workers: false,
    sidecar: true,
  });
  try {
    const office = (await (await fetch(`${started.url}/api/office`)).json()) as {
      bots: number;
      sidecar: { port: number } | null;
      client: { spawnPolicy: string; autoRoutines: boolean };
    };
    assert.equal(office.bots, 3);
    assert.equal(office.client.spawnPolicy, "lazy");
    assert.equal(office.client.autoRoutines, false);
    assert.ok(office.sidecar && office.sidecar.port > 0);
    const health = (await (await fetch(`${started.url}/health`)).json()) as {
      sidecar: { port: number } | null;
    };
    assert.equal(health.sidecar?.port, office.sidecar.port);

    await fetch(`${started.url}/v1/bots/beta/prompt`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text: "stale before wipe" }),
    });
    const wiped = (await (
      await fetch(`${started.url}/api/wipe`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ keepMemory: true }),
      })
    ).json()) as { bots: number; cleared: string[] };
    assert.equal(wiped.bots, 3);
    const inbox = (await (await fetch(`${started.url}/v1/bots/beta/inbox`)).json()) as unknown[];
    assert.equal(inbox.length, 0);
  } finally {
    await started.stop();
  }
});

test("overlay and attach env keep only this Computer's CFO extension", () => {
  const live = makeComputer();
  const clone = makeComputer();
  for (const root of [live, clone]) {
    mkdirSync(join(root, "cfo", "extensions"), { recursive: true });
    writeFileSync(join(root, "cfo", "extensions", "index.ts"), "export default function () {}\n");
  }
  const liveExt = join(live, "cfo", "extensions", "index.ts");
  writeJsonAtomic(join(clone, "harness", "client.json"), {
    extraExtensions: ["./cfo/extensions/index.ts"],
    clientSkills: true,
  });
  const overlaid = overlayOperatorConfig(clone, {
    spawnPolicy: "lazy",
    port: 8787,
    openBrowser: false,
    apiKeys: {},
    extraExtensions: [liveExt],
    clientSkills: true,
    features: { skillAuthoring: false, showToolCalls: true, browser: false, transcriptVerbosity: "full" },
  });
  assert.equal(overlaid.extraExtensions.length, 1);
  assert.ok(overlaid.extraExtensions[0]?.includes(clone));
  assert.equal(overlaid.extraExtensions.some((path) => path.includes(live)), false);

  const collected = collectExtraExtensionPaths({
    computerRoot: clone,
    env: { HARNESS_EXTRA_EXTENSIONS: liveExt },
    config: overlaid,
  });
  assert.equal(collected.length, 1);
  assert.ok(collected[0]?.includes(clone));
  assert.equal(collected.some((path) => path.includes(live)), false);

  const env = applyAttachEnv({ HARNESS_EXTRA_EXTENSIONS: liveExt }, clone, overlaid);
  assert.equal(env.HARNESS_EXTRA_EXTENSIONS?.includes(live), false);
  assert.ok(env.HARNESS_EXTRA_EXTENSIONS?.includes(clone));
});

test("client.json attach env persists Client -e, HARNESS_CLIENT_SKILLS, and HARNESS_V2_ROOT", () => {
  const computer = makeComputer();
  mkdirSync(join(computer, "cfo", "extensions"), { recursive: true });
  writeFileSync(join(computer, "cfo", "extensions", "index.ts"), "export default function () {}\n");
  writeJsonAtomic(join(computer, "harness", "client.json"), {
    extraExtensions: ["./cfo/extensions/index.ts"],
    clientSkills: true,
  });
  const runtime = loadClientRuntime(computer);
  applyClientAttach(computer, runtime);
  const env = applyAttachEnv({}, computer, runtime);
  assert.equal(env.HARNESS_CLIENT_SKILLS, "1");
  assert.ok(env.HARNESS_V2_ROOT && env.HARNESS_V2_ROOT.length > 0);
  const argv = extraExtensionArgs(env);
  assert.equal(argv.includes("-e"), true);
  assert.ok(argv.some((item) => item.endsWith("cfo/extensions/index.ts")));
  const manifest = loadExtensionsManifest(computer);
  assert.equal(manifest.clientSkills, true);
  assert.ok(manifest.extraExtensions.some((item) => item.endsWith("cfo/extensions/index.ts")));
});

function readUtf(path: string): string {
  return readFileSync(path, "utf8");
}

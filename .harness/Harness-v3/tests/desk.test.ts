import assert from "node:assert/strict";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { applyAttachEnv, collectExtraExtensionPaths } from "../src/client-attach.ts";
import { createApproval } from "../src/approvals.ts";
import { cadenceToMs, MAX_SAFE_INTERVAL_MS } from "../src/routines.ts";
import { writeJsonAtomic } from "../src/fs.ts";
import { startServer } from "../src/server/http.ts";
import { patchOperatorConfig } from "../src/server/operator-config.ts";
import { makeComputer } from "./helpers.ts";

function withConfig<T>(fn: () => Promise<T>): Promise<T> {
  const prev = process.env.HARNESS_CONFIG;
  const file = join(mkdtempSync(join(tmpdir(), "harness-cfg-")), "config.json");
  process.env.HARNESS_CONFIG = file;
  return fn().finally(() => {
    if (prev === undefined) {
      delete process.env.HARNESS_CONFIG;
    } else {
      process.env.HARNESS_CONFIG = prev;
    }
  });
}

test("weekly cadence stays exact; monthly is clamped to a 32-bit-safe interval", () => {
  assert.equal(cadenceToMs("weekly"), 7 * 24 * 60 * 60 * 1000);
  assert.equal(cadenceToMs("monthly"), MAX_SAFE_INTERVAL_MS);
  assert.equal(cadenceToMs("every 2 d"), 2 * 24 * 60 * 60 * 1000);
});

test("nested API keys, extra extensions, rooms, skills, search, and protocol inspector persist", async () => {
  await withConfig(async () => {
    const computer = makeComputer();
    const extraDir = join(computer, "client-ext");
    mkdirSync(extraDir, { recursive: true });
    const extraFile = join(extraDir, "index.ts");
    writeFileSync(extraFile, "export default function () {}\n");
    writeJsonAtomic(join(computer, "harness", "extensions.json"), {
      extraExtensions: ["./client-ext/index.ts"],
      clientSkills: true,
    });
    mkdirSync(join(computer, "skills", "briefing"), { recursive: true });
    writeFileSync(join(computer, "skills", "briefing", "SKILL.md"), "# Briefing\n\nWrite a two-line brief.\n");

    const paths = collectExtraExtensionPaths({ computerRoot: computer });
    assert.ok(paths.some((item) => item.endsWith("client-ext/index.ts")));
    const env = applyAttachEnv({}, computer);
    assert.equal(env.HARNESS_CLIENT_SKILLS, "1");

    const started = await startServer({ computerRoot: computer, port: 0, workers: false, fakeWorkers: true });
    try {
      const saved = await fetch(`${started.url}/api/config`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          anthropic: { key: "sk-ant-test-key-value" },
          extraExtensions: [extraFile],
          spawnPolicy: "fake",
          features: { skillAuthoring: true },
        }),
      });
      assert.equal(saved.ok, true);
      const cfg = (await saved.json()) as {
        anthropic: { configured: boolean };
        extraExtensions: string[];
        harness: { spawnPolicy: string };
      };
      assert.equal(cfg.anthropic.configured, true);
      assert.equal(cfg.harness.spawnPolicy, "fake");
      const diskCfg = JSON.parse(readFileSync(process.env.HARNESS_CONFIG ?? "", "utf8")) as {
        anthropic?: { key?: string };
        apiKeys?: unknown;
        extraExtensions?: string[];
      };
      assert.equal(diskCfg.anthropic?.key, "sk-ant-test-key-value");
      assert.equal(diskCfg.apiKeys, undefined);
      const extDisk = JSON.parse(readFileSync(join(computer, "harness", "extensions.json"), "utf8")) as {
        extraExtensions: string[];
        clientSkills: boolean;
      };
      assert.ok(extDisk.extraExtensions.some((item) => item === extraFile || item.endsWith("index.ts")));

      const probed = await fetch(`${started.url}/api/keys/test`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ provider: "anthropic" }),
      });
      const probeBody = (await probed.json()) as { ok: boolean; message: string };
      assert.equal(probeBody.ok, true);
      assert.match(probeBody.message, /not a live API call/);

      const draftTest = await fetch(`${started.url}/api/keys/test`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ provider: "google", key: "sk-draft-should-not-persist" }),
      });
      const draftBody = (await draftTest.json()) as { ok: boolean; message: string };
      assert.equal(draftBody.ok, false);
      assert.match(draftBody.message, /does not save/);
      const afterDraft = await fetch(`${started.url}/api/config`);
      const afterDraftCfg = (await afterDraft.json()) as { google?: { configured: boolean } };
      assert.equal(afterDraftCfg.google?.configured, false);

      const sent = await fetch(`${started.url}/api/bots/bot_beta/messages`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: "desk ping" }),
      });
      assert.equal(sent.ok, true);

      const events = await fetch(`${started.url}/api/threads/bot_beta/events?limit=50`);
      const page = (await events.json()) as { entries: unknown[]; total: { runtime: number } };
      assert.ok(page.total.runtime > 0 || page.entries.length > 0);

      const search = await fetch(`${started.url}/api/search?q=desk+ping`);
      const searchBody = (await search.json()) as { hits: unknown[] };
      assert.ok(Array.isArray(searchBody.hits));

      const skills = await fetch(`${started.url}/api/bots/bot_beta/skills`);
      const skillBody = (await skills.json()) as { skills: Array<{ name: string; enabled: boolean }> };
      assert.ok(skillBody.skills.some((row) => row.name === "briefing"));

      const enable = await fetch(`${started.url}/api/bots/bot_beta/skills/briefing`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ enabled: true }),
      });
      assert.equal(enable.ok, true);

      const memory = await fetch(`${started.url}/api/bots/bot_beta/memory`);
      const memBody = (await memory.json()) as { botId: string; index: { hash: string } };
      assert.equal(memBody.botId, "bot_beta");
      assert.ok(memBody.index.hash.length > 0);

      const journal = await fetch(`${started.url}/api/bots/bot_beta/memory/journal`);
      const journalBody = (await journal.json()) as { entries: unknown[] };
      assert.equal(journal.ok, true);
      assert.ok(Array.isArray(journalBody.entries));

      const savedMem = await fetch(`${started.url}/api/bots/bot_beta/memory/file`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ path: "MEMORY.md", text: "desk note\n", expectedHash: memBody.index.hash }),
      });
      const savedMemBody = (await savedMem.json()) as { ok: boolean; text: string; overview: { botId: string } };
      assert.equal(savedMem.ok, true);
      assert.equal(savedMemBody.ok, true);
      assert.equal(savedMemBody.text, "desk note\n");
      assert.equal(savedMemBody.overview.botId, "bot_beta");

      const overview = await fetch(`${started.url}/api/bots/bot_beta/overview`);
      const overviewBody = (await overview.json()) as { who: { name: string }; does: string[] };
      assert.equal(overview.ok, true);
      assert.ok(overviewBody.who.name.length > 0);
      assert.ok(overviewBody.does.length > 0);

      const prompt = await fetch(`${started.url}/api/bots/bot_beta/system-prompt`);
      const promptBody = (await prompt.json()) as { sections: Array<{ id: string }>; totalBytes: number };
      assert.equal(prompt.ok, true);
      assert.ok(promptBody.sections.some((row) => row.id === "identity"));
      assert.ok(promptBody.totalBytes > 0);

      const missing = await fetch(`${started.url}/api/no-such-desk-route`);
      assert.equal(missing.status, 404);

      const tooSmall = await fetch(`${started.url}/api/groups`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name: "Solo", memberIds: ["bot_alpha"] }),
      });
      assert.equal(tooSmall.status, 400);

      const group = await fetch(`${started.url}/api/groups`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name: "Pair", memberIds: ["bot_alpha", "bot_beta"] }),
      });
      const groupBody = (await group.json()) as { group: { id: string; memberIds: string[] } };
      assert.equal(group.ok, true);
      assert.ok(groupBody.group.memberIds.length >= 2);

      const routine = await fetch(`${started.url}/api/routines`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          name: "hourly-check",
          botId: "bot_beta",
          prompt: "Say hourly",
          schedule: { type: "interval", everyMinutes: 60, anchorAt: Date.now() },
        }),
      });
      assert.equal(routine.ok, true);

      const intercept = await fetch(`${started.url}/api/intercept`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ default: { kind: "operator" }, bots: { alpha: { kind: "bot", bot: "beta" } } }),
      });
      assert.equal(intercept.ok, true);

      const fired = await fetch(`${started.url}/api/routines/hourly-check/run`, { method: "POST" });
      assert.equal(fired.ok, true);
      const listed = await fetch(`${started.url}/api/routines`);
      const listedBody = (await listed.json()) as { runs: Array<{ status: string; routineId: string }> };
      assert.ok(listedBody.runs.some((row) => row.routineId === "hourly-check"));

      const tree = await fetch(`${started.url}/api/computer/tree?from=.`);
      const treeBody = (await tree.json()) as Array<{ path: string; type: string }>;
      assert.ok(Array.isArray(treeBody));
      assert.ok(treeBody.some((row) => row.path.startsWith("harness")));

      const newThread = await fetch(`${started.url}/api/bots/bot_alpha/tasks`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: "{}",
      });
      assert.equal(newThread.status, 400);

      const comms = await fetch(`${started.url}/api/comms`);
      const commsBody = (await comms.json()) as { protocol: string; roster: string };
      assert.ok(commsBody.protocol.includes("protocol.jsonl"));
      assert.ok(commsBody.roster.includes("roster.json"));

      const patched = await fetch(`${started.url}/api/bots/bot_beta`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          harnessSlug: "beta",
          title: "Desk purpose",
          soul: "Desk instructions",
          approvalLevel: "always",
        }),
      });
      assert.equal(patched.ok, true);
      const patchedBody = (await patched.json()) as {
        bot: { harnessSlug?: string; approvalLevel?: string; title?: string; soul?: string };
      };
      assert.equal(patchedBody.bot.harnessSlug, "beta");
      assert.equal(patchedBody.bot.approvalLevel, "always");
      assert.equal(patchedBody.bot.title, "Desk purpose");
      assert.equal(patchedBody.bot.soul, "Desk instructions");

      const rosterAfter = JSON.parse(readFileSync(join(computer, "harness", "roster.json"), "utf8")) as {
        bots: Array<{ slug: string; purpose: string; instructions: string; approvalLevel: string }>;
        routines: Array<{ name: string; bot: string; prompt: string }>;
      };
      const beta = rosterAfter.bots.find((row) => row.slug === "beta");
      assert.ok(beta);
      assert.equal(beta.purpose, "Desk purpose");
      assert.equal(beta.instructions, "Desk instructions");
      assert.equal(beta.approvalLevel, "always");
      assert.ok(rosterAfter.routines.some((row) => row.name === "hourly-check" && row.prompt === "Say hourly"));

      const interceptFile = JSON.parse(readFileSync(join(computer, "harness", "intercept.json"), "utf8")) as {
        default: { kind: string };
      };
      assert.equal(interceptFile.default.kind, "operator");

      const approval = createApproval(computer, {
        botId: "bot_beta",
        toolName: "bash",
        detail: "ls workspace",
      });
      const botsAfter = await fetch(`${started.url}/api/bots`);
      const botsBody = (await botsAfter.json()) as {
        bots: Array<{ id: string; messages?: Array<{ card?: { tool?: string; requestId?: string } }> }>;
      };
      const betaWire = botsBody.bots.find((row) => row.id === "bot_beta");
      const card = betaWire?.messages?.find((row) => row.card?.requestId === approval.id)?.card;
      assert.equal(card?.tool, "bash");

      const allowed = await fetch(`${started.url}/api/threads/bot_beta/respond`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ requestId: approval.id, behavior: "allow" }),
      });
      assert.equal(allowed.ok, true);
      const approvalOnDisk = JSON.parse(
        readFileSync(join(computer, "harness", "approvals", `${approval.id}.json`), "utf8"),
      ) as { status: string };
      assert.equal(approvalOnDisk.status, "allowed");

      const catalog = await fetch(`${started.url}/api/connectors/catalog`);
      const catalogBody = (await catalog.json()) as { cards?: unknown[]; source?: string };
      assert.equal(catalogBody.source, "harness");
      assert.ok(Array.isArray(catalogBody.cards));
      assert.equal(catalogBody.cards.length, 4);

      const removed = await fetch(`${started.url}/api/bots/bot_gamma`, { method: "DELETE" });
      assert.equal(removed.ok, true);
    } finally {
      await started.stop();
    }
  });
});

test("patchOperatorConfig stores nested anthropic keys on disk", () => {
  return withConfig(async () => {
    const next = patchOperatorConfig({ anthropic: { key: "sk-nested-secret" } });
    assert.equal(next.apiKeys.anthropic, "sk-nested-secret");
    const disk = JSON.parse(readFileSync(process.env.HARNESS_CONFIG ?? "", "utf8")) as {
      anthropic?: { key?: string };
      apiKeys?: unknown;
    };
    assert.equal(disk.anthropic?.key, "sk-nested-secret");
    assert.equal(disk.apiKeys, undefined);
  });
});

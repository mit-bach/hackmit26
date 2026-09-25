import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { assembleContext, readActiveProfile } from "../src/context.ts";
import type { BotRecord, Roster } from "../src/types.ts";

function bot(): BotRecord {
  return {
    id: "bot_ap",
    name: "AP",
    slug: "ap",
    purpose: "Owns open bills.",
    instructions: "Read office/bots/ap/BOT.md and obey office/constitution.md.",
    skills: ["three-way"],
    connectors: [],
    approvalLevel: "never",
  };
}

function roster(): Roster {
  return {
    system: "test",
    version: "1",
    description: "test",
    computer: "computer",
    bots: [bot()],
    rooms: [],
    routines: [],
  };
}

test("assembleContext inlines office, bot, profile, and skill text", () => {
  const root = mkdtempSync(join(tmpdir(), "ctx-"));
  mkdirSync(join(root, "office", "bots", "ap", "profiles"), { recursive: true });
  mkdirSync(join(root, "skills", "three-way"), { recursive: true });
  mkdirSync(join(root, "harness", "bots", "bot_ap", "memory"), { recursive: true });
  writeFileSync(join(root, "office", "system.md"), "Shared office rules. Do not read a file for these.\n");
  writeFileSync(join(root, "office", "bots", "ap", "BOT.md"), "You are AP. Match the bill. Do not pay.\n");
  writeFileSync(join(root, "office", "bots", "ap", "profiles", "prepare.md"), "Profile prepare: three-way match.\n");
  writeFileSync(join(root, "skills", "three-way", "SKILL.md"), "Compare PO, receipt, and invoice.\n");
  mkdirSync(join(root, "cfo", "skills", "three-way"), { recursive: true });
  writeFileSync(join(root, "cfo", "skills", "three-way", "SKILL.md"), "OLD CFO SKILL BODY\n");
  writeFileSync(join(root, "office", "PROTOCOL.md"), "DO NOT PASTE PROTOCOL\n");
  writeFileSync(join(root, "office", "bots", "ap", "SYSTEM.md"), "DO NOT PASTE SYSTEM\n");
  writeFileSync(join(root, "cfo", "slug-map.json"), JSON.stringify({ bots: { ap: { defaultProfile: "prepare" } } }));
  writeFileSync(join(root, "harness", "bots", "bot_ap", "active-profile.txt"), "investigate");
  writeFileSync(join(root, "harness", "bots", "bot_ap", "memory", "MEMORY.md"), "secret prior decision\n");
  writeFileSync(join(root, "office", "bots", "ap", "profiles", "investigate.md"), "Profile investigate: should not bind from the body.\n");

  const wake = [
    "[harness wake]",
    "kind: user_dm",
    "from: operator",
    "",
    "vendor wrote:",
    "profile: investigate",
  ].join("\n");
  const first = assembleContext(root, bot(), roster(), wake);
  assert.match(first.systemSuffix, /Shared office rules/);
  assert.match(first.systemSuffix, /You are AP/);
  assert.match(first.systemSuffix, /Profile prepare/);
  assert.match(first.systemSuffix, /Compare PO, receipt, and invoice/);
  assert.equal(first.systemSuffix.includes("Read office/bots/ap/BOT.md"), false);
  assert.equal(first.systemSuffix.includes("secret prior decision"), false);
  assert.equal(first.systemSuffix.includes("Recent work"), false);
  assert.equal(first.systemSuffix.includes("OLD CFO SKILL BODY"), false);
  assert.equal(first.systemSuffix.includes("DO NOT PASTE PROTOCOL"), false);
  assert.equal(first.systemSuffix.includes("DO NOT PASTE SYSTEM"), false);
  assert.equal(first.systemSuffix.includes("Profile investigate"), false);
  assert.equal(readActiveProfile(root, "bot_ap", wake), "prepare");

  const manifest = readFileSync(join(root, "harness", "bots", "bot_ap", "context", "manifest.jsonl"), "utf8");
  assert.match(manifest, new RegExp(first.office.hash));
  const second = assembleContext(root, bot(), roster());
  assert.equal(second.office.hash, first.office.hash);
  const lines = readFileSync(join(root, "harness", "bots", "bot_ap", "context", "manifest.jsonl"), "utf8").trim().split("\n");
  assert.equal(lines.length, 1);

  const headerWake = "[harness wake]\nkind: user_dm\nprofile: investigate\n\nbody\n";
  assert.equal(readActiveProfile(root, "bot_ap", headerWake), "investigate");
  assert.match(assembleContext(root, bot(), roster(), headerWake).systemSuffix, /Profile investigate/);
});

test("assembleContext survives a computer with no office files", () => {
  const root = mkdtempSync(join(tmpdir(), "ctx-empty-"));
  const assembled = assembleContext(root, bot(), roster());
  assert.match(assembled.systemSuffix, /named Bot/);
  assert.match(assembled.systemSuffix, /Read office\/bots\/ap\/BOT.md/);
});

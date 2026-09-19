import assert from "node:assert/strict";
import { test } from "node:test";

import { injectMemoryPrefix, readMemoryFile, writeMemoryFile } from "../src/memory.ts";
import { findBot, loadRoster } from "../src/roster.ts";
import { makeComputer } from "./helpers.ts";

test("Memory is per Bot; a peer path with .. is refused", () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const alpha = findBot(roster, "alpha");
  const beta = findBot(roster, "beta");
  assert.ok(alpha);
  assert.ok(beta);

  writeMemoryFile(computer, alpha.id, "MEMORY.md", "alpha secret note\napi_key: sk-test-12345678");
  const stored = readMemoryFile(computer, alpha.id, "MEMORY.md");
  assert.match(stored, /alpha secret note/);
  assert.match(stored, /«redacted»/);

  writeMemoryFile(computer, beta.id, "topics/work.md", "beta topic");
  assert.equal(readMemoryFile(computer, beta.id, "topics/work.md"), "beta topic");
  assert.doesNotMatch(readMemoryFile(computer, beta.id, "MEMORY.md"), /alpha secret note/);

  assert.throws(() => {
    readMemoryFile(computer, beta.id, `../${alpha.id}/memory/MEMORY.md`);
  });
});

test("MEMORY.md injection cuts at 200 lines", () => {
  const computer = makeComputer();
  const roster = loadRoster(computer);
  const alpha = findBot(roster, "alpha");
  assert.ok(alpha);
  const lines = Array.from({ length: 240 }, (_, i) => `line-${i}`).join("\n");
  writeMemoryFile(computer, alpha.id, "MEMORY.md", lines);
  const prefix = injectMemoryPrefix(computer, alpha.id);
  assert.match(prefix, /truncated/);
  assert.ok((prefix.match(/^line-/gm) ?? []).length <= 200);
});

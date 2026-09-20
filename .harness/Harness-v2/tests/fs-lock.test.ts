import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { appendJsonlAtomic, readJsonl } from "../src/fs.ts";

test("appendJsonlAtomic steals a lock whose pid is already dead", () => {
  const dir = mkdtempSync(join(tmpdir(), "harness-lock-"));
  const filePath = join(dir, "events.jsonl");
  writeFileSync(`${filePath}.lock`, "99999999\n");
  appendJsonlAtomic(filePath, { kind: "ok" });
  const rows = readJsonl(filePath);
  assert.equal(rows.length, 1);
  const row = rows[0];
  if (typeof row !== "object" || row === null || !("kind" in row)) {
    assert.fail("expected a kind field");
  }
  assert.equal(row.kind, "ok");
});

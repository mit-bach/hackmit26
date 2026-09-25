import assert from "node:assert/strict";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { sandboxAllowsBash } from "../src/sandbox.ts";

function root(): string {
  return mkdtempSync(join(tmpdir(), "bash-sandbox-"));
}

test("bash denies python and sed writes outside the desk and another Bot's workspace", () => {
  const computer = root();
  const python = sandboxAllowsBash(
    "ap",
    computer,
    `python3 -c "open('harness/roster.json','w').write('x')"`,
  );
  assert.equal(python.allowed, false);

  const sed = sandboxAllowsBash("ap", computer, "sed -i 's/a/b/' harness/roster.json");
  assert.equal(sed.allowed, false);

  const other = sandboxAllowsBash("ap", computer, "cat workspace/cash/packets/x");
  assert.equal(other.allowed, false);

  const own = sandboxAllowsBash("ap", computer, "cat workspace/ap/packets/x");
  assert.equal(own.allowed, true);
});

test("bash denies cd that leaves the Computer and answer-key paths", () => {
  const computer = root();
  assert.equal(sandboxAllowsBash("ap", computer, "cd .. && cat workspace/ap/a").allowed, false);
  assert.equal(sandboxAllowsBash("ap", computer, "cat workspace/ap/expected_outcomes.json").allowed, false);
  assert.equal(sandboxAllowsBash("ap", computer, "cat workspace/ap/holdout/secret.txt").allowed, false);
  assert.equal(sandboxAllowsBash("ap", computer, "cat expected_results.json").allowed, false);
});

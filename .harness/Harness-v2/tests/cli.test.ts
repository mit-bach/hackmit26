import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { makeCfoComputer } from "./helpers.ts";

const here = dirname(fileURLToPath(import.meta.url));
const cliJs = join(here, "../src/cli.js");

test("node dist/src/cli.js roster actually runs the CLI", () => {
  const computer = makeCfoComputer();
  const result = spawnSync(process.execPath, [cliJs, "roster", "--computer", computer], {
    encoding: "utf8",
  });
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /"slug": "ap"/);
  assert.doesNotMatch(result.stdout, /agent-/);
});

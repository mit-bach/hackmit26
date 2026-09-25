import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { applyServeComputerEnv } from "../src/sidecar.ts";
import { resolveOfficeParent } from "../src/server/office-instances.ts";

test("serve env names the Computer and does not discover a client kernel", () => {
  const repo = mkdtempSync(join(tmpdir(), "kernel-repo-"));
  const computer = join(repo, "computer");
  mkdirSync(computer, { recursive: true });
  const env: NodeJS.ProcessEnv = {};
  applyServeComputerEnv(computer, env);
  assert.equal(env.HARNESS_COMPUTER, computer);
  assert.equal(env.CFO_KERNEL, undefined);
});

test("a Computer is not registered through .cfo-v2/office", () => {
  const repo = mkdtempSync(join(tmpdir(), "office-v3-"));
  const computer = join(repo, ".cfo-v3");
  mkdirSync(join(computer, "harness"), { recursive: true });
  const v2 = join(repo, ".cfo-v2", "office");
  mkdirSync(v2, { recursive: true });
  writeFileSync(
    join(v2, "office.json"),
    JSON.stringify({
      currentId: "live",
      instances: [{ id: "live", name: "Live", computerRel: "../../.cfo-v3", createdAt: "t" }],
    }),
  );
  assert.equal(resolveOfficeParent(computer), join(computer, ".office"));
});

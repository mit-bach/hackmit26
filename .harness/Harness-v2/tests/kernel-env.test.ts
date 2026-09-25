import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { applyServeComputerEnv, resolveCfoKernel } from "../src/sidecar.ts";
import { resolveOfficeParent } from "../src/server/office-instances.ts";

test("resolveCfoKernel uses the Computer kernel and never a directory named .cfo", () => {
  const repo = mkdtempSync(join(tmpdir(), "kernel-repo-"));
  const old = join(repo, ".cfo");
  mkdirSync(old, { recursive: true });
  writeFileSync(join(old, "cfo_kernel"), "");
  const computer = join(repo, ".cfo-v3");
  mkdirSync(join(computer, "kernel"), { recursive: true });
  writeFileSync(join(computer, "kernel", "cfo_kernel"), "");

  const env: NodeJS.ProcessEnv = { CFO_KERNEL: old };
  assert.equal(resolveCfoKernel(computer, env), join(computer, "kernel"));
  applyServeComputerEnv(computer, env);
  assert.equal(env.HARNESS_COMPUTER, computer);
  assert.equal(env.CFO_KERNEL, join(computer, "kernel"));
  assert.equal(env.CFO_KERNEL?.includes("/.cfo/") || env.CFO_KERNEL?.endsWith("/.cfo"), false);
  assert.equal(String(env.HARNESS_COMPUTER).includes(".cfo-v2/office/computer"), false);
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

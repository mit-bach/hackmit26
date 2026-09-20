import assert from "node:assert/strict";
import {existsSync, mkdtempSync, rmSync, writeFileSync} from "node:fs";
import {tmpdir} from "node:os";
import {dirname, join} from "node:path";
import {describe, it} from "node:test";
import {fileURLToPath} from "node:url";

import {callConnectedTool} from "./call.ts";
import {isRecord, loadClientFiles, parseSlugMap} from "./load.ts";
import {bindBot, botIdForSlug, parseProfileFromWake} from "./profile.ts";
import {searchConnectedTools} from "./search.ts";
import {intersectSkillNames} from "./skills.ts";

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

function filesOf(): ReturnType<typeof loadClientFiles> {
  return loadClientFiles(computerRoot);
}

describe("cfo facade bind", () => {
  it("AP Preparer grants differ from AP Approver", () => {
    const files = filesOf();
    const preparer = files.grants.byDisplayName["AP Preparer"];
    const approver = files.grants.byDisplayName["AP Approver"];
    assert.ok(preparer);
    assert.ok(approver);
    assert.ok(preparer.ops.includes("tools.get_invoice"));
    assert.equal(approver.ops.includes("tools.get_invoice"), false);
    assert.notDeepEqual(preparer.ops, approver.ops);
  });

  it("ctl-pay id uses underscores and cannot see AP RECORD_TOOLS", async () => {
    const files = filesOf();
    assert.equal(botIdForSlug("ctl-pay"), "bot_ctl_pay");
    const bind = bindBot({
      computerRoot,
      slug: "ctl-pay",
      profile: "review-match",
      grants: files.grants,
      slugMap: files.slugMap,
    });
    assert.equal(bind.botId, "bot_ctl_pay");
    const invoice = searchConnectedTools(bind, files.catalog, {query: "tools.get_invoice"});
    assert.equal(invoice.some((hit) => hit.id === "tools.get_invoice"), false);
    const call = await callConnectedTool(
      bind,
      files.catalog,
      {name: "tools.get_invoice", args: {invoice_id: "INV-001"}},
      undefined,
      null,
    );
    assert.equal(call.ok, false);
    assert.equal(call.error, "forbidden");
  });

  it("ap / prepare cannot see create_accrual", async () => {
    const files = filesOf();
    const bind = bindBot({
      computerRoot,
      slug: "ap",
      profile: "prepare",
      grants: files.grants,
      slugMap: files.slugMap,
    });
    const hits = searchConnectedTools(bind, files.catalog, {query: "create_accrual"});
    assert.equal(hits.length, 0);
    const invoice = searchConnectedTools(bind, files.catalog, {query: "tools.get_invoice"});
    assert.equal(invoice.some((hit) => hit.id === "tools.get_invoice"), true);
    const call = await callConnectedTool(
      bind,
      files.catalog,
      {name: "accrual.tools.create_accrual", args: {}, idempotencyKey: "k1"},
      undefined,
      null,
    );
    assert.equal(call.ok, false);
    assert.equal(call.error, "forbidden");
  });

  it("audit / interpret in operational phase cannot see get_audit_ground_truth", () => {
    const files = filesOf();
    const inCatalog = files.catalog.ops.some((op) => op.id === "audit.tools.get_audit_ground_truth");
    assert.equal(inCatalog, true);
    const bind = bindBot({
      computerRoot,
      slug: "audit",
      profile: "interpret",
      phase: "operational",
      grants: files.grants,
      slugMap: files.slugMap,
    });
    const hits = searchConnectedTools(bind, files.catalog, {query: "get_audit_ground_truth"});
    assert.equal(hits.length, 0);
    const grant = files.grants.byDisplayName["Auditor Agent"];
    assert.ok(grant);
    assert.equal(grant.ops.includes("audit.tools.get_audit_ground_truth"), false);
  });

  it("close / accrue consequential write routes to ctl-books, not ask_user", async () => {
    const files = filesOf();
    const scratch = mkdtempSync(join(tmpdir(), "cfo-facade-"));
    try {
      const bind = bindBot({
        computerRoot: scratch,
        slug: "close",
        profile: "accrue",
        grants: files.grants,
        slugMap: files.slugMap,
      });
      const missingKey = await callConnectedTool(
        bind,
        files.catalog,
        {name: "accrual.tools.create_accrual", args: {vendor: "Acme"}},
        undefined,
        null,
      );
      assert.equal(missingKey.error, "idempotency_required");
      const routed = await callConnectedTool(
        bind,
        files.catalog,
        {name: "accrual.tools.create_accrual", args: {vendor: "Acme"}, idempotencyKey: "accrual-1"},
        undefined,
        null,
      );
      assert.equal(routed.ok, false);
      assert.equal(routed.error, "verifier_required");
      assert.equal(isRecord(routed.result), true);
      if (!isRecord(routed.result)) {
        throw new Error("expected verifier packet");
      }
      assert.equal(routed.result.verifier, "ctl-books");
      assert.equal(typeof routed.result.instruction, "string");
      assert.match(String(routed.result.instruction), /Never ask_user/);
    } finally {
      rmSync(scratch, {recursive: true, force: true});
    }
  });

  it("refuses a union slug-map list", () => {
    assert.throws(() =>
      parseSlugMap({
        version: "1",
        bots: {
          ap: ["AP Preparer", "AP Approver"],
        },
      }),
    );
  });

  it("stripe payout has no Connectors until a constructor exists", () => {
    const files = filesOf();
    const bind = bindBot({
      computerRoot,
      slug: "stripe",
      profile: "payout",
      grants: files.grants,
      slugMap: files.slugMap,
    });
    assert.equal(bind.connectors, false);
    assert.equal(bind.refuseReason, "missing_display_name");
    assert.equal(searchConnectedTools(bind, files.catalog, {query: ""}).length, 0);
  });

  it("skill names intersect roster when roster is nonempty", () => {
    const names = intersectSkillNames(["three-way-match-analysis", "ap-exception-investigation"], [
      "three-way-match-analysis",
    ]);
    assert.deepEqual(names, ["three-way-match-analysis"]);
  });

  it("reads profile from wake text and replaces, never unions", () => {
    const named = parseProfileFromWake("[harness wake]\nprofile: approve\n\nReview this bill.");
    assert.equal(named, "approve");
    const files = filesOf();
    const prepare = bindBot({
      computerRoot,
      slug: "ap",
      profile: "prepare",
      grants: files.grants,
      slugMap: files.slugMap,
    });
    const investigate = bindBot({
      computerRoot,
      slug: "ap",
      profile: "investigate",
      grants: files.grants,
      slugMap: files.slugMap,
    });
    assert.ok(prepare.grant.ops.includes("tools.get_invoice"));
    assert.ok(investigate.grant.ops.includes("tools.get_prior_cases"));
    assert.notDeepEqual([...prepare.grant.ops], [...investigate.grant.ops]);
    assert.ok(prepare.grant.ops.length < investigate.grant.ops.length);
  });

  it("ctl-pay cannot hold RECORD_TOOLS, pay-run rebuild, or create_accrual", async () => {
    const files = filesOf();
    const match = bindBot({
      computerRoot,
      slug: "ctl-pay",
      profile: "review-match",
      grants: files.grants,
      slugMap: files.slugMap,
    });
    const pay = bindBot({
      computerRoot,
      slug: "ctl-pay",
      profile: "review-pay",
      grants: files.grants,
      slugMap: files.slugMap,
    });
    assert.equal(searchConnectedTools(match, files.catalog, {query: "tools.get_invoice"}).length, 0);
    assert.equal(searchConnectedTools(pay, files.catalog, {query: "get_payment_candidates"}).length, 0);
    assert.equal(searchConnectedTools(pay, files.catalog, {query: "get_approved_pool"}).length, 0);
    const accrual = await callConnectedTool(
      pay,
      files.catalog,
      {name: "accrual.tools.create_accrual", args: {}, idempotencyKey: "ctl-pay-accrual"},
      undefined,
      null,
    );
    assert.equal(accrual.ok, false);
    assert.equal(accrual.error, "forbidden");
    const rebuild = await callConnectedTool(
      pay,
      files.catalog,
      {name: "scheduling.tools.get_payment_candidates", args: {}},
      undefined,
      null,
    );
    assert.equal(rebuild.ok, false);
    assert.equal(rebuild.error, "forbidden");
  });

  it("ctl-books cannot create_accrual on lock or review-treatment", async () => {
    const files = filesOf();
    for (const profile of ["lock", "review-treatment"] as const) {
      const bind = bindBot({
        computerRoot,
        slug: "ctl-books",
        profile,
        grants: files.grants,
        slugMap: files.slugMap,
      });
      const hits = searchConnectedTools(bind, files.catalog, {query: "create_accrual"});
      assert.equal(hits.length, 0);
      const call = await callConnectedTool(
        bind,
        files.catalog,
        {name: "accrual.tools.create_accrual", args: {}, idempotencyKey: `ctl-books-${profile}`},
        undefined,
        null,
      );
      assert.equal(call.error, "forbidden");
    }
  });

  it("completed Verifier Handle lets a consequential op past intercept", async () => {
    const files = filesOf();
    const scratch = mkdtempSync(join(tmpdir(), "cfo-handle-"));
    try {
      const bind = bindBot({
        computerRoot: scratch,
        slug: "close",
        profile: "accrue",
        grants: files.grants,
        slugMap: files.slugMap,
      });
      const pending = await callConnectedTool(
        bind,
        files.catalog,
        {name: "accrual.tools.create_accrual", args: {vendor: "Acme"}, idempotencyKey: "accrual-2"},
        undefined,
        null,
      );
      assert.equal(pending.error, "verifier_required");
      assert.equal(isRecord(pending.result), true);
      if (!isRecord(pending.result)) {
        throw new Error("expected intercept packet");
      }
      const handleId = String(pending.result.handleId);
      const handlePath = join(scratch, "workspace", "verifier", "handles", `${handleId}.json`);
      writeFileSync(
        handlePath,
        `${JSON.stringify({
          id: handleId,
          status: "completed",
          decision: "CONCUR",
          op: "accrual.tools.create_accrual",
        })}\n`,
      );
      const after = await callConnectedTool(
        bind,
        files.catalog,
        {name: "accrual.tools.create_accrual", args: {vendor: "Acme"}, idempotencyKey: "accrual-2"},
        undefined,
        handleId,
      );
      assert.equal(after.error, "sidecar_unavailable");
      assert.notEqual(after.error, "verifier_required");
    } finally {
      rmSync(scratch, {recursive: true, force: true});
    }
  });
});

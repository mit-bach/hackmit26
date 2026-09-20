import assert from "node:assert/strict";
import { existsSync, lstatSync, mkdirSync, mkdtempSync, readlinkSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { test } from "node:test";

import { initComputer } from "../src/computer.ts";
import { writeJsonAtomic } from "../src/fs.ts";
import { protocolLogPath, rosterPath } from "../src/paths.ts";
import { appendProtocol, readProtocol } from "../src/protocol-log.ts";
import { loadRoster } from "../src/roster.ts";
import {
  createOfficeInstance,
  ensureOfficeState,
  resolveServeComputer,
  selectOfficeInstance,
} from "../src/server/office-instances.ts";
import { startServer } from "../src/server/http.ts";
import { FLOOR_ROSTER } from "./helpers.ts";

function makeOfficeComputer(): { readonly parent: string; readonly computer: string } {
  const parent = mkdtempSync(join(tmpdir(), "office-desk-"));
  const computer = join(parent, "computer");
  mkdirSync(join(computer, "harness"), { recursive: true });
  mkdirSync(join(computer, "workspace"), { recursive: true });
  writeJsonAtomic(rosterPath(computer), FLOOR_ROSTER);
  initComputer(computer, FLOOR_ROSTER);
  writeFileSync(join(computer, "workspace", "note.md"), "context for beta\n");
  return { parent, computer };
}

test("missing office.json registers the live computer in place", () => {
  const { parent, computer } = makeOfficeComputer();
  assert.equal(existsSync(join(parent, "office.json")), false);
  const office = ensureOfficeState(computer);
  assert.equal(office.currentId, "live");
  assert.equal(office.instances.length, 1);
  assert.equal(office.instances[0]?.id, "live");
  assert.equal(office.instances[0]?.name, "Live");
  assert.equal(office.instances[0]?.computerRel, "computer");
  assert.equal(existsSync(join(parent, "office.json")), true);
  assert.equal(existsSync(join(computer, "harness", "roster.json")), true);
});

test("create fresh instance clones template files and leaves live protocol intact", () => {
  const { parent, computer } = makeOfficeComputer();
  const dataTarget = join(parent, "shared-data");
  mkdirSync(dataTarget, { recursive: true });
  symlinkSync(dataTarget, join(computer, "data"));
  appendProtocol(computer, { type: "note", text: "stay on live" });
  assert.ok(readProtocol(computer).length > 0);

  const created = createOfficeInstance(computer, "fresh-protocol");
  assert.equal(created.instance.id, "fresh-protocol");
  assert.equal(created.office.currentId, "live");
  const dest = created.computerRoot;
  assert.equal(dest, join(parent, "instances", "fresh-protocol"));
  assert.equal(existsSync(join(dest, "harness", "roster.json")), true);
  assert.equal(existsSync(join(computer, "harness", "roster.json")), true);
  assert.equal(readProtocol(computer).length > 0, true);
  assert.equal(readProtocol(dest).length, 0);
  const protocolFile = protocolLogPath(dest);
  if (existsSync(protocolFile)) {
    assert.equal(readProtocol(dest).length, 0);
  }
  const roster = loadRoster(dest);
  assert.equal(roster.bots.length, 3);
  assert.ok(roster.bots.some((bot) => bot.slug === "alpha"));
  assert.equal(existsSync(join(dest, "workspace", "note.md")), true);
  assert.equal(lstatSync(join(dest, "data")).isSymbolicLink(), true);
  assert.equal(resolveLink(join(dest, "data")), dataTarget);
  assert.equal(existsSync(join(dest, "harness", "protocol.jsonl")) ? readProtocol(dest).length : 0, 0);
});

test("select switches currentId without moving the live tree", () => {
  const { computer } = makeOfficeComputer();
  const created = createOfficeInstance(computer, "desk-two");
  assert.equal(created.office.currentId, "live");
  const selected = selectOfficeInstance(computer, created.instance.id);
  assert.equal(selected.office.currentId, created.instance.id);
  assert.equal(selected.computerRoot, created.computerRoot);
  assert.equal(resolveServeComputer(computer), created.computerRoot);
  const back = selectOfficeInstance(computer, "live");
  assert.equal(back.office.currentId, "live");
  assert.equal(resolveServeComputer(computer), computer);
  assert.equal(existsSync(join(computer, "harness", "roster.json")), true);
});

test("GET /api/office-instances and POST create/select round-trip", async () => {
  const { computer } = makeOfficeComputer();
  const started = await startServer({
    computerRoot: computer,
    port: 0,
    workers: false,
    sidecar: false,
  });
  try {
    const listed = (await (await fetch(`${started.url}/api/office-instances`)).json()) as {
      currentId: string;
      instances: readonly { id: string; computerRel: string }[];
    };
    assert.equal(listed.currentId, "live");
    assert.ok(listed.instances.some((row) => row.id === "live" && row.computerRel === "computer"));

    const created = (await (
      await fetch(`${started.url}/api/office-instances`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name: "fresh-protocol" }),
      })
    ).json()) as {
      instance: { id: string };
      currentId: string;
      computerRoot: string;
    };
    assert.equal(created.instance.id, "fresh-protocol");
    assert.equal(created.currentId, "live");
    assert.equal(readProtocol(created.computerRoot).length, 0);

    const selected = (await (
      await fetch(`${started.url}/api/office-instances/${encodeURIComponent(created.instance.id)}/select`, {
        method: "POST",
      })
    ).json()) as { currentId: string; computerRoot: string };
    assert.equal(selected.currentId, "fresh-protocol");

    const office = (await (await fetch(`${started.url}/api/office`)).json()) as { computerRoot: string };
    assert.equal(office.computerRoot, created.computerRoot);

    const live = (await (
      await fetch(`${started.url}/api/office-instances/live/select`, { method: "POST" })
    ).json()) as { currentId: string };
    assert.equal(live.currentId, "live");
  } finally {
    await started.stop();
  }
});

function resolveLink(path: string): string {
  return resolve(dirname(path), readlinkSync(path));
}

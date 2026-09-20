/**
 * Fake Handle path for session 12.
 * Accept is not complete. Does not spawn Pi.
 *
 * Usage from repo root:
 *   node .cfo-v2/office/tests/fake_handles.mjs
 */
import {mkdirSync, writeFileSync} from "node:fs";
import {dirname, join, resolve} from "node:path";
import {fileURLToPath, pathToFileURL} from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, "../../..");
const computer = resolve(repo, ".cfo-v2/office/computer");
const harnessSrc = resolve(repo, ".harness/Harness-v2/src");

const {initComputer} = await import(pathToFileURL(join(harnessSrc, "computer.ts")).href);
const {sendPrompt} = await import(pathToFileURL(join(harnessSrc, "send.ts")).href);
const {findHandle} = await import(pathToFileURL(join(harnessSrc, "handle.ts")).href);

function writePacket(rel, body) {
  const path = join(computer, rel);
  mkdirSync(dirname(path), {recursive: true});
  writeFileSync(path, `${JSON.stringify(body, null, 2)}\n`);
  return rel;
}

initComputer(computer);

const sourcePath = writePacket("workspace/sources/email/MSG-S12.json", {
  bot: "email",
  profile: "invoice",
  source_id: "MSG-S12",
  classification: "invoice",
  destination: {slug: "ap", profile: "prepare"},
});
const apPath = writePacket("workspace/ap/packets/INV-S12.json", {
  bot: "ap",
  profile: "prepare",
  invoice_id: "INV-S12",
  proposal: "APPROVE",
  destination: {slug: "ctl-pay", profile: "review-match"},
});

const toAp = sendPrompt({
  computerRoot: computer,
  from: "email",
  to: "ap",
  prompt: `profile: prepare\npath: ${sourcePath}\nLanded a vendor bill. Do not invent amounts.`,
  paths: [sourcePath],
  kind: "a2a_handoff",
});
const toCtl = sendPrompt({
  computerRoot: computer,
  from: "ap",
  to: "ctl-pay",
  prompt: `profile: review-match\npath: ${apPath}\nApprove-shaped draft. Concur or refuse. Never a person.`,
  paths: [apPath],
  kind: "a2a_handoff",
});

if (!toAp.accepted || !toCtl.accepted || !toAp.handleId || !toCtl.handleId) {
  throw new Error(`accept failed: ${JSON.stringify({toAp, toCtl})}`);
}

const apHandle = findHandle(computer, toAp.handleId);
const ctlHandle = findHandle(computer, toCtl.handleId);
if (!apHandle || !ctlHandle) {
  throw new Error("handle files missing");
}
if (apHandle.status !== "accepted" || ctlHandle.status !== "accepted") {
  throw new Error(`expected accepted, got ${apHandle.status} ${ctlHandle.status}`);
}
if (apHandle.status === "completed" || ctlHandle.status === "completed") {
  throw new Error("accept must not complete");
}

process.stdout.write(
  JSON.stringify(
    {
      computer,
      sourcePath,
      apPath,
      ap: {handleId: toAp.handleId, status: apHandle.status, to: apHandle.toSlug},
      ctlPay: {handleId: toCtl.handleId, status: ctlHandle.status, to: ctlHandle.toSlug},
      acceptIsNotComplete: true,
    },
    null,
    2,
  ) + "\n",
);

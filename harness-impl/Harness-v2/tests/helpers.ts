import { mkdirSync, writeFileSync } from "node:fs";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { initComputer } from "../src/computer.ts";
import { writeJsonAtomic } from "../src/fs.ts";
import { rosterPath } from "../src/paths.ts";
import type { Roster } from "../src/types.ts";

export const FLOOR_ROSTER: Roster = {
  system: "protocol-floor",
  version: "1",
  description: "Two specialists and a third for Room rounds. Not a domain product.",
  computer: ".",
  bots: [
    {
      id: "bot_alpha",
      name: "Alpha",
      slug: "alpha",
      purpose: "owns handoff tests and writes shared files",
      instructions: "Write context as files. Hand off with bot_send_prompt. Await done.",
      skills: [],
      connectors: [],
      approvalLevel: "ask",
    },
    {
      id: "bot_beta",
      name: "Beta",
      slug: "beta",
      purpose: "receives handoffs and returns a short result",
      instructions: "Read the named path. Write a result path. Stop.",
      skills: [],
      connectors: [],
      approvalLevel: "ask",
    },
    {
      id: "bot_gamma",
      name: "Gamma",
      slug: "gamma",
      purpose: "third member for Room Host order",
      instructions: "Answer in two lines when the Host wakes you.",
      skills: [],
      connectors: [],
      approvalLevel: "always",
    },
  ],
  rooms: [{ id: "floor", title: "Floor", members: ["alpha", "beta", "gamma"] }],
  routines: [
    {
      name: "morning-brief",
      bot: "beta",
      cadence: "daily",
      prompt: "Write a two-line status into workspace/brief.md",
      conversation: "operator_dm",
    },
  ],
};

export function makeComputer(): string {
  const dir = mkdtempSync(join(tmpdir(), "harness-v2-"));
  mkdirSync(join(dir, "harness"), { recursive: true });
  mkdirSync(join(dir, "workspace"), { recursive: true });
  writeJsonAtomic(rosterPath(dir), FLOOR_ROSTER);
  initComputer(dir, FLOOR_ROSTER);
  writeFileSync(join(dir, "workspace", "note.md"), "context for beta\n");
  return dir;
}

export const CFO_ROSTER: Roster = {
  system: "cfo-floor",
  version: "1",
  description: "Six specialists. Domain lives in this file, not in the Harness runtime.",
  computer: ".",
  bots: [
    {
      id: "bot_ingest",
      name: "Ingest",
      slug: "ingest",
      purpose: "owns source files landing on the Computer",
      instructions: "Write a path. Hand off. Do not invent amounts.",
      skills: [],
      connectors: [],
      approvalLevel: "ask",
    },
    {
      id: "bot_ap",
      name: "Payables",
      slug: "ap",
      purpose: "owns payables checks on named paths",
      instructions: "Read the path. Write a result path. Hand off once.",
      skills: [],
      connectors: [],
      approvalLevel: "ask",
    },
    {
      id: "bot_ar",
      name: "Receivables",
      slug: "ar",
      purpose: "owns receivables follow-up on named paths",
      instructions: "Read the path. Write a result path.",
      skills: [],
      connectors: [],
      approvalLevel: "ask",
    },
    {
      id: "bot_cash",
      name: "Cash",
      slug: "cash",
      purpose: "owns cash-position notes on named paths",
      instructions: "Read the path. Write a cash note. Do not pay.",
      skills: [],
      connectors: [],
      approvalLevel: "ask",
    },
    {
      id: "bot_close",
      name: "Close",
      slug: "close",
      purpose: "owns period-close checklist files",
      instructions: "Read result paths. Write close/status.md.",
      skills: [],
      connectors: [],
      approvalLevel: "always",
    },
    {
      id: "bot_audit",
      name: "Audit",
      slug: "audit",
      purpose: "reads protocol and result paths; does not rewrite sources",
      instructions: "Read protocol. Write findings. Do not edit source files.",
      skills: [],
      connectors: [],
      approvalLevel: "ask",
    },
  ],
  rooms: [
    { id: "floor", title: "Floor", members: ["ingest", "ap", "ar", "cash", "close", "audit"] },
    { id: "pay", title: "Pay cycle", members: ["ingest", "ap", "cash"] },
  ],
  routines: [
    {
      name: "morning-brief",
      bot: "close",
      cadence: "daily",
      prompt: "Write two lines into workspace/close/brief.md",
      conversation: "operator_dm",
    },
  ],
};

export function makeCfoComputer(): string {
  const dir = mkdtempSync(join(tmpdir(), "harness-cfo-"));
  mkdirSync(join(dir, "harness"), { recursive: true });
  mkdirSync(join(dir, "workspace", "inbox"), { recursive: true });
  writeJsonAtomic(rosterPath(dir), CFO_ROSTER);
  initComputer(dir, CFO_ROSTER);
  writeFileSync(join(dir, "workspace", "inbox", "INV-1001.md"), "Vendor: Northwind\nAmount: 1280.00\n");
  return dir;
}

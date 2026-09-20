import { mkdirSync } from "node:fs";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { initComputer } from "../src/computer.ts";
import { writeJsonAtomic } from "../src/fs.ts";
import { rosterPath } from "../src/paths.ts";
import { readProtocol } from "../src/protocol-log.ts";
import { loadOperatorConfig } from "../src/server/operator-config.ts";
import { startServer } from "../src/server/http.ts";
import type { Roster } from "../src/types.ts";

process.env.HARNESS_CONFIG = "/tmp/harness-live-xai.json";

const roster: Roster = {
  system: "sky-floor",
  version: "1",
  description: "Two Bots to prove a natural-language ask.",
  computer: ".",
  bots: [
    {
      id: "bot_alpha",
      name: "Alpha",
      slug: "alpha",
      purpose: "asks teammates questions from the Operator",
      instructions: "When asked to consult a teammate, use bot_ask.",
      skills: [],
      connectors: [],
      approvalLevel: "ask",
    },
    {
      id: "bot_beta",
      name: "Beta",
      slug: "beta",
      purpose: "answers short factual questions",
      instructions: "Answer in one short sentence. If asked the color of the sky, reply with the single word blue.",
      skills: [],
      connectors: [],
      approvalLevel: "ask",
    },
  ],
  rooms: [],
  routines: [],
};

const computer = mkdtempSync(join(tmpdir(), "harness-sky-"));
mkdirSync(join(computer, "harness"), { recursive: true });
mkdirSync(join(computer, "workspace"), { recursive: true });
writeJsonAtomic(rosterPath(computer), roster);
initComputer(computer, roster);

const home = loadOperatorConfig();
const started = await startServer({
  computerRoot: computer,
  host: "127.0.0.1",
  port: 8794,
  workers: true,
  lazyWorkers: false,
  fakeWorkers: false,
  autoRoutines: false,
  sidecar: false,
  config: {
    ...home,
    spawnPolicy: "eager",
    provider: home.provider ?? "xai",
    model: home.model ?? "grok-4.5",
    openBrowser: false,
    port: 8794,
  },
});

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

try {
  let sessions: Array<{ slug: string; alive: boolean }> = [];
  for (let i = 0; i < 30; i += 1) {
    sessions = (await (await fetch(`${started.url}/api/sessions`)).json()) as Array<{
      slug: string;
      alive: boolean;
    }>;
    if (sessions.filter((row) => row.alive).length >= 2) {
      break;
    }
    await sleep(1000);
  }
  process.stdout.write(`${JSON.stringify({ url: started.url, computer, sessions }, null, 2)}\n`);

  const sent = (await (
    await fetch(`${started.url}/api/bots/alpha/messages`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text: "Ask one of your agents what color the sky is" }),
    })
  ).json()) as { accepted?: boolean; handleId?: string; error?: string };
  process.stdout.write(`${JSON.stringify({ sent }, null, 2)}\n`);
  if (!sent.handleId) {
    throw new Error("no handle");
  }

  const awaited = (await (
    await fetch(`${started.url}/api/handles/${sent.handleId}/await?timeoutMs=120000`, {
      method: "POST",
    })
  ).json()) as { done?: boolean; status?: string; result?: string };
  const protocol = readProtocol(computer).map((row) => ({
    seq: row.seq,
    type: row.type,
    from: row.from,
    to: row.to,
    slug: row.slug,
    text: (row.text ?? "").slice(0, 160),
  }));
  process.stdout.write(`${JSON.stringify({ awaited, protocol }, null, 2)}\n`);
  if (!awaited.done || awaited.status !== "completed") {
    process.exitCode = 2;
  } else if (!/blue/i.test(awaited.result ?? "")) {
    process.exitCode = 3;
  }
} finally {
  await started.stop();
}

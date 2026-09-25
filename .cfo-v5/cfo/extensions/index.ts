/**
 * CFO v5 Pi extension. Tools are search, call, and complete_step.
 * The step is not a profile. A profile: line in mail changes nothing.
 */

import { readFileSync } from "node:fs";
import { join } from "node:path";

import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

import { callConnectedTool } from "../engine/call.ts";
import { completeStep } from "../engine/complete.ts";
import { loadCatalog, loadStepGrants, opsForStep, readOpsForBot } from "../engine/grants.ts";
import { listItems } from "../engine/ledger.ts";

interface WakeRef {
  readonly item?: string;
  readonly step?: string;
}

function toolText(payload: unknown): {
  content: Array<{ type: "text"; text: string }>;
  details: unknown;
} {
  return {
    content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
    details: payload,
  };
}

function botIdFor(slug: string): string {
  return `bot_${slug.replaceAll("-", "_")}`;
}

function currentWake(computerRoot: string, slug: string): WakeRef {
  const path = join(computerRoot, "harness", "bots", botIdFor(slug), "inbox.jsonl");
  let text = "";
  try {
    text = readFileSync(path, "utf8");
  } catch {
    return {};
  }
  const rows: Array<{ status?: string; prompt?: string }> = [];
  for (const line of text.split("\n")) {
    if (!line.trim()) continue;
    try {
      rows.push(JSON.parse(line) as { status?: string; prompt?: string });
    } catch {
      continue;
    }
  }
  const claimed = [...rows].reverse().find((row) => row.status === "claimed");
  const row = claimed ?? [...rows].reverse().find((row) => row.status === "pending");
  if (!row?.prompt) return {};
  const item = /^item:\s*(.+)$/m.exec(row.prompt)?.[1]?.trim();
  const step = /^step:\s*(.+)$/m.exec(row.prompt)?.[1]?.trim();
  return { item, step };
}

function successorText(computerRoot: string, slug: string): string {
  const items = listItems(computerRoot).filter((item) => item.owner === slug);
  const open = items.filter((item) => !item.terminal);
  const held = items.filter((item) => item.terminal === "hold");
  const lines = [
    "Open ledger items:",
    ...open.map((item) => `${item.id} ${item.step}`),
    `Memory file: sandboxes/${slug}/memory/MEMORY.md`,
    "Held items:",
    ...held.map((item) => {
      const reason = typeof item.history.at(-1)?.result.reason === "string" ? item.history.at(-1)?.result.reason : "";
      return `${item.id} ${item.step} ${reason ?? ""}`.trim();
    }),
  ];
  return lines.join("\n");
}

export default function cfoExtension(pi: ExtensionAPI): void {
  const slug = process.env.HARNESS_BOT?.trim();
  if (!slug) return;
  const computerRoot = process.env.HARNESS_COMPUTER?.trim() || process.cwd();
  let memoryTurn = false;
  let rotated = false;

  pi.registerTool({
    name: "search_connected_tools",
    label: "Search connected tools",
    description: "List Catalog ops this step allows. A skill does not grant a tool.",
    parameters: Type.Object({
      query: Type.Optional(Type.String()),
    }),
    execute: async () => {
      const grants = loadStepGrants(computerRoot);
      const catalog = loadCatalog(computerRoot);
      const wake = currentWake(computerRoot, slug);
      const ids = wake.item && wake.step ? opsForStep(grants, slug, wake.step) : readOpsForBot(grants, slug, catalog);
      const ops = ids.map((id) => {
        const meta = catalog.get(id);
        return { id, mutability: meta?.mutability ?? "read" };
      });
      return toolText({ item: wake.item ?? null, step: wake.step ?? null, ops });
    },
  });

  pi.registerTool({
    name: "call_connected_tool",
    label: "Call connected tool",
    description: "Read or propose a Catalog op. Kernel facts come from this tool. A write waits for a structured CONCUR.",
    parameters: Type.Object({
      name: Type.String(),
      args: Type.Optional(Type.Record(Type.String(), Type.Unknown())),
      idempotencyKey: Type.Optional(Type.String()),
    }),
    execute: async (_id, params) => {
      const wake = currentWake(computerRoot, slug);
      const args =
        params.args && typeof params.args === "object" && !Array.isArray(params.args)
          ? (params.args as Record<string, unknown>)
          : {};
      return toolText(
        callConnectedTool({
          computerRoot,
          caller: slug,
          op: params.name,
          args,
          idempotencyKey: typeof params.idempotencyKey === "string" ? params.idempotencyKey : undefined,
          item: wake.item,
        }),
      );
    },
  });

  pi.registerTool({
    name: "complete_step",
    label: "Complete step",
    description: "Finish the current item step with a typed decision. Assistant prose is not a decision.",
    parameters: Type.Object({
      item: Type.String(),
      result: Type.Unknown(),
      paths: Type.Optional(Type.Array(Type.String())),
    }),
    execute: async (_id, params) => {
      const wake = currentWake(computerRoot, slug);
      if (!wake.step) {
        return toolText({ ok: false, error: "no item step is open" });
      }
      const paths = Array.isArray(params.paths) ? params.paths.filter((path): path is string => typeof path === "string") : [];
      return toolText(
        completeStep({
          computerRoot,
          caller: slug,
          item: params.item,
          wakeStep: wake.step,
          result: params.result,
          paths,
        }),
      );
    },
  });

  pi.on("session_before_compact", (event, ctx) => {
    if (event.reason !== "threshold") return;
    if (!memoryTurn) {
      memoryTurn = true;
      pi.sendUserMessage(
        `Write precedents into sandboxes/${slug}/memory/MEMORY.md. Key each precedent by vendor, account, or processor. Do not store a transcript. This turn only writes memory.`,
        { deliverAs: "followUp" },
      );
      return { cancel: true };
    }
    rotate(ctx);
    return { cancel: true };
  });

  pi.on("agent_end", (_event, ctx) => {
    if (!memoryTurn || rotated) return;
    rotate(ctx);
  });

  function rotate(ctx: ExtensionContext): void {
    if (rotated) return;
    rotated = true;
    const text = successorText(computerRoot, slug);
    const sessionCtx = ctx as ExtensionContext & {
      newSession?: (options: {
        withSession?: (next: { sendUserMessage: (content: string) => Promise<void> }) => Promise<void>;
      }) => Promise<{ cancelled: boolean }>;
    };
    if (typeof sessionCtx.newSession === "function") {
      void sessionCtx.newSession({
        withSession: async (next) => {
          await next.sendUserMessage(text);
        },
      });
      return;
    }
    pi.sendUserMessage(text, { deliverAs: "followUp" });
  }
}

import { join, resolve } from "node:path";

import { loadLayout, memoryRel } from "./layout.ts";

export function harnessRoot(computerRoot: string): string {
  return join(resolve(computerRoot), "harness");
}

export function rosterPath(computerRoot: string): string {
  return join(harnessRoot(computerRoot), "roster.json");
}

export function protocolLogPath(computerRoot: string): string {
  return join(harnessRoot(computerRoot), "protocol.jsonl");
}

export function seqPath(computerRoot: string): string {
  return join(harnessRoot(computerRoot), "seq");
}

export function botsRoot(computerRoot: string): string {
  return join(harnessRoot(computerRoot), "bots");
}

export function botDir(computerRoot: string, botId: string): string {
  return join(botsRoot(computerRoot), botId);
}

export function inboxPath(computerRoot: string, botId: string): string {
  return join(botDir(computerRoot, botId), "inbox.jsonl");
}

export function handleDir(computerRoot: string, botId: string): string {
  return join(botDir(computerRoot, botId), "handles");
}

export function handlePath(computerRoot: string, botId: string, handleId: string): string {
  return join(handleDir(computerRoot, botId), `${handleId}.json`);
}

export function lanePath(computerRoot: string, botId: string): string {
  return join(botDir(computerRoot, botId), "lane.json");
}

export function transcriptPath(computerRoot: string, botId: string): string {
  return join(botDir(computerRoot, botId), "transcript.jsonl");
}

export function memoryDir(computerRoot: string, botId: string): string {
  const root = resolve(computerRoot);
  const slug = botId.startsWith("bot_") ? botId.slice(4).replaceAll("_", "-") : botId;
  const layout = loadLayout(root);
  return join(root, memoryRel(layout, slug));
}

export function memoryFile(computerRoot: string, botId: string): string {
  return join(memoryDir(computerRoot, botId), "MEMORY.md");
}

export function memoryTopicsDir(computerRoot: string, botId: string): string {
  return join(memoryDir(computerRoot, botId), "topics");
}

export function memoryLogDir(computerRoot: string, botId: string): string {
  return join(memoryDir(computerRoot, botId), "log");
}

export function roomDir(computerRoot: string, roomId: string): string {
  return join(harnessRoot(computerRoot), "rooms", roomId);
}

export function roomLogPath(computerRoot: string, roomId: string): string {
  return join(roomDir(computerRoot, roomId), "log.jsonl");
}

export function roomLockPath(computerRoot: string, roomId: string): string {
  return join(roomDir(computerRoot, roomId), "host.lock");
}

export function approvalPath(computerRoot: string, approvalId: string): string {
  return join(approvalDir(computerRoot), `${approvalId}.json`);
}

export function receiptPath(computerRoot: string, receiptId: string): string {
  return join(receiptDir(computerRoot), `${receiptId}.json`);
}

export function leaseDir(computerRoot: string): string {
  return join(harnessRoot(computerRoot), "leases");
}

export function approvalDir(computerRoot: string): string {
  return join(harnessRoot(computerRoot), "approvals");
}

export function receiptDir(computerRoot: string): string {
  return join(harnessRoot(computerRoot), "receipts");
}

export function piRuntimePath(computerRoot: string, botId: string): string {
  return join(botDir(computerRoot, botId), "pi-runtime.jsonl");
}

export function piRpcLogPath(computerRoot: string, botId: string): string {
  return join(botDir(computerRoot, botId), "pi-rpc.jsonl");
}

export function piSessionDir(computerRoot: string, botId: string): string {
  return join(botDir(computerRoot, botId), "pi-session");
}

/** Computer-wide tool protocol. Regenerated on init; not a Bot Memory file. */
export function protocolCardPath(computerRoot: string): string {
  return join(harnessRoot(computerRoot), "PROTOCOL.md");
}

/** Per-Bot copy of the tool protocol, next to the session tree. */
export function botSystemPath(computerRoot: string, botId: string): string {
  return join(botDir(computerRoot, botId), "SYSTEM.md");
}

/** Durable AskBot prompt/reply posts. Pair UI reads this file, not session folds. */
export function threadsDir(computerRoot: string): string {
  return join(harnessRoot(computerRoot), "threads");
}

export function threadFilePath(computerRoot: string, pairId: string): string {
  const safe = pairId.replace(/[^A-Za-z0-9._-]+/g, "__");
  return join(threadsDir(computerRoot), `${safe}.json`);
}

export function extensionsManifestPath(computerRoot: string): string {
  return join(harnessRoot(computerRoot), "extensions.json");
}

export function interceptPath(computerRoot: string): string {
  return join(harnessRoot(computerRoot), "intercept.json");
}

export function demoRoot(computerRoot: string): string {
  return join(harnessRoot(computerRoot), "demo");
}

export function demoLatestDir(computerRoot: string): string {
  return join(demoRoot(computerRoot), "latest");
}

export function computerSkillsRoot(computerRoot: string): string {
  return join(resolve(computerRoot), "skills");
}

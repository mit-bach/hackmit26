import { join, resolve } from "node:path";

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
  return join(botDir(computerRoot, botId), "memory");
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

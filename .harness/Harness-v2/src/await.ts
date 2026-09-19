import { existsSync, watch, type FSWatcher } from "node:fs";

import { findHandle, findHandleOwner, isTerminalStatus } from "./handle.ts";
import { handlePath } from "./paths.ts";
import type { AwaitResult } from "./types.ts";

export interface AwaitOptions {
  readonly timeoutMs?: number;
  readonly pollMs?: number;
  readonly waitOnBlocked?: boolean;
  readonly signal?: AbortSignal;
}

export function awaitSnapshot(computerRoot: string, handleId: string): AwaitResult {
  const found = findHandle(computerRoot, handleId);
  if (!found) {
    return { handleId, status: "accepted", done: false };
  }
  return {
    handleId,
    status: found.status,
    done: isTerminalStatus(found.status),
    result: found.result,
    seq: found.seq,
  };
}

export async function awaitTurn(
  computerRoot: string,
  handleId: string,
  options: AwaitOptions = {},
): Promise<AwaitResult> {
  const timeoutMs = options.timeoutMs ?? 300_000;
  const pollMs = options.pollMs ?? 100;
  const started = Date.now();
  const waitOnBlocked = options.waitOnBlocked ?? false;

  const snapshot = (): AwaitResult => awaitSnapshot(computerRoot, handleId);

  const first = snapshot();
  if (first.done || (first.status === "blocked" && !waitOnBlocked)) {
    return first;
  }

  const owner = findHandleOwner(computerRoot, handleId);
  const file = owner ? handlePath(computerRoot, owner, handleId) : undefined;

  return await new Promise<AwaitResult>((resolve) => {
    let settled = false;
    let watcher: FSWatcher | undefined;
    const finish = (result: AwaitResult): void => {
      if (settled) {
        return;
      }
      settled = true;
      watcher?.close();
      clearInterval(timer);
      resolve(result);
    };

    const tick = (): void => {
      if (options.signal?.aborted) {
        finish(snapshot());
        return;
      }
      if (Date.now() - started > timeoutMs) {
        finish(snapshot());
        return;
      }
      const next = snapshot();
      if (next.done || (next.status === "blocked" && !waitOnBlocked)) {
        finish(next);
      }
    };

    if (file && existsSync(file)) {
      try {
        watcher = watch(file, () => {
          tick();
        });
      } catch {
        watcher = undefined;
      }
    }
    const timer = setInterval(tick, pollMs);
    tick();
  });
}

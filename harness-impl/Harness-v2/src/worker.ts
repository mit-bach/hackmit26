import { bindLane, drainOnce, interruptIfStop, type BoundLane } from "./lane.ts";
import { requireBot, loadRoster } from "./roster.ts";
import { sleep } from "./sleep.ts";
import type { InboxItem, TurnResult } from "./types.ts";

export type FakeExecute = (slug: string, item: InboxItem, lane: BoundLane) => Promise<TurnResult>;

export function startFakeWorkers(
  computerRoot: string,
  slugs: readonly string[],
  execute: FakeExecute,
  intervalMs = 25,
): { readonly lanes: ReadonlyMap<string, BoundLane>; stop: () => void } {
  const roster = loadRoster(computerRoot);
  const lanes = new Map<string, BoundLane>();
  const timers: ReturnType<typeof setInterval>[] = [];
  for (const slug of slugs) {
    const bot = requireBot(roster, slug);
    const lane = bindLane(computerRoot, bot);
    lanes.set(slug, lane);
    const timer = setInterval(() => {
      interruptIfStop(lane);
      void drainOnce(lane, (item) => execute(slug, item, lane)).catch((error: unknown) => {
        const message = error instanceof Error ? error.message : String(error);
        process.stderr.write(`harness drain ${slug}: ${message}\n`);
      });
    }, intervalMs);
    timers.push(timer);
  }
  return {
    lanes,
    stop: (): void => {
      for (const timer of timers) {
        clearInterval(timer);
      }
    },
  };
}

export async function runFakeUntilIdle(
  computerRoot: string,
  slugs: readonly string[],
  execute: FakeExecute,
  timeoutMs = 10_000,
): Promise<void> {
  const workers = startFakeWorkers(computerRoot, slugs, execute);
  const started = Date.now();
  try {
    while (Date.now() - started < timeoutMs) {
      let pending = false;
      for (const lane of workers.lanes.values()) {
        if (lane.currentInbox || lane.drainLock) {
          pending = true;
        }
      }
      if (!pending) {
        await sleep(40);
        let still = false;
        for (const lane of workers.lanes.values()) {
          if (lane.currentInbox || lane.drainLock) {
            still = true;
          }
        }
        if (!still) {
          return;
        }
      }
      await sleep(20);
    }
  } finally {
    workers.stop();
  }
}

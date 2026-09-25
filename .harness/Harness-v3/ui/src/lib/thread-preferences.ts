import { useSyncExternalStore } from "react";

export const SHOW_THREADS_KEY = "omb-show-threads";

// Only a renderer preference: no conversation or server configuration belongs
// here. Keep a session choice even if private/blocked storage rejects reads or
// writes; another window's storage event can supersede that choice.
let sessionChoice: boolean | undefined;
const listeners = new Set<() => void>();

function storage(): Storage | undefined {
  try {
    return globalThis.localStorage;
  } catch {
    return undefined;
  }
}

function showThreads(): boolean {
  // Harness Bots have one transcript.jsonl. Task threads are a foreign
  // OpenMausBot product; this preference must not resurrect them from
  // leftover localStorage.
  return false;
}

function notify() {
  for (const listener of listeners) listener();
}

function onStorage(event: StorageEvent) {
  if (event.key !== SHOW_THREADS_KEY && event.key !== null) return;
  if (event.storageArea && event.storageArea !== storage()) return;
  sessionChoice = undefined;
  notify();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  if (listeners.size === 1 && typeof window !== "undefined") {
    window.addEventListener("storage", onStorage);
  }
  return () => {
    listeners.delete(listener);
    if (listeners.size === 0 && typeof window !== "undefined") {
      window.removeEventListener("storage", onStorage);
    }
  };
}

export function setShowThreads(_enabled: boolean): void {
  sessionChoice = false;
  try {
    storage()?.setItem(SHOW_THREADS_KEY, "0");
  } catch {
    // private mode
  }
  notify();
}

export function useShowThreads(): boolean {
  return useSyncExternalStore(subscribe, showThreads, () => false);
}

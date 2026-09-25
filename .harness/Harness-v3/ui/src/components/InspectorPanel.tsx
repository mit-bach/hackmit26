// The raw event inspector: what a thread's turns actually looked like on
// the wire, for the moment a bot misbehaves and the chat view can't say
// why. Three lenses over the same thread:
//
//   Run log — readable, redacted activity from the visible conversation.
//   Events — the harness's normalized RuntimeEvent stream: turns, tool
//            items, requests, token usage, errors. Follows live over SSE.
//   Raw    — the provider's own protocol messages, verbatim (the native
//            tee). Read from disk; refreshed when a turn settles.
//   Sessions — Pi's on-Computer conversation files (Grok chat logs).
//
// Nothing here is captured for the panel's sake — both logs already exist
// under ~/.openmausbot (server/harness/bus.ts, server/drivers/native.ts).
import { useCallback, useEffect, useMemo, useRef, useState, type ReactElement } from "react";
import { Bug, ChevronDown, ChevronRight, RefreshCw, X } from "lucide-react";
import { useStore, visibleMessages, type Bot } from "@/state/store";
import { transcriptVerbosity } from "@/lib/feature-flags";
import { cn } from "@/lib/cn";
import { useCaptionChrome } from "@/components/DesktopCapabilities";
import { formatTime, toRows, type InspectorEntry, type InspectorPage, type InspectorRow } from "@/lib/inspector";
import { openLiveEvents } from "@/lib/live-events";
import type { RuntimeEvent } from "../../shared/runtime-events";
import { RunLog } from "./RunLog";
import { timelineEvents } from "@/lib/taskTimeline";
import { t } from "@/lib/i18n";

type Lens = "run" | "events" | "raw" | "sessions";

export function InspectorPanel({ bot }: { bot: Bot }) {
  const { state, dispatch } = useStore();
  // Docked flush under the Windows caption corner: drop the header 16px.
  const { padClass } = useCaptionChrome();
  const threadId = bot.threadId;
  const verbosity = transcriptVerbosity(state.config);
  const [lens, setLens] = useState<Lens>(() =>
    verbosity === "compact" ? "run" : verbosity === "tools" ? "events" : "raw",
  );
  const activity = useMemo(() => timelineEvents(visibleMessages(bot)), [bot]);
  const [page, setPage] = useState<InspectorPage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set());
  const listRef = useRef<HTMLDivElement>(null);
  const stickToBottom = useRef(true);
  const loadAbort = useRef<AbortController | null>(null);
  const managedRefresh = useRef<() => void>(() => {});

  const load = useCallback(async (): Promise<boolean> => {
    loadAbort.current?.abort();
    const controller = new AbortController();
    loadAbort.current = controller;
    try {
      const res = await fetch(`/api/threads/${threadId}/events?limit=400`, { signal: controller.signal });
      if (!res.ok) throw new Error(`${res.status}`);
      // SAFETY: this same-version renderer calls the harness's typed
      // inspector endpoint; malformed transport data is handled by catch.
      const next = (await res.json()) as InspectorPage;
      if (controller.signal.aborted) return false;
      setPage(next);
      setError(null);
      return true;
    } catch (e) {
      if (controller.signal.aborted) return false;
      setError(e instanceof Error ? e.message : String(e));
      return false;
    } finally {
      if (loadAbort.current === controller) loadAbort.current = null;
    }
  }, [threadId]);

  // history from disk on open / thread change
  useEffect(() => {
    setPage(null);
    setExpanded(new Set());
    stickToBottom.current = true;
    void load();
    return () => loadAbort.current?.abort();
  }, [load]);

  // live: append this thread's runtime events as they stream, and re-read
  // the disk when a turn settles so the native tee (not on the SSE) catches
  // up. Own EventSource on purpose: the store folds runtime events into
  // chat state and does not re-emit them.
  useEffect(() => {
    let alive = true;
    let settle: ReturnType<typeof setTimeout> | null = null;
    let refreshGeneration = 0;
    let refreshing = false;
    const pendingRuntime: RuntimeEvent[] = [];

    const appendRuntime = (runtime: RuntimeEvent) => {
      setPage((prev) => {
        // A disk refresh and replay can overlap. eventId is canonical, so a
        // replayed entry already present in the snapshot is an exact no-op.
        if (
          prev?.entries.some(
            (entry) => entry.kind === "runtime" && entry.data.eventId === runtime.eventId,
          )
        ) {
          return prev;
        }
        const entry: InspectorEntry = { kind: "runtime", at: runtime.createdAt, data: runtime };
        if (!prev) return { entries: [entry], total: { runtime: 1, native: 0 } };
        return { entries: [...prev.entries, entry], total: { ...prev.total, runtime: prev.total.runtime + 1 } };
      });
    };

    const flushPendingRuntime = () => {
      for (const runtime of pendingRuntime.splice(0)) appendRuntime(runtime);
    };

    const refresh = async (flushLiveOnFailure: boolean): Promise<boolean> => {
      const generation = ++refreshGeneration;
      refreshing = true;
      const loaded = await load();
      // A later refresh aborts the earlier fetch. Only its completion owns
      // the buffered live tail, otherwise the earlier finally can flush
      // frames immediately before the newer snapshot overwrites them.
      if (!alive || generation !== refreshGeneration) return false;
      refreshing = false;
      // An ordinary Reload keeps the previous page when its fetch fails, so
      // live frames buffered during that request still belong on that page.
      // A replacement snapshot must not expose them: its caller will close
      // and replay the stream from the last acknowledged cursor instead.
      if (!loaded) {
        if (flushLiveOnFailure) flushPendingRuntime();
        return false;
      }
      flushPendingRuntime();
      return true;
    };
    const requestRefresh = () => void refresh(true);
    const refreshFromSnapshot = (): Promise<boolean> => {
      // A refused resume starts a new stream generation. Frames retained by
      // an earlier failed refresh will be present in the new disk snapshot or
      // replayed again, so do not carry them across the generation boundary.
      pendingRuntime.splice(0);
      return refresh(false);
    };
    managedRefresh.current = requestRefresh;

    const stopLive = openLiveEvents({
      screens: false,
      onSnapshotRequired: refreshFromSnapshot,
      onFrame: (frame) => {
        if (frame.kind !== "runtime") return;
        const event = frame.event;
        if (!event || Array.isArray(event) || Object(event) !== event) return;
        // SAFETY: runtime stream frames are produced from the typed harness
        // bus; this guard rejects non-object transport corruption.
        const runtime = event as RuntimeEvent;
        if (runtime.threadId !== threadId) return;
        if (refreshing) pendingRuntime.push(runtime);
        else appendRuntime(runtime);
        if (runtime.type === "turn.completed" || runtime.type === "runtime.error") {
          if (settle) clearTimeout(settle);
          settle = setTimeout(requestRefresh, 400);
        }
      },
    });
    return () => {
      alive = false;
      if (managedRefresh.current === requestRefresh) managedRefresh.current = () => {};
      stopLive();
      if (settle) clearTimeout(settle);
    };
  }, [threadId, load]);

  const entries = useMemo(
    () => (page ? page.entries.filter((e) => (lens === "raw" ? e.kind === "native" : e.kind === "runtime")) : []),
    [page, lens],
  );
  const rows = useMemo(() => toRows(entries), [entries]);

  // follow the tail unless the user has scrolled up to read
  useEffect(() => {
    const el = listRef.current;
    if (el && stickToBottom.current) el.scrollTop = el.scrollHeight;
  }, [page?.entries.length, rows.length, lens]);
  const onScroll = () => {
    const el = listRef.current;
    if (!el) return;
    stickToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
  };

  const toggle = (key: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });

  const shown = entries.length;
  const total = lens === "raw" ? (page?.total.native ?? 0) : (page?.total.runtime ?? 0);

  return (
    <aside aria-label="Inspector" className="animate-panel-in absolute inset-0 z-40 flex h-full min-w-0 flex-col border-l border-hairline/40 bg-panel lg:static lg:z-auto lg:w-[min(460px,45vw)] lg:shrink-0">
      <div className={cn("flex items-center justify-between px-4 py-3", padClass)}>
        <span className="flex items-center gap-2 text-[15px] font-semibold text-ink">
          <Bug size={16} className="text-ink-secondary" /> Inspector
          <span className="text-[12px] font-normal text-ink-secondary">{t("inspector.subtitle")}</span>
        </span>
        <button
          onClick={() => dispatch({ type: "toggleInspector", open: false })}
          aria-label="Close the Inspector"
          title="Close the Inspector"
          className="rounded-md p-1 text-ink-secondary hover:bg-raised hover:text-ink"
        >
          <X size={18} />
        </button>
      </div>

      <div className="flex items-center gap-2 border-b border-hairline/40 px-4 pb-3">
        <div role="tablist" aria-label={t("inspector.views")} className="flex rounded-lg bg-inset p-0.5" onKeyDown={(event) => {
          const tabs = Array.from(event.currentTarget.querySelectorAll<HTMLButtonElement>('[role="tab"]'));
          const current = tabs.indexOf(document.activeElement as HTMLButtonElement);
          const next = event.key === "ArrowRight" ? (current + 1) % tabs.length
            : event.key === "ArrowLeft" ? (current + tabs.length - 1) % tabs.length
              : event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : -1;
          if (next < 0) return;
          event.preventDefault();
          tabs[next].focus();
          tabs[next].click();
        }}>
          {(["run", "events", "raw", "sessions"] as const).map((l) => (
            <button
              key={l}
              type="button"
              role="tab"
              id={`inspector-tab-${l}`}
              aria-selected={lens === l}
              aria-controls={`inspector-panel-${l}`}
              tabIndex={lens === l ? 0 : -1}
              onClick={() => setLens(l)}
              className={cn(
                "rounded-md px-2.5 py-1 text-[12px] font-medium",
                lens === l ? "bg-raised text-ink" : "text-ink-secondary hover:text-ink",
              )}
            >
              {l === "run"
                ? t("inspector.lens.run")
                : l === "events"
                  ? t("inspector.lens.events")
                  : l === "raw"
                    ? t("inspector.lens.raw")
                    : t("inspector.lens.sessions")}
            </button>
          ))}
        </div>
        {lens !== "run" && lens !== "sessions" && <span className="ml-auto text-[11px] text-ink-secondary">
          {page ? (shown < total ? `last ${shown} of ${total}` : `${shown} entries`) : "loading…"}
        </span>}
        {lens !== "run" && lens !== "sessions" && <button onClick={() => managedRefresh.current()} className="rounded-md p-1 text-ink-secondary hover:bg-raised hover:text-ink" title="Reload from disk">
          <RefreshCw size={14} />
        </button>}
      </div>

      <div role="tabpanel" id={`inspector-panel-${lens}`} aria-labelledby={`inspector-tab-${lens}`} tabIndex={0} className="flex min-h-0 flex-1 flex-col outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent/60">
      {lens === "run" ? (
        <RunLog key={threadId} events={activity} />
      ) : lens === "sessions" ? (
        <SessionLog botId={bot.id} />
      ) : (
        <div ref={listRef} onScroll={onScroll} className="min-h-0 flex-1 overflow-y-auto font-mono text-[11.5px]">
        {error && <div className="px-4 py-3 text-danger">couldn't load: {error}</div>}
        {page && rows.length === 0 && !error && (
          <div className="px-4 py-6 text-ink-secondary">
            {lens === "raw"
              ? t("inspector.empty.raw")
              : t("inspector.empty.events")}
          </div>
        )}
        {rows.map((row) => (
          <Row key={row.key} row={row} open={expanded.has(row.key)} onToggle={() => toggle(row.key)} />
        ))}
      </div>
      )}
      </div>
    </aside>
  );
}

function Row({ row, open, onToggle }: { row: InspectorRow; open: boolean; onToggle: () => void }) {
  return (
    <div
      className={cn(
        "border-b border-hairline/20",
        row.tone === "boundary" && "bg-raised/40",
        row.tone === "error" && "bg-danger/10",
      )}
    >
      <button onClick={onToggle} className="flex w-full items-start gap-2 px-3 py-1.5 text-left hover:bg-raised/60">
        <span className="mt-[1px] shrink-0 text-ink-secondary">{open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}</span>
        <span className="shrink-0 tabular-nums text-ink-secondary">{formatTime(row.at)}</span>
        <span
          className={cn(
            "shrink-0 rounded px-1 text-[10.5px]",
            row.kind === "native" ? "bg-accent/15 text-accent" : row.tone === "error" ? "bg-danger/20 text-danger" : "bg-inset text-ink-secondary",
          )}
        >
          {row.tag}
          {row.count > 1 ? ` ×${row.count}` : ""}
        </span>
        <span className={cn("min-w-0 flex-1 truncate", row.tone === "error" ? "text-danger" : "text-ink")}>{row.summary}</span>
      </button>
      {open && (
        <pre className="max-h-[50vh] overflow-auto whitespace-pre-wrap break-all border-t border-hairline/20 bg-app px-3 py-2 text-[11px] leading-relaxed text-ink">
          {JSON.stringify(row.data, null, 2)}
        </pre>
      )}
    </div>
  );
}

interface SessionSummary {
  readonly name: string;
  readonly id: string;
  readonly path: string;
  readonly startedAt: string;
  readonly messageCount: number;
}

interface SessionTurn {
  readonly id: string;
  readonly role: "user" | "assistant" | "tool";
  readonly text: string;
  readonly at: string;
  readonly toolName?: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseSessionList(body: unknown): SessionSummary[] {
  if (!isRecord(body) || !Array.isArray(body.sessions)) {
    return [];
  }
  return body.sessions.filter((row): row is SessionSummary => {
    if (!isRecord(row) || typeof row.name !== "string") {
      return false;
    }
    return typeof row.path === "string" && typeof row.startedAt === "string";
  });
}

function parseSessionTurns(body: unknown): SessionTurn[] {
  if (!isRecord(body) || !Array.isArray(body.turns)) {
    return [];
  }
  return body.turns.filter((row): row is SessionTurn => {
    if (!isRecord(row) || typeof row.id !== "string" || typeof row.text !== "string") {
      return false;
    }
    return row.role === "user" || row.role === "assistant" || row.role === "tool";
  });
}

function SessionLog({ botId }: { botId: string }): ReactElement {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [turns, setTurns] = useState<SessionTurn[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const loadList = useCallback(async (): Promise<void> => {
    setBusy(true);
    try {
      const res = await fetch(`/api/bots/${encodeURIComponent(botId)}/sessions`);
      if (!res.ok) {
        throw new Error(`${res.status}`);
      }
      const body: unknown = await res.json();
      const next = parseSessionList(body);
      setSessions(next);
      setError(null);
      setActive((current) => current ?? next[0]?.name ?? null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
      setSessions([]);
    } finally {
      setBusy(false);
    }
  }, [botId]);

  const loadOne = useCallback(async (name: string): Promise<void> => {
    try {
      const res = await fetch(
        `/api/bots/${encodeURIComponent(botId)}/sessions/${encodeURIComponent(name)}`,
      );
      if (!res.ok) {
        throw new Error(`${res.status}`);
      }
      const body: unknown = await res.json();
      setTurns(parseSessionTurns(body));
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
      setTurns([]);
    }
  }, [botId]);

  useEffect(() => {
    setActive(null);
    setTurns([]);
    void loadList();
  }, [botId, loadList]);

  useEffect(() => {
    if (active) {
      void loadOne(active);
    }
  }, [active, loadOne]);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <p className="border-b border-hairline/40 px-4 py-2 text-[12px] leading-relaxed text-ink-secondary">
        {t("inspector.sessions.hint")}
      </p>
      {error ? <div className="px-4 py-2 text-[12px] text-danger">{error}</div> : null}
      <div className="flex min-h-0 flex-1">
        <div className="w-[38%] overflow-y-auto border-r border-hairline/40">
          {busy && sessions.length === 0 ? (
            <div className="px-3 py-6 text-[12px] text-ink-secondary">loading…</div>
          ) : null}
          {!busy && sessions.length === 0 && !error ? (
            <div className="px-3 py-6 text-[12px] text-ink-secondary">{t("inspector.empty.sessions")}</div>
          ) : null}
          {sessions.map((session) => (
            <button
              key={session.name}
              type="button"
              onClick={() => setActive(session.name)}
              className={cn(
                "flex w-full flex-col gap-0.5 px-3 py-2 text-left text-[12px] hover:bg-raised/50",
                active === session.name ? "bg-raised text-ink" : "text-ink",
              )}
            >
              <span className="truncate font-medium">{session.name}</span>
              <span className="text-[11px] text-ink-secondary">
                {session.messageCount} messages · {formatTime(session.startedAt)}
              </span>
            </button>
          ))}
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3 space-y-2">
          {turns.map((turn) => (
            <div
              key={turn.id}
              className={cn(
                "rounded-lg border border-hairline/40 px-3 py-2 text-[12.5px] leading-relaxed",
                turn.role === "user" ? "ml-8 bg-inset" : "mr-8 bg-panel",
              )}
            >
              <div className="mb-1 text-[11px] font-medium uppercase tracking-wide text-ink-secondary">
                {turn.role === "tool" ? turn.toolName ?? "tool" : turn.role}
              </div>
              <pre className="whitespace-pre-wrap break-words font-sans text-ink">{turn.text}</pre>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

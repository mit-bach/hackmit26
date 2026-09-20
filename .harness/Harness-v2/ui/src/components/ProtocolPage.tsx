import { useCallback, useEffect, useState } from "react";
import { ScrollText, Search, X } from "lucide-react";

import { api, useStore } from "@/state/store";
import { cn } from "@/lib/cn";

interface ProtocolEventRow {
  readonly t?: string;
  readonly seq?: number;
  readonly type?: string;
  readonly from?: string;
  readonly to?: string;
  readonly handleId?: string;
  readonly roomId?: string;
  readonly slug?: string;
  readonly text?: string;
  readonly status?: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function parseEvents(body: unknown): ProtocolEventRow[] {
  if (Array.isArray(body)) {
    return body.filter((row): row is ProtocolEventRow => isRecord(row));
  }
  if (isRecord(body) && Array.isArray(body.events)) {
    return body.events.filter((row): row is ProtocolEventRow => isRecord(row));
  }
  return [];
}

function eventLine(row: ProtocolEventRow): string {
  const parts = [
    typeof row.seq === "number" ? `#${row.seq}` : "",
    row.type ?? "",
    row.from ? `${row.from}→${row.to ?? ""}` : "",
    row.handleId ?? "",
    row.status ?? "",
    row.text ?? "",
  ].filter((part) => part.length > 0);
  return parts.join("  ");
}

export function ProtocolPage(): React.ReactElement {
  const { dispatch } = useStore();
  const [query, setQuery] = useState("");
  const [events, setEvents] = useState<ProtocolEventRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async (needle: string): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const path =
        needle.trim().length > 0
          ? `/api/protocol?query=${encodeURIComponent(needle.trim())}`
          : "/api/protocol";
      const body: unknown = await api(path);
      setEvents(parseEvents(body));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
      setEvents([]);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void load("");
  }, [load]);

  const openHit = (row: ProtocolEventRow): void => {
    const owner = asString(row.to) || asString(row.from) || asString(row.slug);
    const roomId = asString(row.roomId);
    if (roomId.length > 0) {
      dispatch({ type: "select", id: roomId });
    } else if (owner.length > 0) {
      dispatch({ type: "select", id: owner.startsWith("bot_") ? owner : owner });
    }
    const messageId = asString(row.handleId) || (typeof row.seq === "number" ? `seq-${row.seq}` : "");
    if (messageId.length > 0) {
      dispatch({
        type: "focusMessage",
        threadId: roomId.length > 0 ? `room-${roomId}` : owner,
        messageId,
      });
    }
  };

  return (
    <main className="flex h-full min-w-0 flex-1 flex-col bg-app">
      <div className="flex items-center justify-between gap-3 border-b border-hairline/40 px-5 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <ScrollText size={16} className="text-ink-secondary" />
          <div>
            <div className="text-[15px] font-semibold text-ink">Protocol</div>
            <div className="text-[12px] text-ink-secondary">
              Office-wide log from harness/protocol.jsonl. Search lands on a Handle or seq.
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={() => dispatch({ type: "showChat" })}
          className="rounded-md p-1.5 text-ink-secondary hover:bg-raised hover:text-ink"
          aria-label="Close Protocol"
        >
          <X size={18} />
        </button>
      </div>
      <form
        className="flex items-center gap-2 border-b border-hairline/40 px-5 py-2"
        onSubmit={(event) => {
          event.preventDefault();
          void load(query);
        }}
      >
        <Search size={14} className="text-ink-secondary" />
        <input
          className="min-w-0 flex-1 bg-transparent text-[13px] text-ink outline-none placeholder:text-ink-secondary"
          placeholder="Search protocol (handle id, slug, text)"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          aria-label="Search protocol"
        />
        <button type="submit" className="rounded-md bg-control px-2.5 py-1 text-[12px] text-ink hover:bg-raised-hover">
          {busy ? "Searching…" : "Search"}
        </button>
      </form>
      <div className="min-h-0 flex-1 overflow-y-auto font-mono text-[12px]">
        {error ? <div className="px-5 py-3 text-danger">{error}</div> : null}
        {!error && busy && events.length === 0 ? (
          <div className="px-5 py-8 text-[13px] text-ink-secondary">Reading harness/protocol.jsonl…</div>
        ) : null}
        {!error && !busy && events.length === 0 ? (
          <div className="px-5 py-8 text-[13px] text-ink-secondary">
            No protocol lines yet. Send a DM or post to a Room — that writes harness/protocol.jsonl.
          </div>
        ) : null}
        {events.map((row) => (
          <button
            key={`${row.seq ?? 0}-${row.handleId ?? ""}-${row.type ?? ""}`}
            type="button"
            onClick={() => openHit(row)}
            className={cn(
              "flex w-full flex-col items-start gap-0.5 border-b border-hairline/20 px-5 py-2 text-left hover:bg-raised/40",
              row.status === "failed" || row.status === "cancelled" ? "bg-danger/10" : "",
            )}
          >
            <span className="text-[11px] text-ink-secondary">
              {row.t ?? ""} {typeof row.seq === "number" ? `seq ${row.seq}` : ""}
            </span>
            <span className="whitespace-pre-wrap text-ink">{eventLine(row)}</span>
          </button>
        ))}
      </div>
    </main>
  );
}

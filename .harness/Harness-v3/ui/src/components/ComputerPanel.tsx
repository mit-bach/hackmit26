import { useCallback, useEffect, useState } from "react";
import { FileText, Folder, Loader2, Monitor, Save, X } from "lucide-react";

import { ComputerTree, buildTree } from "@/components/ComputerTree";
import { api, useStore, type Bot } from "@/state/store";
import { cn } from "@/lib/cn";
import { useCaptionChrome } from "@/components/DesktopCapabilities";

interface TreeEntry {
  readonly path: string;
  readonly type: "file" | "dir";
  readonly size?: number;
}

interface FileBody {
  readonly path: string;
  readonly content: string;
  readonly truncated?: boolean;
}

const PANEL_WIDTH_KEY = "omb-computer-panel-width";
const PANEL_MIN_WIDTH = 360;
const PANEL_MAX_WIDTH = 960;
const PANEL_DEFAULT_WIDTH = 400;

function readPanelWidth(): number {
  try {
    const stored = Number(localStorage.getItem(PANEL_WIDTH_KEY));
    if (Number.isFinite(stored) && stored >= PANEL_MIN_WIDTH && stored <= PANEL_MAX_WIDTH) {
      return stored;
    }
  } catch {
    // private mode
  }
  return PANEL_DEFAULT_WIDTH;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseTree(body: unknown): TreeEntry[] {
  if (Array.isArray(body)) {
    return body.filter((row): row is TreeEntry => isRecord(row) && typeof row.path === "string");
  }
  if (isRecord(body) && Array.isArray(body.entries)) {
    return body.entries.filter((row): row is TreeEntry => isRecord(row) && typeof row.path === "string");
  }
  return [];
}

interface SessionSummary {
  readonly name: string;
  readonly path: string;
  readonly startedAt: string;
  readonly messageCount: number;
}

function parseSessions(body: unknown): SessionSummary[] {
  if (!isRecord(body) || !Array.isArray(body.sessions)) {
    return [];
  }
  return body.sessions.filter((row): row is SessionSummary => {
    return (
      isRecord(row) &&
      typeof row.name === "string" &&
      typeof row.path === "string" &&
      typeof row.startedAt === "string" &&
      typeof row.messageCount === "number"
    );
  });
}

function parseFile(body: unknown): FileBody | null {
  if (!isRecord(body) || typeof body.path !== "string" || typeof body.content !== "string") {
    return null;
  }
  return {
    path: body.path,
    content: body.content,
    truncated: body.truncated === true,
  };
}

export function ComputerPanel({
  bot,
}: {
  readonly bot?: Bot;
}): React.ReactElement {
  const { dispatch, state } = useStore();
  const { padClass } = useCaptionChrome();
  const [width, setWidth] = useState(readPanelWidth);
  const [tree, setTree] = useState<TreeEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [file, setFile] = useState<FileBody | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [treeLoading, setTreeLoading] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [desk, setDesk] = useState<{ instanceId: string; group: string } | null>(null);
  const [openDirs, setOpenDirs] = useState<Set<string>>(() => new Set(["workspace", "runs", "office"]));
  const docked = state.activeView !== "computer";

  const loadTree = useCallback(async (): Promise<void> => {
    setTreeLoading(true);
    try {
      const body: unknown = await api("/api/computer/tree?from=.");
      setTree(parseTree(body));
      if (isRecord(body) && typeof body.instanceId === "string" && typeof body.group === "string") {
        setDesk({ instanceId: body.instanceId, group: body.group });
      }
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
      setTree([]);
    } finally {
      setTreeLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTree();
  }, [loadTree, bot?.id]);

  useEffect(() => {
    if (!bot?.id) {
      setSessions([]);
      return;
    }
    let cancelled = false;
    void api(`/api/bots/${encodeURIComponent(bot.id)}/sessions`)
      .then((body: unknown) => {
        if (!cancelled) {
          setSessions(parseSessions(body));
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSessions([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [bot?.id]);

  const openFile = async (path: string): Promise<void> => {
    setSelected(path);
    setNotice(null);
    try {
      const body: unknown = await api(`/api/computer/file?path=${encodeURIComponent(path)}`);
      const next = parseFile(body);
      if (!next) {
        setError("not a text file");
        setFile(null);
        return;
      }
      setFile(next);
      setDraft(next.content);
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
      setFile(null);
    }
  };

  const save = async (): Promise<void> => {
    if (!file) {
      return;
    }
    setBusy(true);
    setNotice(null);
    try {
      await api("/api/computer/file", {
        method: "PUT",
        body: JSON.stringify({ path: file.path, content: draft }),
      });
      setFile({ ...file, content: draft });
      setNotice("Saved on this Computer.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  const close = (): void => {
    if (state.activeView === "computer") {
      dispatch({ type: "showChat" });
      return;
    }
    dispatch({ type: "toggleComputer", open: false });
  };

  const nodes = buildTree(tree);
  const toggleDir = (path: string): void => {
    setOpenDirs((current) => {
      const next = new Set(current);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  return (
    <aside
      aria-label="Computer"
      className={cn(
        "flex h-full min-w-0 flex-col border-l border-hairline/40 bg-panel",
        docked
          ? "animate-panel-in absolute inset-0 z-40 lg:static lg:z-auto lg:shrink-0"
          : "min-w-0 flex-1",
      )}
      style={docked ? { width: `min(${width}px, 45vw)` } : undefined}
    >
      <div className={cn("flex items-center justify-between px-4 py-3", padClass)}>
        <span className="flex min-w-0 flex-col">
          <span className="flex items-center gap-2 text-[15px] font-semibold text-ink">
            <Monitor size={16} className="text-ink-secondary" /> Computer
          </span>
          <span className="truncate text-[12px] text-ink-secondary">
            {desk ? `${desk.group} / ${desk.instanceId}` : "this instance"}
          </span>
        </span>
        <button
          type="button"
          onClick={close}
          aria-label="Close Computer"
          className="rounded-md p-1 text-ink-secondary hover:bg-raised hover:text-ink"
        >
          <X size={18} />
        </button>
      </div>
      <p className="border-b border-hairline/40 px-4 pb-3 text-[12px] leading-relaxed text-ink-secondary">
        This sandbox is {desk ? `${desk.group} / ${desk.instanceId}` : "the selected instance"}. Folders open in place. data/ stays off this tree.
        {bot
          ? ` Pi sessions live at harness/bots/${bot.id}/pi-session/*.jsonl on this Computer — not the Harness package .pi folder.`
          : ""}
      </p>
      {error ? <div className="px-4 py-2 text-[12px] text-danger">{error}</div> : null}
      {notice ? <div className="px-4 py-2 text-[12px] text-ink-secondary">{notice}</div> : null}
      <div className="flex min-h-0 flex-1">
        <div className="w-[42%] overflow-y-auto border-r border-hairline/40 text-[12px]">
          {treeLoading && tree.length === 0 && !error ? (
            <div className="px-3 py-6 text-ink-secondary">Reading the Computer cwd…</div>
          ) : null}
          {!treeLoading && tree.length === 0 && !error ? (
            <div className="px-3 py-6 text-ink-secondary">
              This Computer has no files yet. They appear under the cwd passed to `harness serve`.
            </div>
          ) : null}
          {sessions.length > 0 ? (
            <div className="border-b border-hairline/40 py-1">
              <div className="px-3 py-1 text-[11px] font-medium uppercase tracking-wide text-ink-secondary">
                Pi sessions
              </div>
              {sessions.map((session) => (
                <button
                  key={session.path}
                  type="button"
                  onClick={() => void openFile(session.path)}
                  className={cn(
                    "flex w-full items-center gap-1.5 px-3 py-1 text-left hover:bg-raised/50",
                    selected === session.path ? "bg-raised text-ink" : "text-ink",
                  )}
                >
                  <FileText size={12} className="shrink-0 text-ink-secondary" />
                  <span className="truncate">{session.name}</span>
                </button>
              ))}
            </div>
          ) : null}
          <ComputerTree
            nodes={nodes}
            depth={0}
            open={openDirs}
            selected={selected}
            onToggle={toggleDir}
            onOpen={(path) => void openFile(path)}
          />
        </div>
        <div className="flex min-w-0 flex-1 flex-col">
          {file ? (
            <>
              <div className="flex items-center justify-between gap-2 border-b border-hairline/40 px-3 py-2 text-[12px]">
                <span className="truncate font-mono text-ink">{file.path}</span>
                <button
                  type="button"
                  disabled={busy || draft === file.content}
                  onClick={() => void save()}
                  className="inline-flex items-center gap-1 rounded-md bg-control px-2 py-1 text-ink hover:bg-raised-hover disabled:opacity-50"
                >
                  {busy ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                  Save
                </button>
              </div>
              {file.truncated ? (
                <div className="px-3 py-1 text-[11px] text-warning">Truncated at 200 KB.</div>
              ) : null}
              <textarea
                className="min-h-0 flex-1 resize-none bg-inset px-3 py-2 font-mono text-[12px] text-ink outline-none"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                spellCheck={false}
              />
            </>
          ) : (
            <div className="px-4 py-8 text-[13px] text-ink-secondary">
              Open a text file on this Computer. Writes go to disk under the shared cwd.
            </div>
          )}
        </div>
      </div>
      {docked ? (
        <div
          role="separator"
          aria-orientation="vertical"
          className="absolute inset-y-0 left-0 w-1 cursor-ew-resize"
          onMouseDown={(event) => {
            event.preventDefault();
            const startX = event.clientX;
            const startW = width;
            const move = (next: MouseEvent): void => {
              const w = Math.min(PANEL_MAX_WIDTH, Math.max(PANEL_MIN_WIDTH, startW - (next.clientX - startX)));
              setWidth(w);
              try {
                localStorage.setItem(PANEL_WIDTH_KEY, String(w));
              } catch {
                // ignore
              }
            };
            const up = (): void => {
              window.removeEventListener("mousemove", move);
              window.removeEventListener("mouseup", up);
            };
            window.addEventListener("mousemove", move);
            window.addEventListener("mouseup", up);
          }}
        />
      ) : null}
    </aside>
  );
}

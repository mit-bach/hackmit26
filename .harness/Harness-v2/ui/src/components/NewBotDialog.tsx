import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";

import { api, useStore } from "@/state/store";
import { cn } from "@/lib/cn";

interface CreatedBot {
  readonly bot?: { readonly id: string };
  readonly id?: string;
}

function createdId(body: unknown): string | undefined {
  if (typeof body !== "object" || body === null) {
    return undefined;
  }
  const record = body as CreatedBot;
  return record.bot?.id ?? record.id;
}

export function NewBotDialog(): React.ReactElement {
  const { dispatch } = useStore();
  const dialogRef = useRef<HTMLDivElement>(null);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [purpose, setPurpose] = useState("");
  const [instructions, setInstructions] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const close = (): void => {
    dispatch({ type: "toggleNewBot", open: false });
  };

  useEffect(() => {
    const returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    dialogRef.current?.querySelector<HTMLElement>("input")?.focus();
    const onKeyDown = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        event.preventDefault();
        close();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      if (returnFocus?.isConnected) {
        returnFocus.focus();
      }
    };
  }, []);

  const submit = async (): Promise<void> => {
    const trimmed = name.trim();
    if (trimmed.length === 0 || busy) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const body: unknown = await api("/api/bots", {
        method: "POST",
        body: JSON.stringify({
          name: trimmed,
          slug: slug.trim(),
          purpose: purpose.trim(),
          instructions: instructions.trim(),
        }),
      });
      const id = createdId(body);
      if (id) {
        dispatch({ type: "select", id });
      }
      close();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  const field = "w-full rounded-lg border border-hairline/40 bg-inset px-3 py-2 text-[14px] text-ink outline-none";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div
        ref={dialogRef}
        role="dialog"
        aria-labelledby="new-bot-title"
        className="w-full max-w-md rounded-2xl border border-hairline/40 bg-panel p-5"
      >
        <div className="flex items-center justify-between">
          <h2 id="new-bot-title" className="text-[16px] font-semibold text-ink">
            Add a Bot
          </h2>
          <button type="button" onClick={close} className="rounded-md p-1 text-ink-secondary hover:bg-raised" aria-label="Close">
            <X size={18} />
          </button>
        </div>
        <p className="mt-1 text-[12px] leading-relaxed text-ink-secondary">
          Writes a BotRecord to harness/roster.json. Slug is the bind key (HARNESS_BOT).
        </p>
        <form
          className="mt-4 flex flex-col gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            void submit();
          }}
        >
          <label className="flex flex-col gap-1 text-[12px] text-ink-secondary">
            Name
            <input className={field} value={name} onChange={(event) => setName(event.target.value)} required />
          </label>
          <label className="flex flex-col gap-1 text-[12px] text-ink-secondary">
            Slug
            <input
              className={cn(field, "font-mono")}
              placeholder="alpha"
              value={slug}
              onChange={(event) => setSlug(event.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-[12px] text-ink-secondary">
            Purpose
            <input
              className={field}
              placeholder="one sentence the others search"
              value={purpose}
              onChange={(event) => setPurpose(event.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-[12px] text-ink-secondary">
            Instructions
            <textarea
              className={cn(field, "min-h-[88px]")}
              placeholder="standing duty, object ownership, done-when"
              value={instructions}
              onChange={(event) => setInstructions(event.target.value)}
            />
          </label>
          {error ? <p className="text-[12px] text-danger">{error}</p> : null}
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={close} className="rounded-lg px-3 py-2 text-[13px] text-ink-secondary hover:bg-raised">
              Cancel
            </button>
            <button
              type="submit"
              disabled={busy || name.trim().length === 0}
              className="rounded-lg bg-control px-3 py-2 text-[13px] text-ink hover:bg-raised-hover disabled:opacity-50"
            >
              {busy ? "Saving…" : "Create Bot"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

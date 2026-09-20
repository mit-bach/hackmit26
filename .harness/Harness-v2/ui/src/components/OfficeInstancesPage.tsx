import { Layers, Loader2, X } from "lucide-react";
import { useState, type FormEvent, type ReactElement } from "react";

import { cn } from "@/lib/cn";
import { t } from "@/lib/i18n";
import { useOfficeInstances } from "@/lib/office-instances";
import { useStore } from "@/state/store";

export function OfficeInstancesPage(): ReactElement {
  const { dispatch } = useStore();
  const { currentId, instances, busy, error, select, create } = useOfficeInstances();
  const [naming, setNaming] = useState(false);
  const [name, setName] = useState("");

  const submitName = (event: FormEvent): void => {
    event.preventDefault();
    void create(name).then((ok): void => {
      if (!ok) {
        return;
      }
      setNaming(false);
      setName("");
    });
  };

  return (
    <main className="flex h-full min-w-0 flex-1 flex-col bg-app">
      <div className="flex items-center justify-between gap-3 border-b border-hairline/40 px-5 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <Layers size={16} className="text-ink-secondary" />
          <div>
            <div className="text-[15px] font-semibold text-ink">{t("sidebar.office.pageTitle")}</div>
            <div className="text-[12px] text-ink-secondary">{t("sidebar.office.pageBlurb")}</div>
          </div>
        </div>
        <button
          type="button"
          onClick={() => dispatch({ type: "showChat" })}
          className="rounded-md p-1.5 text-ink-secondary hover:bg-raised hover:text-ink"
          aria-label={t("sidebar.office.close")}
        >
          <X size={18} />
        </button>
      </div>
      <div className="flex items-center gap-2 border-b border-hairline/40 px-5 py-2">
        {naming ? (
          <form className="flex min-w-0 flex-1 items-center gap-1.5" onSubmit={submitName}>
            <input
              autoFocus
              disabled={busy}
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder={t("sidebar.office.namePlaceholder")}
              aria-label={t("sidebar.office.namePlaceholder")}
              className="min-w-0 flex-1 rounded-md border border-hairline/40 bg-inset/40 px-2 py-1 text-[12px] text-ink placeholder:text-ink-secondary focus:border-accent/50 focus:outline-none"
            />
            <button
              type="submit"
              disabled={busy || name.trim().length === 0}
              className="rounded-md px-2 py-1 text-[12px] text-accent hover:bg-raised disabled:opacity-50"
            >
              {t("sidebar.office.create")}
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                setNaming(false);
                setName("");
              }}
              className="rounded-md px-2 py-1 text-[12px] text-ink-secondary hover:bg-raised"
            >
              {t("sidebar.office.cancel")}
            </button>
          </form>
        ) : (
          <button
            type="button"
            disabled={busy}
            onClick={() => setNaming(true)}
            className="rounded-md px-2 py-1 text-[12px] text-ink-secondary hover:bg-raised hover:text-ink disabled:opacity-50"
          >
            {t("sidebar.office.new")}
          </button>
        )}
        {busy && <Loader2 size={14} className="shrink-0 animate-spin text-ink-secondary" />}
      </div>
      {error && <p className="px-5 py-2 text-[12px] text-rose-400">{error}</p>}
      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-2">
        {instances.length === 0 ? (
          <p className="px-2 py-3 text-[13px] text-ink-secondary">{t("sidebar.office.empty")}</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {instances.map((instance) => {
              const current = instance.id === currentId;
              return (
                <li key={instance.id}>
                  <button
                    type="button"
                    disabled={busy || current}
                    onClick={() => {
                      void select(instance.id);
                    }}
                    aria-current={current ? "page" : undefined}
                    aria-label={
                      current
                        ? `${instance.name}, ${t("sidebar.office.current")}`
                        : t("sidebar.office.switch", { name: instance.name })
                    }
                    className={cn(
                      "flex w-full items-center justify-between gap-3 rounded-xl px-3 py-2.5 text-left text-[14px]",
                      current ? "bg-raised text-ink" : "text-ink hover:bg-raised/50 disabled:opacity-50",
                    )}
                  >
                    <span className="min-w-0 truncate font-medium">{instance.name}</span>
                    {current && (
                      <span className="shrink-0 text-[11px] text-accent">{t("sidebar.office.current")}</span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </main>
  );
}

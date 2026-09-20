import { Loader2 } from "lucide-react";
import { useState, type FormEvent, type ReactElement } from "react";

import { cn } from "@/lib/cn";
import { t } from "@/lib/i18n";
import { useOfficeInstances } from "@/lib/office-instances";

export function OfficeInstanceControl(): ReactElement {
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
    <div className="mt-2 flex flex-col gap-1">
      <span className="px-0.5 text-[11px] text-ink-secondary">{t("sidebar.office.label")}</span>
      {naming ? (
        <form className="flex items-center gap-1.5" onSubmit={submitName}>
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
        <div className="flex items-center gap-1.5">
          <label className="sr-only" htmlFor="office-instance-select">
            {t("sidebar.office.label")}
          </label>
          <select
            id="office-instance-select"
            disabled={busy || instances.length === 0}
            value={currentId}
            aria-label={t("sidebar.office.aria")}
            onChange={(event) => {
              void select(event.target.value);
            }}
            className={cn(
              "min-w-0 flex-1 rounded-md border border-hairline/40 bg-inset/40 px-2 py-1 text-[12px] text-ink",
              "focus:border-accent/50 focus:outline-none disabled:opacity-60",
            )}
          >
            {instances.map((instance) => (
              <option key={instance.id} value={instance.id}>
                {instance.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            disabled={busy}
            onClick={() => setNaming(true)}
            className="shrink-0 rounded-md px-2 py-1 text-[12px] text-ink-secondary hover:bg-raised hover:text-ink disabled:opacity-50"
          >
            {t("sidebar.office.new")}
          </button>
          {busy && <Loader2 size={12} className="shrink-0 animate-spin text-ink-secondary" />}
        </div>
      )}
      {error && <p className="px-0.5 text-[11px] text-rose-400">{error}</p>}
    </div>
  );
}

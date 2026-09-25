import { Layers } from "lucide-react";
import { type ReactElement } from "react";

import { t } from "@/lib/i18n";
import { useStore } from "@/state/store";

export function OfficeInstanceControl(): ReactElement {
  const { state, dispatch } = useStore();
  const current = state.office.instances.find((row) => row.id === state.office.currentId);
  const label = current?.name ?? t("sidebar.office.instances");

  return (
    <button
      type="button"
      onClick={() => dispatch({ type: "showOffice" })}
      aria-label={t("sidebar.office.open")}
      title={t("sidebar.office.open")}
      className="mt-2 flex w-full items-center gap-2 rounded-md border border-hairline/40 bg-inset/40 px-2.5 py-1.5 text-left text-[12px] text-ink hover:border-accent/50 hover:bg-raised/40"
    >
      <Layers size={14} className="shrink-0 text-ink-secondary" />
      <span className="min-w-0 flex-1 truncate">{label}</span>
    </button>
  );
}

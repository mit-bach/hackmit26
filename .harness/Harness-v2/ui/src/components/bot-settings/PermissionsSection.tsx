import { useState } from "react";

import type { Bot } from "@/state/store";
import { cn } from "@/lib/cn";
import type { useBotSettingsDerived } from "./useBotSettingsDerived";

type ApprovalLevel = "ask" | "always" | "never";

const LEVELS: ReadonlyArray<{
  readonly id: ApprovalLevel;
  readonly label: string;
  readonly detail: string;
}> = [
  {
    id: "ask",
    label: "ask",
    detail: "Park consequential tools (side-effect bash, send-as-user) on the Operator.",
  },
  {
    id: "always",
    label: "always",
    detail: "Park bash, write, and edit. Reads still run.",
  },
  {
    id: "never",
    label: "never",
    detail: "Only rm -rf / delete-tree parks. Everything else runs.",
  },
];

function currentLevel(bot: Bot): ApprovalLevel {
  if (bot.approvalLevel === "always" || bot.approvalLevel === "never" || bot.approvalLevel === "ask") {
    return bot.approvalLevel;
  }
  return bot.autoApprove === true ? "never" : "ask";
}

export function PermissionsSection({
  bot,
  derived,
}: {
  bot: Bot;
  derived: ReturnType<typeof useBotSettingsDerived>;
}): React.ReactElement {
  const { patch } = derived;
  const [error, setError] = useState<string | null>(null);
  const selected = currentLevel(bot);

  const setLevel = (level: ApprovalLevel): void => {
    if (bot.busy || level === selected) {
      return;
    }
    setError(null);
    patch({ approvalLevel: level });
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-xl border border-hairline/40 bg-card p-4">
        <div className="text-[15px] font-medium text-ink">Approval level</div>
        <div className="mt-1 text-[12px] leading-relaxed text-ink-secondary">
          Written as approvalLevel on roster.json. Matches Pi’s intercept gate.
        </div>
        <div className="mt-3 flex flex-col gap-2">
          {LEVELS.map((row) => (
            <button
              key={row.id}
              type="button"
              disabled={bot.busy}
              aria-pressed={selected === row.id}
              onClick={() => setLevel(row.id)}
              className={cn(
                "rounded-lg border px-3 py-2.5 text-left",
                selected === row.id
                  ? "border-accent/50 bg-accent/10"
                  : "border-hairline/40 hover:bg-raised",
                bot.busy ? "opacity-50" : "",
              )}
            >
              <div className="font-mono text-[13px] text-ink">{row.label}</div>
              <div className="mt-0.5 text-[12px] text-ink-secondary">{row.detail}</div>
            </button>
          ))}
        </div>
        {error ? <p className="mt-2 text-[12px] text-danger">{error}</p> : null}
      </div>
    </div>
  );
}

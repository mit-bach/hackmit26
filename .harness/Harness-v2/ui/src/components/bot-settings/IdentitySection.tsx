// Identity: name, slug, purpose, standing instructions, avatar color/body.
import { useState } from "react";

import type { Bot } from "@/state/store";
import type { MausMotion, MausState } from "@/lib/mascot";
import { cn } from "@/lib/cn";
import { BOT_PROFILE_LIMITS } from "../../../shared/bot-profile";
import { BotProfileAvatarCard } from "../BotProfileAvatarCard";
import { Field, inputCls } from "./field";
import type { BotPatch } from "./useBotSettingsDerived";

export function IdentitySection({
  bot,
  patch,
  activeState,
  mascotMotion,
}: {
  bot: Bot;
  patch: (patch: BotPatch) => void;
  activeState: MausState;
  mascotMotion: { kind: Exclude<MausMotion, "none">; nonce: number } | null;
}): React.ReactElement {
  const [slug, setSlug] = useState(bot.harnessSlug ?? "");

  return (
    <div className="flex flex-col gap-4">
      <BotProfileAvatarCard bot={bot} activeState={activeState} mascotMotion={mascotMotion} onPatch={patch} />

      <Field label="Name">
        <input
          className={inputCls}
          maxLength={BOT_PROFILE_LIMITS.name}
          value={bot.name}
          onChange={(event) => patch({ name: event.target.value })}
        />
      </Field>
      <Field label="Slug">
        <input
          className={cn(inputCls, "font-mono")}
          value={slug}
          placeholder="alpha"
          onChange={(event) => setSlug(event.target.value)}
          onBlur={() => {
            const next = slug.trim();
            if (next.length > 0 && next !== bot.harnessSlug) {
              patch({ harnessSlug: next });
            }
          }}
        />
        <div className="mt-1 text-[11px] text-ink-secondary">Bind key (HARNESS_BOT). Persists on roster.json.</div>
      </Field>
      <Field label="Purpose">
        <input
          className={inputCls}
          maxLength={BOT_PROFILE_LIMITS.title}
          placeholder="What this Bot is for"
          value={bot.title}
          onChange={(event) => patch({ title: event.target.value })}
        />
      </Field>
      <div className="block">
        <label htmlFor={`bot-instructions-${bot.id}`} className="mb-1.5 block text-[13px] text-ink-secondary">
          Instructions
        </label>
        <textarea
          id={`bot-instructions-${bot.id}`}
          className={cn(inputCls, "min-h-[120px] resize-y leading-relaxed")}
          placeholder="Standing instructions for this Bot. Written to roster.json."
          aria-label="Instructions"
          value={bot.soul ?? ""}
          onChange={(event) => patch({ soul: event.target.value })}
        />
      </div>
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { KeyRound, Palette, Search, User, Workflow, X } from "lucide-react";
import { api, useStore, type AppSettingsSection, type ConfigStatus } from "@/state/store";
import { t } from "@/lib/i18n";
import { ApiKeyRow, OpenAiCompatUrl } from "./ApiKeys";
import { HarnessDeskSettings } from "./HarnessDeskSettings";
import { Card, SettingRow } from "./SettingsPrimitives";
import { shortcutLabel } from "./ShortcutHint";
import { SkinPicker } from "./SkinPicker";
import { cn } from "@/lib/cn";
import { transcriptVerbosity, type TranscriptVerbosity } from "@/lib/feature-flags";

const SECTIONS: Array<{
  id: AppSettingsSection;
  labelKey: "settings.section.general" | "settings.section.harness" | "settings.section.connections" | "settings.section.appearance";
  icon: typeof User;
  keywords: string[];
}> = [
  { id: "general", labelKey: "settings.section.general", icon: User, keywords: ["profile", "name", "email", "operator"] },
  { id: "harness", labelKey: "settings.section.harness", icon: Workflow, keywords: ["harness", "spawn", "extensions", "protocol", "roster", "intercept", "pi"] },
  { id: "connections", labelKey: "settings.section.connections", icon: KeyRound, keywords: ["keys", "api", "anthropic", "openai", "xai", "google"] },
  { id: "appearance", labelKey: "settings.section.appearance", icon: Palette, keywords: ["skin", "theme", "threads", "tool calls", "verbosity", "debug", "pi"] },
];

function sectionMatches(section: (typeof SECTIONS)[number], query: string): boolean {
  if (!query) {
    return true;
  }
  return [t(section.labelKey), ...section.keywords].some((part) => part.toLowerCase().includes(query));
}

function ProfileFields(): React.ReactElement {
  const { state, dispatch } = useStore();
  const [name, setName] = useState(state.config?.profile?.name ?? "");
  const [email, setEmail] = useState(state.config?.profile?.email ?? "");
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    setName(state.config?.profile?.name ?? "");
    setEmail(state.config?.profile?.email ?? "");
  }, [state.config?.profile?.name, state.config?.profile?.email]);

  const save = (): void => {
    setError(null);
    void api("/api/config", {
      method: "PUT",
      body: JSON.stringify({ profile: { name: name.trim(), email: email.trim().toLowerCase() } }),
    })
      .then((config) => dispatch({ type: "configStatus", config: config as ConfigStatus }))
      .catch((cause: unknown) => {
        setError(cause instanceof Error ? cause.message : String(cause));
      });
  };

  const inputClass =
    "w-full rounded-lg border border-hairline/40 bg-inset px-3 py-2 text-[14px] text-ink placeholder:text-ink-secondary focus:border-hairline focus:outline-none";
  return (
    <div className="flex flex-col gap-3">
      <input aria-label="Operator name" value={name} onChange={(event) => setName(event.target.value)} onBlur={save} placeholder="Operator name" className={inputClass} />
      <input
        type="email"
        aria-label="Operator email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        onBlur={save}
        placeholder="you@example.com"
        className={inputClass}
      />
      {error ? <p className="text-[12px] text-danger">{error}</p> : null}
    </div>
  );
}

function VerbosityRow(): React.ReactElement {
  const { state, dispatch } = useStore();
  const value = transcriptVerbosity(state.config);
  const save = (next: TranscriptVerbosity): void => {
    void api("/api/config", {
      method: "PUT",
      body: JSON.stringify({
        features: {
          ...state.config?.features,
          transcriptVerbosity: next,
          showToolCalls: next !== "compact",
        },
      }),
    })
      .then((config) => dispatch({ type: "configStatus", config: config as ConfigStatus }))
      .catch((cause: unknown) => {
        dispatch({ type: "error", message: cause instanceof Error ? cause.message : String(cause) });
      });
  };
  return (
    <SettingRow title={t("settings.verbosity.title")} subtitle={t("settings.verbosity.subtitle")}>
      <select
        aria-label={t("settings.verbosity.aria")}
        className="rounded-lg border border-hairline/40 bg-inset px-3 py-2 text-[13px]"
        value={value}
        onChange={(event) => save(event.target.value as TranscriptVerbosity)}
      >
        <option value="compact">{t("settings.verbosity.compact")}</option>
        <option value="tools">{t("settings.verbosity.tools")}</option>
        <option value="full">{t("settings.verbosity.full")}</option>
      </select>
    </SettingRow>
  );
}

export function SettingsModal(): React.ReactElement {
  const { state, dispatch } = useStore();
  const section: AppSettingsSection = SECTIONS.some((entry) => entry.id === state.appSettingsSection)
    ? state.appSettingsSection
    : "harness";
  const dialogRef = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState("");
  const q = query.trim().toLowerCase();
  const visibleSections = SECTIONS.filter((entry) => sectionMatches(entry, q));
  const sectionLabelKey = SECTIONS.find((entry) => entry.id === section)?.labelKey;

  useEffect(() => {
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const dialog = dialogRef.current;
    const search = dialog?.querySelector<HTMLInputElement>("[data-settings-search]");
    if (search?.checkVisibility()) {
      search.focus();
    } else {
      dialog?.focus();
    }
    const onKey = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        event.preventDefault();
        dispatch({ type: "toggleAppSettings", open: false });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      previousFocus?.focus();
    };
  }, [dispatch]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-3 sm:p-6"
      onMouseDown={(event) => event.target === event.currentTarget && dispatch({ type: "toggleAppSettings", open: false })}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="app-settings-title"
        tabIndex={-1}
        className="flex h-[560px] max-h-[calc(100dvh-24px)] w-full max-w-[860px] overflow-hidden rounded-2xl border border-hairline/50 bg-panel shadow-2xl outline-none"
      >
        <span id="app-settings-title" className="sr-only">
          {t("settings.title")}
        </span>
        <nav className="hidden min-h-0 w-[190px] shrink-0 flex-col gap-1 overflow-y-auto border-r border-hairline/40 bg-app/30 p-3 sm:flex">
          <div className="shrink-0 px-2 py-3 text-[15px] font-semibold text-ink">{t("settings.title")}</div>
          <div className="mb-2 mt-1 flex min-h-8 shrink-0 items-center gap-2 rounded-lg border border-transparent bg-control/70 px-2.5 py-2 focus-within:border-focus">
            <Search size={14} className="shrink-0 text-ink-secondary" />
            <input
              data-settings-search
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={t("settings.search")}
              aria-label={t("settings.searchAria")}
              className="w-full bg-transparent text-[13px] text-ink placeholder:text-ink-secondary focus:outline-none"
            />
          </div>
          {visibleSections.length === 0 && (
            <div className="px-2.5 py-4 text-[12.5px] leading-relaxed text-ink-secondary">
              {t("settings.noMatch", { query: query.trim() })}
            </div>
          )}
          {visibleSections.map(({ id, labelKey, icon: Icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => dispatch({ type: "toggleAppSettings", open: true, section: id })}
              aria-current={section === id ? "page" : undefined}
              className={cn(
                "flex min-h-9 items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-[13px]",
                section === id ? "bg-control text-ink" : "text-ink-secondary hover:bg-control/50 hover:text-ink",
              )}
            >
              <Icon size={15} className="shrink-0" />
              {t(labelKey)}
            </button>
          ))}
        </nav>

        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          <div className="flex shrink-0 items-center justify-between gap-3 border-b border-hairline/30 px-3 py-3 sm:px-5">
            <div className="text-[15px] font-semibold text-ink">{sectionLabelKey ? t(sectionLabelKey) : t("settings.title")}</div>
            <button
              type="button"
              onClick={() => dispatch({ type: "toggleAppSettings", open: false })}
              aria-label={t("settings.close")}
              title={`${t("settings.close")} (${shortcutLabel("close-panel")})`}
              className="ui-icon-button shrink-0"
            >
              <X size={18} />
            </button>
          </div>
          <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-3 py-4 sm:px-5 sm:pb-5">
            {section === "general" && (
              <Card title="Operator" subtitle="Who you are on this Computer. Saved to ~/.harness/config.json.">
                <ProfileFields />
              </Card>
            )}
            {section === "harness" && <HarnessDeskSettings />}
            {section === "connections" && (
              <Card title="Keys" subtitle="Write-only. GET never echoes the secret. Nested { anthropic: { key } } persists.">
                <div className="flex flex-col gap-4">
                  <ApiKeyRow section="anthropic" testProvider="anthropic" />
                  <ApiKeyRow section="openaiCompat" testProvider="openaiCompat" />
                  <OpenAiCompatUrl />
                  <ApiKeyRow section="xai" testProvider="xai" />
                  <ApiKeyRow section="google" testProvider="google" />
                </div>
              </Card>
            )}
            {section === "appearance" && (
              <>
                <Card title={t("settings.skin.title")} subtitle={t("settings.skin.subtitle")}>
                  <SkinPicker />
                </Card>
                <VerbosityRow />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

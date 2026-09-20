// Paste-a-key rows. Packaged Electron saves secrets in the OS-backed store;
// browser development falls back to PUT /api/config. Secrets are write-only
// either way — GET /api/config returns configured flags, never values.
import { useEffect, useId, useRef, useState } from "react";
import { Check, CircleHelp, ExternalLink, Loader2 } from "lucide-react";
import { api, useStore, type ConfigStatus } from "@/state/store";
import { cn } from "@/lib/cn";
import { t } from "@/lib/i18n";
import type { LocaleKey } from "@/locales";

export type ConfigSection = "anthropic" | "openaiCompat" | "xai" | "google";
/** Presence check only — Test does not call the provider and does not persist. */
export type TestableProvider = ConfigSection;

interface KeyTestResult {
  readonly ok: boolean;
  readonly message?: string;
}

const SECTIONS: Record<
  ConfigSection,
  { body: (value: string) => unknown; flag: (config: ConfigStatus) => boolean }
> = {
  anthropic: { body: (v) => ({ anthropic: { key: v } }), flag: (c) => c.anthropic?.configured ?? false },
  openaiCompat: { body: (v) => ({ openaiCompat: { key: v } }), flag: (c) => c.openaiCompat?.configured ?? false },
  xai: { body: (v) => ({ xai: { key: v } }), flag: (c) => c.xai?.configured ?? false },
  google: { body: (v) => ({ google: { key: v } }), flag: (c) => c.google?.configured ?? false },
};

const CREDENTIALS: Record<
  ConfigSection,
  {
    labelKey: LocaleKey;
    placeholder?: string;
    descriptionKey: LocaleKey;
    href: string;
    linkLabelKey: LocaleKey;
    optional: boolean;
  }
> = {
  anthropic: {
    labelKey: "keys.anthropic.label",
    placeholder: "sk-ant-…",
    descriptionKey: "keys.anthropic.desc",
    href: "https://console.anthropic.com/settings/keys",
    linkLabelKey: "keys.anthropic.link",
    optional: true,
  },
  openaiCompat: {
    labelKey: "keys.openaiCompat.label",
    placeholder: "sk-or-v1-…",
    descriptionKey: "keys.openaiCompat.desc",
    href: "https://openrouter.ai/keys",
    linkLabelKey: "keys.openaiCompat.link",
    optional: true,
  },
  xai: {
    labelKey: "keys.xai.label",
    placeholder: "xai-…",
    descriptionKey: "keys.xai.desc",
    href: "https://console.x.ai",
    linkLabelKey: "keys.xai.link",
    optional: true,
  },
  google: {
    labelKey: "keys.google.label",
    placeholder: "AIza…",
    descriptionKey: "keys.google.desc",
    href: "https://aistudio.google.com/apikey",
    linkLabelKey: "keys.google.link",
    optional: true,
  },
};

/** The catalog is read when a row renders, not when this module loads. */
function credentialCopy(section: ConfigSection): {
  label: string;
  placeholder: string;
  description: string;
  linkLabel: string;
  href: string;
  optional: boolean;
} {
  const entry = CREDENTIALS[section];
  return {
    label: t(entry.labelKey),
    placeholder: entry.placeholder ?? "",
    description: t(entry.descriptionKey),
    linkLabel: t(entry.linkLabelKey),
    href: entry.href,
    optional: entry.optional,
  };
}

function CredentialHelp({ section }: { section: ConfigSection }) {
  const credential = credentialCopy(section);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const popoverId = useId();

  useEffect(() => {
    if (!open) return;

    const closeOnOutsideClick = (event: PointerEvent) => {
      if (event.target instanceof Node && !rootRef.current?.contains(event.target)) setOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setOpen(false);
      buttonRef.current?.focus();
    };

    document.addEventListener("pointerdown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="relative ml-auto">
      <button
        ref={buttonRef}
        type="button"
        aria-label={t("keys.aboutAria", { label: credential.label })}
        aria-expanded={open}
        aria-controls={popoverId}
        onClick={() => setOpen((current) => !current)}
        className="flex size-6 items-center justify-center rounded-md text-ink-secondary outline-none transition-colors hover:bg-control hover:text-ink focus-visible:ring-2 focus-visible:ring-accent/70"
      >
        <CircleHelp size={14} aria-hidden="true" />
      </button>
      {open && (
        <div
          id={popoverId}
          role="group"
          aria-label={t("keys.helpAria", { label: credential.label })}
          className="animate-pop-in absolute right-0 z-30 mt-1.5 w-[270px] rounded-xl border border-hairline bg-panel p-3 text-left shadow-2xl"
        >
          <div className="text-[12px] leading-[1.45] text-ink-secondary">{credential.description}</div>
          <a
            href={credential.href}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => setOpen(false)}
            className="mt-2.5 flex items-center gap-1.5 text-[12px] font-medium text-accent hover:underline focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/70"
          >
            {credential.linkLabel}
            <ExternalLink size={12} aria-hidden="true" />
          </a>
        </div>
      )}
    </div>
  );
}

export function ApiKeyRow({
  section,
  onSaved,
  testProvider,
}: {
  section: ConfigSection;
  /** Called after a successful save with the section's new configured flag. */
  onSaved?: (configured: boolean) => void;
  /** Offer a Test button for the saved key or a nonempty draft. */
  testProvider?: TestableProvider;
}) {
  const { state, dispatch } = useStore();
  const [value, setValue] = useState("");
  const [edited, setEdited] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);
  const [verdict, setVerdict] = useState<string | null>(null);
  const testGeneration = useRef(0);

  useEffect(() => {
    testGeneration.current++;
    setVerdict(null);
  }, [state.config]);

  const configured = state.config ? SECTIONS[section].flag(state.config) : false;
  const clearing = !value.trim() && configured;
  const emptyDraft = edited && !value.trim();
  const credential = credentialCopy(section);

  const save = (): void => {
    if (saving || (!value.trim() && !configured)) {
      return;
    }
    setSaving(true);
    setError(null);
    testGeneration.current++;
    setVerdict(null);
    void api<ConfigStatus>("/api/config", {
      method: "PUT",
      body: JSON.stringify(SECTIONS[section].body(value.trim())),
    })
      .then((status) => {
        dispatch({ type: "configStatus", config: status });
        setValue("");
        setEdited(false);
        onSaved?.(SECTIONS[section].flag(status));
      })
      .catch((cause: unknown) => {
        setError(cause instanceof Error ? cause.message : String(cause));
      })
      .finally(() => {
        setSaving(false);
      });
  };

  const test = async (): Promise<void> => {
    if (!testProvider || testing || saving || emptyDraft) {
      return;
    }
    setTesting(true);
    setVerdict(null);
    const generation = ++testGeneration.current;
    try {
      const result = await api<KeyTestResult>("/api/keys/test", {
        method: "POST",
        body: JSON.stringify({
          provider: testProvider,
          ...(value.trim() ? { key: value.trim() } : {}),
        }),
      });
      if (generation !== testGeneration.current) {
        return;
      }
      setVerdict(result.message ?? (result.ok ? "a key is stored (not a live API call)" : "no key stored"));
    } catch (cause: unknown) {
      if (generation === testGeneration.current) {
        setVerdict(cause instanceof Error ? cause.message : String(cause));
      }
    } finally {
      setTesting(false);
    }
  };

  return (
    <div>
      <div className="mb-1.5 flex items-center gap-2 text-[13px] text-ink-secondary">
        <span className={cn("size-1.5 rounded-full", configured ? "bg-success" : "bg-raised-hover")} />
        <span>{credential.label}</span>
        {credential.optional && (
          <span className="rounded bg-control px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-ink-secondary">
            {t("keys.optional")}
          </span>
        )}
        {configured && <span className="text-[11px] text-ink-secondary">{t("keys.configured")}</span>}
        <CredentialHelp section={section} />
      </div>
      <div className="flex gap-2">
        <input
          type="password"
          value={value}
          onChange={(e) => { testGeneration.current++; setVerdict(null); setEdited(true); setValue(e.target.value); }}
          disabled={saving}
          onKeyDown={(e) => e.key === "Enter" && save()}
          placeholder={configured ? t("keys.replace") : credential.placeholder}
          aria-label={credential.label}
          autoComplete="off"
          className="w-full rounded-lg border border-hairline/40 bg-inset px-3 py-2 text-[13px] text-ink placeholder:text-ink-secondary focus:border-hairline focus:outline-none"
        />
        <button
          onClick={save}
          disabled={saving || (!value.trim() && !configured)}
          className={cn(
            "flex w-[72px] shrink-0 items-center justify-center gap-1.5 rounded-lg py-2 text-[13px]",
            clearing
              ? "bg-control text-danger hover:bg-raised-hover"
              : "bg-control text-ink hover:bg-raised-hover",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
          title={clearing ? t("keys.removeKey") : t("common.save")}
        >
          {saving ? <Loader2 size={13} className="animate-spin" /> : clearing ? t("keys.clear") : <><Check size={13} />{t("common.save")}</>}
        </button>
        {testProvider && (configured || value.trim()) && (
          <button
            type="button"
            onClick={() => void test()}
            disabled={testing || saving || emptyDraft}
            className="flex shrink-0 items-center justify-center rounded-lg border border-hairline/40 px-3 py-2 text-[13px] text-ink-secondary hover:bg-raised/50 hover:text-ink disabled:cursor-not-allowed disabled:opacity-50"
          >
            {testing ? t("keys.testing") : t("keys.test")}
          </button>
        )}
      </div>
      {error && <div className="mt-1 text-[12px] text-danger">{error}</div>}
      {verdict && <div role="status" className="mt-1 text-[12px] text-ink-secondary">{verdict}</div>}
    </div>
  );
}

/** The OpenAI-compatible engine's base URL: a setting next to its key. */
export function OpenAiCompatUrl(): React.ReactElement {
  const { state, dispatch } = useStore();
  const saved = state.config?.openaiCompat?.url ?? "";
  const [value, setValue] = useState(saved);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { setValue(saved); }, [saved]);
  const dirty = value.trim() !== saved;

  const save = () => {
    if (saving || !dirty) return;
    setSaving(true);
    setError(null);
    api<ConfigStatus>("/api/config", { method: "PUT", body: JSON.stringify({ openaiCompat: { url: value.trim() } }) })
      .then((status) => dispatch({ type: "configStatus", config: status }))
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : String(cause)))
      .finally(() => setSaving(false));
  };

  return (
    <div>
      <div className="mb-1.5 text-[13px] text-ink-secondary">{t("keys.openaiCompat.url")}</div>
      <div className="flex gap-2">
        <input
          type="url"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && save()}
          placeholder="https://openrouter.ai/api/v1"
          aria-label={t("keys.openaiCompat.url")}
          spellCheck={false}
          className="w-full rounded-lg border border-hairline/40 bg-inset px-3 py-2 font-mono text-[12px] text-ink placeholder:text-ink-secondary focus:border-hairline focus:outline-none"
        />
        <button
          onClick={save}
          disabled={saving || !dirty}
          className="flex w-[72px] shrink-0 items-center justify-center gap-1.5 rounded-lg bg-control py-2 text-[13px] text-ink hover:bg-raised-hover disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? <Loader2 size={13} className="animate-spin" /> : <><Check size={13} />{t("common.save")}</>}
        </button>
      </div>
      <p className="mt-1 text-[11.5px] leading-relaxed text-ink-secondary">{t("keys.openaiCompat.urlHint")}</p>
      {error && <div className="mt-1 text-[12px] text-danger">{error}</div>}
    </div>
  );
}

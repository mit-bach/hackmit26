import { useEffect, useState } from "react";
import { api, useStore, type ConfigStatus } from "@/state/store";
import { Card, Switch } from "./SettingsPrimitives";

interface CommsInfo {
  computerRoot?: string;
  roster?: string;
  protocol?: string;
  bots?: string;
  rooms?: string;
  intercept?: string;
  extensions?: string;
  operatorConfig?: string;
  extraExtensions?: string[];
}

interface InterceptBody {
  default?: { kind: string; bot?: string } | string;
  bots?: Record<string, { kind: string; bot?: string }>;
}

export function HarnessDeskSettings(): React.ReactElement {
  const { state, dispatch } = useStore();
  const harness = state.config?.harness;
  const [spawnPolicy, setSpawnPolicy] = useState(harness?.spawnPolicy ?? state.config?.spawnPolicy ?? "eager");
  const [provider, setProvider] = useState(harness?.provider ?? state.config?.provider ?? "");
  const [model, setModel] = useState(harness?.model ?? state.config?.model ?? "");
  const [thinkingLevel, setThinkingLevel] = useState(harness?.thinkingLevel ?? state.config?.thinkingLevel ?? "low");
  const [extra, setExtra] = useState((harness?.extraExtensions ?? state.config?.extraExtensions ?? []).join("\n"));
  const [clientSkills, setClientSkills] = useState(Boolean(harness?.clientSkills ?? state.config?.clientSkills));
  const [comms, setComms] = useState<CommsInfo | null>(null);
  const [intercept, setIntercept] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void api<CommsInfo>("/api/comms")
      .then((body) => setComms(body))
      .catch((cause: unknown) => {
        setComms(null);
        setMessage(cause instanceof Error ? cause.message : String(cause));
      });
    void api<InterceptBody>("/api/intercept")
      .then((body) => setIntercept(JSON.stringify(body, null, 2)))
      .catch((cause: unknown) => {
        setIntercept("");
        setMessage(cause instanceof Error ? cause.message : String(cause));
      });
  }, []);

  const save = async (): Promise<void> => {
    setBusy(true);
    setMessage("");
    try {
      const extraExtensions = extra
        .split("\n")
        .map((row) => row.trim())
        .filter((row) => row.length > 0);
      const config = await api<ConfigStatus>("/api/config", {
        method: "PUT",
        body: JSON.stringify({
          spawnPolicy,
          provider: provider.trim() || undefined,
          model: model.trim() || undefined,
          thinkingLevel: thinkingLevel.trim() || undefined,
          extraExtensions,
          clientSkills,
        }),
      });
      dispatch({ type: "configStatus", config });
      if (intercept.trim().length > 0) {
        let parsed: unknown;
        try {
          parsed = JSON.parse(intercept) as unknown;
        } catch {
          throw new Error("Intercept map must be valid JSON.");
        }
        await api("/api/intercept", { method: "PUT", body: JSON.stringify(parsed) });
      }
      setMessage("Saved. Restart live Pi workers to pick up extra extensions.");
    } catch (cause) {
      setMessage(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card
      title="Harness desk"
      subtitle="Named Bots, Handles, and the protocol log on this Computer."
    >
      <div className="flex flex-col gap-3 text-[13px]">
        <label className="flex flex-col gap-1">
          <span className="text-[11.5px] font-medium uppercase tracking-wide text-ink-secondary">Spawn policy</span>
          <select
            className="rounded-lg border border-hairline/40 bg-inset px-3 py-2"
            value={spawnPolicy}
            onChange={(event) => setSpawnPolicy(event.target.value)}
          >
            <option value="eager">eager — spawn a Pi process per Bot</option>
            <option value="lazy">lazy — spawn when inbox has work</option>
            <option value="fake">fake — complete Handles without a model</option>
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[11.5px] font-medium uppercase tracking-wide text-ink-secondary">Provider</span>
          <input
            className="rounded-lg border border-hairline/40 bg-inset px-3 py-2"
            placeholder="anthropic | openai | xai | google"
            value={provider}
            onChange={(event) => setProvider(event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[11.5px] font-medium uppercase tracking-wide text-ink-secondary">Model</span>
          <input
            className="rounded-lg border border-hairline/40 bg-inset px-3 py-2"
            placeholder="claude-sonnet-4-5"
            value={model}
            onChange={(event) => setModel(event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[11.5px] font-medium uppercase tracking-wide text-ink-secondary">Pi thinking level</span>
          <select
            className="rounded-lg border border-hairline/40 bg-inset px-3 py-2"
            value={thinkingLevel}
            onChange={(event) => setThinkingLevel(event.target.value)}
            aria-label="Pi thinking level"
          >
            <option value="off">off</option>
            <option value="minimal">minimal</option>
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
          </select>
          <span className="text-[12px] text-ink-secondary">
            Restart live Pi workers after changing this. Low keeps a visible reply; medium/high can think without text.
          </span>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[11.5px] font-medium uppercase tracking-wide text-ink-secondary">Extra Pi extensions</span>
          <textarea
            className="min-h-[72px] rounded-lg border border-hairline/40 bg-inset px-3 py-2 font-mono text-[12px]"
            placeholder={"./cfo/extensions/index.ts"}
            value={extra}
            onChange={(event) => setExtra(event.target.value)}
          />
          <span className="text-[12px] text-ink-secondary">
            One path per line. Same as HARNESS_EXTRA_EXTENSIONS and harness/extensions.json. Client systems (CFO V2) attach here.
          </span>
        </label>
        <label className="flex items-center justify-between gap-3">
          <span>Client skill filter — each Bot only loads roster.skills that exist as Computer/skills/&lt;name&gt;/SKILL.md</span>
          <Switch checked={clientSkills} onClick={() => setClientSkills((prev) => !prev)} aria-label="Client skill filter" />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[11.5px] font-medium uppercase tracking-wide text-ink-secondary">Intercept map</span>
          <textarea
            className="min-h-[88px] rounded-lg border border-hairline/40 bg-inset px-3 py-2 font-mono text-[12px]"
            value={intercept}
            onChange={(event) => setIntercept(event.target.value)}
          />
          <span className="text-[12px] text-ink-secondary">
            Route parked approvals to Operator or a Verifier Bot. File: harness/intercept.json
          </span>
        </label>
        <button
          type="button"
          disabled={busy}
          onClick={() => void save()}
          className="self-start rounded-lg bg-control px-3 py-2 text-[13px] text-ink hover:bg-raised-hover disabled:opacity-50"
        >
          Save Harness settings
        </button>
        {message ? <p className="text-[12px] text-ink-secondary">{message}</p> : null}
        <div className="rounded-lg border border-hairline/40 bg-inset px-3 py-2 font-mono text-[11px] leading-relaxed text-ink-secondary">
          <div>computer: {comms?.computerRoot ?? "—"}</div>
          <div>roster: {comms?.roster ?? harness?.roster ?? "harness/roster.json"}</div>
          <div>protocol: {comms?.protocol ?? harness?.protocol ?? "harness/protocol.jsonl"}</div>
          <div>bots: {comms?.bots ?? "harness/bots/&lt;botId&gt;/"}</div>
          <div>rooms: {comms?.rooms ?? "harness/rooms/&lt;id&gt;/log.jsonl"}</div>
          <div>config: {comms?.operatorConfig ?? harness?.configPath ?? "~/.harness/config.json"}</div>
        </div>
      </div>
    </Card>
  );
}

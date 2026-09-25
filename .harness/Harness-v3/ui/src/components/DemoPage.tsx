import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import {
  ChevronLeft,
  Circle,
  Clapperboard,
  Clock,
  Disc3,
  Pause,
  Play,
  Radio,
  RotateCcw,
  Settings2,
} from "lucide-react";

import { ChatMarkdown } from "@/components/ChatMarkdown";
import { MausAvatar } from "@/components/Avatar";
import { WorkingDots } from "@/components/WorkingIndicator";
import { cn } from "@/lib/cn";
import {
  clampPlaybackSettings,
  collectBeats,
  DEFAULT_DEMO_PLAYBACK,
  formatShowClock,
  loadPlaybackSettings,
  projectPlayhead,
  revealKey,
  revealText,
  savePlaybackSettings,
  showMsForBeat,
  showMsForSeq,
  stepBeat,
  timelineTotalMs,
  type DemoMessageReveal,
  type DemoPlaybackSettings,
} from "@/lib/demo-playback";
import {
  parseDemoBundle,
  parseDemoScenes,
  CAMERA_DEMO_DIRECTOR,
  PANE_CAPS,
  clampDirector,
  loadDirectorSettings,
  saveDirectorSettings,
  type DemoAwakeBot,
  type DemoBundle,
  type DemoColor,
  type DemoDirector,
  type DemoScene,
  type MosaicCell,
  type TranscriptEntry,
} from "@/lib/demo-replay";
import { t } from "@/lib/i18n";
import { MAUS_COLOR_NAMES, type MausColor } from "@/lib/mascot";
import { api, useStore } from "@/state/store";

const SPEED_CHIPS = [0.5, 1, 2, 4] as const;

function asMausColor(value: DemoColor): MausColor {
  return (MAUS_COLOR_NAMES as readonly string[]).includes(value) ? (value as MausColor) : "teal";
}

function caption(frame: { type: string; from?: string; to?: string; slug?: string; text: string; seq: number }): string {
  const who = frame.slug ?? frame.to ?? frame.from ?? "";
  const text = frame.text.trim().replace(/\s+/g, " ").slice(0, 140);
  const parts = [`#${frame.seq}`, frame.type, who, text].filter((part) => part.length > 0);
  return parts.join("  ");
}

function isUserLine(row: TranscriptEntry): boolean {
  return row.kind === "turn.start" || row.kind === "user_dm";
}

function isResultLine(row: TranscriptEntry): boolean {
  return row.kind === "handoff.done" || row.kind === "result" || row.kind === "tool.result" || row.kind.endsWith(".done");
}

function isToolCall(row: TranscriptEntry): boolean {
  return row.kind === "tool.call";
}

function parseDemoQuery(): {
  source: "auto" | "live" | "recording";
  cinema: boolean;
  scene: string;
  play: boolean;
} {
  if (typeof window === "undefined") {
    return { source: "auto", cinema: false, scene: "", play: false };
  }
  const params = new URLSearchParams(window.location.search);
  const raw = params.get("source");
  const source = raw === "live" || raw === "recording" || raw === "auto" ? raw : "auto";
  return {
    source,
    cinema: params.get("cinema") === "1" || params.get("cinema") === "true",
    scene: params.get("scene") ?? "",
    play: params.get("play") === "1" || params.get("play") === "true",
  };
}

function displayText(row: TranscriptEntry): string {
  const done = /^(?:\S+ finished handle \S+: )([\s\S]*)$/.exec(row.text);
  if (done?.[1]) {
    return done[1];
  }
  const wake = /^wake from [^:]+: ([\s\S]*)$/.exec(row.text);
  if (wake?.[1]) {
    return wake[1];
  }
  return row.text;
}

function formatStamp(iso: string, originMs: number): string {
  const ms = Date.parse(iso);
  if (!Number.isFinite(ms)) {
    return "";
  }
  const clock = new Date(ms);
  const hh = String(clock.getHours()).padStart(2, "0");
  const mm = String(clock.getMinutes()).padStart(2, "0");
  const ss = String(clock.getSeconds()).padStart(2, "0");
  if (originMs <= 0) {
    return `${hh}:${mm}:${ss}`;
  }
  const rel = Math.max(0, Math.round((ms - originMs) / 1000));
  return `${hh}:${mm}:${ss}  +${rel}s`;
}

function streamedCopy(row: TranscriptEntry, reveal: DemoMessageReveal | undefined): { text: string; streaming: boolean } {
  const full = displayText(row);
  if (!reveal || reveal.complete) {
    return { text: full, streaming: false };
  }
  const sourceLen = Math.max(1, [...row.text].length);
  const fraction = [...reveal.revealed].length / sourceLen;
  return { text: revealText(full, fraction), streaming: reveal.streaming };
}

function nearestChip(speed: number): number {
  return SPEED_CHIPS.reduce((best, item) => (Math.abs(item - speed) < Math.abs(best - speed) ? item : best), SPEED_CHIPS[0]);
}

function isTextEntryTarget(target: EventTarget | null): boolean {
  if (target instanceof HTMLTextAreaElement) {
    return true;
  }
  if (target instanceof HTMLInputElement) {
    return target.type !== "range" && target.type !== "button" && target.type !== "checkbox" && target.type !== "radio";
  }
  return target instanceof HTMLElement && target.isContentEditable;
}

export function DemoPage(): React.ReactElement {
  const { dispatch } = useStore();
  const boot = useMemo(() => parseDemoQuery(), []);
  const [bundle, setBundle] = useState<DemoBundle | null>(null);
  const [source, setSource] = useState<"auto" | "live" | "recording">(boot.source);
  const [showMs, setShowMs] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [cinema, setCinema] = useState(boot.cinema);
  const [settings, setSettings] = useState<DemoPlaybackSettings>(() => loadPlaybackSettings());
  const [director, setDirectorState] = useState<DemoDirector>(() => loadDirectorSettings());
  const [sceneId, setSceneId] = useState(boot.scene || "full");
  const [sceneTitle, setSceneTitle] = useState("");
  const [sceneBusy, setSceneBusy] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [recordBusy, setRecordBusy] = useState(false);
  const [seqDraft, setSeqDraft] = useState("");
  const playingRef = useRef(false);
  const totalRef = useRef(0);
  const bootedRef = useRef(false);

  const load = useCallback(async (nextSource: "auto" | "live" | "recording"): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const path = nextSource === "auto" ? "/api/demo" : `/api/demo?source=${nextSource}`;
      const body: unknown = await api(path, { timeoutMs: 20_000 });
      const parsed = parseDemoBundle(body);
      if (!parsed) {
        setError(t("demo.err.parse"));
        setBundle(null);
        return;
      }
      setBundle(parsed);
      setShowMs(0);
      setPlaying(false);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
      setBundle(null);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void load(source);
  }, [load, source]);

  const beats = useMemo(() => (bundle ? collectBeats(bundle, director) : []), [bundle, director]);
  const playhead = useMemo(
    () => (bundle ? projectPlayhead(bundle, showMs, settings, director) : null),
    [bundle, director, showMs, settings],
  );
  const frame = playhead?.frame;
  const totalMs = playhead?.totalMs ?? 0;
  const progress = playhead?.progress ?? 0;
  const lastSeq = bundle?.lastSeq ?? 0;
  playingRef.current = playing;
  totalRef.current = totalMs;

  const patchDirector = useCallback((partial: Partial<DemoDirector>): void => {
    const next = clampDirector({ ...director, ...partial });
    saveDirectorSettings(next);
    setDirectorState(next);
    if (partial.seqFrom !== undefined || partial.seqTo !== undefined) {
      setShowMs(0);
      setPlaying(false);
    }
  }, [director]);

  const applyScene = useCallback((scene: DemoScene | "full"): void => {
    if (scene === "full") {
      const next = clampDirector({ ...director, seqFrom: 0, seqTo: 0 });
      saveDirectorSettings(next);
      setDirectorState(next);
      setSceneId("full");
      setShowMs(0);
      setPlaying(false);
      return;
    }
    const next = clampDirector({
      maxPanes: scene.maxPanes,
      featured: scene.featured,
      seqFrom: scene.seqFrom,
      seqTo: scene.seqTo,
    });
    saveDirectorSettings(next);
    setDirectorState(next);
    setSceneId(scene.id);
    setShowMs(0);
    setPlaying(false);
  }, [director]);

  useEffect(() => {
    if (!bundle || bootedRef.current) {
      return;
    }
    bootedRef.current = true;
    if (boot.scene && boot.scene !== "full") {
      const scene = (bundle.scenes ?? []).find((item) => item.id === boot.scene);
      if (scene) {
        applyScene(scene);
      }
    }
    if (boot.play) {
      setPlaying(true);
    }
  }, [applyScene, boot.play, boot.scene, bundle]);

  useEffect(() => {
    if (!cinema) {
      return;
    }
    const onKey = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        setCinema(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [cinema]);

  const patchSettings = useCallback((partial: Partial<DemoPlaybackSettings>): void => {
    const next = clampPlaybackSettings({ ...settings, ...partial });
    if (bundle) {
      const oldTotal = timelineTotalMs(beats, settings);
      const nextTotal = timelineTotalMs(beats, next);
      const kept = oldTotal > 0 ? showMs / oldTotal : 0;
      setShowMs(kept * nextTotal);
    }
    savePlaybackSettings(next);
    setSettings(next);
  }, [beats, bundle, settings, showMs]);

  useEffect(() => {
    if (!playing) {
      return;
    }
    let raf = 0;
    let last = performance.now();
    let acc = 0;
    const tick = (now: number): void => {
      const dt = Math.min(48, now - last);
      last = now;
      acc += dt;
      if (acc >= 32) {
        const step = acc;
        acc = 0;
        setShowMs((prev) => {
          const total = totalRef.current;
          if (total <= 0) {
            setPlaying(false);
            return 0;
          }
          const next = prev + step;
          if (next >= total) {
            setPlaying(false);
            return total;
          }
          return next;
        });
      }
      if (playingRef.current) {
        raf = window.requestAnimationFrame(tick);
      }
    };
    raf = window.requestAnimationFrame(tick);
    const interval = window.setInterval(() => {
      if (playingRef.current) {
        tick(performance.now());
      }
    }, 50);
    return () => {
      window.cancelAnimationFrame(raf);
      window.clearInterval(interval);
    };
  }, [playing]);

  const togglePlay = useCallback((): void => {
    if (playing) {
      setPlaying(false);
      return;
    }
    if (totalMs <= 0) {
      return;
    }
    if (showMs >= totalMs - 24) {
      setShowMs(0);
    }
    setPlaying(true);
  }, [playing, showMs, totalMs]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent): void => {
      if (event.defaultPrevented || event.isComposing) {
        return;
      }
      const target = event.target;
      const typing = isTextEntryTarget(target);
      if (event.key === "Escape") {
        event.preventDefault();
        if (settingsOpen) {
          setSettingsOpen(false);
          return;
        }
        dispatch({ type: "showChat" });
        return;
      }
      if (event.key === " " && !typing) {
        event.preventDefault();
        togglePlay();
        return;
      }
      if (typing) {
        return;
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        setPlaying(false);
        const next = stepBeat(beats, playhead?.beatIndex ?? -1, 1);
        setShowMs(showMsForBeat(beats, next, settings));
        return;
      }
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        setPlaying(false);
        const previous = stepBeat(beats, playhead?.beatIndex ?? -1, -1);
        setShowMs(showMsForBeat(beats, previous, settings));
        return;
      }
      if (event.key === "Home") {
        event.preventDefault();
        setPlaying(false);
        setShowMs(0);
        return;
      }
      if (event.key === "End") {
        event.preventDefault();
        setPlaying(false);
        setShowMs(totalRef.current);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [beats, dispatch, playhead?.beatIndex, settings, settingsOpen, togglePlay]);

  const recordNow = async (): Promise<void> => {
    setRecordBusy(true);
    setError(null);
    try {
      await api("/api/demo/record", { method: "POST" });
      setSource("recording");
      await load("recording");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setRecordBusy(false);
    }
  };

  const saveScene = async (): Promise<void> => {
    if (!bundle) {
      return;
    }
    const title = sceneTitle.trim() || `Cut ${director.seqFrom || 0}–${director.seqTo || bundle.lastSeq}`;
    const nextScene: DemoScene = {
      id: `cut-${Date.now()}`,
      title,
      seqFrom: director.seqFrom,
      seqTo: director.seqTo,
      featured: director.featured,
      maxPanes: director.maxPanes,
    };
    setSceneBusy(true);
    setError(null);
    try {
      const body: unknown = await api("/api/demo/scenes", {
        method: "PUT",
        body: JSON.stringify({ scenes: [...(bundle.scenes ?? []), nextScene] }),
      });
      const scenes = parseDemoScenes(body);
      setBundle({ ...bundle, scenes: scenes.length > 0 ? scenes : [...(bundle.scenes ?? []), nextScene] });
      setSceneId(nextScene.id);
      setSceneTitle("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setSceneBusy(false);
    }
  };

  const originMs = beats[0]?.wallMs ?? 0;
  const modeSpeed = settings.timing === "wall" ? settings.wallSpeed : settings.beatSpeed;
  const chip = nearestChip(modeSpeed);
  const chapter = (bundle?.scenes ?? []).find((item) => item.id === sceneId);
  const chapterLabel = chapter?.title ?? (sceneId === "full" ? t("demo.director.full") : sceneId);

  return (
    <main className={cn("flex h-full min-w-0 flex-1 flex-col bg-app", cinema && "demo-cinema")} data-cinema={cinema ? "true" : "false"}>
      {cinema ? null : (
      <div className="flex items-center gap-3 border-b border-hairline/40 px-4 py-2.5">
        <button
          type="button"
          onClick={() => dispatch({ type: "showChat" })}
          className="rounded-md p-1.5 text-ink-secondary hover:bg-raised hover:text-ink"
          aria-label={t("demo.exit")}
        >
          <ChevronLeft size={18} />
        </button>
        <Clapperboard size={16} className="text-ink-secondary" />
        <div className="min-w-0 flex-1">
          <div className="text-[15px] font-semibold text-ink">{t("demo.title")}</div>
          <div className="truncate text-[12px] text-ink-secondary">
            {bundle?.source === "recording"
              ? t("demo.source.recording", { when: bundle.recordedAt ?? "" })
              : t("demo.source.live")}
          </div>
        </div>
        <div className="flex items-center gap-1 rounded-lg bg-raised/60 p-0.5">
          <SourceButton
            label={t("demo.source.auto")}
            active={source === "auto"}
            onClick={() => setSource("auto")}
          />
          <SourceButton
            label={t("demo.source.liveShort")}
            active={source === "live"}
            onClick={() => setSource("live")}
          />
          <SourceButton
            label={t("demo.source.recordingShort")}
            active={source === "recording"}
            onClick={() => setSource("recording")}
          />
        </div>
        <label className="flex items-center gap-1 text-[12px] text-ink-secondary">
          <span className="hidden sm:inline">{t("demo.director.scene")}</span>
          <select
            value={sceneId}
            aria-label={t("demo.director.scene")}
            onChange={(event) => {
              const value = event.target.value;
              if (value === "full") {
                applyScene("full");
                return;
              }
              const scene = (bundle?.scenes ?? []).find((item) => item.id === value);
              if (scene) {
                applyScene(scene);
              }
            }}
            className="max-w-[10rem] rounded-md border border-hairline/40 bg-raised px-2 py-1 text-[12px] text-ink"
          >
            <option value="full">{t("demo.director.full")}</option>
            {(bundle?.scenes ?? []).map((scene) => (
              <option key={scene.id} value={scene.id}>
                {scene.title}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          onClick={() => void recordNow()}
          disabled={recordBusy}
          className="flex items-center gap-1.5 rounded-lg bg-control px-3 py-1.5 text-[13px] text-ink hover:bg-raised-hover disabled:opacity-50"
        >
          <Disc3 size={14} />
          {recordBusy ? t("demo.recording") : t("demo.record")}
        </button>
        <button
          type="button"
          onClick={() => setCinema((value) => !value)}
          className="rounded-lg bg-control px-3 py-1.5 text-[13px] text-ink hover:bg-raised-hover"
        >
          {t("demo.cinema")}
        </button>
      </div>
      )}

      <div className="relative min-h-0 flex-1">
        {busy && !bundle ? (
          <div className="flex h-full items-center justify-center text-[14px] text-ink-secondary">
            {t("demo.loading")}
          </div>
        ) : error && !bundle ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 px-6 text-center">
            <div className="text-[14px] text-danger">{error}</div>
            <div className="max-w-md text-[13px] text-ink-secondary">{t("demo.empty.hint")}</div>
          </div>
        ) : frame ? (
          <div className="relative h-full w-full" data-demo-playing={playing ? "true" : "false"} data-demo-timing={settings.timing} data-demo-held={frame.awake.some((pane) => pane.held) ? "true" : "false"} data-demo-overflow={frame.overflow}>
            {frame.awake.length === 0 && lastSeq === 0 ? (
              <WipeStage lastSeq={lastSeq} caption={caption(frame)} />
            ) : null}
            <DemoMosaic
              awake={frame.awake}
              layout={frame.layout}
              lingerMs={settings.lingerMs}
              reveals={playhead?.reveals ?? {}}
              showTimestamps={settings.showTimestamps}
              originMs={originMs}
            />
            {frame.overflow > 0 && !cinema ? (
              <div className="absolute right-3 top-3 z-10 rounded-full bg-raised/90 px-2.5 py-1 text-[11px] text-ink-secondary">
                {t("demo.overflow", { count: frame.overflow })}
              </div>
            ) : null}
            {cinema ? (
              <div className="demo-cinema-card pointer-events-none absolute inset-x-0 bottom-0 z-20 px-8 pb-8 pt-24">
                <div className="text-[13px] tracking-[0.18em] text-ink-secondary uppercase">{t("demo.cinema.kicker")}</div>
                <div className="mt-1 text-[28px] font-semibold text-ink">{chapterLabel}</div>
                <div className="mt-2 max-w-4xl text-[15px] leading-snug text-ink-secondary">
                  {frame ? caption(frame) : ""}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
        {error && bundle ? (
          <div className="absolute bottom-3 left-1/2 z-10 max-w-lg -translate-x-1/2 rounded-lg bg-danger/15 px-3 py-1.5 text-[12px] text-danger">
            {error}
          </div>
        ) : null}
      </div>

      {cinema ? null : (
      <div className="border-t border-hairline/40 px-4 py-3">
        <div className="mb-2 flex items-center gap-3">
          <button
            type="button"
            onClick={togglePlay}
            disabled={totalMs <= 0}
            className="rounded-md p-1.5 text-ink hover:bg-raised disabled:opacity-40"
            aria-label={playing ? t("demo.pause") : t("demo.play")}
          >
            {playing ? <Pause size={18} /> : <Play size={18} />}
          </button>
          <div className="flex items-center gap-1">
            {SPEED_CHIPS.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => {
                  if (settings.timing === "wall") {
                    patchSettings({ wallSpeed: item });
                    return;
                  }
                  patchSettings({ beatSpeed: item });
                }}
                className={cn(
                  "rounded-md px-2 py-1 text-[12px] tabular-nums",
                  chip === item ? "bg-raised text-ink" : "text-ink-secondary hover:bg-raised/60",
                )}
              >
                {item}×
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => patchSettings({ showTimestamps: !settings.showTimestamps })}
            className={cn(
              "flex items-center gap-1 rounded-md px-2 py-1 text-[12px]",
              settings.showTimestamps ? "bg-raised text-ink" : "text-ink-secondary hover:bg-raised/60",
            )}
            aria-pressed={settings.showTimestamps}
          >
            <Clock size={12} />
            {settings.showTimestamps ? t("demo.timestamps.on") : t("demo.timestamps.off")}
          </button>
          <div className="min-w-0 flex-1 truncate text-[12px] text-ink-secondary">
            {frame ? caption(frame) : t("demo.loading")}
          </div>
          <div className="text-[12px] tabular-nums text-ink-secondary">
            {formatShowClock(showMs)} / {formatShowClock(totalMs)}
          </div>
          <div className="text-[12px] tabular-nums text-ink-secondary">
            {t("demo.seq", { seq: playhead?.seq ?? 0, last: lastSeq })}
          </div>
          <form
            className="flex items-center gap-1"
            onSubmit={(event) => {
              event.preventDefault();
              const seq = Number(seqDraft);
              if (!Number.isFinite(seq) || beats.length === 0) {
                return;
              }
              setPlaying(false);
              setShowMs(showMsForSeq(beats, seq, settings));
            }}
          >
            <input
              type="number"
              inputMode="numeric"
              min={0}
              max={Math.max(lastSeq, 0)}
              step={1}
              value={seqDraft}
              onChange={(event) => setSeqDraft(event.target.value)}
              onFocus={() => setPlaying(false)}
              aria-label={t("demo.seqJump")}
              placeholder={t("demo.seqJump")}
              className="w-20 rounded-md border border-hairline/40 bg-raised px-2 py-1 text-[12px] tabular-nums text-ink"
            />
            <button
              type="submit"
              className="rounded-md px-2 py-1 text-[12px] text-ink-secondary hover:bg-raised hover:text-ink"
            >
              {t("demo.seqJumpGo")}
            </button>
          </form>
          <button
            type="button"
            onClick={() => setSettingsOpen((value) => !value)}
            className={cn(
              "rounded-md p-1.5 hover:bg-raised",
              settingsOpen ? "bg-raised text-ink" : "text-ink-secondary",
            )}
            aria-label={t("demo.settings.open")}
            aria-expanded={settingsOpen}
          >
            <Settings2 size={16} />
          </button>
        </div>
        <input
          type="range"
          min={0}
          max={1}
          step={0.001}
          value={progress}
          aria-label={t("demo.slider")}
          aria-valuetext={t("demo.seq", { seq: playhead?.seq ?? 0, last: lastSeq })}
          onChange={(event) => {
            setPlaying(false);
            setShowMs(Number(event.target.value) * totalMs);
          }}
          className="demo-timeline w-full"
        />
        {settingsOpen ? (
          <PlaybackSettings
            settings={settings}
            director={director}
            bots={bundle?.bots ?? []}
            lastSeq={lastSeq}
            sceneTitle={sceneTitle}
            sceneBusy={sceneBusy}
            onChange={patchSettings}
            onDirector={patchDirector}
            onSceneTitle={setSceneTitle}
            onSaveScene={() => void saveScene()}
            onReset={() => {
              savePlaybackSettings(DEFAULT_DEMO_PLAYBACK);
              const kept = totalMs > 0 ? showMs / totalMs : 0;
              setSettings(DEFAULT_DEMO_PLAYBACK);
              const nextTotal = bundle ? projectPlayhead(bundle, 0, DEFAULT_DEMO_PLAYBACK, director).totalMs : 0;
              setShowMs(kept * nextTotal);
            }}
            onResetDirector={() => {
              saveDirectorSettings(CAMERA_DEMO_DIRECTOR);
              setDirectorState(CAMERA_DEMO_DIRECTOR);
              setSceneId("full");
              setShowMs(0);
              setPlaying(false);
            }}
          />
        ) : null}
      </div>
      )}
    </main>
  );
}

function PlaybackSettings({
  settings,
  director,
  bots,
  lastSeq,
  sceneTitle,
  sceneBusy,
  onChange,
  onDirector,
  onSceneTitle,
  onSaveScene,
  onReset,
  onResetDirector,
}: {
  settings: DemoPlaybackSettings;
  director: DemoDirector;
  bots: readonly { id: string; slug: string; name: string }[];
  lastSeq: number;
  sceneTitle: string;
  sceneBusy: boolean;
  onChange: (partial: Partial<DemoPlaybackSettings>) => void;
  onDirector: (partial: Partial<DemoDirector>) => void;
  onSceneTitle: (value: string) => void;
  onSaveScene: () => void;
  onReset: () => void;
  onResetDirector: () => void;
}): React.ReactElement {
  const featured = new Set(director.featured.map((item) => item.toLowerCase()));
  return (
    <div className="mt-3 grid gap-3 rounded-xl border border-hairline/40 bg-raised/40 p-3 md:grid-cols-2">
      <div className="md:col-span-2 flex flex-wrap items-center justify-between gap-2">
        <div className="text-[12px] font-semibold text-ink">{t("demo.settings.title")}</div>
        <div className="flex items-center gap-1 rounded-lg bg-app p-0.5">
          <SourceButton
            label={t("demo.settings.beat")}
            active={settings.timing === "beat"}
            onClick={() => onChange({ timing: "beat" })}
          />
          <SourceButton
            label={t("demo.settings.wall")}
            active={settings.timing === "wall"}
            onClick={() => onChange({ timing: "wall" })}
          />
        </div>
        <button
          type="button"
          onClick={onReset}
          className="flex items-center gap-1 rounded-md px-2 py-1 text-[12px] text-ink-secondary hover:bg-raised hover:text-ink"
        >
          <RotateCcw size={12} />
          {t("demo.settings.reset")}
        </button>
      </div>
      <SettingRange
        label={t("demo.settings.beatMs")}
        value={settings.beatMs}
        min={200}
        max={6000}
        step={50}
        display={`${(settings.beatMs / 1000).toFixed(1)}s`}
        onChange={(value) => onChange({ beatMs: value })}
      />
      <SettingRange
        label={t("demo.settings.beatSpeed")}
        value={settings.beatSpeed}
        min={0.25}
        max={8}
        step={0.25}
        display={`${settings.beatSpeed.toFixed(2)}×`}
        onChange={(value) => onChange({ beatSpeed: value })}
      />
      <SettingRange
        label={t("demo.settings.wallSpeed")}
        value={settings.wallSpeed}
        min={0.25}
        max={8}
        step={0.25}
        display={`${settings.wallSpeed.toFixed(2)}×`}
        onChange={(value) => onChange({ wallSpeed: value })}
      />
      <SettingRange
        label={t("demo.settings.wallGap")}
        value={settings.wallMaxGapMs}
        min={0}
        max={30_000}
        step={250}
        display={settings.wallMaxGapMs === 0 ? t("demo.settings.wallGapOff") : `${(settings.wallMaxGapMs / 1000).toFixed(1)}s`}
        onChange={(value) => onChange({ wallMaxGapMs: value })}
      />
      <label className="flex items-center justify-between gap-3 rounded-lg bg-app px-3 py-2 text-[12px] text-ink">
        <span>{t("demo.settings.stream")}</span>
        <input
          type="checkbox"
          checked={settings.stream}
          onChange={(event) => onChange({ stream: event.target.checked })}
        />
      </label>
      <label className="flex items-center justify-between gap-3 rounded-lg bg-app px-3 py-2 text-[12px] text-ink">
        <span>{t("demo.settings.timestamps")}</span>
        <input
          type="checkbox"
          checked={settings.showTimestamps}
          onChange={(event) => onChange({ showTimestamps: event.target.checked })}
        />
      </label>
      <SettingRange
        label={t("demo.settings.streamRate")}
        value={settings.streamCharsPerSec}
        min={12}
        max={240}
        step={4}
        display={`${Math.round(settings.streamCharsPerSec)}/s`}
        onChange={(value) => onChange({ streamCharsPerSec: value })}
      />
      <SettingRange
        label={t("demo.settings.streamHold")}
        value={settings.streamHold}
        min={0}
        max={0.45}
        step={0.01}
        display={`${Math.round(settings.streamHold * 100)}%`}
        onChange={(value) => onChange({ streamHold: value })}
      />
      <SettingRange
        label={t("demo.settings.lead")}
        value={settings.leadMs}
        min={0}
        max={2000}
        step={20}
        display={`${(settings.leadMs / 1000).toFixed(2)}s`}
        onChange={(value) => onChange({ leadMs: value })}
      />
      <SettingRange
        label={t("demo.settings.linger")}
        value={settings.lingerMs}
        min={0}
        max={2000}
        step={20}
        display={`${(settings.lingerMs / 1000).toFixed(2)}s`}
        onChange={(value) => onChange({ lingerMs: value })}
      />
      <div className="md:col-span-2 mt-1 flex flex-wrap items-center justify-between gap-2 border-t border-hairline/30 pt-3">
        <div className="text-[12px] font-semibold text-ink">{t("demo.director.title")}</div>
        <button
          type="button"
          onClick={onResetDirector}
          className="flex items-center gap-1 rounded-md px-2 py-1 text-[12px] text-ink-secondary hover:bg-raised hover:text-ink"
        >
          <RotateCcw size={12} />
          {t("demo.settings.resetDirector")}
        </button>
      </div>
      <div className="md:col-span-2">
        <div className="mb-1 text-[11px] text-ink-secondary">{t("demo.director.panes")}</div>
        <div className="flex flex-wrap gap-1">
          {PANE_CAPS.map((count) => (
            <button
              key={count}
              type="button"
              onClick={() => onDirector({ maxPanes: count })}
              className={cn(
                "rounded-md px-2 py-1 text-[12px] tabular-nums",
                director.maxPanes === count ? "bg-app text-ink" : "text-ink-secondary hover:bg-raised",
              )}
            >
              {count}
            </button>
          ))}
        </div>
      </div>
      <label className="block">
        <div className="mb-1 text-[11px] text-ink-secondary">{t("demo.director.from")}</div>
        <input
          type="number"
          min={0}
          max={Math.max(lastSeq, 0)}
          value={director.seqFrom}
          onChange={(event) => onDirector({ seqFrom: Number(event.target.value) })}
          className="w-full rounded-md border border-hairline/40 bg-app px-2 py-1 text-[12px] tabular-nums text-ink"
        />
      </label>
      <label className="block">
        <div className="mb-1 text-[11px] text-ink-secondary">{t("demo.director.to")}</div>
        <input
          type="number"
          min={0}
          max={Math.max(lastSeq, 0)}
          value={director.seqTo}
          onChange={(event) => onDirector({ seqTo: Number(event.target.value) })}
          className="w-full rounded-md border border-hairline/40 bg-app px-2 py-1 text-[12px] tabular-nums text-ink"
        />
      </label>
      <div className="md:col-span-2">
        <div className="mb-1 text-[11px] text-ink-secondary">{t("demo.director.featured")}</div>
        <div className="flex flex-wrap gap-1">
          {bots.map((bot) => {
            const active = featured.has(bot.slug.toLowerCase()) || featured.has(bot.id.toLowerCase());
            return (
              <button
                key={bot.id}
                type="button"
                onClick={() => {
                  const next = active
                    ? director.featured.filter((item) => item.toLowerCase() !== bot.slug.toLowerCase() && item.toLowerCase() !== bot.id.toLowerCase())
                    : [...director.featured, bot.slug];
                  onDirector({ featured: next });
                }}
                className={cn(
                  "rounded-md px-2 py-1 text-[12px]",
                  active ? "bg-app text-ink" : "text-ink-secondary hover:bg-raised",
                )}
              >
                {bot.slug}
              </button>
            );
          })}
        </div>
      </div>
      <div className="md:col-span-2 flex flex-wrap items-center gap-2">
        <input
          type="text"
          value={sceneTitle}
          onChange={(event) => onSceneTitle(event.target.value)}
          placeholder={t("demo.director.titleField")}
          className="min-w-[12rem] flex-1 rounded-md border border-hairline/40 bg-app px-2 py-1 text-[12px] text-ink"
        />
        <button
          type="button"
          onClick={onSaveScene}
          disabled={sceneBusy}
          className="rounded-md bg-control px-3 py-1.5 text-[12px] text-ink hover:bg-raised-hover disabled:opacity-50"
        >
          {sceneBusy ? t("demo.director.saving") : t("demo.director.save")}
        </button>
      </div>
    </div>
  );
}

function SettingRange({
  label,
  value,
  min,
  max,
  step,
  display,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  display: string;
  onChange: (value: number) => void;
}): React.ReactElement {
  return (
    <label className="block">
      <div className="mb-1 flex justify-between text-[11px] text-ink-secondary">
        <span>{label}</span>
        <span className="tabular-nums text-ink">{display}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-raised accent-[var(--accent)]"
      />
    </label>
  );
}

function SourceButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}): React.ReactElement {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-md px-2 py-1 text-[12px]",
        active ? "bg-app text-ink" : "text-ink-secondary hover:text-ink",
      )}
    >
      {label}
    </button>
  );
}

function WipeStage({ lastSeq, caption }: { lastSeq: number; caption: string }): React.ReactElement {
  return (
    <div className="absolute inset-0 z-0 flex flex-col items-center justify-center gap-3 px-8 text-center">
      <Circle size={28} className="text-ink-secondary/50" />
      <div className="text-[16px] font-semibold text-ink">{t("demo.wipe")}</div>
      <div className="max-w-lg text-[13px] text-ink-secondary">{t("demo.empty.hint")}</div>
      <div className="text-[12px] text-ink-secondary/80">
        {lastSeq === 0 ? t("demo.empty.none") : caption}
      </div>
    </div>
  );
}

function DemoMosaic({
  awake,
  layout,
  lingerMs,
  reveals,
  showTimestamps,
  originMs,
}: {
  awake: readonly DemoAwakeBot[];
  layout: readonly MosaicCell[];
  lingerMs: number;
  reveals: Readonly<Record<string, DemoMessageReveal>>;
  showTimestamps: boolean;
  originMs: number;
}): React.ReactElement {
  const liveRef = useRef(new Map<string, { pane: DemoAwakeBot; cell: MosaicCell }>());
  const [ghosts, setGhosts] = useState<Map<string, { pane: DemoAwakeBot; cell: MosaicCell }>>(new Map());

  useEffect(() => {
    const nextLive = new Map<string, { pane: DemoAwakeBot; cell: MosaicCell }>();
    awake.forEach((pane, index) => {
      const cell = layout[index];
      if (cell) {
        nextLive.set(pane.botId, { pane, cell });
      }
    });
    const gone: Array<{ id: string; pane: DemoAwakeBot; cell: MosaicCell }> = [];
    for (const [id, prev] of liveRef.current) {
      if (!nextLive.has(id)) {
        gone.push({ id, ...prev });
      }
    }
    liveRef.current = nextLive;
    setGhosts((current) => {
      const copy = new Map(current);
      for (const id of nextLive.keys()) {
        copy.delete(id);
      }
      if (lingerMs > 0) {
        for (const item of gone) {
          copy.set(item.id, { pane: item.pane, cell: item.cell });
        }
      }
      return copy;
    });
    if (gone.length === 0 || lingerMs <= 0) {
      return;
    }
    const timer = window.setTimeout(() => {
      setGhosts((current) => {
        const copy = new Map(current);
        for (const item of gone) {
          copy.delete(item.id);
        }
        return copy;
      });
    }, lingerMs);
    return () => window.clearTimeout(timer);
  }, [awake, layout, lingerMs]);

  const items = [
    ...awake.map((pane, index) => ({
      pane,
      cell: layout[index] ?? { index, left: 0, top: 0, width: 100, height: 100 },
      exiting: false,
    })),
    ...[...ghosts.values()].map((item) => ({ ...item, exiting: true })),
  ];

  return (
    <div
      className="relative z-[1] h-full w-full"
      data-demo-awake={awake.length}
      style={{ ["--demo-linger"]: `${Math.max(180, lingerMs)}ms` } as CSSProperties}
    >
      {items.map((item) => (
        <div
          key={item.pane.botId}
          data-bot-slug={item.pane.slug}
          data-exiting={item.exiting ? "true" : "false"}
          data-held={item.pane.held ? "true" : "false"}
          className="demo-mosaic-cell absolute overflow-hidden p-1"
          style={{
            left: `${item.cell.left}%`,
            top: `${item.cell.top}%`,
            width: `${item.cell.width}%`,
            height: `${item.cell.height}%`,
          }}
        >
          <DemoPane
            pane={item.pane}
            solo={awake.length === 1 && !item.exiting}
            reveals={reveals}
            showTimestamps={showTimestamps}
            originMs={originMs}
          />
        </div>
      ))}
    </div>
  );
}

function DemoPane({
  pane,
  solo,
  reveals,
  showTimestamps,
  originMs,
}: {
  pane: DemoAwakeBot;
  solo: boolean;
  reveals: Readonly<Record<string, DemoMessageReveal>>;
  showTimestamps: boolean;
  originMs: number;
}): React.ReactElement {
  const scroller = useRef<HTMLDivElement>(null);
  const lastKey = pane.messages.at(-1) ? revealKey(pane.botId, pane.messages[pane.messages.length - 1]!) : "";
  const lastReveal = lastKey ? reveals[lastKey] : undefined;
  useEffect(() => {
    const node = scroller.current;
    if (node) {
      node.scrollTop = node.scrollHeight;
    }
  }, [pane.messages.length, pane.activity, lastReveal?.revealed.length]);

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-xl border border-hairline/40 bg-app">
      <div className="flex items-center gap-2 border-b border-hairline/40 px-3 py-2">
        <MausAvatar
          color={asMausColor(pane.color)}
          size={solo ? 36 : 28}
          state={pane.held ? "idle" : pane.status === "running" ? "working" : "loading"}
          label={pane.name}
        />
        <div className="min-w-0 flex-1">
          <div className="truncate text-[14px] font-semibold text-ink">{pane.name}</div>
          <div className="truncate text-[11px] text-ink-secondary">{pane.purpose}</div>
        </div>
        <div
          className={cn(
            "flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px]",
            pane.held ? "bg-raised text-ink-secondary" : pane.status === "running" ? "bg-accent/15 text-accent" : "bg-raised text-ink-secondary",
          )}
        >
          {pane.held ? <Radio size={11} /> : pane.status === "running" ? <WorkingDots size={3} /> : <Radio size={11} />}
          {pane.held ? t("demo.pane.idle") : pane.activity}
        </div>
      </div>
      <div ref={scroller} className="min-h-0 flex-1 space-y-3 overflow-y-auto px-3 py-3">
        {pane.messages.length === 0 ? (
          <div className="text-[13px] text-ink-secondary">{pane.prompt ?? t("demo.pane.empty")}</div>
        ) : (
          pane.messages.map((row) => (
            <DemoBubble
              key={`${row.seq}:${row.kind}`}
              row={row}
              reveal={reveals[revealKey(pane.botId, row)]}
              showTimestamps={showTimestamps}
              originMs={originMs}
            />
          ))
        )}
      </div>
    </div>
  );
}

function DemoBubble({
  row,
  reveal,
  showTimestamps,
  originMs,
}: {
  row: TranscriptEntry;
  reveal: DemoMessageReveal | undefined;
  showTimestamps: boolean;
  originMs: number;
}): React.ReactElement {
  const { text, streaming } = streamedCopy(row, reveal);
  const stamp = showTimestamps ? formatStamp(row.t, originMs) : "";
  if (isToolCall(row)) {
    return (
      <div className="flex justify-center">
        <div className="rounded-full border border-accent/40 bg-accent/10 px-3 py-1 text-[12px] font-medium text-accent">
          {text}
          {streaming ? <span className="demo-stream-caret" aria-hidden="true" /> : null}
        </div>
      </div>
    );
  }
  if (isUserLine(row)) {
    return (
      <div className="flex flex-col items-end gap-1">
        {stamp ? <div className="px-1 text-[10px] tabular-nums text-ink-secondary/80">{stamp}</div> : null}
        <div className="w-fit max-w-[min(42rem,86%)] rounded-2xl bg-bubble-user px-4 py-2.5 text-[15px] leading-relaxed whitespace-pre-wrap text-ink animate-msg-in">
          {text}
          {streaming ? <span className="demo-stream-caret" aria-hidden="true" /> : null}
        </div>
      </div>
    );
  }
  if (isResultLine(row)) {
    return (
      <div className="flex flex-col items-start gap-1">
        {stamp ? <div className="px-1 text-[10px] tabular-nums text-ink-secondary/80">{stamp}</div> : null}
        <div className="w-fit max-w-[min(42rem,86%)] rounded-2xl bg-card px-4 py-2.5 text-[15px] leading-relaxed text-ink animate-msg-in">
          <ChatMarkdown text={text} streaming={streaming} />
          {streaming ? <span className="demo-stream-caret" aria-hidden="true" /> : null}
        </div>
      </div>
    );
  }
  return (
    <div className="text-center">
      {stamp ? <div className="mb-0.5 text-[10px] tabular-nums text-ink-secondary/80">{stamp}</div> : null}
      <div className="text-[12px] text-ink-secondary">{text}</div>
    </div>
  );
}

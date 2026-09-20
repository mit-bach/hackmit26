import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Menu } from "lucide-react";
import { StoreProvider, useStore } from "@/state/store";
import { ThreadRefsProvider } from "@/components/ThreadRefs";
import { Sidebar } from "@/components/Sidebar";
import { ChatView } from "@/components/ChatView";
import { GroupView } from "@/components/GroupView";
import { BotSettingsDialog } from "@/components/BotSettingsDialog";
import { NewBotDialog } from "@/components/NewBotDialog";
import { ComputerPanel } from "@/components/ComputerPanel";
import { InspectorPanel } from "@/components/InspectorPanel";
import { SettingsModal } from "@/components/SettingsModal";
import { DesktopCapabilitiesProvider, useDesktopCapabilities } from "@/components/DesktopCapabilities";
import { WindowCaptionButtons } from "@/components/WindowCaptionButtons";
import { RoutinesPage } from "@/components/RoutinesPage";
import { ProtocolPage } from "@/components/ProtocolPage";
import { DemoPage } from "@/components/DemoPage";
import { CommandPalette } from "@/components/CommandPalette";
import { KeyboardShortcutsModal } from "@/components/KeyboardShortcutsModal";
import { setLocale, t } from "@/lib/i18n";
import { shouldOpenKeyboardShortcuts } from "@/lib/keyboard-shortcuts";

function Shell(): React.ReactElement {
  const { state, dispatch } = useStore();
  const { capabilities } = useDesktopCapabilities();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const language = state.config?.language ?? "";
  const [, setLocaleEpoch] = useState(0);
  useEffect(() => {
    setLocale(language || globalThis.navigator?.language);
    setLocaleEpoch((epoch) => epoch + 1);
  }, [language]);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const group = state.groups.find((item) => item.id === state.selectedId);
  const pairPending = !group && state.selectedId.startsWith("pair:");
  const bot = group || pairPending
    ? undefined
    : (state.bots.find((item) => item.id === state.selectedId) ?? state.bots[0]);
  const inspectorBot =
    bot ??
    (group
      ? state.bots.find((item) => item.id === group.busyBotId && group.memberIds.includes(item.id)) ??
        state.bots.find((item) => group.memberIds.includes(item.id))
      : undefined);
  const calendarFocus = state.activeView === "routines";
  const demoFocus = state.activeView === "demo";
  const hideSidebar = calendarFocus || demoFocus;

  useEffect(() => {
    const onKey = (event: KeyboardEvent): void => {
      if (event.defaultPrevented || event.isComposing || state.shortcutsOpen) {
        return;
      }
      if (shouldOpenKeyboardShortcuts(event)) {
        event.preventDefault();
        dispatch({ type: "toggleShortcuts", open: true });
        return;
      }
      const mod = event.metaKey || event.ctrlKey;
      if (!mod) {
        return;
      }
      const bots = state.bots.filter((item) => !item.hidden);
      if (event.key === "n" && !event.shiftKey) {
        event.preventDefault();
        dispatch({ type: "toggleNewBot", open: true });
      } else if (/^[1-9]$/.test(event.key)) {
        const target = bots[Number(event.key) - 1];
        if (target) {
          event.preventDefault();
          dispatch({ type: "select", id: target.id });
        }
      } else if (event.shiftKey && (event.key === "[" || event.key === "]")) {
        const idx = bots.findIndex((item) => item.id === state.selectedId);
        const next = bots[(idx + (event.key === "]" ? 1 : -1) + bots.length) % bots.length];
        if (next) {
          event.preventDefault();
          dispatch({ type: "select", id: next.id });
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [state.bots, state.selectedId, state.shortcutsOpen, dispatch]);

  useEffect(() => {
    setDrawerOpen(false);
  }, [state.selectedId, bot?.threadId, group?.threadId, state.activeView, state.settingsOpen]);

  const closeCalendar = useCallback((): void => {
    dispatch({ type: "select", id: state.selectedId });
  }, [dispatch, state.selectedId]);
  const openCalendarRoom = useCallback(
    (id: string): void => {
      dispatch({ type: "select", id });
    },
    [dispatch],
  );

  useEffect(() => {
    return window.ogb?.onOpenAppSettings?.(() => dispatch({ type: "toggleAppSettings", open: true }));
  }, [dispatch]);

  return (
    <div className="flex h-full flex-col">
      <div className="relative flex min-h-0 flex-1">
        {!hideSidebar && (
          <button
            type="button"
            ref={menuButtonRef}
            aria-label="Open bot list"
            aria-expanded={drawerOpen}
            onClick={() => setDrawerOpen(true)}
            className="absolute left-3 top-3 z-30 rounded-md p-1.5 text-ink-secondary hover:bg-raised hover:text-ink md:hidden"
          >
            <Menu size={18} />
          </button>
        )}
        {drawerOpen && !hideSidebar && (
          <div
            aria-hidden
            onMouseDown={(event) => event.target === event.currentTarget && setDrawerOpen(false)}
            className="absolute inset-0 z-30 bg-black/50 md:hidden"
          />
        )}
        {!hideSidebar && (
          <Sidebar
            open={drawerOpen}
            onClose={() => {
              setDrawerOpen(false);
              menuButtonRef.current?.focus();
            }}
          />
        )}
        {state.activeView === "demo" ? (
          <DemoPage />
        ) : state.activeView === "protocol" ? (
          <ProtocolPage />
        ) : state.activeView === "computer" ? (
          <ComputerPanel bot={bot} />
        ) : state.activeView === "routines" ? (
          <RoutinesPage onBack={closeCalendar} onOpenRoom={openCalendarRoom} />
        ) : group ? (
          <GroupView key={group.id} group={group} />
        ) : bot ? (
          <ChatView bot={bot} />
        ) : (
          <main className="flex h-full min-w-0 flex-1 flex-col items-center justify-center gap-3 bg-app text-ink-secondary">
            {state.connected && !pairPending ? null : <Loader2 size={20} className="animate-spin" />}
            <div className="text-[14px]">
              {pairPending
                ? t("pair.log.loading")
                : state.connected
                  ? "No Bots on this Computer."
                  : "Connecting to the Harness host…"}
            </div>
            {state.connected && !pairPending ? (
              <button
                type="button"
                onClick={() => dispatch({ type: "toggleNewBot", open: true })}
                className="rounded-lg bg-control px-3 py-2 text-[13px] text-ink hover:bg-raised-hover"
              >
                Add a Bot
              </button>
            ) : pairPending ? null : (
              <div className="text-[12px]">
                Start it with <code className="rounded bg-raised px-1.5 py-0.5">npm run serve -- --computer DIR</code>
              </div>
            )}
          </main>
        )}
        {state.settingsOpen && bot && <BotSettingsDialog key={`settings:${bot.id}`} bot={bot} />}
        {state.computerOpen && state.activeView === "chat" && (
          <ComputerPanel key={`computer:${(bot ?? inspectorBot)?.id ?? "floor"}`} bot={bot ?? inspectorBot} />
        )}
        {state.inspectorOpen && inspectorBot && <InspectorPanel key={inspectorBot.threadId} bot={inspectorBot} />}
        {state.appSettingsOpen && <SettingsModal />}
        {state.newBotOpen && <NewBotDialog />}
        {state.shortcutsOpen && (
          <KeyboardShortcutsModal
            open={state.shortcutsOpen}
            onClose={() => dispatch({ type: "toggleShortcuts", open: false })}
          />
        )}
        <CommandPalette onOpenChange={setPaletteOpen} />
      </div>
      <WindowCaptionButtons
        visible={capabilities.windowChrome === "win-caption" && Boolean(window.ogb?.windowControls)}
      />
    </div>
  );
}

export default function App(): React.ReactElement {
  return (
    <DesktopCapabilitiesProvider>
      <StoreProvider>
        <ThreadRefsProvider>
          <Shell />
        </ThreadRefsProvider>
      </StoreProvider>
    </DesktopCapabilitiesProvider>
  );
}

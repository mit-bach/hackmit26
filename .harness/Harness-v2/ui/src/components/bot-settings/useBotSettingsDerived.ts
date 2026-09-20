// Values the bot-settings sections still need from the store.
import { stateForBot, type MausMotion, type MausState } from "@/lib/mascot";
import type { Routine } from "@/lib/routines";
import { useStore, type Bot } from "@/state/store";

export type BotPatch = Partial<
  Pick<
    Bot,
    | "name"
    | "title"
    | "description"
    | "soul"
    | "harnessSlug"
    | "notifications"
    | "color"
    | "mascotExpression"
    | "mascotBody"
    | "avatarUrl"
    | "avatarCrop"
    | "alwaysAllow"
    | "autoApprove"
    | "approvalMode"
    | "approvalLevel"
  >
>;

export interface BotSettingsDerived {
  readonly patch: (next: BotPatch) => void;
  readonly botRoutines: Routine[];
  readonly activeState: MausState;
  readonly mascotMotion: { kind: Exclude<MausMotion, "none">; nonce: number } | null;
}

export function useBotSettingsDerived(bot: Bot): BotSettingsDerived {
  const { state, dispatch } = useStore();
  const patch = (next: BotPatch): void => {
    dispatch({ type: "updateBot", botId: bot.id, patch: next });
  };
  const botRoutines = state.routines.filter((routine) => routine.botId === bot.id);
  const mascotMotion = state.mascotMotion?.botId === bot.id ? state.mascotMotion : null;
  return {
    patch,
    botRoutines,
    activeState: stateForBot(bot),
    mascotMotion,
  };
}

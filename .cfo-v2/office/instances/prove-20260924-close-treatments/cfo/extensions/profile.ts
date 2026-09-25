import {EMPTY_GRANT, type BindRefuseReason, type BoundProfile, type BotSlugEntry, type EvalPhase, type GrantSet, type GrantsFile, type SlugMapFile} from "./types.ts";

const EMPTY: GrantSet = EMPTY_GRANT;

const PROFILE_HEADER = /^profile:\s*([A-Za-z0-9_-]+)\s*$/im;

export function parseProfileFromWake(text: string): string | undefined {
  const match = PROFILE_HEADER.exec(text);
  const name = match?.[1];
  return name && name.length > 0 ? name : undefined;
}

export function chooseProfileName(
  requested: string | undefined,
  entry: BotSlugEntry,
): string {
  if (requested && requested.length > 0) {
    return requested;
  }
  return entry.defaultProfile;
}

export function botIdForSlug(slug: string): string {
  return `bot_${slug.replace(/-/g, "_")}`;
}

export function bindBot(options: {
  readonly computerRoot: string;
  readonly slug: string;
  readonly profile?: string;
  readonly phase?: EvalPhase;
  readonly grants: GrantsFile;
  readonly slugMap: SlugMapFile;
}): BoundProfile {
  const phase = options.phase ?? "operational";
  const botId = botIdForSlug(options.slug);
  const entry = options.slugMap.bots[options.slug];
  if (!entry) {
    return refused(options.computerRoot, options.slug, botId, "", "", phase, "unknown_slug");
  }
  const profile = chooseProfileName(options.profile, entry);
  const displayName = entry.profiles[profile];
  if (displayName === undefined) {
    return refused(
      options.computerRoot,
      options.slug,
      botId,
      profile,
      "",
      phase,
      "missing_profile",
    );
  }
  if (displayName.length === 0) {
    return refused(
      options.computerRoot,
      options.slug,
      botId,
      profile,
      displayName,
      phase,
      "missing_display_name",
    );
  }
  const grant = options.grants.byDisplayName[displayName];
  if (!grant) {
    return refused(
      options.computerRoot,
      options.slug,
      botId,
      profile,
      displayName,
      phase,
      "missing_display_name",
    );
  }
  return {
    computerRoot: options.computerRoot,
    slug: options.slug,
    botId,
    profile,
    displayName,
    grant,
    phase,
    connectors: true,
  };
}

function refused(
  computerRoot: string,
  slug: string,
  botId: string,
  profile: string,
  displayName: string,
  phase: EvalPhase,
  reason: BindRefuseReason,
): BoundProfile {
  return {
    computerRoot,
    slug,
    botId,
    profile,
    displayName,
    grant: EMPTY,
    phase,
    connectors: false,
    refuseReason: reason,
  };
}

export function replaceProfile(_previous: BoundProfile, next: BoundProfile): BoundProfile {
  return next;
}

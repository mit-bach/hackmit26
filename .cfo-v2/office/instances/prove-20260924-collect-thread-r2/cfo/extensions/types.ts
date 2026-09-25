/**
 * Client-system Catalog, Grants, and bind types.
 * Finance domain objects (invoices, ledgers) do not appear here.
 */

export type EvalPhase = "operational" | "evaluation";

export type Mutability = "read" | "write-local" | "side-effect-external";

export interface CatalogOp {
  readonly id: string;
  readonly python: string;
  readonly exportName: string;
  readonly args: Readonly<Record<string, string>>;
  readonly mutability: Mutability;
  readonly sodClass: string;
  readonly evalOnly: boolean;
  readonly ownerPrefixes: readonly string[];
}

export interface CatalogFile {
  readonly version: string;
  readonly ops: readonly CatalogOp[];
}

export interface GrantSet {
  readonly ops: readonly string[];
  readonly skills: readonly string[];
  readonly outputType: string;
}

export interface GrantsFile {
  readonly version: string;
  readonly byDisplayName: Readonly<Record<string, GrantSet>>;
}

export interface BotSlugEntry {
  readonly defaultProfile: string;
  readonly profiles: Readonly<Record<string, string>>;
  readonly allowSodOverlap: boolean;
}

export interface SlugMapFile {
  readonly version: string;
  readonly bots: Readonly<Record<string, BotSlugEntry>>;
}

export interface PathLeaseBot {
  readonly writePrefixes: readonly string[];
}

export interface PathLeaseFile {
  readonly version: string;
  readonly bots: Readonly<Record<string, PathLeaseBot>>;
}

export type BindRefuseReason =
  | "unbound"
  | "unknown_slug"
  | "union_forbidden"
  | "missing_profile"
  | "missing_display_name";

export interface BoundProfile {
  readonly computerRoot: string;
  readonly slug: string;
  readonly botId: string;
  readonly profile: string;
  readonly displayName: string;
  readonly grant: GrantSet;
  readonly phase: EvalPhase;
  readonly connectors: boolean;
  readonly refuseReason?: BindRefuseReason;
}

export interface SearchQuery {
  readonly query: string;
  readonly status?: string;
}

export interface ConnectedToolHit {
  readonly id: string;
  readonly exportName: string;
  readonly args: Readonly<Record<string, string>>;
  readonly mutability: Mutability;
}

export interface CallRequest {
  readonly name: string;
  readonly args: Readonly<Record<string, unknown>>;
  readonly idempotencyKey?: string;
}

export interface CallResult {
  readonly ok: boolean;
  readonly error: string | null;
  readonly result: unknown;
  readonly traceId: string | null;
}

export interface VerifierRoute {
  readonly slug: string;
  readonly profile: string;
  readonly reason: string;
}

export const EMPTY_GRANT: GrantSet = {
  ops: [],
  skills: [],
  outputType: "",
};

export interface PathLeaseBot {
  readonly writePrefixes: readonly string[];
}

export interface PathLeaseFile {
  readonly version: string;
  readonly bots: Readonly<Record<string, PathLeaseBot>>;
};

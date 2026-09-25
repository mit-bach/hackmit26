/**
 * Canonical names for the Harness control plane.
 * One name for one thing. A child is not a Bot. A Handle is not a Receipt.
 */

export type BotStatus = "offline" | "idle" | "running" | "blocked";

export type ApprovalLevel = "ask" | "always" | "never";

export type HandleStatus =
  | "accepted"
  | "queued"
  | "running"
  | "blocked"
  | "completed"
  | "failed"
  | "cancelled";

export type MessageKind =
  | "user_dm"
  | "user_stop"
  | "a2a_handoff"
  | "group_post"
  | "group_mention"
  | "result"
  | "routine";

export type SendMode = "async" | "fire_and_forget" | "blocking";

export type BusyPolicy = "queue" | "supersede" | "reject";

export type InboxItemStatus = "pending" | "claimed" | "done";

export type ConversationKind = "operator_dm" | "peer_dm" | "room";

export interface Conversation {
  readonly kind: ConversationKind;
  readonly botId?: string;
  readonly fromId?: string;
  readonly toId?: string;
  readonly roomId?: string;
}

export interface BotRecord {
  readonly id: string;
  readonly name: string;
  readonly slug: string;
  readonly purpose: string;
  readonly instructions: string;
  readonly skills: readonly string[];
  readonly connectors: readonly string[];
  readonly approvalLevel: ApprovalLevel;
}

export interface RoomRecord {
  readonly id: string;
  readonly title: string;
  readonly members: readonly string[];
}

export interface RoutineRecord {
  readonly name: string;
  readonly bot: string;
  readonly cadence: string;
  readonly prompt: string;
  readonly conversation: string;
}

export interface Roster {
  readonly system: string;
  readonly version: string;
  readonly description: string;
  readonly computer: string;
  readonly bots: readonly BotRecord[];
  readonly rooms: readonly RoomRecord[];
  readonly routines: readonly RoutineRecord[];
}

export interface HandleRecord {
  readonly id: string;
  readonly from: string;
  readonly to: string;
  readonly toSlug: string;
  readonly prompt: string;
  readonly paths: readonly string[];
  readonly conversation: Conversation;
  readonly kind: MessageKind;
  readonly status: HandleStatus;
  readonly createdAt: string;
  readonly updatedAt: string;
  readonly result?: string;
  readonly resultPaths?: readonly string[];
  readonly seq?: number;
  readonly error?: string;
  readonly blockedReason?: string;
}

export interface InboxItem {
  readonly id: string;
  readonly handleId: string;
  readonly kind: MessageKind;
  readonly from: string;
  readonly to: string;
  readonly conversation: Conversation;
  readonly prompt: string;
  readonly paths: readonly string[];
  readonly mentions: readonly string[];
  readonly createdAt: string;
  readonly status: InboxItemStatus;
  readonly claimedByPid?: number;
  readonly claimedAt?: string;
}

export interface ProtocolEvent {
  readonly t: string;
  readonly seq: number;
  readonly type: string;
  readonly from?: string;
  readonly to?: string;
  readonly handleId?: string;
  readonly roomId?: string;
  readonly slug?: string;
  readonly text?: string;
  readonly status?: string;
  readonly paths?: readonly string[];
}

export interface LaneState {
  readonly botId: string;
  readonly slug: string;
  readonly status: BotStatus;
  readonly pid: number;
  readonly handleId?: string;
  readonly updatedAt: string;
}

export interface TurnResult {
  readonly text: string;
  readonly paths: readonly string[];
  readonly error?: string;
}

export interface SendRequest {
  readonly computerRoot: string;
  readonly from: string;
  readonly to: string;
  readonly prompt: string;
  readonly mode?: SendMode;
  readonly onBusy?: BusyPolicy;
  readonly paths?: readonly string[];
  readonly conversation?: Conversation;
  readonly kind?: MessageKind;
  readonly mentions?: readonly string[];
}

export interface SendResult {
  readonly accepted: boolean;
  readonly handleId?: string;
  readonly botId?: string;
  readonly slug?: string;
  readonly status?: HandleStatus;
  readonly reason?: string;
}

export interface AwaitResult {
  readonly handleId: string;
  readonly status: HandleStatus;
  readonly done: boolean;
  readonly result?: string;
  readonly seq?: number;
}

export interface TranscriptEntry {
  readonly seq: number;
  readonly t: string;
  readonly kind: string;
  readonly text: string;
  readonly handleId?: string;
  readonly from?: string;
  readonly to?: string;
}

export interface ApprovalRecord {
  readonly id: string;
  readonly botId: string;
  readonly handleId?: string;
  readonly toolName: string;
  readonly detail: string;
  readonly status: "pending" | "allowed" | "denied";
  readonly createdAt: string;
  readonly resolvedAt?: string;
}

export interface ReceiptRecord {
  readonly id: string;
  readonly name: string;
  readonly bot: string;
  readonly handleId?: string;
  readonly status: "queued" | "running" | "completed" | "failed" | "missed";
  readonly at: string;
  readonly updatedAt: string;
  readonly result?: string;
}

export interface SearchHit {
  readonly id: string;
  readonly slug: string;
  readonly name: string;
  readonly purpose: string;
  readonly status: BotStatus;
}

export interface ParsedAsk {
  readonly slug: string;
  readonly botId: string;
  readonly question: string;
}

export interface AskPeerResult {
  readonly accepted: boolean;
  readonly handleId?: string;
  readonly status?: HandleStatus;
  readonly done?: boolean;
  readonly result?: string;
  readonly error?: string;
  readonly reason?: string;
}

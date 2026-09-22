import {existsSync} from "node:fs";
import {join} from "node:path";
import {pathToFileURL} from "node:url";

import {isRecord} from "./load.ts";

export interface PeerSendRequest {
  readonly computerRoot: string;
  readonly from: string;
  readonly to: string;
  readonly prompt: string;
  readonly paths: readonly string[];
}

interface SendPromptFn {
  (input: {
    readonly computerRoot: string;
    readonly from: string;
    readonly to: string;
    readonly prompt: string;
    readonly paths?: readonly string[];
  }): unknown;
}

function sendPromptOf(value: unknown): SendPromptFn | undefined {
  if (!isRecord(value) || typeof value.sendPrompt !== "function") {
    return undefined;
  }
  const fn = value.sendPrompt;
  return (input): unknown => Reflect.apply(fn, undefined, [input]);
}

export async function sendPeerHandle(request: PeerSendRequest): Promise<string | null> {
  const harnessRoot = process.env.HARNESS_V2_ROOT?.trim();
  if (!harnessRoot) {
    return null;
  }
  const entry = join(harnessRoot, "src", "send.ts");
  if (!existsSync(entry)) {
    return null;
  }
  try {
    const sendPrompt = sendPromptOf(await import(pathToFileURL(entry).href));
    if (!sendPrompt) {
      return null;
    }
    const raw: unknown = sendPrompt({
      computerRoot: request.computerRoot,
      from: request.from,
      to: request.to,
      prompt: request.prompt,
      paths: request.paths,
    });
    if (!isRecord(raw)) {
      return null;
    }
    return typeof raw.handleId === "string" ? raw.handleId : null;
  } catch {
    return null;
  }
}

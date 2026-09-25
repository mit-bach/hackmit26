import { sendPrompt } from "../../../.harness/Harness-v3/src/send.ts";

import { itemFileName } from "./ledger.ts";

export function wakeText(itemId: string, step: string): string {
  return [
    "[harness wake]",
    "kind: item_step",
    `item: ${itemId}`,
    `step: ${step}`,
    `packet: runs/items/${itemFileName(itemId)}`,
  ].join("\n");
}

export function enqueueItem(
  computerRoot: string,
  itemId: string,
  step: string,
  owner: string,
): { readonly owner: string; readonly handleId: string } {
  const prompt = wakeText(itemId, step);
  const sent = sendPrompt({
    computerRoot,
    from: "harness",
    to: owner,
    prompt,
    paths: [`runs/items/${itemFileName(itemId)}`],
    kind: "a2a_handoff",
    onBusy: "queue",
    mode: "async",
  });
  if (!sent.accepted || !sent.handleId) {
    throw new Error(sent.reason ?? `enqueue to ${owner} was not accepted`);
  }
  return { owner, handleId: sent.handleId };
}

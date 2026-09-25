/** Stable id for the Email↔AP (etc.) handoff log. Sorted so either side opens the same channel. */
export function pairChannelId(leftId: string, rightId: string): string {
  const [first, second] = [leftId, rightId].sort();
  return `pair:${first}:${second}`;
}

export function isPairChannelId(id: string): boolean {
  return id.startsWith("pair:");
}

export function parsePairChannelId(id: string): { readonly a: string; readonly b: string } | undefined {
  if (!isPairChannelId(id)) {
    return undefined;
  }
  const parts = id.split(":");
  const a = parts[1];
  const b = parts[2];
  if (!a || !b || parts.length !== 3) {
    return undefined;
  }
  return { a, b };
}

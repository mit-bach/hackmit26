import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

import { ensureDir, withFileLock } from "./fs.ts";
import { seqPath } from "./paths.ts";

export function nextSeq(computerRoot: string): number {
  const file = seqPath(computerRoot);
  ensureDir(dirname(file));
  return withFileLock(file, () => {
    let current = 0;
    if (existsSync(file)) {
      const raw = readFileSync(file, "utf8").trim();
      const parsed = Number.parseInt(raw, 10);
      if (Number.isFinite(parsed)) {
        current = parsed;
      }
    }
    const next = current + 1;
    writeFileSync(file, `${next}\n`, "utf8");
    return next;
  });
}

import { existsSync, writeFileSync } from "node:fs";

import { applyClientAttach, loadClientRuntime } from "./client-runtime.ts";
import { ensureDir, writeJsonAtomic } from "./fs.ts";
import { seedVerifierIntercept } from "./intercept.ts";
import {
  approvalDir,
  botDir,
  extensionsManifestPath,
  handleDir,
  harnessRoot,
  interceptPath,
  leaseDir,
  memoryDir,
  memoryFile,
  memoryLogDir,
  memoryTopicsDir,
  receiptDir,
  roomDir,
  threadsDir,
} from "./paths.ts";
import { loadRoster } from "./roster.ts";
import type { Roster } from "./types.ts";

export function initComputer(computerRoot: string, roster?: Roster): Roster {
  const loaded = roster ?? loadRoster(computerRoot);
  ensureDir(harnessRoot(computerRoot));
  ensureDir(leaseDir(computerRoot));
  ensureDir(approvalDir(computerRoot));
  ensureDir(receiptDir(computerRoot));
  ensureDir(threadsDir(computerRoot));
  const client = loadClientRuntime(computerRoot);
  if (client.extraExtensions.length > 0 || client.clientSkills) {
    applyClientAttach(computerRoot, client);
  } else if (!existsSync(extensionsManifestPath(computerRoot))) {
    writeJsonAtomic(extensionsManifestPath(computerRoot), { extraExtensions: [], clientSkills: false });
  }
  if (!existsSync(interceptPath(computerRoot))) {
    writeJsonAtomic(interceptPath(computerRoot), { default: { kind: "operator" }, bots: {} });
  }
  seedVerifierIntercept(computerRoot);
  for (const bot of loaded.bots) {
    ensureDir(botDir(computerRoot, bot.id));
    ensureDir(handleDir(computerRoot, bot.id));
    ensureDir(memoryDir(computerRoot, bot.id));
    ensureDir(memoryTopicsDir(computerRoot, bot.id));
    ensureDir(memoryLogDir(computerRoot, bot.id));
    const mem = memoryFile(computerRoot, bot.id);
    try {
      writeFileSync(mem, `# ${bot.name}\n\nStanding notes for this Bot. Not shared.\n`, {
        flag: "wx",
      });
    } catch {
      // MEMORY.md already exists.
    }
  }
  for (const room of loaded.rooms) {
    ensureDir(roomDir(computerRoot, room.id));
  }
  return loaded;
}

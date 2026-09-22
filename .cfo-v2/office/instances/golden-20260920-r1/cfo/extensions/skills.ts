import {existsSync} from "node:fs";
import {dirname, join} from "node:path";

export function intersectSkillNames(
  grantSkills: readonly string[],
  rosterSkills: readonly string[],
): readonly string[] {
  if (rosterSkills.length === 0) {
    return grantSkills;
  }
  const roster = new Set(rosterSkills);
  return grantSkills.filter((name) => roster.has(name));
}

export function skillDirectoryPaths(
  names: readonly string[],
  skillRoots: readonly string[],
): string[] {
  const paths: string[] = [];
  const seen = new Set<string>();
  for (const name of names) {
    for (const root of skillRoots) {
      const dir = join(root, name);
      if (!existsSync(dir) || seen.has(dir)) {
        continue;
      }
      seen.add(dir);
      paths.push(dir);
    }
  }
  return paths;
}

export function kernelSkillsRoot(computerRoot: string, env: NodeJS.ProcessEnv = process.env): string | undefined {
  const fromEnv = env.CFO_KERNEL?.trim();
  if (fromEnv) {
    const candidate = join(fromEnv, "skills");
    return existsSync(candidate) ? candidate : undefined;
  }
  let dir = computerRoot;
  for (let i = 0; i < 10; i += 1) {
    const candidate = join(dir, ".cfo", "skills");
    if (existsSync(candidate)) {
      return candidate;
    }
    const parent = dirname(dir);
    if (parent === dir) {
      break;
    }
    dir = parent;
  }
  return undefined;
}

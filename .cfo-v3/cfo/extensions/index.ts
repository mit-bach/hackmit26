/**
 * CFO Client Pi extension. Load with Harness, not instead of it:
 *
 *   HARNESS_BOT=ap HARNESS_COMPUTER=.cfo-v2/office/computer \
 *     pi -e .harness/Harness-v2/extensions/index.ts \
 *        -e .cfo-v2/office/computer/cfo/extensions/index.ts \
 *        --name ap
 *
 * Unbound Pi (no HARNESS_BOT) registers nothing.
 */

import {existsSync, mkdirSync, readFileSync, writeFileSync} from "node:fs";
import {join} from "node:path";

import {Type} from "typebox";

import {callConnectedTool} from "./call.ts";
import {resolvePendingHandleId} from "./intercept.ts";
import {isRecord, loadClientFiles} from "./load.ts";
import type {PiExtensionApi, PiToolResult} from "./pi-api.ts";
import {bindBot, parseProfileFromWake, replaceProfile} from "./profile.ts";
import {resolveOp, searchConnectedTools} from "./search.ts";
import {sendPeerHandle} from "./send.ts";
import {intersectSkillNames, kernelSkillsRoot, skillDirectoryPaths} from "./skills.ts";
import type {BoundProfile, EvalPhase} from "./types.ts";

function toolText(payload: unknown): PiToolResult {
  return {
    content: [{type: "text", text: JSON.stringify(payload, null, 2)}],
    details: payload,
  };
}

function evalPhase(env: NodeJS.ProcessEnv): EvalPhase {
  return env.CFO_EVAL_PHASE === "evaluation" ? "evaluation" : "operational";
}

function readString(params: Record<string, unknown>, key: string): string {
  const value = params[key];
  return typeof value === "string" ? value : "";
}

function readArgs(params: Record<string, unknown>): Record<string, unknown> {
  const value = params.args;
  return isRecord(value) ? value : {};
}

function rosterSkillsFor(computerRoot: string, slug: string): string[] {
  const path = join(computerRoot, "harness", "roster.json");
  if (!existsSync(path)) {
    return [];
  }
  try {
    const raw: unknown = JSON.parse(readFileSync(path, "utf8"));
    if (!isRecord(raw) || !Array.isArray(raw.bots)) {
      return [];
    }
    for (const row of raw.bots) {
      if (!isRecord(row) || row.slug !== slug || !Array.isArray(row.skills)) {
        continue;
      }
      return row.skills.filter((item): item is string => typeof item === "string");
    }
  } catch {
    return [];
  }
  return [];
}

function skillPathsFor(bind: BoundProfile): string[] {
  const roots: string[] = [];
  const computerSkills = join(bind.computerRoot, "skills");
  if (existsSync(computerSkills)) {
    roots.push(computerSkills);
  }
  const nested = join(bind.computerRoot, "cfo", "skills");
  if (existsSync(nested)) {
    roots.push(nested);
  }
  const kernel = kernelSkillsRoot(bind.computerRoot);
  if (kernel) {
    roots.push(kernel);
  }
  const names = intersectSkillNames(bind.grant.skills, rosterSkillsFor(bind.computerRoot, bind.slug));
  const paths = skillDirectoryPaths(names, roots);
  const harnessRoot = process.env.HARNESS_V2_ROOT?.trim();
  if (harnessRoot) {
    const harnessSkills = join(harnessRoot, "skills");
    if (existsSync(harnessSkills)) {
      paths.unshift(harnessSkills);
    }
  }
  return paths;
}

export default function cfoExtension(pi: PiExtensionApi): void {
  const slug = process.env.HARNESS_BOT?.trim();
  if (!slug) {
    return;
  }
  const computerRoot = process.env.HARNESS_COMPUTER?.trim() || process.cwd();
  const files = loadClientFiles(computerRoot);
  const phase = evalPhase(process.env);
  let bind: BoundProfile = bindBot({
    computerRoot,
    slug,
    profile: process.env.HARNESS_PROFILE?.trim(),
    phase,
    grants: files.grants,
    slugMap: files.slugMap,
  });

  pi.on("resources_discover", () => ({skillPaths: skillPathsFor(bind)}));

  pi.on("input", (event) => {
    if (!event.text.startsWith("[harness wake]")) {
      return {action: "continue"};
    }
    const named = parseProfileFromWake(event.text);
    if (!named) {
      return {action: "continue"};
    }
    try {
      const botDir = join(computerRoot, "harness", "bots", `bot_${slug.replaceAll("-", "_")}`);
      mkdirSync(botDir, {recursive: true});
      writeFileSync(join(botDir, "active-profile.txt"), named);
    } catch {
      // The running worker keeps the previous profile. A missing note is not a failed wake.
    }
    bind = replaceProfile(
      bind,
      bindBot({
        computerRoot,
        slug,
        profile: named,
        phase,
        grants: files.grants,
        slugMap: files.slugMap,
      }),
    );
    return {action: "continue"};
  });

  pi.on("tool_call", (event) => {
    if (event.toolName === "ask_user") {
      return {
        block: true,
        reason:
          "Verifier Bots own concurrence. Do not call ask_user. Handle to ctl-pay, ctl-cash, or ctl-books.",
      };
    }
    return;
  });

  pi.registerTool({
    name: "search_connected_tools",
    label: "Search connected tools",
    description: "Search Kernel Connector ops this Bot's active Profile may call.",
    promptSnippet: "Find granted Kernel ops for this Profile",
    promptGuidelines: [
      "search_connected_tools returns only this Profile's Catalog rows. It never returns another Bot's ops or evalOnly ops in operational phase.",
    ],
    parameters: Type.Object({
      query: Type.String({description: "Substring over Catalog id or exportName"}),
      status: Type.Optional(Type.String({description: "Ignored; reserved for later Connector status"})),
    }),
    execute: async (_id, params) => {
      return toolText(
        searchConnectedTools(bind, files.catalog, {
          query: readString(params, "query"),
          status: readString(params, "status") || undefined,
        }),
      );
    },
  });

  pi.registerTool({
    name: "call_connected_tool",
    label: "Call connected tool",
    description: "Call one granted Kernel op. Off-grant names return forbidden. Consequential writes Handle to a Verifier Bot.",
    promptSnippet: "Call a granted Kernel Connector",
    promptGuidelines: [
      "call_connected_tool is the only Kernel door. Do not invent amounts. Python returns candidates. Consequential ops go to ctl-* Verifiers, never ask_user.",
      "After a Verifier Handle completes with CONCUR, call again with the same idempotency_key and the same args. Changed args need a new Verifier Handle. handle_id is optional.",
    ],
    parameters: Type.Object({
      name: Type.String({description: "Catalog id or exportName"}),
      args: Type.Optional(Type.Any()),
      idempotency_key: Type.Optional(Type.String()),
      handle_id: Type.Optional(
        Type.String({description: "Verifier Handle id from verifier_required; looked up by idempotency_key when omitted"}),
      ),
    }),
    execute: async (_id, params) => {
      const name = readString(params, "name");
      const key = readString(params, "idempotency_key");
      const idempotencyKey = key.length > 0 ? key : undefined;
      const passed = readString(params, "handle_id");
      const args = readArgs(params);
      const op = resolveOp(files.catalog, name);
      const handleId =
        passed.length > 0 ? passed : op === undefined ? null : resolvePendingHandleId(bind, op, idempotencyKey, args);
      const result = await callConnectedTool(
        bind,
        files.catalog,
        {
          name,
          args,
          idempotencyKey,
        },
        undefined,
        handleId,
        async (input: {readonly to: string; readonly prompt: string; readonly paths: readonly string[]}): Promise<string | null> =>
          sendPeerHandle({
            computerRoot,
            from: bind.botId,
            to: input.to,
            prompt: input.prompt,
            paths: input.paths,
          }),
      );
      return toolText(result);
    },
  });
}

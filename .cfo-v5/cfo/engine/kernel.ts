import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { join } from "node:path";

export interface BillFacts {
  readonly invoice_id: string;
  readonly amount: number | null;
  readonly po_id: string | null;
  readonly receipt_id: string | null;
  readonly must_hold: readonly string[];
  readonly exception_types: readonly string[];
  readonly clean: boolean;
}

function readPort(computerRoot: string): number | undefined {
  try {
    const raw = JSON.parse(readFileSync(join(computerRoot, "cfo", "kernel.port"), "utf8")) as { port?: unknown };
    return typeof raw.port === "number" && raw.port > 0 ? raw.port : undefined;
  } catch {
    return undefined;
  }
}

export function kernelRpc(
  computerRoot: string,
  body: Record<string, unknown>,
): { ok: boolean; result: unknown; error: string | null } {
  const port = readPort(computerRoot);
  if (port) {
    const result = spawnSync(
      "curl",
      [
        "-sS",
        "-m",
        "20",
        "-X",
        "POST",
        `http://127.0.0.1:${port}/rpc`,
        "-H",
        "content-type: application/json",
        "--data-binary",
        JSON.stringify(body),
      ],
      { encoding: "utf8" },
    );
    if (result.status !== 0) {
      return { ok: false, result: null, error: (result.stderr || "kernel http failed").slice(0, 500) };
    }
    const parsed = JSON.parse(result.stdout) as { ok?: boolean; result?: unknown; error?: { message?: string } | null };
    return { ok: parsed.ok === true, result: parsed.result ?? null, error: parsed.error?.message ?? null };
  }
  const py = join(computerRoot, "kernel", ".venv", "bin", "python");
  const script = `
import json, os, sys
from pathlib import Path
from cfo_kernel.paths import attach_computer
from cfo_kernel.rpc import handle_rpc
attach_computer(Path(os.environ["HARNESS_COMPUTER"]))
print(json.dumps(handle_rpc(json.loads(sys.stdin.read()))))
`;
  const result = spawnSync(py, ["-c", script], {
    cwd: computerRoot,
    input: JSON.stringify(body),
    encoding: "utf8",
    env: {
      ...process.env,
      PYTHONPATH: join(computerRoot, "kernel"),
      HARNESS_COMPUTER: computerRoot,
      CFO_EVAL_PHASE: "operational",
    },
  });
  if (result.status !== 0) {
    return { ok: false, result: null, error: (result.stderr || "kernel rpc failed").slice(0, 500) };
  }
  const parsed = JSON.parse(result.stdout) as { ok?: boolean; result?: unknown; error?: { message?: string } | null };
  return { ok: parsed.ok === true, result: parsed.result ?? null, error: parsed.error?.message ?? null };
}

function kernelPython(computerRoot: string, args: readonly string[]): unknown {
  const py = join(computerRoot, "kernel", ".venv", "bin", "python");
  const result = spawnSync(py, ["-m", "cfo_kernel.facts", ...args], {
    cwd: computerRoot,
    env: {
      ...process.env,
      PYTHONPATH: join(computerRoot, "kernel"),
      HARNESS_COMPUTER: computerRoot,
      CFO_EVAL_PHASE: "operational",
    },
    encoding: "utf8",
  });
  if (result.status !== 0) {
    throw new Error((result.stderr || result.stdout || "kernel facts failed").slice(0, 800));
  }
  return JSON.parse(result.stdout);
}

export function readBillFacts(computerRoot: string, invoiceId: string): BillFacts {
  const port = readPort(computerRoot);
  if (port) {
    const row = kernelRpc(computerRoot, {
      op: "kernel.bill_facts",
      args: { invoice_id: invoiceId },
      botId: "kernel-host",
      slug: "_host",
      profile: "sidecar",
      handleId: "engine",
      idempotencyKey: null,
    });
    if (!row.ok || !row.result) {
      throw new Error(row.error ?? "kernel.bill_facts failed");
    }
    return row.result as BillFacts;
  }
  return kernelPython(computerRoot, ["bill", invoiceId]) as BillFacts;
}

export function cashSignOffRequired(computerRoot: string, amount: number, disposition: string): boolean {
  const port = readPort(computerRoot);
  if (port) {
    const row = kernelRpc(computerRoot, {
      op: "kernel.cash_signoff",
      args: { amount, disposition },
      botId: "kernel-host",
      slug: "_host",
      profile: "sidecar",
      handleId: "engine",
      idempotencyKey: null,
    });
    const result = row.result as { required?: boolean } | null;
    return row.ok && result?.required === true;
  }
  const row = kernelPython(computerRoot, ["signoff", String(amount), disposition]) as { required?: boolean };
  return row.required === true;
}

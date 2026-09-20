import { useState } from "react";
import { post } from "./api";

export function useWorkflow() {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(path: string, body?: unknown) {
    setRunning(true);
    setError(null);
    try {
      const payload = await post<any>(path, body);
      setResult(payload);
      if (payload?.ok === false) {
        setError(payload.error?.message || "Workflow failed");
      }
      return payload;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      setResult({ ok: false, error: { message } });
      return null;
    } finally {
      setRunning(false);
    }
  }

  return { running, result, error, run, setResult };
}
